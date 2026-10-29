#!/usr/bin/env python3
"""
wire_l3_antidotos.py  —  4 antídotos en el Nivel 3 (28/10, pedido del usuario: "no
los tiene"). L3 ya traía el premio por 4/4 (+1 vida apenas se juntan y +1000 al
ganar, de wire_score_hud.py), pero no había frascos, ni el evento de agarrarlos, ni
el contador del HUD.

Todo se copia de Level2, sin piezas nuevas: objetos `Antidoto`, `HudAntiIcon` y
`HudAnti` (mismas instancias de HUD, arriba a la izquierda junto a las vidas), el
evento de agarrar (+250, popup, sonido, Antidotes + 1) y, en el evento del HUD, el
texto "n/4" que se pone verde con 4.

Uno por tramo del recorrido (x de juego = x de diseño de l3_recorrido.py − 2100):
  1. calle del hospital: arriba del toldo que rebota (se agarra subiendo; saltando
     desde el piso no se llega)
  2. la plaza: en el piso, en la patrulla del ZombieM (riesgo / premio)
  3. Corrientes: sobre el cable, arriba del charco electrificado
  4. llegada al Obelisco: sobre la segunda marquesina (se sube con el vapor)

Edita game/game.json (backup .bak-<ts>, idempotente). Correr después de
wire_score_hud.py si se regenera L3.
Uso:  python3 scripts/wire_l3_antidotos.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402

GAME = "game/game.json"
OBJS = ("Antidoto", "HudAntiIcon", "HudAnti")
ANTI_W, ANTI_H = 14, 18
# (x, y) esquina de arriba del frasco, en coordenadas del juego
FRASCOS = [
    (-1488, 34),                         # toldo (x −1504..−1458, y 116): rebota hasta pies ≈ 32
    (-1115, 150 - ANTI_H - 2),           # plaza, en el piso (ZombieM patrulla −1190..−1090)
    (-760, 70 - ANTI_H - 2),             # sobre el cable de Corrientes (−828..−582, y 70)
    (-159, 76 - ANTI_H - 2),             # sobre la 2.ª marquesina (−188..−116, y 76)
]


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get("events", []))


def nombra(e, txt):
    return txt in json.dumps({k: e.get(k) for k in ("conditions", "actions")})


def es_agarrar(e):
    return any(c["type"]["value"] == "CollisionNP" and c["parameters"][:2] == ["Player", "Antidoto"]
               for c in e.get("conditions", []))


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    with open(GAME) as f:
        texto = f.read()
    with open(f"{GAME}.bak-{ts}", "w") as f:
        f.write(texto)
    print("backup", f"{GAME}.bak-{ts}")
    d = json.loads(texto)
    l2 = next(x for x in d["layouts"] if x["name"] == "Level2")
    l3 = next(x for x in d["layouts"] if x["name"] == "Level3")
    evs = l3["events"]

    # ---- limpieza (idempotente) ----
    l3["objects"] = [o for o in l3["objects"] if o["name"] not in OBJS]
    l3["instances"] = [i for i in l3["instances"] if i["name"] not in OBJS]
    fs = l3.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in OBJS]
    evs[:] = [e for e in evs if not es_agarrar(e)]
    hud3 = next(e for e in walk(evs) if nombra(e, '"HudScore"'))      # dentro del grupo "HUD y puntaje"
    hud3["actions"] = [a for a in hud3["actions"] if a["parameters"][:1] != ["HudAnti"]]
    hud3["events"] = [e for e in hud3.get("events", []) if not nombra(e, '"HudAnti"')]

    # ---- objetos e instancias de HUD, copiados de L2 ----
    for nm in OBJS:
        l3["objects"].append(copy.deepcopy(next(o for o in l2["objects"] if o["name"] == nm)))
        if "children" in fs:
            fs["children"].append({"objectName": nm})
    for i in l2["instances"]:
        if i["name"] in ("HudAntiIcon", "HudAnti"):
            l3["instances"].append(dict(copy.deepcopy(i), persistentUuid=str(uuid.uuid4())))
    plantilla = next(i for i in l2["instances"] if i["name"] == "Antidoto")
    for x, y in FRASCOS:
        i = copy.deepcopy(plantilla)
        i.update(x=x, y=y, layer="", persistentUuid=str(uuid.uuid4()))
        l3["instances"].append(i)

    # ---- eventos: agarrar (antes del premio por 4/4) y el contador del HUD ----
    agarrar = copy.deepcopy(next(e for e in l2["events"] if es_agarrar(e)))
    premio = next(k for k, e in enumerate(evs) if nombra(e, '"AntidoteBonus", "="'))
    evs.insert(premio, agarrar)
    hud2 = next(e for e in walk(l2["events"]) if nombra(e, '"HudScore"'))
    hud3["actions"] += [copy.deepcopy(a) for a in hud2["actions"] if a["parameters"][:1] == ["HudAnti"]]
    hud3.setdefault("events", []).extend(
        copy.deepcopy(e) for e in hud2.get("events", []) if nombra(e, '"HudAnti"'))

    with open(GAME, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    json.load(open(GAME))
    print(f"Level3: {len(FRASCOS)} antídotos, evento de agarrar y contador n/4 en el HUD")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main()
