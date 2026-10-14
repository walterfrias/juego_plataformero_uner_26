#!/usr/bin/env python3
"""
wire_antidoto.py  —  mete el pickup `Antidoto` en el Nivel 1.

Mecánica (confirmada): juntar los 4 antídotos del nivel da +1 vida, UNA
sola vez. Tope de vida en 4. Se agrega un 4to corazón al HUD (`Heart4`).

Requiere: scripts/gen_antidoto.py corrido.

Edita game/game.json (backup .bak-<ts>, idempotente, marca los eventos
propios con "_antidoto": true):
  - resources antidoto_1..6.png
  - objeto `Antidoto` (Sprite, anim "Idle" loop, 6 frames)
  - objeto `Heart4` (copia de Heart1: heart.png, 1 frame)
  - vars de escena `Antidotes` = 0, `AntidoteBonus` = 0
  - 4 instancias de `Antidoto`:
      1. x=115  ruta principal, temprano  (enseña qué es)
      2. x=265  balcón de la plaza        (premia trepar los props)
      3. x=890  sobre el pozo de agua     (se agarra en el salto; si fallás, caés)
      4. x=1520 en el barrido de la horda (premio de riesgo)
  - 1 instancia de `Heart4` en el HUD (x=50, capa UI)
  - eventos: pickup (colisión -> Delete + Antidotes+1), bono a los 4,
    clamp de Lives<=4, y show/hide de Heart4 según Lives

Revertir:  REVERT=1 python3 scripts/wire_antidoto.py
Uso:  python3 scripts/wire_antidoto.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
N = 6

# (x, y) de las 4 instancias. y = esquina sup-izq (el sprite es 14x18).
SPOTS = [
    (115, 90),
    (265, 14),
    (890, 96),
    (1450, 92),
]

MYVARS = ("Antidotes", "AntidoteBonus")
MYOBJS = ("Antidoto", "Heart4")


def cond(value, params):
    return {"type": {"value": value}, "parameters": params}


def act(value, params):
    return cond(value, params)


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts, "_antidoto": True}


def sprite_frame(image):
    return {"hasCustomCollisionMask": False, "image": image, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # ---- limpieza (idempotente / revert) ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in MYOBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in MYOBJS]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in MYVARS]
    lay["events"] = [e for e in lay["events"] if not e.get("_antidoto")]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"]
                          if c.get("objectName") not in MYOBJS]

    if revert:
        res[:] = [r for r in res if not r["name"].startswith("antidoto_")]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # ---- resources ----
    have = {r["name"] for r in res}
    for i in range(1, N + 1):
        nm = f"antidoto_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/UI/antidoto_{i}.png", "kind": "image",
                        "metadata": "", "name": nm, "smoothed": False,
                        "userAdded": True})

    # ---- objeto Antidoto ----
    lay["objects"].append({
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": "Antidoto", "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Idle", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 0.12,
                                        "sprites": [sprite_frame(f"antidoto_{i}.png")
                                                    for i in range(1, N + 1)]}]}]})

    # ---- objeto Heart4 (igual que Heart1) ----
    lay["objects"].append({
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": "Heart4", "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Idle", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 1,
                                        "sprites": [sprite_frame("heart.png")]}]}]})

    if "children" in fs:
        fs["children"] += [{"objectName": "Antidoto"}, {"objectName": "Heart4"}]

    # ---- vars ----
    lay["variables"] += [{"name": "Antidotes", "type": "number", "value": 0},
                         {"name": "AntidoteBonus", "type": "number", "value": 0}]

    # ---- instancias ----
    for x, y in SPOTS:
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": "",
            "name": "Antidoto", "persistentUuid": str(uuid.uuid4()),
            "width": 0, "x": x, "y": y, "zOrder": 5,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})
    lay["instances"].append({
        "angle": 0, "customSize": False, "height": 0, "layer": "UI",
        "name": "Heart4", "persistentUuid": str(uuid.uuid4()),
        "width": 0, "x": 50, "y": 8, "zOrder": 10,
        "numberProperties": [], "stringProperties": [], "initialVariables": []})

    # ---- eventos ----
    lay["events"] += [
        # recoger un antídoto
        std([cond("CollisionNP", ["Player", "Antidoto", "", "", ""])],
            [act("Delete", ["Antidoto", ""]),
             act("ModVarScene", ["Antidotes", "+", "1"])]),
        # bono: los 4 -> +1 vida, una sola vez
        std([cond("VarScene", ["Antidotes", ">=", "4"]),
             cond("VarScene", ["AntidoteBonus", "=", "0"])],
            [act("ModVarScene", ["AntidoteBonus", "=", "1"]),
             act("ModVarScene", ["Lives", "+", "1"])]),
        # tope de vida en 4
        std([cond("VarScene", ["Lives", ">", "4"])],
            [act("ModVarScene", ["Lives", "=", "4"])]),
        # HUD del 4to corazón
        std([cond("VarScene", ["Lives", ">=", "4"])], [act("Show", ["Heart4", ""])]),
        std([cond("VarScene", ["Lives", "<", "4"])], [act("Hide", ["Heart4"])]),
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("instancias Antidoto:", sum(1 for i in lay["instances"] if i["name"] == "Antidoto"))
    print("eventos _antidoto:", sum(1 for e in lay["events"] if e.get("_antidoto")))
    print("vars:", [v["name"] for v in lay["variables"] if v["name"] in MYVARS])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/UI/antidoto_1.png"), \
        "corré gen_antidoto.py primero"
    main(revert=os.environ.get("REVERT") == "1")
