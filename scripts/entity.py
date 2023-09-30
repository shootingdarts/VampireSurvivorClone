import math
import pygame
import random

from scripts.aura import Aura
from scripts.collectible import Collectible, ExperienceOrb, Coin
from scripts.particle import Particle
from scripts.weapon import Weapon, WARRIOR_WEAPONS
from scripts.projectile import Projectile, Blade, Shockwave, Shape
from scripts.spark import Spark
from scripts.interface import Cooldown
from scripts.button import Icon, Label, TextBox, Button


class PhysicsEntity(pygame.sprite.Sprite):

    def __init__(self, game, e_type, pos, size, groups):
        super().__init__(groups)
        self.rect = None
        self.game = game
        self.e_type = e_type
        self.size = size
        self.groups = groups
        self.velocity = pygame.math.Vector2((0, 0))
        self.flip = False
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.anim_offset = pygame.math.Vector2((-3, -3))

    def hit(self, effect_magnitude, color=(255, 255, 255)):
        self.game.sfx['hit'].play()
        for i in range(effect_magnitude):
            angle = random.random() * 2 * math.pi
            self.game.sparks.append(Spark(self.rect.center, angle, 1 + random.random(), color))

    def death(self, shake_magnitude, effect_magnitude, color=(255, 255, 255)):
        self.game.sfx['hit'].play()
        for i in range(effect_magnitude):
            angle = random.random() * 2 * math.pi
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect.center, angle, 2 + random.random(), color))
            self.game.particles.append(Particle(self.game, 'particle', self.rect.center,
                                                velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                          math.sin(angle + math.pi) * speed * 0.5],
                                                frame=random.randint(0, 7)))


