#!/usr/bin/env python3
"""
wire_zombies_marcha.py  —  zombies "de marcha": caminan DERECHO de izquierda
a derecha por todo el nivel, sin darse vuelta. Cuando salen por la derecha
reaparecen por la izquierda (loop) — dan la sensación de éxodo/estampida
constante de fondo. Reusan el arte de ZombieM (sin assets nuevos).

Edita game/game.json (backup .bak-<ts>, idempotente):
  - objeto `ZombieMarcha` (Sprite, anim Walk = frames de ZombieM)
  - `ZombieMarcha` al grupo `Zombies` (se puede stompear / hace daño de
    costado, igual que el resto)
  - 5 instancias repartidas a lo largo del nivel (y=76, sobre el piso)
  - eventos: animación Walk + mirar a la derecha, avanzar +20 px/s,
    y wrap al pasar x>2680 -> x=-60

Revertir:  REVERT=1 python3 scripts/wire_zombies_marcha.py
Uso:  python3 scripts/wire_zombies_marcha.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
NAME = "ZombieMarcha"
FRAMES = [f"ZombieM_Walk_{i}.png" for i in range(1, 9)]
SPEED = 20
X_WRAP, X_RESET = 2680, -60
START_XS = [60, 560, 1080, 1600, 2120]
GROUND_Y, SPRITE_H = 110, 34


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def C(t, p):
    return {"type": {"value": t}, "parameters": p}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    # --- limpiar (idempotente / revert) ---
    lay["objects"] = [o for o in lay["objects"] if o["name"] != NAME]
    lay["instances"] = [i for i in lay["instances"] if i["name"] != NAME]
    lay["events"] = [e for e in lay["events"]
                     if not any(a.get("parameters", [""])[0] == NAME for a in e.get("actions", []))]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] != NAME]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") != NAME]

    if revert:
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # --- objeto (reusa frames de ZombieM) ---
    lay["objects"].append({
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": NAME,
        "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Walk", "useMultipleDirections": False, "directions": [{
            "looping": True, "timeBetweenFrames": 0.13, "sprites": [{
                "hasCustomCollisionMask": False, "image": f, "points": [],
                "originPoint": {"name": "origine", "x": 0, "y": 0},
                "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                "customCollisionMask": []} for f in FRAMES]}]}]})
    if "children" in fs:
        fs["children"].append({"objectName": NAME})
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies" and not any(o["name"] == NAME for o in g["objects"]):
            g["objects"].append({"name": NAME})

    # --- instancias ---
    for x in START_XS:
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": "", "name": NAME,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x,
            "y": GROUND_Y - SPRITE_H, "zOrder": 2,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})

    # --- eventos ---
    lay["events"] += [
        std([], [C("SetAnimationName", [NAME, '"Walk"']),
                 C("FlipX", [NAME, "no"])]),
        std([], [C("SetX", [NAME, "+", f"{SPEED} * TimeDelta()"])]),
        std([C("PosX", [NAME, ">", str(X_WRAP)])],
            [C("SetX", [NAME, "=", str(X_RESET)])]),
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("grupo Zombies:", [o["name"] for g in lay["objectsGroups"]
                             if g["name"] == "Zombies" for o in g["objects"]])
    print("instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
