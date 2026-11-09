
import pygame
import os
import math

from systems import config


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PLAYER_PATH = os.path.join(
    BASE_DIR, "assets", "player.png"
)

FOOTSTEP_PATH = os.path.join(
    BASE_DIR, "assets", "audio", "footsteps.wav"
)

STEP_INTERVAL = 0.38


class Player:

    def __init__(self):

        self.x = 480
        self.y = 270
        self.speed = 200

        self.frame_width = 64
        self.frame_height = 64

        self.direction = "down"
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 8

        self.step_timer = 0

        self.frames = {
            "down": [],
            "left": [],
            "right": [],
            "up": []
        }

        self.load_sprites()

        self.image = self.frames["down"][0]
        self.rect = self.image.get_rect(
            center=(self.x, self.y)
        )

        self.footstep_sound = None
        self.footstep_channel = None

        if pygame.mixer.get_init():

            self.footstep_channel = pygame.mixer.Channel(1)

            try:
                self.footstep_sound = pygame.mixer.Sound(
                    FOOTSTEP_PATH
                )

                self.footstep_sound.set_volume(
                    config.SFX_VOLUME
                )

            except (FileNotFoundError, pygame.error):
                print("Не удалось загрузить звук шагов!")

    def load_sprites(self):

        try:
            sheet = pygame.image.load(
                PLAYER_PATH
            ).convert_alpha()

            rows = {
                "down": 0,
                "left": 1,
                "right": 2,
                "up": 3
            }

            columns = sheet.get_width() // 64
            total_rows = sheet.get_height() // 64

            for direction, row in rows.items():

                if row >= total_rows:
                    row = 0

                for column in range(columns):

                    frame = pygame.Surface(
                        (64, 64),
                        pygame.SRCALPHA
                    )

                    frame.blit(
                        sheet,
                        (0, 0),
                        (
                            column * 64,
                            row * 64,
                            64,
                            64
                        )
                    )

                    self.frames[direction].append(frame)

            for direction in self.frames:

                if not self.frames[direction]:
                    self.frames[direction] = [
                        self.make_placeholder()
                    ]

        except (FileNotFoundError, pygame.error):

            print("Не удалось загрузить спрайт персонажа!")

            for direction in self.frames:
                self.frames[direction] = [
                    self.make_placeholder()
                ]

    def make_placeholder(self):

        image = pygame.Surface(
            (64, 64),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            image,
            (180, 100, 60),
            (12, 8, 40, 52)
        )

        return image

    def update(self, dt):

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_a]:
            dx -= 1

        if keys[pygame.K_d]:
            dx += 1

        if keys[pygame.K_w]:
            dy -= 1

        if keys[pygame.K_s]:
            dy += 1

        moving = dx != 0 or dy != 0

        if moving:

            length = math.sqrt(dx * dx + dy * dy)

            dx /= length
            dy /= length

            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

            self.animation_timer += dt

            if self.animation_timer >= 1 / self.animation_speed:

                self.animation_timer = 0
                self.current_frame += 1

                if self.current_frame >= len(
                    self.frames[self.direction]
                ):
                    self.current_frame = 0

            self.step_timer -= dt

            if self.step_timer <= 0:

                if self.footstep_sound and self.footstep_channel:

                    self.footstep_sound.set_volume(
                        config.SFX_VOLUME
                    )

                    self.footstep_channel.play(
                        self.footstep_sound
                    )

                self.step_timer = STEP_INTERVAL

        else:

            if self.footstep_channel:
                self.footstep_channel.stop()

            self.step_timer = 0
            self.animation_timer = 0
            self.current_frame = 0

        self.x = max(32, min(928, self.x))
        self.y = max(32, min(508, self.y))

        self.image = self.frames[self.direction][
            self.current_frame
        ]

        self.rect = self.image.get_rect(
            center=(int(self.x), int(self.y))
        )

    def draw(self, screen):

        screen.blit(self.image, self.rect)
