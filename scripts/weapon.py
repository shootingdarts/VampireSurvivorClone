import random
import pygame

from scripts.projectile import Projectile, Blade


class Weapon:
    def __init__(self, name, description, interval, source, reach, attack_type, *changes, **stats):
        self.refine_cost = 100
        self.name = name
        self.description = description
        self.acquired = False
        self.source = source
        self.interval = interval
        self.reach = reach
        self.changeable_stats = {change: stats[change] for change in changes}
        self.stats = stats
        self.attack_type = attack_type
        self.attack = attack_type(self, **stats)
        self.level = 1
        self.max_level = 3

    def spin(self, dur_multi, rotate_multi, range_multi, damage, pierce):
        def attack(game, pos, cd, target):
            if target and cd == 0:
                r = 30 * range_multi
                Blade(game, pos, pygame.math.Vector2.from_polar((r, 90)), 180 * dur_multi, -3 * rotate_multi,
                      self.source, 0, damage=damage, pierce=pierce)
                Blade(game, pos, pygame.math.Vector2.from_polar((r, -30)), 180 * dur_multi, 3 * rotate_multi,
                      self.source, 0, damage=damage, pierce=pierce)
                Blade(game, pos, pygame.math.Vector2.from_polar((r, -150)), 180 * dur_multi, 3 * rotate_multi,
                      self.source, 0, damage=damage, pierce=pierce)
                return True
            return False
        return attack

    def swing(self, dur_multi, rotate_multi, offset_multi, range_multi, damage, pierce, knockback=1):
        def attack(game, pos, cd, target):
            if target and cd == 0:
                target.scale_to_length(30 * range_multi)
                Blade(game, pos, target, 6 * dur_multi, 15 * rotate_multi, self.source, 0.5 * offset_multi, damage=damage, pierce=pierce, knockback=knockback)
                return True
            return False
        return attack

    def throw(self, dur_multi, speed, damage, pierce):
        def attack(game, pos, cd, target):
            if target and cd == 0:
                target.scale_to_length(speed)
                Projectile(game, pos, target, self.source, 60 * dur_multi, damage=damage, pierce=pierce)
                return True
            return False
        return attack

    def boomer(self, dur_multi, rotate_multi, speed, return_speed, damage, pierce):
        def attack(game, pos, cd, target):
            if target and cd == 0:
                target.scale_to_length(speed)
                Projectile(game, pos, target, self.source, 60 * dur_multi, 10 * rotate_multi, True, return_speed, damage, pierce=pierce)
                return True
            return False
        return attack

    def target(self, dur_multi, range_multi, damage, pierce):
        def attack(game, pos, cd, target):
            if target and cd == 0:
                target.scale_to_length(30 * range_multi)
                Blade(game, pos, target, 30 * dur_multi, 0, self.source, 0, False, damage, pierce=pierce)
                return True
            return False
        return attack

    def refine(self, player, label):
        if player.gold >= self.refine_cost:
            for stat in self.changeable_stats:
                self.stats[stat] += self.changeable_stats[stat]
            self.level += 1
            self.attack = self.attack_type(self, **self.stats)
            player.gold -= self.refine_cost
            label.update_text(self.stat_description())

    def render(self):
        pass

    def stat_description(self):
        return [f'{self.name} (Level {self.level})', ''] + [f'{stat}: {value} (+{self.changeable_stats[stat]})'
                if stat in self.changeable_stats.keys() else f'{stat}: {value}' for stat, value in self.stats.items()]


class Weapons:
    def __init__(self):
        self.all_weapons = dict()
        self.acquired_weapons = dict()

    def add_weapon(self, weapon):
        self.all_weapons[weapon.name] = weapon

    def acquire_weapon(self, weapon):
        acquired = self.all_weapons.pop(weapon.name)
        self.acquired_weapons[weapon.name] = weapon
        return acquired

    def random_weapons(self, count):
        selection = random.sample(list(self.all_weapons.keys()), k=count)
        weapon_selection = []
        for name in selection:
            weapon_selection.append(self.all_weapons[name])
        return weapon_selection

    def reset(self):
        for name in self.acquired_weapons.copy():
            weapon = self.acquired_weapons.pop(name)
            self.all_weapons[weapon.name] = weapon


WARRIOR_WEAPONS = Weapons()
WARRIOR_WEAPONS.add_weapon(Weapon('Sword', 'Swings at target location',15, 'sword', 75, Weapon.swing,
                                  'damage', dur_multi=1, rotate_multi=1, offset_multi=1, range_multi=1, damage=50, pierce=-1))
WARRIOR_WEAPONS.add_weapon(Weapon('Sawblade', 'Spins around you', 300, 'sawblade', 75, Weapon.spin,
                                  'damage', dur_multi=1, rotate_multi=1, range_multi=1, damage=20, pierce=-1))
WARRIOR_WEAPONS.add_weapon(Weapon('Boomer', 'Fires a boomerang that returns back to you', 60, 'boomer', 200, Weapon.boomer,
                                  'damage', dur_multi=1, rotate_multi=1.5, speed=2, return_speed=3, damage=50, pierce=-1))
WARRIOR_WEAPONS.add_weapon(Weapon('ThrowingKnife', 'Throws a knife that pierces enemies', 60, 'throwingknife', 500, Weapon.throw,
                                  'damage', dur_multi=1, speed=3, damage=100, pierce=-1))
WARRIOR_WEAPONS.add_weapon(Weapon('Club', 'Swings at target location and knocks back enemy', 60, 'club', 75, Weapon.swing,
                                  'damage', dur_multi=1, rotate_multi=1, offset_multi=1, range_multi=1, damage=100, pierce=-1, knockback=2))

