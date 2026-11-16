import os

import pygame

from systems import plants as P


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "game_font.ttf")

WOOD = (101, 67, 33)
WOOD_DARK = (62, 40, 22)
CREAM = (245, 232, 200)
GOLD = (255, 214, 102)
GREEN = (157, 207, 113)
GRAY = (150, 145, 135)

# Освещение: час -> (r, g, b, прозрачность затемнения)
LIGHT_KEYS = [
    (0.0, (18, 26, 70, 150)),
    (5.0, (22, 30, 80, 135)),
    (6.5, (255, 170, 110, 70)),
    (8.0, (255, 210, 160, 25)),
    (10.0, (255, 255, 255, 0)),
    (16.5, (255, 255, 255, 0)),
    (18.5, (255, 150, 70, 60)),
    (20.0, (90, 60, 120, 105)),
    (21.5, (18, 26, 70, 145)),
    (24.0, (18, 26, 70, 150)),
]

TOOL_NAMES = {"shovel": "Лопата", "can": "Лейка"}

STATUS_TEXT = {
    0: "Не обнаружено",
    1: "Найдено, не выращено",
    2: "Выращено"
}


def light_for(hour):
    # Плавный переход между ключевыми точками суток

    for i in range(len(LIGHT_KEYS) - 1):

        h1, c1 = LIGHT_KEYS[i]
        h2, c2 = LIGHT_KEYS[i + 1]

        if h1 <= hour <= h2:

            t = (hour - h1) / (h2 - h1)

            return tuple(
                int(c1[k] + (c2[k] - c1[k]) * t) for k in range(4)
            )

    return LIGHT_KEYS[-1][1]


def wrap(font, text, width):

    lines = []
    current = ""

    for word in text.split():

        trial = (current + " " + word).strip()

        if font.size(trial)[0] <= width:
            current = trial
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


