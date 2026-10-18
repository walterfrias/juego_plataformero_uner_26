#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_l3_mecanicas.py  —  arte de los peligros de calle del Nivel 3 (18/10), que
reemplazan a los pozos (en una calle del centro no tenían sentido). Lo cablea
wire_l3_mecanicas.py; la ubicación está en l3_recorrido.py.

Crea (game/assets/City/):
  charco.png          32x8   agua electrificada sobre la vereda, tileable en X
  chispa_1..3.png     24x14  chispazos del cable de alta tensión caído sobre el
                             charco (el cable sale del costado izquierdo)
  toldo_rebote_1.png  46x12  toldo verde y blanco (como el del bar) que rebota
  toldo_rebote_2.png  46x12  el mismo hundido (un instante, al rebotar)
  rejilla_subte.png   32x6   respiradero del subte en la vereda
  vapor.png           28x16  vapor del subte, tileable en Y (sube con YOffset)
  marquesina.png      72x10  marquesina de un local: plataforma que se atraviesa
                             desde abajo (a la que sube el vapor)
  bala.png             8x3   bala del policía zombie (mira a la derecha)
  destello_1/2.png    10x10  fogonazo en la mano: chico (aviso) y grande (disparo)

Pillow, paleta noche, tramado Bayer.
Uso:  python3 scripts/gen_l3_mecanicas.py
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
OUTL = (24, 24, 34, 255)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
WATER = [(26, 34, 50, 255), (40, 52, 74, 255), (70, 90, 120, 255), (150, 176, 210, 255)]
SPARK = [(255, 250, 200, 255), (250, 220, 90, 255), (150, 200, 255, 255)]
CABLE = (20, 20, 26, 255)
AWN_G, AWN_W, AWN_DK = (40, 96, 66, 255), (200, 196, 176, 255), (24, 56, 40, 255)


