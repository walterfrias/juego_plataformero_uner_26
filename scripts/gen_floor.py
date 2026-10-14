#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_floor.py  —  textura del cordón caminable de la Costanera.

Mismo hormigón que el muro del malecón (`gen_costanera.py` / `palette_night.py`):
el cordón es una losa de hormigón con el canto iluminado y un labio en sombra.
Puesto arriba del muro se lee como la misma pieza.

Crea:  game/assets/City/sidewalk.png   (32x16, tileable en horizontal)
  - fila 0:     canto del cordón (iluminado)
  - fila 1-2:   cuerpo + labio en sombra
  - resto:      losa de hormigón (speckle + manchas, igual que el muro)
  - juntas verticales en x=0 y x=16  (cadencia de 16 = la del muro)

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_floor.py
"""
from PIL import Image
import random
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palette_night import (  # noqa: E402
    CONCRETE_LIT, CONCRETE_HI, CONCRETE, CONCRETE_DK, CONCRETE_STAIN, FORMLINE,
)

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)

W, H = 32, 16


def main():
    rng = random.Random(42)
    img = Image.new("RGBA", (W, H), CONCRETE)
    px = img.load()

    for y in range(H):
        for x in range(W):
            if y == 0:
                px[x, y] = CONCRETE_LIT          # canto iluminado
            elif y == 1:
                px[x, y] = CONCRETE_HI
            elif y == 2:
                px[x, y] = FORMLINE              # labio en sombra
            else:
                r = rng.random()
                if r < 0.05:
                    px[x, y] = CONCRETE_HI
                elif r < 0.13:
                    px[x, y] = CONCRETE_DK
                else:
                    px[x, y] = CONCRETE

    # juntas verticales (x=0 y x=16 -> tileable, misma cadencia que el muro)
    for jx in (0, 16):
        for y in range(3, H):
            px[jx, y] = FORMLINE
            px[(jx + 1) % W, y] = CONCRETE_DK

    # junta de dilatación horizontal
    for x in range(W):
        px[x, 9] = CONCRETE_DK if rng.random() < 0.5 else FORMLINE

    # un par de manchas de humedad
    for _ in range(3):
        sx = rng.randint(2, W - 3)
        for y in range(rng.randint(4, 8), H):
            if rng.random() < 0.6:
                px[sx, y] = CONCRETE_STAIN

    img.save(f"{OUT}/sidewalk.png")
    print(f"sidewalk.png {img.size}  ->  {OUT}/sidewalk.png")


if __name__ == "__main__":
    main()
