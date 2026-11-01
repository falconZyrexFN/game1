import os
import sys
import pygame

# ---------- Настройки ----------
WIDTH, HEIGHT = 960, 540
FPS = 60

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_SHEET = os.path.join(BASE_DIR, "assets", "player.png")

# Параметры спрайт-листа персонажа (поменяйте под свой ассет)
FRAME_W, FRAME_H = 64, 64   # размер одного кадра в пикселях
SCALE = 1                   # во сколько раз увеличить спрайт
# Порядок рядов в спрайт-листе: какой ряд за какое направление отвечает
ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}

PLAYER_SPEED = 200          # пикселей в секунду
ANIM_FPS = 8                # скорость анимации ходьбы


def make_placeholder_frames():
    """Запасной вариант, если файла player.png нет: цветные квадраты."""
    size = (FRAME_W * SCALE, FRAME_H * SCALE)
    frames = {}
    for direction in ROWS:
        frames[direction] = []
        for i in range(4):
            surf = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surf, (70, 160, 90), surf.get_rect(), border_radius=8)
            # "глаза" показывают направление
            w, h = size
            offset = {"down": (0, 8), "up": (0, -8), "left": (-8, 0), "right": (8, 0)}[direction]
            for ex in (-8, 8):
                if direction in ("left", "right"):
                    ex = ex // 2
                pygame.draw.circle(surf, (255, 255, 255),
                                   (w // 2 + ex + offset[0], h // 2 + offset[1]), 4)
            # "шаг": небольшая полоска снизу, меняется по кадрам
            pygame.draw.rect(surf, (40, 100, 60), (4 + i * 6, h - 6, 10, 4))
            frames[direction].append(surf)
    return frames


def load_player_frames():
    """Нарезает спрайт-лист на кадры по направлениям."""
    if not os.path.exists(PLAYER_SHEET):
        print(f"[!] Не найден {PLAYER_SHEET} — использую заглушку.")
        return make_placeholder_frames()

    sheet = pygame.image.load(PLAYER_SHEET).convert_alpha()
    cols = sheet.get_width() // FRAME_W
    frames = {}
    for direction, row in ROWS.items():
        frames[direction] = []
        for col in range(cols):
            rect = pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H)
            frame = sheet.subsurface(rect)
            frame = pygame.transform.scale(frame, (FRAME_W * SCALE, FRAME_H * SCALE))
            frames[direction].append(frame)
    return frames


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.frames = load_player_frames()
        self.direction = "down"
        self.frame_index = 0.0
        self.image = self.frames[self.direction][0]
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(self.rect.center)  # точная позиция (float)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        if move.length_squared() > 0:
            move = move.normalize()  # чтобы по диагонали не бегать быстрее
        return move

    def update(self, dt):
        move = self.handle_input()

        if move.x != 0 or move.y != 0:
            # направление взгляда (горизонталь в приоритете при диагонали)
            if abs(move.x) >= abs(move.y):
                self.direction = "right" if move.x > 0 else "left"
            else:
                self.direction = "down" if move.y > 0 else "up"

            self.pos += move * PLAYER_SPEED * dt
            self.frame_index += ANIM_FPS * dt
        else:
            self.frame_index = 0  # стоим — первый кадр

        # границы экрана
        half_w, half_h = self.rect.width / 2, self.rect.height / 2
        self.pos.x = max(half_w, min(WIDTH - half_w, self.pos.x))
        self.pos.y = max(half_h, min(HEIGHT - half_h, self.pos.y))

        frames = self.frames[self.direction]
        self.image = frames[int(self.frame_index) % len(frames)]
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Little Root")
    clock = pygame.time.Clock()

    player = Player((WIDTH // 2, HEIGHT // 2))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000  # время кадра в секундах

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        player.update(dt)

        screen.fill((96, 150, 80))  # временный фон-трава
        screen.blit(player.image, player.rect)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()