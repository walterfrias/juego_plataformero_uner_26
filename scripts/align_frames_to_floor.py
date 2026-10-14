#!/usr/bin/env python3
"""
align_frames_to_floor.py  —  empareja la altura de unos frames y pega los
"pies" del contenido al borde inferior, para que el sprite apoye en el piso.

Por que existe: los frames dibujados a mano salieron 32x32, pero los del
pack CC0 (Big Zombie Idle/Run) son 32x34 con los pies en y=34. Puestos a
la misma Y, el sprite de 32 quedaba flotando ~3px. Este script agranda el
canvas a la altura objetivo y baja el contenido hasta que toque el fondo.

Tech: Python 3 + Pillow.

Uso:
  python3 scripts/align_frames_to_floor.py ALTO_OBJETIVO frame1.png [frame2.png ...]

Ejemplo (lo que se uso para el zombie walk):
  python3 scripts/align_frames_to_floor.py 34 \\
      game/assets/Big_Zombie/Big_Zombie_Walk_*.png

Sobrescribe cada archivo in-place. Hace copia .bak-align al lado.
"""
import sys
import shutil
from PIL import Image


def align(path, target_h):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    bbox = im.getbbox()                      # caja del contenido no transparente
    if bbox is None:
        print(f"  {path}: vacio, salteado")
        return
    content_bottom = bbox[3]
    canvas = Image.new("RGBA", (w, target_h), (0, 0, 0, 0))
    # desplazamiento vertical para que el contenido termine en target_h
    dy = target_h - content_bottom
    canvas.alpha_composite(im, (0, dy))
    canvas = canvas.crop((0, 0, w, target_h))
    shutil.copy(path, path + ".bak-align")
    canvas.save(path)
    out_bbox = canvas.getbbox()
    feet = out_bbox[3] if out_bbox else target_h
    print(f"  {path}: {w}x{h} -> {w}x{target_h}  (contenido bajado {dy}px, "
          f"pies en y={feet})")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    target_h = int(sys.argv[1])
    for p in sys.argv[2:]:
        align(p, target_h)


if __name__ == "__main__":
    main()
