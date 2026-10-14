#!/usr/bin/env python3
"""
wire_luna_level1.py — agrega la luna enferma del MainMenu al cielo de Level1,
al lado (a la derecha) del Obelisco, en la capa BG_far y detrás de la ciudad.

El sprite sale de gen_menu_ui.py (game/assets/Menu/luna.png, 54x54 con halo).
La cámara de Level1 está fija en vertical (FixCamera y: -65..205), así que el
cielo visible arranca en y=-65; la luna queda en la franja alta.

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 la saca.
Uso:  python3 scripts/wire_luna_level1.py    (desde la raíz del repo)
GDevelop tiene que estar CERRADO.
"""
import datetime
import json
import os
import shutil

GAME = "game/game.json"
NAME = "Luna"
IMG = "luna.png"
LAYER = "BG_far"
GAP = 26          # px entre el borde derecho del obelisco y el halo
Y = -64           # tope del sprite (halo incluido)


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lay = next(l for l in d["layouts"] if l["name"] == "Level1")

    # limpiar (idempotente / revert)
    lay["objects"] = [o for o in lay["objects"] if o["name"] != NAME]
    lay["instances"] = [i for i in lay["instances"] if i["name"] != NAME]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") != NAME]

    if not revert:
        res = d["resources"]["resources"]
        if IMG not in {r["name"] for r in res}:
            res.append({"file": f"assets/Menu/{IMG}", "kind": "image", "metadata": "",
                        "name": IMG, "smoothed": False, "userAdded": True})
        assert os.path.exists(f"game/assets/Menu/{IMG}"), "correr antes gen_menu_ui.py"
        lay["objects"].append({
            "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": NAME,
            "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
            "behaviors": [],
            "animations": [{"name": "Idle", "useMultipleDirections": False, "directions": [
                {"looping": False, "timeBetweenFrames": 0.1, "sprites": [
                    {"hasCustomCollisionMask": False, "image": IMG, "points": [],
                     "originPoint": {"name": "origine", "x": 0, "y": 0},
                     "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                     "customCollisionMask": []}]}]}]})
        if "children" in fs:
            fs["children"].append({"objectName": NAME})
        obel = next(i for i in lay["instances"] if i["name"] == "Obelisco")
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": LAYER, "name": NAME,
            "width": 0, "x": obel["x"] + 18 + GAP, "y": Y, "zOrder": -1,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})
        print(f"Luna en ({obel['x'] + 18 + GAP}, {Y}), capa {LAYER}")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else "OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