def charco():
    """agua electrificada: más clara que la vereda y con arcos celestes, para que se
    lea como peligro (la primera versión, oscura y finita, casi no se veía)."""
    img = Image.new("RGBA", (32, 8), T)
    px = img.load()
    for y in range(8):
        for x in range(32):
            px[x, y] = WATER[2] if (x + y * 3) % 7 else WATER[1]
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (31, 0)], fill=WATER[3])                 # superficie con brillo
    for x0, x1, y in ((2, 8, 3), (14, 19, 5), (23, 29, 2)):  # arcos eléctricos
        d.line([(x0, y), ((x0 + x1) // 2, y - 1), (x1, y)], fill=SPARK[2])
    for x in (5, 17, 26):
        d.point((x, 1), fill=SPARK[0])
    return img


def chispa(k):
    """cable caído que entra al charco por la izquierda y chisporrotea (3 cuadros)."""
    img = Image.new("RGBA", (24, 14), T)
    d = ImageDraw.Draw(img)
    d.line([(0, 2), (6, 6), (10, 11)], fill=CABLE, width=2)  # el cable
    d.point((11, 12), fill=(120, 120, 130, 255))             # punta pelada
    rays = [[(11, 12, 16, 6), (11, 12, 6, 7), (11, 12, 19, 11)],
            [(11, 12, 14, 3), (11, 12, 20, 9), (11, 12, 5, 10)],
            [(11, 12, 17, 8), (11, 12, 8, 4), (11, 12, 22, 12)]][k]
    for x0, y0, x1, y1 in rays:
        mx, my = (x0 + x1) // 2 + (1 if k % 2 else -1), (y0 + y1) // 2
        d.line([(x0, y0), (mx, my), (x1, y1)], fill=SPARK[1])
        d.point((x1, y1), fill=SPARK[0])
    d.ellipse([9, 10, 13, 13], fill=SPARK[2 if k == 1 else 0])
    return img


def toldo(hundido):
    w, h = 46, 12
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    sag = 3 if hundido else 0
    for x in range(w):
        mid = 1 - abs(x - w / 2) / (w / 2)                   # se hunde más en el medio
        top = int(2 + sag * mid)
        c = AWN_G if (x // 6) % 2 == 0 else AWN_W
        d.line([(x, top), (x, top + 5)], fill=c)
        d.point((x, top), fill=(min(255, c[0] + 40), min(255, c[1] + 40), min(255, c[2] + 40), 255))
        if x % 6 in (2, 3):                                  # flecos
            d.line([(x, top + 6), (x, top + 7)], fill=c)
    d.line([(0, 0), (0, 8)], fill=AWN_DK)                    # brazos de hierro a la pared
    d.line([(w - 1, 0), (w - 1, 8)], fill=AWN_DK)
    return img


def rejilla():
    img = Image.new("RGBA", (32, 6), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 5], fill=(40, 42, 50, 255))
    for x in range(2, 31, 3):
        d.line([(x, 1), (x, 4)], fill=(10, 10, 14, 255))
    d.line([(0, 0), (31, 0)], fill=(96, 100, 112, 255))
    return img


def vapor():
    img = Image.new("RGBA", (28, 16), T)
    px = img.load()
    for y in range(16):
        for x in range(28):
            e = 1 - abs(x - 13.5) / 14
            a = 120 * e ** 1.2 * (0.7 + 0.3 * ((x * 5 + y * 7) % 9) / 8)
            if a / 16 > BAYER[y % 4][x % 4] * 0.5:
                px[x, y] = (210, 216, 226, int(min(150, a)))
    return img


def marquesina():
    w, h = 72, 10
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, 3], fill=(60, 64, 76, 255))                    # chapa (se pisa la fila 0)
    d.line([(0, 0), (w - 1, 0)], fill=(120, 126, 140, 255))
    d.rectangle([2, 4, w - 3, 9], fill=(28, 30, 40, 255))                    # cartel apagado
    for x in range(6, w - 6, 8):                                              # lamparitas
        d.point((x, 6), fill=(214, 166, 92, 255) if x % 16 else (60, 50, 40, 255))
    return img


def bala():
    """bala del policía zombie: trazo corto y brillante (se lee contra la noche)."""
    img = Image.new("RGBA", (8, 3), T)
    d = ImageDraw.Draw(img)
    d.line([(0, 1), (5, 1)], fill=(250, 214, 120, 160))         # estela
    d.rectangle([5, 0, 7, 2], fill=(255, 240, 190, 255))         # punta
    d.point((7, 1), fill=(255, 255, 255, 255))
    return img


def destello(k):
    """fogonazo en la mano (k=0: chico, el aviso; k=1: grande, el disparo)."""
    img = Image.new("RGBA", (10, 10), T)
    d = ImageDraw.Draw(img)
    r = 2 if k == 0 else 4
    d.ellipse([5 - r, 5 - r, 5 + r, 5 + r], fill=(255, 190, 80, 220))
    d.ellipse([5 - r // 2, 5 - r // 2, 5 + r // 2, 5 + r // 2], fill=(255, 250, 220, 255))
    if k == 1:
        for x0, y0, x1, y1 in ((5, 5, 9, 5), (5, 5, 8, 2), (5, 5, 8, 8)):
            d.line([(x0, y0), (x1, y1)], fill=(255, 220, 140, 255))
    return img


def main():
    charco().save(f"{OUT}/charco.png")
    for k in range(3):
        chispa(k).save(f"{OUT}/chispa_{k + 1}.png")
    toldo(False).save(f"{OUT}/toldo_rebote_1.png")
    toldo(True).save(f"{OUT}/toldo_rebote_2.png")
    rejilla().save(f"{OUT}/rejilla_subte.png")
    vapor().save(f"{OUT}/vapor.png")
    marquesina().save(f"{OUT}/marquesina.png")
    bala().save(f"{OUT}/bala.png")
    destello(0).save(f"{OUT}/destello_1.png")
    destello(1).save(f"{OUT}/destello_2.png")
    print("charco, chispa_1..3, toldo_rebote_1/2, rejilla_subte, vapor, marquesina, bala, destello_1/2  ->", OUT)


if __name__ == "__main__":
    main()
