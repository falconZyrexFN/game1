# Рисование моделей растений в коде.
# Все функции рисуют через "перо" (pen) с методами circle, ellipse, poly, line,
# поэтому один и тот же код работает и в игре (pygame), и в превью.
# Холст 48x48, земля на уровне y=45. Угол 0 = вверх, 90 = вправо.

import math

GRN = (72, 158, 84)
GRN_D = (46, 118, 64)
BROWN = (98, 66, 38)
CREAM = (238, 228, 205)


def rgb(text):
    text = text.lstrip("#")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def mix(c, target, f):
    return tuple(int(c[k] + (target[k] - c[k]) * f) for k in range(3))


def lt(c, f=0.35):
    return mix(c, (255, 255, 255), f)


def dk(c, f=0.35):
    return mix(c, (0, 0, 0), f)


# ==============================
# ОСНОВНЫЕ ФОРМЫ
# ==============================

def _dir(ang):
    a = math.radians(ang)
    return math.sin(a), -math.cos(a)


def leaf(p, x, y, ang, length, width, col):
    # Заострённый лист с жилкой и тенью на нижней половине
    ux, uy = _dir(ang)
    vx, vy = -uy, ux
    prof = [(0.0, 0), (0.18, 0.55), (0.4, 0.95), (0.62, 0.85),
            (0.82, 0.5), (1.0, 0)]

    left = [(x + ux * length * t + vx * width / 2 * w,
             y + uy * length * t + vy * width / 2 * w) for t, w in prof]
    right = [(x + ux * length * t - vx * width / 2 * w,
              y + uy * length * t - vy * width / 2 * w) for t, w in prof]

    p.poly(col, left + right[::-1][1:])
    p.poly(dk(col, 0.22), [(x, y)] + right[1:])
    p.line(lt(col, 0.4), (x + ux * length * 0.1, y + uy * length * 0.1),
           (x + ux * length * 0.82, y + uy * length * 0.82), 1)


def petal(p, x, y, ang, length, width, col):
    # Округлый лепесток, основание в точке (x, y)
    ux, uy = _dir(ang)
    vx, vy = -uy, ux

    def ring(scale_l, scale_w, start, color):
        pts = []

        for k in range(0, 360, 24):
            t = math.radians(k)
            along = start + length * scale_l / 2 * (1 - math.cos(t))
            across = width * scale_w / 2 * math.sin(t)
            pts.append((x + ux * along + vx * across,
                        y + uy * along + vy * across))

        p.poly(color, pts)

    ring(1.0, 1.0, 0, col)
    ring(0.6, 0.45, length * 0.14, lt(col, 0.32))


def blob(p, cx, cy, rx, ry, col):
    # Шарик с тремя тонами и бликом
    p.ellipse(dk(col, 0.3), cx, cy, rx, ry)
    p.ellipse(col, cx - rx * 0.1, cy - ry * 0.12, rx * 0.88, ry * 0.88)
    p.ellipse(lt(col, 0.4), cx - rx * 0.32, cy - ry * 0.4, rx * 0.36, ry * 0.28)
    p.circle((255, 255, 255), (cx - rx * 0.4, cy - ry * 0.48),
             max(1, round(min(rx, ry) * 0.13)))


def stem(p, pts, width, col):
    for a, b in zip(pts, pts[1:]):
        p.line(dk(col, 0.25), a, b, width + 1)

    for a, b in zip(pts, pts[1:]):
        p.line(col, a, b, width)

    for a, b in zip(pts, pts[1:]):
        p.line(lt(col, 0.35), (a[0] - 1, a[1]), (b[0] - 1, b[1]), 1)


def path_point(pts, t):
    # Точка на ломаной и угол касательной
    segs = list(zip(pts, pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    d = t * sum(lens)

    for index, ((a, b), length) in enumerate(zip(segs, lens)):

        if d <= length or index == len(segs) - 1:
            f = d / length if length else 0

            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f,
                    math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]))))

        d -= length


def dome(cx, cy, rx, ry):
    return [(cx + rx * math.cos(math.radians(a)),
             cy + ry * math.sin(math.radians(a))) for a in range(180, 361, 12)]


def grass(p):
    leaf(p, 15, 46, -38, 9, 3.5, GRN_D)
    leaf(p, 33, 46, 38, 9, 3.5, GRN_D)
    leaf(p, 24, 46, -6, 7, 3, GRN)


