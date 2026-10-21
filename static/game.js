// game.js
// Keeps the game page up to date without reloading it.
// Every second, it asks the server for the game state (as JSON) and
// redraws the board, the status message, and the score.

// Find the parts of the page we need to update.
const board = document.getElementById("board");
const buttons = board.querySelectorAll("button");
const statusLine = document.getElementById("status");
const roundOver = document.getElementById("round-over");
const scoreX = document.getElementById("score-x");
const scoreO = document.getElementById("score-o");
const scoreDraw = document.getElementById("score-draw");
// The "not your turn"-style message. It's only on the page after a rejected
// move, so this can be null.
const errorBox = document.getElementById("error");

// The board and result from the last check, joined into one string, so we
// can tell when something changes. null means we haven't checked yet.
let lastSeen = null;

// game.html put these values on the board in data-... attributes.
const me = board.dataset.player;          // "X" or "O"
const stateUrl = board.dataset.stateUrl;  // e.g. "/api/game/ABCD"

// How long to wait between checks, in milliseconds (1000 ms = 1 second).
const POLL_DELAY = 1000;

// Return the status message for a game state.
// These are the same messages game.html shows when the page first loads.
function statusText(state) {
  if (state.result === "draw") return "Draw";
  if (state.result) return state.result + " wins";
  if (state.turn === me) return "Your turn. Tap an empty square.";
  return "Waiting for Player " + state.turn + " to move...";
}

// Update the page to match a game state from the server.
function showState(state) {
  const myTurn = state.turn === me && state.result === null;
  // winning_line is null until someone wins. Use an empty list instead,
  // so .includes() below works either way.
  const winningLine = state.winning_line || [];

  buttons.forEach(function (button, i) {
    const symbol = state.board[i];  // "X", "O", or ""

    // If this square was empty and now has a piece, the other player just
    // played here. The "placed" class plays the pop-in animation (style.css).
    // A square that's been cleared (by "Play again") loses the class, so
    // its next piece will animate too.
    if (button.textContent === "" && symbol !== "") {
      button.classList.add("placed");
    } else if (symbol === "") {
      button.classList.remove("placed");
    }

    button.textContent = symbol;
    // Only empty squares can be clicked, and only on your turn.
    button.disabled = symbol !== "" || !myTurn;
    // classList.toggle(name, true/false) adds or removes a class.
    // "x" and "o" set the color, and "win" highlights the winning squares.
    button.classList.toggle("x", symbol === "X");
    button.classList.toggle("o", symbol === "O");
    button.classList.toggle("win", winningLine.includes(i));
  });

  statusLine.textContent = statusText(state);
  statusLine.classList.toggle("my-turn", myTurn);
  scoreX.textContent = state.score.X;
  scoreO.textContent = state.score.O;
  scoreDraw.textContent = state.score.draw;

  // Show "Play again" only when the round is over.
  roundOver.hidden = state.result === null;

  // Once the game has moved on, an old error message no longer applies.
  const now = state.board.join(",") + state.result;
  if (errorBox && lastSeen !== null && now !== lastSeen) {
    errorBox.hidden = true;
  }
  lastSeen = now;
}

// Ask the server for the latest state, update the page, then schedule
// the next check. "async" lets us use "await" to wait for the reply.
async function checkForUpdates() {
  try {
    const response = await fetch(stateUrl);

    if (response.status === 404) {
      // The server doesn't know this game any more (for example, it was
      // restarted and lost its memory). Tell the player and stop checking.
      statusLine.textContent = "This game no longer exists on the server. Go back home to start a new one.";
      buttons.forEach(function (button) { button.disabled = true; });
      roundOver.hidden = true;
      return;
    }

    if (response.ok) {
      const state = await response.json();
      showState(state);
    }
    // Any other error (like a 500) might be temporary, so we just try again.
  } catch (err) {
    // A network hiccup. Ignore it and try again next time.
    console.log("Couldn't reach the server, will retry:", err);
  }

  // Wait, then check again. We keep checking even after a round ends,
  // so we notice when the other player clicks "Play again".
  // We schedule the next check only after this one finishes, so slow
  // replies never pile up on top of each other.
  setTimeout(checkForUpdates, POLL_DELAY);
}

// Start checking right away.
checkForUpdates();
