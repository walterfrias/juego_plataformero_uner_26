#!/usr/bin/env python3
"""
wire_zombie_tall.py  —  mete el 3er zombie (ZombieT, oficinista alto) + lo
suma a la horda + junta más a los zombies de patrulla y aprieta la horda.

Requiere: scripts/gen_zombie_tall.py corrido.

Edita game/game.json (backup .bak-<ts>, idempotente):
  - resources ZombieT_Walk_1..8.png
  - objeto `ZombieT` (Sprite, anim Walk) + `HordaZombieT` (reusa los frames)
  - var de escena `ZombieTDir`, `ZombieT` al grupo `Zombies`
  - patrulla: ZombieF x=400 (360..440), ZombieM x=470 (440..520),
    ZombieT x=540 (510..600)  -> los tres pegados, se cruzan como grupo
  - horda: rehecha con ~15px de separación (antes ~27), mezcla M/F/T,
    15 instancias x≈895..1105, y jitter 72..80
  - eventos: patrulla de ZombieT (mismo patrón) + HordaZombieT sumado al
    evento de movimiento y al de borrado de la horda

Revertir:  REVERT=1 python3 scripts/wire_zombie_tall.py
Uso:  python3 scripts/wire_zombie_tall.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
N = 8
PATROL = {  # nombre: (x, left, right, speed)
    "ZombieF": (400, 360, 440, 20),
    "ZombieM": (470, 440, 520, 16),
    "ZombieT": (540, 510, 600, 14),
}
GROUND_Y, SPRITE_H = 110, 34
HORDA_X0, HORDA_STEP, HORDA_N = 895, 15, 15
HORDA_YS = [76, 73, 78, 74, 79, 75, 77, 72, 80, 74, 76, 78, 73, 79, 75]
HORDA_TYPES = ["HordaZombieM", "HordaZombieF", "HordaZombieT"]


def walk_anim(prefix, tbf=0.13):
    return {"name": "Walk", "useMultipleDirections": False, "directions": [{
        "looping": True, "timeBetweenFrames": tbf, "sprites": [{
            "hasCustomCollisionMask": False, "image": f"{prefix}_Walk_{i}.png",
            "points": [], "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []} for i in range(1, N + 1)]}]}


def sprite_obj(name, prefix):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": [], "animations": [walk_anim(prefix)]}


def inst(name, x, y, z):
    return {"angle": 0, "customSize": False, "height": 0, "layer": "", "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # --- limpiar horda + ZombieT (idempotente / revert) ---
    horde_names = ["HordaZombieM", "HordaZombieF", "HordaZombieT"]
    lay["instances"] = [i for i in lay["instances"]
                        if i["name"] not in horde_names + ["ZombieT"]]
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in ("ZombieT", "HordaZombieT")]
    lay["variables"] = [v for v in lay["variables"] if v["name"] != "ZombieTDir"]
    lay["events"] = [e for e in lay["events"]
                     if not any(a.get("parameters", [""])[0] == "ZombieT"
                                for a in e.get("actions", []))]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] != "ZombieT"]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"]
                          if c.get("objectName") not in ("ZombieT", "HordaZombieT")]

    def patch_horde_events(types):
        """re-escribe el evento de movimiento y el de borrado de la horda."""
        for e in lay["events"]:
            acts = e.get("actions", [])
            has_move = any(a.get("type", {}).get("value") == "SetX"
                           and a.get("parameters", [""])[0] == "HordaPiso"
                           and "TimeDelta" in "".join(map(str, a.get("parameters", [])))
                           for a in acts)
            has_del = (any(c.get("type", {}).get("value") == "PosX"
                           and c.get("parameters", [""])[0] == "HordaPiso"
                           for c in e.get("conditions", []))
                       and any(a.get("type", {}).get("value") == "Delete" for a in acts))
            if has_move:
                new = []
                for z in types:
                    new.append({"type": {"value": "SetAnimationName"}, "parameters": [z, '"Walk"']})
                for z in types + ["HordaPiso"]:
                    new.append({"type": {"value": "SetX"}, "parameters": [z, "+", "25 * TimeDelta()"]})
                new.append({"type": {"value": "SetX"},
                            "parameters": ["HumoHorda", "=", "HordaPiso.X() + 90"]})
                new.append({"type": {"value": "SetY"},
                            "parameters": ["HumoHorda", "=", "HordaPiso.Y() + 18"]})
                e["actions"] = new
            elif has_del:
                e["actions"] = [{"type": {"value": "Delete"}, "parameters": [z, ""]}
                                for z in types + ["HordaPiso", "HumoHorda"]]

    if revert:
        res[:] = [r for r in res if not r["name"].startswith("ZombieT_Walk_")]
        for name, x in (("ZombieF", 440), ("ZombieM", 760)):
            for i in lay["instances"]:
                if i["name"] == name:
                    i["x"] = x
        # horda M/F apretada, sin T
        for k in range(HORDA_N):
            t = ["HordaZombieM", "HordaZombieF"][k % 2]
            lay["instances"].append(inst(t, HORDA_X0 + k * HORDA_STEP, HORDA_YS[k], 4))
        patch_horde_events(["HordaZombieF", "HordaZombieM"])
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # --- resources ---
    have = {r["name"] for r in res}
    for i in range(1, N + 1):
        nm = f"ZombieT_Walk_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/Zombie_T/Zombie_T_Walk_{i}.png", "kind": "image",
                        "metadata": "", "name": nm, "smoothed": False, "userAdded": True})

    # --- objetos ---
    lay["objects"].append(sprite_obj("ZombieT", "ZombieT"))
    lay["objects"].append(sprite_obj("HordaZombieT", "ZombieT"))
    if "children" in fs:
        fs["children"] += [{"objectName": "ZombieT"}, {"objectName": "HordaZombieT"}]

    # --- var + grupo ---
    lay["variables"].append({"name": "ZombieTDir", "type": "number", "value": 1})
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies" and not any(o["name"] == "ZombieT" for o in g["objects"]):
            g["objects"].append({"name": "ZombieT"})

    # --- patrulla: reposicionar F/M, agregar T ---
    for name in PATROL:
        px = PATROL[name][0]
        found = False
        for i in lay["instances"]:
            if i["name"] == name:
                i["x"], i["y"], found = px, GROUND_Y - SPRITE_H, True
        if not found:
            lay["instances"].insert(0, inst(name, px, GROUND_Y - SPRITE_H, 2))

    # --- patrulla: eventos de ZombieT ---
    x, left, right, speed = PATROL["ZombieT"]
    lay["events"] += [
        std([], [{"type": {"value": "SetAnimationName"}, "parameters": ["ZombieT", '"Walk"']}]),
        std([], [{"type": {"value": "SetX"}, "parameters":
                  ["ZombieT", "+", f"Variable(ZombieTDir) * {speed} * TimeDelta()"]}]),
        std([{"type": {"value": "PosX"}, "parameters": ["ZombieT", ">", str(right)]},
             {"type": {"value": "VarScene"}, "parameters": ["ZombieTDir", "=", "1"]}],
            [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieTDir", "=", "-1"]},
             {"type": {"value": "FlipX"}, "parameters": ["ZombieT", "yes"]}]),
        std([{"type": {"value": "PosX"}, "parameters": ["ZombieT", "<", str(left)]},
             {"type": {"value": "VarScene"}, "parameters": ["ZombieTDir", "=", "-1"]}],
            [{"type": {"value": "ModVarScene"}, "parameters": ["ZombieTDir", "=", "1"]},
             {"type": {"value": "FlipX"}, "parameters": ["ZombieT", "no"]}]),
    ]

    # --- horda: rehacer apretada con M/F/T ---
    for k in range(HORDA_N):
        t = HORDA_TYPES[k % 3]
        lay["instances"].append(inst(t, HORDA_X0 + k * HORDA_STEP, HORDA_YS[k], 4))
    patch_horde_events(["HordaZombieM", "HordaZombieF", "HordaZombieT"])

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("objetos:", [o["name"] for o in lay["objects"] if "Zombie" in o["name"]])
    print("grupo Zombies:", [o["name"] for g in lay["objectsGroups"]
                             if g["name"] == "Zombies" for o in g["objects"]])
    print("instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Zombie_T/Zombie_T_Walk_1.png"), \
        "corré gen_zombie_tall.py primero"
    main(revert=os.environ.get("REVERT") == "1")