def prism(p, x, base, h, w, col):
    # Грань кристалла: светлая слева, тёмная справа, блик
    left, right = x - w / 2, x + w / 2
    top = base - h * 0.72
    tip = (x, base - h)

    p.poly(dk(col, 0.28), [(left, base), (right, base), (right, top), tip,
                           (left, top)])
    p.poly(col, [(left, base), (x, base), tip, (left, top)])
    p.poly(lt(col, 0.5), [(left, top), tip, (x, base - h * 0.5)])
    p.line((255, 255, 255), (x - w / 4, base - 2), (x - w / 4, base - h * 0.55), 1)


def ear(p, x, y, ang, length, col, awn):
    # Колос: пары зёрен вдоль стебля и усики
    for k in range(7):
        t = k / 7
        gx, gy = x + _dir(ang)[0] * length * t, y + _dir(ang)[1] * length * t

        petal(p, gx, gy, ang - 32, 7, 3.6, dk(col, 0.12))
        petal(p, gx, gy, ang + 32, 7, 3.6, col)

    tx, ty = x + _dir(ang)[0] * length, y + _dir(ang)[1] * length

    petal(p, tx, ty, ang, 6, 3.4, lt(col, 0.1))

    for off in (-8, 0, 8):
        ex, ey = _dir(ang + off)
        p.line(awn, (tx, ty), (tx + ex * 8, ty + ey * 8), 1)


def bell(p, x, y, col, rim, s=1.0):
    # Колокольчик, подвешенный к стеблю в точке (x, y)
    cy = y + 8 * s

    def pt(dx, dy):
        return (x + dx * s, cy + dy * s)

    p.poly(dk(col, 0.3), [pt(-8, 6), pt(-6, -3), pt(-2, -8), pt(3, -8),
                          pt(7, -3), pt(9, 6), pt(11, 11), pt(-10, 11)])
    p.poly(col, [pt(-7, 6), pt(-5, -3), pt(-2, -7), pt(2, -7), pt(2, 11),
                 pt(-9, 11)])
    p.ellipse(lt(col, 0.5), x - 3.5 * s, cy - 2 * s, 1.6 * s, 3.5 * s)
    p.ellipse(rim, x + 0.5 * s, cy + 11 * s, 10 * s, 2.2 * s)
    p.circle(dk(rim, 0.3), (x, cy + 12.5 * s), max(1, 2 * s))


def heart(p, cx, cy, ang, r, col):
    # Лист клевера: два шарика и остриё к центру
    ux, uy = _dir(ang)
    vx, vy = -uy, ux
    a = (cx + ux * r * 1.4 + vx * r * 0.7, cy + uy * r * 1.4 + vy * r * 0.7)
    b = (cx + ux * r * 1.4 - vx * r * 0.7, cy + uy * r * 1.4 - vy * r * 0.7)

    p.circle(dk(col, 0.22), (a[0] + 1, a[1] + 1), r)
    p.circle(dk(col, 0.22), (b[0] + 1, b[1] + 1), r)
    p.circle(col, a, r)
    p.circle(col, b, r)
    p.poly(col, [(cx, cy), a, b])
    p.line(lt(col, 0.5), (cx + ux * r * 0.4, cy + uy * r * 0.4),
           (cx + ux * r * 1.8, cy + uy * r * 1.8), 1)


# ==============================
# ВИДЫ РАСТЕНИЙ
# Каждая функция: (перо, id, цвет 1, цвет 2, номер растения)
# ==============================

def s_daisy(p, pid, c1, c2, i):
    n = 8 + i % 4
    cx, cy = 24, 16

    grass(p)
    stem(p, [(24, 45), (23, 34), (24, 22)], 3, GRN)
    leaf(p, 24, 41, -62, 14, 6, GRN)
    leaf(p, 24, 35, 62, 12, 5, GRN_D)

    for k in range(n):
        petal(p, cx, cy, k * 360 / n + 180 / n, 13, 6, dk(c1, 0.22))

    for k in range(n):
        petal(p, cx, cy, k * 360 / n, 12, 6, c1)

    blob(p, cx, cy, 5.5, 5.5, c2)

    for k in range(7):
        a = k * 2.4
        r = 0.8 + k * 0.45
        p.circle(dk(c2, 0.45), (cx + math.cos(a) * r, cy + math.sin(a) * r), 0.6)


def s_bell(p, pid, c1, c2, i):
    count = 1 + i % 2

    grass(p)
    stem(p, [(21, 45), (21, 34), (25, 22), (32, 9)], 3, GRN)
    stem(p, [(23, 28), (17, 21)], 2, GRN)
    leaf(p, 21, 43, -58, 15, 6, GRN)
    leaf(p, 21, 39, 56, 13, 5, GRN_D)

    spots = [(32, 9, 1.0), (17, 21, 0.8)]

    for x, y, s in spots[:count][::-1]:
        bell(p, x, y, c1, c2, s)