class Player(PhysicsEntity):

    def __init__(self, game, pos, size, groups, collision_groups):
        super().__init__(game, 'player', pos, size, groups)
        self.shield = 0
        self.action = 'idle'
        self.animation = self.game.assets[self.e_type + '/' + self.action].copy()
        self.image = self.animation.img()
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.old_rect = self.rect.copy()
        self.exp_multi = 1
        self.coin_multi = 1
        self.health = 100
        self.max_health = 100
        self.health_regen = 0.05
        self.attack_speed = 1.2
        self.i_frame = 60
        self.damage_multi = 1
        self.dashing = 0
        self.dash_speed = 60
        self.pickup_range = 75
        self.search_range = 1
        self.shot_speed = 5
        self.collision_groups = collision_groups
        self.pickup_circle = Aura(self.game, pygame.math.Vector2(self.pickup_range, self.pickup_range),
                                  self.game.auras, self)
        self.search_circle = Aura(self.game, pygame.math.Vector2(self.search_range, self.search_range),
                                  self.game.auras, self)
        self.exp = 50
        self.max_exp = 50
        self.gold = 200
        self.speed = 1
        self.level = 0
        self.immortal = False

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.e_type + '/' + self.action].copy()

    def collision(self, direction):
        collision_sprites = pygame.sprite.spritecollide(self, self.collision_groups, False)
        if collision_sprites:
            self.damage(50)
            if direction == 'horizontal':
                for sprite in collision_sprites:
                    # right collision
                    if self.rect.right >= sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left
                        self.pos.x = self.rect.x
                        self.collisions['right'] = True
                    # left collision
                    if self.rect.left <= sprite.rect.right and self.old_rect.left >= sprite.old_rect.right:
                        self.rect.left = sprite.rect.right
                        self.pos.x = self.rect.x
                        self.collisions['left'] = True
            if direction == 'vertical':
                for sprite in collision_sprites:
                    # down collision
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top
                        self.pos.y = self.rect.y
                        self.collisions['down'] = True
                    # up collision
                    if self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                        self.pos.y = self.rect.y
                        self.collisions['up'] = True

    def enemy_search(self, reach, offset=(0, 0)):
        self.search_circle.update(self.game.display, offset)
        enemies = self.game.visible_enemy.sprites()
        self.search_circle.adjust(reach)
        if enemies:
            for enemy in enemies:
                if pygame.sprite.collide_circle(self.search_circle, enemy):
                    dis = pygame.math.Vector2((enemy.rect.center[0] - self.rect.center[0],
                                               self.rect.center[1] - enemy.rect.center[1]))
                    return dis

    def exp_check(self):
        if self.exp >= self.max_exp:
            self.game.level_up_screen()
            self.level += 1
            self.exp -= self.max_exp
            self.max_exp *= 1.5

    def damage(self, amount):
        if self.i_frame == 60:
            if self.shield:
                self.shield = max(int(self.shield) - amount, 0)
            else:
                self.health -= amount
            self.i_frame = 0

    def update(self, movement=pygame.math.Vector2((0, 0)), offset=(0, 0)):
        self.old_rect = self.rect.copy()
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        orbs = pygame.sprite.spritecollide(self.pickup_circle, self.game.exp_orbs, True, pygame.sprite.collide_circle)
        for orb in orbs:
            self.exp += orb.exp * self.exp_multi
        coins = pygame.sprite.spritecollide(self.pickup_circle, self.game.gold_coins, True, pygame.sprite.collide_circle)
        for coin in coins:
            self.gold += coin.gold * self.coin_multi
        frame_movement = movement * self.speed + self.velocity

        if self.i_frame != 60:
            self.i_frame += 1
        else:
            potential_hits = pygame.sprite.spritecollide(self, self.game.enemy_projectiles, False)
            if potential_hits:
                for projectile in potential_hits:
                    if pygame.sprite.collide_mask(self, projectile):
                        self.damage(projectile.damage)
                        if projectile.pierce > 0:
                            projectile.pierce -= 1
                        self.hit(5)

        self.pos.x += frame_movement.x
        self.rect.x = round(self.pos.x)
        if abs(self.dashing) <= 50:
            self.collision('horizontal')

        self.pos.y += frame_movement.y
        self.rect.y = round(self.pos.y)
        if abs(self.dashing) <= 50:
            self.collision('vertical')

        if movement.x > 0:
            self.flip = False
        elif movement.x < 0:
            self.flip = True

        self.animation.update()

        if self.health <= 0 and not self.immortal:
            self.death(10, 10, (255, 0, 0))
            self.game.dead += 1
            return True
        elif self.health < self.max_health:
            self.health += self.health_regen

        if movement.x != 0 or movement.y != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.dashing) > 50:
            cursor = pygame.mouse.get_pos()
            dis = pygame.math.Vector2((cursor[0] - self.game.screen.get_size()[0] / 2,
                                       self.game.screen.get_size()[1] / 2 - cursor[1]))
            dis.scale_to_length(8)
            self.velocity.x = dis.x
            self.velocity.y = -dis.y
            if abs(self.dashing) == 51:
                self.velocity *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect.center,
                                                velocity=pvelocity, frame=random.randint(0, 7)))

        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect.center,
                                                    velocity=pvelocity, frame=random.randint(0, 7)))

        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

        if self.velocity.x > 0:
            self.velocity.x = max(self.velocity.x - 0.1, 0)
        else:
            self.velocity.x = min(self.velocity.x + 0.1, 0)
        if self.velocity.y > 0:
            self.velocity.y = max(self.velocity.y - 0.1, 0)
        else:
            self.velocity.y = min(self.velocity.y + 0.1, 0)

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                      (self.pos.x - offset[0] + self.anim_offset.x, self.pos.y - offset[1] + self.anim_offset.y))

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

    def reset(self):
        self.i_frame = 60
        self.dashing = 0
        self.dash_speed = 10
        self.pickup_range = 75
        self.exp = 50
        self.gold = 200
        self.exp_multi = 1
        self.coin_multi = 1
        self.max_exp = 50
        self.health = 100
        self.max_health = 100
        self.health_regen = 0.05
        self.speed = 1
        self.attack_speed = 1
        self.rect.topleft = [0, 0]
        self.pos = pygame.math.Vector2((0, 0))
        self.level = 0


