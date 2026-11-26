# La Wayn? — gin446-group01-project

A real-time group restaurant picker built with Flask, vanilla JavaScript, SQLite, and OpenStreetMap data. Friends join a shared group, discover nearby restaurants, swipe at their own pace, and find the first place everyone likes. If the deck runs out, the group's leading choices get a quick second round.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python reset_db.py
python app.py
```

Open http://127.0.0.1:5000. The first registered account can create a group and share its invite code. Restaurant discovery uses the public OpenStreetMap Overpass API and requires an internet connection. Set `SECRET_KEY` and `DATABASE_PATH` in the environment for deployment.

## MVP flow

1. Create an account, create a friend group, or join with an invite code.
2. Start a session by dropping a map pin, setting a search radius, and choosing cuisine, open-now, vegetarian, or halal filters.
3. Group members join the active session and swipe through the shared shuffled deck. A unanimous yes ends the round with a match.
4. When the deck is exhausted, the top three liked places become a short runoff deck.
5. Keep session history with the group, then add a visit rating to a restaurant so the group's average appears on future cards.

## Project layout

```text
app.py            Flask routes and controller
models.py         SQLite schema and data access
api_client.py     OpenStreetMap Overpass client
validators.py     Server-side input validation
reset_db.py       Development database reset utility
templates/        Jinja views
static/           CSS and browser JavaScript
```

The MVP uses short-interval polling for live session updates; it does not require a WebSocket service.
