import math
import random
import sys
from dataclasses import dataclass

import pygame

from lennys_adventure_core import (
    LEVEL_HEIGHT,
    TILE_SIZE,
    GhostBoss,
    Player,
    Projectile,
    RectF,
    generate_level,
    overlaps,
    solid_rects,
)


SCREEN_WIDTH = 960
SCREEN_HEIGHT = LEVEL_HEIGHT * TILE_SIZE
FPS = 60
SKY = (8, 12, 38)
WHITE = (242, 245, 255)
MUTED = (164, 176, 207)
GREEN = (48, 190, 96)
BLUE_FIRE = (58, 168, 255)


def pygame_rect(rect):
    return pygame.Rect(
        round(rect.x),
        round(rect.y),
        round(rect.width),
        round(rect.height),
    )


class SpriteAtlas:
    CELL = 16
    COLUMNS = 8
    NAMES = (
        "lenny_small",
        "lenny_big",
        "lenny_fire",
        "ghost",
        "boss",
        "ground",
        "brick",
        "question",
        "mushroom",
        "flower",
        "star",
        "oneup",
        "coin",
        "fireball",
        "blue_fire",
        "marco",
        "cage",
        "house",
    )

    def __init__(self):
        rows = math.ceil(len(self.NAMES) / self.COLUMNS)
        self.sheet = pygame.Surface(
            (self.COLUMNS * self.CELL, rows * self.CELL),
            pygame.SRCALPHA,
        )
        self.index = {name: index for index, name in enumerate(self.NAMES)}
        self._draw_sheet()

    def _cell_surface(self, name):
        index = self.index[name]
        column = index % self.COLUMNS
        row = index // self.COLUMNS
        return self.sheet.subsurface(
            pygame.Rect(
                column * self.CELL,
                row * self.CELL,
                self.CELL,
                self.CELL,
            )
        )

    def frame(self, name, size=(32, 32), flip=False):
        source = self._cell_surface(name)
        frame = pygame.transform.scale(source, size)
        if flip:
            frame = pygame.transform.flip(frame, True, False)
        return frame

    @staticmethod
    def _pixel(surface, color, x, y, width=1, height=1):
        pygame.draw.rect(surface, color, (x, y, width, height))

    def _draw_sheet(self):
        self._draw_lenny("lenny_small", (32, 194, 76), (39, 76, 164))
        self._draw_lenny("lenny_big", (32, 194, 76), (39, 76, 164))
        self._draw_lenny("lenny_fire", WHITE, (32, 194, 76))
        self._draw_ghost()
        self._draw_boss()
        self._draw_tiles()
        self._draw_powerups()
        self._draw_characters()

    def _draw_lenny(self, name, shirt, overalls):
        surface = self._cell_surface(name)
        skin = (244, 180, 124)
        brown = (86, 47, 31)
        self._pixel(surface, shirt, 5, 1, 7, 2)
        self._pixel(surface, shirt, 4, 3, 10, 2)
        self._pixel(surface, skin, 5, 5, 7, 4)
        self._pixel(surface, brown, 4, 5, 2, 3)
        self._pixel(surface, brown, 11, 6, 2, 1)
        self._pixel(surface, shirt, 4, 9, 9, 3)
        self._pixel(surface, overalls, 6, 9, 5, 5)
        self._pixel(surface, skin, 2, 10, 2, 3)
        self._pixel(surface, skin, 13, 10, 2, 3)
        self._pixel(surface, brown, 4, 14, 4, 2)
        self._pixel(surface, brown, 10, 14, 4, 2)
        self._pixel(surface, WHITE, 8, 2, 1, 2)

    def _draw_ghost(self):
        surface = self._cell_surface("ghost")
        body = (222, 231, 255)
        shade = (151, 168, 213)
        self._pixel(surface, body, 3, 3, 10, 9)
        self._pixel(surface, body, 4, 2, 8, 12)
        self._pixel(surface, shade, 4, 12, 2, 3)
        self._pixel(surface, shade, 8, 12, 2, 3)
        self._pixel(surface, shade, 12, 12, 2, 3)
        self._pixel(surface, (34, 39, 70), 6, 5, 2, 3)
        self._pixel(surface, (34, 39, 70), 11, 5, 2, 3)
        self._pixel(surface, (72, 50, 96), 8, 9, 3, 2)

    def _draw_boss(self):
        surface = self._cell_surface("boss")
        body = (198, 216, 255)
        shade = (102, 119, 182)
        self._pixel(surface, body, 2, 2, 12, 11)
        self._pixel(surface, shade, 2, 11, 3, 4)
        self._pixel(surface, shade, 7, 12, 3, 3)
        self._pixel(surface, shade, 12, 11, 3, 4)
        self._pixel(surface, (25, 25, 48), 5, 5, 3, 3)
        self._pixel(surface, (25, 25, 48), 11, 5, 3, 3)
        self._pixel(surface, (35, 38, 73), 6, 10, 7, 2)
        self._pixel(surface, (91, 49, 124), 8, 9, 3, 1)

    def _draw_tiles(self):
        ground = self._cell_surface("ground")
        ground.fill((64, 62, 91))
        self._pixel(ground, (104, 96, 137), 0, 0, 16, 3)
        for x, y in ((2, 6), (10, 5), (6, 12), (13, 11)):
            self._pixel(ground, (39, 39, 65), x, y, 3, 2)

        brick = self._cell_surface("brick")
        brick.fill((92, 57, 91))
        self._pixel(brick, (155, 85, 129), 0, 0, 16, 2)
        for y in (5, 10, 15):
            self._pixel(brick, (42, 32, 59), 0, y, 16, 1)
        for x, y in ((5, 0), (11, 5), (4, 10)):
            self._pixel(brick, (42, 32, 59), x, y, 1, 5)

        question = self._cell_surface("question")
        question.fill((171, 119, 45))
        self._pixel(question, (247, 202, 79), 1, 1, 14, 2)
        self._pixel(question, (97, 59, 35), 5, 4, 6, 2)
        self._pixel(question, (97, 59, 35), 9, 6, 2, 4)
        self._pixel(question, (97, 59, 35), 7, 9, 3, 2)
        self._pixel(question, (97, 59, 35), 7, 12, 2, 2)

    def _draw_powerups(self):
        mushroom = self._cell_surface("mushroom")
        self._pixel(mushroom, (220, 52, 67), 3, 3, 10, 6)
        self._pixel(mushroom, WHITE, 5, 3, 3, 4)
        self._pixel(mushroom, WHITE, 10, 5, 2, 3)
        self._pixel(mushroom, (238, 202, 154), 6, 9, 6, 5)
        self._pixel(mushroom, (43, 32, 35), 7, 10, 1, 2)
        self._pixel(mushroom, (43, 32, 35), 10, 10, 1, 2)

        flower = self._cell_surface("flower")
        self._pixel(flower, (255, 119, 61), 5, 2, 7, 7)
        self._pixel(flower, (255, 232, 91), 7, 4, 3, 3)
        self._pixel(flower, GREEN, 8, 9, 2, 6)
        self._pixel(flower, GREEN, 4, 10, 4, 3)
        self._pixel(flower, GREEN, 10, 11, 4, 3)

        star = self._cell_surface("star")
        points = [(8, 1), (10, 5), (15, 6), (11, 9), (12, 15), (8, 12),
                  (4, 15), (5, 9), (1, 6), (6, 5)]
        pygame.draw.polygon(star, (255, 223, 79), points)
        self._pixel(star, (44, 40, 50), 6, 6, 1, 2)
        self._pixel(star, (44, 40, 50), 10, 6, 1, 2)

        oneup = self._cell_surface("oneup")
        self._pixel(oneup, (48, 191, 91), 3, 3, 10, 6)
        self._pixel(oneup, WHITE, 6, 3, 4, 4)
        self._pixel(oneup, (238, 202, 154), 6, 9, 6, 5)
        self._pixel(oneup, (43, 32, 35), 7, 10, 1, 2)
        self._pixel(oneup, (43, 32, 35), 10, 10, 1, 2)

        coin = self._cell_surface("coin")
        self._pixel(coin, (255, 211, 56), 6, 2, 5, 12)
        self._pixel(coin, (255, 244, 146), 7, 3, 2, 10)

        fireball = self._cell_surface("fireball")
        self._pixel(fireball, (255, 75, 40), 4, 4, 8, 8)
        self._pixel(fireball, (255, 222, 68), 6, 6, 4, 4)

        blue_fire = self._cell_surface("blue_fire")
        self._pixel(blue_fire, (38, 111, 255), 3, 4, 10, 9)
        self._pixel(blue_fire, (126, 224, 255), 6, 5, 5, 6)
        self._pixel(blue_fire, WHITE, 8, 7, 2, 3)

    def _draw_characters(self):
        marco = self._cell_surface("marco")
        self._pixel(marco, (210, 45, 55), 4, 2, 9, 3)
        self._pixel(marco, (244, 180, 124), 5, 5, 7, 4)
        self._pixel(marco, (81, 46, 32), 4, 5, 2, 3)
        self._pixel(marco, (210, 45, 55), 4, 9, 8, 3)
        self._pixel(marco, (39, 76, 164), 6, 10, 5, 5)
        self._pixel(marco, (81, 46, 32), 4, 14, 4, 2)
        self._pixel(marco, (81, 46, 32), 10, 14, 4, 2)

        cage = self._cell_surface("cage")
        for x in (2, 6, 10, 14):
            self._pixel(cage, (133, 140, 162), x, 1, 1, 14)
        self._pixel(cage, (190, 196, 210), 1, 1, 15, 2)
        self._pixel(cage, (83, 88, 108), 1, 14, 15, 2)

        house = self._cell_surface("house")
        self._pixel(house, (49, 43, 72), 2, 7, 12, 9)
        pygame.draw.polygon(house, (83, 60, 101), [(1, 8), (8, 1), (15, 8)])
        self._pixel(house, (236, 221, 121), 5, 8, 2, 3)
        self._pixel(house, (236, 221, 121), 11, 8, 2, 3)
        self._pixel(house, (24, 21, 43), 7, 11, 4, 5)


