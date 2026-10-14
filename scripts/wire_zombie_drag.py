#!/usr/bin/env python3
"""
wire_zombie_drag.py  —  mete el 4to zombie (ZombieD, mujer que arrastra un
pie) SOLO como zombie de patrulla. NO se agrega a la horda (a pedido).

Requiere: scripts/gen_zombie_drag.py corrido.

Edita game/game.json (backup .bak-<ts>, idempotente):
  - resources ZombieD_Walk_1..8.png
  - objeto `ZombieD` (Sprite, anim Walk), var de escena `ZombieDDir`
  - `ZombieD` al grupo `Zombies` (stomp/daño ya lo cubren)
  - instancia patrullando x 590..720 a 12 px/s (la más lenta: arrastra),
    justo después del nudo de F/M/T
  - eventos de patrulla (mismo patrón)

Revertir:  REVERT=1 python3 scripts/wire_zombie_drag.py
Uso:  python3 scripts/wire_zombie_drag.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
N = 8
START_X, LEFT, RIGHT, SPEED = 630, 590, 720, 12
GROUND_Y, SPRITE_H = 110, 34


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    lay["objects"] = [o for o in lay["objects"] if o["name"] != "ZombieD"]
    lay["instances"] = [i for i in lay["instances"] if i["name"] != "ZombieD"]
    lay["variables"] = [v for v in lay["variables"] if v["name"] != "ZombieDDir"]
    lay["events"] = [e for e in lay["events"]
                     if not any(a.get("parameters", [""])[0] == "ZombieD"
                                for a in e.get("actions", []))]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] != "ZombieD"]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") != "ZombieD"]

    if revert:
        res[:] = [r for r in res if not r["name"].startswith("ZombieD_Walk_")]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK")
        return

    have = {r["name"] for r in res}
    for i in range(1, N + 1):
        nm = f"ZombieD_Walk_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/Zombie_D/Zombie_D_Walk_{i}.png", "kind": "image",
                        "metadata": "", "name": nm, "smoothed": False, "userAdded": True})

    lay["objects"].append({
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": "ZombieD",
        "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Walk", "useMultipleDirections": False, "directions": [{
            "looping": True, "timeBetweenFrames": 0.15, "sprites": [{
                "hasCustomCollisionMask": False, "image": f"ZombieD_Walk_{i}.png", "points": [],
                "originPoint": {"name": "origine", "x": 0, "y": 0},
                "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                "customCollisionMask": []} for i in range(1, N + 1)]}]}]})
    if "children" in fs:
        fs["children"].append({"objectName": "ZombieD"})

    lay["variables"].append({"name": "ZombieDDir", "type": "number", "value": 1})
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies" and not any(o["name"] == "ZombieD" for o in g["objects"]):
            g["objects"].append({"name": "ZombieD"})

    lay["instances"].insert(0, {
        "angle": 0, "customSize": False, "height": 0, "layer": "", "name": "ZombieD",
        "persistentUuid": str(uuid.uuid4()), "width": 0, "x": START_X,
        "y": GROUND_Y - SPRITE_H, "zOrder": 2,
        "numberProperties": [], "stringProperties": [], "initialVariables": []})

    lay["events"] += [
        std([], [{"type": {"value": "SetAnimationName"}, "parameters": ["ZombieD", '"Walk"']}]),
        std([], [{"type": {"value": "SetX"}, "parameters":
                  ["ZombieD", "+", f"Variable(ZombieDDir) * {SPEED} * TimeDelta()"]}]),
        std([{"type": {"value": "PosX"}, "parameters": ["ZombieD", ">", str(RIGHT)]},
             {"type": {"value": "VarScene"}, "parameters": ["ZombieDDir", "=", "1"]}],
            [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieDDir", "=", "-1"]},
             {"type": {"value": "FlipX"}, "parameters": ["ZombieD", "yes"]}]),
        std([{"type": {"value": "PosX"}, "parameters": ["ZombieD", "<", str(LEFT)]},
             {"type": {"value": "VarScene"}, "parameters": ["ZombieDDir", "=", "-1"]}],
            [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieDDir", "=", "1"]},
             {"type": {"value": "FlipX"}, "parameters": ["ZombieD", "no"]}]),
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("grupo Zombies:", [o["name"] for g in lay["objectsGroups"]
                             if g["name"] == "Zombies" for o in g["objects"]])
    print("eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Zombie_D/Zombie_D_Walk_1.png"), \
        "corré gen_zombie_drag.py primero"
    main(revert=os.environ.get("REVERT") == "1")
