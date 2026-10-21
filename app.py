# app.py
# This is the main file for our two-player tic-tac-toe web app.
# Flask is a small web framework: it listens for requests from browsers
# and decides what page to send back.

# "secrets" makes random values that are hard to guess, which is what we
# want for game codes and player tokens. "string" gives us the alphabet.
import secrets
import string
# "threading" gives us a Lock (explained below where we create it).
import threading

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
# HTTPException is the parent of all of Flask's HTTP errors (404, 403, ...).
from werkzeug.exceptions import HTTPException

# Create the Flask application. __name__ tells Flask where to find
# the "templates" folder (it looks next to this file).
app = Flask(__name__)

# All game state lives in this dictionary, in the server's memory.
# Nothing is saved to a database, so restarting the server clears every game.
# Each key is a game code (like "ABCD"), and each value is another
# dictionary describing that game, for example:
#
#   games["ABCD"] = {
#       "x_token": "k3J9...",  # Player X's secret token
#       "o_token": None,       # Player O's secret token (None until they join)
#       "board": ["X", "", "O", "", "", "", "", "", ""],
#       "first": "X",          # who started this round (players take turns starting)
#       "turn": "X",           # whose turn it is: "X" or "O"
#       "result": None,        # None while playing, then "X", "O", or "draw"
#       "winning_line": None,  # the 3 winning squares, like [0, 4, 8], once someone wins
#       "last_move": 2,        # the square played most recently (so the page can animate it)
#       "score": {"X": 0, "O": 0, "draw": 0},  # running totals across rounds
#   }
#
# The board is a list of 9 squares, numbered like this:
#
#    0 | 1 | 2
#   ---+---+---
#    3 | 4 | 5
#   ---+---+---
#    6 | 7 | 8
#
# Each square holds "X", "O", or "" (empty).
games = {}

# Flask can handle several requests at the same time. If two moves arrive at
# once (say, a player double-clicks), both could pass the "is it your turn?"
# check before either one is saved. A Lock lets only one request change the
# games dictionary at a time, so that can't happen.
games_lock = threading.Lock()

# How many letters go in a game code.
CODE_LENGTH = 4

# Every set of three squares that wins the game: 3 rows, 3 columns, 2 diagonals.
WINNING_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def make_game_code():
    """Return a new random code like "QXRT" that no current game is using."""
    while True:
        code = "".join(secrets.choice(string.ascii_uppercase) for _ in range(CODE_LENGTH))
        # In the rare case the code is already taken, loop and try again.
        if code not in games:
            return code


def make_token():
    """Return a secret random string that identifies one player."""
    # token_urlsafe gives letters, numbers, "-" and "_", so it's safe to put in a URL.
    return secrets.token_urlsafe(8)


def find_player(game, token):
    """Return "X" or "O" for the player with this token, or None if it matches neither."""
    if token == game["x_token"]:
        return "X"
    if token == game["o_token"]:
        return "O"
    return None


def find_winning_line(board):
    """Return the 3 winning squares (like [0, 4, 8]) if someone has won, or None."""
    for a, b, c in WINNING_LINES:
        # Three matching, non-empty squares in a line means that symbol won.
        if board[a] != "" and board[a] == board[b] == board[c]:
            return [a, b, c]
    return None


def start_round(game, first):
    """Clear the board for a new round, with `first` ("X" or "O") moving first.

    The players and the score are left alone.
    """
    game["board"] = [""] * 9  # 9 empty squares
    game["first"] = first
    game["turn"] = first
    game["result"] = None
    game["winning_line"] = None
    game["last_move"] = None


def show_game(code, game, player, error=None, status=200):
    """Render the right page for this game and player."""
    token = game["x_token"] if player == "X" else game["o_token"]

    # Player X waits here until someone joins as Player O.
    if game["o_token"] is None:
        return render_template("waiting.html", code=code, token=token), status

    return render_template(
        "game.html",
        code=code,
        token=token,
        player=player,
        board=game["board"],
        turn=game["turn"],
        result=game["result"],
        winning_line=game["winning_line"] or [],
        last_move=game["last_move"],
        score=game["score"],
        error=error,
    ), status


