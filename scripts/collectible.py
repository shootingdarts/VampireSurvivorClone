import pygame


class Collectible(pygame.sprite.Sprite):
    def __init__(self, size, pos, groups, color, player, animation=None):
        super().__init__(groups)
        if animation:
            self.animation = animation.copy()
            self.image = pygame.transform.scale(animation.img(), size)
        else:
            self.animation = None
            self.image = pygame.Surface(size)
            self.image.set_colorkey((0, 0, 0))
            pygame.draw.circle(self.image, color, size / 2, size.x / 2)
        self.radius = size.x / 2
        self.color = color
        self.size = size
        self.pos = pos
        self.groups = groups
        self.player = player
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, surf, offset):
        if self.animation:
            self.animation.update()
            self.image = pygame.transform.scale(self.animation.img(), self.size)
        surf.blit(self.image, (self.pos.x - offset[0], self.pos.y - offset[1]))


class ExperienceOrb(Collectible):
    def __init__(self, size, pos, groups, color, player, exp):
        super().__init__(size, pos, groups, color, player)
        self.exp = exp


class Coin(Collectible):
    def __init__(self, size, pos, groups, color, player, animation, gold):
        super().__init__(size, pos, groups, color, player, animation)
        self.gold = gold
