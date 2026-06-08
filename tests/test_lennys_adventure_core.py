import unittest

from lennys_adventure_core import (
    JUMP_SPEED,
    MOVE_SPEED,
    GhostBoss,
    Player,
    Projectile,
    RectF,
    generate_level,
    overlaps,
    solid_rects,
    tile_rect,
)


class GeometryTests(unittest.TestCase):
    def test_overlaps_detects_intersection_and_separation(self):
        first = RectF(0, 0, 20, 20)
        self.assertTrue(overlaps(first, RectF(10, 10, 20, 20)))
        self.assertFalse(overlaps(first, RectF(20, 0, 20, 20)))

    def test_tile_rect_uses_tile_coordinates(self):
        rect = tile_rect(3, 4)
        self.assertEqual((rect.x, rect.y, rect.width, rect.height), (96, 128, 32, 32))
        self.assertEqual((rect.centerx, rect.centery), (112, 144))

    def test_solid_rects_extracts_supported_tiles(self):
        rectangles = solid_rects(["#B?P.", "....."])
        self.assertEqual(len(rectangles), 4)
        self.assertEqual(rectangles[-1].x, 96)


class LevelGenerationTests(unittest.TestCase):
    def test_all_ten_levels_have_consistent_matrices(self):
        levels = [generate_level(number) for number in range(1, 11)]
        self.assertEqual([level.number for level in levels], list(range(1, 11)))
        for level in levels:
            self.assertEqual(len(level.matrix), 18)
            self.assertTrue(all(len(row) == level.width for row in level.matrix))
            self.assertEqual(level.spawn, (64, 480))

    def test_regular_levels_end_at_ghost_houses_and_increase_width(self):
        levels = [generate_level(number) for number in range(1, 10)]
        self.assertTrue(all(level.goal is not None for level in levels))
        self.assertTrue(all("H" in "".join(level.matrix) for level in levels))
        self.assertEqual(
            [level.width for level in levels],
            sorted(level.width for level in levels),
        )
        self.assertGreater(len(levels[-1].enemy_spawns), len(levels[0].enemy_spawns))

    def test_boss_level_has_arena_boss_and_cage(self):
        level = generate_level(10)
        matrix = "".join(level.matrix)
        self.assertIsNone(level.goal)
        self.assertIsNotNone(level.boss_spawn)
        self.assertIsNotNone(level.cage_spawn)
        self.assertIn("X", matrix)
        self.assertIn("M", matrix)
        self.assertGreaterEqual(len(level.powerups), 2)

    def test_level_generation_is_deterministic(self):
        self.assertEqual(generate_level(5), generate_level(5))

    def test_invalid_level_number_is_rejected(self):
        for number in (0, 11):
            with self.subTest(number=number):
                with self.assertRaisesRegex(ValueError, "between 1 and 10"):
                    generate_level(number)


class PlayerPhysicsTests(unittest.TestCase):
    def test_horizontal_input_sets_velocity_and_facing(self):
        player = Player(0, 0)
        player.set_horizontal_input(False, True)
        self.assertEqual((player.vx, player.facing), (MOVE_SPEED, 1))
        player.set_horizontal_input(True, False)
        self.assertEqual((player.vx, player.facing), (-MOVE_SPEED, -1))
        player.set_horizontal_input(True, True)
        self.assertEqual(player.vx, 0)

    def test_jump_requires_ground_contact(self):
        player = Player(0, 0, on_ground=False)
        self.assertFalse(player.jump())
        player.on_ground = True
        self.assertTrue(player.jump())
        self.assertEqual(player.vy, -JUMP_SPEED)
        self.assertFalse(player.on_ground)

    def test_player_lands_exactly_on_platform(self):
        player = Player(20, 50, vy=100)
        platform = RectF(0, 100, 200, 32)
        player.move_and_collide([platform], 0.1)
        self.assertEqual(player.y, 70)
        self.assertEqual(player.vy, 0)
        self.assertTrue(player.on_ground)

    def test_player_stops_at_horizontal_wall(self):
        player = Player(40, 30, vx=200)
        wall = RectF(70, 0, 32, 100)
        player.move_and_collide([wall], 0.1)
        self.assertEqual(player.x, 48)

    def test_player_stops_when_hitting_block_from_below(self):
        player = Player(20, 72, vy=-300)
        ceiling = RectF(0, 50, 100, 20)
        player.move_and_collide([ceiling], 0.05)
        self.assertEqual(player.y, 70)
        self.assertEqual(player.vy, 0)

    def test_timers_count_down_without_becoming_negative(self):
        player = Player(0, 0, invincible_timer=1, star_timer=0.5)
        player.update_timers(2)
        self.assertEqual(player.invincible_timer, 0)
        self.assertEqual(player.star_timer, 0)


