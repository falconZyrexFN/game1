import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SAVE_PATH = os.path.join(BASE_DIR, "save.json")

# ==============================
# БИОМЫ И РЕДКОСТЬ
# ==============================

BIOMES = ["forest", "meadow", "winter"]

BIOME_NAMES = {
    "forest": "Лес",
    "meadow": "Луг",
    "winter": "Зима",
    "cross": "Скрещивание"
}

RARITIES = ["common", "uncommon", "rare", "legendary"]

RARITY_NAMES = {
    "common": "Обычное",
    "uncommon": "Необычное",
    "rare": "Редкое",
    "legendary": "Легендарное",
    "super": "Суперредкое"
}

RARITY_COLORS = {
    "common": (205, 205, 195),
    "uncommon": (120, 210, 110),
    "rare": (100, 160, 255),
    "legendary": (255, 190, 60),
    "super": (255, 120, 220)
}

# Цена покупки у торговца. Продажа стоит вдвое меньше.
BUY_PRICE = {
    "common": 12,
    "uncommon": 30,
    "rare": 80,
    "legendary": 300,
    "super": 150
}

# Шанс найти растение такой редкости при сборе в биоме
FORAGE_WEIGHT = {
    "common": 60,
    "uncommon": 28,
    "rare": 10,
    "legendary": 2
}

# Вес одного вида в ассортименте торговца
STOCK_WEIGHT = {
    "common": 10,
    "uncommon": 5,
    "rare": 1.2,
    "legendary": 0.3
}

# ==============================
# СПИСОК РАСТЕНИЙ (45 видов)
# id, название, биом, редкость, форма, цвет 1, цвет 2
# ==============================

_RAW = [
    # ---- Лес ----
    ("fern", "Папоротник", "forest", "common", "fern", "#3f9a4a", "#2f7a3a"),
    ("strawberry", "Лесная земляника", "forest", "common", "berry", "#e04058", "#ffd0d8"),
    ("moss_cushion", "Мох-подушка", "forest", "common", "moss", "#4f9a45", "#8bd067"),
    ("sorrel", "Кислица", "forest", "common", "clover", "#58b04a", "#a0e090"),
    ("honey_fungus", "Опёнок", "forest", "common", "mushroom", "#c9a063", "#f0dcb0"),
    ("lingonberry", "Брусника", "forest", "common", "berry", "#a82640", "#e87a90"),
    ("chanterelle", "Лисичка", "forest", "uncommon", "mushroom", "#f0a030", "#ffd890"),
    ("bluebell", "Колокольчик", "forest", "uncommon", "bell", "#6a8bd8", "#e0e8ff"),
    ("lily_valley", "Ландыш", "forest", "uncommon", "bell", "#f4f4ee", "#ffe8a0"),
    ("blueberry", "Черничник", "forest", "uncommon", "berry", "#4a5ab8", "#a0b0ff"),
    ("moon_agaric", "Лунный мухомор", "forest", "rare", "mushroom", "#9a5ad8", "#7af0ff"),
    ("shade_orchid", "Тенистая орхидея", "forest", "rare", "tulip", "#c04ac0", "#ffd0ff"),
    ("glow_fern", "Светящийся папоротник", "forest", "rare", "fern", "#5fe0d0", "#2f9a9a"),
    ("forest_heart", "Сердце леса", "forest", "legendary", "lotus", "#58d070", "#ffe070"),
    ("spirit_tree", "Древо-душа", "forest", "legendary", "pine", "#58e0c0", "#ffe070"),
    # ---- Луг ----
    ("daisy", "Ромашка", "meadow", "common", "daisy", "#ffffff", "#f5c842"),
    ("dandelion", "Одуванчик", "meadow", "common", "daisy", "#ffd633", "#e0a000"),
    ("clover", "Клевер", "meadow", "common", "clover", "#4fae45", "#e8a0d8"),
    ("plantain", "Подорожник", "meadow", "common", "fern", "#8bc34a", "#5a9a30"),
    ("buttercup", "Лютик", "meadow", "common", "tulip", "#ffe14d", "#fff3a0"),
    ("oat", "Колосок", "meadow", "common", "wheat", "#c8c860", "#9aa040"),
    ("poppy", "Мак", "meadow", "uncommon", "tulip", "#e03030", "#301818"),
    ("cornflower", "Василёк", "meadow", "uncommon", "daisy", "#4a78e0", "#c0d0ff"),
    ("lavender", "Лаванда", "meadow", "uncommon", "wheat", "#9a6ad8", "#d0b0ff"),
    ("calendula", "Календула", "meadow", "uncommon", "daisy", "#ff9a2a", "#ffd070"),
    ("golden_wheat", "Золотой колос", "meadow", "rare", "wheat", "#ffc933", "#e09a10"),
    ("dawn_tulip", "Тюльпан-рассвет", "meadow", "rare", "tulip", "#ff7a8a", "#ffd070"),
    ("dahlia", "Георгин", "meadow", "rare", "daisy", "#ff5ab0", "#ffe070"),
    ("sunflower", "Солнечный цветок", "meadow", "legendary", "sunflower", "#ffc82a", "#6b3f1a"),
    ("rainbow_bud", "Радужный бутон", "meadow", "legendary", "tulip", "#ff7ad9", "#7ad9ff"),
    # ---- Зима ----
    ("snowflower", "Снежноцвет", "winter", "common", "daisy", "#f0f6ff", "#a0c8f0"),
    ("ice_moss", "Ледяной мох", "winter", "common", "moss", "#9fd0e8", "#e8f6ff"),
    ("hellebore", "Морозник", "winter", "common", "clover", "#d8f0e8", "#8fc8a8"),
    ("frost_pine", "Хвойный росток", "winter", "common", "pine", "#2f8a5a", "#e8f6ff"),
    ("holly", "Падуб", "winter", "common", "berry", "#d03038", "#2f7a4a"),
    ("rime_grass", "Иней-трава", "winter", "common", "fern", "#d0e8f8", "#8ab8d8"),
    ("rime_berry", "Иней-ягода", "winter", "uncommon", "berry", "#a0c8ff", "#ffffff"),
    ("snow_bell", "Снежный колокольчик", "winter", "uncommon", "bell", "#bcd8f4", "#ffffff"),
    ("silver_fir", "Серебряная ель", "winter", "uncommon", "pine", "#a8c8d8", "#e8f6ff"),
    ("ice_tulip", "Ледяной тюльпан", "winter", "uncommon", "tulip", "#8fd8f0", "#ffffff"),
    ("ice_lotus", "Ледяной лотос", "winter", "rare", "lotus", "#7ae0f8", "#e8fcff"),
    ("crystal_lily", "Хрустальная лилия", "winter", "rare", "crystal", "#8ad8ff", "#e8fcff"),
    ("star_rime", "Звёздный иней", "winter", "rare", "crystal", "#c0a0ff", "#f0e8ff"),
    ("blizzard_heart", "Сердце вьюги", "winter", "legendary", "crystal", "#6af0d8", "#fff0a0"),
    ("aurora", "Северное сияние", "winter", "legendary", "lotus", "#ff7ad9", "#7affb0"),
    # ---- Суперрастения: только скрещивание, растут на особой грядке ----
    ("moon_dandelion", "Лунный одуванчик", "cross", "super", "daisy", "#b8d4ff", "#fff0a0"),
    ("ember_lotus", "Закатный лотос", "cross", "super", "lotus", "#ff7a3a", "#ffd060"),
    ("crystal_fern", "Хрустальный папоротник", "cross", "super", "fern", "#8ae8ff", "#ffffff"),
    ("golden_strawberry", "Золотая земляника", "cross", "super", "berry", "#ffcf33", "#fff3b0"),
    ("frost_orchid", "Морозная орхидея", "cross", "super", "tulip", "#9ad8ff", "#e0c8ff"),
    ("sky_wheat", "Небесный колос", "cross", "super", "wheat", "#9ab8ff", "#f0e8ff"),
]

