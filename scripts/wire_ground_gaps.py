#!/usr/bin/env python3
"""
wire_ground_gaps.py  —  rompe el piso plano del tramo 1 (x -200..1730) en varios
tramos separados por huecos al Río de la Plata, y baja el salto del Player para
que esos huecos exijan un salto con carrera (parado no llegás).

El nivel dejaba de ser "caminar de corrido": ahora hay que saltar huecos reales
y, si errás, caés al río -> -1 vida + respawn en el último checkpoint pisado.

Edita game/game.json (backup .bak-<ts>, idempotente; corré DESPUÉS de
wire_river_gap.py — ese arma el hueco forzado de la horda en x1730..1970 y este
no lo toca):

  - Ground / Embankment / RiverFoam del tramo x[-200..1730] se re-arman en
    segmentos, dejando los HUECOS de GAPS. Los tramos post-hueco-forzado
    (x1970..2600) quedan intactos.
  - GapWater nuevo en cada hueco (mismo look que el hueco forzado).
  - Player.jumpSpeed  400 -> NEW_JUMP  (altura de salto ~89px -> ~68px).
  - Scene vars CheckX / CheckY (checkpoint). Eventos nuevos (tag "_gapcp"):
    al pisar tierra firme pasado cada tramo, CheckX avanza (monótono).
  - El evento de caída (PosY>300 -> Lives-1 + teleport a x1650 fijo) pasa a
    respawnear en (CheckX, CheckY) y baja el umbral a 260.
  - Nudge de patrulla: ZombieF / ZombieO / ZombieV para que no queden pisando
    un hueco.

Revertir:  REVERT=1 python3 scripts/wire_ground_gaps.py
Uso:       python3 scripts/wire_ground_gaps.py        (desde la raíz del repo)
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"

# --- región que se segmenta (a la izquierda del hueco forzado de la horda) ---
REGION_L, REGION_R = -200, 1730

# huecos (x_ini, x_fin) dentro de la región. Anchos 58..72; salto con carrera
# a jumpSpeed 350 cubre ~74px borde-a-borde, parado ~40px.
GAPS = [
    (335, 397),    # 62  1er salto, después del mobiliario, antes de ZombieF
    (885, 951),    # 66  entre el nudo F/T/D/M/N y ZombieO
    (1097, 1155),  # 58  entre ZombieO y ZombieV
    (1334, 1400),  # 66  tramo vacío después de ZombieV
    (1503, 1575),  # 72  el más ancho: aproximación final al hueco forzado
]

NEW_JUMP = 350
OLD_JUMP = 400
FALL_Y_NEW = 260
FALL_Y_OLD = 300

# geometría de cada capa que se parte (y, alto, zOrder) — tomada del estado actual
LAYER_GEO = {
    "Ground":    dict(y=110, h=14, z=1),
    "Embankment": dict(y=120, h=60, z=-3),
    "RiverFoam": dict(y=180, h=8, z=-1),
}
SPLIT = list(LAYER_GEO)

GAPWATER_Y, GAPWATER_H, GAPWATER_Z = 138, 90, -2

# nudges de patrulla: (evento se ubica por contenido) nombre -> (viejo_min, nuevo_min)
PATROL_NUDGE = {
    "ZombieF": (360, 403),
    "ZombieO": (950, 958),
    "ZombieV": (1150, 1160),
}
# reposicionar la instancia si cae dentro de un hueco
INSTANCE_MIN_X = {"ZombieF": 410, "ZombieV": 1165}


def segments():
    """la región menos los huecos -> lista de (x0, x1) de piso sólido."""
    cuts = sorted(GAPS)
    segs, x = [], REGION_L
    for g0, g1 in cuts:
        if g0 > x:
            segs.append((x, g0))
        x = g1
    if x < REGION_R:
        segs.append((x, REGION_R))
    return segs


def inst(name, x, y, z, w, h):
    return {"angle": 0, "customSize": True, "height": h, "layer": "", "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def is_fall_event(e):
    if e.get("type") != "BuiltinCommonInstructions::Standard":
        return False
    has_posy = any(c.get("type", {}).get("value") == "PosY"
                   and c.get("parameters", [None])[0] == "Player"
                   for c in e.get("conditions", []))
    has_setx = any(a.get("type", {}).get("value") == "SetX"
                   and a.get("parameters", [None])[0] == "Player"
                   for a in e.get("actions", []))
    has_lives = any(a.get("type", {}).get("value") == "ModVarScene"
                    and a.get("parameters", [None])[0] == "Lives"
                    for a in e.get("actions", []))
    return has_posy and has_setx and has_lives


def cond(value, params, inverted=False):
    c = {"type": {"value": value}, "parameters": params}
    if inverted:
        c["type"]["inverted"] = True
    return c


def act(value, params):
    return {"type": {"value": value}, "parameters": params}


def checkpoint_event(safe_x):
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "_gapcp": True,
        "conditions": [
            cond("PosX", ["Player", ">", str(safe_x)]),
            cond("PosY", ["Player", "<", "100"]),
            cond("VarScene", ["CheckX", "<", str(safe_x)]),
        ],
        "actions": [act("ModVarScene", ["CheckX", "=", str(safe_x)])],
    }


def set_scene_var(lay, name, value):
    for v in lay["variables"]:
        if v["name"] == name:
            v["value"] = value
            return
    lay["variables"].append({"name": name, "type": "number", "value": value})


def remove_scene_var(lay, name):
    lay["variables"] = [v for v in lay["variables"] if v["name"] != name]


def set_jump(lay, speed):
    P = [o for o in lay["objects"] if o["name"] == "Player"][0]
    for b in P["behaviors"]:
        if b.get("type") == "PlatformBehavior::PlatformerObjectBehavior":
            b["jumpSpeed"] = speed


def nudge_patrol(lay, revert=False):
    for e in lay["events"]:
        for c in e.get("conditions", []):
            p = c.get("parameters", [])
            if len(p) < 3:
                continue
            for name, (old_min, new_min) in PATROL_NUDGE.items():
                a, b = (new_min, old_min) if revert else (old_min, new_min)
                if p[0] == name and p[1] == "<" and p[2] == str(a):
                    p[2] = str(b)
    for i in lay["instances"]:
        if not revert and i["name"] in INSTANCE_MIN_X:
            i["x"] = max(i["x"], INSTANCE_MIN_X[i["name"]])


def rebuild_split_layers(lay, segmented):
    """saca las instancias de SPLIT/GapWater de la región y (si segmented) las re-arma."""
    def in_region(i):
        return i["x"] < REGION_R + 10
    keep = []
    for i in lay["instances"]:
        if i["name"] in SPLIT and in_region(i):
            continue
        if i["name"] == "GapWater" and i["x"] < REGION_R - 10:  # deja el del hueco forzado (x1730)
            continue
        keep.append(i)
    lay["instances"] = keep

    if not segmented:
        # un solo tramo continuo por capa (estado pre-gaps)
        for name, g in LAYER_GEO.items():
            lay["instances"].append(
                inst(name, REGION_L, g["y"], g["z"], REGION_R - REGION_L, g["h"]))
        return

    for name, g in LAYER_GEO.items():
        for x0, x1 in segments():
            lay["instances"].append(inst(name, x0, g["y"], g["z"], x1 - x0, g["h"]))
    for g0, g1 in GAPS:
        lay["instances"].append(
            inst("GapWater", g0, GAPWATER_Y, GAPWATER_Z, g1 - g0, GAPWATER_H))


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    applied = any(v["name"] == "CheckX" for v in lay["variables"])

    # limpiar SIEMPRE lo propio (idempotente): eventos checkpoint + estado.
    # match por tag _gapcp o por estructura (el editor puede comerse el tag).
    def is_cp(e):
        if e.get("_gapcp"):
            return True
        return any(c.get("type", {}).get("value") == "VarScene"
                   and c.get("parameters", [None])[0] == "CheckX"
                   and c.get("parameters", [None, None])[1] == "<"
                   for c in e.get("conditions", []))
    lay["events"] = [e for e in lay["events"] if not is_cp(e)]
    if applied:
        nudge_patrol(lay, revert=True)

    fall = next((e for e in lay["events"] if is_fall_event(e)), None)

    if revert:
        rebuild_split_layers(lay, segmented=False)
        set_jump(lay, OLD_JUMP)
        remove_scene_var(lay, "CheckX")
        remove_scene_var(lay, "CheckY")
        if fall:
            for c in fall["conditions"]:
                if c["type"]["value"] == "PosY":
                    c["parameters"][2] = str(FALL_Y_OLD)
            for a in fall["actions"]:
                if a["type"]["value"] == "SetX" and a["parameters"][0] == "Player":
                    a["parameters"][2] = "1650"
                if a["type"]["value"] == "SetY" and a["parameters"][0] == "Player":
                    a["parameters"][2] = "76"
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK: piso reunido, salto a", OLD_JUMP)
        return

    rebuild_split_layers(lay, segmented=True)
    set_jump(lay, NEW_JUMP)
    set_scene_var(lay, "CheckX", 40)
    set_scene_var(lay, "CheckY", 76)
    nudge_patrol(lay, revert=False)

    if fall:
        for c in fall["conditions"]:
            if c["type"]["value"] == "PosY":
                c["parameters"][2] = str(FALL_Y_NEW)
        for a in fall["actions"]:
            if a["type"]["value"] == "SetX" and a["parameters"][0] == "Player":
                a["parameters"][2] = "Variable(CheckX)"
            if a["type"]["value"] == "SetY" and a["parameters"][0] == "Player":
                a["parameters"][2] = "Variable(CheckY)"
    else:
        print("  WARNING: no encontré el evento de caída — respawn sin tocar")

    # checkpoints: borde izq de cada segmento (menos el 1ro) + 25px
    segs = segments()
    safe_xs = [round(x0 + 25) for x0, _ in segs[1:]]
    if segs and segs[-1][1] >= 1730:
        safe_xs.append(1680)  # antes del hueco forzado (reemplaza el x1650 hardcodeado)
    for sx in safe_xs:
        lay["events"].append(checkpoint_event(sx))

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    print("segmentos:", segments())
    print("huecos:", GAPS)
    print("checkpoints (CheckX):", [40] + safe_xs)
    print("salto:", NEW_JUMP, "| umbral de caída:", FALL_Y_NEW)


if __name__ == "__main__":
    assert os.path.isfile(GAME), "corré desde la raíz del repo"
    main(revert=bool(os.environ.get("REVERT")))
