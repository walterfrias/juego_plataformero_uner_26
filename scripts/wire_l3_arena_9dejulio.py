#!/usr/bin/env python3
"""
wire_l3_arena_9dejulio.py — la arena del Nivel 3 como la 9 de Julio (25/10,
cambios cosméticos pedidos por el usuario; la pelea no cambia):

  - ObeliscoGrande más chico ("está muy grande, se ve muy cerca"): se reubica
    según el tamaño de obelisco_cerca.png (36x132, OB_ESCALA en gen_l3_calle.py),
    con el mismo centro y la base en el piso.
  - EdificioEvita (edificio_evita.png, gen_l3_evita.py): detrás del Obelisco a la
    derecha, la torre crema del ex Ministerio de Obras Públicas con el mural de
    Evita. Sprite quieto en BG_city, delante de las dos filas de edificios (z 15;
    las filas y sus incendios van de 9 a 14) y detrás del Obelisco y las estatuas
    (Decor). Sin parallax: en la arena la cámara queda trabada (0..480) y antes de
    entrar el edificio está fuera de la pantalla.
  - Las pirámides (EstatuaColumnaIzq/Der) pasan a ser PILAS DE PATRULLEROS
    (gen_l3_pilas.py: mismo tamaño y mismas superficies, y 70 y 122), con la sirena
    del patrullero del medio que titila (2 cuadros) y humo (HumoAuto, el de los
    patrulleros de la calle) que sale de arriba, en Decor: detrás de Lio y del jefe.

Idempotente (borra y vuelve a poner sus cosas). Correr después de
wire_l3_recorrido.py y de wire_l3_caos.py (HumoAuto). GAME_JSON=ruta lo aplica a
una copia (vista previa sin tocar game.json). Requiere: gen_l3_calle.py
(obelisco), gen_l3_evita.py y gen_l3_pilas.py. Edita game/game.json (backup
.bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_l3_arena_9dejulio.py
"""
import datetime
import json
import os
import shutil

from PIL import Image

import l3_recorrido as R
from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = os.environ.get("GAME_JSON", "game/game.json")
CITY = "game/assets/City"
OX = R.OFFSET_X
EDIFICIO_X = 250          # x del juego (la arena va de 0 a 480; el Obelisco está centrado en 232)
EDIFICIO_Y = -4           # la antena queda debajo del cartel del jefe del HUD (y −19..−6)
EDIFICIO_Z = 15
PILA_FPS = 0.4            # s entre cuadros de la sirena
# humo de las pilas: (x, y) de la esquina, 80x128 (x2, como el de los patrulleros de la
# calle), sale del patrullero de arriba (chasis en y 70) y se va a la derecha
HUMO_PILAS = [(26, -56), (382, -56)]
HUMO_W, HUMO_H, HUMO_Z = 80, 128, 2


def recurso(nombre):
    return {"file": f"assets/City/{nombre}", "kind": "image", "metadata": "",
            "name": nombre, "smoothed": False, "userAdded": True}


def cuadro(imagen):
    return {"hasCustomCollisionMask": False, "image": imagen, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def sprite(nombre, imagenes, entre=0.15):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": nombre, "type": "Sprite",
            "updateIfNotVisible": False, "variables": [], "effects": [], "behaviors": [],
            "animations": [{"name": "Idle", "useMultipleDirections": False, "directions": [{
                "looping": len(imagenes) > 1, "timeBetweenFrames": entre,
                "sprites": [cuadro(i) for i in imagenes]}]}]}


def inst(nombre, x, y, z, capa, w=0, h=0):
    return {"angle": 0, "customSize": bool(w), "height": h, "layer": capa, "name": nombre, "width": w,
            "x": x, "y": y, "zOrder": z, "numberProperties": [], "stringProperties": [], "initialVariables": []}


def main():
    if GAME == "game/game.json":
        asegurar_gdevelop_cerrado()
        shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    lay = next(l for l in g["layouts"] if l["name"] == "Level3")
    objs = {o["name"]: o for o in lay["objects"]}

    # recursos nuevos
    pilas = {lado: [f"pila_patrulleros_{lado}_{k}.png" for k in (1, 2)] for lado in ("izq", "der")}
    nuevos = ["edificio_evita.png"] + pilas["izq"] + pilas["der"]
    res = g["resources"]["resources"]
    res[:] = [r for r in res if r["name"] not in nuevos] + [recurso(n) for n in nuevos]

    # Obelisco: mismo centro, base en el piso, según el tamaño de la imagen
    ow, oh = Image.open(f"{CITY}/obelisco_cerca.png").size
    ob = [i for i in lay["instances"] if i["name"] == "ObeliscoGrande"]
    assert len(ob) == 1, f"esperaba 1 ObeliscoGrande, hay {len(ob)}"
    ob[0]["x"], ob[0]["y"] = R.OBELISCO_ARENA + OX - ow // 2, R.FLOOR - oh

    # edificio del mural: objeto e instancia (se reemplazan si ya estaban)
    lay["objects"] = [o for o in lay["objects"] if o["name"] != "EdificioEvita"]
    lay["objects"].append(sprite("EdificioEvita", ["edificio_evita.png"]))
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs and not any(c.get("objectName") == "EdificioEvita" for c in fs["children"]):
        fs["children"].append({"objectName": "EdificioEvita"})
    lay["instances"] = [i for i in lay["instances"] if i["name"] != "EdificioEvita"]
    lay["instances"].append(inst("EdificioEvita", EDIFICIO_X, EDIFICIO_Y, EDIFICIO_Z, "BG_city"))

    # pirámides -> pilas de patrulleros (mismo objeto, mismo tamaño: las instancias no se mueven)
    for nombre, lado in (("EstatuaColumnaIzq", "izq"), ("EstatuaColumnaDer", "der")):
        objs[nombre]["animations"] = sprite(nombre, pilas[lado], PILA_FPS)["animations"]

    # humo de las pilas (en Decor; el de los autos de la calle es de Atmos y no se toca)
    lay["instances"] = [i for i in lay["instances"] if not (i["name"] == "HumoAuto" and i["layer"] == "Decor")]
    for x, y in HUMO_PILAS:
        lay["instances"].append(inst("HumoAuto", x, y, HUMO_Z, "Decor", HUMO_W, HUMO_H))

    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Level3: Obelisco {ow}x{oh} en ({ob[0]['x']}, {ob[0]['y']}); EdificioEvita en "
          f"({EDIFICIO_X}, {EDIFICIO_Y}); pilas de patrulleros con {len(HUMO_PILAS)} humos")


if __name__ == "__main__":
    main()
