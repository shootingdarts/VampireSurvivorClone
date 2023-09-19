import pygame


class Aura(pygame.sprite.Sprite):

    def __init__(self, game, size, groups, player, visibility=False, color=(255, 0, 0, 200)):
        super().__init__()
        self.game = game
        self.image = pygame.Surface(size)
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.circle(self.image, color, size / 2, size.x / 2)
        self.radius = size.x / 2
        self.color = color
        self.size = size
        self.visibility = visibility
        self.groups = groups
        self.player = player
        self.rect = self.image.get_rect(center=self.player.rect.center)
        self.pos = self.rect.topleft

    def update(self, surf, offset=(0, 0)):
        self.rect.center = self.player.rect.center
        self.pos = self.rect.topleft
        if self.visibility:
            surf.blit(self.image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))

    def adjust(self, diameter):
        self.size = pygame.math.Vector2((diameter, diameter))
        self.image = pygame.Surface(self.size)
        self.radius = diameter / 2
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=self.player.rect.center)
        self.pos = self.rect.topleft
