#!/usr/bin/env python3
"""
wire_lab_subsuelo.py  —  Nivel 2 y arena del Nivel 3: el "bloque negro" de
debajo del piso del laboratorio pasa a ser el corte del edificio (pedido del
usuario 18/10: "laboratorios con coronavirus encerrados para que no sea un
bloque negro nada más").

Requiere: gen_lab_subsuelo.py (lab_subsuelo.png, contencion[_rota]_0..3.png,
contencion_glow.png).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_lab_subsuelo": true), en Level2 y Level3:
  - LabSubsuelo (TiledSprite): una instancia por tramo de piso (Ground de
    96 px de alto), del mismo ancho, sobre las filas 16..95 de lab_floor.png
    (losa, ducto, cañerías, sala de contención). Los huecos quedan como
    estaban (vidrios rotos al fondo).
  - Contencion / ContencionRota (Sprite, 4 cuadros: el virus flota y gira
    dentro del tubo): repartidos al azar (semilla fija) sobre el piso de
    rejilla de la sala, ~1 de cada 4 roto. Solo decorado por ahora: que los
    rotos suelten un virus queda para otro script.
  - ContencionGlow: halo verde detrás de cada tubo, late despacio (los rotos
    titilan más rápido).
  Todo en la capa de juego (""), z 2..4: el piso (Ground) está en z 1 y
  nada jugable pasa por debajo del canto del piso. Sin comportamientos (no
  colisionan; wire_bordes_plataforma.py no los toma).
Re-correr después de `wire_levels23.py --force` (regenera L2/L3).
Uso:  python3 scripts/wire_lab_subsuelo.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import random
import shutil
import uuid

GAME = "game/game.json"
MARK = "_lab_subsuelo"
SCENES = ("Level2", "Level3")
SUB, TUBE, ROTA, GLOW = "LabSubsuelo", "Contencion", "ContencionRota", "ContencionGlow"
MINE = {SUB, TUBE, ROTA, GLOW}
SLAB = 16            # filas de baldosa de lab_floor.png; el subsuelo va debajo
SUB_H = 80
GRATE = 66           # fila del piso de rejilla dentro de lab_subsuelo.png
TUBE_W, TUBE_H = 24, 40
GAP_MIN, GAP_MAX = 64, 150   # separación entre tubos
MARGIN = 18                  # distancia a los bordes de cada tramo
P_ROTA = 0.25
T = "TimeFromStart()"
RES = (["lab_subsuelo.png", "contencion_glow.png"]
       + [f"contencion_{i}.png" for i in range(4)]
       + [f"contencion_rota_{i}.png" for i in range(4)])


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts, events=()):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
         "actions": acts, MARK: True}
    if events:
        e["events"] = list(events)
    return e


def foreach(obj, acts):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], "events": [
                {"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": acts}],
            MARK: True}


def sprite_obj(base, name, frames, speed, variables=()):
    o = copy.deepcopy(base)
    o["name"] = name
    o["behaviors"] = []
    o["effects"] = []
    o["variables"] = [{"name": k, "type": "number", "value": v} for k, v in variables]
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": len(frames) > 1, "timeBetweenFrames": speed, "sprites": [{
            "hasCustomCollisionMask": False, "image": f, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []} for f in frames]}]}]
    return o


def inst(name, x, y, z, w=None, h=None, vars_=()):
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": "",
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def wire_scene(sc, seed):
    # ---- limpieza (idempotente) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]

    # ---- objetos ----
    ground = next(o for o in sc["objects"] if o["name"] == "Ground")
    sub = copy.deepcopy(ground)            # TiledSprite: misma forma, sin Platform
    sub["name"] = SUB
    sub["texture"] = "lab_subsuelo.png"
    sub["behaviors"] = []
    sub["effects"] = []
    sub["variables"] = []
    base = next(o for o in sc["objects"] if o["name"] == "LampGlow")   # un Sprite cualquiera
    sc["objects"] += [
        sub,
        sprite_obj(base, TUBE, [f"contencion_{i}.png" for i in range(4)], 0.28),
        sprite_obj(base, ROTA, [f"contencion_rota_{i}.png" for i in range(4)], 0.22),
        sprite_obj(base, GLOW, ["contencion_glow.png"], 1, [("Seed", 0), ("Fast", 0)]),
    ]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in (SUB, TUBE, ROTA, GLOW)]

    # ---- instancias: un subsuelo por tramo de piso + tubos repartidos ----
    rnd = random.Random(seed)
    floors = sorted((i for i in sc["instances"] if i["name"] == "Ground"
                     and round(i.get("height", 0)) == 96 and i["y"] > 0), key=lambda i: i["x"])
    new, n_rota = [], 0
    for g in floors:
        gx, gy, gw = g["x"], g["y"], g["width"]
        new.append(inst(SUB, gx, gy + SLAB, 2, gw, SUB_H))
        tube_y = gy + SLAB + GRATE - TUBE_H
        x = gx + MARGIN + rnd.randint(0, 40)
        while x + TUBE_W <= gx + gw - MARGIN:
            rota = rnd.random() < P_ROTA
            n_rota += rota
            seed_v = round(rnd.uniform(0, 6.28), 2)
            new.append(inst(GLOW, x - 12, tube_y - 8, 3, vars_=[("Seed", seed_v), ("Fast", int(rota))]))
            new.append(inst(ROTA if rota else TUBE, x, tube_y, 4))
            x += rnd.randint(GAP_MIN, GAP_MAX)
    sc["instances"] += new

    # ---- eventos ----
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Subsuelo del lab (wire_lab_subsuelo.py): tubos de contención con virus "
                    "(cuadro inicial al azar para que no floten sincronizados) y halo verde que "
                    "late (los rotos titilan).",
         "comment2": "", MARK: True},
        std([ins("BuiltinCommonInstructions::Once", [])], [], [
            foreach(TUBE, [ins("ChangeSprite", [TUBE, "=", "RandomInRange(0, 3)"])]),
            foreach(ROTA, [ins("ChangeSprite", [ROTA, "=", "RandomInRange(0, 3)"])]),
        ]),
        foreach(GLOW, [ins("Opacity", [GLOW, "=",
            f"round(255 * (0.72 + 0.18 * sin({T} * (1.6 + {GLOW}.Variable(Fast) * 9) + {GLOW}.Variable(Seed))"
            # floor(0.5*sin + 0.7) = 1 solo si sin > 0.6: bajón corto (tubo roto)
            f" - {GLOW}.Variable(Fast) * 0.3 * floor(0.5 * sin({T} * 23 + {GLOW}.Variable(Seed) * 3) + 0.7)))"])]),
    ]
    tubes = sum(1 for i in new if i["name"] in (TUBE, ROTA))
    print(f"{sc['name']}: {len(floors)} tramos de piso | {tubes} tubos ({n_rota} rotos)")


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm in RES:
        if nm not in have:
            res.append({"file": f"assets/Lab/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})
    for k, name in enumerate(SCENES):
        wire_scene(next(x for x in d["layouts"] if x["name"] == name), 1810 + k)
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Lab/lab_subsuelo.png"), "corré gen_lab_subsuelo.py primero"
    main()
