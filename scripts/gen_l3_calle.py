#!/usr/bin/env python3
"""
gen_l3_calle.py  —  piezas nuevas del Nivel 3 (recorrido por el centro y la
arena del Obelisco, 18/10). Casi todo el nivel reusa el kit de L1; esto es
lo poco que faltaba. Lo usa wire_l3_recorrido.py.

Mismo criterio que el resto: Pillow, paleta noche.

Crea (game/assets/City/):
  valla.png          16x16  valla de contención metálica, tileable en Y: la
                            barricada que se cierra detrás de Lio al entrar
                            a la arena
  andamio_tablon.png 64x8   tablón de andamio: reemplaza al estante del lab
                            como plataforma de la arena (mismo tamaño)
  andamio_poste.png   4x8   caño del andamio, tileable en Y: sostiene los
                            tablones (si no, flotarían como las camillas)

Uso:  python3 scripts/gen_l3_calle.py   (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
STEEL_LIT = (128, 136, 150, 255)
STEEL = (86, 92, 106, 255)
STEEL_DK = (46, 50, 62, 255)
SEAM = (22, 24, 32, 255)
BLUE = (60, 96, 160, 255)              # franja de la valla policial
WOOD_LIT = (150, 116, 78, 255)
WOOD = (112, 84, 56, 255)
WOOD_DK = (70, 52, 36, 255)


def valla():
    w, h = 16, 16
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1, h - 1], fill=STEEL_LIT)          # parantes
    d.rectangle([14, 0, 15, h - 1], fill=STEEL_DK)
    for x in range(3, 13, 3):                              # barrotes
        d.line([(x, 0), (x, h - 1)], fill=STEEL)
        d.point((x + 1, 0), fill=STEEL_DK)
    d.rectangle([0, 6, 15, 9], fill=BLUE)                  # franja azul
    d.line([(0, 6), (15, 6)], fill=(110, 150, 210, 255))
    d.line([(0, 9), (15, 9)], fill=SEAM)
    img.save(f"{OUT}/valla.png")


def tablon():
    w, h = 64, 8
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, 4], fill=WOOD)               # tabla (se pisa la fila 0)
    d.line([(0, 0), (w - 1, 0)], fill=WOOD_LIT)
    d.line([(0, 4), (w - 1, 4)], fill=WOOD_DK)
    for x in (9, 23, 41, 55):                              # vetas
        d.line([(x, 2), (x + 4, 2)], fill=WOOD_DK)
    d.rectangle([0, 5, w - 1, 6], fill=STEEL)              # caño horizontal debajo
    d.line([(0, 7), (w - 1, 7)], fill=SEAM)
    for x in (2, w - 6):                                   # abrazaderas
        d.rectangle([x, 4, x + 3, 7], fill=STEEL_LIT)
    img.save(f"{OUT}/andamio_tablon.png")


def poste():
    w, h = 4, 8
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (0, h - 1)], fill=STEEL_LIT)
    d.line([(1, 0), (1, h - 1)], fill=STEEL)
    d.line([(2, 0), (2, h - 1)], fill=STEEL)
    d.line([(3, 0), (3, h - 1)], fill=SEAM)
    img.save(f"{OUT}/andamio_poste.png")


if __name__ == "__main__":
    valla()
    tablon()
    poste()
    print(f"valla, andamio_tablon, andamio_poste  ->  {OUT}/")
