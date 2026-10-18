#!/usr/bin/env python3
"""
fix_w_escalera.py  —  con la W no se trepaban los postes (18/10).

En el motor, agarrarse de una escalera (plataforma tipo Ladder, como los
Poste de L1 y L3) lo decide la tecla "Ladder", no "Up":
    _checkTransitionOnLadder(){ this._ladderKey && this._isOverlappingLadder() ... }
La flecha ↑ por defecto activa las dos, pero el evento de la W solo simulaba
Up (PlatformBehavior::SimulateUpKey): con WASD los postes no servían.

Arreglo: en todas las escenas, el evento de la W simula también la tecla
Ladder (PlatformBehavior::SimulateLadderKey, forma legacy sin el segmento del
behavior, como el SimulateUpKey de al lado). Idempotente.
Uso:  python3 scripts/fix_w_escalera.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"


def walk(events):
    for e in events:
        yield e
        yield from walk(e.get("events", []))


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    for lay in d["layouts"]:
        n = 0
        for e in walk(lay["events"]):
            w = any(c["type"]["value"] == "KeyFromTextPressed" and c["parameters"][1] == '"w"'
                    for c in e.get("conditions", []))
            up = [a for a in e.get("actions", []) if a["type"]["value"] == "PlatformBehavior::SimulateUpKey"]
            if not (w and up):
                continue
            if not any(a["type"]["value"] == "PlatformBehavior::SimulateLadderKey" for a in e["actions"]):
                e["actions"].append({"type": {"value": "PlatformBehavior::SimulateLadderKey"},
                                     "parameters": list(up[0]["parameters"])})
            n += 1
        if n:
            print(f"{lay['name']}: W también agarra escaleras ({n} evento)")
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")


if __name__ == "__main__":
    main()
