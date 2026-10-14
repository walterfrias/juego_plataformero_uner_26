#!/usr/bin/env python3
"""
wire_trees.py  —  coloca los 2 árboles (ArbolBajo / ArbolAlto) como
decoración en la capa `Decor` del Nivel 1 (detrás de la acción). Sin
comportamiento.

Requiere: scripts/gen_trees.py corrido.

Edita game/game.json (backup .bak-<ts>, idempotente):
  - resources ArbolBajo.png / ArbolAlto.png
  - objetos Sprite `ArbolBajo` / `ArbolAlto` (anim Idle, sin behaviors)
  - instancias repartidas a lo largo del nivel, en capa `Decor`, pie al piso

Revertir:  REVERT=1 python3 scripts/wire_trees.py
Uso:  python3 scripts/wire_trees.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
GROUND_Y = 110

TREES = {  # nombre: (archivo, alto)
    "ArbolBajo": ("assets/City/ArbolBajo.png", 44),
    "ArbolAlto": ("assets/City/ArbolAlto.png", 80),
}
NAMES = list(TREES)

# (objeto, x)  — evita la cadena del N1 (x120-340) y el hueco (x1730-1970)
PLACES = [
    ("ArbolAlto", 95),
    ("ArbolBajo", 430),
    ("ArbolAlto", 610),
    ("ArbolBajo", 800),
    ("ArbolAlto", 1050),
    ("ArbolBajo", 1300),
    ("ArbolAlto", 1560),
    ("ArbolBajo", 2060),
    ("ArbolAlto", 2320),
]


def one_frame_anim(img):
    return {"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": False, "timeBetweenFrames": 1.0, "sprites": [{
            "hasCustomCollisionMask": False, "image": img, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}]}]}


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
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NAMES]

    if revert:
        res[:] = [r for r in res if r["name"] not in (f"{n}.png" for n in NAMES)]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # tope de copa (coords de píxel) — plataforma Jumpthru; ver
    # scripts/wire_platform_props.py, que también lo (re)aplica sin tocar
    # instancias.
    CROWN_MASK = {
        "ArbolBajo": [(6, 2), (36, 2), (36, 9), (6, 9)],
        "ArbolAlto": [(8, 2), (40, 2), (40, 10), (8, 10)],
    }

    have = {r["name"] for r in res}
    for name, (path, _h) in TREES.items():
        nm = f"{name}.png"
        if nm not in have:
            res.append({"file": path, "kind": "image", "metadata": "", "name": nm,
                        "smoothed": False, "userAdded": True})
        anim = one_frame_anim(nm)
        poly = [{"x": x, "y": y} for x, y in CROWN_MASK[name]]
        for spr in anim["directions"][0]["sprites"]:
            spr["hasCustomCollisionMask"] = True
            spr["customCollisionMask"] = [poly]
        lay["objects"].append({
            "adaptCollisionMaskAutomatically": False, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [],
            "behaviors": [{"name": "Platform", "type": "PlatformBehavior::PlatformBehavior",
                           "platformType": "Jumpthru"}],
            "animations": [anim]})
        if "children" in fs:
            fs["children"].append({"objectName": name})

    for obj, x in PLACES:
        h = TREES[obj][1]
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": "Decor", "name": obj,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x,
            "y": GROUND_Y - h, "zOrder": 1,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("árboles:", [o["name"] for o in lay["objects"] if o["name"] in NAMES],
          "| instancias totales:", len(lay["instances"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/ArbolBajo.png"), "corré gen_trees.py primero"
    main(revert=os.environ.get("REVERT") == "1")
