from board import Board, WHITE, BLACK, EMPTY, KING, ROOK, PAWN
from move import Move
from evaluate import evaluate

MATE_SCORE = 100000


def minimax(board, depth, alpha, beta):
    state = board.get_game_state()

    if state == "checkmate":
        return MATE_SCORE if board.to_move == BLACK else -MATE_SCORE
    elif state == "stalemate":
        return 0

    if depth == 0:
        return evaluate(board)

    legal_moves = board.get_legal_moves()

    if board.to_move == WHITE:
        max_score = -float("inf")
        for move in legal_moves:
            info = board.make_move(move)
            score = minimax(board, depth - 1, alpha, beta)
            board.unmake_move(move, info)
            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score
    else:
        min_score = float("inf")
        for move in legal_moves:
            info = board.make_move(move)
            score = minimax(board, depth - 1, alpha, beta)
            board.unmake_move(move, info)
            min_score = min(min_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score


def find_best_move(board, depth):
    best_move = None
    best_score = -float("inf") if board.to_move == WHITE else float("inf")

    legal_moves = board.get_legal_moves()
    for move in legal_moves:
        info = board.make_move(move)
        score = minimax(board, depth - 1, -float("inf"), float("inf"))
        board.unmake_move(move, info)
        if (board.to_move == WHITE and score > best_score) or (board.to_move == BLACK and score < best_score):
            best_score = score
            best_move = move

    return best_move


if __name__ == "__main__":
    # ---------- PRUEBA 1: mate en 1 de blancas ----------
    board = Board()
    board.state = [[EMPTY for _ in range(8)] for _ in range(8)]
    board.state[0][6] = BLACK * KING     # g8
    board.state[1][5] = BLACK * PAWN     # f7
    board.state[1][6] = BLACK * PAWN     # g7
    board.state[1][7] = BLACK * PAWN     # h7
    board.state[7][6] = WHITE * KING     # g1
    board.state[7][0] = WHITE * ROOK     # a1
    board.to_move = WHITE
    print(find_best_move(board, 1))      # a1a8  (jaque mate)

    # ---------- PRUEBA 2: mate en 1 de negras ----------
    board = Board()
    board.state = [[EMPTY for _ in range(8)] for _ in range(8)]
    board.state[7][6] = WHITE * KING     # g1
    board.state[6][5] = WHITE * PAWN     # f2
    board.state[6][6] = WHITE * PAWN     # g2
    board.state[6][7] = WHITE * PAWN     # h2
    board.state[0][6] = BLACK * KING     # g8
    board.state[0][0] = BLACK * ROOK     # a8
    board.to_move = BLACK
    print(find_best_move(board, 1))      # a8a1  (jaque mate)

    # ---------- PRUEBA 3: posición inicial ----------
    board = Board()
    print(find_best_move(board, 3))      # alguna jugada (solo cuenta material)
