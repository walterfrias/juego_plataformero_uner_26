#!/usr/bin/env python3
"""
fix_tutorial_planeo.py  —  en el Tutorial, después de planear una vez con la
mochila de práctica, Lio quedaba cayendo lento hasta el final (18/10).

El planeo (mantener J o Espacio cayendo) baja MaxFallingSpeed a 80. En L1, L2 y
L3 un evento sin condiciones la vuelve a 600 en cada cuadro, justo antes de los
del planeo; en el Tutorial faltaba. Este script lo agrega en el mismo lugar
(antes del primer evento de planeo, en la misma lista de eventos). Idempotente.
Uso:  python3 scripts/fix_tutorial_planeo.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
SET = "PlatformBehavior::MaxFallingSpeed"


def es_planeo(e):
    return any(a["type"]["value"] == SET and a["parameters"][3] == "80" for a in e.get("actions", []))


def es_reset(e):
    return (not e.get("conditions")) and any(
        a["type"]["value"] == SET and a["parameters"][3] == "600" for a in e.get("actions", []))


def arreglar(eventos):
    for i, e in enumerate(eventos):
        if es_planeo(e):
            if i > 0 and es_reset(eventos[i - 1]):
                return "ya estaba"
            eventos.insert(i, {"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": [
                {"type": {"value": SET}, "parameters": ["Player", "PlatformerObject", "=", "600", "no"]}]})
            return "agregado"
        r = arreglar(e.get("events", []))
        if r:
            return r
    return None


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    tut = next(x for x in d["layouts"] if x["name"] == "Tutorial")
    r = arreglar(tut["events"])
    assert r, "no encontré los eventos de planeo del Tutorial"
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    print("Tutorial: vuelta de la caída a 600 →", r)


if __name__ == "__main__":
    main()
