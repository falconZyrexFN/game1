
import pygame
import random


class World:

    def __init__(self):

        self.width = 960
        self.height = 540

        # Генератор случайных деталей.
        # Одинаковое число означает одинаковую карту
        # при каждом запуске игры.
        random.seed(15)

        self.grass_details = []
        self.flowers = []
        self.trees = []
        self.rocks = []
        self.bushes = []

        self.create_world()

    def create_world(self):

        # Маленькие детали на траве
        for _ in range(180):

            x = random.randint(10, self.width - 10)
            y = random.randint(10, self.height - 10)

            self.grass_details.append((x, y))

        # Цветы
        for _ in range(35):

            x = random.randint(25, self.width - 25)
            y = random.randint(25, self.height - 25)

            color = random.choice([
                (245, 220, 120),
                (245, 170, 190),
                (220, 200, 245),
                (255, 245, 220)
            ])

            self.flowers.append((x, y, color))

        # Деревья.
        # Оставляем свободное место в центре для игрока.
        self.trees = [
            (90, 100, 1.0),
            (230, 75, 0.9),
            (410, 85, 1.0),
            (700, 85, 1.0),
            (870, 120, 1.1),

            (75, 300, 1.0),
            (250, 430, 1.0),
            (440, 450, 0.9),
            (690, 420, 1.0),
            (875, 340, 1.0),

            (150, 500, 0.8),
            (790, 500, 0.9)
        ]

        # Камни
        self.rocks = [
            (155, 185, 1.0),
            (350, 155, 0.8),
            (800, 205, 1.0),
            (570, 460, 0.9),
            (45, 420, 0.8)
        ]

        # Кусты
        self.bushes = [
            (320, 80),
            (610, 110),
            (915, 250),
            (180, 350),
            (600, 320),
            (420, 250),
            (760, 300)
        ]

    def draw_path(self, screen):

        # Извилистая дорожка.
        # Сначала рисуем тёмную границу,
        # затем основную поверхность.

        points = [
            (-30, 280),
            (120, 270),
            (250, 300),
            (390, 280),
            (520, 245),
            (660, 260),
            (800, 290),
            (990, 270)
        ]

        pygame.draw.lines(
            screen,
            (130, 105, 70),
            False,
            points,
            76
        )

        pygame.draw.lines(
            screen,
            (190, 160, 112),
            False,
            points,
            66
        )

        # Мягкие края дорожки
        for x, y in points:

            pygame.draw.circle(
                screen,
                (190, 160, 112),
                (x, y),
                33
            )

        # Маленькие камешки на дорожке
        random.seed(25)

        for _ in range(45):

            x = random.randint(0, self.width)
            y = random.randint(235, 310)

            pygame.draw.ellipse(
                screen,
                (170, 140, 100),
                (x, y, 5, 3)
            )

    def draw_tree(self, screen, x, y, scale):

        # Тень дерева
        pygame.draw.ellipse(
            screen,
            (55, 105, 60),
            (
                int(x - 35 * scale),
                int(y + 15 * scale),
                int(75 * scale),
                int(25 * scale)
            )
        )

        # Ствол
        pygame.draw.rect(
            screen,
            (110, 75, 45),
            (
                int(x - 9 * scale),
                int(y - 8 * scale),
                int(19 * scale),
                int(43 * scale)
            ),
            border_radius=max(1, int(5 * scale))
        )

        # Нижняя тёмная часть кроны
        pygame.draw.circle(
            screen,
            (35, 105, 55),
            (int(x), int(y - 25 * scale)),
            int(39 * scale)
        )

        # Основная крона
        pygame.draw.circle(
            screen,
            (55, 140, 65),
            (int(x - 12 * scale), int(y - 38 * scale)),
            int(30 * scale)
        )

        pygame.draw.circle(
            screen,
            (70, 155, 75),
            (int(x + 13 * scale), int(y - 35 * scale)),
            int(27 * scale)
        )

        pygame.draw.circle(
            screen,
            (85, 170, 80),
            (int(x), int(y - 52 * scale)),
            int(25 * scale)
        )

        # Светлые пятна на листьях
        pygame.draw.circle(
            screen,
            (115, 190, 95),
            (int(x - 12 * scale), int(y - 48 * scale)),
            max(2, int(8 * scale))
        )

        pygame.draw.circle(
            screen,
            (105, 180, 85),
            (int(x + 15 * scale), int(y - 30 * scale)),
            max(2, int(7 * scale))
        )

    def draw_rock(self, screen, x, y, scale):

        pygame.draw.ellipse(
            screen,
            (65, 105, 65),
            (
                int(x - 20 * scale),
                int(y + 7 * scale),
                int(45 * scale),
                int(13 * scale)
            )
        )

        pygame.draw.ellipse(
            screen,
            (105, 115, 105),
            (
                int(x - 19 * scale),
                int(y - 12 * scale),
                int(40 * scale),
                int(27 * scale)
            )
        )

        pygame.draw.ellipse(
            screen,
            (155, 160, 145),
            (
                int(x - 12 * scale),
                int(y - 10 * scale),
                int(22 * scale),
                int(9 * scale)
            )
        )

    def draw_bush(self, screen, x, y):

        pygame.draw.circle(
            screen,
            (35, 105, 50),
            (x, y),
            19
        )

        pygame.draw.circle(
            screen,
            (55, 135, 60),
            (x - 12, y - 5),
            14
        )

        pygame.draw.circle(
            screen,
            (75, 155, 70),
            (x + 10, y - 7),
            13
        )

        pygame.draw.circle(
            screen,
            (95, 175, 80),
            (x, y - 12),
            10
        )

    def draw(self, screen):

        # Основной цвет травы
        screen.fill((105, 165, 85))

        # Небольшие цветовые пятна на земле
        for x, y in self.grass_details:

            pygame.draw.circle(
                screen,
                (115, 175, 92),
                (x, y),
                2
            )

        # Дорожка
        self.draw_path(screen)

        # Цветы
        for x, y, color in self.flowers:

            pygame.draw.circle(
                screen,
                (65, 125, 65),
                (x, y + 3),
                3
            )

            pygame.draw.circle(
                screen,
                color,
                (x, y),
                3
            )

            pygame.draw.circle(
                screen,
                (245, 220, 100),
                (x, y),
                1
            )

        # Камни
        for x, y, scale in self.rocks:
            self.draw_rock(screen, x, y, scale)

        # Кусты
        for x, y in self.bushes:
            self.draw_bush(screen, x, y)

        # Деревья
        for x, y, scale in self.trees:
            self.draw_tree(screen, x, y, scale)
