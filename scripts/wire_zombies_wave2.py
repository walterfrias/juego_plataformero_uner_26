#!/usr/bin/env python3
"""
wire_zombies_wave2.py  —  mete los 4 zombies nuevos (ZombieN/V/O/J) como
zombies de PATRULLA (igual que ZombieD: NO van a la horda). Cada uno con su
tramo y su velocidad segun el andar.

Requiere: scripts/gen_zombies_wave2.py corrido.

Edita game/game.json (backup .bak-<ts>, idempotente):
  - resources Zombie_<X>_Walk_1..8.png
  - objeto Sprite `Zombie<X>` (anim Walk), var de escena `Zombie<X>Dir`
  - `Zombie<X>` al grupo `Zombies` (stomp/daño ya lo cubren)
  - 1 instancia patrullando su tramo, repartidas a lo largo del nivel
  - 4 eventos de patrulla por zombie (mismo patrón que los otros)

Tramos (x, izq, der, px/s):
  ZombieN  780   730  850   26   (adolescente: pasitos rapidos)
  ZombieO  1010  950  1090  13   (obrero: renguera pesada)
  ZombieV  1200  1150 1250  8    (anciana: lentisima)
  ZombieJ  2180  2060 2360  34   (corredor: el mas rapido, pasado el hueco)

Revertir:  REVERT=1 python3 scripts/wire_zombies_wave2.py
Uso:  python3 scripts/wire_zombies_wave2.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
N = 8
GROUND_Y, SPRITE_H = 110, 34

WAVE = {  # letra: (x, izq, der, speed)
    "N": (780, 730, 850, 26),
    "O": (1010, 950, 1090, 13),
    "V": (1200, 1150, 1250, 8),
    "J": (2180, 2060, 2360, 34),
}
NAMES = [f"Zombie{L}" for L in WAVE]


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def walk_anim(letter):
    return {"name": "Walk", "useMultipleDirections": False, "directions": [{
        "looping": True, "timeBetweenFrames": 0.13, "sprites": [{
            "hasCustomCollisionMask": False, "image": f"Zombie_{letter}_Walk_{i}.png",
            "points": [], "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []} for i in range(1, N + 1)]}]}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # --- limpiar (idempotente / revert) ---
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NAMES]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in NAMES]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in {f"{n}Dir" for n in NAMES}]
    lay["events"] = [e for e in lay["events"]
                     if not any(a.get("parameters", [""])[0] in NAMES
                                for a in e.get("actions", []))]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] not in NAMES]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NAMES]

    if revert:
        res[:] = [r for r in res
                  if not any(r["name"].startswith(f"Zombie_{L}_Walk_") for L in WAVE)]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    have = {r["name"] for r in res}
    for L in WAVE:
        for i in range(1, N + 1):
            nm = f"Zombie_{L}_Walk_{i}.png"
            if nm not in have:
                res.append({"file": f"assets/Zombie_{L}/Zombie_{L}_Walk_{i}.png",
                            "kind": "image", "metadata": "", "name": nm,
                            "smoothed": False, "userAdded": True})

    grp = next((g for g in lay.get("objectsGroups", []) if g["name"] == "Zombies"), None)

    for L, (x, left, right, speed) in WAVE.items():
        name = f"Zombie{L}"
        lay["objects"].append({
            "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": [], "animations": [walk_anim(L)]})
        if "children" in fs:
            fs["children"].append({"objectName": name})
        lay["variables"].append({"name": f"{name}Dir", "type": "number", "value": 1})
        if grp is not None and not any(o["name"] == name for o in grp["objects"]):
            grp["objects"].append({"name": name})
        lay["instances"].insert(0, {
            "angle": 0, "customSize": False, "height": 0, "layer": "", "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x,
            "y": GROUND_Y - SPRITE_H, "zOrder": 2,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})
        lay["events"] += [
            std([], [{"type": {"value": "SetAnimationName"}, "parameters": [name, '"Walk"']}]),
            std([], [{"type": {"value": "SetX"}, "parameters":
                      [name, "+", f"Variable({name}Dir) * {speed} * TimeDelta()"]}]),
            std([{"type": {"value": "PosX"}, "parameters": [name, ">", str(right)]},
                 {"type": {"value": "VarScene"}, "parameters": [f"{name}Dir", "=", "1"]}],
                [{"type": {"value": "ModVarScene"}, "parameters": [f"{name}Dir", "=", "-1"]},
                 {"type": {"value": "FlipX"}, "parameters": [name, "yes"]}]),
            std([{"type": {"value": "PosX"}, "parameters": [name, "<", str(left)]},
                 {"type": {"value": "VarScene"}, "parameters": [f"{name}Dir", "=", "-1"]}],
                [{"type": {"value": "ModVarScene"}, "parameters": [f"{name}Dir", "=", "1"]},
                 {"type": {"value": "FlipX"}, "parameters": [name, "no"]}]),
        ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("grupo Zombies:", [o["name"] for g in lay["objectsGroups"]
                             if g["name"] == "Zombies" for o in g["objects"]])
    print("instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Zombie_N/Zombie_N_Walk_1.png"), \
        "corré gen_zombies_wave2.py primero"
    main(revert=os.environ.get("REVERT") == "1")
