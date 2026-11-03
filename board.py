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

#promotion constants
PROMOTION_PIECES = [QUEEN, ROOK, BISHOP, KNIGHT]

# Rook corner squares (row, col) -> castling right that depends on that rook
CORNER_RIGHTS = {
    (7, 0): "Q",
    (7, 7): "K",
    (0, 0): "q",
    (0, 7): "k",
}

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

    def add_pawn_moves(self, moves, row, col, to_row, to_col):
        """Adds a pawn move, or the four promotion moves if it reaches the last rank"""
        piece = self.state[row][col]
        promotion_row = 0 if self.piece_color(piece) == WHITE else 7

        if to_row == promotion_row:
            for promotion_piece in PROMOTION_PIECES:
                moves.append(Move(row, col, to_row, to_col, promotion=promotion_piece))
        else:
            moves.append(Move(row, col, to_row, to_col))


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
            self.add_pawn_moves(moves, row, col, next_row, col)

            # Two-square forward move from its initial row
            double_next_row = row + 2 * direction

            if (
                row == start_row
                and self.is_inside_board(double_next_row, col)
                and self.state[double_next_row][col] == EMPTY
            ):
                self.add_pawn_moves(moves, row, col, double_next_row, col)

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
                self.add_pawn_moves(capture_moves, row, col, target_row, target_col)

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

        moves.extend(self.get_castling_moves(row, col, color))

        return moves

    def get_castling_moves(self, row, col, color):
        """Returns the castling moves available to the king at (row, col)."""
        home_row = 7 if color == WHITE else 0

        # The king must still be on its starting square
        if row != home_row or col != 4:
            return []

        enemy = -color

        # You cannot castle while in check
        if self.is_square_attacked(row, col, enemy):
            return []

        moves = []
        rook = color * ROOK
        kingside_right = "K" if color == WHITE else "k"
        queenside_right = "Q" if color == WHITE else "q"

        # Kingside (O-O): f and g empty, and the king cannot cross or land on an attacked square.
        # We also check the rook is really there: castling_rights can be stale in custom positions.
        if (
            self.castling_rights[kingside_right]
            and self.state[row][7] == rook
            and self.state[row][5] == EMPTY
            and self.state[row][6] == EMPTY
            and not self.is_square_attacked(row, 5, enemy)
            and not self.is_square_attacked(row, 6, enemy)
        ):
            moves.append(Move(row, 4, row, 6, is_castling=True))

        # Queenside (O-O-O): b, c and d empty; only d and c must be safe
        # (the king never goes through b, only the rook passes there)
        if (
            self.castling_rights[queenside_right]
            and self.state[row][0] == rook
            and self.state[row][1] == EMPTY
            and self.state[row][2] == EMPTY
            and self.state[row][3] == EMPTY
            and not self.is_square_attacked(row, 3, enemy)
            and not self.is_square_attacked(row, 2, enemy)
        ):
            moves.append(Move(row, 4, row, 2, is_castling=True))

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

        # promotion replace the pawn with the promoted piece
        if move.promotion:
            self.state[move.end_row][move.end_col] = self.to_move * move.promotion

        # Castling: the king has already moved, now move the rook next to it
        if move.is_castling:
            if move.end_col == 6:  # kingside: rook h -> f
                self.state[move.end_row][5] = self.state[move.end_row][7]
                self.state[move.end_row][7] = EMPTY
            else:  # queenside: rook a -> d
                self.state[move.end_row][3] = self.state[move.end_row][0]
                self.state[move.end_row][0] = EMPTY

        # Castling rights: lost when the king moves...
        if self.piece_type(moved_piece) == KING:
            if self.to_move == WHITE:
                self.castling_rights["K"] = False
                self.castling_rights["Q"] = False
            else:
                self.castling_rights["k"] = False
                self.castling_rights["q"] = False

        # ...and when a rook leaves its corner or is captured on it
        # (checking start AND end square covers both cases)
        for square in [(move.start_row, move.start_col), (move.end_row, move.end_col)]:
            if square in CORNER_RIGHTS:
                self.castling_rights[CORNER_RIGHTS[square]] = False

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

        # Put the rook back where it was
        if move.is_castling:
            if move.end_col == 6:  # kingside: rook f -> h
                self.state[move.end_row][7] = self.state[move.end_row][5]
                self.state[move.end_row][5] = EMPTY
            else:  # queenside: rook d -> a
                self.state[move.end_row][0] = self.state[move.end_row][3]
                self.state[move.end_row][3] = EMPTY

        self.castling_rights = undo_info["castling_rights"]
        self.en_passant_square = undo_info["en_passant_square"]
        self.halfmove_clock = undo_info["halfmove_clock"]
        self.fullmove_number = undo_info["fullmove_number"]


    #number of moves on the turn
    def perft(self, depth):
        """Perft function to count the number of leaf nodes at a given depth."""
        if depth == 0:
            return 1

        moves = self.get_legal_moves()
        total_nodes = 0

        for move in moves:
            undo_info = self.make_move(move)
            total_nodes += self.perft(depth - 1)
            self.unmake_move(move, undo_info)

        return total_nodes

    def is_square_attacked(self, row, col, by_color):
        """Checks if a square is attacked by the given color."""
        # Check for pawn attacks
        pawn_direction = 1 if by_color == WHITE else -1
        for dc in [-1, 1]:
            r = row + pawn_direction
            c = col + dc
            if self.is_inside_board(r, c) and self.state[r][c] == by_color * PAWN:
                return True

        # Check for knight attacks
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        for dr, dc in knight_moves:
            r = row + dr
            c = col + dc
            if self.is_inside_board(r, c) and self.state[r][c] == by_color * KNIGHT:
                return True

        # Check for sliding piece attacks (rook/queen and bishop/queen)
        directions = {
            "rook": [(-1, 0), (1, 0), (0, -1), (0, 1)],
            "bishop": [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        }
        for piece_type in ["rook", "bishop"]:
            for dr, dc in directions[piece_type]:
                r = row + dr
                c = col + dc
                while self.is_inside_board(r, c):
                    target_piece = self.state[r][c]
                    if target_piece != EMPTY:
                        if self.piece_color(target_piece) == by_color and (
                            self.piece_type(target_piece) == ROOK and piece_type == "rook" or
                            self.piece_type(target_piece) == BISHOP and piece_type == "bishop" or
                            self.piece_type(target_piece) == QUEEN
                        ):
                            return True
                        break
                    r += dr
                    c += dc

        # Check for king attacks
        king_offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1), (1, 0), (1, 1) ]

        for dr, dc in king_offsets:
            r = row + dr
            c = col + dc
            if self.is_inside_board(r, c) and self.state[r][c] == by_color * KING:
                return True
            
        return False

    def find_king(self,color):
        for row in range(8):
            for col in range(8):
                piece = self.state[row][col]
                if piece == color * KING:
                    return (row, col)
        return None
    
    def get_legal_moves(self):

        legal_moves = []
        my_color = self.to_move

        for move in self.get_pseudo_legal_moves():
            info = self.make_move(move)
            king_pos = self.find_king(my_color)
            if king_pos is not None:
                king_row, king_col = king_pos
                if not self.is_square_attacked(king_row, king_col, -my_color):
                    legal_moves.append(move)

            self.unmake_move(move, info)
        return legal_moves

    def is_in_check(self,color):
        king_pos = self.find_king(color)
        if king_pos is None:
            return False

        king_row, king_col = king_pos
        return self.is_square_attacked(king_row, king_col, -color)
    
    def get_game_state(self):
        if self.is_in_check(self.to_move):
            if not self.get_legal_moves():
                return "checkmate"
            else:
                return "check"
        else:
            if not self.get_legal_moves():
                return "stalemate"
            else:
                return "ongoing"

    

