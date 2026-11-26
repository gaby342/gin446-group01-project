"""SQLite schema and data access for La Wayn?"""
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "instance", "lawayn.sqlite3"))


def connect():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS friend_groups (id INTEGER PRIMARY KEY, name TEXT NOT NULL, invite_code TEXT NOT NULL UNIQUE, created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memberships (group_id INTEGER NOT NULL REFERENCES friend_groups(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, joined_at TEXT NOT NULL, PRIMARY KEY(group_id,user_id));
CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, group_id INTEGER NOT NULL REFERENCES friend_groups(id), host_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, center_lat REAL NOT NULL, center_lon REAL NOT NULL, radius_m INTEGER NOT NULL, filters TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'voting', round_no INTEGER NOT NULL DEFAULT 1, match_place_id INTEGER, created_at TEXT NOT NULL, finished_at TEXT);
CREATE TABLE IF NOT EXISTS session_members (session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id), joined_at TEXT NOT NULL, PRIMARY KEY(session_id,user_id));
CREATE TABLE IF NOT EXISTS session_places (session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, place_id INTEGER NOT NULL REFERENCES places(id), round_no INTEGER NOT NULL DEFAULT 1, position INTEGER NOT NULL, PRIMARY KEY(session_id,place_id,round_no));
CREATE TABLE IF NOT EXISTS places (id INTEGER PRIMARY KEY, osm_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, cuisine TEXT NOT NULL, category TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, distance_m INTEGER NOT NULL, address TEXT NOT NULL DEFAULT '', opening_hours TEXT NOT NULL DEFAULT '', is_vegetarian TEXT NOT NULL DEFAULT '', is_halal TEXT NOT NULL DEFAULT '', osm_url TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS votes (session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, place_id INTEGER NOT NULL REFERENCES places(id), user_id INTEGER NOT NULL REFERENCES users(id), round_no INTEGER NOT NULL, vote TEXT NOT NULL CHECK(vote IN ('yes','no')), created_at TEXT NOT NULL, PRIMARY KEY(session_id,place_id,user_id,round_no));
CREATE TABLE IF NOT EXISTS ratings (id INTEGER PRIMARY KEY, group_id INTEGER NOT NULL REFERENCES friend_groups(id) ON DELETE CASCADE, place_id INTEGER NOT NULL REFERENCES places(id), user_id INTEGER NOT NULL REFERENCES users(id), rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, UNIQUE(group_id,place_id,user_id));
CREATE INDEX IF NOT EXISTS idx_sessions_group ON sessions(group_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_votes_place ON votes(session_id,place_id,round_no);
"""


def init_db():
    with connect() as db:
        db.executescript(SCHEMA)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rowdict(row):
    return dict(row) if row else None


def create_user(name, email, password_hash):
    with connect() as db:
        cur = db.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)", (name,email,password_hash,now()))
        return cur.lastrowid


def user_by_email(email):
    with connect() as db: return rowdict(db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone())


def user_by_id(user_id):
    with connect() as db: return rowdict(db.execute("SELECT id,name,email,created_at FROM users WHERE id=?",(user_id,)).fetchone())


def create_group(name, user_id):
    code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].upper()
    with connect() as db:
        cur = db.execute("INSERT INTO friend_groups(name,invite_code,created_by,created_at) VALUES(?,?,?,?)",(name,code,user_id,now()))
        group_id = cur.lastrowid
        db.execute("INSERT INTO memberships VALUES(?,?,?)",(group_id,user_id,now()))
        return group_id


def join_group(code, user_id):
    with connect() as db:
        group = db.execute("SELECT * FROM friend_groups WHERE invite_code=?",(code.upper(),)).fetchone()
        if not group: return False
        db.execute("INSERT OR IGNORE INTO memberships VALUES(?,?,?)",(group["id"],user_id,now()))
        return True


def groups_for_user(user_id):
    with connect() as db: return [dict(r) for r in db.execute("SELECT g.*, (SELECT COUNT(*) FROM memberships m WHERE m.group_id=g.id) AS member_count FROM friend_groups g JOIN memberships m ON m.group_id=g.id WHERE m.user_id=? ORDER BY g.created_at DESC",(user_id,))]


def group_for_user(group_id,user_id):
    with connect() as db: return rowdict(db.execute("SELECT g.* FROM friend_groups g JOIN memberships m ON m.group_id=g.id WHERE g.id=? AND m.user_id=?",(group_id,user_id)).fetchone())


def group_members(group_id):
    with connect() as db: return [dict(r) for r in db.execute("SELECT u.id,u.name,u.email FROM users u JOIN memberships m ON m.user_id=u.id WHERE m.group_id=? ORDER BY m.joined_at",(group_id,))]


def create_session(group_id,host_id,title,lat,lon,radius_m,filters,places):
    with connect() as db:
        cur=db.execute("INSERT INTO sessions(group_id,host_id,title,center_lat,center_lon,radius_m,filters,created_at) VALUES(?,?,?,?,?,?,?,?)",(group_id,host_id,title,lat,lon,radius_m,json.dumps(filters),now()))
        sid=cur.lastrowid
        db.execute("INSERT INTO session_members(session_id,user_id,joined_at) SELECT ?,user_id,? FROM memberships WHERE group_id=?",(sid,now(),group_id))
        for pos, place in enumerate(places):
            db.execute("INSERT INTO places(osm_id,name,cuisine,category,lat,lon,distance_m,address,opening_hours,is_vegetarian,is_halal,osm_url) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(osm_id) DO UPDATE SET name=excluded.name,cuisine=excluded.cuisine,category=excluded.category,lat=excluded.lat,lon=excluded.lon,distance_m=excluded.distance_m,address=excluded.address,opening_hours=excluded.opening_hours,is_vegetarian=excluded.is_vegetarian,is_halal=excluded.is_halal,osm_url=excluded.osm_url",tuple(place.get(k,"") for k in ("osm_id","name","cuisine","category","lat","lon","distance_m","address","opening_hours","is_vegetarian","is_halal","osm_url")))
            pid=db.execute("SELECT id FROM places WHERE osm_id=?",(place["osm_id"],)).fetchone()[0]
            db.execute("INSERT INTO session_places VALUES(?,?,1,?)",(sid,pid,pos))
        return sid


def session_for_user(session_id,user_id):
    with connect() as db: return rowdict(db.execute("SELECT s.*,g.name AS group_name FROM sessions s JOIN friend_groups g ON g.id=s.group_id JOIN memberships m ON m.group_id=g.id WHERE s.id=? AND m.user_id=?",(session_id,user_id)).fetchone())


def current_session(group_id):
    with connect() as db: return rowdict(db.execute("SELECT * FROM sessions WHERE group_id=? AND state IN ('voting','runoff') ORDER BY created_at DESC LIMIT 1",(group_id,)).fetchone())


def session_history(group_id):
    with connect() as db: return [dict(r) for r in db.execute("SELECT s.*,p.name AS match_name FROM sessions s LEFT JOIN places p ON p.id=s.match_place_id WHERE s.group_id=? ORDER BY s.created_at DESC",(group_id,))]


def session_status(session_id,user_id):
    with connect() as db:
        s=db.execute("SELECT * FROM sessions WHERE id=?",(session_id,)).fetchone()
        if not s: return None
        members=[dict(r) for r in db.execute("SELECT u.id,u.name FROM users u JOIN session_members m ON m.user_id=u.id WHERE m.session_id=? ORDER BY m.joined_at",(session_id,))]
        places=[dict(r) for r in db.execute("SELECT p.*,sp.position,COALESCE(r.avg_rating,0) AS group_rating,COALESCE(r.rating_count,0) AS rating_count FROM session_places sp JOIN places p ON p.id=sp.place_id LEFT JOIN (SELECT place_id,AVG(rating) avg_rating,COUNT(*) rating_count FROM ratings WHERE group_id=? GROUP BY place_id) r ON r.place_id=p.id WHERE sp.session_id=? AND sp.round_no=? ORDER BY sp.position",(s["group_id"],session_id,s["round_no"]))]
        vote_rows=db.execute("SELECT * FROM votes WHERE session_id=? AND round_no=?",(session_id,s["round_no"])).fetchall()
        votes={}
        for vote in vote_rows: votes.setdefault(vote["place_id"],{})[str(vote["user_id"])]=vote["vote"]
        for p in places: p["votes"]={str(m["id"]):votes.get(p["id"],{}).get(str(m["id"])) for m in members}
        own_votes={str(r["place_id"]):r["vote"] for r in vote_rows if r["user_id"]==user_id}
        return {"session":dict(s),"filters":json.loads(s["filters"]),"members":members,"places":places,"own_votes":own_votes}


def record_vote(session_id,place_id,user_id,vote):
    with connect() as db:
        s=db.execute("SELECT * FROM sessions WHERE id=?",(session_id,)).fetchone()
        member=db.execute("SELECT 1 FROM session_members WHERE session_id=? AND user_id=?",(session_id,user_id)).fetchone() if s else None
        active=db.execute("SELECT 1 FROM session_places WHERE session_id=? AND place_id=? AND round_no=?",(session_id,place_id,s["round_no"])).fetchone() if s else None
        if not s or not member or not active or s["state"] not in ("voting","runoff"): return {"error":"This session is no longer accepting votes."}
        db.execute("INSERT INTO votes VALUES(?,?,?,?,?,?) ON CONFLICT(session_id,place_id,user_id,round_no) DO UPDATE SET vote=excluded.vote,created_at=excluded.created_at",(session_id,place_id,user_id,s["round_no"],vote,now()))
        members=[r[0] for r in db.execute("SELECT user_id FROM session_members WHERE session_id=?",(session_id,))]
        votes={r[0]:r[1] for r in db.execute("SELECT user_id,vote FROM votes WHERE session_id=? AND place_id=? AND round_no=?",(session_id,place_id,s["round_no"]))}
        if members and all(votes.get(uid)=="yes" for uid in members):
            db.execute("UPDATE sessions SET state='matched',match_place_id=?,finished_at=? WHERE id=?",(place_id,now(),session_id))
            return {"state":"matched","place_id":place_id}
        unresolved=db.execute("SELECT COUNT(*) FROM session_members sm CROSS JOIN session_places sp LEFT JOIN votes v ON v.session_id=sp.session_id AND v.place_id=sp.place_id AND v.user_id=sm.user_id AND v.round_no=sp.round_no WHERE sm.session_id=? AND sp.session_id=? AND sp.round_no=? AND v.user_id IS NULL",(session_id,session_id,s["round_no"])).fetchone()[0]
        if unresolved==0:
            runoff=db.execute("SELECT sp.place_id, SUM(CASE WHEN v.vote='yes' THEN 1 ELSE 0 END) yes_count FROM session_places sp LEFT JOIN votes v ON v.session_id=sp.session_id AND v.place_id=sp.place_id AND v.round_no=sp.round_no WHERE sp.session_id=? AND sp.round_no=? GROUP BY sp.place_id HAVING SUM(CASE WHEN v.vote='yes' THEN 1 ELSE 0 END)>0 ORDER BY yes_count DESC,sp.position LIMIT 3",(session_id,s["round_no"])).fetchall()
            if s["round_no"]==1 and any(r["yes_count"] for r in runoff):
                db.execute("UPDATE sessions SET state='runoff',round_no=2 WHERE id=?",(session_id,))
                for i,r in enumerate(runoff): db.execute("INSERT INTO session_places VALUES(?,?,2,?)",(session_id,r["place_id"],i))
                return {"state":"runoff"}
            db.execute("UPDATE sessions SET state='no_match',finished_at=? WHERE id=?",(now(),session_id))
            return {"state":"no_match"}
        return {"state":"voting"}


def add_rating(group_id,place_id,user_id,value,note):
    with connect() as db:
        db.execute("INSERT INTO ratings(group_id,place_id,user_id,rating,note,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(group_id,place_id,user_id) DO UPDATE SET rating=excluded.rating,note=excluded.note,created_at=excluded.created_at",(group_id,place_id,user_id,value,note,now()))


def favorites(group_id,user_id):
    with connect() as db: return [dict(r) for r in db.execute("SELECT p.*,r.rating FROM ratings r JOIN places p ON p.id=r.place_id WHERE r.group_id=? AND r.user_id=? ORDER BY r.created_at DESC",(group_id,user_id))]
