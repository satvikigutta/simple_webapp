# app.py
# This is the main file for our two-player tic-tac-toe web app.
# Flask is a small web framework: it listens for requests from browsers
# and decides what page to send back.

from flask import Flask, render_template

# Create the Flask application. __name__ tells Flask where to find
# the "templates" folder (it looks next to this file).
app = Flask(__name__)

# All game state lives in this dictionary, in the server's memory.
# Nothing is saved to a database, so restarting the server clears every game.
# Later, each key will be a game ID and each value will hold that game's
# board, whose turn it is, and so on. It starts out empty.
games = {}


# A "route" connects a URL to a Python function.
# When someone visits the home page ("/"), Flask runs home() and
# sends back whatever it returns.
@app.route("/")
def home():
    # render_template fills in templates/index.html and returns it as HTML.
    return render_template("index.html")


# This block only runs when you start the file directly with "python app.py".
# debug=True reloads the server when you save changes and shows helpful
# error pages. Turn it off if you ever deploy this for real.
if __name__ == "__main__":
    app.run(debug=True)
