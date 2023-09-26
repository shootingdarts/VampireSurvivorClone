import math
import random
import sys
import pygame

from scripts.button import Button, Icon, Label, TextBox
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.utils import *
from scripts.interface import Interface
from scripts.collectible import Collectible
from scripts.entity import Player, Warrior, Enemy, Boss, Spitter
from scripts.projectile import Projectile, Blade, Pointer
from scripts.upgrade import Upgrade, GAME_UPGRADES
from scripts.weapon import WARRIOR_WEAPONS
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds

# sprite groups
enemy_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
boss_group = pygame.sprite.Group()


class Game:

    def __init__(self):
        pygame.init()

        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((1080, 810))

        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.movement = [False, False, False, False]

        self.assets = {
            'decor': load_sprite_sheet('tiles/decor/Decor.png', (16, 16), 9),
            'grass': load_sprite_sheet('tiles/grass/GrassColors.png', (1, 1), 5),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/mushroom/jump': Animation(
                load_sprite_sheet('entities/enemy/mushroom/jump/Mushroom.png', (16, 16), 12), img_dur=5),
            'enemy/spitter/jump': Animation(
                load_sprite_sheet('entities/enemy/spitter/jump/Mushroom2.png', (16, 16), 12), img_dur=5),
            'enemy/munshroom/idle': Animation(
                load_sprite_sheet('entities/enemy/munshroom/idle/Dr.Munshroom.png', (32, 32), 12), img_dur=20),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'button/log': Animation(load_sprite_sheet('interface/button/Log.png', (16, 16), 7, 16), img_dur=6,
                                    loop=False),
            'projectile': load_image('projectile.png'),
            'spike_attack': Animation(load_sprite_sheet('weapon/SpikeAttack.png', (32, 32), 10), img_dur=20,
                                      loop=False),
            'slash': pygame.transform.scale(load_image('projectile.png'), (60, 4)),
            'boomer': load_image('weapon/boomer.png'),
            'club': load_image('weapon/club.png'),
            'sawblade': load_image('weapon/sawblade.png'),
            'sword': load_image('weapon/sword.png'),
            'throwingknife': load_image('weapon/throwingknife.png'),
            'bossarrow': Animation(load_sprite_sheet('interface/arrow/BossArrow.png', (32, 32), 12)),
            'sharpeningstone': load_image('upgrades/sharpeningstone.png'),
            'bandage': load_image('upgrades/bandage.png'),
            'magnet': load_image('upgrades/magnet.png'),
            'adrenaline': load_image('upgrades/adrenaline.png'),
            'sneaker': load_image('upgrades/sneaker.png'),
            'sugar': load_image('upgrades/sugar.png'),
            'vitamin': load_image('upgrades/vitamin.png'),
            'coin': Animation(load_sprite_sheet('interface/pickups/Coin.png', (16, 16), 12)),
            'shield_skill': Animation(load_sprite_sheet('skill/ShieldSkill.png', (16, 16), 4)),
            'power_skill': Animation(load_sprite_sheet('skill/PowerSkill.png', (128, 128), 2, 0.5)),
            'slam_skill': Animation(load_sprite_sheet('skill/Slam.png', (128, 128), 8), loop=False),
            'shockwave': Animation(load_sprite_sheet('skill/Wave.png', (128, 128), 4), loop=False)
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        # sprite groups
        self.exp_orbs = pygame.sprite.Group()
        self.gold_coins = pygame.sprite.Group()
        self.auras = pygame.sprite.Group()
        self.visible_enemy = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.graveyard = pygame.sprite.Group()
        self.pointer_group = pygame.sprite.Group()

        self.player = Warrior(self, (0, 0), (8, 15), player_group, self.visible_enemy)

        self.clouds = Clouds(self.assets['clouds'])

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        self.inv_upgrade_pos = [50, 200]
        self.effective_skills = dict()
        self.game_state = set('M')
        self.screenshake = 0
        self.visible_range = list()
        self.spawn_delay = 60
        self.entity_limit = 10
        self.current_delay = 60
        self.shooting = False
        self.victory = False
        self.frame_update = True
        self.mouse_released = True
        self.shop_open = False
        self.shop_loc = tuple()

        # interface
        self.health_bar = Interface(self, self.player, (0, 5))
        self.exp_bar = Interface(self, self.player, size=(self.display.get_width(), 5), bg=(107, 110, 104, 150),
                                 fg=(242, 227, 61, 255))
        self.gold_count = Label(self, (900, 50), self.assets['coin'].img(), 16, '0', dim=(64, 32),
                                offset=(32, 0), bg=None)
        self.boss_health_bar = None
        self.announcement = TextBox('The mushrooms seek vengeance', pygame.font.SysFont('arialblack', 15),
                                    (500, 50))
        self.announce_duration = 0

        # buttons
        self.start_button = Button(self, (540, 120), 40, 'Start', animation=self.assets['button/log'].copy(),
                                   offset=(70, 110))
        self.option_button = Button(self, (540, 300), 40, 'Option', animation=self.assets['button/log'].copy(),
                                    offset=(70, 110))
        self.quit_button = Button(self, (540, 700), 40, 'Quit', animation=self.assets['button/log'].copy(),
                                  offset=(70, 110))
        self.resume_button = Button(self, (540, 120), 40, 'Resume', animation=self.assets['button/log'].copy(),
                                    offset=(64, 110))
        self.restart_button = Button(self, (540, 500), 40, 'Restart', animation=self.assets['button/log'].copy(),
                                     offset=(64, 110))
        self.victory_button = Button(self, (540, 120), 40, 'Victory', animation=self.assets['button/log'].copy(),
                                     offset=(64, 110))
        self.game_over_label = Button(self, (540, 100), 40, 'Game Over', animation=self.assets['button/log'].copy(),
                                      offset=(64, 110))

        # inventory
        self.upgrade_slots = dict()

        # shop
        self.shop_label = TextBox('Shop', pygame.font.SysFont('arialblack', 10), (30, 15),
                                  bg=(69, 49, 23), fg=(219, 187, 24))
        self.shop_close = Button(self, (540, 700), 40, ['close'])
        self.weapon_slots = dict()
        self.refine_costs = dict()

    def load_level(self, map_id=0):
        self.game_state.add('G')
        self.game_state.add('A')
        self.tilemap = Tilemap(self, tile_size=16)
        self.assets['grass_tiles'] = self.tilemap.generate_tile(6)
        self.tilemap.generate_tiles()
        player_group.empty()
        self.player = Warrior(self, (0, 0), (8, 15), player_group, self.visible_enemy)
        WARRIOR_WEAPONS.reset()
        self.skill_select()

        self.scroll = [0, 0]
        self.inv_upgrade_pos = [50, 200]
        self.particles = []
        self.sparks = []
        self.movement = [False, False, False, False]
        self.victory = False
        self.frame_update = True
        self.screenshake = 0
        Enemy.health = 300
        Boss.health = 500
        Boss.max_health = 500
        self.dead = 0
        self.transition = -30
        self.entity_limit = 20
        self.spawn_delay = 60
        self.current_delay = 60
        enemy_group.empty()
        self.exp_orbs.empty()
        self.projectiles.empty()
        self.visible_enemy.empty()
        self.graveyard.empty()
        self.pointer_group.empty()
        boss_group.empty()
        GAME_UPGRADES.reset()
        self.upgrade_slots = dict()
        Boss(self, self.boss_location(False), (8, 10), boss_group, Pointer(self, self.player.rect.center, 'bossarrow'))
        self.boss_health_bar = Interface(self, self.player, (0, self.screen.get_height() - 20),
                                         (self.screen.get_width(), 20), 2000, display=True, name='Mr.Munshroom')

    def add_upgrade(self, upgrade):
        text = [f'{upgrade.name}(Level {upgrade.level})'] + upgrade.effect_description()
        if upgrade.level == 1:
            description = Button(self, [self.inv_upgrade_pos[0] + 200, self.inv_upgrade_pos[1] + 125], 15,
                                 text, (350, 200))
            self.upgrade_slots[upgrade.name] = Icon(self, self.inv_upgrade_pos, [50, 50], source=upgrade.source,
                                                    hover_effect=lambda: description.draw(self.screen))
            self.inv_upgrade_pos = [self.inv_upgrade_pos[0] + 50, self.inv_upgrade_pos[1]]
            upgrade.hover_description = description
        else:
            upgrade.hover_description.update_text(text)

    def upgrade_select(self):
        self.upgrade_choices = GAME_UPGRADES.random_upgrades(3)
        self.upgrade1_button = Label(self, (200, 120), self.assets[self.upgrade_choices[0].source], 20,
                                     [self.upgrade_choices[0].name] + self.upgrade_choices[0].effect_description(),
                                     lambda: self.upgrade_choices[0].effects(self.player))
        self.upgrade2_button = Label(self, (200, 300), self.assets[self.upgrade_choices[1].source], 20,
                                     [self.upgrade_choices[1].name] + self.upgrade_choices[1].effect_description(),
                                     lambda: self.upgrade_choices[1].effects(self.player))
        self.upgrade3_button = Label(self, (200, 480), self.assets[self.upgrade_choices[2].source], 20,
                                     [self.upgrade_choices[2].name] + self.upgrade_choices[2].effect_description(),
                                     lambda: self.upgrade_choices[2].effects(self.player))

    def weapon_select(self):
        self.weapon_choices = WARRIOR_WEAPONS.random_weapons(3)
        self.weapon1_button = Label(self, (200, 120), self.assets[self.weapon_choices[0].source], 20,
                                    [self.weapon_choices[0].name, '', self.weapon_choices[0].description])
        self.weapon2_button = Label(self, (200, 300), self.assets[self.weapon_choices[1].source], 20,
                                    [self.weapon_choices[1].name, '', self.weapon_choices[1].description])
        self.weapon3_button = Label(self, (200, 480), self.assets[self.weapon_choices[2].source], 20,
                                    [self.weapon_choices[2].name, '', self.weapon_choices[2].description])

    def skill_select(self):
        self.skill1_button = Label(self, (200, 120), self.assets['shield_skill'].img(), 20,
                                   ['Shield Up', '', 'Blocks incoming damage'])
        self.skill2_button = Label(self, (200, 300), self.assets['power_skill'].img(), 20,
                                   ['Last Stand', '',
                                    'Rapidly drains your health, in-exchange for stat buffs and', ' immortality'])
        self.skill3_button = Label(self, (200, 480), self.assets['slam_skill'].img(), 20,
                                   ['Shield Slam', '',
                                    'Slam your shield to the ground, stunning and', ' damaging enemies with shock waves'])

    def shop(self):
        for name in self.weapon_slots:
            if self.weapon_slots[name].draw(self.screen, self.mouse_released):
                self.mouse_released = False
            self.refine_costs[name].draw(self.screen)
            self.refine_costs[name].update_image(self.assets['coin'].img(), [str(WARRIOR_WEAPONS.get_weapon(name).refine_cost)])
        self.shop_label.render(self.screen, (540, 50))
        if self.shop_close.draw(self.screen):
            self.shop_open = False
            self.game_state.remove('S')
            self.frame_update = True

    def inventory(self):
        for name in self.upgrade_slots:
            self.upgrade_slots[name].draw(self.screen)

    def menu(self):
        if self.start_button.draw(self.screen):
            self.game_state.clear()
            self.load_level()
        if self.quit_button.draw(self.screen):
            pygame.quit()
            sys.exit()

    def pause(self):
        if self.resume_button.draw(self.screen):
            self.game_state.remove('P')
        if self.restart_button.draw(self.screen):
            self.game_state.clear()
            self.load_level()
        if self.option_button.draw(self.screen):
            pass
        if self.quit_button.draw(self.screen):
            pygame.quit()
            sys.exit()

    def game_over(self):
        self.game_over_label.draw(self.screen)
        if self.restart_button.draw(self.screen):
            self.game_state.clear()
            self.load_level()
        if self.quit_button.draw(self.screen):
            pygame.quit()
            sys.exit()

    def boss_location(self, depend):
        if depend:
            player_loc = self.player.rect.center
            quadrant = (player_loc[0] / player_loc[0], player_loc[1] / player_loc[1])
            boss_quadrant = (-quadrant[0], -quadrant[1])
            boss_loc = (boss_quadrant[0] * random.randint(0, 1600),
                        boss_quadrant[1] * random.randint(0, 1600))
        else:
            boss_loc = (random.randint(-100, 100), random.randint(-100, 100))
        return boss_loc

    def boss_arrow(self, offset=(0, 0)):
        for boss in boss_group.sprites():
            dis = pygame.math.Vector2((boss.rect.center[0] - self.player.rect.center[0],
                                       self.player.rect.center[1] - boss.rect.center[1]))
            if dis.magnitude():
                dis.scale_to_length(100)
            boss.pointer.update(dis, not boss.visibility, self.display, offset)

    def boss_battle(self, current_health, new_max_health):
        self.boss_health_bar.update(current_health, new_max_health).draw(self.screen)

    def victory_screen(self):
        if self.victory_button.draw(self.screen):
            self.game_state = set('M')

    def run(self):
        self.sfx['ambience'].play(-1)

        while True:
            if 'P' in self.game_state:
                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
                self.pause()
            elif 'O' in self.game_state:
                self.game_over()
            elif 'G' in self.game_state:
                self.player.exp_check()
                self.scroll[0] += (self.player.rect.centerx - self.display.get_width() / 2 - self.scroll[0])
                self.scroll[1] += (self.player.rect.centery - self.display.get_height() / 2 - self.scroll[1])
                render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
                # render_scroll = (0, 0)
                self.visible_range = ((render_scroll[0], render_scroll[0] + self.display.get_width()),
                                      (render_scroll[1], render_scroll[1] + self.display.get_height()))

                self.screenshake = max(0, self.screenshake - 1)

                if self.frame_update and not self.current_delay and self.entity_limit and self.tilemap.infected_tiles:
                    spawn = random.choice(list(self.tilemap.infected_tiles.items()))
                    loc = (spawn[1]['pos'][0] * self.tilemap.tile_size, spawn[1]['pos'][1] * self.tilemap.tile_size)
                    if random.randint(0, 3) < 1:
                        Spitter(self, loc, (8, 10), enemy_group)
                    else:
                        Enemy(self, loc, (8, 10), enemy_group)
                    self.current_delay = self.spawn_delay
                    self.entity_limit -= 1
                else:
                    self.current_delay = max(0, self.current_delay - 1)

                self.tilemap.render(self.display, offset=render_scroll)

                self.exp_orbs.update(surf=self.display, offset=render_scroll)
                self.gold_coins.update(surf=self.display, offset=render_scroll)

                if self.shop_open:
                    self.shop_label.render(self.display, (self.shop_loc[0] - render_scroll[0], self.shop_loc[1] - render_scroll[1]))
                    if self.player.rect.collidepoint(self.shop_loc):
                        self.game_state.add('S')

                for projectile in self.projectiles.sprites().copy():
                    projectile.render(self.display, offset=render_scroll)
                    if self.frame_update and projectile.update():
                        projectile.kill()

                for enemy_projectile in self.enemy_projectiles.sprites().copy():
                    enemy_projectile.render(self.display, offset=render_scroll)
                    if self.frame_update and enemy_projectile.update():
                        enemy_projectile.kill()

                for enemy in enemy_group.sprites().copy():
                    enemy.render(self.display, offset=render_scroll)
                    if self.frame_update and enemy.update():
                        enemy.kill()
                        self.entity_limit += 1

                for boss in boss_group.sprites().copy():
                    boss.render(self.display, offset=render_scroll)
                    if self.frame_update and boss.update(render_scroll):
                        boss.kill()
                        boss.add(self.graveyard)
                        Boss(self, self.boss_location(True), (8, 10),
                             boss_group, Pointer(self, self.player.rect.center, 'bossarrow'))
                        Enemy.health *= 1.5
                        Boss.health *= 2
                        Boss.max_health *= 2
                        self.spawn_delay = max(self.spawn_delay - 10, 10)
                        self.entity_limit += 10
                        self.announce_duration = 180

                self.boss_arrow(render_scroll)

                for ghost in self.graveyard.sprites().copy():
                    if self.frame_update and ghost.death_effect():
                        ghost.remove(self.graveyard)

                for key, skill in self.effective_skills.copy().items():
                    if self.frame_update and skill(self.display, render_scroll):
                        self.effective_skills.pop(key)
                if not self.dead:
                    move_vector = pygame.math.Vector2((self.movement[1] - self.movement[0],
                                                       self.movement[3] - self.movement[2]))
                    if self.frame_update:
                        self.player.update(move_vector, offset=render_scroll)
                        self.player.pickup_circle.update(self.display)
                    self.player.render(self.display, offset=render_scroll)
                else:
                    self.game_state.add('O')

                for spark in self.sparks.copy():
                    spark.render(self.display, offset=render_scroll)
                    if self.frame_update and spark.update():
                        self.sparks.remove(spark)

                """
                display_mask = pygame.mask.from_surface(self.display)
                display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
                for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    self.display_2.blit(display_silhouette, offset)
                """
                for particle in self.particles.copy():
                    particle.render(self.display, offset=render_scroll)
                    if self.frame_update and particle.update():
                        self.particles.remove(particle)

                if self.frame_update:
                    self.clouds.update().render(self.display, offset=render_scroll)

                # display interface update
                self.health_bar.update(self.player.health, self.player.max_health).draw(self.display)
                self.exp_bar.update(self.player.exp, self.player.max_exp).draw(self.display)

                self.display_2.blit(self.display, (0, 0))

                screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                      random.random() * self.screenshake - self.screenshake / 2)
                self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)

                # screen interface update
                self.assets['coin'].update()
                self.gold_count.update_image(self.assets['coin'].img(), [str(self.player.gold)]).draw(self.screen,
                                                                                                      False)
                if self.frame_update and self.announce_duration:
                    self.announcement.render(self.screen, (0, 750))
                    self.announce_duration = max(self.announce_duration - 1, 0)

                for boss in boss_group.sprites():
                    if boss.visibility:
                        self.boss_battle(boss.health, boss.max_health)

                if self.victory:
                    self.frame_update = False
                    self.victory_screen()
                if 'A' in self.game_state:
                    self.frame_update = False
                    if self.skill1_button.draw(self.screen, self.mouse_released):
                        self.player.get_skill('shield_skill')
                        self.game_state.remove('A')
                        self.mouse_released = False
                    if self.skill2_button.draw(self.screen, self.mouse_released):
                        self.player.get_skill('power_skill')
                        self.game_state.remove('A')
                        self.mouse_released = False
                    if self.skill3_button.draw(self.screen, self.mouse_released):
                        self.player.get_skill('slam_skill')
                        self.game_state.remove('A')
                        self.mouse_released = False
                elif 'L' in self.game_state:
                    self.frame_update = False
                    if self.player.weapon_status():
                        if self.weapon1_button.draw(self.screen, self.mouse_released):
                            self.player.equip_weapon(self.weapon_choices[0])
                            self.game_state.remove('L')
                            self.frame_update = True
                            self.movement = [False, False, False, False]
                            self.mouse_released = False
                        if self.weapon2_button.draw(self.screen, self.mouse_released):
                            self.player.equip_weapon(self.weapon_choices[1])
                            self.game_state.remove('L')
                            self.frame_update = True
                            self.movement = [False, False, False, False]
                            self.mouse_released = False
                        if self.weapon3_button.draw(self.screen, self.mouse_released):
                            self.player.equip_weapon(self.weapon_choices[2])
                            self.game_state.remove('L')
                            self.frame_update = True
                            self.movement = [False, False, False, False]
                            self.mouse_released = False
                    else:
                        if self.upgrade1_button.draw(self.screen, self.mouse_released):
                            upgrade_picked = self.upgrade_choices[0]
                            GAME_UPGRADES.add_stack(upgrade_picked)
                            self.add_upgrade(upgrade_picked)
                            self.game_state.remove('L')
                            self.frame_update = True
                            self.movement = [False, False, False, False]
                            self.mouse_released = False
                        if self.upgrade2_button.draw(self.screen, self.mouse_released):
                            upgrade_picked = self.upgrade_choices[1]
                            GAME_UPGRADES.add_stack(upgrade_picked)
                            self.add_upgrade(upgrade_picked)
                            self.game_state.remove('L')
                            self.frame_update = True
                            self.movement = [False, False, False, False]
                            self.mouse_released = False
                        if self.upgrade3_button.draw(self.screen, self.mouse_released):
                            upgrade_picked = self.upgrade_choices[2]
                            GAME_UPGRADES.add_stack(upgrade_picked)
                            self.add_upgrade(upgrade_picked)
                            self.game_state.remove('L')
                            self.frame_update = True
                            self.movement = [False, False, False, False]
                            self.mouse_released = False
                elif 'S' in self.game_state:
                    self.frame_update = False
                    self.shop()
                if 'I' in self.game_state:
                    self.inventory()
            elif 'M' in self.game_state:
                self.menu()

            if pygame.mouse.get_pressed()[0] == 0:
                self.mouse_released = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:
                        self.player.dash()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_x:
                        self.player.dash()
                    if event.key == pygame.K_ESCAPE:
                        if 'G' in self.game_state and 'L' not in self.game_state:
                            self.game_state.add('P')
                    if event.key == pygame.K_i:
                        if 'I' in self.game_state:
                            self.game_state.remove('I')
                        else:
                            self.game_state.add('I')
                    if event.key == pygame.K_q:
                        self.effective_skills['q'] = self.player.skill_setup()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False

            pygame.display.update()
            self.clock.tick(60)


# print(pygame.font.get_fonts())
Game().run()
