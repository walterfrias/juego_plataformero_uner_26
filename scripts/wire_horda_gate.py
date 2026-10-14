#!/usr/bin/env python3
"""
wire_horda_gate.py — Tier 2 del hueco: horda gatillada por posición del
Player (no por tiempo desde el inicio de escena) + loop infinito, y
caída al hueco = pierde 1 vida + respawn en checkpoint (no game over
directo).

Problema que resuelve (ver reseach.md 2026-09-02): la horda de
`wire_river_gap.py` arranca a los 0s de escena y se BORRA al cruzar el
hueco una sola vez — si el Player tarda de más (peleando el nudo de
zombies) o si cae y tiene que reintentar, puede llegar al hueco y
encontrar que la horda ya pasó y no hay forma de cruzar (softlock).

Solución:
  - La horda queda OCULTA y QUIETA hasta que el Player cruza
    Player.X() > TRIGGER_X (bien antes del hueco).
  - Al activarse, arranca cerca del hueco (no desde x=928) y en vez de
    borrarse al cruzar, se TELETRANSPORTA de vuelta al inicio del loop
    y sigue cruzando en bucle infinito — siempre hay una horda
    disponible tarde o temprano, sin depender de timing perfecto.
  - Caída al hueco (Player.Y()>300): en vez de Lives=0 (game over
    directo), ahora pierde 1 vida y reaparece en un checkpoint justo
    antes del hueco. El game over real sigue ocurriendo cuando
    Lives<=0 (evento ya existente, sin tocar).

Los eventos existentes se ubican por CONTENIDO, no por índice (el
editor de GDevelop puede resavear el archivo y no preserva claves
custom como "_t1" — comprobado: los eventos de wire_tier1.py ya no
tienen ese flag en el JSON actual).

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 para
deshacer (vuelve al despawn de un solo cruce + Lives=0 directo).
Requiere: scripts/wire_river_gap.py ya corrido.
Uso:  python3 scripts/wire_horda_gate.py    (desde la raíz del repo)
Después en GDevelop: cerrar sin guardar + abrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"

TRIGGER_X = 1300          # Player.X() que arma la horda
LOOP_START_X = 1500       # x de HordaPiso al (re)arrancar el cruce
LOOP_END_X = 2060         # x de HordaPiso al que se considera "cruzado"
LOOP_SPAN = LOOP_END_X - LOOP_START_X
CHECKPOINT_X, CHECKPOINT_Y = 1650, 76   # antes del hueco, sobre el Ground

# posiciones originales (de wire_river_gap.py) -> nuevas, shifteadas para
# que el loop arranque pegado al hueco en vez de a 800px de distancia
SHIFT = LOOP_START_X - 928
ORIGINAL_X = {
    "HordaPiso": [928],
    "HordaZombieF": [910, 955, 1000, 1045, 1090],
    "HordaZombieM": [895, 940, 985, 1030, 1075],
    "HordaZombieT": [925, 970, 1015, 1060, 1105],
    "HumoHorda": [1049],
}
TARGET_X = {k: [x + SHIFT for x in v] for k, v in ORIGINAL_X.items()}

HORDA_MOVE = ["HordaZombieM", "HordaZombieF", "HordaZombieT", "HordaPiso"]
HORDA_ZOMBIES = ["HordaZombieF", "HordaZombieM", "HordaZombieT"]
HIDE_AT_START = HORDA_ZOMBIES + ["HumoHorda"]   # HordaPiso ya se oculta aparte (siempre invisible)

PB = "PlatformBehavior::PlatformerObjectBehavior"


def cond(t, params):
    return {"type": {"value": t}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def reposition(instances, mapping):
    for name, targets in mapping.items():
        insts = sorted([i for i in instances if i["name"] == name], key=lambda i: i["x"])
        for i, tx in zip(insts, sorted(targets)):
            i["x"] = tx


def find_hide_at_start(events):
    """Once -> Hide HordaPiso (evento original de wire_river_gap/manual)."""
    for e in events:
        conds = e.get("conditions", [])
        if len(conds) == 1 and conds[0]["type"]["value"] == "BuiltinCommonInstructions::Once":
            acts = e.get("actions", [])
            if any(a["type"]["value"] == "Hide" and a["parameters"][:1] == ["HordaPiso"] for a in acts):
                return e
    return None


def find_trigger_event(events):
    for e in events:
        conds = e.get("conditions", [])
        if len(conds) == 2 and conds[0]["type"]["value"] == "PosX" \
           and conds[0]["parameters"][0] == "Player" \
           and conds[1]["type"]["value"] == "VarScene" \
           and conds[1]["parameters"][0] == "HordaActive":
            return e
    return None


def find_movement_event(events):
    """evento sin condiciones que mueve HordaPiso con TimeDelta (el paso de la horda)."""
    for e in events:
        if e.get("conditions"):
            continue
        acts = e.get("actions", [])
        if any(a["type"]["value"] == "SetX" and a["parameters"][:1] == ["HordaPiso"]
               and "TimeDelta" in a["parameters"][2] for a in acts):
            return e
    return None


def find_loop_event(events):
    """PosX HordaPiso > N (el despawn/recycle de wire_river_gap)."""
    for e in events:
        conds = e.get("conditions", [])
        if len(conds) == 1 and conds[0]["type"]["value"] == "PosX" \
           and conds[0]["parameters"][0] == "HordaPiso" and conds[0]["parameters"][1] == ">":
            return e
    return None


def find_fall_event(events):
    """PosY Player > 300 AND Over = 0 (caida al vacio -> antes Lives=0)."""
    for e in events:
        conds = e.get("conditions", [])
        if len(conds) == 2 and conds[0]["type"]["value"] == "PosY" \
           and conds[0]["parameters"][0] == "Player" and conds[0]["parameters"][1] == ">" \
           and conds[1]["type"]["value"] == "VarScene" and conds[1]["parameters"][0] == "Over":
            return e
    return None


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    events = lay["events"]

    hide_ev = find_hide_at_start(events)
    trig_ev = find_trigger_event(events)
    move_ev = find_movement_event(events)
    loop_ev = find_loop_event(events)
    fall_ev = find_fall_event(events)
    assert hide_ev and move_ev and loop_ev and fall_ev, "no encontré uno de los eventos base (¿corriste wire_river_gap.py y wire_tier1.py?)"

    if revert:
        reposition(lay["instances"], ORIGINAL_X)
        lay["variables"] = [v for v in lay["variables"] if v["name"] != "HordaActive"]
        # ocultar solo HordaPiso, como antes de este script
        hide_ev["actions"] = [a for a in hide_ev["actions"]
                               if not (a["type"]["value"] == "Hide" and a["parameters"][0] in HIDE_AT_START)]
        if trig_ev is not None:
            events.remove(trig_ev)
        move_ev["conditions"] = []
        loop_ev["actions"] = [{"type": {"value": "Delete"}, "parameters": [o, ""]}
                               for o in HORDA_MOVE + ["HumoHorda"]]
        loop_ev["conditions"][0]["parameters"] = ["HordaPiso", ">", "2060"]
        fall_ev["actions"] = [{"type": {"value": "ModVarScene"}, "parameters": ["Lives", "=", "0"]}]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK: horda vuelve a arrancar en escena y despawnear al cruzar; caída = game over directo")
        return

    # --- reposicionar la horda cerca del hueco (en reposo, oculta) ---
    reposition(lay["instances"], TARGET_X)

    # --- scene var ---
    if not any(v["name"] == "HordaActive" for v in lay["variables"]):
        lay["variables"].append({"name": "HordaActive", "type": "number", "value": 0})

    # --- ocultar zombies+humo de la horda también al inicio (HordaPiso ya se oculta) ---
    have = {(a["type"]["value"], tuple(a["parameters"])) for a in hide_ev["actions"]}
    for obj in HIDE_AT_START:
        key = ("Hide", (obj,))
        if key not in have:
            hide_ev["actions"].append({"type": {"value": "Hide"}, "parameters": [obj]})

    # --- gatillo: Player cerca del hueco -> arma la horda ---
    if trig_ev is None:
        events.append(std(
            [cond("PosX", ["Player", ">", str(TRIGGER_X)]),
             cond("VarScene", ["HordaActive", "=", "0"])],
            [cond("ModVarScene", ["HordaActive", "=", "1"])] +
            [cond("Show", [o, ""]) for o in HIDE_AT_START]))
    else:
        trig_ev["conditions"][0]["parameters"][2] = str(TRIGGER_X)

    # --- movimiento: ahora solo mientras HordaActive=1 ---
    move_ev["conditions"] = [cond("VarScene", ["HordaActive", "=", "1"])]

    # --- loop: en vez de borrar al cruzar, teletransporta de vuelta al inicio ---
    loop_ev["conditions"] = [{"type": {"value": "PosX"}, "parameters": ["HordaPiso", ">", str(LOOP_END_X)]}]
    loop_ev["actions"] = [{"type": {"value": "SetX"}, "parameters": [o, "-", str(LOOP_SPAN)]}
                           for o in HORDA_MOVE]

    # --- caida al hueco: pierde 1 vida + respawn en checkpoint (no game over directo) ---
    fall_ev["actions"] = [
        {"type": {"value": "ModVarScene"}, "parameters": ["Lives", "-", "1"]},
        {"type": {"value": "SetX"}, "parameters": ["Player", "=", str(CHECKPOINT_X)]},
        {"type": {"value": "SetY"}, "parameters": ["Player", "=", str(CHECKPOINT_Y)]},
        {"type": {"value": f"{PB}::SetCurrentFallSpeed"}, "parameters": ["Player", "PlatformerObject", "=", "0"]},
        {"type": {"value": "ModVarScene"}, "parameters": ["BounceVel", "=", "0"]},
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print(f"horda: gatillada en Player.X()>{TRIGGER_X}, loop {LOOP_START_X}..{LOOP_END_X} ({LOOP_SPAN}px/vuelta)")
    print(f"checkpoint del hueco: ({CHECKPOINT_X},{CHECKPOINT_Y}) -1 vida por caída")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
