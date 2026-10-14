#!/usr/bin/env python3
"""
fix_event_params.py  —  arregla parámetros de eventos que quedaron
inválidos (subrayados en rojo en el "Diagnostic report" de GDevelop).

Causa: varios eventos (generados por el MCP y por scripts anteriores)
pasaron nombres de texto SIN comillas. GDevelop espera el nombre como
expresión de texto: `"Run"`, no `Run`.

Arregla:
  - SetAnimationName        -> comilla el nombre de animación (param 1)
  - ObjectTimer (condición) -> comilla el nombre del timer (param 1)
  - ResetObjectTimer        -> comilla el nombre del timer (param 1)
Y quita los 2 eventos de cámara (`CenterCameraOnObject`, `ClampCamera`)
que se agregaron con formato incorrecto — se rehacen bien con el MCP
conectado o a mano en el editor.

Edita game/game.json directo. Backup game/game.json.bak-<ts>. Idempotente.
Correr desde la raíz del repo:  python3 scripts/fix_event_params.py
"""
import json
import datetime
import shutil
import os

GAME = "game/game.json"

# acción/condición -> índice del parámetro que debe ir entre comillas
QUOTE_PARAM = {
    "SetAnimationName": 1,
    "ObjectTimer": 1,
    "ResetObjectTimer": 1,
}
DROP_ACTIONS = {"CenterCameraOnObject", "ClampCamera"}


def quote(v):
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v
    return f'"{v}"'


def fix_instr_list(lst):
    changed = 0
    for instr in lst:
        t = instr.get("type", {}).get("value")
        if t in QUOTE_PARAM:
            idx = QUOTE_PARAM[t]
            p = instr.get("parameters", [])
            if len(p) > idx and p[idx] and not (
                p[idx].startswith('"') and p[idx].endswith('"')
            ):
                p[idx] = quote(p[idx])
                changed += 1
    return changed


def walk_events(events):
    changed = 0
    kept = []
    for e in events:
        acts = e.get("actions", [])
        if any(a.get("type", {}).get("value") in DROP_ACTIONS for a in acts):
            # descartar el evento entero si su única acción era de cámara
            acts = [a for a in acts if a.get("type", {}).get("value") not in DROP_ACTIONS]
            e["actions"] = acts
            if not acts and not e.get("conditions") and not e.get("events"):
                continue  # evento vacío -> fuera
        changed += fix_instr_list(e.get("conditions", []))
        changed += fix_instr_list(e.get("actions", []))
        if e.get("events"):
            changed += walk_events(e["events"])
        kept.append(e)
    events[:] = kept
    return changed


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    total = 0
    for lay in d["layouts"]:
        before = len(lay["events"])
        total += walk_events(lay["events"])
        print(f"  {lay['name']}: {before} -> {len(lay['events'])} eventos")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print(f"parámetros comillados: {total}")
    print("eventos de cámara (CenterCameraOnObject/ClampCamera) removidos.")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
