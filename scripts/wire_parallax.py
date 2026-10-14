#!/usr/bin/env python3
"""
wire_parallax.py — parallax del fondo de Level1: el Obelisco y la luna
acompañan a Lio como en la presentación (MainMenu), y las tiras de
edificios se desplazan a distintas velocidades (pedido el 14/10).

En septiembre se había probado con SetCameraX por capa y se revirtió (el
formato no se pudo verificar). Acá las capas siguen a la cámara 1:1 como
hasta ahora y lo que se mueve son los OBJETOS, con acciones ya usadas en el
proyecto:
  - tiras (TiledSprite): XOffset = -(1 - f) * cámara  → la textura se ve
    moverse a f veces la velocidad de la cámara;
  - Obelisco / Luna (Sprite): X = B + (1 - f) * cámara, con B calculado
    para que al arrancar estén en SCREEN0 px de la pantalla.
f = fracción de la velocidad de la cámara (0 = pegado a la pantalla,
1 = mundo). Todo redondeado a píxel entero (pixel art sin temblor).

Agrega la capa BG_farthest (detrás de BG_far) con la tira city_farthest.png
(gen_city_bg.py) y mueve la Luna a esa capa (detrás de todos los edificios).

Idempotente (grupo de eventos propio). GDevelop CERRADO.
Requiere: python3 scripts/gen_city_bg.py
Uso:  python3 scripts/wire_parallax.py   (desde la raíz del repo)
"""
import copy
import datetime
import json
import shutil

from wire_score_hud import act, comment, ev, put_object

GAME = "game/game.json"
SCENE = "Level1"
GROUP = "Parallax del fondo (wire_parallax.py)"
CAM = 'CameraCenterX("")'
CAM0 = 140          # centro de cámara al arrancar (FixCamera: borde izq -100 + 240)
W = 480

# objeto: f
TILES = {"CityFarthest": 0.12, "CityFar": 0.30, "CityNear": 0.55}
# objeto: (f, x en pantalla al arrancar)
SPRITES = {"Luna": (0.03, 412), "Obelisco": (0.15, 372)}
FARTHEST = {"name": "CityFarthest", "texture": "city_farthest.png", "x": -492, "y": 6,
            "w": 4000, "h": 60}


def add_layer(lay):
    if any(l["name"] == "BG_farthest" for l in lay["layers"]):
        return
    far = next(l for l in lay["layers"] if l["name"] == "BG_far")
    new = copy.deepcopy(far)
    new["name"] = "BG_farthest"
    lay["layers"].insert(lay["layers"].index(far), new)     # antes = se dibuja detrás


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    res = g["resources"]["resources"]
    if not any(r["name"] == FARTHEST["texture"] for r in res):
        res.append({"file": f"assets/City/{FARTHEST['texture']}", "kind": "image", "metadata": "",
                    "name": FARTHEST["texture"], "smoothed": False, "userAdded": True})
    lay = next(l for l in g["layouts"] if l["name"] == SCENE)
    add_layer(lay)

    obj = copy.deepcopy(next(o for o in lay["objects"] if o["name"] == "CityFar"))
    obj.update(name=FARTHEST["name"], texture=FARTHEST["texture"], height=FARTHEST["h"])
    put_object(lay, obj)
    lay["instances"] = [i for i in lay["instances"] if i["name"] != FARTHEST["name"]]
    lay["instances"].append({
        "angle": 0, "customSize": True, "width": FARTHEST["w"], "height": FARTHEST["h"],
        "layer": "BG_farthest", "name": FARTHEST["name"], "x": FARTHEST["x"], "y": FARTHEST["y"],
        "zOrder": 0, "numberProperties": [], "stringProperties": [], "initialVariables": []})
    for i in lay["instances"]:
        if i["name"] == "Luna":
            i.update(layer="BG_farthest", zOrder=-1)

    acts = [act("TiledSpriteObject::XOffset", [name, "=", f"round(-{1 - f:.2f} * {CAM})"])
            for name, f in TILES.items()]
    for name, (f, screen0) in SPRITES.items():
        base = round(screen0 - W / 2 + f * CAM0)
        acts.append(act("SetX", [name, "=", f"round({base} + {1 - f:.2f} * {CAM})"]))
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({
        "type": "BuiltinCommonInstructions::Group", "name": GROUP, "source": "",
        "creationTime": 0, "folded": True, "color": {"b": 180, "g": 120, "r": 90},
        "events": [
            comment("Parallax: cada objeto del fondo se ve moverse a f veces la cámara "
                    "(Luna 0.03, edificios lejanos 0.12, Obelisco 0.15, CityFar 0.30, "
                    "CityNear 0.55). Generado por wire_parallax.py."),
            ev([], acts),
        ]})
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{SCENE}: capa BG_farthest + {len(acts)} acciones de parallax")


if __name__ == "__main__":
    main()
