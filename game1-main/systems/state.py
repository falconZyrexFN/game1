import random

from systems import plants as P


# ==============================
# ВРЕМЯ
# ==============================

# Столько реальных секунд длятся игровые сутки
DAY_SECONDS = 300.0
HOURS_PER_SECOND = 24.0 / DAY_SECONDS

START_TIME = 7.0

# В это время наступает новое утро: растут растения, обновляется торговец
NEW_DAY_HOUR = 6.0

START_MONEY = 50

# Сколько раз можно полить, пока лейка не опустеет
WATER_MAX = 8
STOCK_SIZE = 6
SPOTS_PER_BIOME = 7


def phase_name(hour):

    if 6 <= hour < 11:
        return "Утро"

    if 11 <= hour < 17:
        return "День"

    if 17 <= hour < 21:
        return "Вечер"

    return "Ночь"


class GameState:
    # Вся логика игры без графики: время, инвентарь, ферма,
    # коллекция, торговец и прогресс исследования.

    def __init__(self):

        self.day = 1
        self.time = START_TIME
        self.money = START_MONEY
        self.water = WATER_MAX

        # id растения -> сколько штук в инвентаре
        self.inventory = {}

        # Выбранный инструмент: shovel, can или plant
        self.tool = "shovel"
        self.selected_plant = None

        # Найденные и выращенные виды (коллекционная книга)
        self.discovered = set()
        self.grown = set()

        # Грядки: (x, y) -> {"plant", "watered", "mature"}
        self.plots = {}

        # Места, где можно найти растения
        self.spots = []

        self.explore = {
            b: {"searches": 0, "species": []} for b in P.BIOMES
        }

        self.bought = {}
        self.sold = {}
        self.crossed = {}

        self.merchant = {"day": 0, "stock": []}

        # Стартовые растения, чтобы можно было сразу попробовать ферму
        self.add_item("daisy", 2)
        self.discovered.add("daisy")
        self.selected_plant = "daisy"

        self.roll_stock()

    # ==============================
    # ВРЕМЯ И НОВЫЙ ДЕНЬ
    # ==============================

    def phase(self):
        return phase_name(self.time)

    def clock_text(self):
        hours = int(self.time) % 24
        minutes = int((self.time - int(self.time)) * 60)
        return "%02d:%02d" % (hours, minutes)

    def is_night_for_sleep(self):
        return self.time >= 19 or self.time < NEW_DAY_HOUR

    def advance(self, dt):
        # Возвращает сведения о новом дне, если он наступил

        old = self.time
        self.time += dt * HOURS_PER_SECOND

        crossed = old < NEW_DAY_HOUR <= self.time

        if self.time >= 24:
            self.time -= 24

        if crossed:
            return self.new_day()

        return None

    def sleep(self):

        if not self.is_night_for_sleep():
            return None

        self.time = NEW_DAY_HOUR

        return self.new_day()

    def new_day(self):

        self.day += 1

        grown_now = []
        new_species = []

        for plot in self.plots.values():

            if (plot["plant"] and plot["watered"]
                    and not plot["mature"]):

                plot["mature"] = True
                grown_now.append(plot["plant"])

                if plot["plant"] not in self.grown:
                    self.grown.add(plot["plant"])
                    self.discovered.add(plot["plant"])
                    new_species.append(plot["plant"])

        self.roll_stock()

        return {
            "day": self.day,
            "grown": grown_now,
            "new": new_species
        }

    # ==============================
    # ИНВЕНТАРЬ
    # ==============================

    def add_item(self, plant_id, amount=1):
        self.inventory[plant_id] = self.inventory.get(plant_id, 0) + amount

    def remove_item(self, plant_id, amount=1):

        have = self.inventory.get(plant_id, 0)

        if have < amount:
            return False

        if have == amount:
            del self.inventory[plant_id]
        else:
            self.inventory[plant_id] = have - amount

        return True

    def inventory_plants(self):
        # Растения из инвентаря в порядке списка видов
        return [
            p["id"] for p in P.PLANTS
            if self.inventory.get(p["id"], 0) > 0
        ]

    def fix_selection(self):
        # Если выбранное растение закончилось, берём следующее
        if self.selected_plant and self.inventory.get(self.selected_plant, 0) > 0:
            return

        owned = self.inventory_plants()
        self.selected_plant = owned[0] if owned else None

    def cycle_plant(self, step=1):

        owned = self.inventory_plants()

        if not owned:
            self.selected_plant = None
            return

        if self.selected_plant in owned:
            index = (owned.index(self.selected_plant) + step) % len(owned)
        else:
            index = 0

        self.selected_plant = owned[index]

    # ==============================
    # КОЛЛЕКЦИЯ
    # ==============================

    def collection_count(self):
        return len(self.grown)

    def collection_percent(self):
        return int(100 * len(self.grown) / P.TOTAL)

    def is_complete(self):
        return len(self.grown) >= P.TOTAL

    # ==============================
    # ПОИСК РАСТЕНИЙ
    # ==============================

    def forage(self, biome):

        rarity = random.choices(
            P.RARITIES,
            weights=[P.FORAGE_WEIGHT[r] for r in P.RARITIES]
        )[0]

        options = [
            p for p in P.BY_BIOME[biome] if p["rarity"] == rarity
        ]

        plant = random.choice(options)
        is_new = plant["id"] not in self.discovered

        self.discovered.add(plant["id"])
        self.add_item(plant["id"], 1)

        info = self.explore[biome]
        info["searches"] += 1

        if plant["id"] not in info["species"]:
            info["species"].append(plant["id"])

        self.fix_selection()

        return plant, is_new

    # ==============================
    # ФЕРМА
    # ==============================

    def use_tool(self, tile, in_field):
        # Возвращает (успех, сообщение)

        plot = self.plots.get(tile)

        if self.tool == "shovel":

            if plot is None:

                if not in_field:
                    return False, "Грядки делают только на ферме"

                return False, "Грядку нужно вскопать (ПРОБЕЛ)"

            if plot["plant"] is None:
                return False, "Выберите растение (3) и посадите его"

            if plot["mature"]:

                plant_id = plot["plant"]
                amount = 3 if plot.get("rich") else 2

                self.add_item(plant_id, amount)
                self.clear_plot(plot)
                self.fix_selection()

                text = "Урожай: %s x%d" % (P.BY_ID[plant_id]["name"], amount)

                if amount == 3:
                    text += " (богатая почва!)"

                return True, text

            plant_id = plot["plant"]

            self.add_item(plant_id, 1)
            self.clear_plot(plot)

            return True, "Растение выкопано"

        if self.tool == "can":

            # Полив идёт через мини-игру (can_water и water_plot)
            ok, message = self.can_water(tile)

            return False, message or "Удерживайте лейку над растением"

        if self.tool == "hoe":

            if plot is None:
                return False, "Мотыгой улучшают грядку. Сначала вскопайте её лопатой"

            if plot["plant"]:
                return False, "Сначала освободите грядку"

            plot["super"] = not plot.get("super")

            if plot["super"]:
                return True, "Грядка для суперрастений готова"

            return True, "Снова обычная грядка"

        # tool == "plant"

        if plot is None:
            return False, "Сначала сделайте грядку лопатой"

        if plot["plant"]:
            return False, "Здесь уже растёт растение"

        plant_id = self.selected_plant

        if not plant_id or self.inventory.get(plant_id, 0) <= 0:
            return False, "Нет растения для посадки"

        # Суперрастения растут только на особой грядке, обычные только на обычной
        if P.is_super(plant_id) and not plot.get("super"):
            return False, "Суперрастение растёт на особой грядке (мотыга, 4)"

        if not P.is_super(plant_id) and plot.get("super"):
            return False, "На особую грядку сажают только суперрастения"

        self.remove_item(plant_id, 1)

        plot["plant"] = plant_id
        plot["watered"] = False
        plot["mature"] = False

        name = P.BY_ID[plant_id]["name"]

        self.fix_selection()

        return True, "Посажено: %s" % name

    def cross(self, first, second):
        # Скрещивание двух растений. Возвращает (успех, сообщение, результат)

        if not first or not second:
            return False, "Выберите два растения", None

        for plant_id in {first, second}:
            if self.inventory.get(plant_id, 0) < 1:
                return False, "Не хватает растений", None

        result = P.cross_result(first, second)

        if result is None:
            return False, "Эти растения не скрещиваются", None

        self.remove_item(first, 1)
        self.remove_item(second, 1)

        is_new = result not in self.discovered

        self.add_item(result, 1)
        self.discovered.add(result)
        self.crossed[result] = self.crossed.get(result, 0) + 1

        self.fix_selection()

        text = "Скрещено: %s%s" % (
            P.BY_ID[result]["name"], " - новое!" if is_new else "")

        return True, text, result

    def can_water(self, tile):
        # Можно ли сейчас полить растение на этой грядке

        plot = self.plots.get(tile)

        if plot is None:
            return False, "Здесь нет грядки"

        if plot["plant"] is None:
            return False, "Сначала посадите растение"

        if plot["mature"]:
            return False, "Растение уже выросло"

        if plot["watered"]:
            return False, "Это растение уже полито"

        if self.water <= 0:
            return False, "Лейка пуста. Наберите воды у колодца (E)"

        return True, ""

    def water_plot(self, tile, score):
        # score - какую долю времени лейка удерживалась над растением

        ok, message = self.can_water(tile)

        if not ok:
            return False, message

        plot = self.plots[tile]

        if score >= 0.8:
            plot["watered"] = True

            return True, "Идеальный полив! Вода сэкономлена"

        self.water -= 1

        if score >= 0.5:
            plot["watered"] = True

            return True, "Полито (вода %d/%d). К утру вырастет" % (
                self.water, WATER_MAX)

        return False, "Вода пролилась мимо. Попробуйте ещё раз"

    def fill_can(self):

        if self.water >= WATER_MAX:
            return False, "Лейка уже полная"

        self.water = WATER_MAX

        return True, "Лейка наполнена"

    def needs_dig(self, tile, in_field):
        # Новую грядку делают в мини-игре, а не одним нажатием
        return (self.tool == "shovel" and in_field
                and tile not in self.plots)

    def make_bed(self, tile, hits):
        # hits - сколько ударов лопаты из трёх попало в цель

        if tile in self.plots:
            return False, "Здесь уже есть грядка"

        if hits < 2:
            return False, "Земля не поддалась. Попробуйте ещё раз"

        rich = hits >= 3

        self.plots[tile] = {
            "plant": None, "watered": False, "mature": False, "rich": rich,
            "super": False
        }

        if rich:
            return True, "Отличная грядка! Урожай здесь будет больше"

        return True, "Грядка готова"

    def clear_plot(self, plot):
        plot["plant"] = None
        plot["watered"] = False
        plot["mature"] = False

    # ==============================
    # ТОРГОВЕЦ
    # ==============================

    def roll_stock(self):
        # Новый случайный ассортимент. Вчерашние растения выпадают реже,
        # а ещё не выращенные чуть чаще.

        rng = random.Random()
        yesterday = {s["id"] for s in self.merchant["stock"]}

        pool = list(P.WILD)
        stock = []

        for _ in range(min(P.WILD_TOTAL, STOCK_SIZE)):

            weights = []

            for p in pool:

                weight = P.STOCK_WEIGHT[p["rarity"]]

                if p["id"] in yesterday:
                    weight *= 0.25

                if p["id"] not in self.grown:
                    weight *= 1.4

                weights.append(weight)

            plant = rng.choices(pool, weights=weights)[0]
            pool.remove(plant)

            price = round(P.buy_price(plant["id"]) * rng.uniform(0.9, 1.15))

            if plant["rarity"] in ("rare", "legendary"):
                qty = 1
            else:
                qty = rng.randint(1, 3)

            stock.append({"id": plant["id"], "price": price, "qty": qty})

        stock.sort(key=lambda s: P.PLANTS.index(P.BY_ID[s["id"]]))

        self.merchant = {"day": self.day, "stock": stock}

    def buy(self, index):

        if not (0 <= index < len(self.merchant["stock"])):
            return False, "Нечего покупать"

        item = self.merchant["stock"][index]
        name = P.BY_ID[item["id"]]["name"]

        if item["qty"] <= 0:
            return False, "Распродано"

        if self.money < item["price"]:
            return False, "Не хватает монет"

        self.money -= item["price"]
        item["qty"] -= 1

        is_new = item["id"] not in self.discovered

        self.add_item(item["id"], 1)
        self.discovered.add(item["id"])
        self.bought[item["id"]] = self.bought.get(item["id"], 0) + 1

        self.fix_selection()

        return True, "Куплено: %s%s" % (name, " - новое!" if is_new else "")

    def sellable(self, plant_id):
        # Продаются только дубликаты: один экземпляр всегда остаётся
        return max(0, self.inventory.get(plant_id, 0) - 1)

    def sell(self, plant_id):

        if self.sellable(plant_id) <= 0:
            return False, "Дубликатов нет"

        price = P.sell_price(plant_id)

        self.remove_item(plant_id, 1)
        self.money += price
        self.sold[plant_id] = self.sold.get(plant_id, 0) + 1

        self.fix_selection()

        return True, "Продано: %s (+%d)" % (P.BY_ID[plant_id]["name"], price)

    # ==============================
    # СОХРАНЕНИЕ
    # ==============================

    def to_dict(self):

        return {
            "day": self.day,
            "time": self.time,
            "money": self.money,
            "water": self.water,
            "inventory": dict(self.inventory),
            "tool": self.tool,
            "selected_plant": self.selected_plant,
            "discovered": sorted(self.discovered),
            "grown": sorted(self.grown),
            "plots": {
                "%d,%d" % key: dict(plot)
                for key, plot in self.plots.items()
            },
            "spots": [dict(s) for s in self.spots],
            "explore": self.explore,
            "bought": self.bought,
            "sold": self.sold,
            "crossed": self.crossed,
            "merchant": self.merchant
        }

    def load_dict(self, data):
        # Загружаем аккуратно: неверные записи просто пропускаются

        if not isinstance(data, dict):
            return

        try:
            self.day = max(1, int(data.get("day", 1)))
            self.time = float(data.get("time", START_TIME)) % 24
            self.money = max(0, int(data.get("money", START_MONEY)))
            self.water = max(0, min(WATER_MAX,
                                    int(data.get("water", WATER_MAX))))
        except (TypeError, ValueError):
            pass

        inventory = data.get("inventory", {})

        self.inventory = {}

        if isinstance(inventory, dict):
            for key, value in inventory.items():
                if key in P.BY_ID and isinstance(value, int) and value > 0:
                    self.inventory[key] = value

        self.discovered = {
            p for p in data.get("discovered", []) if p in P.BY_ID
        }

        self.grown = {
            p for p in data.get("grown", []) if p in P.BY_ID
        }

        self.discovered |= self.grown

        self.plots = {}

        for key, plot in data.get("plots", {}).items():

            try:
                x, y = [int(v) for v in key.split(",")]
                plant = plot.get("plant")

                if plant is not None and plant not in P.BY_ID:
                    plant = None

                self.plots[(x, y)] = {
                    "plant": plant,
                    "watered": bool(plot.get("watered")) and plant is not None,
                    "mature": bool(plot.get("mature")) and plant is not None,
                    "rich": bool(plot.get("rich")),
                    "super": bool(plot.get("super"))
                }

            except (ValueError, AttributeError, TypeError):
                continue

        self.spots = []

        for spot in data.get("spots", []):

            try:
                if spot["biome"] in P.BIOMES:
                    self.spots.append({
                        "biome": spot["biome"],
                        "tx": int(spot["tx"]),
                        "ty": int(spot["ty"])
                    })
            except (KeyError, TypeError, ValueError):
                continue

        for biome in P.BIOMES:

            info = data.get("explore", {}).get(biome, {})

            try:
                self.explore[biome] = {
                    "searches": max(0, int(info.get("searches", 0))),
                    "species": [
                        s for s in info.get("species", []) if s in P.BY_ID
                    ]
                }
            except (TypeError, ValueError, AttributeError):
                pass

        self.bought = {
            k: v for k, v in data.get("bought", {}).items()
            if k in P.BY_ID and isinstance(v, int)
        }

        self.sold = {
            k: v for k, v in data.get("sold", {}).items()
            if k in P.BY_ID and isinstance(v, int)
        }

        self.crossed = {
            k: v for k, v in data.get("crossed", {}).items()
            if k in P.BY_ID and isinstance(v, int)
        }

        merchant = data.get("merchant", {})
        stock = []

        if isinstance(merchant, dict):

            for item in merchant.get("stock", []):

                try:
                    if item["id"] in P.BY_ID:
                        stock.append({
                            "id": item["id"],
                            "price": max(1, int(item["price"])),
                            "qty": max(0, int(item["qty"]))
                        })
                except (KeyError, TypeError, ValueError):
                    continue

        if stock:
            self.merchant = {"day": self.day, "stock": stock}
        else:
            self.roll_stock()

        tool = data.get("tool", "shovel")
        self.tool = (tool if tool in ("shovel", "can", "plant", "hoe")
                     else "shovel")

        selected = data.get("selected_plant")
        self.selected_plant = selected if selected in P.BY_ID else None
        self.fix_selection()
