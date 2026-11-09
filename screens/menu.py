
import pygame
import os
import math

from systems import audio


class Menu:

    def __init__(self, fonts):

        self.title_font = fonts["title"]
        self.ui_font = fonts["ui"]

        self.buttons = [
            ("ИГРАТЬ", "new"),
            ("ПРОДОЛЖИТЬ", "continue"),
            ("КОЛЛЕКЦИЯ", "collection"),
            ("НАСТРОЙКИ", "settings"),
            ("ВЫХОД", "quit")
        ]

        self.button_rects = []
        self.hovered_action = None

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

    def handle_event(self, event):

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

                        return action

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_RETURN:

                audio.play_ui("click")

                return "new"

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

        start_y = 225

        for index, (text, action) in enumerate(self.buttons):

            rect = pygame.Rect(
                75,
                start_y + index * 57,
                320,
                46
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
                "↻",
                "★",
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
                (rect.x + 19, rect.y + 9)
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

            self.button_rects.append(
                (rect, action)
            )

    # =================================
    # СЧЁТЧИК РАСТЕНИЙ
    # =================================

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
            "0 / 45",
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
