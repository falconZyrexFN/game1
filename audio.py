import math
from array import array

import pygame

from systems import config


hover_sound = None
click_sound = None

# Какая музыка сейчас играет: menu или game
active_music_type = "menu"


def create_tone(start_frequency, end_frequency, duration, volume):

    if not pygame.mixer.get_init():
        return None

    sample_rate = pygame.mixer.get_init()[0]
    samples = array("h")

    count = int(sample_rate * duration)

    for i in range(count):

        progress = i / count

        frequency = (
            start_frequency
            + (end_frequency - start_frequency) * progress
        )

        envelope = min(1, i / 150) * (1 - progress) ** 1.5

        value = math.sin(
            2 * math.pi * frequency * i / sample_rate
        )

        value *= envelope * volume * 32767

        samples.append(int(value))

    try:
        return pygame.mixer.Sound(buffer=samples.tobytes())

    except pygame.error:
        return None


def initialize():

    global hover_sound, click_sound

    if not pygame.mixer.get_init():
        return

    hover_sound = create_tone(850, 650, 0.055, 0.22)
    click_sound = create_tone(550, 750, 0.075, 0.35)


def get_music_volume(music_type):

    if music_type == "menu":
        return config.MENU_MUSIC_VOLUME

    return config.GAME_MUSIC_VOLUME


def set_music_volume():

    if not pygame.mixer.get_init():
        return

    volume = get_music_volume(active_music_type)

    pygame.mixer.music.set_volume(volume)


def set_sfx_volume():
    pass


def play_music(path, music_type="menu"):

    global active_music_type

    if not pygame.mixer.get_init():
        return

    try:
        active_music_type = music_type

        pygame.mixer.music.load(path)

        set_music_volume()

        pygame.mixer.music.play(-1)

        print(f"Музыка запущена: {music_type}")

    except pygame.error as error:

        print("Не удалось загрузить музыку:", error)


def stop_music():

    if pygame.mixer.get_init():
        pygame.mixer.music.stop()


def play_ui(sound_name):

    if not pygame.mixer.get_init():
        return

    if sound_name == "hover" and hover_sound:

        hover_sound.set_volume(config.SFX_VOLUME)
        hover_sound.play()

    elif sound_name == "click" and click_sound:

        click_sound.set_volume(config.SFX_VOLUME)
        click_sound.play()