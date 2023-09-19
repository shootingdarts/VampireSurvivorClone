import json
import random

import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSET = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.infected_tiles = {}
        self.boss_spawners = [
            {'type': 'spawner', 'variant': 1, 'pos': [10, -50]},
            {'type': 'spawner', 'variant': 1, 'pos': [-10, -50]},
            {'type': 'spawner', 'variant': 1, 'pos': [-50, 10]},
            {'type': 'spawner', 'variant': 1, 'pos': [50, 10]}
        ]
        self.foreground_tiles = {}
        self.offgrid_tiles = []

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile)
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap.copy():
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSET:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
        self.infected_tiles.clear()

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            temp_tuple = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (temp_tuple in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[temp_tuple]

    def generate_tile(self, variant):
        tiles = list()
        for i in range(variant):
            tile = pygame.Surface((self.tile_size, self.tile_size))
            for x in range(self.tile_size):
                for y in range(self.tile_size):
                    var = random.randint(0, 4)
                    tile.blit(self.game.assets['grass'][var], (x, y))
            tiles.append(tile)
        return tiles

    def generate_tiles(self):
        for x in range(-100, 100):
            for y in range(-100, 100):
                loc = str(x) + ';' + str(y)
                var = random.randint(0, 5)
                self.tilemap[loc] = {'type': 'grass_tiles', 'variant': var, 'pos': [x, y]}
                fg = random.randint(0, 300)
                if fg < 4:
                    self.foreground_tiles[loc] = {'type': 'decor', 'variant': fg, 'pos': [x, y]}

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']],
                      (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']],
                              (tile['pos'][0] * self.tile_size - offset[0],
                               tile['pos'][1] * self.tile_size - offset[1]))
                if loc in self.foreground_tiles:
                    tile = self.foreground_tiles[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']],
                              (tile['pos'][0] * self.tile_size - offset[0],
                               tile['pos'][1] * self.tile_size - offset[1]))
                if loc in self.infected_tiles:
                    tile = self.infected_tiles[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']],
                              (tile['pos'][0] * self.tile_size - offset[0],
                               tile['pos'][1] * self.tile_size - offset[1]))