if __name__ == "__main__":
    def load_position(placement, to_move=WHITE, rights="KQkq"):
        """Builds a board from the piece-placement part of a FEN string."""
        letters = {"p": PAWN, "n": KNIGHT, "b": BISHOP, "r": ROOK, "q": QUEEN, "k": KING}
        b = Board()
        b.state = []
        for rank in placement.split("/"):
            row = []
            for ch in rank:
                if ch.isdigit():
                    row += [EMPTY] * int(ch)
                else:
                    row.append((WHITE if ch.isupper() else BLACK) * letters[ch.lower()])
            b.state.append(row)
        b.to_move = to_move
        b.castling_rights = {right: (right in rights) for right in "KQkq"}
        return b

    def castles(b):
        return sorted(str(m) for m in b.get_legal_moves() if m.is_castling)

    # Posicion "Kiwipete": ambos bandos pueden enrocar a los dos lados
    kiwipete = load_position("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R")
    print(len(kiwipete.get_legal_moves()))   # 48
    print(castles(kiwipete))                 # ['e1c1', 'e1g1']
    print(kiwipete.perft(2))                 # 2038  (oficial 2039; falta 1 por la captura al paso, aun sin implementar)

    # Aplicar y deshacer el enroque corto deja todo exacto
    move = [m for m in kiwipete.get_legal_moves() if str(m) == "e1g1"][0]
    info = kiwipete.make_move(move)
    print(kiwipete.state[7][5], kiwipete.state[7][6])   # 4 6   (torre en f1, rey en g1)
    print(kiwipete.castling_rights)          # {'K': False, 'Q': False, 'k': True, 'q': True}
    kiwipete.unmake_move(move, info)
    print(kiwipete.state[7][4], kiwipete.state[7][7])   # 6 4   (rey en e1, torre en h1)
    print(kiwipete.castling_rights)          # {'K': True, 'Q': True, 'k': True, 'q': True}

    # No se puede enrocar estando en jaque
    print(castles(load_position("4r1k1/8/8/8/8/8/8/R3K2R")))    # []
    # No se puede pasar por una casilla atacada (f1 atacada: solo queda el enroque largo)
    print(castles(load_position("5rk1/8/8/8/8/8/8/R3K2R")))     # ['e1c1']
    # Que b1 este atacada no impide el enroque largo (el rey no pasa por b1)
    print(castles(load_position("1r4k1/8/8/8/8/8/8/R3K2R")))    # ['e1c1', 'e1g1']
    # Si capturan la torre de a8, las negras pierden el derecho "q"
    board = load_position("r3k2r/8/8/8/8/8/8/R3K2R")
    board.make_move([m for m in board.get_legal_moves() if str(m) == "a1a8"][0])
    print(board.castling_rights)             # {'K': True, 'Q': False, 'k': True, 'q': False}

    print([Board().perft(d) for d in (1, 2, 3, 4)])   # [20, 400, 8902, 197281]