class Warrior(Player):

    def __init__(self, game, pos, size, groups, collision_groups):
        super().__init__(game, pos, size, groups, collision_groups)
        self.immortal = False
        self.skill_icon = None
        self.skill_duration = 0
        self.skill_cd = 0
        self.weapons = list()
        self.weapon_timer = list()
        self.weapon_icon = list()
        self.weapon_limit = 3
        self.icon_pos_x = 30
        self.shop_choice_y = 120
        self.skill_setup = None

    def update(self, movement=pygame.math.Vector2((0, 0)), offset=(0, 0)):
        super().update(movement, offset)
        for i in range(len(self.weapons)):
            self.weapon_timer[i] = max(0, self.weapon_timer[i] - 1)
            if self.weapon_timer[i] == 0 and self.use_weapon(self.weapons[i]):
                self.weapon_timer[i] = self.weapons[i].interval
            self.weapon_icon[i].update(self.weapon_timer[i], self.weapons[i].interval)
            self.weapon_icon[i].draw()
        if self.skill_icon:
            self.skill_icon.update(self.skill_cd, 360)
            self.skill_icon.draw()
        self.skill_cd = max(self.skill_cd - 1, 0)

    def weapon_status(self):
        return self.weapon_limit and not (self.level % 3)

    def use_weapon(self, weapon, cd=0):
        target = self.enemy_search(weapon.reach)
        return weapon.attack(self.game, self.rect.center, cd, target)

    def equip_weapon(self, weapon):
        equipped = WARRIOR_WEAPONS.acquire_weapon(weapon)
        self.weapons.append(equipped)
        self.weapon_timer.append(0)
        self.weapon_icon.append(Cooldown(self.game, self, self.game.assets[weapon.source], [self.icon_pos_x, 30], [16, 16]))
        self.game.weapon_slots[weapon.name] = Label(self, (200, self.shop_choice_y), self.game.assets[equipped.source],
                                                    15, equipped.stat_description(),
                                                    lambda: equipped.refine(self, self.game.weapon_slots[weapon.name]),
                                                    dim=(800, 200), offset=(200, 0))
        self.game.refine_costs[weapon.name] = Label(self.game, (800, self.shop_choice_y + 150), self.game.assets['coin'].img(),
                                                    10, [str(weapon.refine_cost)], dim=(100, 16), offset=(16, 0))
        self.shop_choice_y += 220
        self.icon_pos_x += 20
        self.weapon_limit -= 1

    def reset(self):
        super().reset()
        self.weapon_timer = list()
        self.weapons = list()

    def get_skill(self, name):
        skill = self.game.assets[name].copy()

        if name == 'shield_skill':
            self.skill_icon = Cooldown(self.game, self, skill.img(), [self.icon_pos_x - 20, 30], [16, 16])

            def skill_setup():
                if self.shield == 0 or self.skill_duration == 0:
                    self.shield = 200
                    self.skill_duration = 360

                def skill_update(surf, offset=(0, 0)):
                    if self.skill_cd == 0:
                        skill.update()
                        surf.blit(skill.img(), (self.rect.x - 4 - offset[0], self.rect.y - offset[1]))
                        self.skill_duration = max(self.skill_duration - 1, 0)
                        if self.shield == 0 or self.skill_duration == 0:
                            self.skill_cd = 360
                            return True
                return skill_update
        elif name == 'slam_skill':
            self.skill_icon = Cooldown(self.game, self, skill.img(), [self.icon_pos_x - 20, 30], [16, 16])
            shockwave = self.game.assets['shockwave']

            def skill_setup():
                skill = self.game.assets[name].copy()
                self.skill_duration = 400
                cursor = pygame.mouse.get_pos()
                window_size = self.game.screen.get_size()
                image_size = skill.img().get_size()
                dis = ((cursor[0] - window_size[0] / 2) / 3.375, (cursor[1] - window_size[1] / 2) / 3.375)
                tl_loc = (self.rect.center[0] + dis[0], self.rect.center[1] + dis[1])
                center_loc = (tl_loc[0] - image_size[0] / 2, tl_loc[1] - image_size[1] / 2)
                start_dim = (4, 2)
                inc_dim = (5, 1.5)
                wave = Shockwave(pygame.draw.ellipse, tl_loc, start_dim, (248, 255, 0))
                impact = Shape(tl_loc, (110, 40), pygame.sprite.collide_circle)

                def skill_update(surf, offset=(0, 0)):
                    if self.skill_cd == 0:
                        if not skill.done:
                            skill.update()
                            surf.blit(skill.img(), (center_loc[0] - offset[0], center_loc[1] - offset[1]))
                            if skill.frame == 35:
                                impact.collision(self.game.visible_enemy)
                        else:
                            if shockwave.frame > 15:
                                wave.draw(surf, offset)
                                wave.update(inc_dim)
                                wave.collision(self.game.visible_enemy, 100 * self.damage_multi)
                                if wave.dim[0] > 229:
                                    wave.reset_to_dim(start_dim)
                                    shockwave.frame = 0
                            shockwave.update()
                            surf.blit(shockwave.img(), (center_loc[0] - offset[0], center_loc[1] - offset[1]))

                        self.skill_duration = max(self.skill_duration - 1, 0)
                        if self.skill_duration == 0:
                            self.skill_cd = 360
                            return True
                return skill_update

        elif name == 'power_skill':
            self.skill_icon = Cooldown(self.game, self, skill.img(), [self.icon_pos_x - 20, 30], [16, 16])

            def skill_setup():
                if self.skill_duration == 0:
                    self.skill_duration = 360
                    self.immortal = True
                    self.speed += 1
                    self.damage_multi += 1
                    self.attack_speed += 1.2

                def skill_update(surf, offset=(0, 0)):
                    if self.skill_cd == 0:
                        self.health = max(self.health - 0.5, 1)
                        skill.update()
                        surf.blit(skill.img(), (self.rect.x - 29 - offset[0], self.rect.y - 32 - offset[1]))
                        self.skill_duration = max(self.skill_duration - 1, 0)
                        if self.skill_duration == 0:
                            self.skill_cd = 360
                            self.immortal = False
                            self.speed -= 1
                            self.damage_multi -= 1
                            self.attack_speed -= 1.2
                            return True
                return skill_update
        self.skill_setup = skill_setup


