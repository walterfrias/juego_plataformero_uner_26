#!/usr/bin/env python3
"""
gen_lab_ventanal.py  —  pared del laboratorio con ventanales grandes y
vidrio transparente, para ver detrás la ciudad de noche con parallax
(Nivel 2, 16/10). La de gen_lab.py (lab_far.png, con la ciudad pintada
adentro y quieta) sigue en uso en la arena del Nivel 3.

Qué crea (en game/assets/Lab/):
  - lab_far_ventanal.png  224x176 : misma pared que lab_far.png (paneles,
        guarda, zócalo) pero con 2 ventanales de 94x90 (antes 84x70) cuyo
        vidrio es casi transparente (reflejo tenue + 2 vetas en diagonal).
        Tileable en X. Los huecos van en x 10-104 y 120-214, y 16-106.
  - lab_ventana_luz.png   100x56  : resplandor anaranjado de los incendios
        que entra por el ventanal y cae sobre la pared (degradé que se
        abre hacia abajo). Se titila por evento.

Uso:  python3 scripts/gen_lab_ventanal.py   (desde la raíz del repo)
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from gen_lab import OUT, SEAM, STRIPE, STRIPE_HI, WALL, WALL_DK, WALL_HI, WIN_FRAME  # noqa: E402

W, H = 224, 176
WINDOWS = [(10, 16, 104, 106), (120, 16, 214, 106)]  # x0, y0, x1, y1 (marco incluido)
FRAME_HI = (84, 98, 108, 255)
FRAME_DK = (36, 44, 52, 255)
GLASS = (130, 160, 180, 22)
STREAK = (190, 215, 230, 46)
GRIME = (20, 28, 30, 70)
FIRE = (255, 150, 70)


def lab_far_ventanal():
    img = Image.new("RGBA", (W, H), WALL)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 28):
        d.line([(x, 0), (x, H)], fill=SEAM)
        d.line([(x + 1, 0), (x + 1, H)], fill=WALL_HI)
    d.rectangle([0, H - 30, W, H], fill=WALL_DK)
    d.line([(0, H - 30), (W, H - 30)], fill=SEAM)
    d.rectangle([0, H - 56, W, H - 50], fill=STRIPE)
    d.line([(0, H - 56), (W, H - 56)], fill=STRIPE_HI)

    for x0, y0, x1, y1 in WINDOWS:
        # marco con luz arriba/izq y sombra abajo/der
        d.rectangle([x0, y0, x1, y1], fill=WIN_FRAME)
        d.line([(x0, y0), (x1, y0)], fill=FRAME_HI)
        d.line([(x0, y0), (x0, y1)], fill=FRAME_HI)
        d.line([(x0, y1), (x1, y1)], fill=FRAME_DK)
        d.line([(x1, y0), (x1, y1)], fill=FRAME_DK)
        # alféizar
        d.rectangle([x0 - 3, y1 + 1, x1 + 3, y1 + 3], fill=WIN_FRAME)
        d.line([(x0 - 3, y1 + 1), (x1 + 3, y1 + 1)], fill=FRAME_HI)
        # vidrio: casi transparente
        gx0, gy0, gx1, gy1 = x0 + 3, y0 + 3, x1 - 3, y1 - 3
        d.rectangle([gx0, gy0, gx1, gy1], fill=GLASS)
        # vetas de reflejo en diagonal
        for off, wd in ((10, 3), (26, 1)):
            for t in range(wd):
                d.line([(gx0 + off + t, gy1), (gx0 + off + t + (gy1 - gy0), gy0)], fill=STREAK)
        # mugre en las esquinas de abajo
        for k in range(6):
            d.line([(gx0, gy1 - k), (gx0 + 6 - k, gy1 - k)], fill=GRIME)
            d.line([(gx1 - 6 + k, gy1 - k), (gx1, gy1 - k)], fill=GRIME)
        # parteluz vertical y travesaño (los dibujo al final, opacos)
        mx = (x0 + x1) // 2
        d.rectangle([mx - 1, y0, mx, y1], fill=WIN_FRAME)
        d.line([(mx + 1, gy0), (mx + 1, gy1)], fill=FRAME_DK)
        ty = y0 + 30
        d.line([(x0, ty), (x1, ty)], fill=WIN_FRAME)
        d.line([(gx0, ty + 1), (gx1, ty + 1)], fill=FRAME_DK)
    # las vetas pisan el marco: se vuelve a pintar el marco por encima
    for x0, y0, x1, y1 in WINDOWS:
        for x in range(x0, x1 + 1):
            for y in (y0, y0 + 1, y0 + 2, y1 - 2, y1 - 1, y1):
                if img.getpixel((x, y))[3] < 255:
                    img.putpixel((x, y), WIN_FRAME)
        for y in range(y0, y1 + 1):
            for x in (x0, x0 + 1, x0 + 2, x1 - 2, x1 - 1, x1):
                if img.getpixel((x, y))[3] < 255:
                    img.putpixel((x, y), WIN_FRAME)
    img.save(f"{OUT}/lab_far_ventanal.png")


def lab_ventana_luz():
    w, h = 100, 56
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        t = y / (h - 1)
        a = int(78 * (1 - t) ** 1.6)
        spread = int(4 + 8 * t)              # se abre hacia abajo
        for x in range(w):
            edge = min(x + spread, w - 1 - x + spread) / 14
            k = max(0.0, min(1.0, edge))
            img.putpixel((x, y), (*FIRE, int(a * k)))
    img.save(f"{OUT}/lab_ventana_luz.png")


if __name__ == "__main__":
    lab_far_ventanal()
    lab_ventana_luz()
    print("ok:", f"{OUT}/lab_far_ventanal.png", f"{OUT}/lab_ventana_luz.png")
