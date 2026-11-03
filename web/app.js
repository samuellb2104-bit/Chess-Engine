const FILES = "abcdefgh";

// Piezas con signo (blancas positivas) -> símbolo Unicode
const SYMBOLS = {
  1: "♙", 2: "♘", 3: "♗", 4: "♖", 5: "♕", 6: "♔",
  "-1": "♟", "-2": "♞", "-3": "♝", "-4": "♜", "-5": "♛", "-6": "♚",
};

const STATUS_TEXT = {
  ongoing: "",
  check: "¡Jaque!",
  checkmate: "Jaque mate",
  stalemate: "Tablas por ahogado",
};

const startScreen = document.getElementById("start-screen");
const gameScreen = document.getElementById("game-screen");
const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");

let gameId = null;
let game = null;       // último estado recibido del servidor
let selected = null;   // casilla seleccionada, como "e2"
let busy = false;      // true mientras esperamos al servidor (el bot piensa)

function squareName(row, col) {
  return FILES[col] + (8 - row);
}

async function api(url, body) {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Error del servidor");
  return data;
}

async function newGame(difficulty) {
  game = await api("/api/new", { difficulty });
  gameId = game.game_id;
  selected = null;
  startScreen.hidden = true;
  gameScreen.hidden = false;
  render();
}

// Jugadas legales que salen de la casilla seleccionada -> casillas destino
function targetsFrom(square) {
  return game.legal_moves
    .filter((m) => m.startsWith(square))
    .map((m) => m.slice(2, 4));
}

function render() {
  boardEl.innerHTML = "";
  const targets = selected ? targetsFrom(selected) : [];
  const last = game.last_move;

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const name = squareName(row, col);
      const square = document.createElement("div");
      square.className = "square " + ((row + col) % 2 === 0 ? "light" : "dark");
      if (last && (name === last.slice(0, 2) || name === last.slice(2, 4))) square.classList.add("last-move");
      if (name === selected) square.classList.add("selected");
      if (targets.includes(name)) square.classList.add("target");
      square.textContent = SYMBOLS[game.board[row][col]] || "";
      square.addEventListener("click", () => onSquareClick(row, col));
      boardEl.appendChild(square);
    }
  }

  if (busy) statusEl.textContent = "El bot piensa...";
  else statusEl.textContent = game.game_over ? STATUS_TEXT[game.state] : (STATUS_TEXT[game.state] || "Tu turno");
}

async function onSquareClick(row, col) {
  if (busy || game.game_over) return;
  const name = squareName(row, col);
  const piece = game.board[row][col];

  // Clic en un destino válido: mover
  if (selected && targetsFrom(selected).includes(name)) {
    await playMove(selected, name);
    return;
  }

  // Clic en una pieza propia: seleccionarla (o deseleccionar si ya lo estaba)
  if (piece * game.human_color > 0) {
    selected = name === selected ? null : name;
  } else {
    selected = null;
  }
  render();
}

async function playMove(from, to) {
  // El servidor usa [fila, col]
  const toCoords = (sq) => [8 - Number(sq[1]), FILES.indexOf(sq[0])];
  busy = true;
  selected = null;
  render();
  try {
    game = await api("/api/move", { game_id: gameId, from: toCoords(from), to: toCoords(to) });
  } catch (err) {
    alert(err.message);
  }
  busy = false;
  render();
}

document.querySelectorAll("[data-difficulty]").forEach((button) => {
  button.addEventListener("click", () => newGame(button.dataset.difficulty));
});

document.getElementById("new-game").addEventListener("click", () => {
  gameScreen.hidden = true;
  startScreen.hidden = false;
});
