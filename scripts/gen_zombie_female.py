#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombie_female.py  —  zombie femenina placeholder, ciclo de caminata
"arrastrando los pies" + cabeza que se balancea.

Crea:
  game/assets/Zombie_F/Zombie_F_Walk_1.png .. _10.png   (32x34 c/u, RGBA)
  game/assets/Zombie_F/zombie_f_walk_sheet.png          (320x34, referencia)

Diseño:
  - humanoide completo (no la cabezona "Big Zombie"): vestido roto,
    pelo largo, piel verdosa. Silueta distinta para diferenciarla.
  - 10 frames: los pies casi no se levantan, se deslizan hacia adelante
    y "resetean" (shuffle). La cabeza hace 1 balanceo lento por ciclo.
  - Ancla fija en la cadera: el cuerpo NO se desplaza en el frame (el
    motor lo mueve). Pies a ras del borde inferior (y=34) para apoyar
    igual que los demás sprites del juego.

Tech: Python 3 + Pillow.
Uso:  python3 scripts/gen_zombie_female.py    (desde la raíz del repo)

Para reemplazar por arte propio: dibujá 10 frames 32x34 en Pixaki
(ancla fija en la cadera, pies al borde inferior, fondo transparente),
guardalos con estos nombres.
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Zombie_F"
os.makedirs(OUT, exist_ok=True)

W, H = 32, 34
N = 10

# --- paleta (noche) ---
OUTL    = (24, 24, 34, 255)
SKIN    = (150, 190, 150, 255)
SKIN_S  = (108, 150, 116, 255)
DRESS   = (150, 120, 138, 255)     # vestido rosa polvoriento
DRESS_S = (104, 80, 100, 255)
HAIR    = (54, 48, 66, 255)
HAIR_H  = (84, 78, 100, 255)
SHOE    = (60, 52, 60, 255)
EYE     = (214, 74, 74, 255)
MOUTH   = (120, 40, 44, 255)

TAU = math.tau


def _outline(img):
    """1px de contorno OUTL alrededor de toda la silueta."""
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

    bob = round(math.sin(t * TAU * 2))                  # 2 rebotes / ciclo
    sway = round(1.6 * math.sin(t * TAU))               # cabeza: 1 balanceo / ciclo
    tilt = math.sin(t * TAU + 1)                        # inclinación de la cabeza
    hip_y = 20 + bob

    # ---- piernas + pies (arrastrados: casi no se levantan) ----
    def leg(phase, side):
        s = (t + phase) % 1.0
        slide = (round(s * 5) - 2) if s < 0.82 else -2       # desliza y resetea
        fx = cx + side * 2 + slide
        fy = 33 - (1 if 0.78 < s < 0.92 else 0)              # micro-levantada
        d.line([(cx + side * 2, hip_y + 4), (fx, fy - 1)], fill=SKIN_S, width=2)
        d.rectangle([fx - 2, fy - 1, fx + 2, fy], fill=SHOE)  # pie/zapato
    leg(0.0, -1)
    leg(0.5, +1)

    # ---- vestido (trapecio roto) ----
    waist_y = hip_y - 4
    hem = 30 + bob
    d.polygon([(cx - 3, waist_y), (cx + 3, waist_y),
               (cx + 6, hem), (cx - 5, hem)], fill=DRESS)
    d.polygon([(cx + 1, waist_y), (cx + 3, waist_y),
               (cx + 6, hem), (cx + 2, hem)], fill=DRESS_S)   # sombra derecha
    d.polygon([(cx - 3, waist_y - 5), (cx + 3, waist_y - 5),
               (cx + 3, waist_y + 1), (cx - 3, waist_y + 1)], fill=DRESS)  # torso
    for jx in (cx - 4, cx, cx + 4):                           # jirones del ruedo
        d.rectangle([jx, hem - 1, jx, hem], fill=(0, 0, 0, 0))

    # ---- brazo lejano (detrás del vestido) ----
    def arm(phase, side, col):
        sx, sy = cx + side * 3, waist_y - 3
        sw = round(2 * math.sin((t + phase) * TAU))
        ex, ey = cx + side * 2 + sw, hip_y - 1
        hx, hy = cx + 6 + abs(sw), hip_y + 2                  # mano estirada al frente
        d.line([(sx, sy), (ex, ey), (hx, hy)], fill=col, width=2)
        d.rectangle([hx - 1, hy - 1, hx + 1, hy + 1], fill=SKIN)
    arm(0.75, -1, SKIN_S)

    # ---- cuello + cabeza + pelo ----
    hx = cx + sway
    hy = 7 + bob
    d.rectangle([cx - 1, hy + 3, cx + 1, hy + 6], fill=SKIN_S)          # cuello
    # melena (asimétrica, cuelga por detrás de los hombros)
    d.ellipse([hx - 4, hy - 4, hx + 5, hy + 13 + round(tilt)], fill=HAIR)
    d.ellipse([hx - 4, hy - 4, hx + 1, hy + 10], fill=HAIR_H)          # brillo
    d.ellipse([hx - 3, hy - 3, hx + 3, hy + 4], fill=SKIN)             # cara
    d.ellipse([hx - 4, hy - 4, hx + 4, hy + 0], fill=HAIR)             # flequillo
    d.point([(hx - 2, hy + 1), (hx + 1, hy + 1)], fill=EYE)            # ojos
    d.line([(hx - 1, hy + 3), (hx + 1, hy + 3 - round(tilt))], fill=MOUTH)  # boca torcida
    d.point([(hx + 5, hy + 6), (hx - 4, hy + 11), (hx + 4, hy + 9)], fill=HAIR)  # mechones

    # ---- brazo cercano (por delante) ----
    arm(0.25, 1, SKIN)

    _outline(img)
    return img


def main():
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames, 1):
        f.save(f"{OUT}/Zombie_F_Walk_{i}.png")
    sheet = Image.new("RGBA", (W * N, H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0))
    sheet.save(f"{OUT}/zombie_f_walk_sheet.png")
    print(f"{N} frames {W}x{H}  ->  {OUT}/Zombie_F_Walk_1..{N}.png")
    print(f"spritesheet {sheet.size}  ->  {OUT}/zombie_f_walk_sheet.png")


if __name__ == "__main__":
    main()
