#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_bloques_hormigon.py  —  2 variantes de BLOQUE DE HORMIGON CON HIERROS,
pensadas como plataforma suelta para clonar y ubicar en puntos estrategicos
(losa reventada de la costanera / escombro de edificio).

Mismo hormigon que el cordon y el muro del malecon (`palette_night.py`): canto
superior iluminado por la luna + labio en sombra abajo, para que apoyado en
cualquier nivel se lea como "un pedazo del mundo que se cayo". Los hierros
salen por los COSTADOS y por abajo (nunca hacia arriba): la cara de arriba
queda limpia y plana para pisar.

Genera en game/assets/City/:
  BloqueHormigon_A.png   36x16  — losa ancha, corte limpio a la izquierda y
                                  punta reventada a la derecha con 3 hierros
                                  doblados saliendo en horizontal. Superficie
                                  landable = toda la cara de arriba del cuerpo
                                  de hormigon (x2..x33, y0..y1).
  BloqueHormigon_B.png   26x18  — cacho mas macizo, reventado de los dos lados
                                  (2 hierros por lado, apenas caidos) y una
                                  fisura fina en diagonal. Lee como trozo colgado
                                  en el aire. Superficie landable = cara de arriba
                                  del cuerpo (x3..x22, y0..y1).

Solo el cuerpo de hormigon lleva colision (el wire pone mascara custom en esa
franja); los hierros son dibujo, el player pasa por delante.
Pie al ras del borde inferior: se coloca con  y = alturaPiso - altoSprite.

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_bloques_hormigon.py
"""
from PIL import Image, ImageDraw
import random
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palette_night import (  # noqa: E402
    CONCRETE_LIT, CONCRETE_HI, CONCRETE, CONCRETE_DK, CONCRETE_STAIN, FORMLINE,
    REBAR, REBAR_HI, REBAR_DK,
)

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)

OUTL = (18, 22, 28, 255)


def _outline(img, col=OUTL):
    px = img.load()
    w, h = img.size
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


def _img(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _concrete_body(d, px, rng, x0, y0, x1, y1):
    """Losa de hormigon: relleno + speckle + canto iluminado arriba y labio
    en sombra abajo. Mismas reglas que gen_floor.py."""
    d.rectangle([x0, y0, x1, y1], fill=CONCRETE)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            r = rng.random()
            if r < 0.06:
                px[x, y] = CONCRETE_HI
            elif r < 0.14:
                px[x, y] = CONCRETE_DK
    d.line([(x0, y0), (x1, y0)], fill=CONCRETE_LIT)          # canto iluminado (luna)
    d.line([(x0, y0 + 1), (x1, y0 + 1)], fill=CONCRETE_HI)
    d.line([(x0, y1), (x1, y1)], fill=FORMLINE)              # labio en sombra
    d.line([(x0, y1 - 1), (x1, y1 - 1)], fill=CONCRETE_DK)
    # un par de manchas de humedad
    for _ in range(2):
        sx = rng.randint(x0 + 1, x1 - 1)
        for y in range(rng.randint(y0 + 2, y1 - 1), y1 + 1):
            if rng.random() < 0.6:
                px[sx, y] = CONCRETE_STAIN


def _rebar_h(d, x_from, x_to, y, curl=0):
    """Hierro horizontal de x_from a x_to (x_to puede ser < x_from). Si curl!=0
    la punta se dobla curl px en vertical."""
    step = 1 if x_to >= x_from else -1
    d.line([(x_from, y), (x_to, y)], fill=REBAR)
    d.line([(x_from, y - 1), (x_to - step, y - 1)], fill=REBAR_HI)   # brillo de oxido arriba
    d.point([(x_from, y + 1), (x_from + step, y + 1)], fill=REBAR_DK)
    if curl:
        cy = y
        for _ in range(abs(curl)):
            cy += 1 if curl > 0 else -1
            d.point([(x_to, cy)], fill=REBAR)
        d.point([(x_to, cy)], fill=REBAR_HI)


def bloque_a():
    w, h = 36, 16
    im, d = _img(w, h)
    px = im.load()
    rng = random.Random(11)

    # cuerpo: corte limpio a la izq, la derecha la comemos con jag despues
    _concrete_body(d, px, rng, 2, 0, 33, h - 1)

    # linea de encofrado vertical (junta) a 1/3
    for y in range(1, h - 1):
        px[13, y] = FORMLINE
        px[14, y] = CONCRETE_DK

    # --- punta reventada a la derecha: la losa se troncha en diagonal
    #     (arriba queda mas larga que abajo) con dientes irregulares ---
    jag = [(34, 0), (33, 1), (34, 2), (32, 3), (33, 4), (31, 5), (30, 6),
           (32, 7), (29, 8), (30, 9), (28, 10), (29, 11), (27, 12), (28, 13),
           (26, 14), (27, 15)]
    for jx, jy in jag:
        for x in range(jx, w):
            px[x, jy] = (0, 0, 0, 0)
    # cascotitos sueltos cerca del quiebre
    for cx, cy in ((30, 3), (26, 13), (28, 6)):
        if px[cx, cy][3]:
            px[cx, cy] = CONCRETE_DK

    # --- hierros saliendo de la punta rota (arrancan dentro del hormigon) ---
    _rebar_h(d, 25, 35, 3, curl=2)
    _rebar_h(d, 24, 34, 8)
    _rebar_h(d, 23, 32, 13, curl=-2)

    # sombra proyectada bajo la losa (leve), solo tramo entero
    d.line([(3, h - 1), (12, h - 1)], fill=OUTL)

    _outline(im)
    im.save(f"{OUT}/BloqueHormigon_A.png")
    return im


def bloque_b():
    w, h = 26, 18
    im, d = _img(w, h)
    px = im.load()
    rng = random.Random(23)

    # cuerpo macizo centrado (x3..x22), los costados se mordisquean con jag
    _concrete_body(d, px, rng, 3, 0, 22, h - 1)

    # --- reventado de los dos lados: mordidas chicas (1-2 px) ---
    jag_l = [(3, 1), (4, 2), (3, 4), (4, 6), (3, 7), (4, 9), (3, 11), (4, 12),
             (3, 14), (4, 16)]
    for jx, jy in jag_l:
        for x in range(0, jx):
            px[x, jy] = (0, 0, 0, 0)
    jag_r = [(22, 1), (21, 3), (22, 5), (21, 6), (22, 8), (21, 10), (22, 12),
             (21, 13), (22, 15), (21, 17)]
    for jx, jy in jag_r:
        for x in range(jx + 1, w):
            px[x, jy] = (0, 0, 0, 0)

    # --- fisura fina en diagonal (hairline, no la atraviesa) ---
    for i, fy in enumerate(range(3, h - 3)):
        fx = 9 + i // 3
        if px[fx, fy][3]:
            px[fx, fy] = FORMLINE

    # cascotitos junto a los quiebres
    for cx, cy in ((6, 3), (18, 14), (7, 12), (17, 6)):
        if px[cx, cy][3]:
            px[cx, cy] = CONCRETE_DK

    # --- hierros: 2 por lado, apenas caidos ---
    _rebar_h(d, 6, -2, 3, curl=2)
    _rebar_h(d, 5, -1, 12, curl=1)
    _rebar_h(d, 19, 27, 5, curl=2)
    _rebar_h(d, 20, 26, 14, curl=1)

    _outline(im)
    im.save(f"{OUT}/BloqueHormigon_B.png")
    return im


def main():
    a = bloque_a()
    b = bloque_b()
    # hoja de contacto
    sheet = Image.new("RGBA", (a.width + b.width + 18, max(a.height, b.height) + 8),
                      (16, 20, 40, 255))
    sheet.alpha_composite(a, (6, 6))
    sheet.alpha_composite(b, (a.width + 12, 6))
    sheet.save(f"{OUT}/_bloques_contact.png")
    print(f"BloqueHormigon_A {a.size}  |  BloqueHormigon_B {b.size}  ->  {OUT}/")
    print("  landable: cara de arriba del cuerpo de hormigon (A: x2-33 y0-1 / B: x3-22 y0-1)")
    print("  hierros = solo dibujo, sin colision")


if __name__ == "__main__":
    assert os.path.isdir("game/assets"), "corré desde la raíz del repo"
    main()
