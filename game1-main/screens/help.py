import pygame

from systems.ui import UI, CREAM, GOLD, GREEN, GRAY, WOOD


# Страницы инструкции. type "text" - абзацы, type "keys" - таблица клавиш.
PAGES = [
    {
        "title": "О ЧЁМ ИГРА",
        "type": "text",
        "paras": [
            "Little Root - игра о растениях. Ваша цель: найти и вырастить "
            "все 51 растение и заполнить книгу коллекционера на 100%.",
            "Мир состоит из трёх биомов: ЛЕС (слева, за рекой), ЛУГ (в "
            "центре, здесь ваша ферма) и ЗИМА (справа).",
            "В каждом биоме растут свои растения. Они бывают обычные, "
            "необычные, редкие и легендарные: чем реже растение, тем "
            "меньше шанс его найти.",
            "Ещё 6 суперрастений найти нельзя, их получают только "
            "скрещиванием.",
            "Игра считается пройденной, когда коллекция заполнена на 100%. "
            "Прогресс сохраняется автоматически.",
        ],
    },
    {
        "title": "УПРАВЛЕНИЕ",
        "type": "keys",
        "rows": [
            ("W A S D", "Ходьба"),
            ("1 2 3 4", "Лопата, лейка, растение, мотыга"),
            ("ПРОБЕЛ", "Использовать предмет на клетке перед собой"),
            ("E", "Взаимодействие: искать растение, набрать воды, "
                  "поговорить с торговцем, стол скрещивания, сон"),
            ("I", "Рюкзак"),
            ("B", "Книга коллекционера"),
            ("H", "Эта инструкция"),
            ("ESC", "Меню (игра сохраняется)"),
        ],
    },
    {
        "title": "ПОИСК РАСТЕНИЙ",
        "type": "text",
        "paras": [
            "Ходите по лесу, лугу и зимней части карты и ищите мерцающие "
            "кустики. Подойдите к такому кустику и нажмите E, чтобы найти "
            "растение.",
            "Каждый день места поиска появляются заново и в новых местах, "
            "а найденное растение каждый раз случайное.",
            "Одно и то же растение можно найти несколько раз. Дубликаты "
            "пригодятся для торговли и скрещивания.",
            "Новое растение отмечается сообщением «новое!» и сразу "
            "попадает в книгу как найденное. В коллекцию оно "
            "засчитывается, когда вы его вырастите.",
        ],
    },
    {
        "title": "ФЕРМА",
        "type": "text",
        "paras": [
            "1. Возьмите лопату (1), встаньте перед клеткой внутри забора "
            "и нажмите ПРОБЕЛ. Начнётся мини-игра из трёх ударов: нажимайте "
            "ПРОБЕЛ, когда маркер в зелёной зоне. Два попадания дают "
            "грядку, три дают богатую грядку (урожай x3).",
            "2. Выберите растение (3, повторное нажатие меняет растение) и "
            "нажмите ПРОБЕЛ на грядке.",
            "3. Возьмите лейку (2) и нажмите ПРОБЕЛ на растении. Лейка "
            "дрожит: держите её над растением клавишами A и D (или "
            "стрелками). Хороший полив тратит порцию воды, идеальный не "
            "тратит, а если вода пролилась мимо, попробуйте ещё. Воду "
            "набирают у колодца возле дома (E).",
            "4. Наутро политое растение вырастает. Соберите урожай "
            "лопатой (1). Ею же можно выкопать растение обратно.",
            "Повторно полить растение нельзя. Не политое растение за ночь "
            "не вырастет.",
        ],
    },
    {
        "title": "ТОРГОВЕЦ И СКРЕЩИВАНИЕ",
        "type": "text",
        "paras": [
            "Странник живёт в лесу, за мостом через реку. Нажмите E рядом "
            "с ним. Он покупает дубликаты (одно растение каждого вида "
            "остаётся у вас) и продаёт растения, которых вам не хватает. "
            "Его товары меняются каждый день.",
            "Стол скрещивания стоит слева от фермы. Выберите два "
            "растения из разных биомов и нажмите C. Все рецепты расписаны "
            "на самом столе: нажмите на рецепт, и нужные растения лягут "
            "в слоты. Так получают суперрастения.",
            "Суперрастения растут только на супергрядке: возьмите мотыгу "
            "(4) и примените её на пустой грядке. Обычные растения на "
            "такую грядку сажать нельзя.",
        ],
    },
    {
        "title": "ВРЕМЯ СУТОК И СОВЕТЫ",
        "type": "text",
        "paras": [
            "Сутки длятся около пяти минут: утро, день, вечер и ночь. В "
            "6:00 начинается новый день: растения вырастают, торговец "
            "обновляет товары, а в мире появляются новые места поиска.",
            "Светящиеся места (дом, колодец, стол скрещивания и торговец) - "
            "с ними можно взаимодействовать клавишей E.",
            "Ночью можно лечь спать: подойдите к двери дома после 19:00 и "
            "нажмите E. Утро наступит плавно.",
            "Совет: каждый день ищите растения, лишнее продавайте и копите "
            "на редкие. Заранее собирайте пары для скрещивания.",
            "Игра сохраняется сама каждые несколько секунд и при выходе "
            "в меню. В меню кнопка ИГРАТЬ продолжает вашу игру, а "
            "НОВАЯ ИГРА начинает заново и сначала спрашивает "
            "подтверждение.",
        ],
    },
]


