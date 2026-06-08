import random
from dataclasses import dataclass, field


TILE_SIZE = 32
LEVEL_HEIGHT = 18
GRAVITY = 1800.0
MOVE_SPEED = 220.0
JUMP_SPEED = 620.0
MAX_FALL_SPEED = 760.0
SOLID_TILES = {"#", "B", "?", "P"}
POWERUP_ORDER = ("mushroom", "flower", "star", "oneup")


@dataclass
class RectF:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def centerx(self):
        return self.x + self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2


def overlaps(first, second):
    return (
        first.left < second.right
        and first.right > second.left
        and first.top < second.bottom
        and first.bottom > second.top
    )


def tile_rect(column, row):
    return RectF(
        column * TILE_SIZE,
        row * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE,
    )


def solid_rects(matrix):
    return [
        tile_rect(column, row)
        for row, line in enumerate(matrix)
        for column, tile in enumerate(line)
        if tile in SOLID_TILES
    ]


@dataclass
class LevelData:
    number: int
    matrix: list[str]
    spawn: tuple[int, int]
    enemy_spawns: list[tuple[int, int]]
    powerups: list[tuple[int, int, str]]
    coins: list[tuple[int, int]]
    goal: tuple[int, int] | None
    boss_spawn: tuple[int, int] | None = None
    cage_spawn: tuple[int, int] | None = None

    @property
    def width(self):
        return len(self.matrix[0])


def _blank_grid(width):
    return [["." for _ in range(width)] for _ in range(LEVEL_HEIGHT)]


def _fill_floor(grid):
    for row in (LEVEL_HEIGHT - 2, LEVEL_HEIGHT - 1):
        for column in range(len(grid[0])):
            grid[row][column] = "#"


def _place_platform(grid, start, row, length, tile="B"):
    width = len(grid[0])
    for column in range(max(0, start), min(width, start + length)):
        grid[row][column] = tile


def _carve_gap(grid, start, width):
    for row in (LEVEL_HEIGHT - 2, LEVEL_HEIGHT - 1):
        for column in range(start, min(len(grid[0]), start + width)):
            grid[row][column] = "."


def _generate_boss_level():
    width = 64
    grid = _blank_grid(width)
    _fill_floor(grid)
    _place_platform(grid, 14, 12, 7)
    _place_platform(grid, 27, 9, 8)
    _place_platform(grid, 42, 12, 7)
    _place_platform(grid, 52, 8, 5)
    _place_platform(grid, 4, 13, 5, "?")
    grid[15][2] = "S"
    grid[14][34] = "X"
    grid[14][58] = "M"
    for column in (11, 23, 38, 50):
        grid[14][column] = "C"
    return LevelData(
        number=10,
        matrix=["".join(row) for row in grid],
        spawn=(2 * TILE_SIZE, 15 * TILE_SIZE),
        enemy_spawns=[],
        powerups=[
            (6 * TILE_SIZE, 12 * TILE_SIZE, "flower"),
            (46 * TILE_SIZE, 11 * TILE_SIZE, "mushroom"),
        ],
        coins=[
            (column * TILE_SIZE, 14 * TILE_SIZE)
            for column in (11, 23, 38, 50)
        ],
        goal=None,
        boss_spawn=(34 * TILE_SIZE, 13 * TILE_SIZE),
        cage_spawn=(58 * TILE_SIZE, 13 * TILE_SIZE),
    )


