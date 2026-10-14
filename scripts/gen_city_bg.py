#!/usr/bin/env python3
"""
gen_city_bg.py  —  fondo de ciudad nocturna placeholder (tileable) + Obelisco.

Qué crea:
  - assets/City/city_farthest.png 224x60 : skyline más lejano (bruma, pocas
                                 ventanas) para el parallax de Level1 (14/10)
  - assets/City/city_far.png   224x70  : skyline lejano (edificios claros/hazy)
  - assets/City/city_near.png  224x96  : skyline cercano (siluetas oscuras)
  - assets/City/obelisco.png   18x122  : Obelisco de Buenos Aires (landmark)

Cómo funciona el tileado ("empalme" sin costura):
  cada edificio y cada ventana que cruza el borde derecho se vuelve a
  dibujar en x - ANCHO (y en x + ANCHO). Así la columna del borde
  izquierdo queda idéntica a la del borde derecho y la textura se puede
  repetir horizontalmente sin que se vea el corte.

Tech: Python 3 + Pillow.
Uso:  python3 scripts/gen_city_bg.py      (desde la raíz del repo)

Nota: el color de fondo de la escena se setea aparte en game.json
(layout.r / .v / .b = 16,20,40, azul noche).

Para reemplazar por arte propio: dibujá tiras tileables en Pixaki con
estas medidas, mismo nombre de archivo, y no hace falta tocar game.json.
"""
from PIL import Image, ImageDraw
import random
import os

W = 224
OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)


def make_skyline(fname, height, bcol, edge, wcol, wdim, wprob,
                 seed, minw, maxw, minh, maxh):
    rng = random.Random(seed)
    img = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def building(bx, bw, bh):
        top = height - bh
        for dx in (0, -W, W):                     # wraparound -> tileable
            d.rectangle([bx + dx, top, bx + dx + bw - 1, height - 1], fill=bcol)
            d.line([(bx + dx, top), (bx + dx + bw - 1, top)], fill=edge)
        for wy in range(top + 3, height - 2, 4):
            for wx in range(bx + 2, bx + bw - 2, 3):
                if rng.random() < wprob:
                    c = wcol if rng.random() > 0.4 else wdim
                    for dx in (0, -W, W):
                        d.point([(wx + dx, wy)], fill=c)
                        if rng.random() < 0.35:
                            d.point([(wx + dx, wy + 1)], fill=c)

    x = -rng.randint(0, maxw)
    while x < W:
        bw = rng.randint(minw, maxw)
        bh = rng.randint(minh, maxh)
        building(x, bw, bh)
        x += bw - rng.randint(0, 3)
    img.save(f"{OUT}/{fname}")
    return img


def make_obelisco():
    oh, ow = 122, 18
    ob = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
    d = ImageDraw.Draw(ob)
    pale = (210, 216, 234, 255)
    lit = (232, 236, 248, 255)
    shade = (150, 158, 192, 255)
    dark = (88, 94, 122, 255)
    cx = ow // 2
    base_h = 7
    d.rectangle([cx - 5, oh - base_h, cx + 4, oh - 1], fill=shade)
    d.rectangle([cx - 5, oh - base_h, cx + 4, oh - base_h + 1], fill=pale)
    d.line([(cx - 5, oh - base_h), (cx - 5, oh - 1)], fill=pale)

    shaft_bottom, shaft_top = oh - base_h, 12
    for y in range(shaft_top, shaft_bottom):
        t = (y - shaft_top) / (shaft_bottom - shaft_top)
        hw = 2.0 + 2.2 * t
        L, R = int(round(cx - hw)), int(round(cx + hw))
        d.line([(L, y), (R, y)], fill=pale)
        d.point([(L, y)], fill=lit)
        d.point([(R, y)], fill=shade)
    for k, y in enumerate(range(shaft_top - 5, shaft_top)):     # pyramidion
        hw = min(2, k)
        d.line([(cx - hw, y), (cx + hw, y)], fill=pale)
        d.point([(cx + hw, y)], fill=shade)
    d.point([(cx, shaft_top - 6)], fill=lit)
    for wy in (shaft_top + 5, shaft_top + 8):
        d.point([(cx - 1, wy)], fill=dark)
        d.point([(cx + 1, wy)], fill=dark)
    ob.save(f"{OUT}/obelisco.png")
    return ob


if __name__ == "__main__":
    far = make_skyline("city_far.png", 70, (46, 52, 88, 255), (60, 68, 108, 255),
                       (255, 214, 130, 255), (150, 120, 70, 255), 0.30,
                       seed=7, minw=14, maxw=30, minh=26, maxh=58)
    near = make_skyline("city_near.png", 96, (26, 29, 54, 255), (40, 44, 74, 255),
                        (255, 226, 150, 255), (120, 90, 50, 255), 0.15,
                        seed=23, minw=20, maxw=42, minh=44, maxh=90)
    # va detrás de city_far: más chico, color entre el cielo (16,20,40) y far
    farthest = make_skyline("city_farthest.png", 60, (32, 38, 68, 255), (40, 47, 82, 255),
                            (200, 170, 110, 255), (90, 80, 70, 255), 0.07,
                            seed=41, minw=8, maxw=20, minh=16, maxh=50)
    ob = make_obelisco()
    print(f"city_farthest.png {farthest.size}")
    print(f"city_far.png  {far.size}")
    print(f"city_near.png {near.size}")
    print(f"obelisco.png  {ob.size}")
