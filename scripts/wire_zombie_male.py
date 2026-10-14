#!/usr/bin/env python3
"""
wire_zombie_male.py  —  mete el zombie masculino en el proyecto GDevelop.

Requiere los assets (correr antes `gen_zombie_male.py`):
  game/assets/Zombie_M/Zombie_M_Walk_1.png .. _8.png

Que hace (edita game/game.json, backup .bak-<ts>, idempotente):
  - resources: ZombieM_Walk_1..8.png
  - objeto Sprite `ZombieM` con animacion `Walk` (8 frames, loop)
  - variable de escena `ZombieMDir` = 1
  - instancia en la capa base, patrullando x 680..880 a 18 px/s (el mas
    lento de los tres: renguea)
  - eventos: fija animacion Walk + patrulla (mismo patron ya validado)
  - agrega `ZombieM` al grupo `Zombies` -> stomp/daño ya lo cubren
    (esos eventos ya usan el grupo, ver wire_zombie_female.py)

Correr desde la raiz del repo:  python3 scripts/wire_zombie_male.py
Despues, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.
"""
import json
import datetime
import shutil
import uuid
import os

GAME = "game/game.json"
N = 8
START_X = 760
LEFT, RIGHT = 680, 880
SPEED = 18
GROUND_Y = 110
SPRITE_H = 34


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts}


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    # --- resources ---
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for i in range(1, N + 1):
        nm = f"ZombieM_Walk_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/Zombie_M/Zombie_M_Walk_{i}.png",
                        "kind": "image", "metadata": "", "name": nm,
                        "smoothed": False, "userAdded": True})

    # --- objeto ZombieM ---
    if not any(o["name"] == "ZombieM" for o in lay["objects"]):
        lay["objects"].append({
            "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
            "name": "ZombieM", "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": [],
            "animations": [{
                "name": "Walk", "useMultipleDirections": False, "directions": [{
                    "looping": True, "timeBetweenFrames": 0.13, "sprites": [{
                        "hasCustomCollisionMask": False,
                        "image": f"ZombieM_Walk_{i}.png", "points": [],
                        "originPoint": {"name": "origine", "x": 0, "y": 0},
                        "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                        "customCollisionMask": [],
                    } for i in range(1, N + 1)]}]}]})

    # --- variable de escena ---
    if not any(v["name"] == "ZombieMDir" for v in lay["variables"]):
        lay["variables"].append({"name": "ZombieMDir", "type": "number", "value": 1})

    # --- grupo Zombies (lo crea wire_zombie_female; si no existe, lo armo) ---
    groups = lay.setdefault("objectsGroups", [])
    grp = next((g for g in groups if g["name"] == "Zombies"), None)
    if grp is None:
        grp = {"name": "Zombies", "objects": [{"name": "Zombie"}]}
        groups.append(grp)
    if not any(o["name"] == "ZombieM" for o in grp["objects"]):
        grp["objects"].append({"name": "ZombieM"})

    # --- instancia ---
    if not any(i["name"] == "ZombieM" for i in lay["instances"]):
        lay["instances"].insert(0, {
            "angle": 0, "customSize": False, "height": 0, "layer": "",
            "name": "ZombieM", "persistentUuid": str(uuid.uuid4()),
            "width": 0, "x": START_X, "y": GROUND_Y - SPRITE_H, "zOrder": 2,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})

    # --- eventos: animacion + patrulla ---
    already = any(
        a.get("type", {}).get("value") == "SetAnimationName"
        and a.get("parameters", [None])[0] == "ZombieM"
        for e in lay["events"] for a in e.get("actions", []))
    if not already:
        lay["events"].extend([
            std([], [{"type": {"value": "SetAnimationName"},
                      "parameters": ["ZombieM", '"Walk"']}]),
            std([], [{"type": {"value": "SetX"},
                      "parameters": ["ZombieM", "+",
                                     f"Variable(ZombieMDir) * {SPEED} * TimeDelta()"]}]),
            std([{"type": {"value": "PosX"}, "parameters": ["ZombieM", ">", str(RIGHT)]},
                 {"type": {"value": "VarScene"}, "parameters": ["ZombieMDir", "=", "1"]}],
                [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieMDir", "=", "-1"]},
                 {"type": {"value": "FlipX"}, "parameters": ["ZombieM", "yes"]}]),
            std([{"type": {"value": "PosX"}, "parameters": ["ZombieM", "<", str(LEFT)]},
                 {"type": {"value": "VarScene"}, "parameters": ["ZombieMDir", "=", "-1"]}],
                [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieMDir", "=", "1"]},
                 {"type": {"value": "FlipX"}, "parameters": ["ZombieM", "no"]}]),
        ])

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print("OK. objetos:", [o["name"] for o in lay["objects"]])
    print("    grupo Zombies:", [o["name"] for o in grp["objects"]])
    print("    eventos totales:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    assert os.path.exists("game/assets/Zombie_M/Zombie_M_Walk_1.png"), \
        "faltan los frames: corré gen_zombie_male.py primero"
    main()
