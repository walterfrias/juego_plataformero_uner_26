#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
wire_tendido.py  —  Fase 1 del tendido eléctrico en Level1.

Rutas elevadas por el cableado caído, sobre los pozos de la costanera:

  1. Tramo COSTANERA (después del obelisco): línea continua sobre los 4 pozos
     entre Ground A (..885) y Ground E (1575..). 5 postes-escalera + 4 cables.
     El player trepa el poste de x862, camina toda la línea y baja en x1582.
  2. Cruce del RÍO (hueco grande x1730..1970, > salto máx): 2 postes + 1 cable.

Requiere: scripts/gen_tendido.py corrido (poste.png, cable_tile.png).

Edita game/game.json (backup .bak-<ts>, idempotente, eventos "_tendido"):
  - resources poste.png, cable_tile.png
  - objeto `Poste` (Sprite, Platform "Ladder", máscara = fuste)
  - objeto `Cable` (TiledSprite, Platform "Jumpthru", 7px de alto, se estira por
    instancia; la colisión es su caja, no necesita máscara custom)
  - 7 instancias `Poste`, 5 instancias `Cable`
  - 1 evento checkpoint del otro lado del río (Player.X>1990 & Y<100 -> CheckX)

El Player NO se toca: el behavior Platformer ya sube/baja escaleras con ↑/↓ y
atraviesa jumpthru con ↓+salto (controles por defecto).

Revertir:  REVERT=1 python3 scripts/wire_tendido.py
Uso:  python3 scripts/wire_tendido.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import sys
import uuid
import datetime

sys.path.insert(0, os.path.dirname(__file__))
from gen_tendido import POSTE_W, POSTE_H, CABLE_H  # noqa: E402

GAME = "game/game.json"
MYOBJS = ("Poste", "Cable")

POSTE_Y = 22          # esquina sup-izq: base hincada ~8px en el cordón (y=110)
CABLE_Y = 30          # canto superior de la hebra (lo que se pisa)

# Corridas de postes (x en world). Cada par consecutivo lleva un cable.
POSTE_RUNS = [
    [862, 960, 1165, 1408, 1582],   # costanera: 4 pozos después del obelisco
    [1700, 1986],                   # cruce del río
]


def cond(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts, "_tendido": True}


def poste_obj():
    mask = [[{"x": x, "y": y} for x, y in
             [(3, 3), (POSTE_W - 3, 3), (POSTE_W - 3, POSTE_H - 4), (3, POSTE_H - 4)]]]
    return {
        "adaptCollisionMaskAutomatically": False, "assetStoreId": "",
        "name": "Poste", "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [],
        "behaviors": [{"name": "Platform", "type": "PlatformBehavior::PlatformBehavior",
                       "platformType": "Ladder"}],
        "animations": [{"name": "Idle", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 1,
                                        "sprites": [{
                                            "hasCustomCollisionMask": True,
                                            "image": "poste.png", "points": [],
                                            "originPoint": {"name": "origine", "x": 0, "y": 0},
                                            "centerPoint": {"automatic": True, "name": "centre",
                                                            "x": 0, "y": 0},
                                            "customCollisionMask": mask}]}]}]}


def cable_obj():
    return {
        "assetStoreId": "", "height": CABLE_H, "name": "Cable",
        "texture": "cable_tile.png", "type": "TiledSpriteObject::TiledSprite",
        "width": 64, "variables": [], "effects": [],
        "behaviors": [{"name": "Platform", "type": "PlatformBehavior::PlatformBehavior",
                       "platformType": "Jumpthru"}]}


def poste_inst(x):
    return {"angle": 0, "customSize": False, "height": 0, "layer": "", "name": "Poste",
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x, "y": POSTE_Y,
            "zOrder": 0, "numberProperties": [], "stringProperties": [],
            "initialVariables": []}


def cable_inst(x, w):
    return {"angle": 0, "customSize": True, "depth": 1, "height": CABLE_H, "layer": "",
            "name": "Cable", "persistentUuid": str(uuid.uuid4()), "width": w,
            "x": x, "y": CABLE_Y, "zOrder": 0,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # ---- limpieza (idempotente / revert; incluye nombres de versiones viejas) ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in MYOBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in MYOBJS]
    lay["events"] = [e for e in lay["events"] if not e.get("_tendido")]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MYOBJS]

    def is_tendido_res(name):
        return name in ("poste.png", "cable.png", "cable_tile.png") or \
            name.startswith("cable_")
    res[:] = [r for r in res if not is_tendido_res(r["name"])]

    if revert:
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # ---- resources ----
    for nm, path in (("poste.png", "assets/City/poste.png"),
                     ("cable_tile.png", "assets/City/cable_tile.png")):
        res.append({"file": path, "kind": "image", "metadata": "",
                    "name": nm, "smoothed": False, "userAdded": True})

    # ---- objetos ----
    lay["objects"] += [poste_obj(), cable_obj()]
    if "children" in fs:
        fs["children"] += [{"objectName": "Poste"}, {"objectName": "Cable"}]

    # ---- instancias: postes + un cable por tramo entre postes consecutivos ----
    n_postes = n_cables = 0
    for run in POSTE_RUNS:
        for x in run:
            lay["instances"].append(poste_inst(x))
            n_postes += 1
        for a, b in zip(run, run[1:]):
            cx = a + 2
            cw = (b + POSTE_W - 2) - cx           # llega hasta el aislador del poste der
            lay["instances"].append(cable_inst(cx, cw))
            n_cables += 1

    # ---- checkpoint del otro lado del hueco del río ----
    lay["events"].append(std(
        [cond("PosX", ["Player", ">", "1990"]),
         cond("PosY", ["Player", "<", "100"]),
         cond("VarScene", ["CheckX", "<", "1990"])],
        [cond("ModVarScene", ["CheckX", "=", "1990"])]))

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print(f"postes: {n_postes}   cables: {n_cables}")
    print("cables (x,w):", [(i["x"], i["width"]) for i in lay["instances"]
                            if i["name"] == "Cable"])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/cable_tile.png"), "corré gen_tendido.py primero"
    main(revert=os.environ.get("REVERT") == "1")