class Enemy(PhysicsEntity):

    health = 300
    scaling = 1

    def __init__(self, game, pos, size, groups, e_type='mushroom', action='jump'):
        super().__init__(game, e_type, pos, size, groups)
        self.action = action
        self.animation = self.game.assets['enemy/' + self.e_type + '/' + self.action].copy()
        self.image = self.animation.img()
        self.rect = self.image.get_rect(topleft=pos, size=size)
        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.old_rect = self.rect.copy()
        self.momentum = pygame.math.Vector2((1, 1))
        self.player = self.game.player
        self.visibility = False
        self.i_frame = 0
        self.anim_offset = pygame.math.Vector2((-4, -6))
        self.stun = 0

    def death(self, shake_magnitude, effect_magnitude, color=(255, 255, 255)):
        super().death(shake_magnitude, effect_magnitude, color)
        if self.scaling >= 2:
            orb_color = (0, 0, 255)
        elif self.scaling >= 3:
            orb_color = (255, 0, 0)
        else:
            orb_color = (0, 255, 0)
        ExperienceOrb(pygame.math.Vector2(4, 4), self.pos, self.game.exp_orbs, orb_color, self.player, 50 * self.scaling)
        padding = math.floor(self.scaling - 1)
        amount = random.randint(padding, 3 + padding)
        for i in range(amount):
            position = pygame.math.Vector2(self.pos[0] + random.randint(-i, i) * 8, self.pos[1] + random.randint(-i, i) * 8)
            Coin(pygame.math.Vector2(8, 8), position, self.game.gold_coins, (212, 175, 55), self.player,
                 self.game.assets['coin'], 2)

    def collision(self, direction):
        collision_sprites = pygame.sprite.spritecollide(self, self.groups, False)
        if self.rect.colliderect(self.player.rect):
            collision_sprites.append(self.player)
        if collision_sprites:
            if direction == 'horizontal':
                for sprite in collision_sprites:
                    # right collision
                    if self.rect.right >= sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left
                        self.pos.x = self.rect.x
                        self.collisions['right'] = True
                        # self.momentum.x -= 0.5
                    # left collision
                    if self.rect.left <= sprite.rect.right and self.old_rect.left >= sprite.old_rect.right:
                        self.rect.left = sprite.rect.right
                        self.pos.x = self.rect.x
                        self.collisions['left'] = True
                        # self.momentum.x -= 0.5
            if direction == 'vertical':
                for sprite in collision_sprites:
                    # down collision
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top
                        self.pos.y = self.rect.y
                        self.collisions['down'] = True
                        # self.momentum.y -= 0.5
                    # up collision
                    if self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                        self.pos.y = self.rect.y
                        self.collisions['up'] = True
                        # self.momentum.y -= 0.5

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['enemy/' + self.e_type + '/' + self.action].copy()

    def update(self, move=True):
        if self.visible():
            self.game.visible_enemy.add(self)
        else:
            self.game.visible_enemy.remove(self)

        if abs(self.player.dashing) > 50:
            if self.rect.colliderect(self.player.rect):
                self.death(4, 5)
                return True
        if self.i_frame != 5:
            self.i_frame += 1
        else:
            potential_hits = pygame.sprite.spritecollide(self, self.game.projectiles, False)
            if potential_hits:
                for projectile in potential_hits:
                    if pygame.sprite.collide_mask(self, projectile):
                        self.health -= projectile.damage * self.player.damage_multi
                        self.momentum = pygame.math.Vector2(-projectile.knockback, -projectile.knockback)
                        self.i_frame = 0
                        if projectile.pierce > 0:
                            projectile.pierce -= 1
                        if self.health <= 0:
                            self.death(4, 5)
                            return True
                        else:
                            self.hit(5)
        self.old_rect = self.rect.copy()
        if self.momentum.x < 1:
            self.momentum.x = min(self.momentum.x + 0.1, 1)
        if self.momentum.y < 1:
            self.momentum.y = min(self.momentum.y + 0.1, 1)

        if move and not self.stun:
            dis = self.player.pos - self.pos
            if dis.magnitude() > 1:
                dis.normalize_ip()
            frame_movement = (
                (dis.x + self.velocity[0]) * self.momentum.x, (dis.y + self.velocity[1]) * self.momentum.y)
            self.remove(self.groups)

            self.pos.x += frame_movement[0]
            self.rect.x = round(self.pos.x)
            self.collision('horizontal')

            self.pos.y += frame_movement[1]
            self.rect.y = round(self.pos.y)
            self.collision('vertical')

            self.add(self.groups)
        self.stun = max(self.stun - 1, 0)

        self.animation.update()

    def visible(self):
        x = self.game.visible_range[0]
        y = self.game.visible_range[1]
        self.visibility = (self.rect.right >= x[0] and self.rect.left <= x[1] and self.rect.bottom >= y[0]
                           and self.rect.top <= y[1])
        return self.visibility

    def render(self, surf, offset=(0, 0)):
        if self.visibility:
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                      (self.pos.x - offset[0] + self.anim_offset.x, self.pos.y - offset[1] + self.anim_offset.y))

    def set_stun(self, duration):
        self.stun = duration