class UI:

    def __init__(self, fonts, world):

        self.world = world

        self.f10 = fonts["ui"]
        self.f12 = self.make_font(12)
        self.f16 = self.make_font(16)
        self.f22 = self.make_font(22)

        self.overlay = None
        self.glows = {}

        # Состояние окон
        self.rects = []
        self.inv_sel = 0
        self.book_sel = 0
        self.shop_tab = 0
        self.shop_sel = [0, 0]
        self.shop_message = ""

    def make_font(self, size):

        try:
            return pygame.font.Font(FONT_PATH, size)
        except (FileNotFoundError, pygame.error):
            return pygame.font.Font(None, size * 2)

    # ==============================
    # ОБЩИЕ ЭЛЕМЕНТЫ
    # ==============================

    def text(self, surf, string, font, color, pos,
             anchor="topleft", shadow=True):

        image = font.render(string, True, color)
        rect = image.get_rect(**{anchor: pos})

        if shadow:
            surf.blit(font.render(string, True, (20, 14, 10)),
                      rect.move(1, 1))

        surf.blit(image, rect)

        return rect

    def panel(self, surf, rect, alpha=228):

        back = pygame.Surface(rect.size, pygame.SRCALPHA)
        back.fill((38, 28, 20, alpha))
        surf.blit(back, rect.topleft)

        pygame.draw.rect(surf, WOOD, rect, 3, border_radius=4)
        pygame.draw.rect(surf, WOOD_DARK, rect.inflate(-8, -8), 1,
                         border_radius=3)

    def highlight(self, surf, rect, color=GOLD):

        back = pygame.Surface(rect.size, pygame.SRCALPHA)
        back.fill((255, 214, 102, 45))
        surf.blit(back, rect.topleft)
        pygame.draw.rect(surf, color, rect, 2, border_radius=3)

    def checkmark(self, surf, x, y):
        pygame.draw.lines(surf, (120, 230, 120), False,
                          [(x, y + 4), (x + 3, y + 7), (x + 9, y)], 3)

    # ==============================
    # ОСВЕЩЕНИЕ
    # ==============================

    def glow(self, radius):

        if radius not in self.glows:

            size = radius * 2
            surf = pygame.Surface((size, size), pygame.SRCALPHA)

            for i in range(radius, 0, -6):
                alpha = int(120 * (1 - i / radius) ** 1.6)
                pygame.draw.circle(surf, (255, 210, 120, alpha),
                                   (radius, radius), i)

            self.glows[radius] = surf

        return self.glows[radius]

    def draw_lighting(self, screen, state, camera):

        r, g, b, a = light_for(state.time)
        size = screen.get_size()

        if a > 0:

            if self.overlay is None or self.overlay.get_size() != size:
                self.overlay = pygame.Surface(size, pygame.SRCALPHA)

            self.overlay.fill((r, g, b, a))
            screen.blit(self.overlay, (0, 0))

        strength = max(0.0, min(1.0, (a - 40) / 100))

        if strength < 0.05:
            return

        for wx, wy, radius in self.world.lights:

            sx, sy = wx - camera[0], wy - camera[1]

            if (-radius < sx < size[0] + radius
                    and -radius < sy < size[1] + radius):

                image = self.glow(radius)
                image.set_alpha(int(255 * strength))
                screen.blit(image, (sx - radius, sy - radius))

    # ==============================
    # ИНТЕРФЕЙС ВО ВРЕМЯ ИГРЫ
    # ==============================

    def draw_hud(self, screen, state, hint, toasts):

        width, height = screen.get_size()

        # Название и подсказки по клавишам
        self.text(screen, "LITTLE ROOT", self.f10, (255, 255, 255), (20, 20))
        self.text(screen, "WASD - MOVE | ESC - MENU", self.f10,
                  (255, 255, 255), (20, 45))
        self.text(screen,
                  "ПРОБЕЛ - ДЕЙСТВИЕ | E - ВЗАИМОДЕЙСТВИЕ | I - РЮКЗАК | B - КНИГА",
                  self.f10, (255, 255, 255), (20, 70))

        # Панель дня, времени, денег и коллекции
        rect = pygame.Rect(width - 262, 12, 250, 96)
        self.panel(screen, rect)

        self.text(screen, "День %d" % state.day, self.f12, CREAM,
                  (rect.x + 14, rect.y + 12))
        self.text(screen, "%s  %s" % (state.clock_text(), state.phase()),
                  self.f12, GOLD, (rect.x + 14, rect.y + 32))
        self.text(screen, "Монеты: %d" % state.money, self.f12, CREAM,
                  (rect.x + 14, rect.y + 52))

        if state.is_complete():
            line = "Коллекция 100% - ПОБЕДА"
            color = GOLD
        else:
            line = "Коллекция: %d/%d (%d%%)" % (
                state.collection_count(), P.TOTAL,
                state.collection_percent())
            color = GREEN

        self.text(screen, line, self.f12, color,
                  (rect.x + 14, rect.y + 72))

        self.draw_hotbar(screen, state)

        if hint:
            self.text(screen, hint, self.f12, GOLD,
                      (width // 2, height - 90), anchor="midbottom")

        self.draw_toasts(screen, toasts)

    def draw_hotbar(self, screen, state):

        width, height = screen.get_size()
        size, gap = 56, 8
        x0 = (width - (3 * size + 2 * gap)) // 2
        y0 = height - 72

        slots = [("shovel", "1"), ("can", "2"), ("plant", "3")]

        for i, (tool, key) in enumerate(slots):

            rect = pygame.Rect(x0 + i * (size + gap), y0, size, size)
            self.panel(screen, rect, 215)

            if state.tool == tool:
                pygame.draw.rect(screen, GOLD, rect, 3, border_radius=4)

            if tool == "shovel":
                image = self.world.tile("shovel")
            elif tool == "can":
                image = self.world.tile("watering_can")
            elif state.selected_plant:
                image = P.icon(state.selected_plant, 3)
            else:
                image = None

            if image:
                screen.blit(image, image.get_rect(center=rect.center))

            self.text(screen, key, self.f10, CREAM,
                      (rect.x + 6, rect.y + 5))

            if tool == "plant" and state.selected_plant:
                count = state.inventory.get(state.selected_plant, 0)
                self.text(screen, "x%d" % count, self.f10, CREAM,
                          (rect.right - 5, rect.bottom - 5),
                          anchor="bottomright")

        # Название того, что сейчас в руке
        if state.tool == "plant":
            if state.selected_plant:
                name = P.BY_ID[state.selected_plant]["name"]
            else:
                name = "Нет растений"
        else:
            name = TOOL_NAMES[state.tool]

        self.text(screen, name, self.f10, CREAM,
                  (width // 2, y0 - 6), anchor="midbottom")

    def draw_toasts(self, screen, toasts):

        width, height = screen.get_size()
        y = height - 120

        for toast in reversed(toasts[-3:]):

            alpha = int(255 * max(0.0, min(1.0, toast["time"] / 0.8)))

            image = self.f12.render(toast["text"], True, toast["color"])
            image.set_alpha(alpha)

            box = pygame.Surface(
                (image.get_width() + 24, image.get_height() + 12),
                pygame.SRCALPHA
            )
            box.fill((30, 22, 16, int(alpha * 0.8)))

            rect = box.get_rect(midbottom=(width // 2, y))
            screen.blit(box, rect)
            screen.blit(image, image.get_rect(center=rect.center))

            y -= rect.height + 6

    # ==============================
    # ОБРАБОТКА ОКОН
    # ==============================

    def open_modal(self, kind):
        self.rects = []
        self.shop_message = ""

        if kind == "shop":
            self.shop_tab = 0
            self.shop_sel = [0, 0]

    def handle_modal(self, event, game):
        # Возвращает True, если окно нужно закрыть

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return True

            if game.modal == "inventory" and event.key == pygame.K_i:
                return True

            if game.modal == "book" and event.key == pygame.K_b:
                return True

        if game.modal == "inventory":
            self.inventory_event(event, game)

        elif game.modal == "book":
            self.book_event(event, game)

        elif game.modal == "shop":
            self.shop_event(event, game)

        return False

    def clicked_row(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for rect, index in self.rects:
                if rect.collidepoint(event.pos):
                    return index

        return None

    def draw_modal(self, screen, game):

        self.rects = []

        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        screen.blit(dim, (0, 0))

        if game.modal == "inventory":
            self.draw_inventory(screen, game.state)
        elif game.modal == "book":
            self.draw_book(screen, game.state)
        elif game.modal == "shop":
            self.draw_shop(screen, game.state)

    # ==============================
    # РЮКЗАК
    # ==============================

    def inv_entries(self, state):
        return ["shovel", "can"] + state.inventory_plants()

    def inventory_event(self, event, game):

        state = game.state
        entries = self.inv_entries(state)
        count = len(entries)

        self.inv_sel = max(0, min(self.inv_sel, count - 1))

        clicked = self.clicked_row(event)

        if clicked is not None:

            if clicked == self.inv_sel:
                self.inv_activate(game, entries[clicked])
            else:
                self.inv_sel = clicked

        elif event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_UP, pygame.K_w):
                self.inv_sel = max(0, self.inv_sel - 1)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.inv_sel = min(count - 1, self.inv_sel + 1)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_SPACE):
                self.inv_activate(game, entries[self.inv_sel])

    def inv_activate(self, game, entry):

        state = game.state

        if entry in ("shovel", "can"):
            state.tool = entry
            game.say("В руке: %s" % TOOL_NAMES[entry])
        else:
            state.selected_plant = entry
            state.tool = "plant"
            game.say("В руке: %s" % P.BY_ID[entry]["name"])

    def draw_inventory(self, screen, state):

        panel = pygame.Rect(60, 40, 840, 460)
        self.panel(screen, panel, 238)

        self.text(screen, "РЮКЗАК", self.f22, GOLD, (84, 56))
        self.text(screen, "Монеты: %d" % state.money, self.f12, CREAM,
                  (panel.right - 24, 64), anchor="topright")

        entries = self.inv_entries(state)
        self.inv_sel = max(0, min(self.inv_sel, len(entries) - 1))

        visible = 10
        top = 0 if self.inv_sel < visible else self.inv_sel - visible + 1

        y = 110

        for index in range(top, min(len(entries), top + visible)):

            entry = entries[index]
            row = pygame.Rect(80, y, 440, 34)
            self.rects.append((row, index))

            if index == self.inv_sel:
                self.highlight(screen, row)

            if entry in TOOL_NAMES:

                image = self.world.tile(
                    "shovel" if entry == "shovel" else "watering_can")
                image = pygame.transform.scale(image, (32, 32))
                screen.blit(image, (row.x + 4, row.y + 1))

                self.text(screen, TOOL_NAMES[entry], self.f12, CREAM,
                          (row.x + 48, row.y + 10))

                if state.tool == entry:
                    self.text(screen, "в руке", self.f10, GOLD,
                              (row.right - 10, row.y + 12),
                              anchor="topright")
            else:

                plant = P.BY_ID[entry]
                screen.blit(P.icon(entry, 2), (row.x + 4, row.y + 1))

                self.text(screen, plant["name"], self.f12,
                          P.RARITY_COLORS[plant["rarity"]],
                          (row.x + 48, row.y + 10))

                right = "x%d" % state.inventory[entry]

                if state.tool == "plant" and state.selected_plant == entry:
                    right = "в руке   " + right

                self.text(screen, right, self.f10, CREAM,
                          (row.right - 10, row.y + 12), anchor="topright")

            y += 38

        if len(entries) > visible:
            self.text(screen, "Прокрутка: стрелки вверх и вниз",
                      self.f10, GRAY, (84, 480 - 8), anchor="bottomleft")

        # Описание выбранного предмета
        info = pygame.Rect(545, 100, 335, 370)
        self.panel(screen, info, 200)

        entry = entries[self.inv_sel]

        if entry in TOOL_NAMES:

            title = TOOL_NAMES[entry]
            lines = (
                ["Грядки на ферме: копайте землю, выкапывайте растения и "
                 "собирайте выросший урожай."]
                if entry == "shovel" else
                ["Поливайте посаженные растения. Каждое растение "
                 "поливается только один раз и к утру вырастает."]
            )

            self.text(screen, title, self.f16, CREAM, (info.x + 18, info.y + 18))

            yy = info.y + 54

            for line in lines:
                for part in wrap(self.f12, line, info.width - 36):
                    self.text(screen, part, self.f12, CREAM,
                              (info.x + 18, yy))
                    yy += 20

        else:
            self.draw_plant_details(screen, state, entry, info, True)

        self.text(screen, "ENTER - взять в руку | ESC - закрыть",
                  self.f10, GRAY, (panel.centerx, panel.bottom - 14),
                  anchor="midbottom")

    def draw_plant_details(self, screen, state, plant_id, rect, owned):

        plant = P.BY_ID[plant_id]

        big = P.icon(plant_id, 5)
        screen.blit(big, (rect.x + 18, rect.y + 16))

        x = rect.x + 112

        yy = rect.y + 20

        for part in wrap(self.f16, plant["name"], rect.right - x - 12):
            self.text(screen, part, self.f16, CREAM, (x, yy))
            yy += 22

        self.text(screen, P.RARITY_NAMES[plant["rarity"]], self.f12,
                  P.RARITY_COLORS[plant["rarity"]], (x, yy + 4))

        yy = rect.y + 112

        grown = plant_id in state.grown
        status = 2 if grown else 1

        lines = [
            "Биом: %s" % P.BIOME_NAMES[plant["biome"]],
            "Статус: %s" % STATUS_TEXT[status],
        ]

        if owned:
            lines.append("В рюкзаке: %d" % state.inventory.get(plant_id, 0))
            lines.append("Продажа: %d монет" % P.sell_price(plant_id))

        for line in lines:
            self.text(screen, line, self.f12, CREAM, (rect.x + 18, yy))
            yy += 24

    # ==============================
    # КОЛЛЕКЦИОННАЯ КНИГА
    # ==============================

    BOOK_COLS = 9

    def book_status(self, state, plant_id):

        if plant_id in state.grown:
            return 2

        if plant_id in state.discovered:
            return 1

        return 0

    def book_event(self, event, game):

        count = P.TOTAL
        cols = self.BOOK_COLS

        clicked = self.clicked_row(event)

        if clicked is not None:
            self.book_sel = clicked

        elif event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.book_sel = max(0, self.book_sel - 1)

            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.book_sel = min(count - 1, self.book_sel + 1)

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.book_sel = max(0, self.book_sel - cols)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.book_sel = min(count - 1, self.book_sel + cols)

    def draw_book(self, screen, state):

        panel = pygame.Rect(20, 20, 920, 500)
        self.panel(screen, panel, 240)

        self.text(screen, "КНИГА КОЛЛЕКЦИОНЕРА", self.f22, GOLD, (44, 36))

        total_line = "Выращено %d из %d (%d%%)" % (
            state.collection_count(), P.TOTAL, state.collection_percent())

        self.text(screen, total_line, self.f12, GREEN,
                  (panel.right - 28, 44), anchor="topright")

        # Прогресс исследования биомов
        parts = []

        for biome in P.BIOMES:
            found = len([p for p in P.BY_BIOME[biome]
                         if p["id"] in state.discovered])
            parts.append("%s: найдено %d/%d (поисков %d)" % (
                P.BIOME_NAMES[biome], found, len(P.BY_BIOME[biome]),
                state.explore[biome]["searches"]))

        self.text(screen, "   |   ".join(parts), self.f10, CREAM, (44, 74))

        cols = self.BOOK_COLS
        cell, gap = 70, 6
        x0, y0 = 40, 104

        for index, plant in enumerate(P.PLANTS):

            col, row = index % cols, index // cols
            rect = pygame.Rect(x0 + col * (cell + gap),
                               y0 + row * (cell + gap), cell, cell)
            self.rects.append((rect, index))

            status = self.book_status(state, plant["id"])

            back = pygame.Surface(rect.size, pygame.SRCALPHA)
            back.fill((20, 15, 12, 200))
            screen.blit(back, rect.topleft)

            if status == 0:
                image = P.silhouette(plant["id"], 3)
                border = (70, 65, 60)
            else:
                image = P.icon(plant["id"], 3)
                border = P.RARITY_COLORS[plant["rarity"]]

            screen.blit(image, image.get_rect(center=rect.center))
            pygame.draw.rect(screen, border, rect, 2, border_radius=3)

            if status == 2:
                self.checkmark(screen, rect.right - 16, rect.y + 5)

            if index == self.book_sel:
                pygame.draw.rect(screen, (255, 255, 255), rect.inflate(4, 4),
                                 2, border_radius=4)

        # Карточка выбранного растения
        info = pygame.Rect(700, 104, 220, 380)
        self.panel(screen, info, 205)

        plant = P.PLANTS[self.book_sel]
        status = self.book_status(state, plant["id"])

        if status == 0:
            image = P.silhouette(plant["id"], 6)
        else:
            image = P.icon(plant["id"], 6)

        screen.blit(image, image.get_rect(midtop=(info.centerx, info.y + 14)))

        yy = info.y + 124

        if status == 0:

            lines = [("???", self.f16, CREAM),
                     ("Редкость: ???", self.f12, GRAY),
                     ("Биом: ???", self.f12, GRAY),
                     (STATUS_TEXT[0], self.f12, GRAY)]
        else:

            lines = []

            for part in wrap(self.f16, plant["name"], info.width - 28):
                lines.append((part, self.f16, CREAM))

            lines += [
                ("Редкость: %s" % P.RARITY_NAMES[plant["rarity"]],
                 self.f12, P.RARITY_COLORS[plant["rarity"]]),
                ("Биом: %s" % P.BIOME_NAMES[plant["biome"]],
                 self.f12, CREAM),
                (STATUS_TEXT[status], self.f12,
                 GREEN if status == 2 else GOLD),
            ]

        for string, font, color in lines:
            for part in wrap(font, string, info.width - 28) or [string]:
                self.text(screen, part, font, color, (info.x + 14, yy))
                yy += font.get_height() + 8

        self.text(screen, "Стрелки - выбор | B или ESC - закрыть",
                  self.f10, GRAY, (panel.centerx, panel.bottom - 12),
                  anchor="midbottom")

    # ==============================
    # ТОРГОВЕЦ
    # ==============================

    def sell_entries(self, state):
        return [p for p in state.inventory_plants()
                if state.sellable(p) > 0]

    def shop_event(self, event, game):

        state = game.state

        buy_list = state.merchant["stock"]
        sell_list = self.sell_entries(state)
        lengths = [len(buy_list), len(sell_list)]

        for i in range(2):
            self.shop_sel[i] = max(0, min(self.shop_sel[i],
                                          max(0, lengths[i] - 1)))

        clicked = self.clicked_row(event)

        if clicked is not None:

            tab, index = clicked // 100, clicked % 100

            if tab == self.shop_tab and index == self.shop_sel[tab]:
                self.shop_act(state)
            else:
                self.shop_tab = tab
                self.shop_sel[tab] = index

        elif event.type == pygame.KEYDOWN:

            tab = self.shop_tab

            if event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT,
                             pygame.K_a, pygame.K_d):
                self.shop_tab = 1 - tab

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.shop_sel[tab] = max(0, self.shop_sel[tab] - 1)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.shop_sel[tab] = min(max(0, lengths[tab] - 1),
                                         self.shop_sel[tab] + 1)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_SPACE):
                self.shop_act(state)

    def shop_act(self, state):

        if self.shop_tab == 0:
            ok, message = state.buy(self.shop_sel[0])
        else:
            items = self.sell_entries(state)

            if not items:
                ok, message = False, "Дубликатов нет"
            else:
                index = min(self.shop_sel[1], len(items) - 1)
                ok, message = state.sell(items[index])

        self.shop_message = message

    def draw_shop(self, screen, state):

        panel = pygame.Rect(40, 24, 880, 492)
        self.panel(screen, panel, 242)

        self.text(screen, "СТРАННИК", self.f22, (190, 150, 255), (64, 40))
        self.text(screen, "«Тени шепчут, чего тебе не хватает...»",
                  self.f12, GRAY, (64, 72))
        self.text(screen, "Монеты: %d" % state.money, self.f16, GOLD,
                  (panel.right - 28, 44), anchor="topright")

        columns = [
            ("КУПИТЬ", pygame.Rect(60, 104, 410, 360), 0),
            ("ПРОДАТЬ ДУБЛИКАТЫ", pygame.Rect(490, 104, 410, 360), 1),
        ]

        buy_list = state.merchant["stock"]
        sell_list = self.sell_entries(state)

        for title, area, tab in columns:

            color = GOLD if self.shop_tab == tab else CREAM
            self.text(screen, title, self.f12, color, (area.x, area.y - 22))

            entries = buy_list if tab == 0 else sell_list

            if not entries:
                message = ("Всё распродано" if tab == 0
                           else "Нет дубликатов для продажи")
                self.text(screen, message, self.f12, GRAY,
                          (area.x + 8, area.y + 10))
                continue

            sel = max(0, min(self.shop_sel[tab], len(entries) - 1))
            self.shop_sel[tab] = sel

            visible = 7
            top = 0 if sel < visible else sel - visible + 1

            y = area.y

            for index in range(top, min(len(entries), top + visible)):

                row = pygame.Rect(area.x, y, area.width, 46)
                self.rects.append((row, tab * 100 + index))

                if tab == self.shop_tab and index == sel:
                    self.highlight(screen, row)

                if tab == 0:
                    item = entries[index]
                    plant_id = item["id"]
                    right = "%d монет" % item["price"]
                    sub = "x%d" % item["qty"] if item["qty"] > 0 \
                        else "нет в наличии"
                else:
                    plant_id = entries[index]
                    right = "+%d монет" % P.sell_price(plant_id)
                    sub = "дубликатов: %d" % state.sellable(plant_id)

                plant = P.BY_ID[plant_id]
                screen.blit(P.icon(plant_id, 2), (row.x + 6, row.y + 7))

                self.text(screen, plant["name"], self.f12,
                          P.RARITY_COLORS[plant["rarity"]],
                          (row.x + 52, row.y + 6))
                self.text(screen,
                          "%s | %s" % (P.RARITY_NAMES[plant["rarity"]], sub),
                          self.f10, GRAY, (row.x + 52, row.y + 27))
                self.text(screen, right, self.f12, CREAM,
                          (row.right - 10, row.y + 14), anchor="topright")

                y += 50

        if self.shop_message:
            self.text(screen, self.shop_message, self.f12, GOLD,
                      (panel.centerx, panel.bottom - 40), anchor="midbottom")

        self.text(screen,
                  "TAB - сменить список | СТРЕЛКИ - выбор | ENTER - купить или продать | ESC - выйти",
                  self.f10, GRAY, (panel.centerx, panel.bottom - 14),
                  anchor="midbottom")
