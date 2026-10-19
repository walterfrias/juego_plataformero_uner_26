#!/usr/bin/env python3
"""
wire_grafitis_n1.py — pone en Level1 las pintadas del muro de la costanera
(gen_grafitis_n1.py: Malvinas al comienzo, Patricio Rey y el esclavo de
Oktubre en el centro, la Ley de Financiamiento Universitario antes de la meta).

Un objeto Sprite por pintada (Grafiti_<nombre>), capa base, z −2: delante del
muro (Embankment, z −3) y detrás de todo lo jugable. Llevan el mismo efecto
"Noche" que el muro (Adjustment, brillo 0.62): la pared está en sombra y la
pintura también. Sin colisión ni comportamientos: solo decorado.

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 las saca.
Uso:  python3 scripts/gen_grafitis_n1.py && python3 scripts/wire_grafitis_n1.py
GDevelop tiene que estar CERRADO.
"""
import copy
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402
from gen_grafitis_n1 import PINTADAS  # noqa: E402

GAME = "game/game.json"
PREFIJO = "Grafiti_"
Z = -2


def nombre_objeto(pintada):
    """grafiti_malvinas → Grafiti_Malvinas"""
    return PREFIJO + pintada.split("_", 1)[1].capitalize()


def main(revert=False):
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lay = next(l for l in d["layouts"] if l["name"] == "Level1")

    # limpiar (idempotente / revert)
    lay["objects"] = [o for o in lay["objects"] if not o["name"].startswith(PREFIJO)]
    lay["instances"] = [i for i in lay["instances"] if not i["name"].startswith(PREFIJO)]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if not c.get("objectName", "").startswith(PREFIJO)]

    if not revert:
        muro = next(o for o in lay["objects"] if o["name"] == "Embankment")
        noche = copy.deepcopy(next(e for e in muro["effects"] if e["name"] == "Noche"))
        res = d["resources"]["resources"]
        nombres = {r["name"] for r in res}
        for pintada, p in PINTADAS.items():
            img = f"{pintada}.png"
            assert os.path.exists(f"game/assets/City/{img}"), "correr antes gen_grafitis_n1.py"
            if img not in nombres:
                res.append({"file": f"assets/City/{img}", "kind": "image", "metadata": "",
                            "name": img, "smoothed": False, "userAdded": True})
            obj = nombre_objeto(pintada)
            lay["objects"].append({
                "adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": obj,
                "type": "Sprite", "updateIfNotVisible": False, "variables": [],
                "effects": [copy.deepcopy(noche)], "behaviors": [],
                "animations": [{"name": "Idle", "useMultipleDirections": False, "directions": [
                    {"looping": False, "timeBetweenFrames": 0.1, "sprites": [
                        {"hasCustomCollisionMask": False, "image": img, "points": [],
                         "originPoint": {"name": "origine", "x": 0, "y": 0},
                         "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                         "customCollisionMask": []}]}]}]})
            if "children" in fs:
                fs["children"].append({"objectName": obj})
            lay["instances"].append({
                "angle": 0, "customSize": False, "height": 0, "layer": "", "name": obj,
                "width": 0, "x": p["x"], "y": p["y"], "zOrder": Z,
                "numberProperties": [], "stringProperties": [], "initialVariables": []})
            print(f"{obj} en ({p['x']}, {p['y']})")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else "OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
