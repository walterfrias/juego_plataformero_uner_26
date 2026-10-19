#!/usr/bin/env python3
"""
wire_grafitis_n1.py — pone en el muro de la costanera de Level1 las pintadas
de gen_grafitis_n1.py (19/10, pedido del usuario: "no se ven los grafitis";
el generador estaba pero nadie las cableaba al juego).

Un Sprite por pintada (Grafiti<Nombre>), en la capa "" a z -2: delante del
muro (Embankment, z -3) y a la par del río (empieza en y 178, debajo de todas).
Lleva el mismo efecto Adjustment "Noche" del muro (brillo 0.62), así la pintura
queda en la misma sombra que el hormigón. Posición: x/y de PINTADAS.

Idempotente (reemplaza sus objetos e instancias). GDevelop CERRADO.
Requiere: gen_grafitis_n1.py
Uso:  python3 scripts/wire_grafitis_n1.py   (desde la raíz del repo)
"""
import datetime
import json
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado
from gen_grafitis_n1 import PINTADAS
from wire_lab_luces import inst, sprite
from wire_noche_n1 import adjustment, res_image
from wire_score_hud import put_object

GAME = "game/game.json"
SCENE = "Level1"
CITY = "assets/City"
Z = -2
NOCHE = adjustment(brightness=0.62, saturation=0.8, contrast=1.0)   # el del Embankment


def nombre_objeto(png):
    """grafiti_malvinas -> GrafitiMalvinas"""
    return "Grafiti" + png.split("_", 1)[1].capitalize()


def main():
    asegurar_gdevelop_cerrado()
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    res = g["resources"]["resources"]
    lay = next(l for l in g["layouts"] if l["name"] == SCENE)
    mios = {nombre_objeto(n) for n in PINTADAS}
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in mios]
    for png, p in PINTADAS.items():
        res_image(res, png + ".png", f"{CITY}/{png}.png")
        o = sprite(nombre_objeto(png), png + ".png")
        o["effects"] = [dict(NOCHE)]
        put_object(lay, o)
        lay["instances"].append(inst(o["name"], p["x"], p["y"], Z, ""))
        print(f"{o['name']}: x {p['x']}, y {p['y']}")
    json.dump(g, open(GAME, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
