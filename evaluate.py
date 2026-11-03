from board import Board, EMPTY, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

PIECE_VALUES = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 0,
}

# Tablas de valor por casilla, vistas desde las blancas.
# Fila 0 = rango 8, fila 7 = rango 1 (igual que board.state), así que se leen como un tablero visto desde arriba.
# Valores en centipeones: positivo = casilla buena para esa pieza, negativo = casilla mala.
PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],      # Peones a punto de coronar
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],            # Premia ocupar el centro (d4/e4)
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],      # Penaliza dejar d2/e2 sin mover
    [0, 0, 0, 0, 0, 0, 0, 0],
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],  # El caballo en el borde vale poco
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],        # Torre en la séptima fila
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]

QUEEN_TABLE = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]

# Rey de medio juego: lo quiere escondido en las esquinas. No hay tabla de final de partida todavía.
KING_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]

PIECE_TABLES = {
    PAWN: PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    BISHOP: BISHOP_TABLE,
    ROOK: ROOK_TABLE,
    QUEEN: QUEEN_TABLE,
    KING: KING_TABLE,
}


def evaluate(board):
    """Material + posición: positivo favorece a las blancas, negativo a las negras."""
    score = 0

    for row in range(8):
        for col in range(8):
            piece = board.state[row][col]

            if piece == EMPTY:
                continue

            piece_type = board.piece_type(piece)
            color = board.piece_color(piece)

            # Las tablas están escritas desde las blancas. Para las negras se voltea la fila (7 - row).
            table_row = row if color == 1 else 7 - row
            positional = PIECE_TABLES[piece_type][table_row][col]

            score += (PIECE_VALUES[piece_type] + positional) * color

    return score


if __name__ == "__main__":
    board = Board()
    print(evaluate(board))          # 0     (material igualado)

    board.state[0][3] = EMPTY       # quitar la dama negra (d8)
    print(evaluate(board))          # 895   (dama de más, menos 5 por el bonus posicional de la dama negra)

    board.state[7][0] = EMPTY       # quitar la torre blanca (a1)
    print(evaluate(board))          # 395   (895 - 500, torre a1 en su casilla vale 500 + 0)

    board.state[6][4] = EMPTY       # quitar el peón blanco de e2
    print(evaluate(board))          # 315   (395 - 100 + 20: quitar el peón e2 quita su penalización de -20)