def generate_level(number):
    if not 1 <= number <= 10:
        raise ValueError("Level number must be between 1 and 10.")
    if number == 10:
        return _generate_boss_level()

    rng = random.Random(7300 + number)
    width = 86 + number * 8
    grid = _blank_grid(width)
    _fill_floor(grid)
    grid[15][2] = "S"

    gap_count = 2 + number // 2
    gap_width = min(2 + number // 3, 5)
    gap_columns = []
    cursor = 18
    for _ in range(gap_count):
        remaining = width - cursor - 20
        if remaining <= 0:
            break
        start = cursor + rng.randint(7, min(14, remaining))
        _carve_gap(grid, start, gap_width)
        gap_columns.extend(range(start, start + gap_width))
        cursor = start + gap_width

    platform_count = 7 + number
    for index in range(platform_count):
        start = 9 + index * max(6, (width - 22) // platform_count)
        start += rng.randint(-2, 2)
        row = rng.choice((10, 11, 12, 13))
        length = rng.randint(3, 6)
        _place_platform(grid, start, row, length)
        if index % 3 == 1:
            grid[row][start + length // 2] = "?"

    enemy_spawns = []
    enemy_count = 4 + number
    for index in range(enemy_count):
        column = 12 + index * max(6, (width - 25) // enemy_count)
        while column in gap_columns and column < width - 12:
            column += 1
        enemy_spawns.append((column * TILE_SIZE, 15 * TILE_SIZE))
        grid[15][column] = "E"

    powerups = []
    powerup_count = 2 + number // 3
    for index in range(powerup_count):
        column = 14 + index * max(12, (width - 30) // powerup_count)
        row = 9 if index % 2 else 12
        kind = POWERUP_ORDER[(number + index - 1) % len(POWERUP_ORDER)]
        powerups.append((column * TILE_SIZE, row * TILE_SIZE, kind))
        grid[row][column] = "U"

    coins = []
    for column in range(8, width - 10, 8):
        row = rng.choice((8, 9, 12, 14))
        coins.append((column * TILE_SIZE, row * TILE_SIZE))
        if grid[row][column] == ".":
            grid[row][column] = "C"

    house_column = width - 7
    for row in range(12, 16):
        for column in range(house_column, house_column + 4):
            grid[row][column] = "H"
    grid[15][house_column - 1] = "G"

    return LevelData(
        number=number,
        matrix=["".join(row) for row in grid],
        spawn=(2 * TILE_SIZE, 15 * TILE_SIZE),
        enemy_spawns=enemy_spawns,
        powerups=powerups,
        coins=coins,
        goal=((house_column - 1) * TILE_SIZE, 13 * TILE_SIZE),
    )


@dataclass
class Player:
    x: float
    y: float
    width: float = 22
    height: float = 30
    vx: float = 0
    vy: float = 0
    on_ground: bool = False
    facing: int = 1
    form: str = "small"
    lives: int = 3
    coins: int = 0
    score: int = 0
    invincible_timer: float = 0
    star_timer: float = 0

    @property
    def rect(self):
        return RectF(self.x, self.y, self.width, self.height)

    def set_horizontal_input(self, left, right):
        direction = int(bool(right)) - int(bool(left))
        self.vx = direction * MOVE_SPEED
        if direction:
            self.facing = direction

    def jump(self):
        if not self.on_ground:
            return False
        self.vy = -JUMP_SPEED
        self.on_ground = False
        return True

    def update_timers(self, dt):
        self.invincible_timer = max(0.0, self.invincible_timer - dt)
        self.star_timer = max(0.0, self.star_timer - dt)

    def move_and_collide(self, solids, dt):
        self.update_timers(dt)
        self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * dt)

        self.x += self.vx * dt
        for solid in solids:
            if overlaps(self.rect, solid):
                if self.vx > 0:
                    self.x = solid.left - self.width
                elif self.vx < 0:
                    self.x = solid.right

        self.on_ground = False
        self.y += self.vy * dt
        for solid in solids:
            if overlaps(self.rect, solid):
                if self.vy > 0:
                    self.y = solid.top - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = solid.bottom
                    self.vy = 0

    def apply_powerup(self, kind):
        if kind == "mushroom":
            if self.form == "small":
                self.form = "big"
                self.y -= 18
                self.height = 48
            self.score += 1000
        elif kind == "flower":
            if self.form == "small":
                self.y -= 18
                self.height = 48
            self.form = "fire"
            self.score += 1000
        elif kind == "star":
            self.star_timer = 10.0
            self.score += 1000
        elif kind == "oneup":
            self.lives += 1
        else:
            raise ValueError(f"Unknown power-up: {kind}")

    def take_damage(self):
        if self.invincible_timer > 0 or self.star_timer > 0:
            return "protected"
        if self.form == "fire":
            self.form = "big"
            self.invincible_timer = 2.0
            return "shrunk"
        if self.form == "big":
            self.form = "small"
            self.y += 18
            self.height = 30
            self.invincible_timer = 2.0
            return "shrunk"
        self.lives -= 1
        return "dead"


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float = 0
    width: float = 14
    height: float = 14
    friendly: bool = False
    alive: bool = True

    @property
    def rect(self):
        return RectF(self.x, self.y, self.width, self.height)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt


@dataclass
class GhostBoss:
    x: float
    y: float
    width: float = 72
    height: float = 72
    vx: float = 115
    health: int = 3
    fire_timer: float = 1.5
    hit_timer: float = 0
    alive: bool = True
    projectiles: list[Projectile] = field(default_factory=list)

    @property
    def rect(self):
        return RectF(self.x, self.y, self.width, self.height)

    def update(self, dt, left_bound, right_bound, target):
        if not self.alive:
            return
        self.hit_timer = max(0.0, self.hit_timer - dt)
        self.x += self.vx * dt
        if self.x <= left_bound:
            self.x = left_bound
            self.vx = abs(self.vx)
        elif self.x + self.width >= right_bound:
            self.x = right_bound - self.width
            self.vx = -abs(self.vx)

        self.fire_timer -= dt
        if self.fire_timer <= 0:
            direction = 1 if target.centerx >= self.rect.centerx else -1
            self.projectiles.append(
                Projectile(
                    self.rect.centerx - 7,
                    self.rect.centery,
                    230 * direction,
                    friendly=False,
                )
            )
            self.fire_timer = 1.25
        for projectile in self.projectiles:
            projectile.update(dt)

    def stomp(self):
        if not self.alive or self.hit_timer > 0:
            return False
        self.health -= 1
        self.hit_timer = 0.8
        if self.health <= 0:
            self.alive = False
        return True