class Spitter(Enemy):
    def __init__(self, game, pos, size, groups):
        super().__init__(game, pos, size, groups, 'spitter')
        self.attack_range = 150
        self.attack_delay = 180
        self.attack_timer = 0

    def update(self, move=True):
        if self.visible():
            self.game.visible_enemy.add(self)
        else:
            self.game.visible_enemy.remove(self)

        if abs(self.player.dashing) > 50:
            if self.rect.colliderect(self.player.rect):
                self.death(4, 5)
                return True
        if self.i_frame != 5:
            self.i_frame += 1
        else:
            potential_hits = pygame.sprite.spritecollide(self, self.game.projectiles, False)
            if potential_hits:
                for projectile in potential_hits:
                    if pygame.sprite.collide_mask(self, projectile):
                        self.health -= projectile.damage * self.player.damage_multi
                        self.momentum = pygame.math.Vector2(-projectile.knockback, -projectile.knockback)
                        self.i_frame = 0
                        if projectile.pierce > 0:
                            projectile.pierce -= 1
                        if self.health <= 0:
                            self.death(4, 5)
                            return True
                        else:
                            self.hit(5)
        self.old_rect = self.rect.copy()
        if self.momentum.x < 1:
            self.momentum.x = min(self.momentum.x + 0.1, 1)
        if self.momentum.y < 1:
            self.momentum.y = min(self.momentum.y + 0.1, 1)

        dis = self.player.pos - self.pos
        mag = dis.magnitude()
        if mag > 1:
            dis.normalize_ip()
            if mag <= self.attack_range:
                if self.attack_timer == 0:
                    trajectory = pygame.math.Vector2((self.player.rect.center[0] - self.rect.center[0],
                                                      self.rect.center[1] - self.player.rect.center[1]))
                    trajectory.scale_to_length(2)
                    Projectile(self.game, self.rect.center, trajectory, pierce=1, enemy=True)
                    self.attack_timer = self.attack_delay
                else:
                    self.attack_timer = max(self.attack_timer - 1, 0)

        if move and not self.stun:
            frame_movement = (
                (dis.x + self.velocity[0]) * self.momentum.x, (dis.y + self.velocity[1]) * self.momentum.y)
            self.remove(self.groups)

            self.pos.x += frame_movement[0]
            self.rect.x = round(self.pos.x)
            self.collision('horizontal')

            self.pos.y += frame_movement[1]
            self.rect.y = round(self.pos.y)
            self.collision('vertical')

            self.add(self.groups)
        self.stun = max(self.stun - 1, 0)

        self.action = 'jump'

        self.animation.update()


