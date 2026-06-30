import unittest
from unittest.mock import patch

import tetris


def empty_board():
    return [[None for _ in range(tetris.COLUMNS)] for _ in range(tetris.ROWS)]


class PieceTests(unittest.TestCase):
    def test_each_shape_has_a_distinct_color_and_four_blocks(self):
        colors = [tuple(shape["color"]) for shape in tetris.SHAPES.values()]
        self.assertEqual(len(colors), len(set(colors)))

        for name, shape in tetris.SHAPES.items():
            with self.subTest(shape=name):
                self.assertEqual(len(shape["blocks"]), 4)
                self.assertTrue(all(len(block) == 2 for block in shape["blocks"]))

    def test_piece_cells_apply_current_position_and_offsets(self):
        piece = tetris.Piece("T")
        piece.x = 3
        piece.y = 5
        self.assertEqual(
            piece.cells(1, 2),
            [(5, 7), (4, 8), (5, 8), (6, 8)],
        )

    def test_o_piece_does_not_rotate(self):
        piece = tetris.Piece("O")
        self.assertEqual(piece.rotated_blocks(), piece.blocks)

    def test_non_square_piece_rotates_with_normalized_coordinates(self):
        piece = tetris.Piece("L")
        self.assertEqual(piece.rotated_blocks(), [(1, 2), (0, 0), (0, 1), (0, 2)])

    def test_new_piece_uses_shape_catalog(self):
        with patch("random.choice", return_value="S"):
            piece = tetris.new_piece()

        self.assertEqual(piece.name, "S")
        self.assertEqual(piece.color, tetris.SHAPES["S"]["color"])


class BoardRuleTests(unittest.TestCase):
    def test_valid_position_accepts_empty_board(self):
        self.assertTrue(tetris.valid_position(tetris.Piece("I"), empty_board()))

    def test_valid_position_rejects_left_right_and_bottom_bounds(self):
        board = empty_board()

        left_piece = tetris.Piece("O")
        left_piece.x = -2
        self.assertFalse(tetris.valid_position(left_piece, board))

        right_piece = tetris.Piece("O")
        right_piece.x = tetris.COLUMNS - 1
        self.assertFalse(tetris.valid_position(right_piece, board))

        bottom_piece = tetris.Piece("I")
        bottom_piece.y = tetris.ROWS
        self.assertFalse(tetris.valid_position(bottom_piece, board))

    def test_valid_position_allows_cells_above_visible_board(self):
        piece = tetris.Piece("T")
        piece.y = -1
        self.assertTrue(tetris.valid_position(piece, empty_board()))

    def test_valid_position_rejects_collision(self):
        board = empty_board()
        piece = tetris.Piece("T")
        occupied_x, occupied_y = piece.cells()[0]
        board[occupied_y][occupied_x] = (1, 2, 3)

        self.assertFalse(tetris.valid_position(piece, board))

    def test_lock_piece_writes_piece_color_to_board(self):
        board = empty_board()
        piece = tetris.Piece("J")
        tetris.lock_piece(piece, board)

        for x, y in piece.cells():
            self.assertEqual(board[y][x], piece.color)

    def test_clear_lines_removes_full_rows_and_preserves_partial_rows(self):
        color = (9, 9, 9)
        board = empty_board()
        board[-1] = [color for _ in range(tetris.COLUMNS)]
        board[-2] = [color for _ in range(tetris.COLUMNS)]
        board[-3][0] = color

        cleared_board, cleared = tetris.clear_lines(board)

        self.assertEqual(cleared, 2)
        self.assertEqual(cleared_board[0], [None for _ in range(tetris.COLUMNS)])
        self.assertEqual(cleared_board[1], [None for _ in range(tetris.COLUMNS)])
        self.assertEqual(cleared_board[-1][0], color)
        self.assertEqual(len(cleared_board), tetris.ROWS)

    def test_reset_game_returns_clean_initial_state(self):
        with patch("random.choice", side_effect=["I", "Z"]):
            board, current_piece, next_piece, score, level, game_over = tetris.reset_game()

        self.assertEqual(board, empty_board())
        self.assertEqual((current_piece.name, next_piece.name), ("I", "Z"))
        self.assertEqual((score, level, game_over), (0, 1, False))


if __name__ == "__main__":
    unittest.main()
