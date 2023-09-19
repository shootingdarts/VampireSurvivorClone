import random

import pygame

from scripts.particle import Particle
from scripts.projectile import Projectile
import math
from scripts.spark import Spark


class PhysicsEntity:

    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.type = e_type
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.health = 100
        self.hit = 60

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.last_movement = movement
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        self.pos[1] += frame_movement[1]

        if movement[0] > 0:
            self.flip = False
        elif movement[0] < 0:
            self.flip = True

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, e_type, pos, size):
        super().__init__(game, e_type, pos, size)
        self.dashing = 0
        self.damage = 50

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        if self.health <= 0:
            self.game.dead += 1
        elif self.health < 100:
            self.health += 1

        if movement[0] != 0 or movement[1] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                velocity=pvelocity, frame=random.randint(0, 7)))

        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                    velocity=pvelocity, frame=random.randint(0, 7)))

        if abs(self.dashing) <= 50 and self.hit == 60:
            for enemy in self.game.enemies:
                if self.rect().colliderect(enemy.rect()):
                    self.hit = 0
                    self.game.sfx['hit'].play()
                    self.health -= 50
                    self.game.screenshake = max(32, self.game.screenshake)
                    for i in range(30):
                        angle = random.random() * 2 * math.pi
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                            velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                      math.sin(angle + math.pi) * speed * 0.5],
                                                            frame=random.randint(0, 7)))
                    self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                    self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                    break

        if self.hit != 60:
            self.hit += 1

        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

    def shoot(self):
        if not self.game.attack_speed:
            self.game.attack_speed = 10
            self.game.sfx['shoot'].play()
            cursor = pygame.mouse.get_pos()
            dis = [cursor[0] - self.game.screen.get_size()[0] / 2,
                   self.game.screen.get_size()[1] / 2 - cursor[1]]
            print(dis)
            length = math.sqrt(dis[0] * dis[0] + dis[1] * dis[1])
            frame_movement = (dis[0] / length * 3, dis[1] / length * 3)
            self.game.projectiles.append(Projectile(self.game, [self.rect().centerx, self.rect().centery],
                                                    frame_movement, 0).effect())

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

    def update(self, tilemap, offset=(0, 0), movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        dis = [self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1]]

        if self.collisions['up'] and self.collisions['down'] and self.collisions['left'] and self.collisions['right']:
            self.velocity[0] = 0
            self.velocity[1] = 0
        else:
            if self.velocity[0] > 0:
                self.velocity[0] = max(self.velocity[0] - 0.1, 0)
            else:
                self.velocity[0] = min(self.velocity[0] + 0.1, 0)
            if self.velocity[1] > 0:
                self.velocity[1] = max(self.velocity[1] - 0.1, 0)
            else:
                self.velocity[1] = min(self.velocity[1] + 0.1, 0)

        length = max((math.sqrt(dis[0] * dis[0] + dis[1] * dis[1])) * 2, 1)
        frame_movement = (dis[0] / length + self.velocity[0], dis[1] / length + self.velocity[1])

        self.pos[0] += frame_movement[0] * 1.5
        entity_rect = self.rect()
        entity_x = entity_rect.x
        entity_y = entity_rect.y
        # print('pos:' + str(self.pos[0]) + ', ' + str(self.pos[1]))
        for enemy in self.game.enemies.copy():
            rect = enemy.rect()
            rect_x = rect.x
            rect_y = rect.y
            # print(rect_x, rect_y, entity_x, entity_y)
            if rect_x is not entity_x and rect_y is not entity_y:
                if entity_rect.colliderect(rect):
                    x_distance = entity_x - rect_x
                    if frame_movement[0] > 0 > x_distance:
                        entity_rect.right = rect.left
                        self.collisions['right'] = True
                        self.velocity[0] -= 1
                    if frame_movement[0] < 0 < x_distance:
                        entity_rect.left = rect.right
                        self.collisions['left'] = True
                        self.velocity[0] += 1
                    self.pos[0] = entity_x

        self.pos[1] += frame_movement[1] * 1.5
        entity_rect = self.rect()
        entity_x = entity_rect.x
        entity_y = entity_rect.y
        for enemy in self.game.enemies.copy():
            rect = enemy.rect()
            rect_x = rect.x
            rect_y = rect.y
            # print(rect_x, rect_y, entity_x, entity_y)
            if rect_x is not entity_x and rect_y is not entity_y:
                if entity_rect.colliderect(rect):
                    y_distance = entity_y - rect_y
                    if frame_movement[1] > 0 > y_distance:
                        entity_rect.bottom = rect.top
                        self.collisions['down'] = True
                        self.velocity[1] -= 1
                    if frame_movement[1] < 0 < y_distance:
                        entity_rect.top = rect.bottom
                        self.collisions['up'] = True
                        self.velocity[1] += 1
                    self.pos[1] = entity_y

            if frame_movement[0] > 0.5:
                self.flip = False
            elif frame_movement[0] < -0.5:
                self.flip = True

        # pygame.draw.line(self.game.display, (255, 0, 0), (self.pos[0] - offset[0], self.pos[1] - offset[1]),
        # (self.pos[0] + dis[0] - offset[0], self.pos[1] + dis[1] - offset[1]), 1)

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(4, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(5):
                    angle = random.random() * 2 * math.pi
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                        velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                  math.sin(angle + math.pi) * speed * 0.5],
                                                        frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True

        for projectile in self.game.projectiles.copy():
            if self.rect().collidepoint(projectile.pos):
                self.game.projectiles.remove(projectile)
                self.game.sfx['hit'].play()
                self.health -= 50
                if self.health <= 0:
                    self.game.screenshake = max(4, self.game.screenshake)
                    for i in range(5):
                        angle = random.random() * 2 * math.pi
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                            velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                      math.sin(angle + math.pi) * speed * 0.5],
                                                            frame=random.randint(0, 7)))
                    return True
                else:
                    for i in range(5):
                        angle = random.random() * 2 * math.pi
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    return False

        self.set_action('run')

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
