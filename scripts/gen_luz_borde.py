#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_luz_borde.py  —  luz de borde pintada sobre los árboles y faroles que se
pisan (variante B elegida por el usuario el 14/10).

En vez de la barra de wire_bordes_plataforma.py (que en formas orgánicas se
leía como una tabla flotando), una capa del mismo tamaño que el sprite con:
  - los 2 píxeles de arriba de cada canto que mira hacia arriba, aclarados
    hacia el ámbar de farol (75 % / 40 %);
  - un halo cálido semitransparente de 1 px justo encima de la silueta.
Solo dentro de la franja de la máscara de colisión (más 2 px a los lados y
3 abajo): así se ilumina la copa o la cabeza del farol, no el tronco, las
raíces ni la base. La máscara se lee de game/game.json (Level1).

Crea (junto a cada sprite original):
  game/assets/City/ArbolBajo_luz.png, ArbolAlto_luz.png, farol_luz.png

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_luz_borde.py
"""
import json

from PIL import Image

GAME = "game/game.json"
OBJECTS = ("ArbolBajo", "ArbolAlto", "Farol")
WARM = (255, 214, 140)
HOT = (255, 240, 190)
HALO_ALPHA = 110


def out_name(src):
    return src[:-4] + "_luz.png"


def rim(im, band):
    x0, _, x1, y1 = band
    w, h = im.size
    px = im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = out.load()

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and px[x, y][3] > 128

    for y in range(h):
        for x in range(w):
            if not (solid(x, y) and not solid(x, y - 1) and x0 - 2 <= x <= x1 + 2 and y <= y1 + 3):
                continue
            for d, a, mix in ((0, 0.75, HOT), (1, 0.4, WARM)):
                if solid(x, y + d):
                    c = px[x, y + d]
                    o[x, y + d] = tuple(round(c[i] * (1 - a) + mix[i] * a) for i in range(3)) + (255,)
            if y > 0:
                o[x, y - 1] = WARM + (HALO_ALPHA,)
    return out


def sources():
    """{objeto: (archivo, franja x0,y0,x1,y1 de la máscara)} desde Level1."""
    g = json.load(open(GAME, encoding="utf-8"))
    files = {r["name"]: r["file"] for r in g["resources"]["resources"]}
    lay = next(l for l in g["layouts"] if l["name"] == "Level1")
    out = {}
    for o in lay["objects"]:
        if o["name"] not in OBJECTS:
            continue
        f = o["animations"][0]["directions"][0]["sprites"][0]
        pts = [p for poly in f["customCollisionMask"] for p in poly]
        band = (min(p["x"] for p in pts), min(p["y"] for p in pts),
                max(p["x"] for p in pts), max(p["y"] for p in pts))
        out[o["name"]] = (files[f["image"]], band)
    assert set(out) == set(OBJECTS), out.keys()
    return out


def main():
    for name, (src, band) in sources().items():
        im = Image.open("game/" + src).convert("RGBA")
        rim(im, band).save("game/" + out_name(src))
        print(f"{name}: franja {band} -> game/{out_name(src)}")


if __name__ == "__main__":
    main()
