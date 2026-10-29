class Move:
    def __init__(
        self,
        start_row,
        start_col,
        end_row,
        end_col,
        promotion=None,
        is_castling=False,
        is_en_passant=False,
    ):
        self.start_row = start_row
        self.start_col = start_col
        self.end_row = end_row
        self.end_col = end_col

        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant

    def __str__(self):
        files = "abcdefgh"

        start_square = f"{files[self.start_col]}{8 - self.start_row}"
        end_square = f"{files[self.end_col]}{8 - self.end_row}"

        return start_square + end_square

    def __repr__(self):
        return str(self)


if __name__ == "__main__":
    move = Move(6, 4, 4, 4)

    print(move)