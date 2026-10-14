#!/usr/bin/env python3
"""
gen_borde_plataforma.py  —  borde iluminado de lo que se puede pisar.

Una tira de 8x7 que se estira al ancho del canto de cada plataforma
(wire_bordes_plataforma.py): un poco de resplandor arriba, la línea clara
en la fila 3 (que va justo sobre el canto de la máscara de colisión) y luz
que se apaga hacia abajo. La opacidad la maneja el evento según la
cercanía de Lio.

Crea (game/assets/UI/):
  borde_plataforma.png       8x7 RGBA  ámbar de farol (calle, L1)
  borde_plataforma_lab.png   8x7 RGBA  verde tóxico (laboratorio, L2/L3)

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_borde_plataforma.py
"""
from PIL import Image
import os

OUT = "game/assets/UI"
os.makedirs(OUT, exist_ok=True)

LINE_ROW = 3
# (resplandor, línea, debajo, fondo): ámbar de farol en la calle (L1),
# verde tóxico de los tubos en el laboratorio (L2/L3)
PALETTES = {
    "borde_plataforma.png": ((255, 206, 110), (255, 236, 176), (240, 170, 70), (180, 110, 40)),
    "borde_plataforma_lab.png": ((132, 214, 92), (210, 250, 170), (110, 190, 80), (70, 140, 60)),
}


def strip(glow, line, low, deep):
    rows = [(glow, 20), (glow, 45), (glow, 95), (line, 255), (low, 210), (deep, 90), (deep, 30)]
    im = Image.new("RGBA", (8, len(rows)), (0, 0, 0, 0))
    for y, (c, a) in enumerate(rows):
        for x in range(8):
            im.putpixel((x, y), c + (a,))
    return im


def main():
    for name, pal in PALETTES.items():
        strip(*pal).save(f"{OUT}/{name}")
        print(f"8x7  ->  {OUT}/{name}")


if __name__ == "__main__":
    main()
