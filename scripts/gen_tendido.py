#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_tendido.py  —  Fase 1 del tendido eléctrico: postes + cable.

Arte (game/assets/City/, paleta de palette_night.py):
  - poste.png       18x96   poste de hormigón, cruceta de madera + 2 aisladores.
                            Sirve de ESCALERA (wire_tendido le pone platformType
                            "Ladder"): el player sube/baja por el fuste con ↑/↓.
  - poste_alto.png  18x152  el mismo, POSTE_ALTO_SUBE px más alto, con una segunda
                            cruceta para el 2.º tramo (28/10, primer tramo de L1:
                            fix_n1_tendido_alto.py).
  - poste_medio.png 18x114  TRAMO2_SUBE px más alto, con una segunda cruceta a la
                            altura del común (28/10, entre el 2.º y el 3.º tramo).
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
POSTE_ALTO_SUBE = 56                 # poste alto (fix_n1_tendido_alto.py): 96 + 56 = 152
TRAMO2_SUBE = 18                     # el 2.º tramo de L1, por arriba del árbol: poste medio 96 + 18
CABLE_TILE_W, CABLE_H = 32, 7

WOOD      = (58, 46, 44, 255)
WOOD_LIT  = (78, 62, 56, 255)
WOOD_DK   = (40, 32, 32, 255)
INSUL     = (150, 156, 168, 255)     # aislador de porcelana, pálido
INSUL_DK  = (96, 102, 118, 255)
WIRE      = (34, 37, 50, 255)        # hebra caminable: se tiene que LEER
WIRE_LIT  = (92, 98, 116, 255)       # canto con luz de luna (lo que se "pisa")
WIRE_DK   = (22, 24, 34, 255)        # panza en sombra


def cruceta(d, W, cx, y):
    """cruceta de madera con un aislador en cada punta; y = canto de arriba."""
    d.rectangle([1, y, W - 2, y + 3], fill=WOOD)
    d.line([(1, y), (W - 2, y)], fill=WOOD_LIT)
    d.line([(1, y + 3), (W - 2, y + 3)], fill=WOOD_DK)
    d.rectangle([cx - 1, y - 5, cx + 1, y + 1], fill=WOOD)
    for ix in (2, W - 4):
        d.rectangle([ix, y - 3, ix + 2, y], fill=INSUL)
        d.point([(ix, y), (ix + 2, y)], fill=INSUL_DK)
        d.point([(ix + 1, y - 4)], fill=INSUL)


def dibujar_poste(H, sube=0, baja=None):
    """fuste de H px. `sube` > 0: poste más alto que el común, con otra cruceta `baja` px
    más abajo que la de arriba (para el cable que sigue; por defecto, a la altura de un
    poste común)."""
    baja = sube if baja is None else baja
    W = POSTE_W
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
        d.line([(cx - 3, jy + sube), (cx + 3, jy + sube)], fill=FORMLINE)
    for k in range(5):
        d.point([(cx + 1 + (k % 2), 40 + sube + k)], fill=CONCRETE_STAIN)
    if sube:
        if sube >= 28:
            d.line([(cx - 3, 30), (cx + 3, 30)], fill=FORMLINE)    # junta del tramo de más
        cruceta(d, W, cx, 11 + baja)

    cruceta(d, W, cx, 11)
    d.rectangle([cx - 2, 4, cx + 2, 6], fill=CONCRETE_HI)
    return im


def poste():
    im = dibujar_poste(POSTE_H)
    im.save(f"{OUT}/poste.png")
    print("poste.png", im.size)


def poste_alto():
    """28/10: el primer tramo del tendido de L1 sube POSTE_ALTO_SUBE px (rebotando en
    los zombies de antes, Lio caía arriba y se salteaba el antídoto de abajo). La cruceta
    de abajo, para el 2.º tramo, que también subió TRAMO2_SUBE."""
    im = dibujar_poste(POSTE_H + POSTE_ALTO_SUBE, POSTE_ALTO_SUBE, POSTE_ALTO_SUBE - TRAMO2_SUBE)
    im.save(f"{OUT}/poste_alto.png")
    print("poste_alto.png", im.size)


def poste_medio():
    """28/10: el 2.º tramo del tendido de L1 sube TRAMO2_SUBE px, por arriba de la copa del
    árbol alto (antes pasaba justo a la altura de la copa). Arriba ese cable; la cruceta
    de abajo, a la altura de un poste común, para el 3.º tramo."""
    im = dibujar_poste(POSTE_H + TRAMO2_SUBE, TRAMO2_SUBE)
    im.save(f"{OUT}/poste_medio.png")
    print("poste_medio.png", im.size)


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
    poste_alto()
    poste_medio()
    cable_tile()


if __name__ == "__main__":
    main()