class PlayerStateTests(unittest.TestCase):
    def test_powerups_cover_all_classic_forms(self):
        player = Player(0, 100)
        player.apply_powerup("mushroom")
        self.assertEqual((player.form, player.height, player.y), ("big", 48, 82))
        player.apply_powerup("flower")
        self.assertEqual(player.form, "fire")
        player.apply_powerup("star")
        self.assertEqual(player.star_timer, 10)
        lives = player.lives
        player.apply_powerup("oneup")
        self.assertEqual(player.lives, lives + 1)
        self.assertEqual(player.score, 3000)

    def test_repeated_mushroom_does_not_change_height_twice(self):
        player = Player(0, 100)
        player.apply_powerup("mushroom")
        player.apply_powerup("mushroom")
        self.assertEqual((player.height, player.y), (48, 82))

    def test_flower_grows_small_player(self):
        player = Player(0, 100)
        player.apply_powerup("flower")
        self.assertEqual((player.form, player.height, player.y), ("fire", 48, 82))

    def test_unknown_powerup_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown power-up"):
            Player(0, 0).apply_powerup("moon")

    def test_damage_steps_down_forms_before_losing_life(self):
        player = Player(0, 100, form="fire", height=48)
        self.assertEqual(player.take_damage(), "shrunk")
        self.assertEqual(player.form, "big")
        player.invincible_timer = 0
        self.assertEqual(player.take_damage(), "shrunk")
        self.assertEqual((player.form, player.height, player.y), ("small", 30, 118))
        player.invincible_timer = 0
        self.assertEqual(player.take_damage(), "dead")
        self.assertEqual(player.lives, 2)

    def test_star_and_invincibility_protect_player(self):
        player = Player(0, 0, star_timer=1)
        self.assertEqual(player.take_damage(), "protected")
        player.star_timer = 0
        player.invincible_timer = 1
        self.assertEqual(player.take_damage(), "protected")


class ProjectileAndBossTests(unittest.TestCase):
    def test_projectile_moves_using_velocity(self):
        projectile = Projectile(10, 20, 30, -10)
        projectile.update(0.5)
        self.assertEqual((projectile.x, projectile.y), (25, 15))
        self.assertEqual((projectile.rect.width, projectile.rect.height), (14, 14))

    def test_boss_patrols_bounds_and_shoots_at_target(self):
        boss = GhostBoss(100, 100, vx=-115, fire_timer=0)
        target = RectF(300, 100, 20, 20)
        boss.update(0.2, 100, 500, target)
        self.assertEqual(boss.x, 100)
        self.assertGreater(boss.vx, 0)
        self.assertEqual(len(boss.projectiles), 1)
        self.assertGreater(boss.projectiles[0].vx, 0)

    def test_boss_reverses_at_right_bound(self):
        boss = GhostBoss(430, 100, vx=115, fire_timer=10)
        boss.update(0.2, 100, 500, RectF(0, 0, 20, 20))
        self.assertEqual(boss.x, 428)
        self.assertLess(boss.vx, 0)

    def test_boss_requires_three_stomps(self):
        boss = GhostBoss(0, 0)
        self.assertTrue(boss.stomp())
        self.assertEqual(boss.health, 2)
        self.assertFalse(boss.stomp())
        boss.hit_timer = 0
        self.assertTrue(boss.stomp())
        boss.hit_timer = 0
        self.assertTrue(boss.stomp())
        self.assertFalse(boss.alive)
        self.assertFalse(boss.stomp())

    def test_dead_boss_does_not_update(self):
        boss = GhostBoss(10, 20, alive=False)
        boss.update(1, 0, 500, RectF(0, 0, 10, 10))
        self.assertEqual((boss.x, boss.y, boss.projectiles), (10, 20, []))


if __name__ == "__main__":
    unittest.main()
