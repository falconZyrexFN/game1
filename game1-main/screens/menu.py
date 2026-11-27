
import pygame

from systems import plants
import os
import math

from systems import audio


class Menu:

    def __init__(self, fonts):

        self.title_font = fonts["title"]
        self.ui_font = fonts["ui"]

        self.buttons = [
            ("ИГРАТЬ", "play"),
            ("НОВАЯ ИГРА", "new"),
            ("КОЛЛЕКЦИЯ", "collection"),
            ("ИНСТРУКЦИЯ", "help"),
            ("НАСТРОЙКИ", "settings"),
            ("ВЫХОД", "quit")
        ]

        self.button_rects = []
        self.hovered_action = None

        # Окно подтверждения новой игры
        self.confirm = False
        self.confirm_focus = 1
        self.confirm_rects = []

        self.animation_time = 0

        self.width = 960
        self.height = 540

        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        background_path = os.path.join(
            base_dir,
            "assets",
            "images",
            "menu_background.png"
        )

        try:

            image = pygame.image.load(
                background_path
            ).convert()

            self.background = pygame.transform.scale(
                image,
                (self.width, self.height)
            )

        except (FileNotFoundError, pygame.error):

            print("Не удалось загрузить фон меню!")

            self.background = None

        # Цвета оформления
        self.wood_dark = (76, 43, 30)
        self.wood = (139, 83, 48)
        self.wood_light = (181, 119, 70)

        self.cream = (255, 235, 190)
        self.green = (116, 160, 83)
        self.green_light = (157, 195, 112)

        self.text_color = (255, 244, 211)

        # Шрифты
        self.logo_font = pygame.font.Font(
            None, 66
        )

        self.subtitle_font = pygame.font.Font(
            None, 19
        )

        self.button_font = pygame.font.Font(
            None, 27
        )

        self.small_font = pygame.font.Font(
            None, 19
        )

    # =================================
    # ОБРАБОТКА СОБЫТИЙ
    # =================================

    def save_info(self):

        # Читаем сохранение не чаще раза в секунду
        now = pygame.time.get_ticks() // 1000

        if getattr(self, "_info_time", None) != now:
            self._info_time = now
            self._info = plants.saved_summary()

        return self._info

    def request_new_game(self):
        # Если есть сохранение, сначала спрашиваем: игра с нуля сотрёт прогресс

        exists, _ = plants.saved_summary()

        if exists:
            self.confirm = True
            self.confirm_focus = 1
            return None

        return "new"

    def handle_confirm(self, event):

        if event.type == pygame.MOUSEMOTION:

            for index, rect in enumerate(self.confirm_rects):
                if rect.collidepoint(event.pos):
                    self.confirm_focus = index

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for index, rect in enumerate(self.confirm_rects):
                if rect.collidepoint(event.pos):
                    return self.finish_confirm(index)

        elif event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB,
                             pygame.K_a, pygame.K_d):
                self.confirm_focus = 1 - self.confirm_focus

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.finish_confirm(self.confirm_focus)

            elif event.key == pygame.K_ESCAPE:
                self.confirm = False

        return None

    def finish_confirm(self, index):

        self.confirm = False
        audio.play_ui("click")

        # 0 - "Да, заново", 1 - "Отмена"
        return "new" if index == 0 else None

    def handle_event(self, event):

        if self.confirm:
            return self.handle_confirm(event)

        if event.type == pygame.MOUSEMOTION:

            current_hover = None

            for rect, action in self.button_rects:

                if rect.collidepoint(event.pos):

                    current_hover = action
                    break

            if current_hover != self.hovered_action:

                if current_hover is not None:
                    audio.play_ui("hover")

                self.hovered_action = current_hover

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                for rect, action in self.button_rects:

                    if rect.collidepoint(event.pos):

                        audio.play_ui("click")

                        if action == "new":
                            return self.request_new_game()

                        return action

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_RETURN:

                audio.play_ui("click")

                # Enter всегда продолжает игру и ничего не стирает
                return "play"

            if event.key == pygame.K_ESCAPE:

                return None

        return None

    # =================================
    # ДЕРЕВЯННАЯ ПАНЕЛЬ
    # =================================

    def draw_wood_panel(self, screen, rect, hovered=False):

        # Тень
        shadow = rect.move(0, 5)

        pygame.draw.rect(
            screen,
            (43, 29, 22),
            shadow
        )

        # Основная доска
        color = self.wood_light if hovered else self.wood

        pygame.draw.rect(
            screen,
            color,
            rect
        )

        # Внешняя рамка
        pygame.draw.rect(
            screen,
            self.wood_dark,
            rect,
            5
        )

        # Внутренняя рамка
        inner = rect.inflate(-12, -12)

        pygame.draw.rect(
            screen,
            (213, 157, 94),
            inner,
            2
        )

        # Декоративные точки
        pygame.draw.circle(
            screen,
            (75, 44, 29),
            (rect.x + 12, rect.y + 12),
            3
        )

        pygame.draw.circle(
            screen,
            (75, 44, 29),
            (rect.right - 12, rect.y + 12),
            3
        )

        pygame.draw.circle(
            screen,
            (75, 44, 29),
            (rect.x + 12, rect.bottom - 12),
            3
        )

        pygame.draw.circle(
            screen,
            (75, 44, 29),
            (rect.right - 12, rect.bottom - 12),
            3
        )

    # =================================
    # ЛОГОТИП LITTLE ROOT
    # =================================

    def draw_logo(self, screen):

        rect = pygame.Rect(
            45, 35, 405, 165
        )

        self.draw_wood_panel(screen, rect)

        # Название игры
        little = self.logo_font.render(
            "Little",
            True,
            (255, 235, 190)
        )

        root = self.logo_font.render(
            "Root",
            True,
            (157, 207, 113)
        )

        screen.blit(
            little,
            (80, 65)
        )

        screen.blit(
            root,
            (235, 65)
        )

        # Росток
        pygame.draw.line(
            screen,
            (91, 151, 76),
            (360, 111),
            (360, 80),
            5
        )

        pygame.draw.ellipse(
            screen,
            (112, 177, 85),
            (340, 77, 23, 13)
        )

        pygame.draw.ellipse(
            screen,
            (145, 202, 104),
            (359, 68, 24, 14)
        )

        subtitle = self.subtitle_font.render(
            "YOUR LITTLE FOREST ADVENTURE",
            True,
            self.cream
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(center=(247, 160))
        )

    # =================================
    # КНОПКИ МЕНЮ
    # =================================

    def draw_buttons(self, screen):

        self.button_rects = []

        mouse_pos = pygame.mouse.get_pos()

        start_y = 212

        for index, (text, action) in enumerate(self.buttons):

            rect = pygame.Rect(
                75,
                start_y + index * 49,
                320,
                40
            )

            hovered = rect.collidepoint(mouse_pos)

            self.draw_wood_panel(
                screen,
                rect,
                hovered
            )

            # Иконки
            icons = [
                "▶",
                "+",
                "★",
                "?",
                "⚙",
                "✕"
            ]

            icon = self.button_font.render(
                icons[index],
                True,
                self.green_light
            )

            screen.blit(
                icon,
                icon.get_rect(midleft=(rect.x + 19, rect.centery))
            )

            # Текст
            label = self.button_font.render(
                text,
                True,
                self.text_color
            )

            screen.blit(
                label,
                label.get_rect(
                    center=(rect.centerx + 15, rect.centery)
                )
            )

            # На кнопке ИГРАТЬ видно, что именно запустится
            if action == "play":

                exists, day = self.save_info()

                if not exists:
                    note = "НОВАЯ"
                elif day > 0:
                    note = "ДЕНЬ %d" % day
                else:
                    note = ""

                if note:

                    info = self.small_font.render(note, True, self.cream)

                    screen.blit(
                        info,
                        info.get_rect(midright=(rect.right - 14,
                                                rect.centery))
                    )

            self.button_rects.append(
                (rect, action)
            )

    # =================================
    # СЧЁТЧИК РАСТЕНИЙ
    # =================================

    def collection_progress(self):

        # Читаем сохранение не чаще раза в секунду
        now = pygame.time.get_ticks() // 1000

        if getattr(self, "_progress_time", None) != now:
            self._progress_time = now
            self._progress = plants.saved_progress()

        return self._progress

    def draw_collection_counter(self, screen):

        rect = pygame.Rect(
            735, 465, 200, 55
        )

        self.draw_wood_panel(screen, rect)

        label = self.small_font.render(
            "РАСТЕНИЯ",
            True,
            self.cream
        )

        counter = self.button_font.render(
            "%d / %d" % self.collection_progress(),
            True,
            (157, 207, 113)
        )

        screen.blit(
            label,
            (rect.x + 14, rect.y + 16)
        )

        screen.blit(
            counter,
            (rect.x + 115, rect.y + 12)
        )

    # =================================
    # АНИМАЦИЯ
    # =================================

    def update_animation(self, dt):

        self.animation_time += dt

    def draw_animation(self, screen):

        # Небольшие светящиеся частицы
        for i in range(7):

            x = 460 + i * 65

            y = 130 + math.sin(
                self.animation_time * 1.5 + i
            ) * 12

            pygame.draw.circle(
                screen,
                (255, 225, 145),
                (int(x), int(y)),
                2
            )

    # =================================
    # ГЛАВНАЯ ОТРИСОВКА
    # =================================

    def draw(self, screen):

        if self.background:

            screen.blit(
                self.background,
                (0, 0)
            )

        else:

            screen.fill(
                (100, 130, 100)
            )

        self.draw_animation(screen)

        self.draw_logo(screen)

        self.draw_buttons(screen)

        self.draw_collection_counter(screen)

        # Версия игры
        version = self.small_font.render(
            "VERSION 1.0.0",
            True,
            self.cream
        )

        screen.blit(
            version,
            (15, 510)
        )

        self.draw_confirm(screen)

    def draw_confirm(self, screen):

        if not self.confirm:
            return

        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, (0, 0))

        panel = pygame.Rect(0, 0, 600, 230)
        panel.center = (screen.get_width() // 2, screen.get_height() // 2)

        self.draw_wood_panel(screen, panel, False)

        title = self.button_font.render(
            "НАЧАТЬ НОВУЮ ИГРУ?", True, self.cream)
        screen.blit(title, title.get_rect(midtop=(panel.centerx,
                                                  panel.y + 24)))

        lines = [
            "Весь текущий прогресс будет удалён.",
            "Чтобы вернуться в свою игру, нажмите «ИГРАТЬ».",
        ]

        for i, line in enumerate(lines):
            text = self.small_font.render(line, True, self.text_color)
            screen.blit(text, text.get_rect(midtop=(panel.centerx,
                                                    panel.y + 78 + i * 26)))

        self.confirm_rects = [
            pygame.Rect(panel.x + 30, panel.bottom - 76, 255, 48),
            pygame.Rect(panel.right - 285, panel.bottom - 76, 255, 48),
        ]

        for index, (rect, label) in enumerate(
                zip(self.confirm_rects, ("ДА, ЗАНОВО", "ОТМЕНА"))):

            self.draw_wood_panel(screen, rect, index == self.confirm_focus)

            text = self.button_font.render(label, True, self.text_color)
            screen.blit(text, text.get_rect(center=rect.center))
