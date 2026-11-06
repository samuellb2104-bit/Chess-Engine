const FILES = "abcdefgh";

const STATUS_TEXT = {
  ongoing: "Tu turno",
  check: "¡Jaque!",
  checkmate: "Jaque mate",
  stalemate: "Tablas por ahogado",
};

const LEVEL_NAME = { easy: "Aprendiz", medium: "Jugador", hard: "Maestro" };

const startScreen = document.getElementById("start-screen");
const gameScreen = document.getElementById("game-screen");
const statusEl = document.getElementById("status");
const botLabel = document.getElementById("bot-label");
const menuItems = [...document.querySelectorAll("#menu li")];

let gameId = null;
let game = null;       // último estado recibido del servidor
let selected = null;   // casilla seleccionada, como "e2"
let busy = false;      // true mientras esperamos al servidor (el bot piensa)
let menuIndex = 1;     // opción del menú resaltada (empieza en "Jugador")

// "e2" <-> [fila, col]
const squareName = (row, col) => FILES[col] + (8 - row);
const toRowCol = (sq) => [8 - Number(sq[1]), FILES.indexOf(sq[0])];

async function api(url, body) {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Error del servidor");
  return data;
}

/* ---------- Menú ---------- */

function setMenuIndex(index) {
  menuIndex = (index + menuItems.length) % menuItems.length;
  menuItems.forEach((item, i) => item.classList.toggle("active", i === menuIndex));
  // El tema (colores del tablero y acento) cambia mientras eliges: sirve de vista previa
  document.body.dataset.theme = menuItems[menuIndex].dataset.difficulty;
}

menuItems.forEach((item, i) => {
  item.addEventListener("mouseenter", () => setMenuIndex(i));
  item.addEventListener("focus", () => setMenuIndex(i));
  item.addEventListener("click", () => newGame(item.dataset.difficulty));
});

document.addEventListener("keydown", (event) => {
  if (!startScreen.hidden) {
    if (event.key === "ArrowDown") { setMenuIndex(menuIndex + 1); event.preventDefault(); }
    if (event.key === "ArrowUp") { setMenuIndex(menuIndex - 1); event.preventDefault(); }
    if (event.key === "Enter") newGame(menuItems[menuIndex].dataset.difficulty);
  } else if (event.key === "Escape") {
    backToMenu();
  }
});

function backToMenu() {
  gameScreen.hidden = true;
  startScreen.hidden = false;
  setMenuIndex(menuIndex);
}

/* ---------- Partida ---------- */

async function newGame(difficulty) {
  game = await api("/api/new", { difficulty });
  gameId = game.game_id;
  selected = null;
  document.body.dataset.theme = difficulty;
  botLabel.textContent = "Bot · " + LEVEL_NAME[difficulty];
  startScreen.hidden = true;
  gameScreen.hidden = false;
  Board3D.setTheme();
  Board3D.resize();
  render();
}

// Jugadas legales que salen de la casilla seleccionada -> casillas destino
function targetsFrom(square) {
  return game.legal_moves
    .filter((m) => m.startsWith(square))
    .map((m) => m.slice(2, 4));
}

function renderMarkers() {
  const targets = selected ? targetsFrom(selected) : [];
  const last = game.last_move ? [game.last_move.slice(0, 2), game.last_move.slice(2, 4)] : [];

  // Un destino con pieza rival es una captura: se dibuja con anillo en vez de punto
  const isCapture = (sq) => {
    const [row, col] = toRowCol(sq);
    return game.board[row][col] !== 0;
  };

  Board3D.setMarkers({
    selected: selected ? toRowCol(selected) : null,
    last: last.map(toRowCol),
    targets: targets.filter((sq) => !isCapture(sq)).map(toRowCol),
    captures: targets.filter(isCapture).map(toRowCol),
  });
}

function renderStatus(text) {
  statusEl.textContent = text ?? STATUS_TEXT[game.state];
}

// Redibuja todo desde el estado del servidor
function render() {
  Board3D.setPosition(game.board);
  renderMarkers();
  renderStatus();
}

async function onSquareClick(row, col) {
  if (!game || busy || game.game_over) return;
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
  renderMarkers();
}

const MIN_THINK_MS = 450; // pausa mínima antes de que el bot mueva, para que se note el cambio de turno
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function playMove(from, to) {
  const previous = game;
  busy = true;
  selected = null;
  Board3D.setMarkers({});
  renderStatus("");

  // La petición sale ya; mientras tanto se anima tu jugada sin esperar al servidor
  const request = api("/api/move", { game_id: gameId, from: toRowCol(from), to: toRowCol(to) });
  request.catch(() => {}); // el error se gestiona más abajo; esto evita avisos mientras animamos

  try {
    await Board3D.animateMove(from + to);
    renderStatus("El bot piensa…");
    const [response] = await Promise.all([request, sleep(MIN_THINK_MS)]);
    game = response;
    if (game.bot_move) await Board3D.animateMove(game.bot_move);
  } catch (err) {
    alert(err.message);
    game = previous; // vuelve a la posición anterior
  }

  busy = false;
  render(); // sincroniza con el estado real del servidor
}

document.getElementById("new-game").addEventListener("click", backToMenu);

// El tablero 3D da dos candidatos por toque: la pieza tocada y la casilla del suelo bajo el dedo.
// Una pieza alta tapa visualmente la casilla de detrás, así que con una pieza seleccionada
// se prefiere el candidato que sea un destino legal.
function onBoardTap({ piece, plane }) {
  const isTarget = (sq) => sq && selected && targetsFrom(selected).includes(squareName(sq[0], sq[1]));
  const pick = isTarget(piece) ? piece : isTarget(plane) ? plane : piece || plane;
  if (pick) onSquareClick(pick[0], pick[1]);
}

Board3D.init(document.getElementById("board3d"), onBoardTap);
setMenuIndex(menuIndex);
