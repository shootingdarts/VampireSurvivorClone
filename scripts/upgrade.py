import random

from scripts.button import Button, Icon


class Upgrade:
    def __init__(self, name, description, source, *effects):
        self.name = name
        self.description = description
        self.effects = self.total_effect(effects)
        self.effect_list = effects
        self.level = 0
        self.max_level = 5
        self.source = source
        self.hover_description = None

    @staticmethod
    def single_effect(effect, player):
        stat, percent = effect
        amount = 1 + percent / 100
        if stat == 'health':
            player.max_health = player.max_health * amount
            player.health *= amount
        elif stat == 'speed':
            player.speed = player.speed * amount
        elif stat == 'damage':
            player.damage_multi = player.damage_multi * amount
        elif stat == 'attack_speed':
            player.attack_speed = player.attack_speed * amount
        elif stat == 'health_regen':
            player.health_regen = player.health_regen * amount
        elif stat == 'pickup_range':
            player.pickup_range = player.pickup_range * amount
            player.pickup_circle.adjust(player.pickup_range)

    def total_effect(self, effects):
        def apply(player):
            for effect in effects:
                Upgrade.single_effect(effect, player)
        return apply

    def effect_description(self):
        return [f'Increase {effect[0]} by {effect[1]}%' if self.level == 0 else f'Increase {effect[0]} by {effect[1] * self.level} (+{effect[1]})%' for effect in self.effect_list]


class Upgrades:
    def __init__(self):
        self.slot_pos_y = 150
        self.available_upgrades = dict()
        self.maxed_upgrades = dict()

    def add_upgrade(self, upgrade):
        self.available_upgrades[upgrade.name] = upgrade

    def add_stack(self, upgrade):
        upgrade.level += 1
        if upgrade.level == upgrade.max_level:
            self.available_upgrades.pop(upgrade.name)

    def random_upgrades(self, count):
        selection = random.sample(list(self.available_upgrades.keys()), k=count)
        upgrade_selection = []
        for name in selection:
            upgrade_selection.append(self.available_upgrades[name])
        return upgrade_selection

    def reset(self):
        for name in self.available_upgrades:
            self.available_upgrades[name].level = 0
        for name in self.maxed_upgrades:
            self.maxed_upgrades[name].level = 0
            self.add_upgrade(self.maxed_upgrades[name])


GAME_UPGRADES = Upgrades()
GAME_UPGRADES.add_upgrade(Upgrade('Sharpening Stone', 'Sharpens weapon', 'sharpeningstone', ('damage', 10)))
GAME_UPGRADES.add_upgrade(Upgrade('Vitamin', 'Makes you healthy', 'vitamin', ('health', 10)))
GAME_UPGRADES.add_upgrade(Upgrade('Bandage', 'Heals you', 'bandage', ('health_regen', 100)))
GAME_UPGRADES.add_upgrade(Upgrade('Sneakers', 'Help you run faster', 'sneaker', ('speed', 10)))
GAME_UPGRADES.add_upgrade(Upgrade('Sugar', 'Induces sugar rush', 'sugar', ('attack_speed', 30)))
GAME_UPGRADES.add_upgrade(Upgrade('Adrenaline', 'Increase your reflex', 'adrenaline', ('attack_speed', 15), ('damage', 5)))
GAME_UPGRADES.add_upgrade(Upgrade('Magnet', 'Grabs things from far away', 'magnet', ('pickup_range', 30)))

