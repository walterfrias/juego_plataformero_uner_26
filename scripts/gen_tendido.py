#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_tendido.py  —  Fase 1 del tendido eléctrico: postes + cable.

Arte (game/assets/City/, paleta de palette_night.py):
  - poste.png       18x96   poste de hormigón, cruceta de madera + 2 aisladores.
                            Sirve de ESCALERA (wire_tendido le pone platformType
                            "Ladder"): el player sube/baja por el fuste con ↑/↓.
  - cable_tile.png  32x7    tramo de cable, tileado horizontal (seamless). El
                            objeto `Cable` es un TiledSprite jumpthru: se estira
                            a cualquier ancho por instancia y se camina por la
                            hebra de arriba (canto con luz de luna).

La máscara de colisión del poste (fuste) la pone wire_tendido.py; la del cable
es la caja del TiledSprite (7px de alto), no hace falta máscara custom.

Luz de luna arriba-izquierda (misma convención que gen_trees / gen_costanera).

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_tendido.py
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from palette_night import (  # noqa: E402
    CONCRETE_LIT, CONCRETE_HI, CONCRETE, CONCRETE_DK, CONCRETE_STAIN, FORMLINE,
)

OUT = "game/assets/City"
T = (0, 0, 0, 0)

# --- geometría compartida con wire_tendido.py ---
POSTE_W, POSTE_H = 18, 96
CABLE_TILE_W, CABLE_H = 32, 7

WOOD      = (58, 46, 44, 255)
WOOD_LIT  = (78, 62, 56, 255)
WOOD_DK   = (40, 32, 32, 255)
INSUL     = (150, 156, 168, 255)     # aislador de porcelana, pálido
INSUL_DK  = (96, 102, 118, 255)
WIRE      = (34, 37, 50, 255)        # hebra caminable: se tiene que LEER
WIRE_LIT  = (92, 98, 116, 255)       # canto con luz de luna (lo que se "pisa")
WIRE_DK   = (22, 24, 34, 255)        # panza en sombra


def poste():
    W, H = POSTE_W, POSTE_H
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)
    cx = 9

    # --- fuste de hormigón, apenas cónico (más ancho en la base) ---
    for y in range(6, H):
        t = y / H
        half = 2 + t * 2.2
        x0, x1 = round(cx - half), round(cx + half)
        d.line([(x0, y), (x1, y)], fill=CONCRETE)
        d.point([(x0, y)], fill=CONCRETE_HI)
        d.point([(x0 + 1, y)], fill=CONCRETE_LIT)
        d.point([(x1, y)], fill=CONCRETE_DK)

    d.polygon([(3, H - 8), (W - 3, H - 8), (W - 5, H), (5, H)], fill=CONCRETE_DK)
    d.line([(4, H - 8), (6, H)], fill=CONCRETE_STAIN)

    for jy in (28, 52, 74):
        d.line([(cx - 3, jy), (cx + 3, jy)], fill=FORMLINE)
    for k in range(5):
        d.point([(cx + 1 + (k % 2), 40 + k)], fill=CONCRETE_STAIN)

    # --- cruceta de madera cerca del tope ---
    d.rectangle([1, 11, W - 2, 14], fill=WOOD)
    d.line([(1, 11), (W - 2, 11)], fill=WOOD_LIT)
    d.line([(1, 14), (W - 2, 14)], fill=WOOD_DK)
    d.rectangle([cx - 1, 6, cx + 1, 12], fill=WOOD)

    # --- aisladores en las puntas de la cruceta ---
    for ix in (2, W - 4):
        d.rectangle([ix, 8, ix + 2, 11], fill=INSUL)
        d.point([(ix, 11), (ix + 2, 11)], fill=INSUL_DK)
        d.point([(ix + 1, 7)], fill=INSUL)

    d.rectangle([cx - 2, 4, cx + 2, 6], fill=CONCRETE_HI)
    im.save(f"{OUT}/poste.png")
    print("poste.png", im.size)


def cable_tile():
    W, H = CABLE_TILE_W, CABLE_H
    im = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(im)
    # hebra plana y uniforme -> tilea sin costura
    d.line([(0, 0), (W, 0)], fill=WIRE_LIT)   # canto superior (lo que se pisa)
    d.line([(0, 1), (W, 1)], fill=WIRE)
    d.line([(0, 2), (W, 2)], fill=WIRE)
    d.line([(0, 3), (W, 3)], fill=WIRE_DK)    # panza en sombra
    im.save(f"{OUT}/cable_tile.png")
    print("cable_tile.png", im.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    poste()
    cable_tile()


if __name__ == "__main__":
    main()
