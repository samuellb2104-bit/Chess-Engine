from move import Move
import move

# Piece types
EMPTY = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

# Sides
WHITE = 1
BLACK = -1

BACK_RANK = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]

#Directoins for sliding pieces
DIRECTIONS = {
    "bishop" : [(-1, -1), (-1, +1), (+1, -1), (+1, +1)],
    "rook" : [(-1, 0), (1, 0), (0, -1), (0, 1)],
    "queen" : [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, +1), (+1, -1), (+1, +1)]}

class Board:
    def __init__(self):
        self.to_move = WHITE

        self.castling_rights = {
            "K": True,  # White kingside
            "Q": True,  # White queenside
            "k": True,  # Black kingside
            "q": True,  # Black queenside
        }

        self.en_passant_square = None
        self.halfmove_clock = 0
        self.fullmove_number = 1

        self.setup_initial_position()

    def setup_initial_position(self):
        """Creates the standard chess starting position."""
        self.state = [[EMPTY for _ in range(8)] for _ in range(8)]

        for col, piece_type in enumerate(BACK_RANK):
            self.state[0][col] = BLACK * piece_type
            self.state[7][col] = WHITE * piece_type

        for col in range(8):
            self.state[1][col] = BLACK * PAWN
            self.state[6][col] = WHITE * PAWN

    def piece_at(self, row, col):
        """Returns the piece at the given row and column."""
        return self.state[row][col]

    def print_board(self):
        """Prints the board state with coordinates."""
        print("    a  b  c  d  e  f  g  h")

        for row_index, row in enumerate(self.state):
            rank = 8 - row_index
            print(f"{rank}  {row}  {rank}")

        print("    a  b  c  d  e  f  g  h")

    def is_inside_board(self, row, col):
        """Checks if the given row and column are within the board boundaries."""
        return 0 <= row < 8 and 0 <= col < 8

    def piece_color(self, piece):
        """Returns the color of the given piece."""
        if piece == EMPTY:
            return None
        return WHITE if piece > 0 else BLACK

    def piece_type(self, piece):
        """Returns the type of the given piece."""
        return abs(piece)

    def is_current_player_piece(self, piece):
        """Checks if the given piece belongs to the player whose turn it is."""
        return self.piece_color(piece) == self.to_move
    

    # PAWN MOVES

    def get_pawn_moves(self, row, col):
        """Returns all pseudo-legal moves for a pawn."""
        if not self.is_inside_board(row, col):
            return []

        piece = self.state[row][col]

        if piece == EMPTY or self.piece_type(piece) != PAWN:
            return []

        moves = []
        color = self.piece_color(piece)

        if color == WHITE:
            direction = -1
            start_row = 6
        else:
            direction = 1
            start_row = 1

        # One-square forward move
        next_row = row + direction

        if (
            self.is_inside_board(next_row, col)
            and self.state[next_row][col] == EMPTY
        ):
            moves.append(Move(row, col, next_row, col))

            # Two-square forward move from its initial row
            double_next_row = row + 2 * direction

            if (
                row == start_row
                and self.is_inside_board(double_next_row, col)
                and self.state[double_next_row][col] == EMPTY
            ):
                moves.append(Move(row, col, double_next_row, col))

        # Diagonal captures are checked independently:
        # a blocked pawn may still capture a rival diagonally.
        moves.extend(self.pawn_capture(row, col))

        return moves
    

    def get_pawn_double_move(self, row, col):
        """Return the two square pawn move if possible"""
        if not self.is_inside_board(row, col):
            return []

        piece = self.state[row][col]

        if piece == EMPTY or self.piece_type(piece) != PAWN:
            return []

        color = self.piece_color(piece)

        if color == WHITE:
            direction = -1
        else:
            direction = 1

        next_row = row + direction

        double_next_row = row + 2 * direction

        if not self.is_inside_board(double_next_row, col):
            return []

        if self.state[next_row][col] != EMPTY or self.state[double_next_row][col] != EMPTY:
            return []

        if (color == WHITE and row != 6) or (color == BLACK and row != 1):
            return []

        return [(double_next_row, col)]

    def pawn_capture(self, row, col):
        if not self.is_inside_board(row, col):
            return []

        piece = self.state[row][col]

        if piece == EMPTY or self.piece_type(piece) != PAWN:
            return []

        #check color of pawn
        if self.piece_color(piece) == WHITE:
            direction = -1
        else:
            direction = 1

        capture_moves = []
        color = self.piece_color(piece)

        for column_offset in [-1, 1]:
            target_row = row + direction
            target_col = col + column_offset

            if not self.is_inside_board(target_row, target_col):
                continue

            target_piece = self.state[target_row][target_col]

            if (
                target_piece != EMPTY
                and self.piece_color(target_piece) != color
            ):
                capture_moves.append(Move(row, col, target_row, target_col))

        return capture_moves

    def get_knight_moves(self, row, col):
        """Returns all pseudo-legal moves for a knight."""
        if not self.is_inside_board(row, col):
            return []

        piece = self.state[row][col]

        if piece == EMPTY or self.piece_type(piece) != KNIGHT:
            return []

        moves = []
        color = self.piece_color(piece)

        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        for dr, dc in knight_moves:
            target_row = row + dr
            target_col = col + dc

            if not self.is_inside_board(target_row, target_col):
                continue

            target_piece = self.state[target_row][target_col]

            if target_piece == EMPTY or self.piece_color(target_piece) != color:
                moves.append(Move(row, col, target_row, target_col))

        return moves


