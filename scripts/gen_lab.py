#!/usr/bin/env python3
"""
gen_lab.py  —  arte procedural del interior del laboratorio (Nivel 2, y
reusado en la arena del Nivel 3). Mismo criterio que el resto del juego:
Pillow, sin IA de imagen ni packs.

Qué crea (en game/assets/Lab/):
  - lab_far.png    224x176 : pared del fondo (paneles, guarda, ventanales
                             con la ciudad de noche detrás). Tileable en X.
  - lab_near.png   224x64  : equipamiento contra la pared (gabinetes,
                             tanques con líquido verde, monitores). Tileable.
  - lab_floor.png  32x96   : piso de baldosas (canto iluminado arriba,
                             se oscurece hacia abajo). Para el objeto Ground.
  - lab_shelf.png  32x8    : estante metálico (plataforma jumpthru).
  - lab_glass.png  32x46   : vidrios rotos / jeringas en el fondo de los
                             huecos (hazard visual, como rebar_spikes.png).
  Mecánicas del Nivel 2 (27/09):
  - camilla.png    48x16   : camilla con ruedas (plataforma móvil sobre
                             huecos anchos). La superficie es la fila 0.
  - wet_floor.png  32x4    : brillo de piso encerado (se superpone al piso;
                             pisarlo = resbalar).
  - wet_sign.png   12x18   : cartel amarillo "piso mojado" (decorado).
  - vent.png       32x6    : rejilla de ventilación en el piso.
  - airflow.png    32x32   : corriente de aire (semitransparente, tileable
                             en Y; se anima con YOffset).
  - lab_cabinet.png 32x32  : gabinete metálico alto (tileable en Y), la
                             pared que solo se pasa con el ducto.

Uso:  python3 scripts/gen_lab.py      (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import random
import os

OUT = "game/assets/Lab"
os.makedirs(OUT, exist_ok=True)

# --- paleta noche, interior ---
WALL_DK = (22, 34, 40, 255)
WALL = (30, 45, 52, 255)
WALL_HI = (40, 58, 66, 255)
SEAM = (16, 25, 30, 255)
STRIPE = (54, 92, 88, 255)
STRIPE_HI = (80, 128, 118, 255)
WIN_FRAME = (58, 70, 80, 255)
WIN_SKY = (12, 16, 32, 255)
WIN_CITY = (26, 32, 54, 255)
WIN_LIGHT = (150, 140, 90, 255)
METAL_LIT = (120, 132, 140, 255)
METAL = (78, 88, 98, 255)
METAL_DK = (44, 50, 58, 255)
TANK_GLASS = (60, 90, 96, 255)
LIQUID = (70, 170, 90, 255)
LIQUID_HI = (140, 230, 140, 255)
SCREEN = (40, 110, 100, 255)
SCREEN_HI = (110, 210, 180, 255)
FLOOR_LIT = (150, 164, 166, 255)
FLOOR = (104, 116, 120, 255)
FLOOR_ALT = (92, 104, 110, 255)
FLOOR_GAP = (56, 64, 70, 255)
GLASS = (150, 210, 220, 255)
GLASS_DK = (80, 130, 150, 255)
NEEDLE = (190, 196, 200, 255)
SYRINGE = (200, 220, 225, 255)


def lab_far():
    w, h = 224, 176
    img = Image.new("RGBA", (w, h), WALL)
    d = ImageDraw.Draw(img)
    # paneles verticales
    for x in range(0, w, 28):
        d.line([(x, 0), (x, h)], fill=SEAM)
        d.line([(x + 1, 0), (x + 1, h)], fill=WALL_HI)
    # zócalo oscuro abajo
    d.rectangle([0, h - 30, w, h], fill=WALL_DK)
    d.line([(0, h - 30), (w, h - 30)], fill=SEAM)
    # guarda horizontal (tipo hospital)
    d.rectangle([0, h - 56, w, h - 50], fill=STRIPE)
    d.line([(0, h - 56), (w, h - 56)], fill=STRIPE_HI)
    # ventanales con la ciudad de noche
    rng = random.Random(7)
    for wx in (14, 126):
        x0, y0, x1, y1 = wx, 30, wx + 84, 100
        d.rectangle([x0, y0, x1, y1], fill=WIN_FRAME)
        d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], fill=WIN_SKY)
        # edificios lejanos
        bx = x0 + 3
        while bx < x1 - 3:
            bw = rng.randint(6, 14)
            bh = rng.randint(12, 36)
            d.rectangle([bx, y1 - 3 - bh, min(bx + bw, x1 - 3), y1 - 3], fill=WIN_CITY)
            for _ in range(rng.randint(0, 3)):
                lx = rng.randint(bx + 1, max(bx + 1, min(bx + bw, x1 - 4) - 1))
                ly = rng.randint(y1 - 2 - bh, y1 - 5)
                d.point((lx, ly), fill=WIN_LIGHT)
            bx += bw + 1
        # parteluces
        mx = (x0 + x1) // 2
        d.line([(mx, y0), (mx, y1)], fill=WIN_FRAME, width=2)
        d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=WIN_FRAME)
    img.save(f"{OUT}/lab_far.png")


def lab_near():
    w, h = 224, 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # gabinete metálico
    d.rectangle([4, 16, 40, h - 1], fill=METAL_DK)
    d.rectangle([6, 18, 38, h - 3], fill=METAL)
    d.line([(22, 18), (22, h - 3)], fill=METAL_DK)
    d.point((20, 40), fill=METAL_LIT)
    d.point((24, 40), fill=METAL_LIT)
    # dos tanques con líquido verde (el "cultivo" del virus)
    for tx in (58, 86):
        d.rectangle([tx, 6, tx + 20, h - 1], fill=METAL_DK)
        d.rectangle([tx + 2, 10, tx + 18, h - 8], fill=TANK_GLASS)
        d.rectangle([tx + 2, 26, tx + 18, h - 8], fill=LIQUID)
        d.line([(tx + 4, 26), (tx + 4, h - 10)], fill=LIQUID_HI)
        for by in (32, 40, 47):
            d.point((tx + 10 + (by % 3), by), fill=LIQUID_HI)
        d.rectangle([tx, 4, tx + 20, 9], fill=METAL)
    # mesada con monitores
    d.rectangle([122, 38, 196, 42], fill=METAL_LIT)
    d.rectangle([126, 43, 130, h - 1], fill=METAL_DK)
    d.rectangle([188, 43, 192, h - 1], fill=METAL_DK)
    for mx in (132, 162):
        d.rectangle([mx, 18, mx + 24, 35], fill=METAL_DK)
        d.rectangle([mx + 2, 20, mx + 22, 33], fill=SCREEN)
        for ly in range(22, 32, 3):
            d.line([(mx + 4, ly), (mx + 4 + (ly * 7) % 14, ly)], fill=SCREEN_HI)
        d.rectangle([mx + 10, 35, mx + 14, 38], fill=METAL_DK)
    # estantería alta con frascos
    d.rectangle([204, 8, 222, h - 1], fill=METAL_DK)
    for sy in (20, 36, 52):
        d.line([(204, sy), (222, sy)], fill=METAL_LIT)
        d.rectangle([207, sy - 5, 210, sy - 1], fill=LIQUID)
        d.rectangle([214, sy - 4, 218, sy - 1], fill=GLASS_DK)
    img.save(f"{OUT}/lab_near.png")


def lab_floor():
    w, h = 32, 96
    img = Image.new("RGBA", (w, h), FLOOR)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], fill=FLOOR)
    d.rectangle([16, 0, 31, 15], fill=FLOOR_ALT)
    d.line([(0, 0), (w, 0)], fill=FLOOR_LIT)
    d.line([(0, 1), (w, 1)], fill=FLOOR_LIT)
    d.line([(0, 15), (w, 15)], fill=FLOOR_GAP)
    d.line([(15, 2), (15, 15)], fill=FLOOR_GAP)
    # debajo: losa, cada vez más oscura
    for y in range(16, h):
        t = (y - 16) / (h - 16)
        c = tuple(int(a * (1 - t) + b * t) for a, b in zip(WALL_DK[:3], (10, 14, 18))) + (255,)
        d.line([(0, y), (w, y)], fill=c)
    img.save(f"{OUT}/lab_floor.png")


def lab_shelf():
    w, h = 32, 8
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 3], fill=METAL)
    d.line([(0, 0), (w, 0)], fill=METAL_LIT)
    d.line([(0, 3), (w, 3)], fill=METAL_DK)
    d.rectangle([2, 4, 3, h], fill=METAL_DK)
    d.rectangle([28, 4, 29, h], fill=METAL_DK)
    img.save(f"{OUT}/lab_shelf.png")


def lab_glass():
    w, h = 32, 46
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # base de escombros
    d.rectangle([0, h - 10, w, h], fill=FLOOR_GAP)
    # vidrios (triángulos) — el patrón cierra en el borde para tilear
    shards = [(0, 14, 5), (6, 22, 4), (13, 10, 6), (21, 26, 4), (27, 16, 5)]
    for x, top, half in shards:
        d.polygon([(x - half + 3, h - 10), (x + 3, h - 10 - top), (x + half + 3, h - 10)],
                  fill=GLASS_DK)
        d.line([(x + 3, h - 10 - top), (x + 1, h - 11)], fill=GLASS)
    # jeringas clavadas
    for sx, sy in ((9, 14), (24, 20)):
        d.rectangle([sx, sy, sx + 2, sy + 12], fill=SYRINGE)
        d.line([(sx + 1, sy + 13), (sx + 1, h - 10)], fill=NEEDLE)
        d.rectangle([sx - 1, sy - 1, sx + 3, sy], fill=METAL_LIT)
        d.rectangle([sx, sy + 7, sx + 2, sy + 11], fill=LIQUID)
    img.save(f"{OUT}/lab_glass.png")


def camilla():
    w, h = 48, 16
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, 4], fill=(196, 204, 206, 255))          # colchón
    d.line([(0, 0), (w - 1, 0)], fill=(226, 232, 232, 255))
    d.rectangle([34, 0, 46, 3], fill=(170, 200, 206, 255))            # almohada
    d.rectangle([0, 5, w - 1, 6], fill=METAL)                         # bastidor
    d.line([(0, 5), (w - 1, 5)], fill=METAL_LIT)
    for x in (5, 41):
        d.rectangle([x, 7, x + 1, 12], fill=METAL_DK)                 # patas
        d.ellipse([x - 2, 12, x + 3, 15], fill=(40, 42, 48, 255))     # ruedas
        d.point((x, 13), fill=METAL_LIT)
    d.line([(7, 10), (41, 10)], fill=METAL_DK)
    img.save(f"{OUT}/camilla.png")


def wet_floor():
    w, h = 32, 4
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1, w - 1, 3], fill=(150, 200, 220, 110))
    for x in (3, 4, 5, 17, 18, 26):
        d.point((x, 1), fill=(230, 245, 250, 220))
    d.line([(9, 2), (13, 2)], fill=(210, 235, 245, 170))
    img.save(f"{OUT}/wet_floor.png")


def wet_sign():
    w, h = 12, 18
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y1, y2 = (222, 190, 60, 255), (170, 140, 36, 255)
    d.polygon([(6, 0), (11, 17), (1, 17)], fill=y1)
    d.polygon([(6, 0), (11, 17), (7, 17)], fill=y2)
    d.rectangle([4, 7, 7, 10], fill=(30, 30, 34, 255))               # pictograma
    d.point([(5, 6), (6, 12), (4, 13)], fill=(30, 30, 34, 255))
    img.save(f"{OUT}/wet_sign.png")


def vent():
    w, h = 32, 6
    img = Image.new("RGBA", (w, h), METAL_DK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=METAL)
    for x in range(3, w - 2, 4):
        d.line([(x, 1), (x, h - 2)], fill=(18, 22, 26, 255))
    d.line([(0, 0), (w - 1, 0)], fill=METAL_LIT)
    img.save(f"{OUT}/vent.png")


def airflow():
    w, h = 32, 32
    img = Image.new("RGBA", (w, h), (150, 210, 220, 22))
    d = ImageDraw.Draw(img)
    rng = random.Random(3)
    for _ in range(9):
        x = rng.randint(1, w - 2)
        y = rng.randint(0, h - 1)
        ln = rng.randint(5, 11)
        for k in range(ln):
            d.point((x, (y + k) % h), fill=(200, 240, 245, 40 + 8 * k))
    img.save(f"{OUT}/airflow.png")


def lab_cabinet():
    w, h = 32, 32
    img = Image.new("RGBA", (w, h), METAL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=METAL_DK)
    d.line([(1, 0), (1, h - 1)], fill=METAL_LIT)
    d.line([(15, 0), (15, h - 1)], fill=METAL_DK)
    d.line([(0, 15), (w - 1, 15)], fill=METAL_DK)
    for y in (6, 22):
        d.rectangle([12, y, 13, y + 2], fill=METAL_LIT)
        d.rectangle([18, y, 19, y + 2], fill=METAL_LIT)
    d.rectangle([3, 3, 9, 6], fill=(200, 196, 150, 255))               # etiqueta
    img.save(f"{OUT}/lab_cabinet.png")


if __name__ == "__main__":
    camilla()
    wet_floor()
    wet_sign()
    vent()
    airflow()
    lab_cabinet()
    lab_far()
    lab_near()
    lab_floor()
    lab_shelf()
    lab_glass()
    print("OK:", sorted(os.listdir(OUT)))
