# Tic-Tac-Toe (Flask)

A two-player tic-tac-toe game built with Flask for a class project. Two people play from separate browsers while the Flask server runs the game.

## What it does

- One player clicks **Create game** and gets a 4-letter code (like `QXRT`) to share. They play as **X**.
- The other player enters the code under **Join game** and plays as **O**.
- Players take turns tapping squares. The server checks every move: it must be your turn, the square must be empty, and the game must not be over.
- The server spots three in a row or a full board, then shows "X wins", "O wins" or "Draw" to both players and highlights the winning squares.
- **Play again** starts a new round with the same two players. A running score keeps track of wins and draws.
- Each player's page updates by itself about once a second, so you see your opponent's move without reloading.
- The pages work on phones and follow the device's dark mode setting.

To keep things simple, there's no database, no logins and no websockets. Games are stored in a Python dictionary in the server's memory, so **restarting the server clears all games**.

## Install

You need Python 3.9 or newer. From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

This creates a virtual environment (a private folder of Python packages for this project) and installs Flask into it. Run the `source` line again whenever you open a new terminal.

## Run

```bash
flask --app app run
```

Then open http://127.0.0.1:5000 in your browser. Press `Ctrl+C` in the terminal to stop the server.

While you're writing code, debug mode is handier: it restarts the server when you save a file and shows Python errors in the browser.

```bash
flask --app app run --debug
```

Don't use debug mode when other people are playing. It shows them Python tracebacks instead of the friendly error page, and every restart wipes the games in progress.

## Test it with two browser windows

You can play both sides yourself on one computer:

1. Start the server with `flask --app app run`.
2. Open http://127.0.0.1:5000 in a browser window and click **Create game**. This window is Player X. Note the 4-letter code on the waiting page.
3. Open a second window (a new tab works too), go to http://127.0.0.1:5000, type the code under **Join game** and click it. This window is Player O.
4. Within a couple of seconds, Player X's window switches from the waiting page to the board.
5. Put the windows side by side and take turns. Each move should appear in the other window within about a second.

Two windows of the same browser work fine. The app tells the players apart by the secret token in each page's URL, not by cookies.

Things worth trying:

- **Out of turn:** in the window whose turn it isn't, the squares can't be tapped. Even if a move got through, the server would reject it with "It's not your turn."
- **Win and draw:** finish a round both ways and check that both windows show the result, the highlight and the updated score.
- **Play again:** click it in one window and check that the other window's board clears too.
- **Errors:** try joining with an empty code, `AB12`, a code that doesn't exist, or a code for a game that already has two players.
- **Bad links:** change a letter in a game URL's token to get the "This link isn't valid" page, or visit a made-up URL for the 404 page.
- **Phone size:** open your browser's developer tools and turn on device mode to see the phone layout.

## How it works

Each player's page URL looks like `/game/QXRT/<token>`. The token is a long random string given only to that player, and it tells the server who is X and who is O. Treat your URL like a password: anyone who has it can play as you.

The game page runs a small script, `static/game.js`. Every second it asks the server for the game state at `/api/game/<code>`, which replies with JSON like this:

```json
{"board": ["X", "", "", "", "O", "", "", "", ""], "turn": "X", "result": null,
 "winning_line": null, "score": {"X": 1, "O": 0, "draw": 0}}
```

The script then redraws the board, the status message and the score. Moves themselves are sent as normal form submissions, and the server checks the rules before saving anything.

## Files

- `app.py`: the Flask app. It holds the game state, the routes, the move rules and the error handlers.
- `templates/base.html`: the layout every page shares
- `templates/index.html`: the home page, with the Create and Join forms
- `templates/waiting.html`: what Player X sees until Player O joins
- `templates/game.html`: the game page, with the board and score
- `templates/error.html`: the friendly page for errors like 404 (not found) and 500 (server problem)
- `static/game.js`: the script that keeps the board up to date
- `static/style.css`: all the styling, including the phone layout, dark mode and animations
- `requirements.txt`: the Python packages the app needs (just Flask)
