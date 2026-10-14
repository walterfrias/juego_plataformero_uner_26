#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_puentes.py  —  puentes rotos para los pozos de la costanera (post-obelisco).

4 variantes con silueta y mecánica distinta (para que 4 pozos no parezcan
copy-paste) + 1 acento para el hueco grande del río:

  puente_a.png  88x26  tablones con el del medio caído   -> CRUZABLE (saltito)
  puente_b.png  80x20  chapa/puerta improvisada, ladeada  -> CRUZABLE (entera)
  puente_c.png  84x60  sección de vereda colgando + hierros -> deco (no cruzable)
  puente_d.png  92x40  losa volcada hundida en el pozo     -> deco (no cruzable)
  puente_e.png  60x54  tramo de vereda quebrado al río     -> deco (acento río)

La colisión (decks sólidos de A y B, stub de C) la pone wire_puentes.py.
Luz de luna arriba-izquierda (convención de gen_trees / gen_costanera).

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_puentes.py
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from palette_night import (  # noqa: E402
    CONCRETE_HI, CONCRETE, CONCRETE_DK, CONCRETE_STAIN, FORMLINE,
    REBAR, REBAR_HI, RUBBLE, WATER, WATER_HI,
)

OUT = "game/assets/N1"
T = (0, 0, 0, 0)

PLANK      = (66, 56, 50, 255)
PLANK_LIT  = (88, 75, 64, 255)
PLANK_DK   = (42, 35, 32, 255)
METAL      = (74, 80, 92, 255)
METAL_LIT  = (106, 112, 124, 255)
METAL_DK   = (46, 50, 60, 255)
RUST       = (96, 64, 48, 255)


def _outline(im, col=FORMLINE):
    px = im.load()
    w, h = im.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny] != col:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = col


def _planks(d, x0, x1, y0, y1):
    """deck de tablones horizontales entre x0..x1, y0..y1."""
    for py in range(y0, y1):
        c = PLANK_LIT if py == y0 else (PLANK_DK if py == y1 - 1 else PLANK)
        d.line([(x0, py), (x1 - 1, py)], fill=c)
    for sx in range(x0 + 3, x1, 7):                 # juntas entre tablones
        d.line([(sx, y0), (sx, y1 - 1)], fill=PLANK_DK)
    for sx in range(x0 + 1, x1, 7):                 # cabezas de clavo
        d.point([(sx, y0 + 1)], fill=PLANK_LIT)


def puente_a():
    """Tablones, falta el del medio. Deck izq x0..32, der x52..88, hueco 20px."""
    W, H = 88, 26
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)
    gap0, gap1 = 32, 52

    # largueros que cruzan el vacío (se ven en el hueco)
    for by in (9, 13):
        d.line([(4, by), (W - 4, by)], fill=CONCRETE_DK)
        d.line([(4, by + 1), (W - 4, by + 1)], fill=FORMLINE)

    _planks(d, 0, gap0, 0, 8)
    _planks(d, gap1, W, 0, 8)

    # tablón roto colgando del borde derecho del hueco
    d.line([(gap1, 7), (gap1 - 9, 18)], fill=PLANK)
    d.line([(gap1 + 1, 7), (gap1 - 8, 18)], fill=PLANK_DK)
    d.point([(gap1 - 9, 18), (gap1 - 9, 19)], fill=PLANK_LIT)

    # patas de apoyo (cortas) cerca de los bordes de tierra
    for sx in (3, W - 5):
        d.line([(sx, 8), (sx, H - 2)], fill=CONCRETE_DK)
        d.line([(sx + 1, 8), (sx + 1, H - 6)], fill=FORMLINE)
    # hierros sueltos en el filo izquierdo del hueco
    d.line([(gap0, 6), (gap0 + 5, 0)], fill=REBAR)
    d.line([(gap0 - 1, 6), (gap0 + 2, 1)], fill=REBAR_HI)

    im.save(f"{OUT}/puente_a.png")
    print("puente_a.png", im.size)


def puente_b():
    """Chapa acanalada ladeada, apoyada en un cascote a la izquierda."""
    W, H = 80, 20
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)

    # cascote de apoyo (izq)
    d.rectangle([0, 6, 9, H - 1], fill=CONCRETE_DK)
    d.rectangle([0, 6, 9, 7], fill=CONCRETE_HI)
    d.line([(0, 12), (9, 12)], fill=FORMLINE)

    # chapa: leve caída de izq (y3) a der (y7)
    for x in range(2, W):
        top = 3 + round(4 * x / W)
        d.line([(x, top), (x, top + 6)], fill=METAL)
        d.point([(x, top)], fill=METAL_LIT)
        d.point([(x, top + 6)], fill=METAL_DK)
        if x % 3 == 0:                               # acanalado
            d.line([(x, top), (x, top + 6)], fill=METAL_DK)
    # óxido + agujeros
    rng = random.Random(7)
    for _ in range(5):
        rx = rng.randint(6, W - 4)
        ry = 3 + round(4 * rx / W) + rng.randint(0, 5)
        d.point([(rx, ry), (rx + 1, ry)], fill=RUST)
    for hx in (18, 46):
        hy = 3 + round(4 * hx / W) + 3
        d.point([(hx, hy)], fill=WATER)
        d.point([(hx + 1, hy + 1)], fill=WATER_HI)

    im.save(f"{OUT}/puente_b.png")
    print("puente_b.png", im.size)


