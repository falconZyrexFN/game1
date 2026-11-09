import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SETTINGS_PATH = os.path.join(
    BASE_DIR, "settings.json"
)


# Громкость отдельных звуков
MENU_MUSIC_VOLUME = 0.35
GAME_MUSIC_VOLUME = 0.35
SFX_VOLUME = 0.85


def load_settings():

    global MENU_MUSIC_VOLUME
    global GAME_MUSIC_VOLUME
    global SFX_VOLUME

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Поддержка старой настройки music_volume
        old_volume = data.get("music_volume", 0.35)

        MENU_MUSIC_VOLUME = max(
            0,
            min(1, float(data.get("menu_music_volume", old_volume)))
        )

        GAME_MUSIC_VOLUME = max(
            0,
            min(1, float(data.get("game_music_volume", old_volume)))
        )

        SFX_VOLUME = max(
            0,
            min(1, float(data.get("sfx_volume", 0.85)))
        )

    except (
        FileNotFoundError,
        ValueError,
        TypeError,
        json.JSONDecodeError
    ):
        save_settings()


def save_settings():

    data = {
        "menu_music_volume": MENU_MUSIC_VOLUME,
        "game_music_volume": GAME_MUSIC_VOLUME,
        "sfx_volume": SFX_VOLUME
    }

    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except OSError as error:
        print("Не удалось сохранить настройки:", error)


load_settings()