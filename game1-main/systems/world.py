import json
import math
import os
import random

import pygame

from systems import plants


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TILES_DIR = os.path.join(BASE_DIR, "assets", "tiles")

# Размер тайла в наборе, масштаб на экране и итоговый размер тайла
T = 16
SCALE = 3
TS = T * SCALE

# Размер карты в тайлах
COLS = 48
ROWS = 28

# Участок фермы, где можно делать грядки (тайлы внутри забора).
# Центральный столбец 24 — тропа, тайл (26, 13) занят пугалом.
FIELD_SET = {
    (x, y) for y in range(10, 18) for x in range(20, 30)
    if x != 24 and (x, y) != (26, 13)
}

# Тайл, где стоит торговец (в лесу, недалеко от моста)
MERCHANT_TILE = (8, 21)

OUTLINE = "#3b2a1a"

# Область столкновений для спрайтов: (x, y, ширина, высота) в пикселях тайла.
# Деревья блокируют только ствол, чтобы можно было пройти под кроной.
BLOCKS = {
    "tree_oak": (5, 10, 6, 5),
    "tree_apple": (5, 10, 6, 5),
    "tree_orange": (5, 10, 6, 5),
    "tree_autumn": (5, 10, 6, 5),
    "bush": (2, 6, 12, 8),
    "berry_bush": (2, 6, 12, 8),
    "rock": (2, 6, 12, 8),
    "stump": (3, 6, 10, 8),
    "log": (1, 7, 14, 7),
    "barrel": (2, 3, 12, 12),
    "crate": (2, 3, 12, 12),
    "hay_bale": (1, 3, 14, 12),
    "haystack": (2, 3, 12, 12),
    "trough": (1, 4, 14, 10),
    "wheelbarrow": (2, 5, 12, 9),
    "well": (1, 3, 14, 13),
    "mailbox": (5, 8, 6, 6),
    "signpost": (5, 9, 6, 6),
    "scarecrow": (5, 10, 6, 5),
    "fence_horizontal": (0, 6, 16, 8),
    "fence_vertical": (5, 0, 6, 16),
    "fence_post": (5, 2, 6, 12),
}


def river_x(y):
    # Столбец, где у реки начинается вода (ширина 2 тайла)
    return 13 + round(2 * math.sin(y / 3.2))


def snow_x(y):
    # Столбец, где начинается зима
    return 33 + round(math.sin(y / 2.7) * 1.3)


def fill(surface, x, y, w, h, color):
    surface.fill(pygame.Color(color) if isinstance(color, str) else color,
                 (x, y, w, h))


def recolor(tile, low, high):
    # Перекрашивает тайл по яркости, сохраняя его текстуру.
    # Так из травы получается снег, а из воды лёд.
    out = tile.copy()
    pixels = [(x, y) for x in range(T) for y in range(T)]
    lum = {p: sum(out.get_at(p)[:3]) for p in pixels}
    lo, hi = min(lum.values()), max(lum.values())
    span = (hi - lo) or 1

    for p in pixels:
        t = (lum[p] - lo) / span
        color = [int(low[k] + (high[k] - low[k]) * t) for k in range(3)]
        out.set_at(p, (*color, 255))

    return out


