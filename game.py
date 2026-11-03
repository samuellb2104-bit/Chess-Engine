from board import Board, WHITE, BLACK, QUEEN, ROOK, BISHOP, KNIGHT  # Importamos el tablero, los colores y los tipos de pieza de promoción
from search import find_best_move  # Importamos la función que calcula la mejor jugada del bot

DIFFICULTY_DEPTH = {"easy": 1, "medium": 2, "hard": 3}  # Cada dificultad es la profundidad (en jugadas) con la que busca el bot


class Game:  # Clase que une el tablero, el humano y el bot en una sola partida
    def __init__(self, difficulty="medium"):  # Constructor: recibe la dificultad elegida (por defecto "medium")
        if difficulty not in DIFFICULTY_DEPTH:  # Si la dificultad no es una de las tres válidas...
            raise ValueError(f"Dificultad desconocida: {difficulty}")  # ...avisamos con un error claro en vez de fallar más tarde
        self.board = Board()  # Creamos el tablero en la posición inicial
        self.depth = DIFFICULTY_DEPTH[difficulty]  # Guardamos la profundidad de búsqueda que corresponde a la dificultad
        self.human_color = WHITE  # El humano juega con blancas
        self.bot_color = BLACK  # El bot juega con negras (el color contrario)

    def human_move(self, start_row, start_col, end_row, end_col, promotion=None):  # Intenta aplicar la jugada del humano
        if self.is_over():  # Si la partida ya terminó...
            return False  # ...no se puede mover: devolvemos False
        if self.board.to_move != self.human_color:  # Si no es el turno del humano...
            return False  # ...rechazamos la jugada
        candidates = []  # Lista de jugadas legales que coinciden con las casillas pedidas
        for move in self.board.get_legal_moves():  # Recorremos todas las jugadas legales actuales
            if (move.start_row == start_row and move.start_col == start_col  # ¿Misma casilla de origen?
                    and move.end_row == end_row and move.end_col == end_col):  # ¿Y misma casilla de destino?
                candidates.append(move)  # Es candidata (una promoción genera 4 candidatas con el mismo origen/destino)
        if not candidates:  # Si ninguna jugada legal coincide...
            return False  # ...la jugada es ilegal: devolvemos False
        chosen = None  # Aquí guardaremos la jugada definitiva
        if promotion is not None:  # Si el usuario indicó pieza de promoción...
            for move in candidates:  # ...buscamos entre las candidatas
                if move.promotion == promotion:  # ...la que promociona a esa pieza
                    chosen = move  # La elegimos
        else:  # Si no indicó promoción...
            chosen = candidates[0]  # ...tomamos la primera candidata (si no es promoción, solo hay una)
            for move in candidates:  # Pero si hay varias (es una promoción)...
                if move.promotion == QUEEN:  # ...preferimos coronar a dama por defecto
                    chosen = move  # Elegimos la de dama
        if chosen is None:  # Si indicó una promoción que no existe entre las candidatas...
            return False  # ...rechazamos la jugada
        self.board.make_move(chosen)  # Aplicamos EXACTAMENTE el objeto legal encontrado (trae enroque/al paso bien marcados)
        return True  # Informamos de que la jugada se hizo

    def bot_move(self):  # Hace que el bot elija y juegue su jugada
        if self.is_over():  # Si la partida terminó...
            return None  # ...no hay jugada que hacer
        if self.board.to_move != self.bot_color:  # Si no es el turno del bot...
            return None  # ...no hace nada
        move = find_best_move(self.board, self.depth)  # Buscamos la mejor jugada con la profundidad de la dificultad
        if move is None:  # Por seguridad: si no hay jugada (no debería pasar si la partida sigue)...
            return None  # ...devolvemos None
        self.board.make_move(move)  # Aplicamos la jugada del bot al tablero
        return move  # Devolvemos la jugada (la web la usará para mostrarla)

    def get_state(self):  # Devuelve el estado de la partida: "checkmate", "check", "stalemate" u "ongoing"
        return self.board.get_game_state()  # Delegamos en el tablero

    def is_over(self):  # ¿Terminó la partida?
        return self.get_state() in ("checkmate", "stalemate")  # Termina con jaque mate o ahogado


def parse_move(text):  # Convierte texto tipo "e2e4" o "a7a8q" en números (solo para jugar por terminal)
    text = text.strip().lower()  # Quitamos espacios y pasamos a minúsculas
    if len(text) not in (4, 5):  # Debe tener 4 caracteres (o 5 si lleva promoción)
        return None  # Formato inválido
    start_col = ord(text[0]) - ord("a")  # Letra de columna -> 0..7 (a=0)
    start_row = 8 - int(text[1]) if text[1].isdigit() else -1  # Número de rango -> fila (rango 8 = fila 0, rango 1 = fila 7)
    end_col = ord(text[2]) - ord("a")  # Columna de destino
    end_row = 8 - int(text[3]) if text[3].isdigit() else -1  # Fila de destino
    promotion = None  # Por defecto, sin promoción
    if len(text) == 5:  # Si hay quinto carácter...
        promotion = {"q": QUEEN, "r": ROOK, "b": BISHOP, "n": KNIGHT}.get(text[4])  # ...lo traducimos a tipo de pieza
        if promotion is None:  # Si la letra no es q/r/b/n...
            return None  # ...formato inválido
    for value in (start_row, start_col, end_row, end_col):  # Comprobamos que todas las coordenadas estén en 0..7
        if not 0 <= value <= 7:  # Si alguna se sale del tablero...
            return None  # ...formato inválido
    return start_row, start_col, end_row, end_col, promotion  # Devolvemos la tupla lista para human_move


if __name__ == "__main__":  # Esto solo se ejecuta al lanzar `python game.py`, no al importarlo
    level = input("Dificultad (easy/medium/hard): ").strip().lower()  # Pedimos la dificultad
    game = Game(level if level in DIFFICULTY_DEPTH else "medium")  # Creamos la partida (medium si escribe algo raro)
    while not game.is_over():  # Bucle principal: mientras la partida siga
        game.board.print_board()  # Dibujamos el tablero
        if game.board.to_move == game.human_color:  # Turno del humano
            parsed = parse_move(input("Tu jugada (ej. e2e4, a7a8q): "))  # Leemos y convertimos su jugada
            if parsed is None or not game.human_move(*parsed):  # Si el formato es malo o la jugada es ilegal...
                print("Jugada inválida, prueba otra.")  # ...avisamos
                continue  # ...y volvemos a pedir jugada sin cambiar de turno
        else:  # Turno del bot
            print("El bot piensa...")  # Aviso porque en "hard" puede tardar
            print("El bot juega:", game.bot_move())  # El bot juega y mostramos su jugada (usa Move.__str__)
    game.board.print_board()  # Tablero final
    print("Fin de la partida:", game.get_state())  # Mostramos "checkmate" o "stalemate"

    # Pruebas sugeridas (salida esperada):
    # 1) python game.py, "easy", jugar e2e4  -> el tablero muestra el peón en e4 y el bot responde con una jugada legal
    # 2) Escribir e2e5 (ilegal)              -> "Jugada inválida, prueba otra." y sigue siendo tu turno
    # 3) Escribir "hola"                     -> "Jugada inválida, prueba otra."
    # 4) Jugar f2f3, e7e5, g2g4 y esperar d8h4 del bot en "medium"/"hard" -> mate del loco, "Fin de la partida: checkmate"