def puente_c():
    """Sección de vereda colgando vertical por los hierros, del borde izq."""
    W, H = 84, 60
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)
    rng = random.Random(13)

    # stub de deck a la izquierda (lo único pisable)
    d.rectangle([0, 52, 16, 59], fill=CONCRETE)
    d.line([(0, 52), (16, 52)], fill=CONCRETE_HI)
    d.line([(0, 59), (16, 59)], fill=FORMLINE)

    # losa colgando (rotada ~90°), pende hacia el pozo
    sx = 18
    for yy in range(10, 50):
        off = round(0.14 * (yy - 10))
        d.line([(sx + off, yy), (sx + off + 11, yy)], fill=CONCRETE
               if (yy % 5) else CONCRETE_STAIN)
        d.point([(sx + off, yy)], fill=CONCRETE_HI)
        d.point([(sx + off + 11, yy)], fill=CONCRETE_DK)
    d.line([(sx + 3, 12), (sx + 9, 46)], fill=FORMLINE)     # fisura

    # hierros retorcidos que sostienen la losa
    for k in range(4):
        x0, y0 = 15 + k, 52
        x1, y1 = sx + 2 + k * 3, 12 + k * 2
        d.line([(x0, y0), ((x0 + x1) // 2 - 2, (y0 + y1) // 2), (x1, y1)],
               fill=REBAR_HI if k % 2 else REBAR)

    # borde derecho: labio desmoronado + hierros parados
    for x in range(60, W):
        peak = int(H - 6 - 20 * math.sin(math.pi * (x - 60) / (W - 60)) + rng.randint(-2, 2))
        for y in range(max(0, peak), H):
            d.point([(x, y)], fill=RUBBLE if rng.random() > 0.15 else CONCRETE_STAIN)
    for bx in range(62, W, 4):
        h = rng.randint(10, 20)
        d.line([(bx, H - 8), (bx + rng.randint(-2, 2), H - 8 - h)], fill=REBAR)
        d.point([(bx, H - 8 - h)], fill=REBAR_HI)

    _outline(im)
    im.save(f"{OUT}/puente_c.png")
    print("puente_c.png", im.size)


def puente_d():
    """Losa de la vereda partida y volcada dentro del pozo: una plancha grande
    inclinada, hundida ~14px bajo el cordón, con montones de cascote a ras en
    los dos bordes. Nada sobresale del cordón -> no se cruza ni tapa el salto."""
    W, H = 92, 40
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)
    rng = random.Random(23)

    # plancha volcada: rectángulo grueso, ladeado, hundido en el pozo
    slab = [(16, 20), (74, 12), (80, 22), (22, 30)]
    d.polygon(slab, fill=CONCRETE)
    d.line([(16, 20), (74, 12)], fill=CONCRETE_HI)              # canto con luz
    d.line([(22, 30), (80, 22)], fill=CONCRETE_DK)              # canto en sombra
    for k in range(4):                                          # nervios / fisuras
        d.line([(24 + k * 14, 15 + k), (28 + k * 14, 29)], fill=FORMLINE)
    for _ in range(12):                                         # textura de hormigón
        tx, ty = rng.randint(20, 76), rng.randint(14, 28)
        d.point([(tx, ty)], fill=CONCRETE_STAIN if rng.random() < .5 else CONCRETE_HI)

    # montones de cascote a ras del cordón en los dos labios
    for x0, x1 in ((0, 24), (W - 24, W)):
        for x in range(x0, x1):
            base = 0 if x0 == 0 else 0
            peak = base + rng.randint(0, 3)
            for y in range(peak, peak + rng.randint(8, 13)):
                if y < H:
                    d.point([(x, y)], fill=RUBBLE if rng.random() > 0.12 else CONCRETE_HI)

    # hierros doblados asomando de los escombros, hacia arriba/afuera
    for bx in list(range(6, 22, 5)) + list(range(W - 20, W - 4, 5)):
        h = rng.randint(7, 13)
        tipx = bx + rng.choice((-3, -2, 2, 3))
        d.line([(bx, 8), (tipx, 8 - h)], fill=REBAR)
        d.point([(tipx, 8 - h)], fill=REBAR_HI)

    # agua entrevista bajo la plancha
    for _ in range(14):
        wx, wy = rng.randint(24, W - 24), rng.randint(H - 7, H - 1)
        d.point([(wx, wy)], fill=WATER_HI if rng.random() < .4 else WATER)

    _outline(im)
    im.save(f"{OUT}/puente_d.png")
    print("puente_d.png", im.size)


def puente_e():
    """Tramo de vereda quebrado, colgando en diagonal hacia el río. Acento
    para el borde izq del hueco grande."""
    W, H = 60, 54
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)
    rng = random.Random(29)

    # el tramo: cuña que baja de (2,4) a (44,44)
    for i in range(0, 44):
        x = 2 + i
        yt = 4 + round(0.92 * i)
        d.line([(x, yt), (x, yt + 9)], fill=CONCRETE if (i % 5) else CONCRETE_STAIN)
        d.point([(x, yt)], fill=CONCRETE_HI)
        d.point([(x, yt + 9)], fill=CONCRETE_DK)
    # tablones sueltos encima
    for i in range(2, 40, 6):
        x = 2 + i
        yt = 4 + round(0.92 * i)
        d.line([(x, yt - 1), (x + 4, yt - 1 + 4)], fill=PLANK)
        d.point([(x, yt - 1)], fill=PLANK_LIT)
    # hierros que todavía lo atan arriba
    for k in range(3):
        d.line([(2, 3 + k * 2), (10 + k * 3, -1)], fill=REBAR_HI if k else REBAR)
    # salpicadura donde toca el agua
    for _ in range(8):
        sx, sy = rng.randint(40, 52), rng.randint(H - 8, H - 1)
        d.point([(sx, sy)], fill=WATER_HI)

    _outline(im)
    im.save(f"{OUT}/puente_e.png")
    print("puente_e.png", im.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    puente_a()
    puente_b()
    puente_c()
    puente_d()
    puente_e()


if __name__ == "__main__":
    main()
