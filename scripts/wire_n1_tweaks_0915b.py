#!/usr/bin/env python3
"""
wire_n1_tweaks_0915b.py — sigue a wire_n1_tweaks_0915.py: el usuario
jugó y el zombie "corredor" del final (ZombieEnd1, reusa el arte de
ZombieJ) quedó animando "Walk" parado en el mismo lugar en vez de
correr de izquierda a derecha como el ZombieJ original. Fix: le agrega
patrulla propia (misma variable-de-escena-por-objeto que usan
ZombieN/O/V/J en wire_zombies_wave2.py — cada objeto la suya, así no
repite el bug de compartir Dir entre instancias del mismo objeto).

Además agrega 3 zombies MÁS al tramo final, también con patrulla
propia (a pedido: "que estén deambulando", no quietos como
ZombieEnd2/3 que se dejaron sin tocar):
  ZombieEnd4 (arte Zombie_V, "anciana", lenta)   2300-2400  8px/s
  ZombieEnd5 (arte Zombie_O, "obrero")           2400-2500  13px/s
  ZombieEnd6 (arte Zombie_N, "adolescente")      2480-2560  26px/s

Edita game/game.json (backup .bak-<ts>, idempotente, marca eventos
propios con "_tw0915b": true). REVERT=1 para deshacer (saca la
patrulla de ZombieEnd1 y los 3 objetos nuevos; ZombieEnd1 vuelve a
quedar quieto, no se borra).
Uso: python3 scripts/wire_n1_tweaks_0915b.py   (GDevelop CERRADO)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"

# (nombre, x_spawn, izq, der, velocidad, frames)
PATROL_END = [
    ("ZombieEnd1", 2210, 2150, 2320, 34, None),  # ya existe, sólo le agrego patrulla
    ("ZombieEnd4", 2350, 2300, 2400, 8, [f"Zombie_V_Walk_{i}.png" for i in range(1, 9)]),
    ("ZombieEnd5", 2450, 2400, 2500, 13, [f"Zombie_O_Walk_{i}.png" for i in range(1, 9)]),
    ("ZombieEnd6", 2520, 2480, 2560, 26, [f"Zombie_N_Walk_{i}.png" for i in range(1, 9)]),
]
NEW_OBJS = [n for n, *_ in PATROL_END if n != "ZombieEnd1"]
ALL_NAMES = [n for n, *_ in PATROL_END]
ALL_VARS = [f"{n}Dir" for n in ALL_NAMES]


def zombie_object(name, frames):
    return {
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": name, "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Walk", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 0.13,
                                        "sprites": [{"hasCustomCollisionMask": False,
                                                     "image": f, "points": [],
                                                     "originPoint": {"name": "origine", "x": 0, "y": 0},
                                                     "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                                                     "customCollisionMask": []} for f in frames]}]}]}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, "_tw0915b": True}


def C(t, p):
    return {"type": {"value": t}, "parameters": p}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    assert lay["name"] == "Level1"

    # ---- limpieza idempotente de lo que agrega ESTE script ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NEW_OBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in NEW_OBJS]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in ALL_VARS]
    lay["events"] = [e for e in lay["events"] if not e.get("_tw0915b")]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] not in NEW_OBJS]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NEW_OBJS]

    if revert:
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK (ZombieEnd1 queda, sin patrulla)")
        return

    assert any(o["name"] == "ZombieEnd1" for o in lay["objects"]), \
        "corré primero scripts/wire_n1_tweaks_0915.py"

    grp = next((g for g in lay.get("objectsGroups", []) if g["name"] == "Zombies"), None)

    for name, sx, left, right, speed, frames in PATROL_END:
        if frames is not None:
            # objeto nuevo
            lay["objects"].append(zombie_object(name, frames))
            if "children" in fs:
                fs["children"].append({"objectName": name})
            if grp is not None and not any(o["name"] == name for o in grp["objects"]):
                grp["objects"].append({"name": name})
            lay["instances"].append({
                "angle": 0, "customSize": False, "height": 0, "layer": "",
                "name": name, "persistentUuid": str(uuid.uuid4()),
                "width": 0, "x": sx, "y": 76, "zOrder": 2,
                "numberProperties": [], "stringProperties": [], "initialVariables": []})

        lay["variables"].append({"name": f"{name}Dir", "type": "number", "value": 1})
        lay["events"] += [
            std([], [C("SetAnimationName", [name, '"Walk"'])]),
            std([], [C("SetX", [name, "+", f"Variable({name}Dir) * {speed} * TimeDelta()"])]),
            std([C("PosX", [name, ">", str(right)]),
                 C("VarScene", [f"{name}Dir", "=", "1"])],
                [C("ModVarScene", [f"{name}Dir", "=", "-1"]),
                 C("FlipX", [name, "yes"])]),
            std([C("PosX", [name, "<", str(left)]),
                 C("VarScene", [f"{name}Dir", "=", "-1"])],
                [C("ModVarScene", [f"{name}Dir", "=", "1"]),
                 C("FlipX", [name, "no"])]),
        ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("patrulla agregada:", ALL_NAMES)
    print("total instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
