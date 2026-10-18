#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportMissingImports=false
"""
gen_l3_siluetas.py  —  siluetas para la multitud de fondo del Nivel 3 (18/10).
Primero eran los mismos sprites de los zombies teñidos de oscuro y competían con
los zombies jugables ("habría que sacarle algo de detalle a los zombies de
fondo"). Ahora cada cuadro de la caminata se convierte en una forma plana:

  - todo lo opaco → un solo tono oscuro y frío;
  - borde de luz de 1 px donde arriba o a la izquierda hay vacío (la luna);
  - los ojos rojos se conservan, apagados (en la oscuridad inquietan).

Lee los cuadros reales de cada tipo (los que usa game/game.json), así la forma y
la animación son exactamente las del zombie. Crea game/assets/Siluetas/
silueta_<cuadro original>.png. Lo cablea wire_l3_recorrido.py (FONDO).
Uso:  python3 scripts/gen_l3_siluetas.py
"""
import json
import os

from PIL import Image

import l3_recorrido as R

GAME = "game/game.json"
OUT = "game/assets/Siluetas"
BODY = (32, 36, 52, 255)
RIM = (60, 66, 88, 255)
EYE_SRC = (214, 74, 74)          # ojos de los zombies del juego
EYE = (150, 46, 50, 255)
ORIGEN = {"ZombieJ": "ZombieEnd1"}   # como en wire_l3_recorrido.ZOMBIES_L1


def silueta(src):
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    sp = im.load()
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = out.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            if (r, g, b) == EYE_SRC:
                px[x, y] = EYE
            elif (y == 0 or sp[x, y - 1][3] == 0) or (x == 0 or sp[x - 1, y][3] == 0):
                px[x, y] = RIM
            else:
                px[x, y] = BODY
    return out


def frames_of(game, name):
    """imágenes de la animación Walk del objeto (buscado en L1/L2)."""
    res = {r["name"]: r["file"] for r in game["resources"]["resources"]}
    for lay in game["layouts"]:
        for o in lay["objects"]:
            if o["name"] == ORIGEN.get(name, name):
                walk = next(a for a in o["animations"] if a["name"] == "Walk")
                return [res[s["image"]] for s in walk["directions"][0]["sprites"]]
    raise KeyError(name)


def main():
    os.makedirs(OUT, exist_ok=True)
    g = json.load(open(GAME))
    n = 0
    for t in sorted({t for t, *_ in R.FONDO}):
        for f in frames_of(g, t):
            silueta(f"game/{f}").save(f"{OUT}/silueta_{os.path.basename(f)}")
            n += 1
    print(f"{n} cuadros de silueta  ->  {OUT}/")


if __name__ == "__main__":
    main()