# A "route" connects a URL to a Python function.
# When someone visits the home page ("/"), Flask runs home() and
# sends back whatever it returns.
@app.route("/")
def home():
    # render_template fills in templates/index.html and returns it as HTML.
    return render_template("index.html")


# methods=["POST"] means this route only answers form submissions,
# not someone just typing the URL into their browser.
@app.route("/create", methods=["POST"])
def create_game():
    x_token = make_token()

    with games_lock:
        code = make_game_code()
        # Save the new game. Nobody is Player O yet.
        games[code] = {
            "x_token": x_token,
            "o_token": None,
            "score": {"X": 0, "O": 0, "draw": 0},
        }
        # Set up the empty board. X goes first in the first round.
        start_round(games[code], first="X")

    # Send Player X to their own private game page.
    return redirect(url_for("game_page", code=code, token=x_token))


@app.route("/join", methods=["POST"])
def join_game():
    # request.form holds what the user typed into the form.
    # .strip() removes extra spaces and .upper() lets people type "abcd".
    code = request.form.get("code", "").strip().upper()

    # If something is wrong, show the home page again with an error message.
    # We also pass back what they typed, so the box isn't wiped clean.
    # The number after the template (400, 404) is the HTTP status code.
    if code == "":
        return render_template("index.html", error="Please enter a game code."), 400

    # A real code is exactly 4 letters A-Z. isascii() rules out letters
    # like "É" that isalpha() would otherwise accept.
    if len(code) != CODE_LENGTH or not (code.isascii() and code.isalpha()):
        return render_template("index.html", code=code,
                               error=f"Game codes are {CODE_LENGTH} letters, like ABCD."), 400

    with games_lock:
        game = games.get(code)

        if game is None:
            return render_template("index.html", code=code,
                                   error=f"There's no game with the code {code}. Check it and try again."), 404
        if game["o_token"] is not None:
            return render_template("index.html", code=code,
                                   error=f"Game {code} already has two players. Ask your friend for a new code."), 400

        # The game exists and has a free spot, so this person becomes Player O.
        o_token = make_token()
        game["o_token"] = o_token

    return redirect(url_for("game_page", code=code, token=o_token))


# The parts in <angle brackets> are filled in from the URL, so visiting
# /game/ABCD/k3J9... calls game_page(code="ABCD", token="k3J9...").
@app.route("/game/<code>/<token>")
def game_page(code, token):
    game = games.get(code)
    if game is None:
        abort(404)  # Show a "Not Found" page.

    player = find_player(game, token)
    if player is None:
        abort(403)  # The token doesn't match either player: "Forbidden".

    return show_game(code, game, player)


# This route returns data instead of a web page. The JavaScript in
# static/game.js calls it every second to see whether the board has changed.
@app.route("/api/game/<code>")
def api_game(code):
    game = games.get(code)
    if game is None:
        # Reply in JSON too, so the script can read the error.
        return jsonify(error="Game not found"), 404

    # jsonify turns a Python dictionary into JSON text, e.g.
    # {"board": ["X", "", ...], "turn": "O", "result": null, ...}
    # We send only what the page needs. The tokens stay secret on the server.
    return jsonify(
        board=game["board"],
        turn=game["turn"],
        result=game["result"],
        winning_line=game["winning_line"],
        score=game["score"],
    )


