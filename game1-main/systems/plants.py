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
# РИСОВАНИЕ ИКОНОК РАСТЕНИЙ
# Все иконки 16x16 рисуются в коде, поэтому файлы не нужны.
# ==============================

GREEN = "#3f8a4a"


def _f(surface, x, y, w, h, color):
    import pygame
    surface.fill(pygame.Color(color), (x, y, w, h))


def _daisy(s, c1, c2):
    _f(s, 7, 8, 2, 7, GREEN)
    _f(s, 4, 11, 3, 2, GREEN)
    _f(s, 9, 10, 3, 2, GREEN)

    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3),
                   (-2, -2), (2, -2), (-2, 2), (2, 2)):
        _f(s, 8 + dx - 1, 5 + dy - 1, 2, 2, c1)

    _f(s, 7, 4, 3, 3, c2)


def _bell(s, c1, c2):
    _f(s, 7, 9, 2, 6, GREEN)
    _f(s, 9, 12, 4, 2, GREEN)
    _f(s, 5, 3, 6, 5, c1)
    _f(s, 4, 7, 8, 2, c1)
    _f(s, 7, 9, 2, 1, c2)
    _f(s, 6, 4, 2, 2, c2)


def _tulip(s, c1, c2):
    _f(s, 7, 9, 2, 6, GREEN)
    _f(s, 4, 11, 3, 3, GREEN)
    _f(s, 9, 11, 3, 3, GREEN)
    _f(s, 5, 3, 6, 6, c1)
    _f(s, 5, 2, 2, 1, c1)
    _f(s, 9, 2, 2, 1, c1)
    _f(s, 7, 4, 2, 4, c2)


def _mushroom(s, c1, c2):
    _f(s, 6, 8, 4, 6, "#f0e6d0")
    _f(s, 5, 13, 6, 2, "#d8c8a8")
    _f(s, 4, 8, 8, 1, "#e8dcc0")
    _f(s, 3, 4, 10, 4, c1)
    _f(s, 5, 3, 6, 1, c1)
    _f(s, 5, 5, 2, 1, c2)
    _f(s, 9, 6, 2, 1, c2)


def _fern(s, c1, c2):
    _f(s, 7, 3, 2, 12, GREEN)

    for i in range(5):
        w = min(4, 2 + i)
        color = c1 if i % 2 == 0 else c2
        _f(s, 7 - w, 3 + i * 2, w, 1, color)
        _f(s, 9, 3 + i * 2, w, 1, color)


def _berry(s, c1, c2):
    _f(s, 4, 3, 3, 2, GREEN)
    _f(s, 9, 3, 3, 2, GREEN)
    _f(s, 6, 2, 4, 2, GREEN)
    _f(s, 7, 4, 2, 4, GREEN)

    for x, y in ((3, 8), (9, 8), (6, 11)):
        _f(s, x, y, 4, 4, c1)
        _f(s, x + 1, y + 1, 1, 1, c2)


def _moss(s, c1, c2):
    _f(s, 3, 10, 10, 4, c1)
    _f(s, 4, 8, 8, 2, c1)
    _f(s, 6, 7, 4, 1, c1)

    for x, y in ((5, 9), (9, 8), (7, 11), (11, 11), (4, 12)):
        _f(s, x, y, 1, 1, c2)


def _clover(s, c1, c2):
    _f(s, 7, 9, 2, 6, GREEN)
    _f(s, 3, 5, 4, 4, c1)
    _f(s, 9, 5, 4, 4, c1)
    _f(s, 6, 2, 4, 4, c1)
    _f(s, 7, 6, 2, 2, c2)


def _wheat(s, c1, c2):
    _f(s, 7, 3, 2, 12, GREEN)
    _f(s, 9, 11, 4, 1, GREEN)
    _f(s, 4, 10, 3, 1, GREEN)
    _f(s, 7, 1, 2, 2, c1)

    for y in (3, 5, 7):
        _f(s, 5, y, 2, 2, c1)
        _f(s, 9, y, 2, 2, c2)


def _sunflower(s, c1, c2):
    _f(s, 7, 9, 2, 6, GREEN)
    _f(s, 4, 11, 3, 2, GREEN)
    _f(s, 9, 12, 3, 2, GREEN)
    _f(s, 4, 2, 8, 8, c1)
    _f(s, 3, 4, 10, 4, c1)
    _f(s, 6, 4, 4, 4, c2)


