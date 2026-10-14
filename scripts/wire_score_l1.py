#!/usr/bin/env python3
"""
wire_score_l1.py — sistema de puntaje, versión mínima (solo Level1).

- Variable GLOBAL Puntaje (para que en el futuro se arrastre a L2/L3).
- Level1 la pone en 0 al arrancar (también al reintentar con R / click).
- Puntos: stomp que mata un zombie +100, antídoto +250, llegar a la meta +1000.
- HUD: texto PuntajeText arriba a la derecha (capa UI), estilo de BossHPText.

Los eventos a parchear se buscan por contenido, no por índice:
  stomp  -> acciones con Delete(Zombies) + sfx_stomp.wav
  antíd. -> acciones con Delete(Antidoto)
  meta   -> acciones con ModVarScene(Won = 1) + Show(VictoryText)

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 lo saca.
Uso:  python3 scripts/wire_score_l1.py    (desde la raíz del repo)
GDevelop tiene que estar CERRADO.
"""
import datetime
import json
import os
import shutil

GAME = "game/game.json"
SCENE = "Level1"
VAR = "Puntaje"
TEXT = "PuntajeText"
X, Y = 392, 14     # HUD: centro vertical alineado con los corazones (8..50, 8)
PTS_STOMP, PTS_ANTIDOTO, PTS_META = 100, 250, 1000


def act(value, params):
    return {"type": {"value": value}, "parameters": params}


def add_points(n):
    return act("ModVarGlobal", [VAR, "+", str(n)])


def is_score_action(a):
    return a["type"]["value"] == "ModVarGlobal" and a["parameters"][0] == VAR


def sig(e):
    return [(a["type"]["value"], a["parameters"]) for a in e.get("actions", [])]


def has(e, value, *params):
    return any(v == value and all(p in ps for p in params) for v, ps in sig(e))


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lay = next(l for l in d["layouts"] if l["name"] == SCENE)

    # limpiar (idempotente / revert)
    for e in lay["events"]:
        if "actions" in e:
            e["actions"] = [a for a in e["actions"] if not is_score_action(a)]
    lay["events"] = [e for e in lay["events"] if VAR not in json.dumps(e)]
    lay["objects"] = [o for o in lay["objects"] if o["name"] != TEXT]
    lay["instances"] = [i for i in lay["instances"] if i["name"] != TEXT]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") != TEXT]
    d["variables"] = [v for v in d["variables"] if v["name"] != VAR]

    if not revert:
        d["variables"].append({"name": VAR, "type": "number", "value": 0})

        targets = {
            "stomp": (lambda e: has(e, "Delete", "Zombies")
                      and has(e, "PlaySound", "sfx_stomp.wav"), PTS_STOMP),
            "antidoto": (lambda e: has(e, "Delete", "Antidoto"), PTS_ANTIDOTO),
            "meta": (lambda e: has(e, "ModVarScene", "Won", "1")
                     and has(e, "Show", "VictoryText"), PTS_META),
        }
        for name, (match, pts) in targets.items():
            hits = [e for e in lay["events"] if match(e)]
            assert len(hits) == 1, f"evento '{name}': {len(hits)} coincidencias"
            hits[0]["actions"].append(add_points(pts))
            print(f"  {name}: +{pts}")

        lay["objects"].append({
            "assetStoreId": "", "name": TEXT, "type": "TextObject::Text",
            "variables": [], "effects": [], "behaviors": [],
            "content": {
                "bold": False, "italic": False, "smoothed": True, "underlined": False,
                "text": "PUNTOS 0", "font": "", "characterSize": 12,
                "color": "240;210;120", "textAlignment": "left",
                "verticalTextAlignment": "center", "isOutlineEnabled": True,
                "outlineThickness": 2, "outlineColor": "12;14;22",
                "isShadowEnabled": False, "shadowColor": "0;0;0", "shadowOpacity": 127,
                "shadowDistance": 4, "shadowAngle": 90, "shadowBlurRadius": 2}})
        if "children" in fs:
            fs["children"].append({"objectName": TEXT})
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": "UI", "name": TEXT,
            "width": 0, "x": X, "y": Y, "zOrder": 30,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})

        lay["events"] += [
            {"type": "BuiltinCommonInstructions::Comment", "color":
                {"r": 255, "g": 230, "b": 206}, "textR": 0, "textG": 0, "textB": 0,
             "comment": f"{VAR}: global, 0 al entrar a Level1; stomp +{PTS_STOMP}, "
                        f"antidoto +{PTS_ANTIDOTO}, meta +{PTS_META} (wire_score_l1.py)."},
            {"type": "BuiltinCommonInstructions::Standard",
             "conditions": [act("BuiltinCommonInstructions::Once", [])],
             "actions": [act("ModVarGlobal", [VAR, "=", "0"])], "events": []},
            {"type": "BuiltinCommonInstructions::Standard", "conditions": [],
             "actions": [act("TextObject::String", [
                 TEXT, "=", f'"PUNTOS " + ToString(GlobalVariable({VAR}))'])],
             "events": []},
        ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else "OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