class Boss(Enemy):

    health = 5000
    max_health = 5000

    def __init__(self, game, pos, size, groups, pointer):
        super().__init__(game, pos, size, groups, 'munshroom', 'idle')
        self.name = 'Dr.Munshroom'
        self.pointer = pointer
        self.radius = 1
        self.tl_tr = []
        self.tr_br = []
        self.br_bl = []
        self.bl_tl = []
        self.infection_timer = 0
        self.infection_speed = 20
        self.defection_timer = 0
        self.defection_speed = 5
        self.attack_range = 150
        self.attack_delay = 240
        self.attack_timer = 240
        self.attack_target = list()
        self.attack_circle = None
        self.charging = 300
        self.tilemap = self.game.tilemap
        self.tile_pos = (int(self.pos[0] // self.tilemap.tile_size),
                         int(self.pos[1] // self.tilemap.tile_size))
        self.tilemap.infected_tiles.update(
            {str(self.tile_pos[0]) + ';' + str(self.tile_pos[1]):
                 {'type': 'stone', 'variant': 8, 'pos': self.tile_pos}})
        self.generate_tiles()

    def charge(self, dis):
        if self.charging >= 270:
            if dis.magnitude():
                dis.scale_to_length(2)
                self.velocity.x = dis.x
                self.velocity.y = -dis.y
                if self.charging == 271:
                    self.velocity.x *= 0.1
                    self.velocity.y *= 0.1
                pvelocity = [abs(self.charging) / self.charging * random.random() * 3, 0]
                self.game.particles.append(Particle(self.game, 'particle', self.rect.center,
                                                    velocity=pvelocity, frame=random.randint(0, 7)))

    def update(self, offset=(0, 0)):
        dis = pygame.math.Vector2((self.player.rect.center[0] - self.rect.center[0],
                                   self.rect.center[1] - self.player.rect.center[1]))
        if dis.magnitude() <= 120:
            self.charge(dis)
            self.charging = max(self.charging - 1, 0)
        if not self.charging:
            self.charging = 300
        self.pos.x += self.velocity[0]
        self.rect.x = round(self.pos.x)

        self.pos.y += self.velocity[1]
        self.rect.y = round(self.pos.y)
        if self.velocity.x > 0:
            self.velocity.x = max(self.velocity.x - 0.1, 0)
        else:
            self.velocity.x = min(self.velocity.x + 0.1, 0)
        if self.velocity.y > 0:
            self.velocity.y = max(self.velocity.y - 0.1, 0)
        else:
            self.velocity.y = min(self.velocity.y + 0.1, 0)

        if not self.tl_tr:
            self.radius += 1
            self.generate_tiles()
        if self.infection_timer == self.infection_speed:
            self.infection_timer = 0
            tile1 = (self.tile_pos[0] + self.tl_tr.pop(0), self.tile_pos[1] - self.radius)
            self.tilemap.infected_tiles.update(
                {str(tile1[0]) + ';' + str(tile1[1]):
                     {'type': 'stone', 'variant': 8, 'pos': tile1}})
            tile2 = (self.tile_pos[0] + self.radius, self.tile_pos[1] + self.tr_br.pop(0))
            self.tilemap.infected_tiles.update(
                {str(tile2[0]) + ';' + str(tile2[1]):
                     {'type': 'stone', 'variant': 8, 'pos': tile2}})
            tile3 = (self.tile_pos[0] + self.br_bl.pop(0), self.tile_pos[1] + self.radius)
            self.tilemap.infected_tiles.update(
                {str(tile3[0]) + ';' + str(tile3[1]):
                     {'type': 'stone', 'variant': 8, 'pos': tile3}})
            tile4 = (self.tile_pos[0] - self.radius, self.tile_pos[1] + self.bl_tl.pop(0))
            self.tilemap.infected_tiles.update(
                {str(tile4[0]) + ';' + str(tile4[1]):
                     {'type': 'stone', 'variant': 8, 'pos': tile4}})
        self.infection_timer += 1
        self.attack_timer = min(self.attack_timer + 1, self.attack_delay)
        if dis.magnitude() <= self.attack_range and self.attack_timer == self.attack_delay:
            self.attack_target = self.player.rect.center
            self.attack_circle = Shape(self.attack_target, (40, 40), pygame.sprite.collide_circle)
            self.attack_timer = 0
        self.attack(self.attack_target, offset)
        return super().update(False)

    def attack(self, target, offset):
        if self.attack_timer <= 60:
            pygame.draw.circle(self.game.display, (255, 0, 0),
                               (target[0] - offset[0], target[1] - offset[1]), 20)
        elif self.attack_timer <= 90:
            if pygame.sprite.collide_circle(self.player, self.attack_circle):
                self.player.damage(50 * self.scaling)
            pygame.draw.circle(self.game.display, (0, 0, 255),
                               (target[0] - offset[0], target[1] - offset[1]), 20)

    def death_effect(self):
        if not self.tl_tr:
            self.radius -= 1
            if self.radius == 0:
                self.tilemap.infected_tiles.pop(str(self.tile_pos[0]) + ';' + str(self.tile_pos[1]))
                return True
            self.generate_tiles()
        if self.defection_timer == self.defection_speed:
            self.defection_timer = 0
            tile1 = (self.tile_pos[0] + self.tl_tr.pop(0), self.tile_pos[1] - self.radius)
            self.tilemap.infected_tiles.pop(str(tile1[0]) + ';' + str(tile1[1]))
            tile2 = (self.tile_pos[0] + self.radius, self.tile_pos[1] + self.tr_br.pop(0))
            self.tilemap.infected_tiles.pop(str(tile2[0]) + ';' + str(tile2[1]))
            tile3 = (self.tile_pos[0] + self.br_bl.pop(0), self.tile_pos[1] + self.radius)
            self.tilemap.infected_tiles.pop(str(tile3[0]) + ';' + str(tile3[1]))
            tile4 = (self.tile_pos[0] - self.radius, self.tile_pos[1] + self.bl_tl.pop(0))
            self.tilemap.infected_tiles.pop(str(tile4[0]) + ';' + str(tile4[1]))
        self.defection_timer += 1

    def generate_tiles(self, missing=False):
        pos = self.radius
        neg = -self.radius
        if missing:
            tiles1 = list(range(neg, pos))
            tiles2 = list(range(neg + 1, pos + 1))
            self.tl_tr = [coord for coord in tiles1 if coord not in self.tl_tr]
            self.tr_br = [coord for coord in tiles1 if coord not in self.tr_br]
            self.br_bl = [coord for coord in tiles2 if coord not in self.br_bl]
            self.bl_tl = [coord for coord in tiles2 if coord not in self.bl_tl]
        else:
            self.tl_tr = list(range(neg, pos))
            self.tr_br = list(range(neg, pos))
            self.br_bl = list(range(neg + 1, pos + 1))
            self.bl_tl = list(range(neg + 1, pos + 1))
        random.shuffle(self.tl_tr)
        random.shuffle(self.tr_br)
        random.shuffle(self.br_bl)
        random.shuffle(self.bl_tl)

    def death(self, shake_magnitude, effect_magnitude, color=(255, 255, 255)):
        self.game.sfx['hit'].play()
        for i in range(effect_magnitude):
            angle = random.random() * 2 * math.pi
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect.center, angle, 2 + random.random(), color))
            self.game.particles.append(Particle(self.game, 'particle', self.rect.center,
                                                velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                          math.sin(angle + math.pi) * speed * 0.5],
                                                frame=random.randint(0, 7)))
        if self.scaling >= 2:
            orb_color = (0, 0, 255)
        elif self.scaling >= 3:
            orb_color = (255, 0, 0)
        else:
            orb_color = (0, 255, 0)
        ExperienceOrb(pygame.math.Vector2(4, 4), self.pos, self.game.exp_orbs, orb_color, self.player,
                      250 * self.scaling)
        padding = math.floor(self.scaling - 1)
        amount = random.randint(padding, 15 + padding)
        for i in range(amount):
            position = pygame.math.Vector2(self.pos[0] + random.randint(-i, i) * 8, self.pos[1] + random.randint(-i, i) * 8)
            Coin(pygame.math.Vector2(8, 8), position, self.game.gold_coins, (212, 175, 55), self.player,
                 self.game.assets['coin'], 2)
        self.generate_tiles(True)
        self.game.shop_open = True
        self.game.shop_loc = self.rect.center
