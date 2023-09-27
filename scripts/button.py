import pygame


class Icon:

    def __init__(self, game, pos, dim, hover_effect=None, bg=(255, 255, 255), fg=(0, 0, 0), source=None):
        self.game = game
        self.dim = dim
        self.bg = bg
        self.fg = fg
        self.pos = pos
        self.hover_effect = hover_effect
        if source:
            self.image = pygame.transform.scale(self.game.assets[source], dim)
        else:
            self.image = pygame.Surface(dim)
            self.image.fill(bg)
        self.rect = self.image.get_rect(topleft=pos)

    def draw(self, surf):
        cursor = pygame.mouse.get_pos()
        if self.rect.collidepoint(cursor):
            if self.hover_effect:
                self.hover_effect()
        surf.blit(self.image, self.rect.topleft)


class Button:

    def __init__(self, game, pos, size, text, dim=(256, 256), animation=None, offset=(0, 0), press_effect=None, hover_effect=None, bg=(255, 255, 255), fg=(29, 19, 8)):
        self.game = game
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        self.text = text
        self.animation = animation
        self.dim = dim
        self.bg = bg
        self.fg = fg
        self.offset = offset
        self.press_effect = press_effect
        self.hover_effect = hover_effect
        self.font = pygame.font.SysFont('arialblack', size)
        self.font_height = self.font.get_height()
        self.image = pygame.Surface(dim)
        self.image.set_colorkey((0, 0, 0))
        if self.animation:
            pygame.transform.scale(self.animation.img(), dim, self.image)
        else:
            self.image.fill(bg)
        self.line_pos = [offset[0], offset[1] + 10]
        for line in self.text:
            self.image.blit(self.font.render(line, True, self.fg), self.line_pos)
            self.line_pos[1] += self.font_height
        self.rect = self.image.get_rect(center=pos)

    def update_text(self, text):
        self.text = text
        self.image = pygame.Surface(self.dim)
        self.image.set_colorkey((0, 0, 0))
        if self.animation:
            pygame.transform.scale(self.animation.img(), self.dim, self.image)
        else:
            self.image.fill(self.bg)
        self.line_pos = [self.offset[0], self.offset[1] + 10]
        for line in self.text:
            self.image.blit(self.font.render(line, True, self.fg), self.line_pos)
            self.line_pos[1] += self.font_height
        self.rect = self.image.get_rect(center=self.pos)

    def draw(self, surf, released=True):
        cursor = pygame.mouse.get_pos()
        if self.rect.collidepoint(cursor):
            if self.animation:
                self.animation.update()
                self.image.fill((0, 0, 0))
                self.image.set_colorkey((0, 0, 0))
                self.image.blit(self.animation.img(), (0, 0))
                self.image.blit(self.font.render(self.text, True, self.fg), self.offset)
            if self.hover_effect:
                self.hover_effect()
            if released:
                if pygame.mouse.get_pressed()[0]:
                    if self.press_effect:
                        self.press_effect()
                    return True
        else:
            if self.animation:
                self.animation.reset()
                self.image.fill((0, 0, 0))
                self.image.set_colorkey((0, 0, 0))
                self.image.blit(self.animation.img(), (0, 0))
                self.image.blit(self.font.render(self.text, True, self.fg), self.offset)
        surf.blit(self.image, self.rect.topleft)
        return False


class Label:
    def __init__(self, game, pos, image, size, text, press_effect=None, hover_effect=None, dim=(800, 150), offset=(150, 0), bg=(23, 107, 135)):
        self.rect = None
        self.image = None
        self.game = game
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        self.press_effect = press_effect
        self.hover_effect = hover_effect
        self.font = pygame.font.SysFont('arialblack', size)
        self.font_height = self.font.get_height()
        self.dim = dim
        self.offset = offset
        self.bg = bg
        self.text = text
        self.icon = image
        self.update_image(image, text)

    def draw(self, surf, released=True):
        surf.blit(self.image, self.rect.topleft)
        cursor = pygame.mouse.get_pos()
        if self.rect.collidepoint(cursor):
            if self.hover_effect:
                self.hover_effect()
            if released:
                if pygame.mouse.get_pressed()[0]:
                    if self.press_effect:
                        self.press_effect()
                    return True
        return False

    def update_text(self, text):
        self.image = pygame.Surface(self.dim)
        self.text = text
        self.image.set_colorkey((0, 0, 0))
        if self.bg:
            pygame.draw.rect(self.image, self.bg, pygame.Rect(0, 0, self.dim[0], self.dim[1]))
            self.image.blit(pygame.transform.scale(self.icon, (self.dim[1], self.dim[1])), (0, 0))
        line_pos = [self.offset[0], self.offset[1]]
        for line in self.text:
            words = self.font.render(line, True, (0, 0, 255))
            self.image.blit(words, line_pos)
            line_pos[1] += self.font_height

    def update_image(self, image, text):
        self.image = pygame.Surface(self.dim)
        self.text = text
        self.image.set_colorkey((0, 0, 0))
        if self.bg:
            pygame.draw.rect(self.image, self.bg, pygame.Rect(0, 0, self.dim[0], self.dim[1]))
        self.image.blit(pygame.transform.scale(image, (self.dim[1], self.dim[1])), (0, 0))
        line_pos = [self.offset[0], self.offset[1]]
        for line in self.text:
            words = self.font.render(line, True, (0, 0, 255))
            self.image.blit(words, line_pos)
            line_pos[1] += self.font_height
        self.rect = self.image.get_rect(topleft=self.pos)
        return self


class TextBox:
    def __init__(self, text, font, dim, fg=(255, 0, 0), bg=(0, 0, 0)):
        self.font = font
        self.dim = dim
        self.text = self.word_wrap(text)
        self.height = font.get_height()
        self.fg = fg
        self.bg = bg
        self.image = pygame.Surface(dim)
        self.image.fill(bg)
        self.image.set_colorkey((0, 0, 0))
        line_pos = [0, 0]
        for line in self.text:
            words = self.font.render(line, True, fg)
            self.image.blit(words, line_pos)
            line_pos[1] += self.height

    def update_text(self, text):
        self.text = self.word_wrap(text)
        self.image = pygame.Surface(self.dim)
        self.image.fill(self.bg)
        self.image.set_colorkey((0, 0, 0))
        line_pos = [0, 0]
        for line in self.text:
            words = self.font.render(line, True, self.fg)
            self.image.blit(words, line_pos)
            line_pos[1] += self.height

    def word_wrap(self, text):
        all_lines = list()
        line = ''
        max_width = self.dim[0]
        for char in text:
            line += char
            if self.font.size(line)[0] > max_width:
                all_lines.append(line)
                line = ''
        if line:
            all_lines.append(line)
        return all_lines

    def render(self, surf, pos):
        surf.blit(self.image, pos)