PLANTS = [
    {
        "id": r[0], "name": r[1], "biome": r[2], "rarity": r[3],
        "shape": r[4], "c1": r[5], "c2": r[6]
    }
    for r in _RAW
]

BY_ID = {p["id"]: p for p in PLANTS}

BY_BIOME = {
    b: [p for p in PLANTS if p["biome"] == b] for b in BIOMES
}

TOTAL = len(PLANTS)

# Дикие растения можно найти и купить, суперрастения только скрестить
WILD = [p for p in PLANTS if p["rarity"] != "super"]
SUPER = [p for p in PLANTS if p["rarity"] == "super"]
WILD_TOTAL = len(WILD)

# Рецепты скрещивания: (растение 1, растение 2, результат).
# Порядок родителей не важен.
RECIPES = [
    ("dandelion", "moon_agaric", "moon_dandelion"),
    ("poppy", "ice_lotus", "ember_lotus"),
    ("fern", "crystal_lily", "crystal_fern"),
    ("strawberry", "golden_wheat", "golden_strawberry"),
    ("snowflower", "shade_orchid", "frost_orchid"),
    ("lavender", "star_rime", "sky_wheat"),
]

_RECIPE_MAP = {frozenset((a, b)): r for a, b, r in RECIPES}


def is_super(plant_id):
    return BY_ID[plant_id]["rarity"] == "super"


def cross_result(a, b):
    if a == b:
        return None

    return _RECIPE_MAP.get(frozenset((a, b)))


def recipe_parents(result_id):

    for a, b, r in RECIPES:
        if r == result_id:
            return a, b

    return None


def recipe_hint(result_id):
    # Подсказка без названий: биомы и редкость родителей

    a, b = recipe_parents(result_id)
    parts = []

    for pid in (a, b):
        plant = BY_ID[pid]
        parts.append("%s (%s)" % (
            BIOME_NAMES[plant["biome"]].lower(),
            RARITY_NAMES[plant["rarity"]].lower()
        ))

    return " + ".join(parts)


