#!/usr/bin/env python3
"""
wire_street_props.py  —  registro reproducible de como se metieron los
props de calle (farol, tacho) en el proyecto GDevelop.

Edita game/game.json directamente (el proyecto GDevelop es un JSON).
Se hace a mano porque el MCP `gdevelop` no conecta en estas sesiones.
Hace backup  game/game.json.bak-<timestamp>  antes de tocar nada.

Que agrega:
  - resources: farol.png, tacho.png
  - capa "Decor" (followBaseLayerCamera:true -> scrollea 1:1 con el mundo),
    ordenada delante de BG_far/BG_near y detras de la capa base
  - objetos Sprite: Farol, Tacho
  - instancias: 3 faroles (x=36,150,268) y 2 tachos (x=60,244), con
    y = 110 - altoSprite para que apoyen en el piso

Es idempotente: si ya existen los recursos/objetos/instancias, no
duplica. Correr desde la raiz del repo:  python3 scripts/wire_street_props.py

IMPORTANTE: GDevelop no relee el archivo del disco. Cerrar proyecto (sin
guardar) y volver a abrir game/game.json para ver los cambios.
"""
import json
import datetime
import shutil
import uuid
import copy
import os

GAME = "game/game.json"


def sprite_obj(name, img):
    return {
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
        "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
        "behaviors": [], "animations": [{
            "name": "Idle", "useMultipleDirections": False, "directions": [{
                "looping": True, "timeBetweenFrames": 0.1, "sprites": [{
                    "hasCustomCollisionMask": False, "image": img, "points": [],
                    "originPoint": {"name": "origine", "x": 0, "y": 0},
                    "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                    "customCollisionMask": [],
                }]}]}]}


def inst(name, x, y, layer="Decor", z=1):
    return {"angle": 0, "customSize": False, "height": 0, "layer": layer, "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm, f in [("farol.png", "assets/City/farol.png"),
                  ("tacho.png", "assets/City/tacho.png")]:
        if nm not in have:
            res.append({"file": f, "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})

    base = [l for l in lay["layers"] if l["name"] == ""][0]
    if not any(l["name"] == "Decor" for l in lay["layers"]):
        decor = copy.deepcopy(base)
        decor["name"] = "Decor"
        decor["followBaseLayerCamera"] = True
        front = [l for l in lay["layers"] if l["name"] in ("BG_far", "BG_near")]
        lay["layers"] = front + [decor, base]

    names = {o["name"] for o in lay["objects"]}
    for o in [sprite_obj("Farol", "farol.png"), sprite_obj("Tacho", "tacho.png")]:
        if o["name"] not in names:
            lay["objects"].append(o)

    GY = 110
    inames = {i["name"] for i in lay["instances"]}
    new = []
    if "Farol" not in inames:
        new += [inst("Farol", 36, GY - 56), inst("Farol", 150, GY - 56),
                inst("Farol", 268, GY - 56)]
    if "Tacho" not in inames:
        new += [inst("Tacho", 60, GY - 18), inst("Tacho", 244, GY - 18)]
    lay["instances"] = new + lay["instances"]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print("OK. capas:", [l["name"] or "BASE" for l in lay["layers"]])
    print("    objetos:", [o["name"] for o in lay["objects"]])
    print("    +instancias:", [(i["name"], i["x"], i["y"]) for i in new])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
