#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false
"""
gen_l3_luces.py  —  luces del Nivel 3 (18/10): incendios entre los edificios y
luz de los fuegos y faroles sobre las fachadas. Pedido del usuario: "mejoremos
las luces y agreguemos algunos fuegos de fondo entre los edificios". Los
incendios lejanos de L1 que traía L3 quedaron tapados por las dos filas de
edificios (gen_l3_ciudad_capas.py). Lo cablea wire_l3_luces.py.

Crea (game/assets/City/):
  incendio_techo_1..3.png  56x44   llamas sobre un techo, con brasas (3 cuadros)
  resplandor_cielo.png    240x150  el cielo teñido de naranja detrás de un
                                   incendio (recorta las torres a contraluz)
  luz_pared_fuego.png     150x110  la luz de un tacho con fuego sobre la fachada
  luz_pared_farol.png     110x90   la luz de sodio de un farol sobre la fachada

Alfas en escalones con tramado Bayer 4x4 (como lamp_glow y fuego_glow).
Uso:  python3 scripts/gen_l3_luces.py
"""
from PIL import Image, ImageDraw
import math
import os
import random

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
FIRE = [(120, 30, 20), (200, 70, 30), (245, 140, 50), (255, 210, 110), (255, 244, 200)]


def dither(a, x, y, step=24):
    q = a / step
    base = int(q)
    return min(255, (base + (1 if (q - base) * 16 > BAYER[y % 4][x % 4] else 0)) * step)


def glow(w, h, color, a_max, cx=0.5, cy=0.5, power=1.4, floor_cut=False):
    """resplandor elíptico tramado; floor_cut: se corta abajo (apoyado en algo)."""
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5 - w * cx) / (w / 2), (y + 0.5 - h * cy) / (h / 2)
            r = (dx * dx + dy * dy) ** 0.5
            a = max(0.0, 1 - r) ** power * a_max
            if floor_cut and y > h * cy:
                a *= max(0.0, 1 - (y - h * cy) / (h * (1 - cy)) * 1.5)
            v = dither(a, x, y)
            if v:
                px[x, y] = color + (v,)
    return img


def incendio_techo(k):
    """lenguas de fuego sobre la línea de un techo (fila de abajo = el techo)."""
    w, h = 56, 44
    rnd = random.Random(100 + k)
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for x in range(w):
        # altura de la llama en cada columna: varias lenguas que se mueven con k
        e = 1 - abs(x - w / 2) / (w / 2)
        tongue = sum(math.sin(x * f + k * 1.9 + i) * a for i, (f, a) in enumerate(((0.35, 5), (0.8, 3), (1.7, 2))))
        top = int(h - (e ** 0.8) * (h - 6) - tongue)
        for y in range(max(0, top), h):
            t = (y - top) / max(1, h - top)                   # 0 arriba (punta) → 1 abajo (base)
            i = min(4, int((1 - abs(t - 0.75)) * 4.2))        # el centro de la llama, más claro
            c = FIRE[max(0, i - (1 if y < top + 2 else 0))]
            px[x, y] = c + (255 if t > 0.15 else 200,)
    d = ImageDraw.Draw(img)
    for _ in range(8):                                        # brasas que vuelan
        x, y = rnd.randrange(4, w - 4), rnd.randrange(0, h // 2)
        d.point((x, y), fill=FIRE[3] + (255,))
    return img


def main():
    for k in range(3):
        incendio_techo(k).save(f"{OUT}/incendio_techo_{k + 1}.png")
    glow(240, 150, (220, 96, 40), 120, cy=0.62, power=1.6).save(f"{OUT}/resplandor_cielo.png")
    glow(150, 110, (240, 130, 60), 95, cy=0.75, power=1.5, floor_cut=True).save(f"{OUT}/luz_pared_fuego.png")
    glow(110, 90, (230, 190, 110), 70, cy=0.45, power=1.5).save(f"{OUT}/luz_pared_farol.png")
    print("incendio_techo_1..3, resplandor_cielo, luz_pared_fuego, luz_pared_farol  ->", OUT)


if __name__ == "__main__":
    main()
