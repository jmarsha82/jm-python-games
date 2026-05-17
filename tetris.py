import random
import sys

import pygame


CELL_SIZE = 30
COLUMNS = 10
ROWS = 20
SIDEBAR_WIDTH = 170
WIDTH = COLUMNS * CELL_SIZE + SIDEBAR_WIDTH
HEIGHT = ROWS * CELL_SIZE
FPS = 60
DROP_INTERVAL_MS = 700

BLACK = (16, 18, 24)
GRID = (42, 46, 58)
WHITE = (236, 240, 244)
MUTED = (150, 158, 172)
PANEL = (27, 31, 40)

SHAPES = {
    "I": {
        "color": (0, 216, 255),
        "blocks": [(0, 1), (1, 1), (2, 1), (3, 1)],
    },
    "O": {
        "color": (255, 214, 10),
        "blocks": [(1, 0), (2, 0), (1, 1), (2, 1)],
    },
    "T": {
        "color": (177, 93, 255),
        "blocks": [(1, 0), (0, 1), (1, 1), (2, 1)],
    },
    "S": {
        "color": (45, 214, 121),
        "blocks": [(1, 0), (2, 0), (0, 1), (1, 1)],
    },
    "Z": {
        "color": (255, 80, 80),
        "blocks": [(0, 0), (1, 0), (1, 1), (2, 1)],
    },
    "J": {
        "color": (58, 134, 255),
        "blocks": [(0, 0), (0, 1), (1, 1), (2, 1)],
    },
    "L": {
        "color": (255, 146, 43),
        "blocks": [(2, 0), (0, 1), (1, 1), (2, 1)],
    },
}


class Piece:
    def __init__(self, name):
        shape = SHAPES[name]
        self.name = name
        self.color = shape["color"]
        self.blocks = list(shape["blocks"])
        self.x = COLUMNS // 2 - 2
        self.y = 0

    def cells(self, x_offset=0, y_offset=0, blocks=None):
        active_blocks = blocks if blocks is not None else self.blocks
        return [
            (self.x + x + x_offset, self.y + y + y_offset)
            for x, y in active_blocks
        ]

    def rotated_blocks(self):
        if self.name == "O":
            return self.blocks

        # Rotate clockwise around a 4x4 local grid.
        rotated = [(3 - y, x) for x, y in self.blocks]
        min_x = min(x for x, _ in rotated)
        min_y = min(y for _, y in rotated)
        return [(x - min_x, y - min_y) for x, y in rotated]


def new_piece():
    return Piece(random.choice(list(SHAPES.keys())))


def valid_position(piece, board, x_offset=0, y_offset=0, blocks=None):
    for x, y in piece.cells(x_offset, y_offset, blocks):
        if x < 0 or x >= COLUMNS or y >= ROWS:
            return False
        if y >= 0 and board[y][x] is not None:
            return False
    return True


def lock_piece(piece, board):
    for x, y in piece.cells():
        if 0 <= y < ROWS:
            board[y][x] = piece.color


def clear_lines(board):
    remaining_rows = [row for row in board if any(cell is None for cell in row)]
    cleared = ROWS - len(remaining_rows)
    for _ in range(cleared):
        remaining_rows.insert(0, [None for _ in range(COLUMNS)])
    return remaining_rows, cleared


def draw_cell(surface, x, y, color, offset_x=0, offset_y=0):
    rect = pygame.Rect(
        offset_x + x * CELL_SIZE,
        offset_y + y * CELL_SIZE,
        CELL_SIZE,
        CELL_SIZE,
    )
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (255, 255, 255), rect.inflate(-8, -8), 1)
    pygame.draw.rect(surface, BLACK, rect, 1)


def draw_board(surface, board):
    surface.fill(BLACK)
    pygame.draw.rect(surface, PANEL, (COLUMNS * CELL_SIZE, 0, SIDEBAR_WIDTH, HEIGHT))

    for y in range(ROWS):
        for x in range(COLUMNS):
            cell = board[y][x]
            if cell:
                draw_cell(surface, x, y, cell)
            else:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, GRID, rect, 1)


