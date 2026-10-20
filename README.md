# Tic-Tac-Toe (Flask)

A two-player tic-tac-toe game for a class project. Two people play from separate browsers, and the Flask server keeps track of the game.

The app keeps things simple: game state is stored in a Python dictionary in memory, with no database, logins, or websockets. Restarting the server clears all games.

So far it has only a home page. The game itself isn't built yet.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

## Files

- `app.py`: the Flask app and its routes
- `templates/base.html`: the layout shared by every page
- `templates/index.html`: the home page
- `requirements.txt`: the Python packages the app needs
