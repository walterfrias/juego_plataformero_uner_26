#!/usr/bin/env python3
"""
slice_spritesheet.py  —  corta un spritesheet (tira de frames) en PNGs sueltos.

GDevelop puede importar un spritesheet directo (con Piskel integrado),
pero tener los frames sueltos es mas comodo para editar y versionar.

Tech: Python 3 + Pillow.

Uso:
  python3 scripts/slice_spritesheet.py ENTRADA.png ANCHO ALTO PREFIJO_SALIDA

Ejemplo (lo que se uso para el zombie):
  python3 scripts/slice_spritesheet.py \\
      game/assets/Big_Zombie/zombie1.png 32 32 \\
      game/assets/Big_Zombie/Big_Zombie_Walk_

  -> Big_Zombie_Walk_1.png ... Big_Zombie_Walk_N.png

Los frames salen en el mismo modo (idealmente RGBA con fondo
transparente: si tu export de Pixaki trae fondo blanco, borra la capa
de fondo en el proyecto y volve a exportar).
"""
import sys
from PIL import Image


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    src_path, fw, fh, prefix = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    src = Image.open(src_path).convert("RGBA")
    W, H = src.size
    if W % fw or H % fh:
        print(f"aviso: {W}x{H} no es multiplo exacto de {fw}x{fh}")
    cols, rows = W // fw, H // fh
    n = 0
    for r in range(rows):
        for c in range(cols):
            n += 1
            box = (c * fw, r * fh, c * fw + fw, r * fh + fh)
            src.crop(box).save(f"{prefix}{n}.png")
            print(f"  {prefix}{n}.png  {fw}x{fh}")
    alpha = src.getchannel("A")
    if alpha.getextrema()[0] == 255:
        print("OJO: la imagen no parece tener transparencia (fondo opaco).")


if __name__ == "__main__":
    main()
