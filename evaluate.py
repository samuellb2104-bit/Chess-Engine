from board import Board, EMPTY, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

PIECE_VALUES = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 0,
}


def evaluate(board):
    """Returns the material score: positive favors White, negative favors Black."""
    score = 0

    for row in range(8):
        for col in range(8):
            piece = board.state[row][col]

            if piece == EMPTY:
                continue

            value = PIECE_VALUES[board.piece_type(piece)]
            score += value * board.piece_color(piece)

    return score


if __name__ == "__main__":
    board = Board()
    print(evaluate(board))          # 0     (material igualado)

    board.state[0][3] = EMPTY       # quitar la dama negra (d8)
    print(evaluate(board))          # 900   (blancas tienen una dama de más)

    board.state[7][0] = EMPTY       # quitar la torre blanca (a1)
    print(evaluate(board))          # 400   (900 - 500)

    board.state[6][4] = EMPTY       # quitar el peón blanco de e2
    print(evaluate(board))          # 300   (400 - 100)