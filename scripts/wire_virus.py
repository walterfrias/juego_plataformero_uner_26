#!/usr/bin/env python3
"""
wire_virus.py  —  mete 5 virus voladores (obstáculo aéreo) en el Nivel 1,
en 3 tamaños (16x16 nativo ×2, y 3 más chicos: 12/10/13px).

Diseño (confirmado con el usuario 2026-09-13):
  - Vuelo errático con rebote: cada 1.5-2.5s el virus elige un ángulo
    nuevo al azar y vuela en línea recta a velocidad constante (55 px/s);
    si sale de su caja de patrulla (spawn ± rango), se lo fuerza a
    "rebotar" eligiendo un ángulo aleatorio dentro de la mitad que lo
    devuelve adentro. No hay animación de muerte: es un obstáculo, no
    se puede eliminar (a diferencia de los zombies).
  - Al tocar a Lio: -1 vida + empuje horizontal (knockback) en la
    dirección opuesta al virus + un pequeño salto hacia arriba. Reusa
    el mismo cooldown "Invuln" del Player que ya usan los zombies (así
    un golpe de zombie + virus casi simultáneo no descuenta 2 vidas).

  Sigue el patrón de este repo (1 objeto por instancia con su propia
  scene var, como ZombieF/ZombieFDir) en vez de variables de objeto
  por-instancia, que no se usan en ningún otro lado de este game.json.

Requiere: scripts/gen_virus.py corrido (game/assets/Virus/virus_1..6.png).

Edita game/game.json (backup .bak-<ts>, idempotente, marca los eventos
propios con "_virus": true):
  - resources virus_1..6.png
  - objetos Virus1, Virus2 (Sprite, anim "Idle" loop, 6 frames)
  - scene vars Virus1Angle/Virus1NextChange, Virus2Angle/Virus2NextChange
  - 1 instancia de cada uno (spawn spot = centro de su caja de patrulla)
  - eventos: seed inicial de ángulo random; movimiento cada frame;
    retarget random cada 1.5-2.5s; rebote en los 4 bordes de la caja;
    daño por colisión con Player (2 variantes según el lado)

Revertir:  REVERT=1 python3 scripts/wire_virus.py
Uso:  python3 scripts/wire_virus.py   (desde la raíz del repo, con
      GDevelop CERRADO — si está abierto, al guardar pisa este script)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
N_FRAMES = 6

# (nombre, spawn_x, spawn_y, rango_x, rango_y, tamaño_px | None=nativo 16x16)
# a pedido del usuario 2026-09-13: sumar más, en tamaños distintos, siempre
# más chicos que el original (16x16).
VIRUSES = [
    ("Virus1", 250, 55, 90, 40, None),
    ("Virus2", 850, 50, 90, 40, None),
    ("Virus3", 150, 60, 70, 35, 12),
    ("Virus4", 620, 40, 70, 35, 10),
    ("Virus5", 2250, 55, 70, 35, 13),
]
SPEED = 55

MYOBJS = [v[0] for v in VIRUSES]
MYVARS = [f"{n}Angle" for n, *_ in VIRUSES] + [f"{n}NextChange" for n, *_ in VIRUSES]


def cond(value, params):
    return {"type": {"value": value}, "parameters": params}


def act(value, params):
    return cond(value, params)


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts, "_virus": True}


def sprite_frame(image):
    return {"hasCustomCollisionMask": False, "image": image, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def virus_object(name):
    return {
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": name, "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Idle", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 0.1,
                                        "sprites": [sprite_frame(f"virus_{i}.png")
                                                    for i in range(1, N_FRAMES + 1)]}]}]}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # ---- limpieza (idempotente / revert) ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in MYOBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in MYOBJS]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in MYVARS]
    lay["events"] = [e for e in lay["events"] if not e.get("_virus")]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MYOBJS]

    if revert:
        res[:] = [r for r in res if not r["name"].startswith("virus_")]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # ---- resources ----
    have = {r["name"] for r in res}
    for i in range(1, N_FRAMES + 1):
        nm = f"virus_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/Virus/{nm}", "kind": "image",
                        "metadata": "", "name": nm, "smoothed": False,
                        "userAdded": True})

    # ---- objetos + instancias ----
    for name, sx, sy, _rx, _ry, size in VIRUSES:
        lay["objects"].append(virus_object(name))
        custom = size is not None
        wh = size if custom else 0
        lay["instances"].append({
            "angle": 0, "customSize": custom, "height": wh, "layer": "",
            "name": name, "persistentUuid": str(uuid.uuid4()),
            "width": wh, "x": sx, "y": sy, "zOrder": 6,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in MYOBJS]

    # ---- scene vars ----
    for n in MYVARS:
        lay["variables"].append({"name": n, "type": "number", "value": 0})

    RAND_ANGLE = "Random(359)*3.14159265/180"
    RAND_NEXT = "1.5+Random(100)/100"

    evs = []
    for name, sx, sy, rx, ry, _size in VIRUSES:
        ang_var = f"{name}Angle"
        next_var = f"{name}NextChange"
        left, right = sx - rx, sx + rx
        top, bottom = sy - ry, sy + ry

        # seed inicial (una vez, al empezar la escena)
        evs.append(std(
            [cond("BuiltinCommonInstructions::Once", [])],
            [act("ResetObjectTimer", [name, '"Retarget"']),
             act("ModVarScene", [ang_var, "=", RAND_ANGLE]),
             act("ModVarScene", [next_var, "=", RAND_NEXT])]))

        # movimiento continuo
        evs.append(std(
            [],
            [act("SetX", [name, "+", f"cos(Variable({ang_var}))*{SPEED}*TimeDelta()"]),
             act("SetY", [name, "+", f"sin(Variable({ang_var}))*{SPEED}*TimeDelta()"])]))

        # retarget random cada 1.5-2.5s
        evs.append(std(
            [cond("ObjectTimer", [name, '"Retarget"', f"Variable({next_var})"])],
            [act("ResetObjectTimer", [name, '"Retarget"']),
             act("ModVarScene", [ang_var, "=", RAND_ANGLE]),
             act("ModVarScene", [next_var, "=", RAND_NEXT])]))

        # rebote en los 4 bordes de la caja de patrulla
        evs.append(std([cond("PosX", [name, "<", str(left)])],
                        [act("ModVarScene", [ang_var, "=", "(-60+Random(120))*3.14159265/180"])]))
        evs.append(std([cond("PosX", [name, ">", str(right)])],
                        [act("ModVarScene", [ang_var, "=", "(120+Random(120))*3.14159265/180"])]))
        evs.append(std([cond("PosY", [name, "<", str(top)])],
                        [act("ModVarScene", [ang_var, "=", "(30+Random(120))*3.14159265/180"])]))
        evs.append(std([cond("PosY", [name, ">", str(bottom)])],
                        [act("ModVarScene", [ang_var, "=", "(210+Random(120))*3.14159265/180"])]))

        # daño por colisión (2 variantes por lado, para el knockback horizontal)
        for op, push in ((">=", "70"), ("<", "-70")):
            evs.append(std(
                [cond("CollisionNP", ["Player", name, "", "", ""]),
                 cond("ObjectTimer", ["Player", '"Invuln"', "1"]),
                 cond("PosX", ["Player", op, f"{name}.X()"])],
                [act("ModVarScene", ["Lives", "-", "1"]),
                 act("ResetObjectTimer", ["Player", '"Invuln"']),
                 act("SetAnimationName", ["Player", '"Hit"']),
                 act("PlaySound", ["", "sfx_hurt.wav", "no", "GlobalVariable(SfxVolume)", "1"]),
                 act("SetX", ["Player", "+", push]),
                 act("SetY", ["Player", "+", "-30"])]))

    lay["events"] += evs

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("objetos Virus:", sum(1 for o in lay["objects"] if o["name"] in MYOBJS))
    print("instancias:", sum(1 for i in lay["instances"] if i["name"] in MYOBJS))
    print("eventos _virus:", sum(1 for e in lay["events"] if e.get("_virus")))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Virus/virus_1.png"), \
        "corré gen_virus.py primero"
    main(revert=os.environ.get("REVERT") == "1")
