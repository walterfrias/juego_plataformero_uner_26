#!/usr/bin/env python3
"""
wire_city_background.py  —  registro reproducible de como se metio el
fondo de ciudad (skyline + Obelisco) en el proyecto GDevelop.

Requiere que existan los assets (correr antes `gen_city_bg.py`):
  game/assets/City/city_far.png, city_near.png, obelisco.png

Edita game/game.json directo (el proyecto GDevelop es JSON) porque el MCP
`gdevelop` no conecta en estas sesiones. Backup game/game.json.bak-<ts>
antes de tocar nada. Es idempotente (no duplica si ya esta puesto).

Que hace:
  - color de fondo de la escena -> azul noche (layout.r/.v/.b = 16,20,40)
  - resources: city_far.png, city_near.png, obelisco.png
  - capas BG_far / BG_near, ANTES de la capa base en el array ->
    renderizan detras del gameplay. `followBaseLayerCamera:true` ->
    scrollean 1:1 con el mundo (sin eventos).
  - objetos: CityFar / CityNear (Tiled Sprite 4000px de ancho),
    Obelisco (Sprite). Instancias en sus capas.

NOTA: el parallax con profundidad (far mas lento que near) se saco
porque dependia de eventos `SetCameraX` con formato sin verificar. Se
puede reintroducir mas adelante, ya validado a mano en el editor. Por
ahora el fondo es scroll plano 1:1.

El seguimiento de camara al jugador y el tamaño del suelo los arregla
`wire_camera_follow.py` (correr ese despues de este).

Correr desde la raiz del repo:  python3 scripts/wire_city_background.py
Despues, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.
"""
import json
import datetime
import shutil
import uuid
import copy
import os

GAME = "game/game.json"


def tiled(name, tex, w, h):
    return {"assetStoreId": "", "name": name, "texture": tex,
            "type": "TiledSpriteObject::TiledSprite", "width": w, "height": h,
            "variables": [], "effects": [], "behaviors": []}


def sprite_obj(name, img):
    return {
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
        "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
        "behaviors": [], "animations": [{
            "name": "Idle", "useMultipleDirections": False, "directions": [{
                "looping": True, "timeBetweenFrames": 0.15, "sprites": [{
                    "hasCustomCollisionMask": False, "image": img, "points": [],
                    "originPoint": {"name": "origine", "x": 0, "y": 0},
                    "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                    "customCollisionMask": [],
                }]}]}]}


def inst(name, x, y, layer, z, w=None, h=None):
    return {"angle": 0, "customSize": bool(w), "height": h or 0, "layer": layer,
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0,
            "x": x, "y": y, "zOrder": z, "numberProperties": [],
            "stringProperties": [], "initialVariables": []}


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    # fondo de escena azul noche
    lay["r"], lay["v"], lay["b"] = 16, 20, 40

    # resources
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm in ("city_far.png", "city_near.png", "obelisco.png"):
        if nm not in have:
            res.append({"file": f"assets/City/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})

    # capas BG (detras de la capa base), scrollean 1:1 con el mundo
    base = [l for l in lay["layers"] if l["name"] == ""][0]
    for name in ("BG_far", "BG_near"):
        existing = [l for l in lay["layers"] if l["name"] == name]
        if existing:
            existing[0]["followBaseLayerCamera"] = True
        else:
            bl = copy.deepcopy(base)
            bl["name"] = name
            bl["followBaseLayerCamera"] = True
            lay["layers"].insert(0, bl)
    # asegurar orden: BG_far, BG_near, (Decor?), BASE
    want = ["BG_far", "BG_near", "Decor", ""]
    lay["layers"].sort(key=lambda l: want.index(l["name"]) if l["name"] in want else 99)

    # objetos
    names = {o["name"] for o in lay["objects"]}
    for o in [tiled("CityFar", "city_far.png", 4000, 70),
              tiled("CityNear", "city_near.png", 4000, 96),
              sprite_obj("Obelisco", "obelisco.png")]:
        if o["name"] not in names:
            lay["objects"].append(o)

    # instancias
    inames = {i["name"] for i in lay["instances"]}
    new = []
    if "CityFar" not in inames:
        new.append(inst("CityFar", -500, 42, "BG_far", 0, 4000, 70))
    if "CityNear" not in inames:
        new.append(inst("CityNear", -500, 20, "BG_near", 0, 4000, 96))
    if "Obelisco" not in inames:
        new.append(inst("Obelisco", 250, 4, "BG_far", 1))
    lay["instances"] = new + lay["instances"]

    # sacar eventos de parallax SetCameraX de corridas viejas (si hay)
    def is_setcamerax(e):
        return any(a.get("type", {}).get("value") == "SetCameraX"
                   for a in e.get("actions", []))
    lay["events"] = [e for e in lay["events"] if not is_setcamerax(e)]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print("OK. capas:", [l["name"] or "BASE" for l in lay["layers"]])
    print("    objetos:", [o["name"] for o in lay["objects"]])
    print("    +instancias:", [i["name"] for i in new])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
