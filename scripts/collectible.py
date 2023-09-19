import pygame


class Collectible(pygame.sprite.Sprite):
    def __init__(self, size, pos, groups, color, player):
        super().__init__(groups)
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
        surf.blit(self.image, (self.pos.x - offset[0], self.pos.y - offset[1]))
