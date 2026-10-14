#!/usr/bin/env python3
"""
wire_n1_tweaks_0915.py — 3 ajustes de gameplay pedidos por el usuario
tras un playtest (2026-09-15), sobre Nivel 1:

  1. La horda ("quedarse atrás" la agarra) ahora saca 2 vidas en vez de
     1 (evento existente, sólo se cambia el número).
  2. Se sacan los últimos enemigos del tramo final (ZombieJ completo —
     objeto, variable de escena, eventos de patrulla y su única
     instancia— y la instancia de ZombieMarcha en x=2120): el usuario
     los probó y no hacían nada (no se podían matar ni sacaban vida).
     No se pudo reproducir la causa exacta mirando el JSON (están en
     el grupo "Zombies" igual que el resto, que sí funciona), así que
     en vez de intentar "arreglarlos" se los saca y se reemplazan por
     zombies nuevos más simples.
  3. Se agregan 3 zombies QUIETOS (sin patrulla, sin variable de
     dirección propia — así no repiten el bug de arriba) en el tramo
     final (x 2210/2380/2480, antes de Meta en x=2569), reusando el
     arte ya cargado de ZombieJ/D/T (mismo patrón que Virus/Antídoto:
     un objeto Sprite simple con 1 animación en loop, sumado al grupo
     "Zombies" para heredar gratis el stomp/daño ya cableado — no
     hace falta ningún evento nuevo de combate).

No toca el antídoto/mochila ni la caída al río (evento aparte, sin
relación con la horda). El virus (3 instancias más) se agrega aparte
corriendo scripts/wire_virus.py, que ya estaba preparado con 5.

Edita game/game.json (backup .bak-<ts>, idempotente, marca eventos
propios con "_tw0915": true). REVERT=1 para deshacer.
Uso: python3 scripts/wire_n1_tweaks_0915.py   (GDevelop CERRADO)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"

# --- zombies quietos nuevos: (nombre, x, y, frames reusados) ---
GROUND_Y, SPRITE_H = 110, 34
NEW_ZOMBIES = [
    ("ZombieEnd1", 2210, [f"Zombie_J_Walk_{i}.png" for i in range(1, 9)]),
    ("ZombieEnd2", 2380, [f"ZombieD_Walk_{i}.png" for i in range(1, 9)]),
    ("ZombieEnd3", 2480, [f"ZombieT_Walk_{i}.png" for i in range(1, 9)]),
]
NEW_NAMES = [n for n, *_ in NEW_ZOMBIES]

REMOVED_OBJ = ["ZombieJ"]
REMOVED_VARS = ["ZombieJDir"]


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, "_tw0915": True}


def zombie_object(name, frames):
    return {
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": name, "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Walk", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 0.13,
                                        "sprites": [{"hasCustomCollisionMask": False,
                                                     "image": f, "points": [],
                                                     "originPoint": {"name": "origine", "x": 0, "y": 0},
                                                     "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                                                     "customCollisionMask": []} for f in frames]}]}]}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    assert lay["name"] == "Level1"

    # ---- limpieza idempotente de lo que agrega ESTE script ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NEW_NAMES]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in NEW_NAMES]
    lay["events"] = [e for e in lay["events"] if not e.get("_tw0915")]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] not in NEW_NAMES]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NEW_NAMES]

    if revert:
        # 1) horda vuelve a -1 vida
        for e in lay["events"]:
            conds = {c["type"]["value"]: c["parameters"] for c in e.get("conditions", [])}
            if (conds.get("VarScene") == ["HordaActive", "=", "1"]
                    and conds.get("PosX") == ["Player", "<", "HordaPiso.X() - 25"]):
                for a in e["actions"]:
                    if a["type"]["value"] == "ModVarScene" and a["parameters"][:2] == ["Lives", "-"]:
                        a["parameters"][2] = "1"
        # 2) ZombieJ vuelve (sólo se puede deshacer re-corriendo wire_zombies_wave2.py)
        print("NOTA: para restaurar ZombieJ y la instancia de ZombieMarcha en x=2120,")
        print("volvé a correr scripts/wire_zombies_wave2.py y agregá la instancia a mano.")
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK (parcial, ver nota arriba)")
        return

    # ---- 1) horda: -1 -> -2 vidas ----
    changed = 0
    for e in lay["events"]:
        conds = {c["type"]["value"]: c["parameters"] for c in e.get("conditions", [])}
        if (conds.get("VarScene") == ["HordaActive", "=", "1"]
                and conds.get("PosX") == ["Player", "<", "HordaPiso.X() - 25"]):
            for a in e["actions"]:
                if a["type"]["value"] == "ModVarScene" and a["parameters"][:2] == ["Lives", "-"]:
                    a["parameters"][2] = "2"
                    changed += 1
    assert changed == 1, f"esperaba modificar 1 accion de la horda, modifique {changed}"

    # ---- 2) sacar ZombieJ (objeto + var + eventos + grupo + instancia) ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in REMOVED_OBJ]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in REMOVED_VARS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in REMOVED_OBJ]
    lay["events"] = [e for e in lay["events"]
                     if not any(a.get("parameters", [""])[0] in REMOVED_OBJ
                                for a in e.get("actions", []))]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] not in REMOVED_OBJ]
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in REMOVED_OBJ]

    # ---- 2b) sacar la instancia de ZombieMarcha en x=2120 (deja las otras 4) ----
    before = len(lay["instances"])
    lay["instances"] = [i for i in lay["instances"]
                        if not (i["name"] == "ZombieMarcha" and abs(i["x"] - 2120) < 1)]
    assert len(lay["instances"]) == before - 1, "esperaba sacar exactamente 1 instancia de ZombieMarcha"

    # ---- 3) agregar 3 zombies quietos nuevos al tramo final ----
    grp = next((g for g in lay.get("objectsGroups", []) if g["name"] == "Zombies"), None)
    for name, x, frames in NEW_ZOMBIES:
        lay["objects"].append(zombie_object(name, frames))
        if "children" in fs:
            fs["children"].append({"objectName": name})
        if grp is not None and not any(o["name"] == name for o in grp["objects"]):
            grp["objects"].append({"name": name})
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": "",
            "name": name, "persistentUuid": str(uuid.uuid4()),
            "width": 0, "x": x, "y": GROUND_Y - SPRITE_H, "zOrder": 2,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})
        lay["events"].append(std([], [{"type": {"value": "SetAnimationName"},
                                        "parameters": [name, '"Walk"']}]))

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("horda: Lives - 2 (era -1)")
    print("sacado: ZombieJ (objeto+eventos+instancia), ZombieMarcha@x=2120")
    print("agregado:", NEW_NAMES, "al grupo Zombies")
    print("total instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
