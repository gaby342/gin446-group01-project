"""Flask controller for the La Wayn? group restaurant picker."""
import json
import os
import random
import sqlite3
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import api_client
import models
import validators

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


@app.before_request
def ensure_database():
    models.init_db()


@app.context_processor
def template_globals():
    user = models.user_by_id(session["user_id"]) if session.get("user_id") else None
    return {"models_user_name": user["name"] if user else ""}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def group_or_404(group_id):
    group = models.group_for_user(group_id, session["user_id"])
    if not group: abort(404)
    return group


def error_response(message, code=400):
    if request.is_json: return jsonify(error=message), code
    flash(message, "error")
    return redirect(request.referrer or url_for("home"))


@app.get("/")
def home():
    user = models.user_by_id(session["user_id"]) if session.get("user_id") else None
    groups = models.groups_for_user(user["id"]) if user else []
    return render_template("home.html", user=user, groups=groups)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            name = validators.text(request.form.get("name"), "Name", 2, 60)
            email = validators.email(request.form.get("email"))
            password = validators.password(request.form.get("password"))
            user_id = models.create_user(name, email, generate_password_hash(password))
            session.clear(); session["user_id"] = user_id
            flash("Welcome! Create a friend group to get started.", "success")
            return redirect(url_for("home"))
        except validators.ValidationError as exc: flash(str(exc), "error")
        except sqlite3.IntegrityError: flash("That email already has an account.", "error")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = models.user_by_email(email)
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear(); session["user_id"] = user["id"]
            next_path=request.args.get("next", "")
            return redirect(next_path if next_path.startswith("/") and not next_path.startswith("//") else url_for("home"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.post("/groups")
@login_required
def create_group():
    try: name = validators.text(request.form.get("name"), "Group name", 2, 60)
    except validators.ValidationError as exc: return error_response(str(exc))
    models.create_group(name, session["user_id"])
    flash("Your friend group is ready. Share its invite code.", "success")
    return redirect(url_for("home"))


@app.post("/groups/join")
@login_required
def join_group():
    code = (request.form.get("invite_code") or "").strip()
    if not 5 <= len(code) <= 12 or not models.join_group(code, session["user_id"]):
        flash("We couldn't find a group with that invite code.", "error")
    else: flash("You joined the group.", "success")
    return redirect(url_for("home"))


@app.get("/groups/<int:group_id>")
@login_required
def group_detail(group_id):
    group = group_or_404(group_id)
    active = models.current_session(group_id)
    history = models.session_history(group_id)
    return render_template("results.html", group=group, members=models.group_members(group_id), active=active, history=history)


@app.get("/groups/<int:group_id>/favorites")
@login_required
def favorites_page(group_id):
    group = group_or_404(group_id)
    return render_template("favorites.html", group=group, favorites=models.favorites(group_id,session["user_id"]))


@app.get("/groups/<int:group_id>/search")
@login_required
def search_page(group_id):
    group=group_or_404(group_id)
    return render_template("detail.html", group=group, members=models.group_members(group_id))


@app.post("/groups/<int:group_id>/search")
@login_required
def search_api(group_id):
    group_or_404(group_id)
    data = request.get_json(silent=True) or request.form
    try:
        lat, lon = validators.coordinates(data.get("lat"), data.get("lon"))
        radius = validators.radius(data.get("radius_m", 3000))
        cuisines = validators.choices(data.get("cuisines", []), {"lebanese","middle_eastern","italian","japanese","chinese","mexican","indian","american","french","thai","mediterranean","pizza","burger","korean","vegan"}, "cuisines")
        filters = {"cuisines": cuisines, "open_now": str(data.get("open_now", "")).lower() in ("true","1","on"), "vegetarian": str(data.get("vegetarian", "")).lower() in ("true","1","on"), "halal": str(data.get("halal", "")).lower() in ("true","1","on")}
        try:
            weekday, minute = int(data.get("local_weekday")), int(data.get("local_minute"))
            if weekday not in range(7) or minute not in range(1440): raise ValueError
        except (TypeError, ValueError):
            from datetime import datetime
            current = datetime.now(); weekday, minute = (current.weekday()+1)%7, current.hour*60+current.minute
        places = api_client.search_restaurants(lat,lon,radius,cuisines,filters["vegetarian"],filters["halal"],filters["open_now"],weekday,minute)
        if not places: return error_response("No restaurants matched. Try a larger radius or fewer filters.")
        random.SystemRandom().shuffle(places)
        title = validators.text(data.get("title") or "Dinner decision", "Session name", 2, 80)
        sid = models.create_session(group_id,session["user_id"],title,lat,lon,radius,filters,places)
        return jsonify(redirect=url_for("session_page",session_id=sid), count=len(places)) if request.is_json else redirect(url_for("session_page",session_id=sid))
    except validators.ValidationError as exc: return error_response(str(exc))
    except Exception as exc:
        app.logger.exception("OpenStreetMap search failed")
        return error_response("Restaurant search is temporarily unavailable. Please try again in a moment.", 502)


@app.get("/sessions/<int:session_id>")
@login_required
def session_page(session_id):
    state=models.session_status(session_id,session["user_id"])
    if not state: abort(404)
    return render_template("session.html", data=state)


@app.get("/sessions/<int:session_id>/status")
@login_required
def session_poll(session_id):
    state=models.session_status(session_id,session["user_id"])
    if not state: abort(404)
    return jsonify(state)


@app.post("/sessions/<int:session_id>/vote")
@login_required
def vote(session_id):
    data=request.get_json(silent=True) or request.form
    try:
        place_id=int(data.get("place_id"))
        choice=data.get("vote")
        if choice not in ("yes","no"): raise validators.ValidationError("Choose yes or no.")
    except (TypeError,ValueError): return jsonify(error="Choose a valid restaurant."),400
    except validators.ValidationError as exc: return jsonify(error=str(exc)),400
    result=models.record_vote(session_id,place_id,session["user_id"],choice)
    return (jsonify(result),400) if "error" in result else jsonify(result)


@app.post("/groups/<int:group_id>/places/<int:place_id>/rating")
@login_required
def rate_place(group_id,place_id):
    group_or_404(group_id)
    data=request.get_json(silent=True) or request.form
    try:
        value=validators.rating(data.get("rating"))
        note=validators.text(data.get("note", ""),"Note",0,500)
        models.add_rating(group_id,place_id,session["user_id"],value,note)
        return jsonify(ok=True) if request.is_json else redirect(url_for("favorites_page",group_id=group_id))
    except validators.ValidationError as exc: return error_response(str(exc))


@app.get("/detail/<int:place_id>")
@login_required
def place_detail(place_id):
    with models.connect() as db:
        row=db.execute("SELECT * FROM places WHERE id=?",(place_id,)).fetchone()
    if not row: abort(404)
    return render_template("place.html", place=dict(row), groups=models.groups_for_user(session["user_id"]))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT",5000)))
