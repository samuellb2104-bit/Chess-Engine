from board import Board, WHITE, BLACK, QUEEN, ROOK, BISHOP, KNIGHT
from search import find_best_move

# Cada dificultad es la profundidad de búsqueda del bot
DIFFICULTY_DEPTH = {"easy": 1, "medium": 2, "hard": 3}


class Game:
    def __init__(self, difficulty="medium"):
        if difficulty not in DIFFICULTY_DEPTH:
            raise ValueError(f"Dificultad desconocida: {difficulty}")
        self.board = Board()
        self.depth = DIFFICULTY_DEPTH[difficulty]
        self.human_color = WHITE
        self.bot_color = BLACK

    def human_move(self, start_row, start_col, end_row, end_col, promotion=None):
        if self.is_over() or self.board.to_move != self.human_color:
            return False

        # Una promoción genera 4 jugadas legales con las mismas casillas
        candidates = []
        for move in self.board.get_legal_moves():
            if (move.start_row == start_row and move.start_col == start_col
                    and move.end_row == end_row and move.end_col == end_col):
                candidates.append(move)
        if not candidates:
            return False

        chosen = None
        if promotion is not None:
            for move in candidates:
                if move.promotion == promotion:
                    chosen = move
        else:
            chosen = candidates[0]
            for move in candidates:
                if move.promotion == QUEEN:  # Dama por defecto al promocionar
                    chosen = move
        if chosen is None:
            return False

        # Usamos el objeto legal, no uno nuevo: trae bien marcados enroque y captura al paso
        self.board.make_move(chosen)
        return True

    def bot_move(self):
        if self.is_over() or self.board.to_move != self.bot_color:
            return None
        move = find_best_move(self.board, self.depth)
        if move is None:
            return None
        self.board.make_move(move)
        return move

    def get_state(self):
        return self.board.get_game_state()

    def is_over(self):
        return self.get_state() in ("checkmate", "stalemate")


def parse_move(text):
    # Convierte "e2e4" o "a7a8q" a números (solo para jugar por terminal)
    text = text.strip().lower()
    if len(text) not in (4, 5):
        return None
    start_col = ord(text[0]) - ord("a")
    start_row = 8 - int(text[1]) if text[1].isdigit() else -1  # Rango 8 = fila 0
    end_col = ord(text[2]) - ord("a")
    end_row = 8 - int(text[3]) if text[3].isdigit() else -1
    promotion = None
    if len(text) == 5:
        promotion = {"q": QUEEN, "r": ROOK, "b": BISHOP, "n": KNIGHT}.get(text[4])
        if promotion is None:
            return None
    for value in (start_row, start_col, end_row, end_col):
        if not 0 <= value <= 7:
            return None
    return start_row, start_col, end_row, end_col, promotion


if __name__ == "__main__":
    level = input("Dificultad (easy/medium/hard): ").strip().lower()
    game = Game(level if level in DIFFICULTY_DEPTH else "medium")
    while not game.is_over():
        game.board.print_board()
        if game.board.to_move == game.human_color:
            parsed = parse_move(input("Tu jugada (ej. e2e4, a7a8q): "))
            if parsed is None or not game.human_move(*parsed):
                print("Jugada inválida, prueba otra.")
                continue
        else:
            print("El bot piensa...")
            print("El bot juega:", game.bot_move())
    game.board.print_board()
    print("Fin de la partida:", game.get_state())

    # Pruebas sugeridas (salida esperada):
    # 1) python game.py, "easy", jugar e2e4  -> el tablero muestra el peón en e4 y el bot responde con una jugada legal
    # 2) Escribir e2e5 (ilegal)              -> "Jugada inválida, prueba otra." y sigue siendo tu turno
    # 3) Escribir "hola"                     -> "Jugada inválida, prueba otra."
    # 4) Jugar f2f3, e7e5, g2g4 y esperar d8h4 del bot en "medium"/"hard" -> mate del loco, "Fin de la partida: checkmate"
