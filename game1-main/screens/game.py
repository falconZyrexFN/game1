import json
import math
import os
import random

import pygame

from screens.help import HelpScreen
from systems import plants as P
from systems.player import Player
from systems.state import (
    GameState, SPOTS_PER_BIOME, WATER_MAX, HOURS_PER_SECOND
)
from systems.ui import UI, CREAM, GOLD, GREEN
from systems.world import World, TS


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SAVE_PATH = os.path.join(BASE_DIR, "save.json")

FAIL_COLOR = (255, 170, 140)

# Сон: затемнение, пауза, плавный рассвет
SLEEP_OUT = 1.0
SLEEP_HOLD = 1.1
SLEEP_IN = 3.4

# С какого часа начинается рассвет и сколько игровых часов он длится.
# Новый день наступает в 6:00, посередине рассвета.
WAKE_START = 4.5
WAKE_HOURS = 2.6

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
        self.dig_tile = None
        self.water_tile = None
        self.transition = None
        self.help = HelpScreen(fonts)

        self.player.bounds = (self.world.width, self.world.height)
        self.place_player(*self.world.spawn)

        if load_saved:
            self.load_game()

        if not self.state.spots:
            self.regenerate_spots()

        self.victory_announced = self.state.is_complete()

        # Какие виды уже учтены: новые улетают в книгу
        self.seen_discovered = set(self.state.discovered)
        self.screen_size = (1280, 720)

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

        names = {"shovel": "Лопата", "can": "Лейка", "hoe": "Мотыга"}
        self.say("В руке: %s" % names[tool])

    def use_tool(self):

        tile = self.target_tile()
        in_field = self.world.in_field(*tile)

        # Новую грядку копают в мини-игре
        if self.state.needs_dig(tile, in_field):

            self.dig_tile = tile
            self.open_modal("dig")

            return

        # Полив: сначала проверяем, есть ли что поливать, потом мини-игра
        if self.state.tool == "can":

            ok, message = self.state.can_water(tile)

            if not ok:
                self.say(message, FAIL_COLOR)
                return

            self.water_tile = tile
            self.ui.water_plant = self.state.plots[tile]["plant"]
            self.open_modal("water")

            return

        ok, message = self.state.use_tool(tile, in_field)

        self.say(message, CREAM if ok else FAIL_COLOR)

    def finish_dig(self, hits):

        ok, message = self.state.make_bed(self.dig_tile, hits)

        if not ok:
            color = FAIL_COLOR
        elif hits >= 3:
            color = GOLD
        else:
            color = CREAM

        self.say(message, color)
        self.close_modal()

    def finish_water(self, score):

        ok, message = self.state.water_plot(self.water_tile, score)

        if not ok:
            color = FAIL_COLOR
        elif score >= 0.8:
            color = GOLD
        else:
            color = CREAM

        self.say(message, color)
        self.close_modal()

    def glow_points(self):
        # Места, с которыми можно взаимодействовать, светятся

        state = self.state
        world = self.world

        def near(point, distance):
            return self.near(point, distance)

        return [
            {"pos": (world.merchant_pos[0], world.merchant_pos[1] - 20),
             "radius": 72, "color": (190, 150, 255), "strength": 0.85,
             "near": near(world.merchant_pos, 100), "phase": 0.0},

            {"pos": world.well_pos, "radius": 64, "color": (110, 205, 255),
             "strength": 0.9 if state.water < WATER_MAX else 0.4,
             "near": near(world.well_pos, 90), "phase": 1.3},

            {"pos": (world.station_pos[0], world.station_pos[1] - 6),
             "radius": 70, "color": (255, 140, 225), "strength": 0.9,
             "near": near(world.station_pos, 90), "phase": 2.1},

            {"pos": (world.door_pos[0], world.door_pos[1] - 20),
             "radius": 72, "color": (255, 220, 140),
             "strength": 0.95 if state.is_night_for_sleep() else 0.35,
             "near": near(world.door_pos, 80), "phase": 3.4},
        ]

    def interact(self):

        if self.near(self.world.merchant_pos, 100):
            self.open_modal("shop")
            return

        # Колодец: набираем воду в лейку
        if self.near(self.world.well_pos, 90):

            ok, message = self.state.fill_can()
            self.say(message, CREAM if ok else FAIL_COLOR)

            return

        # Стол скрещивания
        if self.near(self.world.station_pos, 90):
            self.open_modal("cross")
            return

        spot = self.nearest_spot()

        if spot:
            self.forage(spot)
            return

        if self.near(self.world.door_pos, 80):

            if not self.state.is_night_for_sleep():
                self.say("Спать можно с 19:00 до утра", FAIL_COLOR)
            else:
                self.start_sleep()

    # ==============================
    # СОН И ПЕРЕХОД К НОВОМУ ДНЮ
    # ==============================

    def start_sleep(self):

        self.transition = {"phase": "out", "t": 0.0}

        if self.player.footstep_channel:
            self.player.footstep_channel.stop()

    def update_transition(self, dt):

        tr = self.transition
        tr["t"] += dt

        if tr["phase"] == "out":

            if tr["t"] >= SLEEP_OUT:
                tr["phase"] = "hold"
                tr["t"] = 0.0

                # Экран чёрный: переносим время в глубокую ночь
                self.state.time = WAKE_START

        elif tr["phase"] == "hold":

            if tr["t"] >= SLEEP_HOLD:
                tr["phase"] = "in"
                tr["t"] = 0.0

        else:

            # Рассвет: время плавно бежит до утра, а в 6:00 наступает
            # новый день с ростом растений и новым ассортиментом
            result = self.state.advance(
                dt * (WAKE_HOURS / SLEEP_IN) / HOURS_PER_SECOND
            )

            if result:
                self.on_new_day(result)

            if tr["t"] >= SLEEP_IN:
                self.transition = None

    def draw_transition(self, screen):

        tr = self.transition

        if tr["phase"] == "out":
            alpha = 255 * tr["t"] / SLEEP_OUT
        elif tr["phase"] == "hold":
            alpha = 255
        else:
            alpha = 255 * (1 - tr["t"] / SLEEP_IN)

        if tr["phase"] == "in" and self.state.time >= 6.0:
            lines = [("Утро. День %d" % self.state.day, self.ui.f22, GOLD)]
        else:
            lines = [("Zzz...", self.ui.f22, CREAM)]

        self.ui.draw_fade(screen, alpha, lines)

    def forage(self, spot):

        plant, is_new = self.state.forage(spot["biome"])
        self.state.spots.remove(spot)

        if is_new:
            self.fly_to_book(plant["id"], self.spot_screen_pos(spot))

        text = "Найдено: %s (%s)" % (
            plant["name"], P.RARITY_NAMES[plant["rarity"]]
        )

        if is_new:
            text += " - новое!"

        self.say(text, P.RARITY_COLORS[plant["rarity"]])

    def spot_screen_pos(self, spot):

        width, height = self.screen_size
        camera = self.world.camera(self.player, width, height)

        return (spot["tx"] * TS + TS / 2 - camera[0],
                spot["ty"] * TS + TS / 2 - camera[1])

    def fly_to_book(self, plant_id, origin=None):

        self.seen_discovered.add(plant_id)

        if origin is None:
            # Покупка или скрещивание: растение вылетает из центра экрана
            width, height = self.screen_size
            origin = (width // 2, height // 2)

        self.ui.add_flight(plant_id, origin)

    def check_new_species(self):

        for plant_id in self.state.discovered - self.seen_discovered:
            self.fly_to_book(plant_id)

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

        # Во время сна управление отключено
        if self.transition:
            return None

        if self.modal == "help":

            closed = self.help.handle_event(event)

            if closed == "back" or (event.type == pygame.KEYDOWN
                                    and event.key == pygame.K_h):
                self.close_modal()

            return None

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

            elif key == pygame.K_4:
                self.select_tool("hoe")

            elif key == pygame.K_i:
                self.open_modal("inventory")

            elif key == pygame.K_b:
                self.open_modal("book")

            elif key == pygame.K_h:
                self.help.open()
                self.open_modal("help")

            elif key == pygame.K_e:
                self.interact()

            elif key == pygame.K_SPACE:
                self.use_tool()

        return None

    def compute_hint(self):

        if self.near(self.world.merchant_pos, 100):
            return "E - поговорить с Странником"

        if self.near(self.world.well_pos, 90):
            return "E - набрать воды (%d/%d)" % (self.state.water, WATER_MAX)

        if self.near(self.world.station_pos, 90):
            return "E - стол скрещивания"

        if self.nearest_spot():
            return "E - искать растение"

        if self.near(self.world.door_pos, 80):

            if self.state.is_night_for_sleep():
                return "E - лечь спать"

            return "Дом: спать можно с 19:00"

        # Что растёт на грядке перед персонажем
        plot = self.state.plots.get(self.target_tile())

        if plot:

            rich = " (богатая)" if plot.get("rich") else ""

            if plot.get("super"):
                rich += " (супергрядка)"

            if not plot["plant"]:
                return "Грядка%s: посадите растение (3)" % rich

            name = P.BY_ID[plot["plant"]]["name"]

            if plot["mature"]:
                status = "готово, соберите лопатой"
            elif plot["watered"]:
                status = "полито, вырастет к утру"
            else:
                status = "нужен полив (лейка)"

            return "%s%s: %s" % (name, rich, status)

        return ""

    def update(self, dt):

        # Полоска коллекции и полёт растений идут даже при открытых окнах
        self.check_new_species()
        self.ui.update_hud(dt, self.state)

        for toast in self.toasts:
            toast["time"] -= dt

        self.toasts = [t for t in self.toasts if t["time"] > 0]

        # Сон: идёт затемнение и плавный рассвет
        if self.transition:
            self.update_transition(dt)
            return

        # Мини-игре нужно время, остальные окна ставят игру на паузу
        if self.modal == "dig":
            self.ui.update_dig(dt, self)
            return

        if self.modal == "water":
            self.ui.update_water(dt, self)
            return

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
        self.screen_size = (width, height)
        camera = self.world.camera(self.player, width, height)

        # Карта, грядки, места поиска и персонаж рисуются вместе,
        # чтобы персонаж заходил за деревья и дом
        self.world.draw(screen, self.player, camera,
                        self.state.plots, self.spot_items())

        self.draw_target(screen, camera)

        # День и ночь
        self.ui.draw_lighting(screen, self.state, camera)

        # Сияние поверх ночного затемнения, чтобы места были заметны
        self.ui.draw_glows(screen, self.glow_points(), camera,
                           self.world.time)

        hint = "" if self.modal else self.hint

        self.ui.draw_hud(screen, self.state, hint, self.toasts)

        if self.modal == "help":
            self.help.draw(screen, None, clear=False)
        elif self.modal:
            self.ui.draw_modal(screen, self)

        self.ui.draw_flights(screen)

        if self.transition:
            self.draw_transition(screen)
