import time
import uuid

from flask import Flask, jsonify, request, send_from_directory

from board import QUEEN
from game import Game, DIFFICULTY_DEPTH

app = Flask(__name__, static_folder="web", static_url_path="")

# game_id -> Game (una partida por jugador, en memoria)
games = {}

# Sin esto el diccionario crecería para siempre en el servidor
GAME_TTL_SECONDS = 2 * 60 * 60  # una partida sin actividad durante 2 horas se borra
MAX_GAMES = 500                 # tope de partidas a la vez


def purge_games():
    now = time.time()
    for game_id in [gid for gid, g in games.items() if now - g.last_used > GAME_TTL_SECONDS]:
        del games[game_id]
    # Si aun así se llena, se descartan las menos usadas
    while len(games) >= MAX_GAMES:
        oldest = min(games, key=lambda gid: games[gid].last_used)
        del games[oldest]


def error(message, status=400):
    return jsonify({"error": message}), status


def get_game():
    data = request.get_json(silent=True) or {}
    # El id viene en el cuerpo (POST) o en la URL (GET)
    game_id = data.get("game_id") or request.args.get("game_id")
    game = games.get(game_id)
    if game is not None:
        game.last_used = time.time()
    return game_id, game


def serialize(game_id, game, human_move=None, bot_move=None):
    board = game.board
    over = game.is_over()
    human_turn = board.to_move == game.human_color
    legal = [str(m) for m in board.get_legal_moves()] if (human_turn and not over) else []
    last = bot_move or human_move
    return {
        "game_id": game_id,
        "board": board.state,
        "to_move": board.to_move,
        "state": game.get_state(),
        "game_over": over,
        "human_color": game.human_color,
        "legal_moves": legal,
        "human_move": str(human_move) if human_move else None,
        "bot_move": str(bot_move) if bot_move else None,
        "last_move": str(last) if last else None,
    }


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/api/new", methods=["POST"])
def new_game():
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", "medium")
    if difficulty not in DIFFICULTY_DEPTH:
        return error("Dificultad inválida")
    purge_games()
    game_id = uuid.uuid4().hex
    games[game_id] = Game(difficulty)
    games[game_id].last_used = time.time()
    return jsonify(serialize(game_id, games[game_id]))


@app.route("/api/state", methods=["GET"])
def state():
    game_id, game = get_game()
    if game is None:
        return error("Partida no encontrada", 404)
    return jsonify(serialize(game_id, game))


@app.route("/api/move", methods=["POST"])
def move():
    game_id, game = get_game()
    if game is None:
        return error("Partida no encontrada", 404)
    data = request.get_json(silent=True) or {}
    try:
        start_row, start_col = data["from"]
        end_row, end_col = data["to"]
    except (KeyError, TypeError, ValueError):
        return error("Formato inválido: usa {'from': [fila, col], 'to': [fila, col]}")
    promotion = data.get("promotion")

    # Localizamos la jugada antes de aplicarla para poder devolverla como texto
    human = None
    for m in game.board.get_legal_moves():
        if (m.start_row, m.start_col, m.end_row, m.end_col) == (start_row, start_col, end_row, end_col):
            human = m
            break
    if not game.human_move(start_row, start_col, end_row, end_col, promotion):
        return error("Jugada ilegal")
    if human is not None and human.promotion is not None:
        human.promotion = promotion or QUEEN  # Mismo valor por defecto que human_move

    bot = game.bot_move()
    return jsonify(serialize(game_id, game, human, bot))


if __name__ == "__main__":
    # 0.0.0.0 permite que tus amigos de la red local se conecten
    app.run(host="0.0.0.0", port=5000, debug=False)

    # Pruebas sugeridas (con el servidor en marcha, en otra terminal):
    # curl -X POST localhost:5000/api/new -H "Content-Type: application/json" -d "{\"difficulty\":\"easy\"}"
    #   -> JSON con game_id, board inicial, state "ongoing", 20 legal_moves
    # curl -X POST localhost:5000/api/move -H "Content-Type: application/json" -d "{\"game_id\":\"<id>\",\"from\":[6,4],\"to\":[4,4]}"
    #   -> human_move "e2e4", bot_move con una jugada negra, to_move 1
    # Mismo move con "to":[3,4] (e2e5)  -> {"error": "Jugada ilegal"} con código 400
    # curl "localhost:5000/api/state?game_id=inventado"  -> {"error": "Partida no encontrada"} con código 404
