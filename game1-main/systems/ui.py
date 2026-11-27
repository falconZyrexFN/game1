import math
import os
import random

import pygame

from systems import plants as P
from systems.state import WATER_MAX


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

FLIGHT_TIME = 1.2

TOOL_NAMES = {"shovel": "Лопата", "can": "Лейка", "hoe": "Мотыга"}
TOOL_TILES = {"shovel": "shovel", "can": "watering_can", "hoe": "hoe"}

STATUS_TEXT = {
    0: "Не обнаружено",
    1: "Найдено, не выращено",
    2: "Выращено"
}


def status_label(plant, status):

    if plant["rarity"] == "super":
        return {0: "Не получено", 1: "Скрещено, не выращено",
                2: "Выращено"}[status]

    return STATUS_TEXT[status]


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
        self.dig = None
        self.fade = None
        self.spark_img = None
        self.wg = None
        self.water_plant = None

        # Полоска коллекции и растения, летящие в книгу
        self.flights = []
        self.flights_pending = 0
        self.book_bump = 0.0
        self.book_pos = (1200, 88)
        self.bar_grown = None

        # Стол скрещивания
        self.cross_slots = [None, None]
        self.cross_sel = 0
        self.cross_msg = ""
        self.cross_result = None

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

        # Панель дня, времени, денег и коллекции
        rect = pygame.Rect(width - 262, 12, 250, 96)
        self.panel(screen, rect)

        self.text(screen, "День %d" % state.day, self.f12, CREAM,
                  (rect.x + 14, rect.y + 12))
        self.text(screen, "%s  %s" % (state.clock_text(), state.phase()),
                  self.f12, GOLD, (rect.x + 14, rect.y + 32))
        self.text(screen, "Монеты: %d" % state.money, self.f12, CREAM,
                  (rect.x + 14, rect.y + 52))

        self.draw_collection_bar(screen, state, rect)

        self.draw_hotbar(screen, state)

        if hint:
            self.text(screen, hint, self.f12, GOLD,
                      (width // 2, height - 90), anchor="midbottom")

        self.draw_toasts(screen, toasts)

    # ==============================
    # ПОЛОСКА КОЛЛЕКЦИИ И ПОЛЁТ РАСТЕНИЙ В КНИГУ
    # ==============================

    def add_flight(self, plant_id, origin):
        # Новое растение летит от origin (x, y на экране) в книгу

        self.flights.append({"id": plant_id, "origin": origin, "t": 0.0})
        self.flights_pending += 1

    def update_hud(self, dt, state):

        for flight in self.flights:
            flight["t"] += dt

            if flight["t"] >= FLIGHT_TIME:
                self.flights_pending = max(0, self.flights_pending - 1)
                self.book_bump = 0.45

        self.flights = [f for f in self.flights if f["t"] < FLIGHT_TIME]

        if self.book_bump > 0:
            self.book_bump = max(0.0, self.book_bump - dt)

        # Тёмная часть полоски (выращено) плавно догоняет цель
        target = float(state.collection_count())

        if self.bar_grown is None:
            self.bar_grown = target
        else:
            self.bar_grown += (target - self.bar_grown) * min(1.0, dt * 4)

    def found_progress(self, state):
        # Сколько видов уже "в книге": растение, которое ещё летит,
        # добавляет к полоске долю своего пути

        flying = sum(self.ease(f["t"] / FLIGHT_TIME) for f in self.flights)
        base = len(state.discovered) - self.flights_pending

        return max(0.0, min(float(P.TOTAL), base + flying))

    @staticmethod
    def ease(t):
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    def draw_book_icon(self, surf, center, scale=1.0):

        w, h = 28, 24
        icon = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(icon, (120, 58, 40), (1, 1, w - 2, h - 2),
                         border_radius=3)
        pygame.draw.rect(icon, (70, 34, 24), (1, 1, w - 2, h - 2), 2,
                         border_radius=3)
        pygame.draw.rect(icon, (235, 220, 175), (w - 6, 4, 3, h - 8))
        pygame.draw.rect(icon, (60, 28, 20), (5, 1, 3, h - 2))
        pygame.draw.rect(icon, GOLD, (11, 7, 9, 2))
        pygame.draw.rect(icon, GOLD, (11, 12, 9, 2))
        pygame.draw.rect(icon, GOLD, (11, 17, 6, 2))

        if scale != 1.0:
            icon = pygame.transform.smoothscale(
                icon, (int(w * scale), int(h * scale)))

        surf.blit(icon, icon.get_rect(center=center))

    def draw_collection_bar(self, screen, state, rect):

        # Книга слева, полоска справа
        book_center = (rect.x + 28, rect.y + 76)
        self.book_pos = book_center

        pulse = 0.0

        if self.book_bump > 0:
            pulse = math.sin(self.book_bump / 0.45 * math.pi)

        self.draw_book_icon(screen, book_center, 1.0 + 0.35 * pulse)

        bar = pygame.Rect(rect.x + 54, rect.y + 68, rect.width - 54 - 14, 16)
        total = float(P.TOTAL)

        pygame.draw.rect(screen, (20, 15, 12), bar, border_radius=4)

        inner = bar.inflate(-4, -4)

        found = self.found_progress(state) / total
        grown = (self.bar_grown or 0.0) / total

        # Светлая часть: найдено (книга), яркая: выращено
        found_w = int(inner.width * min(1.0, found))
        grown_w = int(inner.width * min(1.0, grown))

        if found_w > 0:
            pygame.draw.rect(screen, (92, 128, 70),
                             (inner.x, inner.y, found_w, inner.height),
                             border_radius=3)

        if grown_w > 0:
            color = GOLD if state.is_complete() else GREEN
            pygame.draw.rect(screen, color,
                             (inner.x, inner.y, grown_w, inner.height),
                             border_radius=3)

        # Вспышка на краю полоски, пока растение летит или только что влетело
        if self.flights or pulse > 0:
            glow = pygame.Surface(bar.size, pygame.SRCALPHA)
            alpha = 70 if self.flights else int(110 * pulse)
            pygame.draw.rect(glow, (255, 240, 170, alpha),
                             glow.get_rect(), border_radius=4)
            screen.blit(glow, bar.topleft)

        pygame.draw.rect(screen, WOOD, bar, 2, border_radius=4)

        label = "%d/%d" % (state.collection_count(), P.TOTAL)
        self.text(screen, label, self.f10, CREAM, bar.center,
                  anchor="center")

    def draw_flights(self, screen):

        bx, by = self.book_pos

        for flight in self.flights:

            ox, oy = flight["origin"]
            t = flight["t"] / FLIGHT_TIME

            def point(u):
                # Кривая: сначала вверх, потом к книге
                e = self.ease(u)
                cx, cy = ox, by - 40
                x = (1 - e) ** 2 * ox + 2 * (1 - e) * e * cx + e * e * bx
                y = (1 - e) ** 2 * oy + 2 * (1 - e) * e * cy + e * e * by
                return x, y

            # След из искр
            for i in range(1, 7):

                u = t - i * 0.035

                if u <= 0:
                    break

                px, py = point(u)
                size = max(1, 5 - i)
                fade = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(fade, (255, 230, 140, 200 - i * 28),
                                   (6, 6), size)
                screen.blit(fade, fade.get_rect(center=(px, py)))

            x, y = point(t)
            scale = 1.25 - 0.8 * self.ease(t)

            image = P.icon(flight["id"], 3)
            size = max(8, int(image.get_width() * scale))
            image = pygame.transform.smoothscale(image, (size, size))

            screen.blit(image, image.get_rect(center=(x, y)))

    def draw_hotbar(self, screen, state):

        width, height = screen.get_size()
        size, gap = 56, 8
        x0 = (width - (4 * size + 3 * gap)) // 2
        y0 = height - 72

        slots = [("shovel", "1"), ("can", "2"), ("plant", "3"), ("hoe", "4")]

        for i, (tool, key) in enumerate(slots):

            rect = pygame.Rect(x0 + i * (size + gap), y0, size, size)
            self.panel(screen, rect, 215)

            if state.tool == tool:
                pygame.draw.rect(screen, GOLD, rect, 3, border_radius=4)

            if tool == "shovel":
                image = self.world.tile("shovel")
            elif tool == "can":
                image = self.world.tile("watering_can")
            elif tool == "hoe":
                image = self.world.tile("hoe")
            elif state.selected_plant:
                image = P.icon(state.selected_plant, 3)
            else:
                image = None

            if image:
                screen.blit(image, image.get_rect(center=rect.center))

            self.text(screen, key, self.f10, CREAM,
                      (rect.x + 6, rect.y + 5))

            if tool == "can":

                bar = pygame.Rect(rect.x + 6, rect.bottom - 10,
                                  rect.width - 12, 5)
                pygame.draw.rect(screen, (20, 15, 12), bar)

                fill_width = int(bar.width * state.water / WATER_MAX)

                if fill_width > 0:
                    pygame.draw.rect(screen, (80, 160, 255),
                                     (bar.x, bar.y, fill_width, bar.height))

                self.text(screen, "%d" % state.water, self.f10, CREAM,
                          (rect.right - 5, rect.y + 5), anchor="topright")

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
        elif state.tool == "can":
            name = "Лейка (вода %d/%d)" % (state.water, WATER_MAX)
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

        if kind == "dig":
            self.start_dig()

        if kind == "water":
            self.start_water()

        if kind == "cross":
            self.cross_slots = [None, None]
            self.cross_sel = 0
            self.cross_msg = ""
            self.cross_result = None

    # ==============================
    # МИНИ-ИГРА: КОПАНИЕ ГРЯДКИ
    # Три удара лопатой: нужно нажать ПРОБЕЛ, когда движущийся
    # маркер в зелёной зоне. Каждый раунд быстрее и зона уже.
    # 2 попадания - грядка, 3 попадания - богатая грядка (урожай x3).
    # ==============================

    DIG_ROUNDS = 3
    DIG_SPEED = [2.4, 3.3, 4.2]
    DIG_ZONE = [0.26, 0.19, 0.13]

    def dig_zone(self, rnd):

        width = self.DIG_ZONE[rnd]
        center = random.uniform(0.12 + width / 2, 0.88 - width / 2)

        return center, width

    def start_dig(self):

        self.dig = {
            "round": 0, "hits": 0, "t": 0.0, "results": [],
            "shift": random.uniform(0, 6.28),
            "phase": "aim", "timer": 0.0, "text": "", "ok": True,
            "zone": self.dig_zone(0)
        }

    def dig_marker(self):

        d = self.dig
        speed = self.DIG_SPEED[min(d["round"], self.DIG_ROUNDS - 1)]

        return 0.5 + 0.5 * math.sin(d["t"] * speed + d["shift"])

    def update_dig(self, dt, game):

        d = self.dig
        d["t"] += dt

        if d["phase"] == "feedback":

            d["timer"] -= dt

            if d["timer"] <= 0:

                if d["round"] >= self.DIG_ROUNDS:
                    d["phase"] = "result"
                    d["timer"] = 1.2
                else:
                    d["phase"] = "aim"
                    d["zone"] = self.dig_zone(d["round"])
                    d["t"] = 0.0
                    d["shift"] = random.uniform(0, 6.28)

        elif d["phase"] == "result":

            d["timer"] -= dt

            if d["timer"] <= 0:
                game.finish_dig(d["hits"])

    def dig_event(self, event, game):

        d = self.dig

        if (event.type == pygame.KEYDOWN and d["phase"] == "aim"
                and event.key in (pygame.K_SPACE, pygame.K_RETURN,
                                  pygame.K_KP_ENTER, pygame.K_e)):

            center, width = d["zone"]
            hit = abs(self.dig_marker() - center) <= width / 2

            if hit:
                d["hits"] += 1

            d["results"].append(hit)
            d["ok"] = hit
            d["text"] = "Отлично!" if hit else "Мимо!"
            d["round"] += 1
            d["phase"] = "feedback"
            d["timer"] = 0.5

    def draw_dig(self, screen):

        d = self.dig
        width, height = screen.get_size()

        panel = pygame.Rect(width // 2 - 260, height // 2 - 130, 520, 260)
        self.panel(screen, panel, 242)

        self.text(screen, "КОПАЕМ ГРЯДКУ", self.f16, GOLD,
                  (panel.centerx, panel.y + 16), anchor="midtop")
        self.text(screen, "Нажмите ПРОБЕЛ, когда маркер в зелёной зоне",
                  self.f10, CREAM, (panel.centerx, panel.y + 46),
                  anchor="midtop")

        bob = int(6 * math.sin(d["t"] * 9)) if d["phase"] == "aim" else 0
        shovel = self.world.tile("shovel")
        screen.blit(shovel,
                    shovel.get_rect(center=(panel.centerx,
                                            panel.y + 92 + bob)))

        bar = pygame.Rect(panel.x + 50, panel.y + 135, panel.width - 100, 30)
        pygame.draw.rect(screen, (25, 18, 14), bar)

        center, zone_width = d["zone"]
        zone = pygame.Rect(
            bar.x + int(bar.width * (center - zone_width / 2)), bar.y,
            int(bar.width * zone_width), bar.height)
        pygame.draw.rect(screen, (90, 190, 90), zone)
        pygame.draw.rect(screen, WOOD, bar, 3)

        marker_x = bar.x + int(bar.width * self.dig_marker())
        pygame.draw.rect(screen, (255, 255, 255),
                         (marker_x - 3, bar.y - 6, 6, bar.height + 12))

        # Три точки: результат каждого удара
        for i in range(self.DIG_ROUNDS):

            if i < len(d["results"]):
                color = (90, 200, 90) if d["results"][i] else (210, 80, 70)
            else:
                color = (90, 85, 80)

            pygame.draw.circle(screen, color,
                               (panel.centerx - 30 + i * 30, panel.y + 192), 9)

        if d["phase"] == "feedback":
            self.text(screen, d["text"], self.f12,
                      GREEN if d["ok"] else (255, 150, 130),
                      (panel.centerx, panel.y + 214), anchor="midtop")

        elif d["phase"] == "result":

            if d["hits"] >= 3:
                line, color = "Отличная грядка! Урожай x3", GOLD
            elif d["hits"] == 2:
                line, color = "Грядка готова", GREEN
            else:
                line, color = "Земля не поддалась", (255, 150, 130)

            self.text(screen, line, self.f12, color,
                      (panel.centerx, panel.y + 214), anchor="midtop")

        self.text(screen, "ESC - отмена", self.f10, GRAY,
                  (panel.centerx, panel.bottom - 8), anchor="midbottom")

    def handle_modal(self, event, game):
        # Возвращает True, если окно нужно закрыть

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                return True

            if game.modal == "inventory" and event.key == pygame.K_i:
                return True

            if game.modal == "book" and event.key == pygame.K_b:
                return True

            if game.modal == "cross" and event.key == pygame.K_e:
                return True

        if game.modal == "inventory":
            self.inventory_event(event, game)

        elif game.modal == "book":
            self.book_event(event, game)

        elif game.modal == "shop":
            self.shop_event(event, game)

        elif game.modal == "dig":
            self.dig_event(event, game)

        # Полив управляется зажатыми клавишами, см. update_water

        elif game.modal == "cross":
            self.cross_event(event, game)

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
        elif game.modal == "dig":
            self.draw_dig(screen)
        elif game.modal == "water":
            self.draw_water(screen)
        elif game.modal == "cross":
            self.draw_cross(screen, game.state)

    # ==============================
    # РЮКЗАК
    # ==============================

    def inv_entries(self, state):
        return ["shovel", "can", "hoe"] + state.inventory_plants()

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

        if entry in TOOL_NAMES:
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

                image = self.world.tile(TOOL_TILES[entry])
                image = pygame.transform.scale(image, (32, 32))
                screen.blit(image, (row.x + 4, row.y + 1))

                self.text(screen, TOOL_NAMES[entry], self.f12, CREAM,
                          (row.x + 48, row.y + 10))

                right = ""

                if entry == "can":
                    right = "вода %d/%d" % (state.water, WATER_MAX)

                if state.tool == entry:
                    right = ("в руке   " + right).strip()

                if right:
                    self.text(screen, right, self.f10, GOLD,
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
                ["Копайте грядки на ферме (мини-игра: три удара), "
                 "выкапывайте растения и собирайте выросший урожай."]
                if entry == "shovel" else
                ["Поливайте посаженные растения. Каждое растение "
                 "поливается только один раз и к утру вырастает.",
                 "Каждый полив тратит порцию воды. Вода: %d/%d. "
                 "Наполняйте лейку у колодца возле дома (E)."
                 % (state.water, WATER_MAX)]
            )

            if entry == "hoe":
                lines = ["Превращает пустую грядку в грядку для "
                         "суперрастений (фиолетовая земля). Обычные "
                         "растения на неё сажать нельзя, а суперрастения "
                         "растут только на ней. Повторное применение "
                         "возвращает обычную грядку."]

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
            "Статус: %s" % status_label(plant, status),
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
            parts.append("%s %d/%d (поисков %d)" % (
                P.BIOME_NAMES[biome], found, len(P.BY_BIOME[biome]),
                state.explore[biome]["searches"]))

        parts.append("Скрещено %d/%d" % (
            len([p for p in P.SUPER if p["id"] in state.discovered]),
            len(P.SUPER)))

        self.text(screen, " | ".join(parts), self.f10, CREAM, (44, 74))

        cols = self.BOOK_COLS
        cell, gap = 60, 5
        x0, y0 = 40, 100

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
        info = pygame.Rect(640, 100, 280, 392)
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
                     (status_label(plant, 0), self.f12, GRAY)]
        else:

            lines = []

            for part in wrap(self.f16, plant["name"], info.width - 28):
                lines.append((part, self.f16, CREAM))

            lines += [
                ("Редкость: %s" % P.RARITY_NAMES[plant["rarity"]],
                 self.f12, P.RARITY_COLORS[plant["rarity"]]),
                ("Биом: %s" % P.BIOME_NAMES[plant["biome"]],
                 self.f12, CREAM),
                (status_label(plant, status), self.f12,
                 GREEN if status == 2 else GOLD),
            ]

        if plant["rarity"] == "super":

            names = " + ".join(
                P.BY_ID[p]["name"] for p in P.recipe_parents(plant["id"]))
            lines.append(("Рецепт: " + names, self.f10, CREAM))

        for string, font, color in lines:
            for part in wrap(font, string, info.width - 28) or [string]:
                self.text(screen, part, font, color, (info.x + 14, yy))
                yy += font.get_height() + 8

        self.text(screen, "Стрелки - выбор | B или ESC - закрыть",
                  self.f10, GRAY, (panel.centerx, panel.bottom - 12),
                  anchor="midbottom")

    # ==============================
    # МИНИ-ИГРА: ПОЛИВ
    # Лейка дрожит в руках. Клавишами A и D (или стрелками) нужно
    # удерживать её над растением, пока идёт полив.
    # Идеально - вода не тратится, хорошо - растение полито, плохо - мимо.
    # ==============================

    WATER_TIME = 4.5
    WATER_ZONE = 0.28

    def start_water(self):

        self.wg = {
            "t": 0.0, "pos": 0.5 + random.uniform(-0.15, 0.15), "vel": 0.0,
            "inside": 0.0, "phase": "play", "timer": 0.0, "score": 0.0,
            "seed": random.uniform(0, 100), "jn": 0.0
        }

    def update_water(self, dt, game):

        d = self.wg
        dt = min(dt, 0.05)

        if d["phase"] == "play":

            d["t"] += dt

            keys = pygame.key.get_pressed()
            push = 0

            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                push += 1

            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                push -= 1

            # Лейку уводит в сторону медленным дрейфом и быстрой дрожью,
            # к концу полива тряска нарастает. A и D двигают лейку обратно.
            grow = 0.75 + 0.6 * d["t"] / self.WATER_TIME

            drift = (math.sin(d["t"] * 1.3 + d["seed"])
                     + math.sin(d["t"] * 2.9 + d["seed"] * 2) * 0.7) * 0.40

            d["jn"] = d["jn"] * 0.85 + random.uniform(-1, 1) * 0.15

            jitter = (math.sin(d["t"] * 17 + d["seed"]) * 0.5
                      + d["jn"] * 2) * 0.6

            d["vel"] = (drift + jitter) * grow + push * 0.75
            d["pos"] = min(0.96, max(0.04, d["pos"] + d["vel"] * dt))

            if abs(d["pos"] - 0.5) <= self.WATER_ZONE / 2:
                d["inside"] += dt

            if d["t"] >= self.WATER_TIME:
                d["phase"] = "result"
                d["timer"] = 1.4
                d["score"] = min(1.0, d["inside"] / self.WATER_TIME)

        else:

            d["timer"] -= dt

            if d["timer"] <= 0:
                game.finish_water(d["score"])

    def draw_water(self, screen):

        d = self.wg
        width, height = screen.get_size()

        panel = pygame.Rect(width // 2 - 270, height // 2 - 155, 540, 310)
        self.panel(screen, panel, 242)

        self.text(screen, "ПОЛИВ", self.f16, (130, 200, 255),
                  (panel.centerx, panel.y + 14), anchor="midtop")
        self.text(screen, "Лейка дрожит! Держите её над растением: "
                  "A и D (или стрелки)", self.f10, CREAM,
                  (panel.centerx, panel.y + 42), anchor="midtop")

        bar = pygame.Rect(panel.x + 50, panel.y + 232, panel.width - 100, 22)
        pygame.draw.rect(screen, (25, 18, 14), bar)

        zone_w = int(bar.width * self.WATER_ZONE)
        zone = pygame.Rect(bar.centerx - zone_w // 2, bar.y, zone_w,
                           bar.height)
        pygame.draw.rect(screen, (70, 170, 200), zone)
        pygame.draw.rect(screen, WOOD, bar, 3)

        # Растение, которое поливаем
        if self.water_plant:
            sprout = P.sprout_icon(self.water_plant, "seed", 3)
            screen.blit(sprout, (bar.centerx - 24, bar.y - 46))

        # Лейка: чем сильнее движется, тем заметнее трясётся
        can_x = bar.x + int(bar.width * d["pos"])
        can_y = panel.y + 92

        shake = min(3, int(abs(d["vel"]) * 3)) if d["phase"] == "play" else 0
        jitter_x = random.randint(-shake, shake) if shake else 0
        jitter_y = random.randint(-shake, shake) if shake else 0

        can = self.world.tile("watering_can")
        screen.blit(can, can.get_rect(center=(can_x + jitter_x,
                                              can_y + jitter_y)))

        # Струйка воды
        if d["phase"] == "play":

            top = can_y + 26
            fall = bar.y - 6 - top

            for k in range(8):
                f = (d["t"] * 1.9 + k / 8) % 1
                pygame.draw.rect(screen, (120, 190, 255),
                                 (can_x + 12 + int(f * 8), top + int(f * fall),
                                  3, 6))

        # Шкала успеха с отметками "хорошо" и "идеально"
        meter = pygame.Rect(panel.x + 50, panel.y + 266, panel.width - 100, 8)
        pygame.draw.rect(screen, (25, 18, 14), meter)

        filled = int(meter.width * min(1.0, d["inside"] / self.WATER_TIME))

        if filled > 0:
            pygame.draw.rect(screen, (90, 190, 255),
                             (meter.x, meter.y, filled, meter.height))

        for mark in (0.5, 0.8):
            mx = meter.x + int(meter.width * mark)
            pygame.draw.line(screen, GOLD, (mx, meter.y - 3),
                             (mx, meter.bottom + 3), 2)

        if d["phase"] == "play":
            left = max(0.0, self.WATER_TIME - d["t"])
            self.text(screen, "Осталось: %.1f с" % left, self.f10, GRAY,
                      (panel.right - 20, panel.y + 14), anchor="topright")
        else:

            if d["score"] >= 0.8:
                line, color = "Идеально! Вода сэкономлена", GOLD
            elif d["score"] >= 0.5:
                line, color = "Растение полито", GREEN
            else:
                line, color = "Вода пролилась мимо", (255, 150, 130)

            self.text(screen, line, self.f16, color,
                      (panel.centerx, panel.y + 150), anchor="center")

    # ==============================
    # СИЯНИЕ ВОКРУГ ВАЖНЫХ МЕСТ
    # ==============================

    def tinted_glow(self, radius, color):

        key = (radius, color)

        if key not in self.glows:

            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            for i in range(radius, 0, -4):
                alpha = int(105 * (1 - i / radius) ** 1.5)
                pygame.draw.circle(surf, (*color, alpha),
                                   (radius, radius), i)

            self.glows[key] = surf

        return self.glows[key]

    def spark(self):

        if self.spark_img is None:

            surf = pygame.Surface((7, 7), pygame.SRCALPHA)
            pygame.draw.line(surf, (255, 255, 255, 255), (0, 3), (6, 3))
            pygame.draw.line(surf, (255, 255, 255, 255), (3, 0), (3, 6))
            surf.set_at((3, 3), (255, 250, 200, 255))

            self.spark_img = surf

        return self.spark_img

    def draw_glows(self, screen, points, camera, t):
        # Мерцающее сияние и искры: с этим местом можно взаимодействовать

        size = screen.get_size()

        for point in points:

            sx = point["pos"][0] - camera[0]
            sy = point["pos"][1] - camera[1]
            radius = point["radius"]

            if not (-radius < sx < size[0] + radius
                    and -radius < sy < size[1] + radius):
                continue

            speed = 4.2 if point["near"] else 2.2
            pulse = 0.65 + 0.35 * math.sin(t * speed + point["phase"])
            boost = 1.3 if point["near"] else 1.0
            alpha = int(min(255, 255 * point["strength"] * pulse * boost))

            image = self.tinted_glow(radius, point["color"])
            image.set_alpha(alpha)
            screen.blit(image, (sx - radius, sy - radius))

            spark = self.spark()

            for k in range(3):

                phase = (t * 0.6 + k / 3 + point["phase"]) % 1
                x = sx + math.sin(k * 2.1 + t * 0.9) * radius * 0.45
                y = sy + radius * 0.25 - phase * radius * 0.95

                spark.set_alpha(int(255 * (1 - phase) * point["strength"]))
                screen.blit(spark, (x - 3, y - 3))

    # ==============================
    # СТОЛ СКРЕЩИВАНИЯ
    # ==============================

    def cross_clean(self, state):

        for i in range(2):

            plant_id = self.cross_slots[i]

            if plant_id and state.inventory.get(plant_id, 0) <= 0:
                self.cross_slots[i] = None

    def cross_toggle(self, plant_id):

        if plant_id in self.cross_slots:
            self.cross_slots[self.cross_slots.index(plant_id)] = None
        elif None in self.cross_slots:
            self.cross_slots[self.cross_slots.index(None)] = plant_id
        else:
            self.cross_slots[1] = plant_id

        self.cross_result = None
        self.cross_msg = ""

    def cross_do(self, game):

        ok, message, result = game.state.cross(*self.cross_slots)

        self.cross_msg = message
        self.cross_result = result if ok else None

        if ok:
            self.cross_slots = [None, None]
            game.say(message, P.RARITY_COLORS["super"])

    def cross_event(self, event, game):

        state = game.state
        owned = state.inventory_plants()
        count = len(owned)

        self.cross_clean(state)
        self.cross_sel = max(0, min(self.cross_sel, max(0, count - 1)))

        clicked = self.clicked_row(event)

        if clicked is not None:

            if clicked == 1000:
                self.cross_do(game)

            elif clicked >= 3000:

                first, second = P.recipe_parents(
                    P.SUPER[clicked - 3000]["id"])

                missing = [P.BY_ID[x]["name"] for x in (first, second)
                           if state.inventory.get(x, 0) < 1]

                self.cross_result = None

                if missing:
                    self.cross_msg = "Не хватает: " + ", ".join(missing)
                else:
                    self.cross_slots = [first, second]
                    self.cross_msg = ""

            elif clicked >= 2000:
                self.cross_slots[clicked - 2000] = None

            elif clicked < count:

                if clicked == self.cross_sel:
                    self.cross_toggle(owned[clicked])
                else:
                    self.cross_sel = clicked

        elif event.type == pygame.KEYDOWN:

            key = event.key

            if key in (pygame.K_UP, pygame.K_w):
                self.cross_sel = max(0, self.cross_sel - 1)

            elif key in (pygame.K_DOWN, pygame.K_s):
                self.cross_sel = min(max(0, count - 1), self.cross_sel + 1)

            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                         pygame.K_SPACE) and count:
                self.cross_toggle(owned[self.cross_sel])

            elif key == pygame.K_c:
                self.cross_do(game)

            elif key in (pygame.K_x, pygame.K_BACKSPACE):
                self.cross_slots = [None, None]

    def draw_cross(self, screen, state):

        self.cross_clean(state)

        panel = pygame.Rect(40, 24, 880, 492)
        self.panel(screen, panel, 242)

        super_color = P.RARITY_COLORS["super"]

        self.text(screen, "СТОЛ СКРЕЩИВАНИЯ", self.f22, super_color, (64, 40))
        self.text(screen, "Нажмите на рецепт справа: растения лягут в слоты",
                  self.f12, GRAY, (64, 72))

        # Растения из рюкзака
        owned = state.inventory_plants()
        self.cross_sel = max(0, min(self.cross_sel, max(0, len(owned) - 1)))

        self.text(screen, "ВАШИ РАСТЕНИЯ", self.f12, GOLD, (64, 104))

        if not owned:
            self.text(screen, "Рюкзак пуст", self.f12, GRAY, (70, 134))

        visible = 10
        top = 0 if self.cross_sel < visible else self.cross_sel - visible + 1
        y = 130

        for index in range(top, min(len(owned), top + visible)):

            plant_id = owned[index]
            plant = P.BY_ID[plant_id]
            row = pygame.Rect(60, y, 270, 34)
            self.rects.append((row, index))

            if index == self.cross_sel:
                self.highlight(screen, row)

            screen.blit(P.icon(plant_id, 2), (row.x + 4, row.y + 1))
            self.text(screen, plant["name"], self.f10,
                      P.RARITY_COLORS[plant["rarity"]], (row.x + 44, row.y + 11))

            right = ("в слоте" if plant_id in self.cross_slots
                     else "x%d" % state.inventory[plant_id])
            self.text(screen, right, self.f10, GOLD,
                      (row.right - 8, row.y + 11), anchor="topright")

            y += 38

        # Два слота
        slots = [pygame.Rect(355, 130, 110, 130),
                 pygame.Rect(495, 130, 110, 130)]

        self.text(screen, "+", self.f22, CREAM, (480, 175), anchor="midtop")

        for i, rect in enumerate(slots):

            self.rects.append((rect, 2000 + i))
            self.panel(screen, rect, 205)

            plant_id = self.cross_slots[i]

            if plant_id:

                screen.blit(P.icon(plant_id, 4),
                            (rect.centerx - 32, rect.y + 10))

                for k, part in enumerate(
                        wrap(self.f10, P.BY_ID[plant_id]["name"],
                             rect.width - 12)[:3]):
                    self.text(screen, part, self.f10, CREAM,
                              (rect.centerx, rect.y + 82 + k * 13),
                              anchor="midtop")
            else:
                self.text(screen, "?", self.f22, GRAY, rect.center,
                          anchor="center")

        # Кнопка
        ready = all(self.cross_slots)
        button = pygame.Rect(375, 280, 210, 40)
        self.rects.append((button, 1000))
        self.panel(screen, button, 235)

        if ready:
            pygame.draw.rect(screen, GREEN, button, 3, border_radius=4)

        self.text(screen, "СКРЕСТИТЬ (C)", self.f12,
                  CREAM if ready else GRAY, button.center, anchor="center")

        if self.cross_msg:

            color = super_color if self.cross_result else (255, 150, 130)

            for k, part in enumerate(wrap(self.f12, self.cross_msg, 250)):
                self.text(screen, part, self.f12, color,
                          (480, 332 + k * 18), anchor="midtop")

        if self.cross_result:
            image = P.icon(self.cross_result, 6)
            screen.blit(image, image.get_rect(midtop=(480, 372)))

        # Рецепты: какие именно растения нужны для каждого суперрастения
        self.text(screen, "РЕЦЕПТЫ", self.f12, GOLD, (620, 104))

        yy = 126

        for index, plant in enumerate(P.SUPER):

            row = pygame.Rect(620, yy, 284, 58)
            self.rects.append((row, 3000 + index))
            self.panel(screen, row, 175)

            first, second = P.recipe_parents(plant["id"])
            have = [state.inventory.get(first, 0),
                    state.inventory.get(second, 0)]
            ready = have[0] > 0 and have[1] > 0

            if ready:
                pygame.draw.rect(screen, GREEN, row, 2, border_radius=3)

            status = self.book_status(state, plant["id"])

            if status == 0:
                image, title, color = (P.silhouette(plant["id"], 2),
                                       "???", GRAY)
            else:
                image, title, color = (P.icon(plant["id"], 2),
                                       plant["name"], super_color)

            screen.blit(image, (row.x + 6, row.y + 13))
            self.text(screen, title, self.f10, color, (row.x + 44, row.y + 5))

            for k, plant_id in enumerate((first, second)):

                label = "%s%s (x%d)" % ("+ " if k else "",
                                        P.BY_ID[plant_id]["name"], have[k])

                self.text(screen, label, self.f10,
                          GREEN if have[k] > 0 else (255, 150, 130),
                          (row.x + 44, row.y + 20 + k * 14))

            if ready:
                self.text(screen, "ГОТОВО", self.f10, GREEN,
                          (row.right - 8, row.y + 5), anchor="topright")

            if status == 2:
                self.checkmark(screen, row.right - 20, row.y + 36)

            yy += 62

        self.text(screen,
                  "СТРЕЛКИ - выбор | ENTER - в слот | C - скрестить | X - очистить | ESC - выйти",
                  self.f10, GRAY, (panel.centerx, panel.bottom - 10),
                  anchor="midbottom")

    # ==============================
    # ЗАТЕМНЕНИЕ ЭКРАНА (СОН)
    # ==============================

    def draw_fade(self, screen, alpha, lines):

        if alpha <= 0:
            return

        size = screen.get_size()

        if self.fade is None or self.fade.get_size() != size:
            self.fade = pygame.Surface(size)

        self.fade.fill((5, 6, 14))
        self.fade.set_alpha(int(min(255, alpha)))
        screen.blit(self.fade, (0, 0))

        if alpha > 90:
            for i, (string, font, color) in enumerate(lines):
                self.text(screen, string, font, color,
                          (size[0] // 2, size[1] // 2 - 20 + i * 36),
                          anchor="center")

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
                self.shop_act(game)
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
                self.shop_act(game)

    def shop_act(self, game):

        state = game.state

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

        # Новое растение отмечаем так же, как при поиске в биоме
        if ok and message.endswith("новое!"):
            game.say(message, GOLD)

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
                          (row.right - 10, row.y + 8), anchor="topright")

                if tab == 0 and plant_id not in state.discovered:
                    self.text(screen, "НОВОЕ", self.f10, GOLD,
                              (row.right - 10, row.y + 28),
                              anchor="topright")

                y += 50

        if self.shop_message:
            self.text(screen, self.shop_message, self.f12, GOLD,
                      (panel.centerx, panel.bottom - 40), anchor="midbottom")

        self.text(screen,
                  "TAB - сменить список | СТРЕЛКИ - выбор | ENTER - купить или продать | ESC - выйти",
                  self.f10, GRAY, (panel.centerx, panel.bottom - 14),
                  anchor="midbottom")