def s_tulip(p, pid, c1, c2, i):
    grass(p)
    stem(p, [(24, 45), (24, 28)], 3, GRN)
    leaf(p, 24, 44, -28, 26, 8, GRN)
    leaf(p, 24, 44, 30, 23, 7, GRN_D)

    petal(p, 24, 32, -24, 19, 11, dk(c1, 0.22))
    petal(p, 24, 32, 24, 19, 11, dk(c1, 0.22))
    petal(p, 24, 32, -9, 21, 11, c1)
    petal(p, 24, 32, 9, 21, 11, lt(c1, 0.08))

    p.ellipse(c2, 24, 18, 2.2, 6)
    p.ellipse(lt(c1, 0.5), 19.5, 20, 1.4, 5)


def s_mushroom(p, pid, c1, c2, i):
    grass(p)

    p.poly(dk(CREAM, 0.12), [(18, 45), (21, 27), (27, 27), (30, 45)])
    p.poly(CREAM, [(18, 45), (21, 27), (25, 27), (24, 45)])
    p.ellipse(dk(CREAM, 0.1), 24, 44, 8, 2.5)

    p.ellipse(dk(CREAM, 0.3), 24, 28.5, 17, 3)
    p.poly(dk(c1, 0.3), dome(24, 28, 19, 16))
    p.poly(c1, dome(23, 28, 17, 14))
    p.ellipse(lt(c1, 0.45), 16, 19, 5.5, 2.4)
    p.line(dk(c1, 0.45), (6, 28), (42, 28), 2)

    spots = [(14, 23, 3), (24, 15, 3.4), (32, 21, 2.8), (21, 23, 2),
             (29, 26, 2), (36, 25, 1.6)]

    for x, y, r in spots[:4 + i % 3]:
        p.circle(c2, (x, y), r)
        p.circle(lt(c2, 0.6), (x - 1, y - 1), max(1, r * 0.4))


def s_fern(p, pid, c1, c2, i):
    grass(p)

    curve = [(24, 45), (23, 34), (24, 22), (27, 12), (32, 6)]
    stem(p, curve, 2, dk(GRN, 0.1))

    for k in range(1, 10):
        t = k / 10
        x, y, ang = path_point(curve, 0.1 + t * 0.85)
        size = 15 * (1 - t * 0.72)
        col = c1 if k % 2 else mix(c1, c2, 0.6)

        leaf(p, x, y, ang - 68, size, size * 0.42, col)
        leaf(p, x, y, ang + 68, size, size * 0.42, lt(col, 0.08))

    x, y, ang = path_point(curve, 1.0)
    leaf(p, x, y, ang, 7, 3, c1)


def s_berry(p, pid, c1, c2, i):
    holly = pid == "holly"
    leaf_col = (34, 104, 62) if holly else GRN

    grass(p)
    stem(p, [(24, 45), (24, 33), (18, 22)], 2, BROWN)
    stem(p, [(24, 36), (31, 27)], 2, BROWN)

    for x, y, a, size in [(22, 38, -72, 13), (26, 36, 72, 13),
                          (19, 27, -52, 12), (25, 28, 38, 12),
                          (31, 23, 66, 11), (17, 19, -24, 10)]:
        leaf(p, x, y, a, size, 7 if holly else 6, leaf_col)

    spots = [(14, 29), (30, 29), (22, 36), (19, 20), (33, 20), (25, 26)]

    for x, y in spots[:4 + i % 3]:
        blob(p, x, y, 5, 5, c1)
        p.circle(dk(c1, 0.55), (x + 1, y - 4), 1)


def s_moss(p, pid, c1, c2, i):
    for x, y, rx, ry, col in [(13, 39, 9, 6, dk(c1, 0.2)),
                              (35, 39, 9, 6, dk(c1, 0.2)),
                              (24, 34, 15, 10, c1),
                              (17, 30, 9, 7, lt(c1, 0.12)),
                              (31, 30, 9, 7, lt(c1, 0.12)),
                              (24, 25, 8, 6, lt(c1, 0.25))]:
        blob(p, x, y, rx, ry, col)

    for x, y in [(15, 22), (24, 15), (33, 21), (20, 11), (29, 11)][:4 + i % 2]:
        p.line(dk(c1, 0.2), (x, y + 8), (x, y), 1)
        p.circle(c2, (x, y), 2.4)
        p.circle(lt(c2, 0.6), (x - 1, y - 1), 1)


