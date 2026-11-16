import json
import math
import os
import random

import pygame

from systems import plants as P
from systems.player import Player
from systems.state import GameState, SPOTS_PER_BIOME
from systems.ui import UI, CREAM, GOLD, GREEN
from systems.world import World, TS


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SAVE_PATH = os.path.join(BASE_DIR, "save.json")

FAIL_COLOR = (255, 170, 140)

DIRECTIONS = {
    "down": (0, 1),
    "up": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}


class Game:

    def __init__(self, fonts, load_saved=True):

        self.ui_font = fonts["ui"]

        # Персонаж, карта и вся игровая логика
        self.player = Player()
        self.world = World()
        self.state = GameState()
        self.ui = UI(fonts, self.world)

        # Открытое окно: None, "inventory", "book" или "shop"
        self.modal = None
        self.toasts = []
        self.hint = ""

        self.player.bounds = (self.world.width, self.world.height)
        self.place_player(*self.world.spawn)

        if load_saved:
            self.load_game()

        if not self.state.spots:
            self.regenerate_spots()

        self.victory_announced = self.state.is_complete()

    # ==============================
    # СООБЩЕНИЯ
    # ==============================

    def say(self, text, color=CREAM):

        self.toasts.append({"text": text, "color": color, "time": 3.5})
        self.toasts = self.toasts[-4:]

    # ==============================
    # СОХРАНЕНИЕ
    # ==============================

    def place_player(self, x, y, direction="down"):

        self.player.x = x
        self.player.y = y
        self.player.direction = direction
        self.player.current_frame = 0
        self.player.image = self.player.frames[direction][0]

        self.player.rect = self.player.image.get_rect(
            center=(int(x), int(y))
        )

    def save_game(self):

        data = {
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "direction": self.player.direction
            },
            "state": self.state.to_dict()
        }

        try:

            with open(SAVE_PATH, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

        except OSError as error:

            print("Ошибка сохранения:", error)

    def load_game(self):

        if not os.path.exists(SAVE_PATH):

            print("Сохранение не найдено. Начинаем новую игру.")
            return

        try:

            with open(SAVE_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)

        except (OSError, ValueError) as error:

            print("Не удалось загрузить сохранение:", error)
            return

        # Игровое состояние: день, инвентарь, грядки, коллекция
        self.state.load_dict(data.get("state"))

        # Позиция персонажа
        try:

            player_data = data["player"]

            x = float(player_data["x"])
            y = float(player_data["y"])

            if not (0 <= x <= self.world.width
                    and 0 <= y <= self.world.height):
                raise ValueError("Некорректная позиция персонажа")

            direction = player_data.get("direction", "down")

            if direction not in DIRECTIONS:
                direction = "down"

            x = max(32, min(self.world.width - 32, x))
            y = max(32, min(self.world.height - 32, y))

            # Если старое сохранение попало в воду или в дерево,
            # возвращаем персонажа на тропу у фермы
            if self.world.blocked(x, y):
                x, y = self.world.spawn

            self.place_player(x, y, direction)

            print("Сохранение успешно загружено!")

        except (ValueError, TypeError, KeyError) as error:

            print("Не удалось загрузить позицию:", error)

    # ==============================
    # МЕСТА ДЛЯ ПОИСКА РАСТЕНИЙ
    # ==============================

    def regenerate_spots(self):
        # Каждый день места поиска выбираются заново случайным образом

        spots = []

        for biome in P.BIOMES:

            tiles = self.world.spot_candidates(biome)
            count = min(SPOTS_PER_BIOME, len(tiles))

            for tx, ty in random.sample(tiles, count):
                spots.append({"biome": biome, "tx": tx, "ty": ty})

        self.state.spots = spots

    def feet(self):
        return self.player.x, self.player.y + 24

    def nearest_spot(self):

        fx, fy = self.feet()
        best = None
        best_dist = 62

        for spot in self.state.spots:

            sx = spot["tx"] * TS + TS / 2
            sy = spot["ty"] * TS + TS / 2

            dist = math.hypot(fx - sx, fy - sy)

            if dist < best_dist:
                best = spot
                best_dist = dist

        return best

    def near(self, point, distance):
        fx, fy = self.feet()
        return math.hypot(fx - point[0], fy - point[1]) < distance

    # ==============================
    # ДЕЙСТВИЯ ИГРОКА
    # ==============================

    def target_tile(self):
        # Тайл перед персонажем

        fx, fy = self.feet()
        dx, dy = DIRECTIONS[self.player.direction]

        return int((fx + dx * 30) // TS), int((fy + dy * 30) // TS)

    def select_tool(self, tool):

        state = self.state

        if tool == "plant":

            if state.tool == "plant":
                state.cycle_plant(1)
            else:
                state.tool = "plant"
                state.fix_selection()

            if state.selected_plant:
                self.say("В руке: %s" %
                         P.BY_ID[state.selected_plant]["name"])
            else:
                self.say("Нет растений. Найдите их в биомах", FAIL_COLOR)

            return

        state.tool = tool
        self.say("В руке: %s" % ("Лопата" if tool == "shovel" else "Лейка"))

    def use_tool(self):

        tile = self.target_tile()
        in_field = self.world.in_field(*tile)

        ok, message = self.state.use_tool(tile, in_field)

        self.say(message, CREAM if ok else FAIL_COLOR)

    def interact(self):

        if self.near(self.world.merchant_pos, 100):
            self.open_modal("shop")
            return

        spot = self.nearest_spot()

        if spot:
            self.forage(spot)
            return

        if self.near(self.world.door_pos, 80):

            result = self.state.sleep()

            if result is None:
                self.say("Спать можно с 19:00 до утра", FAIL_COLOR)
            else:
                self.on_new_day(result)

    def forage(self, spot):

        plant, is_new = self.state.forage(spot["biome"])
        self.state.spots.remove(spot)

        text = "Найдено: %s (%s)" % (
            plant["name"], P.RARITY_NAMES[plant["rarity"]]
        )

        if is_new:
            text += " - новое!"

        self.say(text, P.RARITY_COLORS[plant["rarity"]])

    def on_new_day(self, result):

        self.regenerate_spots()

        self.say("Наступил день %d" % result["day"], GOLD)

        if result["grown"]:
            self.say("Выросло растений: %d" % len(result["grown"]), GREEN)

        for plant_id in result["new"]:
            self.say("В коллекции: %s" % P.BY_ID[plant_id]["name"], GOLD)

        self.say("Торговец обновил товары")

        if self.state.is_complete() and not self.victory_announced:

            self.victory_announced = True
            self.say("Коллекция собрана на 100%! Вы прошли игру!", GOLD)

    # ==============================
    # ОКНА
    # ==============================

    def open_modal(self, kind):

        self.modal = kind
        self.ui.open_modal(kind)

        if self.player.footstep_channel:
            self.player.footstep_channel.stop()

    def close_modal(self):
        self.modal = None

    # ==============================
    # СОБЫТИЯ И ОБНОВЛЕНИЕ
    # ==============================

    def handle_event(self, event):

        if self.modal:

            if self.ui.handle_modal(event, self):
                self.close_modal()

            return None

        if event.type == pygame.KEYDOWN:

            key = event.key

            if key == pygame.K_ESCAPE:

                self.save_game()

                if self.player.footstep_channel:
                    self.player.footstep_channel.stop()

                return "menu"

            if key == pygame.K_1:
                self.select_tool("shovel")

            elif key == pygame.K_2:
                self.select_tool("can")

            elif key == pygame.K_3:
                self.select_tool("plant")

            elif key == pygame.K_i:
                self.open_modal("inventory")

            elif key == pygame.K_b:
                self.open_modal("book")

            elif key == pygame.K_e:
                self.interact()

            elif key == pygame.K_SPACE:
                self.use_tool()

        return None

    def compute_hint(self):

        if self.near(self.world.merchant_pos, 100):
            return "E - поговорить с Странником"

        if self.nearest_spot():
            return "E - искать растение"

        if self.near(self.world.door_pos, 80):

            if self.state.is_night_for_sleep():
                return "E - лечь спать"

            return "Дом: спать можно с 19:00"

        return ""

    def update(self, dt):

        for toast in self.toasts:
            toast["time"] -= dt

        self.toasts = [t for t in self.toasts if t["time"] > 0]

        # Пока открыто окно, время и персонаж стоят
        if self.modal:
            return

        self.world.update(dt)
        self.player.update(dt, self.world)

        result = self.state.advance(dt)

        if result:
            self.on_new_day(result)

        self.hint = self.compute_hint()

    # ==============================
    # ОТРИСОВКА
    # ==============================

    def spot_items(self):

        items = []

        for spot in self.state.spots:

            image = self.world.spot_surface(spot["biome"])
            x, y = spot["tx"] * TS, spot["ty"] * TS

            items.append((y + TS - 20, image, x, y, None))

        return items

    def draw_target(self, screen, camera):

        tx, ty = self.target_tile()

        if not self.world.in_field(tx, ty):
            return

        rect = pygame.Rect(tx * TS - camera[0], ty * TS - camera[1], TS, TS)

        pygame.draw.rect(screen, (255, 240, 170), rect, 2)

    def draw(self, screen):

        width, height = screen.get_size()
        camera = self.world.camera(self.player, width, height)

        # Карта, грядки, места поиска и персонаж рисуются вместе,
        # чтобы персонаж заходил за деревья и дом
        self.world.draw(screen, self.player, camera,
                        self.state.plots, self.spot_items())

        self.draw_target(screen, camera)

        # День и ночь
        self.ui.draw_lighting(screen, self.state, camera)

        hint = "" if self.modal else self.hint

        self.ui.draw_hud(screen, self.state, hint, self.toasts)

        if self.modal:
            self.ui.draw_modal(screen, self)
