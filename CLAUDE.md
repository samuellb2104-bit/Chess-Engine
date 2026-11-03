# Chess engine — contexto para Claude

Proyecto hobby de Samuel: un motor de ajedrez desde cero en Python (sin librerías de ajedrez), con interfaz web para jugar contra el bot con amigos y un selector de dificultad antes de empezar la partida.

## Reglas de trabajo
- Responder en español.
- **Samuel quiere entender y escribir el código él mismo.** Guía con explicaciones, pseudocódigo y revisiones. Da código completo solo cuando él lo pida explícitamente, y en ese caso explícalo línea por línea.
- Antes de pasar al siguiente paso, propón pruebas concretas con la salida esperada en comentarios (debajo de `if __name__ == "__main__":`).
- Ojo: Samuel suele tener los archivos abiertos en VS Code; si editas un archivo, avísale para que no sobrescriba tu cambio guardando su pestaña.
- A veces trae código de otras fuentes con otros nombres (`board.board`, `current_player`, `from .constants`); hay que adaptarlo a este proyecto.

## Arquitectura
- `move.py`: clase `Move(start_row, start_col, end_row, end_col, promotion=None, is_castling=False, is_en_passant=False)`; `__str__` → notación tipo UCI (`e2e4`, `a7a8q`). `PROMOTION_LETTER` usa números para evitar import circular con board.py.
- `board.py`: estado y reglas.
- `evaluate.py`: `evaluate(board)` por material (PIECE_VALUES 100/320/330/500/900/0).
- `search.py`: `minimax(board, depth, alpha, beta)` con poda alfa-beta y `find_best_move(board, depth)`; `MATE_SCORE = 100000`; revisa fin de partida ANTES de `depth == 0`.
- `game.py`, `app.py`, `web/` (index.html, style.css, app.js), `tests/`: vacíos todavía.

## Convenciones
- `board.state[fila][col]`: fila 0 = rango 8 (negras), fila 7 = rango 1 (blancas); col 0 = a.
- Piezas con signo = `color * tipo`. WHITE = 1, BLACK = -1. EMPTY=0, PAWN=1, KNIGHT=2, BISHOP=3, ROOK=4, QUEEN=5, KING=6.
- Turno: `board.to_move`. Cambiar turno: `self.to_move = -self.to_move`.
- Evaluación: positivo = mejor para blancas.
- `make_move(move)` devuelve `undo_info` (moved_piece, captured_piece, castling_rights.copy(), en_passant_square, halfmove_clock, fullmove_number); `unmake_move(move, undo_info)` restaura exacto.

## Métodos de Board
piece_at, print_board, is_inside_board, piece_color, piece_type, is_current_player_piece, get_pawn_moves, add_pawn_moves (genera las 4 promociones), pawn_capture (incluye captura al paso), get_knight_moves, get_sliding_moves + get_bishop/rook/queen_moves (DIRECTIONS), get_king_moves, get_pseudo_legal_moves, make_move, unmake_move, perft, is_square_attacked, find_king, get_legal_moves, is_in_check(color), get_game_state() → "checkmate" / "check" / "stalemate" / "ongoing".

## Verificado
- perft desde la posición inicial: 1–4 = 20 / 400 / 8902 / 197281 ✅.
- Mate del pastor invertido → "checkmate"; ahogado → "stalemate".
- search: mate en 1 blancas (a1a8) y negras (a8a1); promoción elige a7a8q.
- Promoción y captura al paso: aplicar y deshacer probados.
- Pendiente confirmar: `Board().perft(5)` debe dar 4865609 (~3 min).

## Pendiente
1. **Siguiente paso: `game.py`** — clase `Game(difficulty)` con board, depth (`DIFFICULTY_DEPTH = {"easy": 1, "medium": 2, "hard": 3}`), human_color = WHITE; métodos `human_move(start_row, start_col, end_row, end_col, promotion=None)` (busca la jugada en get_legal_moves y usa ESE objeto), `bot_move()`, `is_over()`. Probar jugando en la terminal con input().
2. `app.py`: servidor web con rutas JSON (nueva partida con dificultad, estado, mover).
3. `web/`: tablero 8×8, clics, pantalla inicial Fácil / Medio / Difícil.
4. Enroque (generar, aplicar/deshacer, actualizar castling_rights; no se puede enrocar estando en jaque ni pasando por casillas atacadas). Probar con la posición "Kiwipete".
5. Evaluación posicional (piece-square tables) para que el bot desarrolle piezas.
6. Mover las pruebas a `tests/`.
7. Limpieza: borrar `import move` y `get_pawn_double_move` en board.py; constantes `KNIGHT_OFFSETS` / `KING_OFFSETS`; posible `constants.py`.

El historial completo de la conversación con el primer agente está en `context.md` (largo; consultar solo si hace falta).