def s_clover(p, pid, c1, c2, i):
    grass(p)
    stem(p, [(24, 45), (24, 34), (24, 16)], 2, GRN)

    for cx, cy, turn in ((12, 35, 0), (36, 34, 40)):
        for k in range(3):
            heart(p, cx, cy, k * 120 + turn, 4.2, c1)

    for k in range(8):
        a = math.radians(k * 45)
        p.circle(c2, (24 + math.cos(a) * 4, 12 + math.sin(a) * 4), 2.6)

    p.circle(lt(c2, 0.45), (24, 12), 3.2)
    p.circle((255, 255, 255), (23, 11), 1)


def s_wheat(p, pid, c1, c2, i):
    grass(p)

    for base_x, top_x, top_y in ((24, 24, 13), (19, 13, 17), (29, 35, 17)):
        mid = ((base_x + top_x) / 2, 32)
        stem(p, [(base_x, 45), mid, (top_x, top_y + 8)], 2, GRN)

        x, y, ang = path_point([mid, (top_x, top_y + 8)], 1.0)
        ear(p, top_x, top_y + 9, 0 if top_x == 24 else (-14 if top_x < 24 else 14),
            16 if top_x == 24 else 14, c1, c2)

    leaf(p, 24, 44, -38, 22, 5, GRN)
    leaf(p, 24, 44, 40, 20, 5, GRN_D)


def s_sunflower(p, pid, c1, c2, i):
    cx, cy = 24, 16

    grass(p)
    stem(p, [(24, 45), (24, 30), (24, 22)], 4, GRN)
    leaf(p, 24, 40, -66, 16, 10, GRN)
    leaf(p, 24, 34, 66, 15, 9, GRN_D)

    for k in range(16):
        petal(p, cx, cy, k * 22.5 + 11, 14, 5.5, dk(c1, 0.22))

    for k in range(16):
        petal(p, cx, cy, k * 22.5, 13, 5.5, c1)

    blob(p, cx, cy, 8, 8, c2)

    for k in range(14):
        a = k * 2.4
        r = 1.2 + k * 0.38
        p.circle(dk(c2, 0.5), (cx + math.cos(a) * r, cy + math.sin(a) * r), 1)


def s_crystal(p, pid, c1, c2, i):
    leaf(p, 24, 46, -72, 14, 5, GRN)
    leaf(p, 24, 46, 72, 14, 5, GRN_D)

    prism(p, 10, 45, 13, 6, mix(c1, c2, 0.4))
    prism(p, 38, 45, 15, 7, mix(c1, c2, 0.4))
    prism(p, 16, 45, 24, 9, dk(c1, 0.08))
    prism(p, 32, 45, 28, 10, c1)
    prism(p, 24, 46, 38, 12, lt(c1, 0.12))

    for x, y in ((6, 20), (42, 14), (13, 8)):
        p.line(c2, (x - 3, y), (x + 3, y), 1)
        p.line(c2, (x, y - 3), (x, y + 3), 1)


def s_lotus(p, pid, c1, c2, i):
    p.ellipse(dk(GRN, 0.25), 24, 41, 21, 6)
    p.ellipse(GRN, 24, 40, 20, 5)
    p.ellipse(lt(GRN, 0.15), 18, 39, 8, 2)

    for a in (-78, -52, 52, 78):
        petal(p, 24, 39, a, 21, 9.5, dk(c1, 0.2))

    for a in (-30, 30):
        petal(p, 24, 39, a, 24, 11, c1)

    petal(p, 24, 39, 0, 27, 12, lt(c1, 0.1))

    for a, length in ((-30, 24), (30, 24), (0, 27)):
        ux, uy = _dir(a)
        p.circle(c2, (24 + ux * length, 39 + uy * length), 2.2)


def s_pine(p, pid, c1, c2, i):
    p.poly(BROWN, [(22, 45), (22, 36), (26, 36), (26, 45)])

    layers = [(40, 28), (32, 24), (24, 20), (16, 15), (9, 10)]

    for y, w in layers:
        top = (24, y - 12)

        p.poly(dk(c1, 0.28), [top, (24 - w / 2, y), (24 + w / 2, y)])
        p.poly(c1, [top, (24 - w / 2, y), (24, y)])
        p.poly(c2, [top, (24 - w * 0.2, y - 7), (24 + w * 0.2, y - 7)])
        p.line(lt(c1, 0.3), (24 - w / 2 + 2, y - 1), (24 - 1, y - 1), 1)


