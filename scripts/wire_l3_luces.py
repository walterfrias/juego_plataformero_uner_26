#!/usr/bin/env python3
"""
wire_l3_luces.py  —  luces del Nivel 3 (18/10): incendios entre los edificios y la
luz de los fuegos y faroles sobre las fachadas. Pedido del usuario: "mejoremos
las luces y agreguemos algunos fuegos de fondo entre los edificios".

Requiere: gen_l3_luces.py (arte), gen_l3_ciudad_capas.py (ciudad_capas.json: los
edificios de cada tira) y wire_l3_recorrido.py (las tiras CiudadTrasera z 10 y
CiudadMedia z 13, los tachos y faroles).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_l3_luces": true), en Level3:
  - INCENDIOS sobre techos reales de las filas de fondo (si no, flotarían): se
    eligen edificios de ciudad_capas.json (QUEMA_MEDIA / QUEMA_TRASERA) y en cada
    uno van llamas animadas (FuegoTecho), una columna de humo (HumoTecho) y el
    cielo teñido de naranja detrás (ResplandorFuego), en BG_city:
        resplandor de la trasera  z 9   (detrás de las torres: a contraluz)
        fuego/humo de la trasera  z 11  (asoma entre los edificios de la media)
        resplandor de la media    z 12
        fuego/humo de la media    z 14  (sobre los techos de la media)
    Se mueven con el parallax de SU fila (var F = 0.70 o 0.85): X = Base + (1−F)·cámara,
    igual que el texto de la tira (XOffset = −(1−F)·cámara), así quedan pegados al
    techo. Como la tira se repite cada 1024 px, cada incendio va en todas las copias.
  - LUZ SOBRE LAS FACHADAS (capa Decor, detrás de tachos y faroles): cada tacho con
    fuego ilumina la pared con un resplandor naranja que titila (LuzParedFuego); cada
    farol, con luz de sodio fija (LuzParedFarol).
Re-correr después de wire_l3_recorrido.py.
Uso:  python3 scripts/wire_l3_luces.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import uuid

import l3_recorrido as R
from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
MARK = "_l3_luces"
CAPAS_JSON = "game/assets/City/ciudad_capas.json"
CAM = 'CameraCenterX("")'
T = "TimeFromStart()"
FUEGO, HUMO, RESPL = "FuegoTecho", "HumoTecho", "ResplandorFuego"
LUZ_FUEGO, LUZ_FAROL = "LuzParedFuego", "LuzParedFarol"
MINE = {FUEGO, HUMO, RESPL, LUZ_FUEGO, LUZ_FAROL}
RES = ([f"incendio_techo_{k}.png" for k in (1, 2, 3)] +
       ["resplandor_cielo.png", "luz_pared_fuego.png", "luz_pared_farol.png"])
TIRA = 1024
# por fila: (F parallax, z resplandor, z fuego)
FILAS = {"media": (0.85, 12, 14), "trasera": (0.70, 9, 11)}
# qué edificios se queman: hasta QUEMA_N por copia de la tira, separados QUEMA_SEP px, que
# no sean torres vidriadas y con el techo a la vista (y ≥ TECHO_MIN: el borde de arriba de
# la cámara es y = −25 y la llama mide 44; con techos más altos no se veía)
QUEMA_N, QUEMA_SEP, TECHO_MIN = 3, 250, 8
FW, FH = 56, 44                      # incendio_techo
RW, RH = 240, 150                    # resplandor_cielo


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts, MARK: True}


def foreach(obj, acts):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], MARK: True,
            "events": [{"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": acts}]}


def sprite_obj(tpl, name, images, tbf=1.0, loop=False, variables=()):
    o = copy.deepcopy(tpl)
    o.update(name=name, effects=[], behaviors=[],
             variables=[{"name": k, "type": "number", "value": 0} for k in variables])
    spr = o["animations"][0]["directions"][0]["sprites"][0]
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": loop, "timeBetweenFrames": tbf,
        "sprites": [dict(spr, image=im, hasCustomCollisionMask=False, customCollisionMask=[], points=[])
                    for im in images]}]}]
    return o


def inst(name, x, y, z, layer, vars_=()):
    return {"angle": 0, "customSize": False, "height": 0, "layer": layer, "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def flicker(obj, base, a, b):
    return (f"round(255 * ({base} + {a} * sin({T} * 3.1 + {obj}.Variable(Seed)) "
            f"+ {b} * sin({T} * 7.3 + {obj}.Variable(Seed) * 2)))")


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    capas = json.load(open(CAPAS_JSON))
    lays = {x["name"]: x for x in d["layouts"]}
    l1, sc = lays["Level1"], lays["Level3"]
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm in RES:
        if nm not in have:
            res.append({"file": f"assets/City/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})

    # ---- limpieza (idempotente) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    sc["objectsGroups"] = [g for g in sc.get("objectsGroups", []) if g["name"] != "FuegosFondo"]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]

    # ---- objetos ----
    o1 = {o["name"]: o for o in l1["objects"]}
    tpl = o1["Tacho"]
    humo = copy.deepcopy(o1["NocheHumo"])                      # el humo animado de la noche de L1
    humo.update(name=HUMO, effects=[], variables=[{"name": k, "type": "number", "value": 0} for k in ("Base", "F")])
    objs = [
        sprite_obj(tpl, FUEGO, [f"incendio_techo_{k}.png" for k in (1, 2, 3)], tbf=0.09, loop=True,
                   variables=("Base", "F")),
        sprite_obj(tpl, RESPL, ["resplandor_cielo.png"], variables=("Base", "F", "Seed")),
        humo,
        sprite_obj(tpl, LUZ_FUEGO, ["luz_pared_fuego.png"], variables=("Seed",)),
        sprite_obj(tpl, LUZ_FAROL, ["luz_pared_farol.png"]),
    ]
    sc["objects"] += objs
    if "children" in fs:
        fs["children"] += [{"objectName": o["name"]} for o in objs]
    sc["objectsGroups"].append({"name": "FuegosFondo", "objects": [{"name": n} for n in (FUEGO, HUMO, RESPL)]})

    # ---- instancias: incendios sobre techos reales, en todas las copias de la tira ----
    tira = next(i for i in sc["instances"] if i["name"] == "CiudadMedia")
    x0_tira = tira["x"]
    new, seed = [], 0.0
    for fila, (f, z_resp, z_fuego) in FILAS.items():
        alto = capas[fila]["alto"]
        y_tira = R.FLOOR - alto
        elegidos, ultimo = [], -10 ** 6
        for kind, u, w, top in capas[fila]["edificios"]:
            if kind != "vidriada" and y_tira + top >= TECHO_MIN and u - ultimo >= QUEMA_SEP:
                elegidos.append((u, w, top))
                ultimo = u
        assert elegidos, f"no hay techos a la vista en la fila {fila}"
        print(f"  {fila}: se queman los edificios en x {[u for u, _, _ in elegidos[:QUEMA_N]]} de la tira")
        for u, w, top in elegidos[:QUEMA_N]:
            techo = y_tira + top
            for k in range(-1, 5):                           # copias de la tira (cubren la cámara)
                base = x0_tira + k * TIRA + u + w / 2
                seed += 1.37
                new.append(inst(RESPL, base - RW / 2, techo - RH * 0.62, z_resp, "BG_city",
                                vars_=[("Base", base - RW / 2), ("F", f), ("Seed", round(seed % 6.28, 2))]))
                new.append(inst(HUMO, base - 14, techo - 110 - 30, z_fuego, "BG_city",
                                vars_=[("Base", base - 14), ("F", f)]))
                new.append(inst(FUEGO, base - FW / 2, techo - FH + 2, z_fuego, "BG_city",
                                vars_=[("Base", base - FW / 2), ("F", f)]))
    # ---- luz sobre las fachadas: tachos con fuego y faroles ----
    for name, x, y, ex in R.PROPS:
        gx = x + R.OFFSET_X
        if name == "Tacho" and ex.get("fuego"):
            seed += 1.11
            new.append(inst(LUZ_FUEGO, gx + 8 - 75, R.FLOOR - 110 + 6, 0, "Decor",
                            vars_=[("Seed", round(seed % 6.28, 2))]))
        elif name == "Farol":
            new.append(inst(LUZ_FAROL, gx + 10 - 55, y - 20, 0, "Decor"))
    sc["instances"] += new

    # ---- eventos ----
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Luces de L3 (wire_l3_luces.py): incendios sobre techos de las filas de fondo, con el "
                    "parallax de su fila (X = Base + (1-F)·cámara); luz de tachos y faroles en las fachadas.",
         "comment2": "", MARK: True},
        foreach("FuegosFondo", [ins("SetX", ["FuegosFondo", "=", f"round(FuegosFondo.Variable(Base) + "
                                                                f"(1 - FuegosFondo.Variable(F)) * {CAM})"])]),
        # lo lejano, más apagado: llamas de la trasera (F 0.70) ~65 %, de la media (0.85) ~85 %
        # (la opacidad de instancia de un Sprite el runtime la ignora: va por evento)
        foreach(FUEGO, [ins("Opacity", [FUEGO, "=", f"round(255 * ({FUEGO}.Variable(F) * 1.33 - 0.28))"])]),
        foreach(RESPL, [ins("Opacity", [RESPL, "=", flicker(RESPL, 0.75, 0.15, 0.08)])]),
        foreach(LUZ_FUEGO, [ins("Opacity", [LUZ_FUEGO, "=", flicker(LUZ_FUEGO, 0.8, 0.12, 0.08)])]),
    ]
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    cnt = {}
    for i in new:
        cnt[i["name"]] = cnt.get(i["name"], 0) + 1
    print("Level3: luces", cnt)


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/incendio_techo_1.png"), "corré gen_l3_luces.py primero"
    assert os.path.exists(CAPAS_JSON), "corré gen_l3_ciudad_capas.py primero"
    main()