#funcion auxiliar para movimimientos largos


    def get_sliding_moves(self, row, col, ray_directions):
        if not self.is_inside_board(row, col):
            return []

        piece = self.state[row][col]

        if piece == EMPTY:
            return []

        moves = []
        color = self.piece_color(piece)

        for dr, dc in ray_directions:
            target_row = row + dr
            target_col = col + dc

            while self.is_inside_board(target_row, target_col):
                target_piece = self.state[target_row][target_col]

                if target_piece == EMPTY:
                    moves.append(Move(row, col, target_row, target_col))
                elif self.piece_color(target_piece) != color:
                    moves.append(Move(row, col, target_row, target_col))
                    break
                else:
                    break

                target_row += dr
                target_col += dc

        return moves

#Bishop, Rook and Queen moves
    def get_bishop_moves(self, row, col):
        return self.get_sliding_moves(row, col, DIRECTIONS["bishop"])

    def get_rook_moves(self, row, col):
        return self.get_sliding_moves(row, col, DIRECTIONS["rook"])

    def get_queen_moves(self, row, col):
        return self.get_sliding_moves(row, col, DIRECTIONS["queen"])

#King moves
    def get_king_moves(self, row, col):
        if not self.is_inside_board(row, col):
            return []

        piece = self.state[row][col]

        if piece == EMPTY or self.piece_type(piece) != KING:
            return []

        moves = []
        color = self.piece_color(piece)

        king_offset = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]

        for dr, dc in king_offset:
            target_row = row + dr
            target_col = col + dc

            if not self.is_inside_board(target_row, target_col):
                continue

            target_piece = self.state[target_row][target_col]

            if target_piece == EMPTY or self.piece_color(target_piece) != color:
                moves.append(Move(row, col, target_row, target_col))

        return moves

    

    def get_pseudo_legal_moves(self):
        #create a list to store all pseudo-legal moves

        pseudo_legal_moves = []

        #run trhough all sqaures on the board
        for row in range(8):
            for col in range(8):
                piece = self.state[row][col]

                if piece == EMPTY:
                    continue

                if not self.is_current_player_piece(piece):
                    continue

                piece_type = self.piece_type(piece)

                if piece_type == PAWN:
                    pseudo_legal_moves.extend(self.get_pawn_moves(row, col))

                if piece_type == KNIGHT:
                    pseudo_legal_moves.extend(self.get_knight_moves(row, col))

                if piece_type == BISHOP:
                    pseudo_legal_moves.extend(self.get_bishop_moves(row, col))

                if piece_type == ROOK:
                    pseudo_legal_moves.extend(self.get_rook_moves(row, col))

                if piece_type == QUEEN:
                    pseudo_legal_moves.extend(self.get_queen_moves(row, col))

                if piece_type == KING:
                    pseudo_legal_moves.extend(self.get_king_moves(row, col))
                    
                # Add other piece types here (e.g., KNIGHT, BISHOP, ROOK, QUEEN, KING)

        return pseudo_legal_moves

    
    #Make moves
    def make_move(self, move):
        """Applies a move to the board and returns the info needed to undo it."""
        moved_piece = self.state[move.start_row][move.start_col]
        captured_piece = self.state[move.end_row][move.end_col]

        undo_info = {
            "moved_piece": moved_piece,
            "captured_piece": captured_piece,
            "castling_rights": self.castling_rights.copy(),
            "en_passant_square": self.en_passant_square,
            "halfmove_clock": self.halfmove_clock,
            "fullmove_number": self.fullmove_number,
        }

        # Move the piece
        self.state[move.end_row][move.end_col] = moved_piece
        self.state[move.start_row][move.start_col] = EMPTY

        # En passant square: only right after a two-square pawn move
        if self.piece_type(moved_piece) == PAWN and abs(move.end_row - move.start_row) == 2:
            self.en_passant_square = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_square = None

        # Halfmove clock (50-move rule)
        if self.piece_type(moved_piece) == PAWN or captured_piece != EMPTY:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Fullmove number grows after Black moves
        if self.to_move == BLACK:
            self.fullmove_number += 1

        # Switch turn
        self.to_move = -self.to_move

        return undo_info


    def unmake_move(self,move, undo_info):
        """Restores the board exactly as it was before the move."""
        self.to_move = -self.to_move

        self.state[move.start_row][move.start_col] = undo_info["moved_piece"]
        self.state[move.end_row][move.end_col] = undo_info["captured_piece"]

        self.castling_rights = undo_info["castling_rights"]
        self.en_passant_square = undo_info["en_passant_square"]
        self.halfmove_clock = undo_info["halfmove_clock"]
        self.fullmove_number = undo_info["fullmove_number"]

    

if __name__ == "__main__":
    board = Board()
    before = [row[:] for row in board.state]

    move = Move(6, 4, 4, 4)  # e2e4
    info = board.make_move(move)
    board.print_board()
    print(board.to_move, board.en_passant_square)   # -1 (5, 4)

    board.unmake_move(move, info)
    print(board.state == before, board.to_move == WHITE)  # True True