SHAPES = {
    "daisy": s_daisy, "bell": s_bell, "tulip": s_tulip,
    "mushroom": s_mushroom, "fern": s_fern, "berry": s_berry,
    "moss": s_moss, "clover": s_clover, "wheat": s_wheat,
    "sunflower": s_sunflower, "crystal": s_crystal,
    "lotus": s_lotus, "pine": s_pine
}


# ==============================
# ВЫЗОВЫ ДЛЯ ИГРЫ
# ==============================

def render_plant(p, plant, index):
    SHAPES[plant["shape"]](p, plant["id"], rgb(plant["c1"]),
                           rgb(plant["c2"]), index)


def render_aura(p, plant):
    # Тень под растением. У редких, легендарных и суперрастений ещё и свечение.
    p.ellipse((0, 0, 0, 60), 24, 45, 14, 3.5)

    rarity = plant["rarity"]

    if rarity not in ("rare", "legendary", "super"):
        return

    base = rgb(plant["c1"] if rarity == "rare" else plant["c2"])
    top = {"rare": 36, "legendary": 56, "super": 72}[rarity]

    for k in range(10, 0, -1):
        alpha = int(top * (1 - k / 10) ** 1.1 + 5)
        p.circle((*base, alpha), (24, 25), k * 2.3)


def render_sparkles(p, plant):
    rarity = plant["rarity"]

    if rarity not in ("legendary", "super"):
        return

    spots = [(7, 9), (41, 13), (9, 33), (40, 31), (24, 3)]

    for x, y in spots[:3 if rarity == "legendary" else 5]:
        p.line((255, 255, 255), (x - 3, y), (x + 3, y), 1)
        p.line((255, 255, 255), (x, y - 3), (x, y + 3), 1)
        p.circle((255, 240, 160), (x, y), 1)


def render_sprout(p, plant, stage):
    # Росток своего цвета: по бутону видно, какое растение вырастет
    c1, c2 = rgb(plant["c1"]), rgb(plant["c2"])
    shape = plant["shape"]

    p.ellipse((0, 0, 0, 55), 24, 45, 13, 3.5)
    p.ellipse(dk(BROWN, 0.2), 24, 43.5, 13, 4)
    p.ellipse(BROWN, 24, 42.5, 12, 3.5)
    p.ellipse(lt(BROWN, 0.25), 20, 41.5, 5, 1.5)

    if stage == "seed":
        stem(p, [(24, 42), (24, 35)], 2, GRN)
        leaf(p, 24, 37, -55, 9, 4, GRN)
        leaf(p, 24, 37, 55, 9, 4, GRN_D)
        blob(p, 24, 32, 3.6, 4.2, c1)
        return

    stem(p, [(24, 42), (24, 25)], 3, GRN)
    leaf(p, 24, 40, -58, 14, 6, GRN)
    leaf(p, 24, 36, 60, 14, 6, GRN_D)
    leaf(p, 24, 30, -38, 10, 4.5, GRN)
    leaf(p, 24, 30, 40, 10, 4.5, GRN_D)

    if shape in ("tulip", "bell", "lotus"):
        p.poly(dk(c1, 0.25), [(24, 7), (18, 19), (20, 26), (28, 26), (30, 19)])
        p.poly(c1, [(24, 7), (18, 19), (20, 26), (25, 26)])
        p.ellipse(c2, 24, 10, 1.8, 3)

    elif shape == "mushroom":
        p.poly(dk(c1, 0.3), dome(24, 26, 10, 10))
        p.poly(c1, dome(23, 26, 8.5, 8.5))
        p.circle(c2, (22, 19), 1.8)
        p.circle(c2, (27, 22), 1.4)

    elif shape == "wheat":
        ear(p, 24, 28, 0, 14, c1, c2)

    elif shape == "crystal":
        prism(p, 24, 27, 17, 9, c1)

    elif shape == "pine":
        for y, w in ((26, 14), (19, 11), (12, 8)):
            p.poly(dk(c1, 0.28), [(24, y - 8), (24 - w / 2, y), (24 + w / 2, y)])
            p.poly(c1, [(24, y - 8), (24 - w / 2, y), (24, y)])

    elif shape == "fern":
        p.circle(dk(c1, 0.2), (24, 18), 6)
        p.circle(c1, (24, 17), 5)
        p.circle(lt(c1, 0.45), (22, 15), 1.8)
        p.circle(dk(c1, 0.35), (25, 19), 2)

    else:
        blob(p, 24, 19, 6, 7, c1)
        leaf(p, 24, 24, -45, 8, 3.5, GRN)
        leaf(p, 24, 24, 45, 8, 3.5, GRN_D)
        p.circle(c2, (24, 12), 1.8)