class HelpScreen:

    def __init__(self, fonts):

        self.ui = UI(fonts, None)
        self.page = 0
        self.rects = []

    def open(self):
        self.page = 0

    def handle_event(self, event):
        # Возвращает "back", когда инструкцию нужно закрыть

        if event.type == pygame.KEYDOWN:

            key = event.key

            if key == pygame.K_ESCAPE:
                return "back"

            if key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN,
                       pygame.K_SPACE):
                self.page = min(len(PAGES) - 1, self.page + 1)

            elif key in (pygame.K_LEFT, pygame.K_a):
                self.page = max(0, self.page - 1)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for rect, action in self.rects:

                if rect.collidepoint(event.pos):

                    if action == "next":
                        self.page = min(len(PAGES) - 1, self.page + 1)
                    elif action == "prev":
                        self.page = max(0, self.page - 1)
                    else:
                        return "back"

        return None

    # ==============================
    # ОТРИСОВКА
    # ==============================

    def draw_paragraphs(self, screen, paras, x, y, width, height):
        # Если текст не помещается обычным шрифтом, берём мельче

        from systems.ui import wrap

        for font, step in ((self.ui.f12, 20), (self.ui.f10, 16)):

            wrapped = [wrap(font, p, width) for p in paras]
            total = sum(len(w) * step + 12 for w in wrapped)

            if total <= height or font is self.ui.f10:
                break

        for lines in wrapped:

            for line in lines:
                self.ui.text(screen, line, font, CREAM, (x, y))
                y += step

            y += 12

    def draw_keys(self, screen, rows, x, y):

        from systems.ui import wrap

        ui = self.ui

        for keys, description in rows:

            kx = x

            for key in keys.split(" "):

                image = ui.f12.render(key, True, CREAM)
                box = pygame.Rect(kx, y, image.get_width() + 18, 30)

                ui.panel(screen, box, 235)
                screen.blit(image, image.get_rect(center=box.center))

                kx = box.right + 6

            lines = wrap(ui.f12, description, 520)

            for i, line in enumerate(lines):
                ui.text(screen, line, ui.f12, GOLD if i == 0 else CREAM,
                        (x + 270, y + 8 + i * 18))

            y += max(42, 18 * len(lines) + 20)

    def draw(self, screen, background=None, clear=True):

        ui = self.ui
        self.rects = []
        width, height = screen.get_size()

        if background is not None:
            screen.blit(background, (0, 0))
        elif clear:
            screen.fill((100, 130, 100))

        dim = pygame.Surface((width, height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 130))
        screen.blit(dim, (0, 0))

        panel = pygame.Rect(30, 24, width - 60, height - 48)
        ui.panel(screen, panel, 242)

        page = PAGES[self.page]

        ui.text(screen, "ИНСТРУКЦИЯ", ui.f10, GRAY, (56, 44))
        ui.text(screen, page["title"], ui.f22, GOLD, (56, 62))
        ui.text(screen, "Страница %d из %d" % (self.page + 1, len(PAGES)),
                ui.f10, GRAY, (panel.right - 28, 48), anchor="topright")

        pygame.draw.line(screen, WOOD, (56, 98), (panel.right - 28, 98), 3)

        if page["type"] == "keys":
            self.draw_keys(screen, page["rows"], 60, 116)
        else:
            self.draw_paragraphs(screen, page["paras"], 60, 114,
                                 panel.width - 100, 330)

        # Точки страниц
        for i in range(len(PAGES)):

            color = GREEN if i == self.page else (90, 85, 80)
            pygame.draw.circle(
                screen, color,
                (width // 2 - (len(PAGES) - 1) * 12 + i * 24, 448), 6)

        # Кнопки
        buttons = [
            ("< НАЗАД", "prev", pygame.Rect(56, 468, 150, 34),
             self.page > 0),
            ("ЗАКРЫТЬ", "close", pygame.Rect(width // 2 - 75, 468, 150, 34),
             True),
            ("ДАЛЕЕ >", "next", pygame.Rect(panel.right - 206, 468, 150, 34),
             self.page < len(PAGES) - 1),
        ]

        for label, action, rect, enabled in buttons:

            ui.panel(screen, rect, 235)
            ui.text(screen, label, ui.f12, CREAM if enabled else GRAY,
                    rect.center, anchor="center")

            if enabled:
                self.rects.append((rect, action))