@dataclass
class Enemy:
    x: float
    y: float
    vx: float
    vy: float = 0
    alive: bool = True

    @property
    def rect(self):
        return RectF(self.x, self.y, 28, 28)

    def update(self, solids, dt):
        if not self.alive:
            return
        self.vy = min(640, self.vy + 1500 * dt)
        self.x += self.vx * dt
        for solid in solids:
            if overlaps(self.rect, solid):
                if self.vx > 0:
                    self.x = solid.left - self.rect.width
                    self.vx *= -1
                else:
                    self.x = solid.right
                    self.vx *= -1
        self.y += self.vy * dt
        for solid in solids:
            if overlaps(self.rect, solid):
                if self.vy > 0:
                    self.y = solid.top - self.rect.height
                    self.vy = 0
                elif self.vy < 0:
                    self.y = solid.bottom
                    self.vy = 0


@dataclass
class Pickup:
    x: float
    y: float
    kind: str
    collected: bool = False

    @property
    def rect(self):
        return RectF(self.x + 3, self.y + 3, 26, 26)


class MagicalAdventure:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Lenny's Magical Adventure")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 21, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 15, bold=True)
        self.large_font = pygame.font.SysFont("consolas", 46, bold=True)
        self.atlas = SpriteAtlas()
        self.stars = self._make_stars()
        self.state = "title"
        self.level_number = 1
        self.player = None
        self.fireballs = []
        self.level_timer = 0
        self.message_timer = 0
        self.victory_timer = 0
        self.boss = None
        self.marco_freed = False
        self.victory_timer = 0
        self.camera_x = 0

    @staticmethod
    def _make_stars():
        rng = random.Random(404)
        return [
            (rng.randrange(SCREEN_WIDTH * 2), rng.randrange(30, 320), rng.choice((1, 1, 2)))
            for _ in range(95)
        ]

    def load_level(self, number, preserve_player=True):
        old_player = self.player
        self.level_number = number
        self.level = generate_level(number)
        self.solids = solid_rects(self.level.matrix)
        self.player = Player(*self.level.spawn)
        if preserve_player and old_player:
            self.player.lives = old_player.lives
            self.player.coins = old_player.coins
            self.player.score = old_player.score
            self.player.form = old_player.form
            if self.player.form != "small":
                self.player.height = 48
                self.player.y -= 18
        self.enemies = [
            Enemy(x, y, (-1 if index % 2 else 1) * (65 + number * 4))
            for index, (x, y) in enumerate(self.level.enemy_spawns)
        ]
        self.pickups = [
            Pickup(x, y, kind)
            for x, y, kind in self.level.powerups
        ]
        self.coins = [
            Pickup(x, y, "coin")
            for x, y in self.level.coins
        ]
        self.fireballs = []
        self.boss = (
            GhostBoss(*self.level.boss_spawn)
            if self.level.boss_spawn
            else None
        )
        self.marco_freed = False
        self.camera_x = 0
        self.level_timer = 300
        self.message_timer = 1.4
        self.state = "playing"

    def shoot(self):
        if self.player.form != "fire" or len(self.fireballs) >= 2:
            return
        direction = self.player.facing
        self.fireballs.append(
            Projectile(
                self.player.rect.centerx,
                self.player.rect.centery,
                430 * direction,
                vy=-80,
                friendly=True,
            )
        )

    def damage_player(self):
        result = self.player.take_damage()
        if result == "dead":
            if self.player.lives <= 0:
                self.state = "game_over"
            else:
                self.load_level(self.level_number)

    def update_fireballs(self, dt):
        for fireball in self.fireballs:
            fireball.vy += 620 * dt
            fireball.update(dt)
            for solid in self.solids:
                if overlaps(fireball.rect, solid):
                    if fireball.vy > 0:
                        fireball.y = solid.top - fireball.height
                        fireball.vy = -220
                    else:
                        fireball.alive = False
                    break
            for enemy in self.enemies:
                if enemy.alive and overlaps(fireball.rect, enemy.rect):
                    enemy.alive = False
                    fireball.alive = False
                    self.player.score += 200
            if self.boss and self.boss.alive and overlaps(fireball.rect, self.boss.rect):
                fireball.alive = False
            if abs(fireball.x - self.player.x) > SCREEN_WIDTH:
                fireball.alive = False
        self.fireballs = [fireball for fireball in self.fireballs if fireball.alive]

    def update_pickups(self):
        for pickup in self.pickups:
            if not pickup.collected and overlaps(self.player.rect, pickup.rect):
                pickup.collected = True
                self.player.apply_powerup(pickup.kind)
        for coin in self.coins:
            if not coin.collected and overlaps(self.player.rect, coin.rect):
                coin.collected = True
                self.player.coins += 1
                self.player.score += 100
                if self.player.coins >= 100:
                    self.player.coins -= 100
                    self.player.lives += 1

    def update_enemies(self, dt, previous_bottom):
        for enemy in self.enemies:
            enemy.update(self.solids, dt)
            if not enemy.alive or not overlaps(self.player.rect, enemy.rect):
                continue
            if self.player.star_timer > 0:
                enemy.alive = False
                self.player.score += 200
            elif self.player.vy > 0 and previous_bottom <= enemy.rect.top + 10:
                enemy.alive = False
                self.player.vy = -360
                self.player.score += 200
            else:
                self.damage_player()
                return

    def update_boss(self, dt, previous_bottom):
        if not self.boss:
            return
        self.boss.update(
            dt,
            left_bound=24 * TILE_SIZE,
            right_bound=56 * TILE_SIZE,
            target=self.player.rect,
        )
        if self.boss.alive and overlaps(self.player.rect, self.boss.rect):
            if self.player.vy > 0 and previous_bottom <= self.boss.rect.top + 18:
                if self.boss.stomp():
                    self.player.vy = -440
                    self.player.score += 1000
            elif self.boss.hit_timer <= 0:
                self.damage_player()
                return
        for projectile in self.boss.projectiles:
            if projectile.alive and overlaps(projectile.rect, self.player.rect):
                projectile.alive = False
                self.damage_player()
                return
        self.boss.projectiles = [
            projectile
            for projectile in self.boss.projectiles
            if projectile.alive
            and abs(projectile.x - self.boss.x) < SCREEN_WIDTH * 1.5
        ]
        if not self.boss.alive:
            self.marco_freed = True
            self.victory_timer += dt
            if self.victory_timer >= 2.5:
                self.state = "victory"

    def update(self, dt):
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        self.player.set_horizontal_input(
            keys[pygame.K_LEFT] or keys[pygame.K_a],
            keys[pygame.K_RIGHT] or keys[pygame.K_d],
        )
        previous_bottom = self.player.rect.bottom
        self.player.move_and_collide(self.solids, dt)
        world_width = self.level.width * TILE_SIZE
        self.player.x = max(0, min(self.player.x, world_width - self.player.width))

        self.level_timer = max(0, self.level_timer - dt)
        self.message_timer = max(0, self.message_timer - dt)
        if self.level_timer <= 0 or self.player.y > SCREEN_HEIGHT + 100:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.state = "game_over"
            else:
                self.load_level(self.level_number)
            return

        self.update_pickups()
        self.update_enemies(dt, previous_bottom)
        if self.state != "playing":
            return
        self.update_fireballs(dt)
        self.update_boss(dt, previous_bottom)
        if self.state != "playing":
            return

        if self.level.goal:
            goal_rect = RectF(
                self.level.goal[0],
                self.level.goal[1],
                TILE_SIZE * 2,
                TILE_SIZE * 3,
            )
            if overlaps(self.player.rect, goal_rect):
                self.player.score += max(0, int(self.level_timer)) * 10
                if self.level_number < 9:
                    self.load_level(self.level_number + 1)
                else:
                    self.load_level(10)
                return

        target_camera = self.player.rect.centerx - SCREEN_WIDTH * 0.42
        self.camera_x = max(
            0,
            min(target_camera, world_width - SCREEN_WIDTH),
        )

    def draw_background(self):
        self.screen.fill(SKY)
        moon_x = 760 - int(self.camera_x * 0.03)
        pygame.draw.circle(self.screen, (222, 226, 204), (moon_x, 88), 46)
        pygame.draw.circle(self.screen, SKY, (moon_x + 18, 75), 42)
        for x, y, size in self.stars:
            screen_x = int(x - self.camera_x * 0.08) % (SCREEN_WIDTH * 2)
            if screen_x < SCREEN_WIDTH:
                color = (169, 189, 230) if size == 1 else (224, 230, 255)
                pygame.draw.rect(self.screen, color, (screen_x, y, size, size))

        cemetery_offset = int(self.camera_x * 0.22)
        for index in range(24):
            x = index * 86 - cemetery_offset % 86
            height = 45 + (index % 4) * 12
            pygame.draw.rect(
                self.screen,
                (20, 26, 55),
                (x, SCREEN_HEIGHT - 64 - height, 43, height),
            )
            pygame.draw.ellipse(
                self.screen,
                (20, 26, 55),
                (x, SCREEN_HEIGHT - 76 - height, 43, 24),
            )

    def draw_world(self):
        first_column = max(0, int(self.camera_x // TILE_SIZE) - 1)
        last_column = min(
            self.level.width,
            first_column + SCREEN_WIDTH // TILE_SIZE + 3,
        )
        for row, line in enumerate(self.level.matrix):
            for column in range(first_column, last_column):
                tile = line[column]
                screen_x = column * TILE_SIZE - self.camera_x
                screen_y = row * TILE_SIZE
                if tile == "#":
                    self.screen.blit(
                        self.atlas.frame("ground"),
                        (screen_x, screen_y),
                    )
                elif tile == "B":
                    self.screen.blit(
                        self.atlas.frame("brick"),
                        (screen_x, screen_y),
                    )
                elif tile == "?":
                    self.screen.blit(
                        self.atlas.frame("question"),
                        (screen_x, screen_y),
                    )

        if self.level.goal:
            house_x = self.level.goal[0] + TILE_SIZE - self.camera_x
            house_y = 12 * TILE_SIZE
            self.screen.blit(
                self.atlas.frame("house", (128, 128)),
                (house_x, house_y),
            )
            pygame.draw.rect(
                self.screen,
                (116, 206, 232),
                (self.level.goal[0] - self.camera_x, 13 * TILE_SIZE, 5, 96),
            )

        for coin in self.coins:
            if not coin.collected:
                self.screen.blit(
                    self.atlas.frame("coin", (24, 28)),
                    (coin.x - self.camera_x + 4, coin.y + 2),
                )
        for pickup in self.pickups:
            if not pickup.collected:
                bob = math.sin(pygame.time.get_ticks() / 180) * 3
                self.screen.blit(
                    self.atlas.frame(pickup.kind),
                    (pickup.x - self.camera_x, pickup.y + bob),
                )
        for enemy in self.enemies:
            if enemy.alive:
                self.screen.blit(
                    self.atlas.frame("ghost"),
                    (enemy.x - self.camera_x - 2, enemy.y - 4),
                )
        for fireball in self.fireballs:
            self.screen.blit(
                self.atlas.frame("fireball", (18, 18)),
                (fireball.x - self.camera_x, fireball.y),
            )

        if self.boss:
            if self.boss.alive:
                if self.boss.hit_timer <= 0 or int(self.boss.hit_timer * 12) % 2:
                    self.screen.blit(
                        self.atlas.frame("boss", (88, 88), self.boss.vx < 0),
                        (self.boss.x - self.camera_x - 8, self.boss.y - 8),
                    )
                for projectile in self.boss.projectiles:
                    self.screen.blit(
                        self.atlas.frame("blue_fire", (22, 22)),
                        (projectile.x - self.camera_x, projectile.y),
                    )
            self.draw_cage_scene()

        form_sprite = {
            "small": "lenny_small",
            "big": "lenny_big",
            "fire": "lenny_fire",
        }[self.player.form]
        player_size = (32, 32) if self.player.form == "small" else (32, 50)
        visible = (
            self.player.invincible_timer <= 0
            or int(self.player.invincible_timer * 12) % 2
        )
        if visible:
            self.screen.blit(
                self.atlas.frame(
                    form_sprite,
                    player_size,
                    flip=self.player.facing < 0,
                ),
                (
                    self.player.x - self.camera_x - 5,
                    self.player.y - (2 if self.player.form == "small" else 1),
                ),
            )

    def draw_cage_scene(self):
        cage_x, cage_y = self.level.cage_spawn
        screen_x = cage_x - self.camera_x
        if self.marco_freed:
            self.screen.blit(
                self.atlas.frame("marco", (36, 48)),
                (screen_x + 12, cage_y + 10),
            )
            pygame.draw.rect(
                self.screen,
                (116, 124, 151),
                (screen_x + 50, cage_y, 4, 72),
            )
        else:
            self.screen.blit(
                self.atlas.frame("marco", (32, 42)),
                (screen_x + 12, cage_y + 16),
            )
            self.screen.blit(
                self.atlas.frame("cage", (64, 72)),
                (screen_x, cage_y),
            )

    def draw_hud(self):
        panel = pygame.Surface((SCREEN_WIDTH, 42), pygame.SRCALPHA)
        panel.fill((5, 8, 25, 220))
        self.screen.blit(panel, (0, 0))
        fields = [
            f"LENNY  {self.player.score:06d}",
            f"COINS {self.player.coins:02d}",
            f"WORLD {self.level_number}-N",
            f"TIME {int(self.level_timer):03d}",
            f"LIVES {self.player.lives}",
        ]
        positions = (18, 250, 430, 620, 800)
        for text, x in zip(fields, positions):
            self.screen.blit(self.small_font.render(text, True, WHITE), (x, 12))
        if self.boss and self.boss.alive:
            for index in range(self.boss.health):
                pygame.draw.circle(
                    self.screen,
                    (122, 197, 255),
                    (SCREEN_WIDTH // 2 - 28 + index * 28, 57),
                    9,
                )

    def draw_center_message(self, title, subtitle):
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((3, 5, 18, 185))
        self.screen.blit(veil, (0, 0))
        title_surface = self.large_font.render(title, True, WHITE)
        subtitle_surface = self.font.render(subtitle, True, MUTED)
        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(SCREEN_WIDTH // 2, 245)),
        )
        self.screen.blit(
            subtitle_surface,
            subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, 305)),
        )

    def draw(self):
        self.draw_background()
        if self.player:
            self.draw_world()
            self.draw_hud()
        if self.state == "title":
            title = self.large_font.render("LENNY'S MAGICAL ADVENTURE", True, GREEN)
            self.screen.blit(
                title,
                title.get_rect(center=(SCREEN_WIDTH // 2, 180)),
            )
            ghost = self.atlas.frame("boss", (128, 128))
            lenny = self.atlas.frame("lenny_big", (64, 96))
            self.screen.blit(lenny, (300, 250))
            self.screen.blit(ghost, (560, 235))
            lines = [
                "A ten-level moonlit rescue",
                "Press ENTER to begin",
                "Move: arrows / A D   Jump: SPACE / Z   Fire: X",
            ]
            for index, line in enumerate(lines):
                surface = self.font.render(
                    line,
                    True,
                    WHITE if index == 1 else MUTED,
                )
                self.screen.blit(
                    surface,
                    surface.get_rect(center=(SCREEN_WIDTH // 2, 390 + index * 38)),
                )
        elif self.state == "game_over":
            self.draw_center_message("GAME OVER", "Press R to try the adventure again")
        elif self.state == "victory":
            self.draw_center_message(
                "MARCO IS FREE!",
                "The great ghost fades. Press ENTER for a new adventure.",
            )
        elif self.message_timer > 0 and self.state == "playing":
            if self.level_number == 10:
                title = "FINAL HAUNT"
                subtitle = "Stomp the great ghost three times"
            else:
                title = f"NIGHT {self.level_number}"
                subtitle = "Find the ghost house"
            title_surface = self.font.render(title, True, WHITE)
            subtitle_surface = self.small_font.render(subtitle, True, MUTED)
            self.screen.blit(title_surface, (24, 58))
            self.screen.blit(subtitle_surface, (24, 84))
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if self.state in {"title", "victory"} and event.key == pygame.K_RETURN:
                        self.player = None
                        self.load_level(1, preserve_player=False)
                    elif self.state == "game_over" and event.key == pygame.K_r:
                        self.player = None
                        self.load_level(1, preserve_player=False)
                    elif self.state == "playing":
                        if event.key in (pygame.K_SPACE, pygame.K_z, pygame.K_UP):
                            self.player.jump()
                        elif event.key == pygame.K_x:
                            self.shoot()
                        elif event.key == pygame.K_r:
                            self.load_level(self.level_number)
            self.update(dt)
            self.draw()


def main():
    MagicalAdventure().run()


if __name__ == "__main__":
    main()
