#!/usr/bin/env python3
"""
fix_contagio_limite.py  —  cuántas veces se puede contagiar cada zombie, por nivel
(19/10, pedido del usuario): Level1 1 vez, Level2 2 veces, Level3 sin límite (no se
toca: sigue con la inmunidad de 3 s después de curarse, como antes).

Cambio: variable de objeto `Contagios` (0) en los zombies del grupo Zombies de cada
nivel con límite, y el evento del contagio (virus toca zombie: Infected = 0 y timer
"Immune" >= 3) pide Contagios < límite y le suma 1. Lo demás del contagio (contorno,
gas, escupitajos, cura) no cambia. Reemplaza a fix_n1_contagio_unico.py (var
`YaContagiado`, solo L1): la saca si la encuentra.

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 lo deshace.
Uso:  python3 scripts/fix_contagio_limite.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402

GAME = "game/game.json"
VAR = "Contagios"
VIEJAS = (VAR, "YaContagiado")          # YaContagiado: la versión anterior, solo L1
LIMITES = {"Level1": 1, "Level2": 2}    # Level3: sin límite


def cond(limite):
    return {"type": {"value": "NumberObjectVariable"}, "parameters": ["Zombies", VAR, "<", str(limite)]}


ACT = {"type": {"value": "ModVarObjet"}, "parameters": ["Zombies", VAR, "+", "1"]}


def es_el_contagio(e):
    cs = [(c["type"]["value"], c["parameters"]) for c in e.get("conditions", [])]
    return (("CollisionNP", ["Virus", "Zombies", "", "", ""]) in cs
            and ("NumberObjectVariable", ["Zombies", "Infected", "=", "0"]) in cs)


def main(revert=False):
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    with open(GAME) as f:
        texto = f.read()
    with open(f"{GAME}.bak-{ts}", "w") as f:
        f.write(texto)
    print("backup", f"{GAME}.bak-{ts}")
    d = json.loads(texto)
    for escena, limite in LIMITES.items():
        lay = next(l for l in d["layouts"] if l["name"] == escena)
        ev = [e for e in lay["events"] if es_el_contagio(e)]
        assert len(ev) == 1, f"esperaba 1 evento de contagio en {escena}, encontré {len(ev)}"
        ev = ev[0]
        ev["conditions"] = [c for c in ev["conditions"] if c["parameters"][1] not in VIEJAS]
        ev["actions"] = [a for a in ev["actions"] if a["parameters"][1:2] not in ([v] for v in VIEJAS)]
        zombies = next(g for g in lay["objectsGroups"] if g["name"] == "Zombies")["objects"]
        objs = {o["name"]: o for o in lay["objects"]}
        for z in zombies:
            objs[z["name"]]["variables"] = [v for v in objs[z["name"]]["variables"] if v["name"] not in VIEJAS]
        if not revert:
            ev["conditions"].append(cond(limite))
            ev["actions"].append(ACT)
            for z in zombies:
                objs[z["name"]]["variables"].append({"name": VAR, "type": "number", "value": 0})
            print(f"{escena}: hasta {limite} contagio(s) por zombie ({len(zombies)} zombies)")

    with open(GAME, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else "OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
