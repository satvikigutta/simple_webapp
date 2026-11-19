# tests/test_app.py
# Automated tests for the tic-tac-toe app. Run them with:  pytest -v
#
# Flask's "test client" acts like a fake browser: it sends requests straight
# to app.py without starting a real server, so the tests run in a second.

import pytest

from app import app, find_winning_line, games


@pytest.fixture
def client():
    """Give each test a fresh fake browser and an empty games dictionary."""
    app.config["TESTING"] = True
    games.clear()  # start every test with no games, so tests can't affect each other
    with app.test_client() as c:
        yield c


def start_game(client):
    """Create a game and have a second player join it.

    Returns the game code and the two players' tokens.
    """
    client.post("/create")
    code = next(iter(games))  # the only game in the dictionary
    client.post("/join", data={"code": code.lower()})  # lowercase works too
    game = games[code]
    return code, game["x_token"], game["o_token"]


# ---------- Test 1: the home page loads ----------

def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Create game" in response.data
    assert b"Join a friend" in response.data


# ---------- Test 2: win detection ----------

def test_find_winning_line_spots_rows_columns_and_diagonals():
    assert find_winning_line(["X", "X", "X", "", "", "", "", "", ""]) == [0, 1, 2]
    assert find_winning_line(["O", "", "", "O", "", "", "O", "", ""]) == [0, 3, 6]
    assert find_winning_line(["", "", "X", "", "X", "", "X", "", ""]) == [2, 4, 6]
    assert find_winning_line([""] * 9) is None


# ---------- Test 3: creating and joining a game ----------

def test_create_then_join_game(client):
    # Creating a game sends Player X to the waiting page.
    response = client.post("/create", follow_redirects=True)
    assert b"Waiting for Player O to join" in response.data

    code = next(iter(games))
    assert len(code) == 4

    # A second player joins with the code and lands on the game board.
    response = client.post("/join", data={"code": code}, follow_redirects=True)
    assert response.status_code == 200
    assert games[code]["o_token"] is not None


# ---------- Test 4: bad game codes get a helpful error ----------

def test_join_with_bad_code_shows_error(client):
    response = client.post("/join", data={"code": "ZZZZ"})
    assert response.status_code == 404
    assert b"no game with the code ZZZZ" in response.data

    response = client.post("/join", data={"code": "AB1"})
    assert response.status_code == 400


# ---------- Test 5: the server enforces turns ----------

def test_cannot_move_out_of_turn_or_on_taken_square(client):
    code, x, o = start_game(client)

    # O tries to go first: rejected.
    response = client.post(f"/game/{code}/{o}/move", data={"square": "0"})
    assert response.status_code == 400
    assert games[code]["board"][0] == ""

    # X plays square 0, then O tries the same square: rejected.
    client.post(f"/game/{code}/{x}/move", data={"square": "0"})
    response = client.post(f"/game/{code}/{o}/move", data={"square": "0"})
    assert response.status_code == 400
    assert games[code]["board"][0] == "X"


# ---------- Test 6: a full game, start to win ----------

def test_full_game_x_wins_and_score_updates(client):
    code, x, o = start_game(client)

    # X takes the top row while O plays the middle row.
    for token, square in [(x, 0), (o, 3), (x, 1), (o, 4), (x, 2)]:
        client.post(f"/game/{code}/{token}/move", data={"square": str(square)})

    state = client.get(f"/api/game/{code}").get_json()
    assert state["result"] == "X"
    assert state["winning_line"] == [0, 1, 2]
    assert state["score"]["X"] == 1
    # The API must never leak the players' secret tokens.
    assert x not in str(state) and o not in str(state)


# ---------- Test 7: a stranger's token is refused ----------

def test_wrong_token_is_forbidden(client):
    code, x, o = start_game(client)
    response = client.get(f"/game/{code}/not-a-real-token")
    assert response.status_code == 403
