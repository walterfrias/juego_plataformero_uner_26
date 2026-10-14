#!/usr/bin/env python3
"""
wire_puentes.py  —  puentes rotos en los 4 pozos de la costanera + acento río.

Requiere: scripts/gen_puentes.py corrido.

Asignación (para que 4 pozos no parezcan copy-paste):
  pozo 1 (885-951)   PuenteA  tablones, falta el del medio   -> CRUZABLE (saltito)
  pozo 2 (1097-1155) PuenteB  chapa improvisada ladeada       -> CRUZABLE (entera)
  pozo 3 (1334-1400) PuenteC  sección colgando + hierros      -> deco + stub pisable
  pozo 4 (1503-1575) PuenteD  losa volcada hundida            -> deco (sin colisión)
  río   (~1730)      PuenteE  tramo quebrado colgando al agua -> deco (sin colisión)

A y B llevan behavior Platform SÓLIDO con máscara custom (el deck). C lleva un
stub sólido chico a la izquierda (para asomarse al borde). D y E son puro dibujo.

OJO: los pozos 3 y 4 siguen siendo SALTABLES con el salto actual (~68px). Para
que "no se pueda pasar por arriba" hay que ENSANCHARLOS (mover instancias Ground
+ correr 2 checkpoints); se dejó para después de playtestear el trepado del
tendido. Ver [[project_gdevelop_state]].

Edita game/game.json (backup .bak-<ts>, idempotente):
  - resources puente_a..e.png
  - objetos PuenteA..E + instancias (1 c/u)

Revertir:  REVERT=1 python3 scripts/wire_puentes.py
Uso:  python3 scripts/wire_puentes.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
MYOBJS = ("PuenteA", "PuenteB", "PuenteC", "PuenteD", "PuenteE")

# name -> (png, ancho, x_inst, y_inst, [polígonos de colisión] o None, sólido?)
BRIDGES = {
    "PuenteA": ("puente_a.png", 88, 874, 110,
                [[(0, 0), (32, 0), (32, 6), (0, 6)],
                 [(52, 0), (88, 0), (88, 6), (52, 6)]], True),
    "PuenteB": ("puente_b.png", 80, 1086, 108,
                [[(0, 2), (80, 2), (80, 8), (0, 8)]], True),
    "PuenteC": ("puente_c.png", 84, 1325, 58,
                [[(0, 52), (16, 52), (16, 59), (0, 59)]], True),
    "PuenteD": ("puente_d.png", 92, 1493, 108, None, False),
    "PuenteE": ("puente_e.png", 60, 1740, 104, None, False),
}


def obj(name, png, mask, solid):
    frame = {"hasCustomCollisionMask": bool(mask), "image": png, "points": [],
             "originPoint": {"name": "origine", "x": 0, "y": 0},
             "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
             "customCollisionMask": [[{"x": x, "y": y} for x, y in poly]
                                     for poly in (mask or [])]}
    behaviors = []
    if solid:
        behaviors = [{"name": "Platform", "type": "PlatformBehavior::PlatformBehavior",
                      "platformType": "NormalPlatform"}]
    return {"adaptCollisionMaskAutomatically": not mask, "assetStoreId": "",
            "name": name, "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": behaviors,
            "animations": [{"name": "Idle", "useMultipleDirections": False,
                            "directions": [{"looping": True, "timeBetweenFrames": 1,
                                            "sprites": [frame]}]}]}


def inst(name, x, y):
    return {"angle": 0, "customSize": False, "height": 0, "layer": "", "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x, "y": y,
            "zOrder": 0, "numberProperties": [], "stringProperties": [],
            "initialVariables": []}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    lay["objects"] = [o for o in lay["objects"] if o["name"] not in MYOBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in MYOBJS]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MYOBJS]
    res[:] = [r for r in res if not r["name"].startswith("puente_")]

    if revert:
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    for name, (png, _width, x, y, mask, solid) in BRIDGES.items():  # noqa: F841
        res.append({"file": f"assets/N1/{png}", "kind": "image", "metadata": "",
                    "name": png, "smoothed": False, "userAdded": True})
        lay["objects"].append(obj(name, png, mask, solid))
        lay["instances"].append(inst(name, x, y))
        if "children" in fs:
            fs["children"].append({"objectName": name})

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("puentes:", [o["name"] for o in lay["objects"] if o["name"] in MYOBJS])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/N1/puente_a.png"), "corré gen_puentes.py primero"
    main(revert=os.environ.get("REVERT") == "1")
