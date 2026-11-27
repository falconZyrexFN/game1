import pygame

from systems import config
from systems import audio


class Settings:

    def __init__(self, fonts):

        self.title_font = fonts["title"]
        self.ui_font = fonts["ui"]

        self.menu_music_bar = pygame.Rect(300, 220, 360, 10)
        self.game_music_bar = pygame.Rect(300, 310, 360, 10)
        self.sfx_bar = pygame.Rect(300, 400, 360, 10)

        self.back_rect = pygame.Rect(330, 465, 300, 50)

        self.dragging = None
        self.was_back_hovered = False

    def change_volume(self, bar, mouse_x):

        value = (mouse_x - bar.x) / bar.width
        value = max(0, min(1, value))

        if bar == self.menu_music_bar:

            config.MENU_MUSIC_VOLUME = value

            if audio.active_music_type == "menu":
                audio.set_music_volume()

        elif bar == self.game_music_bar:

            config.GAME_MUSIC_VOLUME = value

            if audio.active_music_type == "game":
                audio.set_music_volume()

        elif bar == self.sfx_bar:

            config.SFX_VOLUME = value

        return value

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                config.save_settings()
                audio.play_ui("click")

                return "back"

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.menu_music_bar.inflate(20, 30).collidepoint(event.pos):

                    self.dragging = "menu_music"

                    self.change_volume(
                        self.menu_music_bar,
                        event.pos[0]
                    )

                    audio.play_ui("click")

                elif self.game_music_bar.inflate(20, 30).collidepoint(event.pos):

                    self.dragging = "game_music"

                    self.change_volume(
                        self.game_music_bar,
                        event.pos[0]
                    )

                    audio.play_ui("click")

                elif self.sfx_bar.inflate(20, 30).collidepoint(event.pos):

                    self.dragging = "sfx"

                    self.change_volume(
                        self.sfx_bar,
                        event.pos[0]
                    )

                    audio.play_ui("click")

                elif self.back_rect.collidepoint(event.pos):

                    config.save_settings()
                    audio.play_ui("click")

                    return "back"

        if event.type == pygame.MOUSEMOTION:

            if self.dragging == "menu_music":

                self.change_volume(
                    self.menu_music_bar,
                    event.pos[0]
                )

            elif self.dragging == "game_music":

                self.change_volume(
                    self.game_music_bar,
                    event.pos[0]
                )

            elif self.dragging == "sfx":

                self.change_volume(
                    self.sfx_bar,
                    event.pos[0]
                )

            back_hovered = self.back_rect.collidepoint(event.pos)

            if back_hovered and not self.was_back_hovered:
                audio.play_ui("hover")

            self.was_back_hovered = back_hovered

        if event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1 and self.dragging:

                self.dragging = None
                config.save_settings()

        return None

    def draw_slider(self, screen, bar, volume, label):

        text = self.ui_font.render(
            f"{label}: {int(volume * 100)}%",
            True,
            (255, 245, 215)
        )

        screen.blit(
            text,
            text.get_rect(center=(480, bar.y - 28))
        )

        pygame.draw.rect(
            screen,
            (65, 75, 60),
            bar,
            border_radius=8
        )

        filled = pygame.Rect(
            bar.x,
            bar.y,
            int(bar.width * volume),
            bar.height
        )

        pygame.draw.rect(
            screen,
            (125, 175, 100),
            filled,
            border_radius=8
        )

        knob_x = bar.x + int(bar.width * volume)

        pygame.draw.circle(
            screen,
            (255, 235, 180),
            (knob_x, bar.centery),
            11
        )

        pygame.draw.circle(
            screen,
            (65, 95, 65),
            (knob_x, bar.centery),
            11,
            2
        )

    def draw(self, screen):

        screen.fill((45, 85, 60))

        title = self.title_font.render(
            "SETTINGS",
            True,
            (255, 240, 190)
        )

        screen.blit(
            title,
            title.get_rect(center=(480, 100))
        )

        self.draw_slider(
            screen,
            self.menu_music_bar,
            config.MENU_MUSIC_VOLUME,
            "MENU MUSIC"
        )

        self.draw_slider(
            screen,
            self.game_music_bar,
            config.GAME_MUSIC_VOLUME,
            "GAME MUSIC"
        )

        self.draw_slider(
            screen,
            self.sfx_bar,
            config.SFX_VOLUME,
            "SOUND EFFECTS"
        )

        mouse_pos = pygame.mouse.get_pos()

        hovered = self.back_rect.collidepoint(mouse_pos)

        color = (125, 155, 90) if hovered else (105, 135, 75)

        pygame.draw.rect(
            screen,
            color,
            self.back_rect,
            border_radius=8
        )

        label = self.ui_font.render(
            "BACK",
            True,
            (255, 255, 230)
        )

        screen.blit(
            label,
            label.get_rect(center=self.back_rect.center)
        )