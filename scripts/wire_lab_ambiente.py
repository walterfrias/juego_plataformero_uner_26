#!/usr/bin/env python3
"""
wire_lab_ambiente.py  —  luces de ambiente del laboratorio (sprint de arte
del 18/10). Las zonas oscuras de L2 eran un velo gris parejo (LabSombra) y
la arena de L3 se veía como cualquier pasillo: ahora la oscuridad tiene
islas de luz con color.

Requiere: gen_lab_ambiente.py (luz_tanque, luz_monitor, baliza, baliza_haz,
alarma_tinte) y wire_lab_luces.py (capa Atmos con LabSombra / LampGlow).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_lab_ambiente": true). Todo va en la capa Atmos POR ENCIMA de la sombra
(LabSombra z 0, LampGlow z 1), si no la sombra lo apaga:
  - LuzTanque (z 3): resplandor verde de los tanques del fondo + charco en
    el piso, dentro de las zonas oscuras de L2 y en la arena de L3. Burbujea
    (opacidad con dos senos).
  - LuzMonitor (z 3): resplandor cian de los monitores, con algún parpadeo
    corto de vez en cuando (floor(0.5*sin + 0.52) = 1 solo si sin > 0.96).
  - Zona de ALARMA (tramo final de L2, 2940..3800, y la arena de L3):
      Baliza (z 5): cúpula roja en los pilares entre ventanales.
      BalizaHaz (z 4): haz rojo que barre ±60° rotando desde la punta de
        arriba (origen y centro de rotación en (35, 0)); más brillante al
        pasar por el medio, como una baliza que gira.
      AlarmaTinte (z 2): tinte rojo de toda la zona que late. En L3 late más
        rápido cuanto menos vida le queda al jefe (BossHP 3 → 2 → 1). Se
        apaga al ganar (Won).
Posiciones: los tanques y monitores salen de lab_near.png (tile de 224 px
desde LabNear.x: tanques en x 58..106, monitores en 132 y 162); los pilares
de la pared caen cada 112 px desde LabFar.x.
Re-correr después de `wire_levels23.py --force` y de `wire_lab_luces.py`.
Uso:  python3 scripts/wire_lab_ambiente.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import uuid

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
MARK = "_lab_ambiente"
LAYER = "Atmos"
TANQUE, MONITOR, BALIZA, HAZ, TINTE = "LuzTanque", "LuzMonitor", "Baliza", "BalizaHaz", "AlarmaTinte"
MINE = {TANQUE, MONITOR, BALIZA, HAZ, TINTE}
RES = ["luz_tanque.png", "luz_monitor.png", "baliza.png", "baliza_haz.png", "alarma_tinte.png"]
TILE = 224
TANK_DX, MON_DX = 52, (127, 157)       # en el tile de lab_near (sprite: tanque x-6, monitor x-5)
PILLAR = 112                           # pilares de la pared: cada 112 px desde LabFar.x
BEACON_Y = 30                          # baliza: 30 px debajo del borde de arriba de LabFar
TINT_MAX = 38                          # opacidad máxima del tinte rojo
T = "TimeFromStart()"

# zonas por escena: oscuras (luces de tanque/monitor) y de alarma (balizas + tinte)
SCENES = {
    "Level2": {"dark": [(1740, 2200), (2940, 3800)], "alarm": (2940, 3800),
               "beacons": [3060, 3396, 3732], "rate": "3"},
    "Level3": {"dark": [(-60, 540)], "alarm": (-60, 540),
               "beacons": [148, 372], "rate": "3 + (3 - Variable(BossHP)) * 1.5"},
}


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def foreach(obj, acts):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], "events": [
                {"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": acts}],
            MARK: True}


def sprite_obj(base, name, image, origin=(0, 0), variables=()):
    o = copy.deepcopy(base)
    o.update(name=name, behaviors=[], effects=[],
             variables=[{"name": k, "type": "number", "value": v} for k, v in variables])
    ox, oy = origin
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": False, "timeBetweenFrames": 1, "sprites": [{
            "hasCustomCollisionMask": False, "image": image, "points": [],
            "originPoint": {"name": "origine", "x": ox, "y": oy},
            "centerPoint": {"automatic": origin == (0, 0), "name": "centre", "x": ox, "y": oy},
            "customCollisionMask": []}]}]}]
    return o


def inst(name, x, y, z, w=None, h=None, vars_=()):
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": LAYER,
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def inside(x, zones, w=0):
    return any(a <= x + w / 2 <= b for a, b in zones)


def wire_scene(sc, cfg):
    # ---- limpieza (idempotente) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]

    # ---- objetos ----
    base = next(o for o in sc["objects"] if o["name"] == "LampGlow")
    sc["objects"] += [
        sprite_obj(base, TANQUE, "luz_tanque.png", variables=[("Seed", 0)]),
        sprite_obj(base, MONITOR, "luz_monitor.png", variables=[("Seed", 0)]),
        sprite_obj(base, BALIZA, "baliza.png"),
        sprite_obj(base, HAZ, "baliza_haz.png", origin=(35, 0), variables=[("Seed", 0)]),
        sprite_obj(base, TINTE, "alarma_tinte.png"),
    ]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in (TANQUE, MONITOR, BALIZA, HAZ, TINTE)]

    # ---- instancias ----
    near = next(i for i in sc["instances"] if i["name"] == "LabNear")
    far = next(i for i in sc["instances"] if i["name"] == "LabFar")
    nx0, ny = near["x"], near["y"]
    n_tiles = -(-int(near["width"]) // TILE)
    new, k = [], 0
    for t in range(n_tiles):
        tx = nx0 + t * TILE
        if inside(tx + TANK_DX, cfg["dark"], 64):
            new.append(inst(TANQUE, tx + TANK_DX, ny - 4, 3, vars_=[("Seed", round(k * 2.39 % 6.28, 2))]))
            k += 1
        for mdx in MON_DX:
            if inside(tx + mdx, cfg["dark"], 34):
                new.append(inst(MONITOR, tx + mdx, ny + 15, 3, vars_=[("Seed", round(k * 1.7 % 6.28, 2))]))
                k += 1
    a0, a1 = cfg["alarm"]
    new.append(inst(TINTE, a0, far["y"] + 1, 2, a1 - a0, 270))
    by = far["y"] + BEACON_Y
    for j, bx in enumerate(cfg["beacons"]):
        assert (bx - far["x"]) % PILLAR == 0, f"baliza en x={bx} no cae en un pilar"
        new.append(inst(HAZ, bx, by + 4, 4, vars_=[("Seed", round(j * 2.1, 2))]))
        new.append(inst(BALIZA, bx - 5, by, 5))
    sc["instances"] += new

    # ---- eventos ----
    sweep = f"({T} * 2.4 + {HAZ}.Variable(Seed))"
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Luces de ambiente (wire_lab_ambiente.py): resplandor de tanques y monitores en "
                    "las zonas oscuras; zona de alarma con balizas que barren y tinte rojo que late.",
         "comment2": "", MARK: True},
        foreach(TANQUE, [ins("Opacity", [TANQUE, "=",
            f"round(255 * (0.8 + 0.12 * sin({T} * 1.3 + {TANQUE}.Variable(Seed))"
            f" + 0.06 * sin({T} * 4.1 + {TANQUE}.Variable(Seed) * 2)))"])]),
        foreach(MONITOR, [ins("Opacity", [MONITOR, "=",
            # floor(0.5*sin + 0.52) = 1 solo si sin > 0.96: un parpadeo corto de vez en cuando
            f"round(255 * (0.85 - 0.6 * floor(0.5 * sin({T} * 7 + {MONITOR}.Variable(Seed) * 3) + 0.52)))"])]),
        foreach(HAZ, [
            ins("SetAngle", [HAZ, "=", f"60 * sin{sweep}"]),
            # más brillante al pasar por el medio (de frente), como una baliza que gira
            ins("Opacity", [HAZ, "=", f"round(255 * (0.3 + 0.7 * abs(cos{sweep})))"]),
        ]),
        {"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": [
            ins("Opacity", [TINTE, "=",
                f"round({TINT_MAX} * (0.5 + 0.5 * sin({T} * ({cfg['rate']}))) * (1 - Variable(Won)))"])],
         MARK: True},
    ]
    counts = {n: sum(1 for i in new if i["name"] == n) for n in (TANQUE, MONITOR, BALIZA)}
    print(f"{sc['name']}: {counts}")


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
    for name, cfg in SCENES.items():
        sc = next(x for x in d["layouts"] if x["name"] == name)
        assert any(ly["name"] == LAYER for ly in sc["layers"]), f"{name} sin capa {LAYER}: wire_lab_luces.py"
        wire_scene(sc, cfg)
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Lab/luz_tanque.png"), "corré gen_lab_ambiente.py primero"
    main()
