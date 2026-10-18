#!/usr/bin/env python3
"""
wire_lab_pistones.py  —  Nivel 2: los dos pozos anchos (140 y 200 px, que no
se saltan) se cruzan con PISTONES HIDRÁULICOS en vez de camillas (18/10).
Las camillas flotaban en el aire (ni colgadas de un pórtico convencían) y no
eran divertidas: solo había que esperar a que llegaran. Los pistones exigen
timing, como los virus con patrón fijo (lo que funcionó en el playtest).

Requiere: gen_lab_piston.py (piston_0/1, piston_vastago).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_lab_pistones": true), en Level2:
  - saca las Camilla y sus barras de borde (PlatEdge con Owner = MinX de la
    camilla). El objeto Camilla y sus eventos quedan (sin instancias no
    hacen nada).
  - Piston (Sprite 40x10, plataforma maciza): N por pozo con huecos de 20 px
    (140 = 2·40 + 3·20; 200 = 3·40 + 4·20). Ojo: Lio salta 40-45 px CON
    carrera, pero PARADO solo ~28 px (acelera a 300 px/s² desde cero; medido
    18/10): con pistones de 32 y huecos de 26 el robot parado en el borde caía.
    20 px > el ancho de Lio (18): no se cruza caminando, hay que saltar.
    PistonVastago (TiledSprite) cuelga debajo del cabezal y lo sigue (var
    Owner = Id del pistón), detrás de los vidrios.
  - movimiento (cada frame): s = sin(t·W + Ph);
        Y = 110 + DEPTH · max(0, s)^1.5
    → con s ≤ 0 está ARRIBA, al ras del piso (la mitad del ciclo); con s > 0
    se hunde hasta 110 + DEPTH (fuera de pantalla: quedarse arriba = caer al
    pozo y perder una vida). El ^1.5 suaviza la salida de arriba.
    t = TimeFromStart(): se congela con time scale 0 (pausa, notas).
  - aviso: s entre WARN_S y 0 y subiendo (cos > 0) → las luces parpadean en
    rojo (cuadro 1) ~0.5 s antes de bajar. Con −0.45 (~0.22 s) no alcanzaba:
    el salto dura ~0.45 s y el robot de prueba saltaba a un pistón que se le
    iba abajo en el aire. Regla para el jugador: no saltar a uno en rojo; si
    estás sobre uno en rojo, saltá al siguiente.
  - desfase en ola hacia la derecha (Ph_i = Ph0 − i·LAG): el pistón siguiente
    sube cuando el anterior se pone en rojo (ver LAG); dos vecinos arriba a
    la vez durante (π − LAG)/W ≈ 0.55 s, con el de adelante en verde.
Re-correr después de `wire_levels23.py --force` (devuelve las camillas).
`wire_bordes_plataforma.py` saltea Piston (su franja de peligro ya marca el
borde; una barra fija no lo seguiría al bajar).
Uso:  python3 scripts/wire_lab_pistones.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import math
import os
import shutil
import uuid

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
MARK = "_lab_pistones"
SCENE = "Level2"
PISTON, VASTAGO = "Piston", "PistonVastago"
MINE = {PISTON, VASTAGO}
RES = ["piston_0.png", "piston_1.png", "piston_vastago.png"]
TOP = 110                 # piso: arriba, el cabezal queda al ras
DEPTH = 200               # cuánto se hunde (110 + 200 = 310: Lio muere con Y > 260)
P_W, P_H = 40, 10
ROD_W, ROD_DX = 12, 14    # vástago centrado bajo el cabezal
GAP = 20                  # hueco objetivo entre pistones (ver docstring)
WARN_S = -0.85            # aviso desde sin = −0.85 (≈ 0.5 s antes de bajar)
WIDE_PIT = 100            # pozos más anchos que esto llevan pistones
LAG = 2.0                 # rad de desfase entre pistones vecinos: cuando uno se pone en
                          # rojo (sin = −0.85, ángulo 5.26) el siguiente acaba de subir
                          # (π + LAG = 5.14) y sigue en verde hasta después de que baja el
                          # primero. Con 0.9 los dos quedaban en rojo a la vez y el jugador
                          # prudente, parado en el borde, no tenía salida (robot 18/10).
# por pozo (en orden de x): W (rad/s) y fase del primero
PITS = [(1.9, 0.0), (2.1, 1.3)]
CAMILLA_OWNERS = {2484, 2764}   # MinX de las camillas originales (barras PlatEdge)
T = "TimeFromStart()"


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def inst(name, x, y, z, w=None, h=None, vars_=(), layer=""):
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": layer,
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def main():
    asegurar_gdevelop_cerrado()
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
    sc = next(x for x in d["layouts"] if x["name"] == SCENE)

    # ---- limpieza (idempotente) + fuera camillas y sus barras ----
    owners = CAMILLA_OWNERS | {v["value"] for i in sc["instances"] if i["name"] == "Camilla"
                               for v in i["initialVariables"] if v["name"] == "MinX"}
    n_cam = sum(1 for i in sc["instances"] if i["name"] == "Camilla")
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE | {"Camilla"}
                       and not (i["name"] == "PlatEdge" and any(
                           v["name"] == "Owner" and v["value"] in owners for v in i["initialVariables"]))]
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]

    # ---- objetos ----
    ground = next(o for o in sc["objects"] if o["name"] == "Ground")
    base = next(o for o in sc["objects"] if o["name"] == "LampGlow")      # un Sprite
    piston = copy.deepcopy(base)
    piston.update(name=PISTON, effects=[], behaviors=copy.deepcopy(ground["behaviors"]),  # maciza
                  variables=[{"name": k, "type": "number", "value": 0} for k in ("Id", "W", "Ph")])
    piston["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": False, "timeBetweenFrames": 1, "sprites": [{
            "hasCustomCollisionMask": False, "image": f"piston_{k}.png", "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []} for k in (0, 1)]}]}]
    vastago = copy.deepcopy(ground)
    vastago.update(name=VASTAGO, texture="piston_vastago.png", behaviors=[], effects=[],
                   variables=[{"name": "Owner", "type": "number", "value": 0}])
    sc["objects"] += [piston, vastago]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in (PISTON, VASTAGO)]

    # ---- instancias: pistones repartidos en cada pozo ancho ----
    floors = sorted((i for i in sc["instances"] if i["name"] == "Ground"
                     and round(i["height"]) == 96 and i["y"] > 0), key=lambda i: i["x"])
    # un pozo de verdad tiene vidrios rotos al fondo (el corredor del ducto, 966..1268,
    # también queda entre dos piezas macizas de piso y no es un pozo)
    spikes = [i["x"] for i in sc["instances"] if i["name"] == "GlassSpikes"]
    pits = [(a["x"] + a["width"], b["x"]) for a, b in zip(floors, floors[1:])
            if b["x"] - (a["x"] + a["width"]) > WIDE_PIT
            and any(a["x"] + a["width"] <= x < b["x"] for x in spikes)]
    assert len(pits) == len(PITS), f"esperaba {len(PITS)} pozos anchos, hay {pits}"
    new, pid = [], 0
    for (a, b), (w, ph0) in zip(pits, PITS):
        width = b - a
        n = round((width - GAP) / (P_W + GAP))
        gap = (width - n * P_W) / (n + 1)
        assert 18.5 < gap <= 24, f"hueco de {gap:.1f} px en el pozo {a}..{b}: o se camina o no se salta parado"
        for k in range(n):
            x = round(a + gap * (k + 1) + P_W * k)
            pid += 1
            new.append(inst(PISTON, x, TOP, 1, vars_=[("Id", pid), ("W", w), ("Ph", round(ph0 - k * LAG, 3))]))
            new.append(inst(VASTAGO, x + ROD_DX, TOP + P_H, -1, ROD_W, 260, vars_=[("Owner", pid)]))
        print(f"  pozo {round(a)}..{round(b)} ({round(width)} px): {n} pistones, huecos de {gap:.1f} px")
    sc["instances"] += new

    # ---- eventos ----
    s = f"sin({T} * {PISTON}.Variable(W) + {PISTON}.Variable(Ph))"
    c = f"cos({T} * {PISTON}.Variable(W) + {PISTON}.Variable(Ph))"
    warn = {"type": "BuiltinCommonInstructions::Standard",
            "conditions": [ins("BuiltinCommonInstructions::CompareNumbers", [s, ">", str(WARN_S)]),
                           ins("BuiltinCommonInstructions::CompareNumbers", [s, "<=", "0"]),
                           ins("BuiltinCommonInstructions::CompareNumbers", [c, ">", "0"])],
            "actions": [ins("ChangeSprite", [PISTON, "=", f"mod(floor({T} * 12), 2)"])]}
    rod = {"type": "BuiltinCommonInstructions::Standard",
           "conditions": [ins("NumberObjectVariable", [VASTAGO, "Owner", "=", f"{PISTON}.Variable(Id)"])],
           "actions": [ins("SetX", [VASTAGO, "=", f"{PISTON}.X() + {ROD_DX}"]),
                       ins("SetY", [VASTAGO, "=", f"{PISTON}.Y() + {P_H}"])]}
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": f"Pistones (wire_lab_pistones.py): Y = {TOP} + {DEPTH}·max(0, sin(t·W+Ph))^1.5 "
                    "(arriba media vuelta, después se hunden). Aviso: luces rojas que parpadean antes "
                    "de bajar. El vástago sigue al cabezal (Owner = Id).",
         "comment2": "", MARK: True},
        {"type": "BuiltinCommonInstructions::ForEach", "object": PISTON, "objectsToPick": PISTON,
         "conditions": [], "actions": [], "events": [
             {"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": [
                 ins("SetY", [PISTON, "=", f"{TOP} + {DEPTH} * pow(max(0, {s}), 1.5)"]),
                 ins("ChangeSprite", [PISTON, "=", "0"])],
              "events": [warn, rod]}],
         MARK: True},
    ]
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    both_up = (math.pi - LAG) / max(w for w, _ in PITS)
    print(f"{SCENE}: {pid} pistones | camillas sacadas: {n_cam} | dos vecinos arriba {both_up:.2f} s")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Lab/piston_0.png"), "corré gen_lab_piston.py primero"
    main()