def make_pine():
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    layers = [2, 4, 6, 4, 6, 8, 6, 8, 10, 12]

    fill(s, 7, 11, 2, 4, "#5b3a20")
    fill(s, 7, 0, 2, 1, "#1c3b2c")

    for i, w in enumerate(layers):
        fill(s, 7 - w // 2, i + 1, w + 2, 1, "#1c3b2c")

    fill(s, 2, 11, 12, 1, "#1c3b2c")

    for i, w in enumerate(layers):
        if i % 3 == 0:
            color = "#ffffff"
        else:
            color = "#2f6b4a" if i % 2 else "#3f8a5c"

        fill(s, 8 - w // 2, i + 1, w, 1, color)

    return s


def make_snowman():
    s = pygame.Surface((T, T), pygame.SRCALPHA)

    fill(s, 3, 14, 10, 1, (0, 0, 0, 40))
    fill(s, 3, 7, 10, 8, OUTLINE)
    fill(s, 4, 8, 8, 6, "#ffffff")
    fill(s, 4, 12, 8, 2, "#dbe7f2")
    fill(s, 4, 2, 8, 7, OUTLINE)
    fill(s, 5, 3, 6, 5, "#ffffff")
    fill(s, 6, 4, 1, 1, "#222222")
    fill(s, 9, 4, 1, 1, "#222222")
    fill(s, 10, 5, 3, 1, "#f08a24")
    fill(s, 4, 8, 8, 2, "#dd3333")
    fill(s, 5, 0, 6, 2, "#222222")

    return s


def make_merchant():
    # Загадочный торговец в тёмном плаще с фонарём и посохом
    s = pygame.Surface((T, T), pygame.SRCALPHA)

    fill(s, 2, 3, 1, 11, "#6b4a2b")
    fill(s, 1, 2, 3, 2, "#7ae0ff")
    fill(s, 3, 9, 10, 5, "#4b3577")
    fill(s, 4, 5, 8, 5, "#4b3577")
    fill(s, 5, 1, 6, 5, "#3a2a5a")
    fill(s, 6, 2, 4, 3, "#150d24")
    fill(s, 6, 3, 1, 1, "#ffe066")
    fill(s, 9, 3, 1, 1, "#ffe066")
    fill(s, 3, 13, 10, 1, "#c9a24a")
    fill(s, 12, 7, 2, 1, "#555555")
    fill(s, 12, 8, 2, 3, "#ffcf55")

    out = s.copy()

    for x in range(T):
        for y in range(T):
            if s.get_at((x, y))[3] != 0:
                continue

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy

                if (0 <= nx < T and 0 <= ny < T
                        and s.get_at((nx, ny))[3] > 0):
                    out.set_at((x, y), (25, 18, 35, 255))
                    break

    return out


def make_spot(biome, step):
    # Место, где можно найти растение: пучок травы с мерцанием
    s = pygame.Surface((T, T), pygame.SRCALPHA)

    grass = {"forest": "#3f9a6a", "meadow": "#5fb84a", "winter": "#9fd0e8"}
    spark = {"forest": "#9ff7d0", "meadow": "#fff3a0", "winter": "#ffffff"}

    fill(s, 4, 12, 8, 2, (0, 0, 0, 40))
    fill(s, 4, 9, 2, 4, grass[biome])
    fill(s, 7, 6, 2, 7, grass[biome])
    fill(s, 10, 8, 2, 5, grass[biome])
    fill(s, 5, 11, 6, 2, grass[biome])

    x, y = [(3, 4), (11, 3), (12, 8), (2, 9)][step % 4]

    fill(s, x, y - 1, 1, 3, spark[biome])
    fill(s, x - 1, y, 3, 1, spark[biome])

    return s


def make_bridge():
    s = pygame.Surface((T, T))

    s.fill(pygame.Color("#a9763f"))

    for i in (4, 8, 12):
        fill(s, i, 0, 1, T, "#7a5129")

    fill(s, 0, 0, T, 2, OUTLINE)
    fill(s, 0, 14, T, 2, OUTLINE)

    return s


def make_building(house):
    # Дом (house=True) или амбар. Поверхность 70x62, начало здания в (3, 12).
    s = pygame.Surface((70, 62), pygame.SRCALPHA)
    x, y, w = 3, 12, 64

    if house:
        wall, wall_dark = "#e0c08e", "#c9a572"
        roof, roof_hi, roof_lo = "#b5402f", "#d9573a", "#8c2f20"
    else:
        wall, wall_dark = "#a8342a", "#7e2620"
        roof, roof_hi, roof_lo = "#7a3030", "#96413f", "#5a2222"

    fill(s, x + 2, y + 46, w + 2, 3, (0, 0, 0, 50))
    fill(s, x, y + 20, w, 28, OUTLINE)
    fill(s, x + 1, y + 21, w - 2, 26, wall)
    fill(s, x + 1, y + 43, w - 2, 4, wall_dark)

    if house:
        fill(s, x + 46, y - 3, 8, 10, OUTLINE)
        fill(s, x + 47, y - 2, 6, 9, "#8a8a8a")
        fill(s, x + 47, y - 8, 3, 3, (255, 255, 255, 200))
        fill(s, x + 50, y - 12, 3, 3, (255, 255, 255, 140))

    fill(s, x - 3, y + 3, w + 6, 19, OUTLINE)
    fill(s, x - 2, y + 4, w + 4, 17, roof)
    fill(s, x - 2, y + 4, w + 4, 2, roof_hi)

    for i in range(3):
        fill(s, x - 2, y + 10 + i * 4, w + 4, 1, roof_lo)

    if house:
        fill(s, x + 34, y + 30, 12, 18, OUTLINE)
        fill(s, x + 35, y + 31, 10, 17, "#6b3f22")
        fill(s, x + 43, y + 40, 1, 1, "#f0c040")

        for ox in (8, 50):
            fill(s, x + ox, y + 28, 10, 9, OUTLINE)
            fill(s, x + ox + 1, y + 29, 8, 7, "#8fd3f4")
            fill(s, x + ox + 5, y + 29, 1, 7, OUTLINE)
    else:
        fill(s, x + 20, y + 26, 24, 22, OUTLINE)
        fill(s, x + 21, y + 27, 22, 21, "#f3e9d2")
        fill(s, x + 31, y + 27, 2, 21, wall)
        fill(s, x + 21, y + 36, 22, 2, wall)
        fill(s, x + 27, y + 10, 10, 8, OUTLINE)
        fill(s, x + 28, y + 11, 8, 6, "#2a1a14")

    return s


class World:

    def __init__(self, seed=7):

        self.cols = COLS
        self.rows = ROWS
        self.width = COLS * TS
        self.height = ROWS * TS

        # Место появления игрока: на тропе у фермы
        self.spawn = (24 * TS + TS // 2, 21 * TS)

        self.time = 0.0
        self.rng = random.Random(seed)

        self.load_tiles()
        self.create_world()

    # ==============================
    # ЗАГРУЗКА ТАЙЛОВ
    # ==============================

    def load_tiles(self):

        sheet = pygame.image.load(
            os.path.join(TILES_DIR, "spritesheet.png")
        ).convert_alpha()

        with open(
            os.path.join(TILES_DIR, "frames.json"),
            "r",
            encoding="utf-8"
        ) as file:
            frames = json.load(file)

        self.native = {}

        for name, (x, y) in frames.items():

            tile = pygame.Surface((T, T), pygame.SRCALPHA)
            tile.blit(sheet, (0, 0), (x, y, T, T))

            self.native[name] = tile

        self.scaled = {}

    def big(self, surface):
        return pygame.transform.scale(
            surface,
            (surface.get_width() * SCALE, surface.get_height() * SCALE)
        )

    def tile(self, name):

        if name not in self.scaled:
            self.scaled[name] = self.big(self.native[name])

        return self.scaled[name]

    # ==============================
    # СОЗДАНИЕ КАРТЫ
    # ==============================

    def create_world(self):

        rng = self.rng

        self.objects = []
        self.blocks = []
        self.animals = []
        self.water_tiles = []
        self.water_set = set()
        self.lights = []
        self._spot_cache = {}
        self._spot_surfaces = {}

        def pick(items):
            return rng.choice(items)

        def jitter(n):
            return rng.randrange(n) - n // 2

        def add(sort_y, surface, x, y):
            self.objects.append(
                (sort_y, surface, x, y, surface.get_rect(topleft=(x, y)))
            )

        def block(x, y, w, h):
            self.blocks.append(pygame.Rect(x, y, w, h))

        def sprite(name, tx, ty, ox=0, oy=0, sort_offset=0):
            # Обычный спрайт из набора, который стоит на карте
            x = tx * TS + ox * SCALE
            y = ty * TS + oy * SCALE

            add(y + TS + sort_offset, self.tile(name), x, y)

            if name in BLOCKS:
                bx, by, bw, bh = BLOCKS[name]
                block(x + bx * SCALE, y + by * SCALE,
                      bw * SCALE, bh * SCALE)

        def custom(surface, tx, ty, ox=0, oy=0):
            # Нарисованный в коде спрайт 16x16, например ель
            x = tx * TS + ox * SCALE
            y = ty * TS + oy * SCALE
            add(y + TS, self.big(surface), x, y)
            return x, y

        def farm_zone(x, y):
            return 17 <= x <= 32 and 2 <= y <= 23

        def in_lake(x, y):
            return ((x - 41) / 5) ** 2 + ((y - 19) / 3.4) ** 2 < 1

        # ---------- земля ----------

        snow_tiles = [
            recolor(self.native["grass_%d" % i],
                    (196, 216, 236), (255, 255, 255))
            for i in (1, 2, 3)
        ]

        ice_tiles = [
            recolor(self.native["water_%d" % i],
                    (146, 198, 234), (236, 247, 255))
            for i in (1, 2, 3)
        ]

        self.snow = [self.big(t) for t in snow_tiles]
        self.ice = [self.big(t) for t in ice_tiles]
        self.water_frames = [self.tile("water_%d" % i) for i in (1, 2, 3)]

        grid = []

        for y in range(ROWS):

            row = []
            rv = river_x(y)
            sx = snow_x(y)

            for x in range(COLS):

                if x in (rv, rv + 1):
                    g = "W%d" % rng.randrange(3)

                elif x in (rv - 1, rv + 2):
                    g = "sand"

                elif x < rv - 1:
                    g = "grass_dark"

                elif x >= sx - 3 and rng.random() < (x - sx + 3) / 6:
                    g = "S%d" % rng.randrange(3)

                elif rng.random() < 0.1:
                    g = pick([
                        "grass_flowers_white",
                        "grass_flowers_red",
                        "grass_flowers_blue"
                    ])

                else:
                    g = pick(["grass_1", "grass_1", "grass_2", "grass_3"])

                if g[0] == "S" and in_lake(x, y):
                    g = "I" + g[1]

                row.append(g)

            grid.append(row)

        # Тропа, мост и поле
        for y in range(6, 25):
            grid[y][24] = "path_gravel"

        bridge_x = river_x(24)

        for x in range(bridge_x + 3, 38):
            grid[24][x] = "path_gravel"

        bridge_tiles = range(bridge_x - 1, bridge_x + 3)

        for y in range(10, 18):
            for x in range(20, 30):
                if (x, y) in FIELD_SET:
                    grid[y][x] = "grass_2"

        # Рисуем землю один раз на большую поверхность
        self.ground = pygame.Surface((self.width, self.height))

        for y in range(ROWS):
            for x in range(COLS):

                g = grid[y][x]
                k = int(g[1]) if g[0] in "WSI" and g[1:].isdigit() else 0

                if g[0] == "W":
                    surface = self.water_frames[k]

                    # Под мостом вода не анимируется и не перерисовывается:
                    # раньше она закрывала мост
                    if not (y == 24 and x in bridge_tiles):
                        self.water_tiles.append((x, y, k))
                        self.water_set.add((x, y))

                elif g[0] == "S" and g[1:].isdigit():
                    surface = self.snow[k]

                elif g[0] == "I" and g[1:].isdigit():
                    surface = self.ice[k]

                else:
                    surface = self.tile(g)

                self.ground.blit(surface, (x * TS, y * TS))

        bridge = self.big(make_bridge())

        for x in bridge_tiles:
            self.ground.blit(bridge, (x * TS, 24 * TS))

        self.grid = grid
        self.bridge_tiles = list(bridge_tiles)

        # ---------- ферма ----------

        sprite("scarecrow", 26, 13)

        for x in range(20, 30):
            for y in (9, 18):
                sprite("gate_open" if x == 24 else "fence_horizontal", x, y)

        for y in range(10, 18):
            for x in (19, 30):
                sprite("fence_vertical", x, y)

        for x in (19, 30):
            for y in (9, 18):
                sprite("fence_post", x, y)

        # Дом и амбар
        for tx, house in ((22, True), (27, False)):

            surface = self.big(make_building(house))
            x = tx * TS - 3 * SCALE
            y = 3 * TS - 12 * SCALE

            add((3 * T + 49) * SCALE, surface, x, y)
            block(tx * TS, (3 * T + 3) * SCALE, 64 * SCALE, 45 * SCALE)

        props = [
            ("well", 20, 6), ("bucket", 21, 6), ("mailbox", 26, 6),
            ("barrel", 26, 5), ("crate", 26, 4), ("hay_bale", 31, 5),
            ("hay_bale", 31, 4), ("haystack", 32, 4), ("trough", 31, 6),
            ("wheelbarrow", 22, 8), ("signpost", 18, 23),
            ("egg_basket", 29, 6)
        ]

        for name, x, y in props:
            sprite(name, x, y)

        # Торговец в лесу, рядом ящик и бочка
        mx, my = MERCHANT_TILE
        px, py = custom(make_merchant(), mx, my)
        block(px + 3 * SCALE, py + 4 * SCALE, 10 * SCALE, 11 * SCALE)
        sprite("crate", mx + 1, my + 1)
        sprite("barrel", mx - 1, my + 1)

        self.merchant_pos = (px + 8 * SCALE, py + 12 * SCALE)
        self.lights.append((px + 13 * SCALE, py + 9 * SCALE, 130))

        # Окна дома светятся ночью, дверь нужна для сна
        self.lights.append(((22 * T + 13) * SCALE, (3 * T + 32) * SCALE, 90))
        self.lights.append(((22 * T + 55) * SCALE, (3 * T + 32) * SCALE, 90))
        self.door_pos = ((22 * T + 37) * SCALE, (3 * T + 49) * SCALE)

        # Животные. Позиция в тайлах плюс смещение в пикселях тайла.
        animals = [
            ("cow", 21, 20, 0, 0), ("cow", 23, 22, 6, -2),
            ("pig", 27, 21, 0, 0), ("sheep", 29, 20, 4, 0),
            ("sheep", 26, 22, -2, 3), ("chicken", 21, 7, 0, 6),
            ("chicken", 23, 7, 8, 2), ("chicken", 28, 7, 4, 8),
            ("chicken", 30, 7, 0, 2)
        ]

        for i, (name, tx, ty, ox, oy) in enumerate(animals):
            self.animals.append({
                "name": name,
                "x": tx * TS + ox * SCALE,
                "y": ty * TS + oy * SCALE,
                "index": i
            })

        # ---------- лес, луг, зима ----------

        for y in range(ROWS):

            rv = river_x(y)
            sx = snow_x(y)

            # Лес слева от реки. Ряд с мостом оставляем свободным.
            if y != 24:
                for x in range(0, rv - 1):

                    # Вокруг торговца оставляем поляну
                    if (abs(x - MERCHANT_TILE[0]) <= 2
                            and abs(y - MERCHANT_TILE[1]) <= 2):
                        continue

                    q = rng.random()

                    if q < 0.5:
                        t = rng.random()
                        name = ("tree_oak" if t < 0.55 else
                                "tree_apple" if t < 0.67 else
                                "tree_orange" if t < 0.77 else
                                "tree_autumn")
                        sprite(name, x, y, jitter(5), jitter(5))

                    elif q < 0.6:
                        sprite(pick(["bush", "mushroom", "stump", "log",
                                     "rock", "berry_bush"]), x, y)

            # Кувшинки на реке
            if y < 23 or y > 25:
                for x in (rv, rv + 1):
                    if rng.random() < 0.07:
                        sprite("lily_pad", x, y, sort_offset=-TS)

            # Луг между рекой и зимой
            for x in range(rv + 3, sx - 3):

                if farm_zone(x, y) or y == 24 or x == 24:
                    continue

                q = rng.random()

                if q < 0.2:
                    sprite(pick(["tree_oak", "tree_apple", "tree_oak"]),
                           x, y, jitter(5), 0)

                elif q < 0.3:
                    sprite(pick(["flower_red", "flower_yellow",
                                 "flower_blue", "flower_pink",
                                 "bush", "rock"]),
                           x, y, jitter(7), jitter(5))

            # Зимние ели и камни
            for x in range(sx, COLS):

                if grid[y][x][0] != "S" or y == 24:
                    continue

                if abs(x - 38) < 2 and abs(y - 7) < 2:
                    continue

                q = rng.random()
                ox = jitter(5)

                if q < 0.3:
                    px, py = custom(make_pine(), x, y, ox, 0)
                    block(px + 6 * SCALE, py + 10 * SCALE,
                          4 * SCALE, 5 * SCALE)

                elif q < 0.34:
                    sprite("rock", x, y)

        # Снеговик
        px, py = custom(make_snowman(), 38, 7)
        block(px + 3 * SCALE, py + 7 * SCALE, 10 * SCALE, 8 * SCALE)

        self.objects.sort(key=lambda item: item[0])

    # ==============================
    # ОБНОВЛЕНИЕ И СТОЛКНОВЕНИЯ
    # ==============================

    def update(self, dt):
        self.time += dt

    def blocked(self, x, y):
        # Проверяем ступни персонажа (x, y — центр спрайта 64x64)
        feet = pygame.Rect(0, 0, 22, 12)
        feet.center = (int(x), int(y) + 24)

        if (feet.left < 0 or feet.top < 0
                or feet.right > self.width or feet.bottom > self.height):
            return True

        for tx in range(feet.left // TS, (feet.right - 1) // TS + 1):
            for ty in range(feet.top // TS, (feet.bottom - 1) // TS + 1):
                if (tx, ty) in self.water_set:
                    return True

        return feet.collidelist(self.blocks) != -1

    def camera(self, player, view_w, view_h):
        cx = int(player.x - view_w / 2)
        cy = int(player.y - view_h / 2)

        cx = max(0, min(self.width - view_w, cx))
        cy = max(0, min(self.height - view_h, cy))

        return cx, cy

    # ==============================
    # БИОМЫ И МЕСТА ДЛЯ ПОИСКА
    # ==============================

    def biome_of(self, tx, ty):

        if not (0 <= tx < COLS and 0 <= ty < ROWS):
            return None

        if tx < river_x(ty) - 1:
            return "forest"

        ground = self.grid[ty][tx]

        if ground[0] in "SI" and ground[1:].isdigit():
            return "winter"

        if tx > river_x(ty) + 2:
            return "meadow"

        return None

    def in_field(self, tx, ty):
        return (tx, ty) in FIELD_SET

    def spot_candidates(self, biome):
        # Свободные тайлы биома: без деревьев, построек, тропы и фермы.
        # Считаем один раз и запоминаем.

        if biome in self._spot_cache:
            return self._spot_cache[biome]

        found = []

        for ty in range(1, ROWS - 1):
            for tx in range(1, COLS - 1):

                if self.biome_of(tx, ty) != biome or ty == 24:
                    continue

                ground = self.grid[ty][tx]

                if ground == "path_gravel" or ground[0] == "I":
                    continue

                if 17 <= tx <= 32 and 2 <= ty <= 23:
                    continue

                if (abs(tx - MERCHANT_TILE[0]) <= 3
                        and abs(ty - MERCHANT_TILE[1]) <= 3):
                    continue

                rect = pygame.Rect(tx * TS, ty * TS, TS, TS)

                if rect.collidelist(self.blocks) != -1:
                    continue

                center = rect.center

                if any(o[4].collidepoint(center) for o in self.objects):
                    continue

                found.append((tx, ty))

        self._spot_cache[biome] = found

        return found

    def spot_surface(self, biome):

        step = int(self.time / 0.35) % 4
        key = (biome, step)

        if key not in self._spot_surfaces:
            self._spot_surfaces[key] = self.big(make_spot(biome, step))

        return self._spot_surfaces[key]

    # ==============================
    # ОТРИСОВКА
    # ==============================

    def draw(self, screen, player, camera, plots=None, extra=()):

        cx, cy = camera
        view_w, view_h = screen.get_size()
        view = pygame.Rect(cx, cy, view_w, view_h)

        screen.blit(self.ground, (0, 0), view)

        step = int(self.time / 0.6)

        for tx, ty, k in self.water_tiles:

            x, y = tx * TS, ty * TS

            if view.colliderect((x, y, TS, TS)):
                screen.blit(self.water_frames[(k + step) % 3],
                            (x - cx, y - cy))

        # Грядки и растения на них лежат прямо на земле
        if plots:

            for (tx, ty), plot in plots.items():

                x, y = tx * TS, ty * TS

                if not view.colliderect((x, y, TS, TS)):
                    continue

                soil = "soil_tilled_wet" if plot["watered"] \
                    else "soil_tilled_dry"

                screen.blit(self.tile(soil), (x - cx, y - cy))

                if plot["plant"]:

                    if plot["mature"]:
                        image = plants.icon(plot["plant"], SCALE)
                    else:
                        image = self.tile("carrot_stage1")

                    screen.blit(image, (x - cx, y - cy))

        items = [item for item in self.objects
                 if view.colliderect(item[4])]

        for animal in self.animals:

            frame = 1 + (step + animal["index"]) % 2
            surface = self.tile("%s_%d" % (animal["name"], frame))
            x, y = animal["x"], animal["y"]

            if view.colliderect((x, y, TS, TS)):
                items.append((y + TS, surface, x, y, None))

        for sort_y, surface, x, y, _ in extra:

            if view.colliderect((x, y, surface.get_width(),
                                 surface.get_height())):
                items.append((sort_y, surface, x, y, None))

        # Игрок рисуется в общей очереди, чтобы заходить за деревья и дом
        items.append((int(player.y) + 26, player.image,
                      player.rect.x, player.rect.y, None))

        items.sort(key=lambda item: item[0])

        for _, surface, x, y, _ in items:
            screen.blit(surface, (x - cx, y - cy))
