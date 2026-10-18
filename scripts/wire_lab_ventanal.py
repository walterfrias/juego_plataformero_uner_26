#!/usr/bin/env python3
"""
wire_lab_ventanal.py  —  Nivel 2: la ciudad de noche se ve por los
ventanales del laboratorio y se mueve con parallax, como en el Nivel 1
(pedido del usuario 16/10: "el level2 aún está verde").

Requiere: gen_lab_ventanal.py (lab_far_ventanal.png, lab_ventana_luz.png) y
el arte de la noche de L1 (gen_city_bg.py, gen_noche_n1.py).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_lab_ventanal": true):
  - LabFar de L2 pasa a lab_far_ventanal.png (vidrio transparente). El de
    L3 no se toca (sigue con lab_far.png, ciudad pintada).
  - capa nueva `BG_city` detrás de BG_far, con copias de los objetos de la
    noche de L1 (mismo arte y efectos): NocheCielo, NocheNubes, Luna,
    CityFarthest, CityFar, CityNear, NocheIncendio + NocheHumo (5 incendios).
    Todo 40 px más arriba que en L1: el lab está en un piso alto y por los
    ventanales (y -50..40 del mundo) se ven los techos, no la calle.
  - parallax igual que L1 (f = cuánto se mueve respecto de la cámara):
    Luna 0.03, CityFarthest 0.12, incendios 0.2, CityFar 0.30, CityNear 0.55;
    la pared (BG_far) va 1:1, así la ciudad se desliza detrás del vidrio.
  - LabVentanaLuz: resplandor anaranjado de los incendios debajo de cada
    ventanal (BG_far, encima de la pared), titila como el fuego de L1.
Re-correr después de `wire_levels23.py --force` (regenera L2).
Uso:  python3 scripts/wire_lab_ventanal.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import uuid

GAME = "game/game.json"
MARK = "_lab_ventanal"
LAYER = "BG_city"
CITY_OBJS = ["NocheCielo", "NocheNubes", "Luna", "CityFarthest", "CityFar", "CityNear",
             "NocheIncendio", "NocheHumo"]
LUZ = "LabVentanaLuz"
DY = -40                     # todo más arriba que en L1 (piso alto)
X0, W = -300, 4600           # tiras: cubren la cámara de L2 (x -100..3800)
FIRE_BASES = [0, 300, 600, 900, 1200]   # se ven en pantalla en x = base + 240 - 0.2*cam
LAB_X, LAB_Y, TILE = -300, -66, 224     # instancia LabFar de L2
WINDOWS_X = [(10, 104), (120, 214)]     # en el tile (gen_lab_ventanal.py)
WIN_BOTTOM = 106
CAM = 'CameraCenterX("")'
T = "TimeFromStart()"


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, MARK: True}


def foreach(obj, acts):
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], "events": [
                {"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": acts}],
            MARK: True}


def inst(name, x, y, z, w=None, h=None, vars_=()):
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": LAYER if name != LUZ else "BG_far",
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def flicker(obj, base, a, b):
    return (f"round(255 * ({base} + {a} * sin({T} * 3.1 + {obj}.Variable(Seed)) "
            f"+ {b} * sin({T} * 7.3 + {obj}.Variable(Seed) * 2)))")


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    l1 = next(x for x in d["layouts"] if x["name"] == "Level1")
    l2 = next(x for x in d["layouts"] if x["name"] == "Level2")
    res = d["resources"]["resources"]

    # ---- recursos ----
    have = {r["name"] for r in res}
    for nm in ("lab_far_ventanal.png", "lab_ventana_luz.png"):
        if nm not in have:
            res.append({"file": f"assets/Lab/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})

    # ---- limpieza (idempotente) ----
    mine = set(CITY_OBJS + [LUZ])
    l2["objects"] = [o for o in l2["objects"] if o["name"] not in mine]
    l2["instances"] = [i for i in l2["instances"] if i["name"] not in mine]
    l2["events"] = [e for e in l2["events"] if not e.get(MARK)]
    l2["layers"] = [ly for ly in l2["layers"] if ly["name"] != LAYER]
    fs = l2.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in mine]

    # ---- pared con vidrio ----
    labfar = next(o for o in l2["objects"] if o["name"] == "LabFar")
    labfar["texture"] = "lab_far_ventanal.png"

    # ---- capa de la ciudad, detrás de todo ----
    base_layer = copy.deepcopy(next(ly for ly in l2["layers"] if ly["name"] == "BG_far"))
    base_layer["name"] = LAYER
    base_layer["effects"] = []
    l2["layers"].insert(0, base_layer)

    # ---- objetos: copias de los de L1 + el resplandor ----
    l1objs = {o["name"]: o for o in l1["objects"]}
    for n in CITY_OBJS:
        l2["objects"].append(copy.deepcopy(l1objs[n]))
    luz = copy.deepcopy(l1objs["NocheIncendio"])   # Sprite con vars Base/Seed
    luz["name"] = LUZ
    luz["effects"] = []
    luz["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": False, "timeBetweenFrames": 1, "sprites": [{
            "hasCustomCollisionMask": False, "image": "lab_ventana_luz.png", "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}]}]}]
    l2["objects"].append(luz)
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in CITY_OBJS + [LUZ]]

    # ---- instancias (y de L1 + DY) ----
    l1i = {i["name"]: i for i in l1["instances"]}
    ys = {n: l1i[n]["y"] + DY for n in CITY_OBJS}
    new = [
        inst("NocheCielo", X0, ys["NocheCielo"], -10, W, 270),
        inst("Luna", 176, -46, -1),
        inst("CityFarthest", X0, ys["CityFarthest"], 0, W, 60),
        inst("NocheNubes", X0, -100, 4, W, 80),
        inst("CityFar", X0, ys["CityFar"], 6, W, 70),
        inst("CityNear", X0, ys["CityNear"], 8, W, 96),
    ]
    for k, b in enumerate(FIRE_BASES):
        new.append(inst("NocheIncendio", b, ys["NocheIncendio"], 2, vars_=[("Base", b), ("Seed", 1.3 + k * 1.7)]))
        new.append(inst("NocheHumo", b + 38, ys["NocheHumo"], 1, vars_=[("Base", b + 38)]))
    n_tiles = -(-l2_labfar_width(l2) // TILE)
    k = 0
    for t in range(n_tiles):
        for wx0, wx1 in WINDOWS_X:
            cx = LAB_X + t * TILE + (wx0 + wx1) // 2
            new.append(inst(LUZ, cx - 50, LAB_Y + WIN_BOTTOM + 4, 1, vars_=[("Seed", round(k * 2.39 % 6.28, 2))]))
            k += 1
    l2["instances"] += new

    # ---- eventos ----
    evs = [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Ciudad por los ventanales (wire_lab_ventanal.py): parallax como L1 "
                    "(Luna 0.03, CityFarthest 0.12, incendios 0.2, CityFar 0.30, CityNear 0.55); "
                    "la pared va 1:1. LabVentanaLuz: resplandor de los incendios que titila.",
         "comment2": "", MARK: True},
        std([], [
            ins("TiledSpriteObject::XOffset", ["NocheCielo", "=", f"round(-{CAM})"]),
            ins("TiledSpriteObject::XOffset", ["NocheNubes", "=", f"round(-0.98 * {CAM} + {T} * 3.0)"]),
            ins("TiledSpriteObject::XOffset", ["CityFarthest", "=", f"round(-0.88 * {CAM})"]),
            ins("TiledSpriteObject::XOffset", ["CityFar", "=", f"round(-0.70 * {CAM})"]),
            ins("TiledSpriteObject::XOffset", ["CityNear", "=", f"round(-0.45 * {CAM})"]),
            ins("SetX", ["Luna", "=", f"round(176 + 0.97 * {CAM})"]),
        ]),
        foreach("NocheIncendio", [
            ins("SetX", ["NocheIncendio", "=", f"round(NocheIncendio.Variable(Base) + 0.80 * {CAM})"]),
            ins("Opacity", ["NocheIncendio", "=", flicker("NocheIncendio", 0.78, 0.12, 0.1)]),
        ]),
        foreach("NocheHumo", [
            ins("SetX", ["NocheHumo", "=", f"round(NocheHumo.Variable(Base) + 0.80 * {CAM})"]),
        ]),
        foreach(LUZ, [ins("Opacity", [LUZ, "=", flicker(LUZ, 0.62, 0.22, 0.16)])]),
    ]
    l2["events"] += evs

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("L2: capa", LAYER, "| objetos", len(CITY_OBJS) + 1, "| instancias", len(new), "| eventos", len(evs))


def l2_labfar_width(l2):
    return int(next(i for i in l2["instances"] if i["name"] == "LabFar")["width"])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Lab/lab_far_ventanal.png"), "corré gen_lab_ventanal.py primero"
    main()
