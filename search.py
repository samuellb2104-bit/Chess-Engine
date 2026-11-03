import random

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
    best_moves = []  # Todas las jugadas que empatan con la mejor puntuación
    best_score = -float("inf") if board.to_move == WHITE else float("inf")

    legal_moves = board.get_legal_moves()
    for move in legal_moves:
        info = board.make_move(move)
        score = minimax(board, depth - 1, -float("inf"), float("inf"))
        board.unmake_move(move, info)

        if (board.to_move == WHITE and score > best_score) or (board.to_move == BLACK and score < best_score):
            best_score = score
            best_moves = [move]  # Mejor puntuación nueva: descartamos las anteriores
        elif score == best_score:
            best_moves.append(move)  # Empata con la mejor: la guardamos como alternativa

    if not best_moves:
        return None
    return random.choice(best_moves)  # Desempate aleatorio para no elegir siempre la primera generada


if __name__ == "__main__":
    board = Board()
    board.state = [[EMPTY for _ in range(8)] for _ in range(8)]
    board.state[1][0] = WHITE * PAWN     # a7
    board.state[7][4] = WHITE * KING     # e1
    board.state[2][7] = BLACK * KING     # h6
    board.to_move = WHITE
    print(find_best_move(board, 2))  
