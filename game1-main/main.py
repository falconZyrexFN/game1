
import pygame

from screens.menu import Menu
from screens.game import Game
from screens.settings import Settings

from systems import audio
from systems import config


# ==============================
# ИНИЦИАЛИЗАЦИЯ PYGAME
# ==============================

pygame.init()

try:
    pygame.mixer.init()
    SOUND_ENABLED = True

except pygame.error:
    print("Звуковое устройство недоступно")
    SOUND_ENABLED = False


# ==============================
# НАСТРОЙКИ ОКНА
# ==============================

WIDTH = 960
HEIGHT = 540

screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Little Root")

clock = pygame.time.Clock()
FPS = 60


# ==============================
# МУЗЫКА
# ==============================

MENU_MUSIC = "assets/audio/menu_music.mp3"
GAME_MUSIC = "assets/audio/game_music.mp3"


if SOUND_ENABLED:

    audio.initialize()

    # При запуске включается музыка меню
    audio.play_music(
        MENU_MUSIC,
        "menu"
    )


# ==============================
# ЗАГРУЗКА ШРИФТОВ
# ==============================

try:

    title_font = pygame.font.Font(
        "assets/fonts/game_font.ttf",
        24
    )

    ui_font = pygame.font.Font(
        "assets/fonts/game_font.ttf",
        10
    )

except (FileNotFoundError, pygame.error):

    title_font = pygame.font.Font(None, 36)
    ui_font = pygame.font.Font(None, 24)


fonts = {
    "title": title_font,
    "ui": ui_font
}


# ==============================
# СОЗДАНИЕ ЭКРАНОВ
# ==============================

menu = Menu(fonts)

settings = Settings(fonts)

game = None

current_screen = "menu"

running = True

save_timer = 0


# ==============================
# ГЛАВНЫЙ ИГРОВОЙ ЦИКЛ
# ==============================

while running:

    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():

        # ==========================
        # ЗАКРЫТИЕ ИГРЫ
        # ==========================

        if event.type == pygame.QUIT:

            if game:
                game.save_game()

            config.save_settings()

            running = False

        # ==========================
        # ГЛАВНОЕ МЕНЮ
        # ==========================

        elif current_screen == "menu":

            action = menu.handle_event(event)

            # НОВАЯ ИГРА
            if action == "new":

                if SOUND_ENABLED:

                    audio.stop_music()

                    audio.play_music(
                        GAME_MUSIC,
                        "game"
                    )

                game = Game(
                    fonts,
                    load_saved=False
                )

                game.save_game()

                save_timer = 0

                current_screen = "game"

            # ПРОДОЛЖИТЬ
            elif action == "continue":

                if SOUND_ENABLED:

                    audio.stop_music()

                    audio.play_music(
                        GAME_MUSIC,
                        "game"
                    )

                if game is None:

                    game = Game(
                        fonts,
                        load_saved=True
                    )

                current_screen = "game"

            # НАСТРОЙКИ
            elif action == "settings":

                current_screen = "settings"

            # ВЫХОД
            elif action == "quit":

                if game:
                    game.save_game()

                config.save_settings()

                running = False

        # ==========================
        # НАСТРОЙКИ
        # ==========================

        elif current_screen == "settings":

            action = settings.handle_event(event)

            if action == "back":

                current_screen = "menu"

        # ==========================
        # ИГРА
        # ==========================

        elif current_screen == "game":

            action = game.handle_event(event)

            # ВОЗВРАТ В МЕНЮ
            if action == "menu":

                game.save_game()

                current_screen = "menu"

                if SOUND_ENABLED:

                    audio.stop_music()

                    audio.play_music(
                        MENU_MUSIC,
                        "menu"
                    )

    # ==============================
    # ОБНОВЛЕНИЕ ИГРЫ
    # ==============================

    if current_screen == "game" and game:

        game.update(dt)

        # Автосохранение каждые 5 секунд
        save_timer += dt

        if save_timer >= 5:

            game.save_game()

            save_timer = 0

    # ==============================
    # ОТРИСОВКА
    # ==============================

    if current_screen == "menu":

        menu.draw(screen)

    elif current_screen == "settings":

        settings.draw(screen)

    elif current_screen == "game" and game:

        game.draw(screen)

    pygame.display.flip()


# ==============================
# ЗАВЕРШЕНИЕ И СОХРАНЕНИЕ
# ==============================

if game:

    game.save_game()

config.save_settings()

if SOUND_ENABLED:

    audio.stop_music()

pygame.quit()
