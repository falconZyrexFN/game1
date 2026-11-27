import json

import pygame

from systems import plants as P
from systems.state import GameState
from systems.ui import UI, CREAM


def load_state_from_save():
    # Состояние из файла сохранения для просмотра коллекции в меню.
    # Без сохранения показываем пустую книгу.

    state = GameState()

    state.inventory = {}
    state.discovered = set()
    state.grown = set()
    state.selected_plant = None

    try:

        with open(P.SAVE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        state.load_dict(data.get("state"))

    except (OSError, ValueError, AttributeError):
        pass

    return state


class CollectionScreen:
    # Книга коллекционера в главном меню (только просмотр)

    def __init__(self, fonts):

        self.ui = UI(fonts, None)
        self.state = None
        self.back_rect = pygame.Rect(40, 494, 100, 22)

    def open(self, state):

        self.state = state
        self.ui.book_sel = 0

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_ESCAPE, pygame.K_b,
                             pygame.K_BACKSPACE):
                return "back"

        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.back_rect.collidepoint(event.pos)):
            return "back"

        self.ui.book_event(event, None)

        return None

    def draw(self, screen, background=None):

        if background is not None:
            screen.blit(background, (0, 0))
        else:
            screen.fill((100, 130, 100))

        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        screen.blit(dim, (0, 0))

        self.ui.rects = []
        self.ui.draw_book(screen, self.state)

        self.ui.panel(screen, self.back_rect, 235)
        self.ui.text(screen, "< НАЗАД", self.ui.f10, CREAM,
                     self.back_rect.center, anchor="center")
