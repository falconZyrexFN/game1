
import pygame
import json
import os

from systems.player import Player
from systems.world import World


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SAVE_PATH = os.path.join(BASE_DIR, "save.json")


class Game:

    def __init__(self, fonts, load_saved=True):

        self.ui_font = fonts["ui"]

        # Создаём персонажа
        self.player = Player()

        # Создаём лесную карту
        self.world = World()

        if load_saved:
            self.load_game()

    def save_game(self):

        data = {
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "direction": self.player.direction
            }
        }

        try:

            with open(SAVE_PATH, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

        except OSError as error:

            print("Ошибка сохранения:", error)

    def load_game(self):

        if not os.path.exists(SAVE_PATH):

            print("Сохранение не найдено. Начинаем новую игру.")
            return

        try:

            with open(SAVE_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)

            player_data = data["player"]

            x = float(player_data["x"])
            y = float(player_data["y"])

            if not (0 <= x <= 960 and 0 <= y <= 540):
                raise ValueError("Некорректная позиция персонажа")

            direction = player_data.get("direction", "down")

            if direction not in ("down", "up", "left", "right"):
                direction = "down"

            self.player.x = max(32, min(928, x))
            self.player.y = max(32, min(508, y))

            self.player.direction = direction
            self.player.current_frame = 0

            self.player.image = self.player.frames[direction][0]

            self.player.rect = self.player.image.get_rect(
                center=(
                    int(self.player.x),
                    int(self.player.y)
                )
            )

            print("Сохранение успешно загружено!")

        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError
        ) as error:

            print("Не удалось загрузить сохранение:", error)

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                self.save_game()

                if self.player.footstep_channel:
                    self.player.footstep_channel.stop()

                return "menu"

        return None

    def update(self, dt):

        self.player.update(dt)

    def draw(self, screen):

        # Сначала рисуем лес
        self.world.draw(screen)

        # Затем персонажа
        self.player.draw(screen)

        # Название игры
        title = self.ui_font.render(
            "LITTLE ROOT",
            True,
            (255, 255, 255)
        )

        screen.blit(title, (20, 20))

        # Управление
        controls = self.ui_font.render(
            "WASD - MOVE | ESC - MENU",
            True,
            (255, 255, 255)
        )

        screen.blit(controls, (20, 45))
