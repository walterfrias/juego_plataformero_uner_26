#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombie_male.py  —  zombie masculino placeholder, caminata con RENGUERA
(una pierna tiesa que arrastra) + cabeza caída que se mece.

Crea:
  game/assets/Zombie_M/Zombie_M_Walk_1.png .. _8.png   (32x34 c/u, RGBA)
  game/assets/Zombie_M/zombie_m_walk_sheet.png         (256x34, referencia)

Diseño (para diferenciarlo de los otros dos zombies):
  - contextura ancha, encorvado. Camisa azul rota (un hombro con herida),
    pantalón oscuro, pelo corto. Piel verdosa como la familia.
  - 8 frames: la pierna izquierda queda tiesa y pivota como pata de palo
    (renguera); la derecha da el paso real. El cuerpo se hunde y se
    inclina cuando el peso cae en la pierna tiesa. Cabeza caída hacia
    adelante, se mece 1 vez por ciclo. Brazos estirados al frente.
  - Ancla fija en la cadera. Pies al borde inferior (y=34).

Tech: Python 3 + Pillow.
Uso:  python3 scripts/gen_zombie_male.py    (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Zombie_M"
os.makedirs(OUT, exist_ok=True)

W, H = 32, 34
N = 8

OUTL    = (24, 24, 34, 255)
SKIN    = (150, 190, 150, 255)
SKIN_S  = (108, 150, 116, 255)
SHIRT   = (92, 112, 140, 255)
SHIRT_S = (60, 78, 108, 255)
PANTS   = (58, 58, 74, 255)
PANTS_S = (40, 40, 54, 255)
HAIR    = (58, 50, 44, 255)
WOUND   = (150, 52, 56, 255)
EYE     = (214, 74, 74, 255)
MOUTH   = (120, 40, 44, 255)

TAU = math.tau


def _outline(img):
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 \
                        and px[nx, ny] != OUTL:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = OUTL


def frame(i):
    t = i / N
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = 15

    # la renguera: el cuerpo se hunde en la fase de apoyo sobre la pierna tiesa
    stance = max(0.0, math.sin((t - 0.10) * TAU))          # pico ~t=0.35
    dip = round(2 * stance)
    lurch = round(1.5 * stance)                            # se va para adelante
    hip_y = 20 + dip

    # ---- pierna tiesa (izq): pivota como pata de palo ----
    peg_ang = 0.5 * math.sin(t * TAU)                      # oscila alrededor del apoyo
    lx = cx - 2 + round(math.sin(peg_ang) * 3)
    d.line([(cx - 2, hip_y + 3), (lx, 33)], fill=SKIN_S, width=3)
    d.rectangle([lx - 2, 32, lx + 2, 33], fill=PANTS_S)

    # ---- pierna sana (der): da el paso ----
    s = (t + 0.5) % 1.0
    rx = cx + 2 + (round(s * 6) - 3)
    ry = 33 - round(3 * max(0.0, math.sin(s * math.pi)))   # levanta y baja
    d.line([(cx + 2, hip_y + 3), (rx, ry)], fill=SKIN_S, width=3)
    d.rectangle([rx - 2, ry - 1, rx + 2, ry], fill=PANTS)

    # ---- pantalón / cadera ----
    d.polygon([(cx - 4, hip_y - 2), (cx + 5, hip_y - 2),
               (cx + 4, hip_y + 5), (cx - 4, hip_y + 5)], fill=PANTS)
    d.polygon([(cx + 1, hip_y - 2), (cx + 5, hip_y - 2),
               (cx + 4, hip_y + 5), (cx + 1, hip_y + 5)], fill=PANTS_S)

    # ---- torso ancho encorvado (camisa) ----
    sh_y = hip_y - 9 + dip
    d.polygon([(cx - 5 + lurch, sh_y), (cx + 6 + lurch, sh_y),
               (cx + 5, hip_y - 1), (cx - 4, hip_y - 1)], fill=SHIRT)
    d.polygon([(cx + 2 + lurch, sh_y), (cx + 6 + lurch, sh_y),
               (cx + 5, hip_y - 1), (cx + 2, hip_y - 1)], fill=SHIRT_S)
    d.rectangle([cx + 3 + lurch, sh_y, cx + 5 + lurch, sh_y + 2], fill=WOUND)  # herida hombro

    # ---- brazos estirados al frente (uno más alto) ----
    def arm(yoff, phase):
        sx, sy = cx + 4 + lurch, sh_y + 1 + yoff
        sw = round(1.5 * math.sin((t + phase) * TAU))
        hx, hy = cx + 8, sh_y + 3 + yoff + sw
        d.line([(sx, sy), (cx + 6, sy + 1), (hx, hy)], fill=SHIRT_S, width=2)
        d.rectangle([hx - 1, hy - 1, hx + 1, hy + 1], fill=SKIN)
    arm(4, 0.5)                                            # brazo bajo (más atrás)
    # cabeza va en el medio del z-order

    # ---- cabeza caída + pelo corto ----
    hx = cx + round(1.5 * math.sin(t * TAU))
    hy = 8 + dip + round(math.sin(t * TAU * 2))
    d.rectangle([cx, hy + 3, cx + 2, hy + 6], fill=SKIN_S)          # cuello (inclinado adel.)
    d.ellipse([hx - 3, hy - 3, hx + 4, hy + 4], fill=SKIN)         # cara
    d.ellipse([hx - 3, hy - 4, hx + 4, hy + 0], fill=HAIR)         # pelo corto
    d.point([(hx - 3, hy), (hx + 4, hy - 1)], fill=HAIR)           # patillas
    d.point([(hx - 1, hy + 1), (hx + 2, hy + 1)], fill=EYE)        # ojos
    d.line([(hx - 1, hy + 3), (hx + 2, hy + 2)], fill=MOUTH)       # boca torcida

    arm(0, 0.0)                                            # brazo alto (al frente)

    _outline(img)
    return img


def main():
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames, 1):
        f.save(f"{OUT}/Zombie_M_Walk_{i}.png")
    sheet = Image.new("RGBA", (W * N, H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0))
    sheet.save(f"{OUT}/zombie_m_walk_sheet.png")
    print(f"{N} frames {W}x{H}  ->  {OUT}/Zombie_M_Walk_1..{N}.png")


if __name__ == "__main__":
    main()
