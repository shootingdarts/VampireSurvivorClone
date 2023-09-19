import pygame


class Interface:
    def __init__(self, game, player, pos=(0, 0), size=(100, 5), max=100, bg=(255, 0, 0), fg=(0, 255, 0), reverse=False,
                 display=False, name='Boss'):
        self.game = game
        self.player = player
        self.pos = list(pos)
        self.size = size
        self.max = max
        self.ratio = 1
        self.bg = bg
        self.fg = fg
        self.reverse = reverse
        self.display = display
        self.name = name
        self.font = pygame.font.SysFont('arialblack', size[1])

    def update(self, current, new_max=100):
        self.max = new_max
        self.ratio = current / self.max
        return self

    def draw(self, surf):
        pygame.draw.rect(surf, self.bg,
                         (self.pos[0], self.pos[1], self.size[0], self.size[1]))
        if self.reverse:
            pygame.draw.rect(surf, self.fg,
                             (self.pos[0], self.pos[1], self.size[0] * (1 - self.ratio), self.size[1]))
        else:
            pygame.draw.rect(surf, self.fg,
                             (self.pos[0], self.pos[1], self.size[0] * self.ratio, self.size[1]))
        if self.display:
            text = self.font.render(f'{self.name}: {int(self.max * self.ratio)}/{self.max}', True, (255, 255, 255))
            loc = (self.size[0] / 2 - text.get_width() / 2 + self.pos[0], self.pos[1] - 5)
            surf.blit(text, loc)


class Cooldown(Interface):
    def __init__(self, game, player, image, pos=(0, 0), size=(100, 5), max=100, bg=(0, 255, 0), fg=(0, 0, 0, 125), reverse=False):
        super().__init__(game, player, pos, size, max, bg, fg, reverse)
        self.image = pygame.transform.scale(image, size)

    def icon(self):
        pass

    def draw(self):
        self.game.display.blit(self.image, self.pos)
        if self.reverse:
            pygame.draw.rect(self.game.display, self.fg,
                             (self.pos[0], self.pos[1], self.size[0], self.size[1] * (1 - self.ratio)))
        else:
            pygame.draw.rect(self.game.display, self.fg,
                             (self.pos[0], self.pos[1], self.size[0], self.size[1] * self.ratio))
