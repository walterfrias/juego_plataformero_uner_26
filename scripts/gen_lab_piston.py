#!/usr/bin/env python3
"""
gen_lab_piston.py  —  pistones hidráulicos del Nivel 2 (18/10). Reemplazan a
las camillas que cruzaban los dos pozos anchos: se veían flotando y no eran
divertidas (solo esperar a que llegue). Los pistones salen del fondo del
pozo, suben y bajan desfasados, y hay que saltar de uno a otro a tiempo.
Lo cablea wire_lab_pistones.py.

Mismo criterio que gen_lab.py: Pillow, paleta del lab.

Crea (game/assets/Lab/):
  piston_0.png  40x10  cabezal: placa con franja de peligro arriba y luces
                       verdes; abajo el collar donde entra el vástago
  piston_1.png  40x10  el mismo con las luces en rojo (aviso: está por bajar)
  piston_vastago.png  12x8  vástago cromado, tileable en Y

Uso:  python3 scripts/gen_lab_piston.py   (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/Lab"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
METAL_LIT = (120, 132, 140, 255)          # = gen_lab.py
METAL = (78, 88, 98, 255)
METAL_DK = (44, 50, 58, 255)
SEAM = (16, 25, 30, 255)
HAZ_Y = (196, 164, 44, 255)               # franja de peligro (un poco más viva que la del subsuelo)
HAZ_K = (20, 20, 24, 255)
LED_OK = (120, 230, 120, 255)
LED_WARN = (255, 70, 60, 255)
CHROME_HI = (214, 224, 228, 255)
CHROME = (150, 162, 170, 255)
CHROME_DK = (84, 94, 102, 255)


def cabezal(led):
    w, h = 40, 10
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    # placa (la superficie que se pisa es la fila 0)
    for x in range(w):
        d.line([(x, 0), (x, 1)], fill=HAZ_Y if (x // 4) % 2 == 0 else HAZ_K)
    d.rectangle([0, 2, w - 1, 5], fill=METAL)
    d.line([(0, 2), (w - 1, 2)], fill=METAL_LIT)
    d.line([(0, 5), (w - 1, 5)], fill=METAL_DK)
    for x in (5, 33):                         # luces de estado
        d.rectangle([x, 3, x + 1, 4], fill=led)
    d.point((19, 3), fill=METAL_LIT)          # bulones
    d.point((20, 3), fill=METAL_LIT)
    # collar del cilindro
    d.rectangle([12, 6, 27, 9], fill=METAL_DK)
    d.line([(12, 6), (27, 6)], fill=METAL)
    d.line([(12, 9), (27, 9)], fill=SEAM)
    return img


def vastago():
    w, h = 12, 8
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    cols = [CHROME_DK, CHROME, CHROME_HI, CHROME_HI, CHROME, CHROME, CHROME,
            CHROME, CHROME_DK, CHROME_DK, SEAM, SEAM]
    for x, c in enumerate(cols):
        d.line([(x, 0), (x, h - 1)], fill=c)
    d.point((3, 5), fill=CHROME)              # brillo cortado: se nota que sube y baja
    img.save(f"{OUT}/piston_vastago.png")


if __name__ == "__main__":
    cabezal(LED_OK).save(f"{OUT}/piston_0.png")
    cabezal(LED_WARN).save(f"{OUT}/piston_1.png")
    vastago()
    print(f"piston_0, piston_1, piston_vastago  ->  {OUT}/")
