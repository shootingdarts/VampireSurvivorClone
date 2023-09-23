import math
import random

import pygame

from scripts.spark import Spark
from scripts.utils import Animation


class Projectile(pygame.sprite.Sprite):
    def __init__(self, game, pos, velocity, source='projectile', duration=120, rotate=0, returns=False, return_speed=1,
                 damage=50, pierce=-1, enemy=False, animation=None):
        self.game = game
        if enemy:
            super().__init__(self.game.enemy_projectiles)
        else:
            super().__init__(self.game.projectiles)
        self.pos = list(pos)
        self.velocity = velocity
        self.frame = 0
        self.return_speed = return_speed
        self.animation = animation
        if animation:
            self.original = animation.img()
            self.duration = animation.img_duration * animation.end_frame
        else:
            self.original = self.game.assets[source]
            self.duration = duration
        self.pierce = pierce
        self.returns = returns
        self.damage = damage
        self.knockback = -1
        self.image = self.original
        self.rect = self.image.get_rect(center=self.pos)
        self.angle = self.vector_to_angle(self.velocity)
        self.image = pygame.transform.rotate(self.original, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.rotate = rotate

    def update(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] -= self.velocity[1]
        if self.animation:
            self.animation.update()
            self.original = self.animation.img()
            self.image = pygame.transform.rotate(self.original, self.angle)
        if self.rotate:
            self.angle_update(self.rotate)
        self.rect = self.image.get_rect(center=self.pos)
        self.frame += 1
        if self.pierce == 0:
            return True
        if self.frame > self.duration:
            if self.returns:
                return self.find_target(self.game.player.rect)
            else:
                return True

    def find_target(self, target):
        dis = pygame.math.Vector2(target.center[0] - self.pos[0], self.pos[1] - target.center[1])
        if dis.magnitude() <= 1:
            return True
        else:
            dis = dis.normalize() * self.return_speed
        self.velocity = dis

    def angle_update(self, angle):
        self.angle += angle
        self.image = pygame.transform.rotate(self.original, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    @staticmethod
    def vector_to_angle(vector):
        angle = pygame.math.Vector2(0, 0).angle_to(vector)
        if abs(angle) < 5:
            angle = 0
        elif 85 < abs(angle) < 95:
            if angle > 0:
                angle = 90
            else:
                angle = -90
        elif 175 < abs(angle) < 185:
            if angle > 0:
                angle = 180
            else:
                angle = -180
        return angle

    def render(self, surf, offset=(0, 0)):
        surf.blit(self.image, (self.pos[0] - self.image.get_width() / 2 - offset[0],
                               self.pos[1] - self.image.get_height() / 2 - offset[1]))

    def effect(self, amount=4):
        for i in range(amount):
            self.game.sparks.append(
                Spark(self.pos, random.random() - 0.5 + math.radians(self.angle),
                      1 + random.random()))
        return self


class Blade(pygame.sprite.Sprite):
    def __init__(self, game, pos, velocity, duration=6, rotate=15, source='slash', offset=0.5, follow=True, damage=50,
                 pierce=-1, knockback=-1, enemy=False, animation=None):
        self.game = game
        if enemy:
            super().__init__(self.game.enemy_projectiles)
        else:
            super().__init__(self.game.projectiles)
        self.pos = [pos[0] + velocity[0],
                    pos[1] - velocity[1]]
        self.follow = follow
        self.damage = damage
        self.pierce = pierce
        self.frame = 0
        self.knockback = knockback
        polar = velocity.as_polar()
        angle_offset = duration * rotate * offset
        if polar[1] < 0:
            self.velocity = pygame.math.Vector2.from_polar((polar[0], polar[1] + angle_offset))
        else:
            self.velocity = pygame.math.Vector2.from_polar((polar[0], polar[1] - angle_offset))
        self.initial = self.velocity
        self.animation = animation
        if animation:
            self.original = animation.img()
            self.duration = animation.img_duration * animation.end_frame
        else:
            self.original = self.game.assets[source]
            self.duration = duration
        self.angle = Projectile.vector_to_angle(self.velocity)
        self.image = pygame.transform.rotate(self.original, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.rotate = ((polar[1] / abs(polar[1])) if polar[1] != 0 else 0) * rotate

    def update(self):
        if self.animation:
            self.animation.update()
            self.original = self.animation.img()
            self.image = pygame.transform.rotate(self.original, self.angle)
        if self.rotate:
            self.angle_update(self.rotate)
        if self.follow:
            self.rect.center = (self.game.player.rect.center[0] + self.velocity[0],
                                self.game.player.rect.center[1] - self.velocity[1])
        self.pos = self.rect.center
        self.frame += 1
        if self.pierce == 0:
            return True
        if self.frame > self.duration:
            return True

    def angle_update(self, angle):
        polar = self.velocity.as_polar()
        self.velocity = pygame.math.Vector2.from_polar((polar[0], polar[1] + angle))
        self.angle += angle
        self.image = pygame.transform.rotate(self.original, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    def render(self, surf, offset=(0, 0)):
        surf.blit(self.image, (self.pos[0] - self.image.get_width() / 2 - offset[0],
                               self.pos[1] - self.image.get_height() / 2 - offset[1]))

    def effect(self, amount=4):
        for i in range(amount):
            self.game.sparks.append(
                Spark(self.pos, random.random() - 0.5 + math.radians(self.angle),
                      1 + random.random()))
        return self


class Shockwave(pygame.sprite.Sprite):
    def __init__(self, shape, pos, dim, color, width=1, png_offset=(0.5, 47), *groups):
        super().__init__(*groups)
        self.shape = shape
        self.pos = [pos[0] - dim[0] / 2 + png_offset[0], pos[1] - dim[1] / 2 + png_offset[1]]
        self.old_pos = self.pos
        self.dim = list(dim)
        self.color = color
        self.width = width
        self.png_offset = png_offset
        self.rect = pygame.Rect(pos, dim)
        self.image = pygame.Surface(dim)
        self.image.set_colorkey((0, 0, 0))
        self.shape(self.image, self.color, ((0, 0), self.dim), self.width)
        self.prev_hits = list()

    def update(self, inc):
        self.dim[0] += inc[0]
        self.dim[1] += inc[1]
        self.pos = [self.pos[0] - inc[0] / 2, self.pos[1] - inc[1] / 2]
        self.rect.size = self.dim
        self.rect.topleft = self.pos
        self.image = pygame.Surface(self.dim)
        self.image.set_colorkey((0, 0, 0))
        self.shape(self.image, self.color, ((0, 0), self.dim), self.width)

    def reset_to_dim(self, dim):
        self.dim = list(dim)
        self.rect = pygame.Rect(self.old_pos, dim)
        self.pos = self.old_pos
        self.image = pygame.Surface(dim)
        self.image.set_colorkey((0, 0, 0))
        self.shape(self.image, self.color, ((0, 0), dim), self.width)
        self.prev_hits = list()

    def draw(self, surf, offset=(0, 0)):
        surf.blit(self.image, (self.rect.left - offset[0], self.rect.top - offset[1]))

    def collision(self, group, damage):
        rect_hits = pygame.sprite.spritecollide(self, group, False)
        if rect_hits:
            for enemy in [hit for hit in rect_hits if hit not in self.prev_hits]:
                enemy.health -= damage
                enemy.set_stun(60)
                if enemy.health <= 0:
                    enemy.death(4, 5)
                    enemy.kill()
                else:
                    enemy.hit(5)
            self.prev_hits = rect_hits


class Pointer(pygame.sprite.Sprite):
    def __init__(self, game, pos, source, duration=1, follow=True):
        self.game = game
        super().__init__(self.game.pointer_group)
        self.pos = pos
        self.follow = follow
        self.original = self.game.assets[source].img()
        self.image = self.original
        self.rect = self.image.get_rect(center=self.pos)
        self.duration = duration

    def update(self, vector, show, surf, offset=(0, 0)):
        self.pos = [self.pos[0] + vector[0],
                    self.pos[1] - vector[1]]
        angle = Projectile.vector_to_angle(vector)
        self.image = pygame.transform.rotate(self.original, angle)
        self.rect = self.image.get_rect(center=self.pos)
        if self.follow:
            self.rect.center = (self.game.player.rect.center[0] + vector[0],
                                self.game.player.rect.center[1] - vector[1])
        self.pos = self.rect.center
        if show:
            surf.blit(self.image, (self.pos[0] - self.image.get_width() / 2 - offset[0],
                                   self.pos[1] - self.image.get_height() / 2 - offset[1]))


class Shape(pygame.sprite.Sprite):
    def __init__(self, pos, dim, shape, image=None, *groups):
        super().__init__(*groups)
        self.shape = shape
        self.pos = [pos[0] - dim[0] / 2, pos[1] - dim[1] / 2]
        self.dim = dim
        self.rect = pygame.Rect(pos, dim)
        self.image = image

    def collision(self, group):
        rect_hits = pygame.sprite.spritecollide(self, group, False, self.shape)
        if rect_hits:
            for enemy in rect_hits:
                enemy.set_stun(60)
                enemy.hit(5)

