#!/usr/bin/env python3
"""
wire_costanera.py  —  mete en Level1 el muro de la Costanera + el río + los
caños de desagüe (assets de gen_costanera.py).

Edita game/game.json (backup .bak-<ts>, idempotente):
  - Ground: instancia de 110px -> 14px de alto (vuelve a ser solo el cordón
    caminable; el cuerpo de abajo ahora lo hace el muro).
  - objetos nuevos (todos sin behavior, solo visual):
      Embankment  TiledSprite  muro de hormigón   y 122..162  zOrder -3
      River       TiledSprite  agua del río       y 158..308  zOrder -2
      RiverFoam   TiledSprite  espuma en la orilla y 156..162 zOrder -1
      DrainPipe   Sprite       boca de caño (x5)  y~130       zOrder 0
      DrainStream Sprite (4f)  chorro de agua (x5) y~140      zOrder 0
  - eventos: scroll de XOffset de River y RiverFoam (agua que fluye aunque
    estés parado).

Revertir:  restaurar el .bak-<ts>  (o REVERT=1 para sacar objetos+instancias).
Uso:  python3 scripts/wire_costanera.py   (desde la raíz del repo)
Después en GDevelop: cerrar sin guardar + abrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"
LVL_X0, LVL_W = -200, 2800
PIPE_XS = [150, 560, 1050, 1580, 2120]

NEW_OBJECTS = ["Embankment", "River", "RiverFoam", "DrainPipe", "DrainStream",
               "DrainSplash"]
STREAM_FILES = [f"drain_stream_{k}.png" for k in range(1, 5)]
SPLASH_FILES = [f"drain_splash_{k}.png" for k in range(1, 5)]


def tiled(name, tex, w, h):
    return {"assetStoreId": "", "name": name, "texture": tex,
            "type": "TiledSpriteObject::TiledSprite",
            "width": w, "height": h,
            "variables": [], "effects": [], "behaviors": []}


def spr(name, frames, tbf, loop):
    return {
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
        "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{
            "name": "Idle", "useMultipleDirections": False,
            "directions": [{
                "looping": loop, "timeBetweenFrames": tbf,
                "sprites": [{
                    "hasCustomCollisionMask": False, "image": img, "points": [],
                    "originPoint": {"name": "origine", "x": 0, "y": 0},
                    "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                    "customCollisionMask": [],
                } for img in frames],
            }],
        }],
    }


def inst(name, x, y, z, w=0, h=0, custom=False):
    return {"angle": 0, "customSize": custom, "height": h, "layer": "",
            "name": name, "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def std(actions):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": [], "actions": actions}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # limpiar lo previo (idempotente / revert)
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NEW_OBJECTS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in NEW_OBJECTS]
    lay["events"] = [e for e in lay["events"]
                     if not any(a.get("parameters", [""])[0] in ("River", "RiverFoam")
                                for a in e.get("actions", []))]
    # folder structure
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NEW_OBJECTS]

    # Ground: alto 14 (revert -> 110)
    for i in lay["instances"]:
        if i["name"] == "Ground":
            i["height"] = 110 if revert else 14
            i["customSize"] = True
    print("Ground alto ->", 110 if revert else 14)

    all_files = ["embankment.png", "river.png", "river_foam.png", "drain_pipe.png",
                 *STREAM_FILES, *SPLASH_FILES]

    if revert:
        res[:] = [r for r in res if r["name"] not in all_files]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK")
        return

    # --- resources ---
    have = {r["name"] for r in res}
    for fn in all_files:
        if fn not in have:
            res.append({"file": f"assets/City/{fn}", "kind": "image", "metadata": "",
                        "name": fn, "smoothed": False, "userAdded": True})

    # --- objetos ---
    lay["objects"] += [
        tiled("Embankment", "embankment.png", LVL_W, 60),
        tiled("River", "river.png", LVL_W, 150),
        tiled("RiverFoam", "river_foam.png", LVL_W, 8),
        spr("DrainPipe", ["drain_pipe.png"], 0.15, True),
        spr("DrainStream", STREAM_FILES, 0.11, True),
        spr("DrainSplash", SPLASH_FILES, 0.16, True),
    ]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in NEW_OBJECTS]

    # --- instancias --- (cordón caminable en y=110)
    lay["instances"] += [
        inst("Embankment", LVL_X0, 120, -3, LVL_W, 60, True),
        inst("River", LVL_X0, 178, -2, LVL_W, 150, True),
        inst("RiverFoam", LVL_X0, 174, -1, LVL_W, 8, True),
    ]
    for x in PIPE_XS:
        lay["instances"].append(inst("DrainPipe", x, 122, 0))       # 48x48, boca ~y167
        lay["instances"].append(inst("DrainStream", x + 6, 158, 1))   # 36x27 ancho y corto
        lay["instances"].append(inst("DrainSplash", x, 170, 2))       # 48x14 sobre el agua

    # --- eventos: agua que fluye ---
    lay["events"] += [
        std([{"type": {"value": "XOffset"}, "parameters": ["River", "+", "3 * TimeDelta()"]},
             {"type": {"value": "XOffset"}, "parameters": ["RiverFoam", "+", "2 * TimeDelta()"]}]),
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("objetos:", [o["name"] for o in lay["objects"]])
    print("instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]),
          "| resources:", len(res))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/embankment.png"), "corré gen_costanera.py primero"
    main(revert=os.environ.get("REVERT") == "1")