def draw_piece(surface, piece):
    for x, y in piece.cells():
        if y >= 0:
            draw_cell(surface, x, y, piece.color)


def draw_sidebar(surface, font, small_font, next_piece, score, level, game_over):
    left = COLUMNS * CELL_SIZE + 20
    surface.blit(font.render("TETRIS", True, WHITE), (left, 24))

    surface.blit(small_font.render(f"Score: {score}", True, WHITE), (left, 80))
    surface.blit(small_font.render(f"Level: {level}", True, WHITE), (left, 108))

    surface.blit(small_font.render("Next", True, MUTED), (left, 158))
    preview_x = COLUMNS * CELL_SIZE + 38
    preview_y = 190
    for x, y in next_piece.blocks:
        draw_cell(surface, x, y, next_piece.color, preview_x, preview_y)

    hints = [
        "Left/Right: move",
        "Up: rotate",
        "Down: drop",
        "Space: hard drop",
        "R: restart",
    ]
    for index, hint in enumerate(hints):
        surface.blit(small_font.render(hint, True, MUTED), (left, 320 + index * 24))

    if game_over:
        overlay = pygame.Surface((COLUMNS * CELL_SIZE, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))
        text = font.render("GAME OVER", True, WHITE)
        restart = small_font.render("Press R to restart", True, WHITE)
        surface.blit(text, text.get_rect(center=(COLUMNS * CELL_SIZE // 2, HEIGHT // 2 - 20)))
        surface.blit(
            restart,
            restart.get_rect(center=(COLUMNS * CELL_SIZE // 2, HEIGHT // 2 + 24)),
        )


def reset_game():
    board = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
    return board, new_piece(), new_piece(), 0, 1, False


def main():
    pygame.init()
    pygame.display.set_caption("Color Shape Tetris")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28, bold=True)
    small_font = pygame.font.SysFont("arial", 18)

    board, current_piece, next_piece, score, level, game_over = reset_game()
    last_drop = pygame.time.get_ticks()

    while True:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board, current_piece, next_piece, score, level, game_over = reset_game()
                    last_drop = now
                    continue

                if game_over:
                    continue

                if event.key == pygame.K_LEFT and valid_position(current_piece, board, -1):
                    current_piece.x -= 1
                elif event.key == pygame.K_RIGHT and valid_position(current_piece, board, 1):
                    current_piece.x += 1
                elif event.key == pygame.K_DOWN and valid_position(current_piece, board, 0, 1):
                    current_piece.y += 1
                    score += 1
                elif event.key == pygame.K_UP:
                    rotated = current_piece.rotated_blocks()
                    for kick in (0, -1, 1, -2, 2):
                        if valid_position(current_piece, board, kick, 0, rotated):
                            current_piece.x += kick
                            current_piece.blocks = rotated
                            break
                elif event.key == pygame.K_SPACE:
                    while valid_position(current_piece, board, 0, 1):
                        current_piece.y += 1
                        score += 2
                    last_drop = 0

        interval = max(100, DROP_INTERVAL_MS - (level - 1) * 60)
        if not game_over and now - last_drop >= interval:
            if valid_position(current_piece, board, 0, 1):
                current_piece.y += 1
            else:
                lock_piece(current_piece, board)
                board, cleared = clear_lines(board)
                score += [0, 100, 300, 500, 800][cleared] * level
                level = score // 1000 + 1
                current_piece = next_piece
                next_piece = new_piece()
                if not valid_position(current_piece, board):
                    game_over = True
            last_drop = now

        draw_board(screen, board)
        if not game_over:
            draw_piece(screen, current_piece)
        draw_sidebar(screen, font, small_font, next_piece, score, level, game_over)
        pygame.display.flip()


if __name__ == "__main__":
    main()