def buy_price(plant_id):
    return BUY_PRICE[BY_ID[plant_id]["rarity"]]


def sell_price(plant_id):
    return BUY_PRICE[BY_ID[plant_id]["rarity"]] // 2


def saved_summary():
    # Для главного меню: (есть ли сохранение, номер дня в нём)

    if not os.path.exists(SAVE_PATH):
        return False, 0

    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        return True, int(data["state"]["day"])

    except (OSError, ValueError, KeyError, TypeError):
        return True, 0


def saved_progress():
    # Для главного меню: сколько видов выращено по файлу сохранения
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        grown = data["state"]["grown"]

        return len([g for g in grown if g in BY_ID]), TOTAL

    except (OSError, ValueError, KeyError, TypeError):
        return 0, TOTAL


# ==============================
# ИКОНКИ РАСТЕНИЙ
# Модели рисуются в коде (systems/plant_art.py) на холсте 48x48.
# icon(id, scale) даёт картинку 16*scale пикселей.
# ==============================

ART_SIZE = 48
OUTLINE_COLOR = (28, 34, 30, 255)

_cache = {}


class _Pen:
    # Перо для рисования на pygame.Surface (общий интерфейс с plant_art)

    def __init__(self, surface):
        import pygame

        self.s = surface
        self.pg = pygame

    def circle(self, color, pos, radius):
        self.pg.draw.circle(
            self.s, color, (round(pos[0]), round(pos[1])),
            max(1, round(radius))
        )

    def ellipse(self, color, cx, cy, rx, ry):
        self.pg.draw.ellipse(
            self.s, color,
            self.pg.Rect(round(cx - rx), round(cy - ry),
                         max(1, round(2 * rx)), max(1, round(2 * ry)))
        )

    def poly(self, color, points):
        self.pg.draw.polygon(
            self.s, color, [(round(x), round(y)) for x, y in points]
        )

    def line(self, color, a, b, width=1):
        self.pg.draw.line(
            self.s, color, (round(a[0]), round(a[1])),
            (round(b[0]), round(b[1])), max(1, int(width))
        )


def _layer():
    import pygame

    return pygame.Surface((ART_SIZE, ART_SIZE), pygame.SRCALPHA)


def _outlined(layer):
    # Тёмный контур по краю фигуры
    import pygame

    mask = pygame.mask.from_surface(layer)
    shape = mask.to_surface(setcolor=OUTLINE_COLOR, unsetcolor=(0, 0, 0, 0))
    out = _layer()

    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out.blit(shape, (dx, dy))

    out.blit(layer, (0, 0))

    return out


def _resize(base, size):
    # 48 - родной размер, 96 - вдвое крупнее без размытия,
    # остальное плавно из 96, чтобы картинка оставалась чёткой
    import pygame

    if size == ART_SIZE:
        return base

    big = pygame.transform.scale(base, (ART_SIZE * 2, ART_SIZE * 2))

    if size == ART_SIZE * 2:
        return big

    return pygame.transform.smoothscale(big, (size, size))


def _body(plant_id):
    # Само растение с контуром, без свечения
    key = ("body", plant_id)

    if key not in _cache:

        from systems import plant_art

        plant = BY_ID[plant_id]
        layer = _layer()

        plant_art.render_plant(_Pen(layer), plant, PLANTS.index(plant))

        _cache[key] = _outlined(layer)

    return _cache[key]


def base_icon(plant_id):
    # Растение со свечением у редких видов и блёстками у легендарных
    key = ("base", plant_id)

    if key not in _cache:

        from systems import plant_art

        plant = BY_ID[plant_id]
        final = _layer()

        plant_art.render_aura(_Pen(final), plant)
        final.blit(_body(plant_id), (0, 0))
        plant_art.render_sparkles(_Pen(final), plant)

        _cache[key] = final

    return _cache[key]


def icon(plant_id, scale=3):
    key = ("icon", plant_id, scale)

    if key not in _cache:
        _cache[key] = _resize(base_icon(plant_id), 16 * scale)

    return _cache[key]


def sprout_icon(plant_id, stage, scale=3):
    # Росток своего цвета: stage "seed" (посажено) или "sprout" (полито)
    key = ("sprout", plant_id, stage, scale)

    if key not in _cache:

        from systems import plant_art

        layer = _layer()
        plant_art.render_sprout(_Pen(layer), BY_ID[plant_id], stage)

        _cache[key] = _resize(_outlined(layer), 16 * scale)

    return _cache[key]


def silhouette(plant_id, scale=3):
    # Тёмный силуэт для неизвестных растений
    key = ("sil", plant_id, scale)

    if key not in _cache:
        import pygame

        mask = pygame.mask.from_surface(_body(plant_id))
        shape = mask.to_surface(
            setcolor=(28, 30, 38, 255), unsetcolor=(0, 0, 0, 0)
        )

        _cache[key] = _resize(shape, 16 * scale)

    return _cache[key]