@app.route("/game/<code>/<token>/move", methods=["POST"])
def make_move(code, token):
    game = games.get(code)
    if game is None:
        abort(404)

    player = find_player(game, token)
    if player is None:
        abort(403)

    # The clicked button sends its square number (0-8) as "square".
    # Anyone can send any value to a server, so we check it's a real square.
    square = request.form.get("square", "")
    if not square.isdigit() or int(square) > 8:
        return show_game(code, game, player, error="That isn't a square on the board.", status=400)
    square = int(square)

    with games_lock:
        # The page only lets you click when a move is allowed, but we never
        # trust the browser: someone could send a request by hand, or click
        # on an old page. So the server checks every rule itself.
        if game["o_token"] is None:
            error = "Wait for Player O to join."
        elif game["result"] is not None:
            error = "The game is already over."
        elif game["turn"] != player:
            error = f"It's not your turn. Wait for Player {game['turn']} to move."
        elif game["board"][square] != "":
            error = "That square is already taken."
        else:
            error = None
            # The move is allowed, so place the symbol.
            game["board"][square] = player
            game["last_move"] = square

            # Did that move win the game, or fill the board?
            line = find_winning_line(game["board"])
            if line:
                game["result"] = player
                game["winning_line"] = line
                game["score"][player] += 1
            elif "" not in game["board"]:
                game["result"] = "draw"
                game["score"]["draw"] += 1

            # Hand the turn to the other player.
            game["turn"] = "O" if player == "X" else "X"

    if error:
        return show_game(code, game, player, error=error, status=400)

    # After a successful form submission, redirect back to the game page.
    # That way, refreshing the page doesn't send the same move again.
    return redirect(url_for("game_page", code=code, token=token))


@app.route("/game/<code>/<token>/play-again", methods=["POST"])
def play_again(code, token):
    game = games.get(code)
    if game is None:
        abort(404)

    if find_player(game, token) is None:
        abort(403)

    with games_lock:
        # Only reset a finished game. If both players click "Play again" at
        # the same moment, the first click starts the new round and the
        # second one finds a game in progress, so it does nothing. Without
        # this check, the second click could wipe out moves in the new round.
        if game["result"] is not None:
            # Take turns going first: whoever didn't start last round starts this one.
            start_round(game, first="O" if game["first"] == "X" else "X")

    return redirect(url_for("game_page", code=code, token=token))


# ----- Error pages -----
# When something goes wrong, Flask raises an HTTP error, for example
# abort(404) above, or a URL that doesn't match any route. These
# "error handlers" replace Flask's plain built-in error pages with our own
# page, error.html, which uses the same layout as the rest of the site.

# A friendly title and message for each kind of error we expect.
ERROR_MESSAGES = {
    403: ("This link isn't valid",
          "The player part of this game link doesn't match this game. "
          "Make sure you copied the whole link."),
    404: ("Page not found",
          "We couldn't find that game or page. The code may be wrong, "
          "or the server may have restarted (which clears all games)."),
    405: ("That didn't work",
          "This page only works when you use the buttons on the site."),
    500: ("Something went wrong",
          "The server ran into a problem. Please go back and try again."),
}


# HTTPException covers every HTTP error (403, 404, 405, ...), so this one
# function handles them all.
@app.errorhandler(HTTPException)
def handle_http_error(error):
    # Use our message if we wrote one for this error, or Flask's name for it if not.
    title, message = ERROR_MESSAGES.get(error.code, (error.name, "Please go back and try again."))
    return render_template("error.html", title=title, message=message), error.code


# A 500 error means a bug in our code raised a Python exception. Flask logs
# the full traceback in the terminal for us to fix, and this handler shows
# the player a friendly page instead of the traceback.
@app.errorhandler(500)
def handle_server_error(error):
    title, message = ERROR_MESSAGES[500]
    return render_template("error.html", title=title, message=message), 500


# This block only runs when you start the file directly with "python app.py".
# debug=True reloads the server when you save changes and shows helpful
# error pages. Turn it off if you ever deploy this for real.
# Note: in debug mode, a Python error shows the traceback in the browser
# (useful while you're coding) instead of our friendly 500 page.
if __name__ == "__main__":
    app.run(debug=True)
