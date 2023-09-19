import os

import pygame

import copy

BASE_IMG_PATH = 'data/images/'


class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
        self.end_frame = len(self.images)

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    def reset(self):
        self.frame = 0

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * self.end_frame)
        else:
            self.frame = min(self.frame + 1, self.img_duration * self.end_frame - 1)
            if self.frame >= self.img_duration * self.end_frame - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]


def load_image(path, scale=1):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    pygame.transform.scale_by(img, scale)
    img.set_colorkey((0, 0, 0))
    return img


def load_images(path, scale=1):
    images = []
    for img_name in os.listdir(BASE_IMG_PATH + path):
        images.append(load_image(path + '/' + img_name, scale))
    return images


def load_sprite_sheet(path, dimensions, frames, scale=1, color=(0, 0, 0)):
    spread_sheet = load_image(path)
    images = list()
    for frame in range(frames):
        image = pygame.Surface(dimensions).convert()
        image.blit(spread_sheet, (0, 0), ((frame * dimensions[0]), 0, dimensions[0], dimensions[1]))
        image = pygame.transform.scale(image, (dimensions[0] * scale, dimensions[1] * scale))
        image.set_colorkey(color)
        images.append(image)
    return images