def _crystal(s, c1, c2):
    _f(s, 3, 12, 4, 2, GREEN)
    _f(s, 9, 12, 4, 2, GREEN)
    _f(s, 7, 11, 2, 4, GREEN)
    _f(s, 3, 7, 2, 4, c1)
    _f(s, 11, 6, 2, 5, c1)
    _f(s, 3, 6, 2, 1, c2)
    _f(s, 11, 5, 2, 1, c2)

    for x, y, w, h in ((7, 1, 2, 1), (6, 2, 4, 1), (5, 3, 6, 2),
                       (5, 5, 6, 2), (6, 7, 4, 1), (7, 8, 2, 2)):
        _f(s, x, y, w, h, c1)

    _f(s, 6, 3, 2, 3, c2)


def _lotus(s, c1, c2):
    _f(s, 2, 12, 12, 2, GREEN)
    _f(s, 7, 2, 2, 9, c1)
    _f(s, 5, 4, 2, 7, c1)
    _f(s, 9, 4, 2, 7, c1)
    _f(s, 3, 7, 2, 4, c1)
    _f(s, 11, 7, 2, 4, c1)
    _f(s, 7, 5, 2, 5, c2)


def _pine(s, c1, c2):
    _f(s, 7, 11, 2, 4, "#6b4a2b")

    for i, w in enumerate([2, 4, 6, 4, 6, 8, 6, 8]):
        _f(s, 8 - w // 2, 1 + i, w, 1, c1 if i % 2 == 0 else c2)


SHAPES = {
    "daisy": _daisy, "bell": _bell, "tulip": _tulip,
    "mushroom": _mushroom, "fern": _fern, "berry": _berry,
    "moss": _moss, "clover": _clover, "wheat": _wheat,
    "sunflower": _sunflower, "crystal": _crystal,
    "lotus": _lotus, "pine": _pine
}

_cache = {}


def _outline(surface):
    # Тёмный контур по краю, как в наборе тайлов
    w, h = surface.get_size()
    out = surface.copy()

    for x in range(w):
        for y in range(h):
            if surface.get_at((x, y))[3] != 0:
                continue

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy

                if (0 <= nx < w and 0 <= ny < h
                        and surface.get_at((nx, ny))[3] > 0):
                    out.set_at((x, y), (35, 40, 38, 255))
                    break

    return out


def base_icon(plant_id):
    key = ("base", plant_id)

    if key not in _cache:
        import pygame

        plant = BY_ID[plant_id]
        surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        SHAPES[plant["shape"]](surface, plant["c1"], plant["c2"])
        result = _outline(surface)

        # Суперрастения блестят
        if plant["rarity"] == "super":
            for x, y in ((2, 2), (1, 3), (3, 3), (2, 4),
                         (13, 5), (12, 6), (14, 6), (13, 7)):
                result.set_at((x, y), (255, 255, 255, 255))

        _cache[key] = result

    return _cache[key]


def icon(plant_id, scale=3):
    key = ("icon", plant_id, scale)

    if key not in _cache:
        import pygame

        _cache[key] = pygame.transform.scale(
            base_icon(plant_id), (16 * scale, 16 * scale)
        )

    return _cache[key]


def sprout_icon(plant_id, stage, scale=3):
    # Росток своего цвета: по бутону видно, что именно растёт.
    # stage: "seed" (только посажено) или "sprout" (полито, растёт).
    key = ("sprout", plant_id, stage, scale)

    if key not in _cache:
        import pygame

        plant = BY_ID[plant_id]
        c1, c2 = plant["c1"], plant["c2"]
        s = pygame.Surface((16, 16), pygame.SRCALPHA)

        if stage == "seed":
            _f(s, 5, 12, 6, 2, "#5b3a20")
            _f(s, 6, 11, 4, 1, "#6e4a2c")
            _f(s, 7, 9, 2, 3, GREEN)
            _f(s, 5, 9, 2, 1, GREEN)
            _f(s, 9, 10, 2, 1, GREEN)
            _f(s, 7, 7, 2, 2, c1)
        else:
            _f(s, 4, 13, 8, 2, "#5b3a20")
            _f(s, 7, 6, 2, 8, GREEN)
            _f(s, 3, 9, 4, 2, GREEN)
            _f(s, 9, 8, 4, 2, GREEN)
            _f(s, 5, 2, 6, 5, c1)
            _f(s, 7, 3, 2, 2, c2)

        _cache[key] = pygame.transform.scale(
            _outline(s), (16 * scale, 16 * scale)
        )

    return _cache[key]


def silhouette(plant_id, scale=3):
    # Тёмный силуэт для неизвестных растений
    key = ("sil", plant_id, scale)

    if key not in _cache:
        import pygame

        mask = pygame.mask.from_surface(base_icon(plant_id))
        shape = mask.to_surface(
            setcolor=(28, 30, 38, 255), unsetcolor=(0, 0, 0, 0)
        )

        _cache[key] = pygame.transform.scale(
            shape, (16 * scale, 16 * scale)
        )

    return _cache[key]
