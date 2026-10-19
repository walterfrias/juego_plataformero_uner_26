#!/usr/bin/env python3
"""
wire_l3_publico.py  —  arena del jefe (L3), 19/10, pedido del usuario:
  - "achicá bastante los coronavirus decorativos, si están atrás tienen que ser
    más chicos": VirusFondo de x2/x3 (32/48 px) a x0.75/x1 (12/16 px). La misma
    escala queda en VIRUS_FONDO de wire_l3_caos.py.
  - "una fila más de zombies más chicos, como en perspectiva, que sean muchos y
    del color original": público lejano detrás de las siluetas (FondoZombie*, x0.8,
    pies en y 152) y de los monumentos. Dos hileras: x0.5 con los pies en y 145 y
    x0.42 con los pies en y 141, más atrás. Copias de los 13 zombies del grupo
    Zombies (mismos dibujos, sin contorno ni variables: no son del grupo, no
    lastiman ni se pisan), capa BG_near, z 0/1. Se mueven en el lugar: animación de
    caminar a velocidad y cuadro al azar, la mitad espejados.

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 saca el público
(los virus quedan chicos). Correr después de wire_l3_caos.py.
Uso:  python3 scripts/wire_l3_publico.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402

GAME = "game/game.json"
PREFIJO = "Publico_"
GRUPO = "Público lejano de la arena (wire_l3_publico.py)"
VIRUS_TAM = {48: 16, 32: 12}          # x3 → x1, x2 → x0.75 (sobre el virus de 16 px)
SPRITE = (32, 34)                     # tamaño de los zombies
# hileras: (escala, y de los pies, z, cantidad)
HILERAS = [(0.42, 141, 0, 16), (0.5, 145, 1, 14)]
ARENA = (4, 476)


def ins(value, params):
    return {"type": {"value": value}, "parameters": [str(p) for p in params]}


def main(revert=False):
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    with open(GAME) as f:
        texto = f.read()
    with open(f"{GAME}.bak-{ts}", "w") as f:
        f.write(texto)
    print("backup", f"{GAME}.bak-{ts}")
    d = json.loads(texto)
    lay = next(l for l in d["layouts"] if l["name"] == "Level3")

    # virus de fondo más chicos (idempotente: solo convierte los tamaños viejos)
    n = 0
    for i in lay["instances"]:
        if i["name"] == "VirusFondo" and round(i["width"]) in VIRUS_TAM:
            dx = (i["width"] - VIRUS_TAM[round(i["width"])]) / 2          # mismo centro
            i["x"] += dx
            i["y"] += dx
            for v in i.get("initialVariables", []):
                if v["name"] in ("BX", "BY"):
                    v["value"] = float(v["value"]) + dx
            i["width"] = i["height"] = VIRUS_TAM[round(i["width"])]
            n += 1
    print("virus de fondo achicados:", n)

    # limpiar el público (idempotente / revert)
    lay["objects"] = [o for o in lay["objects"] if not o["name"].startswith(PREFIJO)]
    lay["instances"] = [i for i in lay["instances"] if not i["name"].startswith(PREFIJO)]
    lay["events"] = [e for e in lay["events"] if e.get("name") != GRUPO]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if not c.get("objectName", "").startswith(PREFIJO)]

    if not revert:
        objs = {o["name"]: o for o in lay["objects"]}
        tipos = [o["name"] for o in next(g for g in lay["objectsGroups"] if g["name"] == "Zombies")["objects"]]
        for t in tipos:
            o = copy.deepcopy(objs[t])
            o["name"] = PREFIJO + t
            o["effects"], o["behaviors"] = [], []
            o["variables"] = [{"name": "Flip", "type": "number", "value": 0}]
            lay["objects"].append(o)
            if "children" in fs:
                fs["children"].append({"objectName": o["name"]})
        rnd = random.Random(1903)
        total = 0
        for escala, pies, z, cant in HILERAS:
            w, h = round(SPRITE[0] * escala), round(SPRITE[1] * escala)
            paso = (ARENA[1] - ARENA[0] - w) / (cant - 1)
            orden = tipos * 3
            rnd.shuffle(orden)
            for k in range(cant):
                x = ARENA[0] + k * paso + rnd.uniform(-paso * 0.3, paso * 0.3)
                lay["instances"].append({
                    "angle": 0, "customSize": True, "width": w, "height": h, "layer": "BG_near",
                    "name": PREFIJO + orden[k], "x": round(x), "y": pies - h + rnd.choice((0, 0, 1)),
                    "zOrder": z, "numberProperties": [], "stringProperties": [],
                    "initialVariables": [{"name": "Flip", "type": "number", "value": rnd.choice((0, 1))}]})
                total += 1
        # al empezar: cuadro y velocidad de la animación al azar, la mitad espejados
        evs = []
        for t in tipos:
            o = PREFIJO + t
            evs.append({"type": "BuiltinCommonInstructions::Standard",
                        "conditions": [ins("BuiltinCommonInstructions::Once", [])],
                        "actions": [ins("SetAnimationName", [o, '"Walk"']),
                                    ins("ChangeSprite", [o, "=", "Random(5)"]),
                                    ins("ChangeAnimationSpeedScale", [o, "=", "0.35 + RandomFloat(0.35)"])],
                        "events": [{"type": "BuiltinCommonInstructions::Standard",
                                    "conditions": [ins("NumberObjectVariable", [o, "Flip", "=", "1"])],
                                    "actions": [ins("FlipX", [o, "yes"])], "events": []}]})
        lay["events"].append({"type": "BuiltinCommonInstructions::Group", "name": GRUPO, "source": "",
                              "creationTime": 0, "folded": True, "color": {"b": 120, "g": 120, "r": 120},
                              "conditions": [], "events": evs})
        print(f"público: {total} zombies en {len(HILERAS)} hileras, {len(tipos)} tipos")

    with open(GAME, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else "OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
