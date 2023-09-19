import random

import pygame


class Cloud:
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)
        self.img = img
        self.mask = pygame.mask.from_surface(img).to_surface(setcolor=(0, 0, 0, 50), unsetcolor=(0, 0, 0, 0))
        self.speed = speed
        self.depth = depth

    def update(self):
        self.pos[0] += self.speed

    def render(self, surf, offset=(0, 0)):
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        surf.blit(self.mask, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(),
                              render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))


class Clouds:
    def __init__(self, cloud_images, count=10):
        self.clouds = []

        for i in range(count):
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999), random.choice(cloud_images),
                                     random.random() * 0.1 + 0.1, random.random() * 0.6 + 0.2))

        self.clouds.sort(key=lambda x: x.depth)

    def update(self):
        for cloud in self.clouds:
            cloud.update()
        return self

    def render(self, surf, offset=(0, 0)):
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
