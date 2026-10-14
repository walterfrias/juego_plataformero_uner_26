#!/usr/bin/env python3
"""
wire_pause_panel.py — menú de pausa de Level1/2/3 con el mismo panel que el
MainMenu (wire_main_menu_v2.py): velo oscuro sobre el nivel, panel de
hormigón con cinta de cuarentena, título PAUSA en ámbar, barras de volumen
y ayudas en la pixel font del juego.

No toca la lógica de la pausa (toggle ESC/P con estado intermedio
Paused=2, ver fix_pause_toggle.py; R reinicia; M al menú; espejo a
SettingsOpen; Link a SettingsControls). Solo:
  1. PauseTitle / PauseMusic / PauseSfx / PauseHint pasan de TextObject a
     Sprite con el MISMO nombre, así los Show/Hide existentes siguen
     funcionando tal cual.
  2. El evento que escribía "Musica: 80%" ahora elige la animación de la
     barra: SetAnimationName "v" + ToString(volumen / 10).
  3. Objetos nuevos PauseDim (velo) y PausePanel, con visibilidad
     declarativa derivada de Paused (=1 visible, si no oculto).

Requiere:  python3 scripts/gen_menu_ui.py
Edita game/game.json (backup .bak-<ts>, idempotente). GDevelop CERRADO.
Uso:  python3 scripts/wire_pause_panel.py    (desde la raíz del repo)
"""
import datetime
import json
import os
import shutil

GAME = "game/game.json"
LEVELS = ["Level1", "Level2", "Level3"]
W, H = 480, 270
PW, PH = 200, 124
PX, PY = (W - PW) // 2, 70
Z_DIM, Z_PANEL, Z_ITEMS = 31, 32, 33
TAG = "Pausa: panel + velo, visibles solo con Paused = 1 (wire_pause_panel.py)."

IMAGES = (["pause_dim.png", "pause_panel.png", "pause_title.png", "pause_hint.png"]
          + [f"pause_{k}_{i}.png" for k in ("music", "sfx") for i in range(11)])


def frame(img):
    return {"hasCustomCollisionMask": False, "image": img, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def sprite(name, anims):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
            "behaviors": [],
            "animations": [{"name": a, "useMultipleDirections": False,
                            "directions": [{"looping": False, "timeBetweenFrames": 0.1,
                                            "sprites": [frame(img)]}]} for a, img in anims]}


def inst(name, x, y, z, w=0, h=0):
    return {"angle": 0, "customSize": bool(w), "height": h, "layer": "UI", "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def act(t, params):
    return {"type": {"value": t}, "parameters": params}


OBJECTS = {
    "PauseDim": sprite("PauseDim", [("Idle", "pause_dim.png")]),
    "PausePanel": sprite("PausePanel", [("Idle", "pause_panel.png")]),
    "PauseTitle": sprite("PauseTitle", [("Idle", "pause_title.png")]),
    "PauseMusic": sprite("PauseMusic", [(f"v{i}", f"pause_music_{i}.png") for i in range(11)]),
    "PauseSfx": sprite("PauseSfx", [(f"v{i}", f"pause_sfx_{i}.png") for i in range(11)]),
    "PauseHint": sprite("PauseHint", [("Idle", "pause_hint.png")]),
}

INSTANCES = [
    inst("PauseDim", 0, 0, Z_DIM, W, H),
    inst("PausePanel", PX, PY, Z_PANEL),
    inst("PauseTitle", PX + (PW - 62) // 2, PY + 12, Z_ITEMS),
    inst("PauseMusic", PX + 12, PY + 42, Z_ITEMS),
    inst("PauseSfx", PX + 12, PY + 60, Z_ITEMS),
    inst("PauseHint", PX + (PW - 141) // 2, PY + 77, Z_ITEMS),   # 4 líneas + mochila (I: MOCHILA)
]

BAR_ANIM = {"PauseMusic": '"v" + ToString(GlobalVariable(MusicVolume) / 10)',
            "PauseSfx": '"v" + ToString(GlobalVariable(SfxVolume) / 10)'}


def visibility_events():
    names = ["PauseDim", "PausePanel"]
    return [
        {"type": "BuiltinCommonInstructions::Comment",
         "color": {"b": 0, "g": 0, "r": 0, "textB": 0, "textG": 0, "textR": 0}, "comment": TAG},
        {"type": "BuiltinCommonInstructions::Standard",
         "conditions": [act("VarScene", ["Paused", "=", "1"])],
         "actions": [act("Show", [n, ""]) for n in names]},
        {"type": "BuiltinCommonInstructions::Standard",
         "conditions": [act("VarScene", ["Paused", "!=", "1"])],
         "actions": [act("Hide", [n]) for n in names]},
    ]


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get("events", []))


def wire_level(lay):
    # objetos: reemplaza por nombre (idempotente), conserva la posición en la lista
    idx = {o["name"]: i for i, o in enumerate(lay["objects"])}
    for name, obj in OBJECTS.items():
        if name in idx:
            lay["objects"][idx[name]] = json.loads(json.dumps(obj))
        else:
            lay["objects"].append(json.loads(json.dumps(obj)))
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        have = {c.get("objectName") for c in fs["children"]}
        fs["children"] += [{"objectName": n} for n in OBJECTS if n not in have]

    lay["instances"] = [i for i in lay["instances"] if i["name"] not in OBJECTS] + \
        json.loads(json.dumps(INSTANCES))

    # texto de volumen -> animación de barra
    swapped = 0
    for e in walk(lay["events"]):
        for a in e.get("actions", []):
            obj = a["parameters"][0] if a["parameters"] else None
            if a["type"]["value"] == "TextObject::String" and obj in BAR_ANIM:
                a["type"]["value"] = "SetAnimationName"
                a["parameters"] = [obj, BAR_ANIM[obj]]
                swapped += 1
            elif a["type"]["value"] == "SetAnimationName" and obj in BAR_ANIM:
                swapped += 1
    assert swapped == 2, f"{lay['name']}: esperaba 2 acciones de volumen, hay {swapped}"

    # visibilidad del panel/velo (reemplaza la versión anterior si existe)
    evs = lay["events"]
    for k, e in enumerate(evs):
        if e.get("comment") == TAG:
            del evs[k:k + 3]
            break
    evs += visibility_events()


def main():
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    for img in IMAGES:
        assert os.path.exists(f"game/assets/Menu/{img}"), f"falta {img}: correr gen_menu_ui.py"
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))

    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for img in IMAGES:
        if img not in have:
            res.append({"file": f"assets/Menu/{img}", "kind": "image", "metadata": "",
                        "name": img, "smoothed": False, "userAdded": True})

    for name in LEVELS:
        wire_level(next(l for l in d["layouts"] if l["name"] == name))
        print(name, "OK")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


if __name__ == "__main__":
    main()
