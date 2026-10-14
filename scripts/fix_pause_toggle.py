#!/usr/bin/env python3
"""
fix_pause_toggle.py — arregla el bug de la pausa de Level1 (abierto desde el
19/09: ESC/P no abrían la pausa).

Causa (confirmada el 27/09 interceptando setTimeScale en runtime: en el
MISMO frame se llamaba setTimeScale(0) y enseguida setTimeScale(1)): la
pausa era un toggle hecho con DOS eventos hermanos,

    [a] JustPressed(ESC) & Paused=0 & Over=0 & Won=0 -> Paused=1, pausar
    [b] JustPressed(ESC) & Paused=1                  -> Paused=0, despausar

GDevelop evalúa los eventos en orden dentro del mismo frame: [a] pone
Paused=1, y [b] ve ESC todavía "recién apretada" (lo es durante todo el
frame) y Paused=1, así que despausa. Resultado: la pausa se abre y se
cierra en el mismo frame y nunca se ve. Igual con P.

Arreglo: un evento padre por tecla, con sub-eventos y un estado
intermedio (Paused=2, "cerrando") para que cada pulsación togglee UNA vez:

    JustPressed(tecla):
        Paused=1                      -> Paused=2, despausar
        Paused=0 & Over=0 & Won=0     -> Paused=1, pausar
        Paused=2                      -> Paused=0

(El resto de los eventos que miran Paused comparan con 0 o 1, y el espejo
SettingsOpen=Paused corre después, cuando ya volvió a 0.)

Edita game/game.json directo (backup .bak-<ts>). Idempotente.
Correr con GDevelop CERRADO y después `python3 scripts/wire_levels23.py
--force` (Level2/3 copian los eventos de pausa de Level1).
"""
import copy
import datetime
import json
import os
import shutil

GAME = "game/game.json"
LAYOUTS = ["Level1"]


def is_toggle_half(e):
    """Uno de los 4 eventos viejos: JustPressed(ESC|p) & Paused=0|1 (top-level)."""
    c = e.get("conditions", [])
    keys = [x for x in c if x["type"]["value"] == "KeyFromTextJustPressed"]
    paused = [x for x in c if x["type"]["value"] == "VarScene" and x["parameters"][0] == "Paused"]
    acts = [a["type"]["value"] for a in e.get("actions", [])]
    return len(keys) == 1 and len(paused) == 1 and "ChangeTimeScale" in acts and \
        keys[0]["parameters"][1] in ('"Escape"', '"p"')


def main():
    d = json.load(open(GAME))
    changed = False
    for lay in d["layouts"]:
        if lay["name"] not in LAYOUTS:
            continue
        halves = [e for e in lay["events"] if is_toggle_half(e)]
        if not halves:
            print(f"{lay['name']}: ya arreglado (idempotente)")
            continue
        if not changed:
            ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
            shutil.copy(GAME, f"{GAME}.bak-{ts}")
            print("backup", f"{GAME}.bak-{ts}")
            changed = True
        first = lay["events"].index(halves[0])
        new = []
        for key in ('"Escape"', '"p"'):
            mine = [e for e in halves if any(
                x["type"]["value"] == "KeyFromTextJustPressed" and x["parameters"][1] == key
                for x in e["conditions"])]
            opener = next(e for e in mine if any(
                x["parameters"][:3] == ["Paused", "=", "0"] for x in e["conditions"]))
            closer = next(e for e in mine if any(
                x["parameters"][:3] == ["Paused", "=", "1"] for x in e["conditions"]))
            key_cond = next(x for x in opener["conditions"]
                            if x["type"]["value"] == "KeyFromTextJustPressed")
            open_conds = [x for x in opener["conditions"] if x is not key_cond]
            close_acts = copy.deepcopy(closer["actions"])
            for a in close_acts:      # Paused=0 -> Paused=2 ("cerrando")
                if a["type"]["value"] == "ModVarScene" and a["parameters"][0] == "Paused":
                    a["parameters"][2] = "2"
            new.append({
                "type": "BuiltinCommonInstructions::Standard",
                "conditions": [copy.deepcopy(key_cond)], "actions": [],
                "events": [
                    {"type": "BuiltinCommonInstructions::Standard",
                     "conditions": [{"type": {"value": "VarScene"},
                                     "parameters": ["Paused", "=", "1"]}],
                     "actions": close_acts, "events": []},
                    {"type": "BuiltinCommonInstructions::Standard",
                     "conditions": copy.deepcopy(open_conds),
                     "actions": copy.deepcopy(opener["actions"]), "events": []},
                    {"type": "BuiltinCommonInstructions::Standard",
                     "conditions": [{"type": {"value": "VarScene"},
                                     "parameters": ["Paused", "=", "2"]}],
                     "actions": [{"type": {"value": "ModVarScene"},
                                  "parameters": ["Paused", "=", "0"]}], "events": []},
                ]})
        lay["events"] = [e for e in lay["events"] if e not in halves]
        lay["events"][first:first] = new
        print(f"{lay['name']}: 4 eventos de toggle -> 2 eventos padre (ESC, P) con sub-eventos")
    if changed:
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
