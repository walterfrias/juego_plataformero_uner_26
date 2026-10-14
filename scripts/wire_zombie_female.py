#!/usr/bin/env python3
"""
wire_zombie_female.py  —  mete la zombie femenina en el proyecto GDevelop.

Requiere los assets (correr antes `gen_zombie_female.py`):
  game/assets/Zombie_F/Zombie_F_Walk_1.png .. _10.png

Que hace (edita game/game.json directo, backup .bak-<ts>, idempotente):
  - resources: ZombieF_Walk_1..10.png
  - objeto Sprite `ZombieF` con animacion `Walk` (10 frames, loop)
  - variable de escena `ZombieFDir` = 1
  - instancia de `ZombieF` en la capa base, patrullando x 360..520
  - eventos: fija animacion Walk + patrulla (mismo patron que el Zombie
    existente, con el nombre de animacion entre comillas)
  - grupo de objetos `Zombies` = [Zombie, ZombieF] y los eventos de
    stomp / daño pasan a usar el grupo -> los DOS tipos de zombie se
    pueden pisar y hacen daño.

Formatos ya validados contra el Diagnostic report de GDevelop.
Correr desde la raiz del repo:  python3 scripts/wire_zombie_female.py
Despues, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.
"""
import json
import datetime
import shutil
import uuid
import os

GAME = "game/game.json"
N = 10
START_X = 440
LEFT, RIGHT = 360, 520
SPEED = 22
GROUND_Y = 110
SPRITE_H = 34


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
        nm = f"ZombieF_Walk_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/Zombie_F/Zombie_F_Walk_{i}.png",
                        "kind": "image", "metadata": "", "name": nm,
                        "smoothed": False, "userAdded": True})

    # --- objeto ZombieF ---
    if not any(o["name"] == "ZombieF" for o in lay["objects"]):
        lay["objects"].append({
            "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
            "name": "ZombieF", "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": [],
            "animations": [{
                "name": "Walk", "useMultipleDirections": False, "directions": [{
                    "looping": True, "timeBetweenFrames": 0.11, "sprites": [{
                        "hasCustomCollisionMask": False,
                        "image": f"ZombieF_Walk_{i}.png", "points": [],
                        "originPoint": {"name": "origine", "x": 0, "y": 0},
                        "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                        "customCollisionMask": [],
                    } for i in range(1, N + 1)]}]}]})

    # --- variable de escena ---
    if not any(v["name"] == "ZombieFDir" for v in lay["variables"]):
        lay["variables"].append({"name": "ZombieFDir", "type": "number", "value": 1})

    # --- grupo de objetos Zombies ---
    groups = lay.setdefault("objectsGroups", [])
    grp = next((g for g in groups if g["name"] == "Zombies"), None)
    if grp is None:
        grp = {"name": "Zombies", "objects": []}
        groups.append(grp)
    names_in_grp = {o["name"] for o in grp["objects"]}
    for nm in ("Zombie", "ZombieF"):
        if nm not in names_in_grp:
            grp["objects"].append({"name": nm})

    # --- instancia ---
    if not any(i["name"] == "ZombieF" for i in lay["instances"]):
        lay["instances"].insert(0, {
            "angle": 0, "customSize": False, "height": 0, "layer": "",
            "name": "ZombieF", "persistentUuid": str(uuid.uuid4()),
            "width": 0, "x": START_X, "y": GROUND_Y - SPRITE_H, "zOrder": 2,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})

    # --- eventos de ZombieF (animacion + patrulla) ---
    def std(conds, acts):
        return {"type": "BuiltinCommonInstructions::Standard",
                "conditions": conds, "actions": acts}

    already = any(
        a.get("type", {}).get("value") == "SetAnimationName"
        and a.get("parameters", [None, None])[0] == "ZombieF"
        for e in lay["events"] for a in e.get("actions", []))
    if not already:
        zf_events = [
            std([], [{"type": {"value": "SetAnimationName"},
                      "parameters": ["ZombieF", '"Walk"']}]),
            std([], [{"type": {"value": "SetX"},
                      "parameters": ["ZombieF", "+",
                                     f"Variable(ZombieFDir) * {SPEED} * TimeDelta()"]}]),
            std([{"type": {"value": "PosX"}, "parameters": ["ZombieF", ">", str(RIGHT)]},
                 {"type": {"value": "VarScene"}, "parameters": ["ZombieFDir", "=", "1"]}],
                [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieFDir", "=", "-1"]},
                 {"type": {"value": "FlipX"}, "parameters": ["ZombieF", "yes"]}]),
            std([{"type": {"value": "PosX"}, "parameters": ["ZombieF", "<", str(LEFT)]},
                 {"type": {"value": "VarScene"}, "parameters": ["ZombieFDir", "=", "-1"]}],
                [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieFDir", "=", "1"]},
                 {"type": {"value": "FlipX"}, "parameters": ["ZombieF", "no"]}]),
        ]
        # insertarlos despues del bloque de patrulla del Zombie (tras el ultimo
        # evento que toca "Zombie" con SetX/PosX). Simplify: al final.
        lay["events"].extend(zf_events)

    # --- stomp / daño -> usar el grupo Zombies ---
    def swap_zombie_to_group(instr):
        p = instr.get("parameters", [])
        for k, v in enumerate(p):
            if v == "Zombie":
                p[k] = "Zombies"
            elif v == "Zombie.Y()":
                p[k] = "Zombies.Y()"
    for e in lay["events"]:
        acts = e.get("actions", [])
        conds = e.get("conditions", [])
        # solo los eventos de colisión Player/Zombie (stomp y daño)
        is_collision_evt = any(
            c.get("type", {}).get("value") == "CollisionNP"
            and "Zombie" in c.get("parameters", []) for c in conds)
        if is_collision_evt:
            for x in conds + acts:
                swap_zombie_to_group(x)

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print("OK. objetos:", [o["name"] for o in lay["objects"]])
    print("    grupo Zombies:", [o["name"] for o in grp["objects"]])
    print("    eventos totales:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    assert os.path.exists("game/assets/Zombie_F/Zombie_F_Walk_1.png"), \
        "faltan los frames: corré gen_zombie_female.py primero"
    main()
