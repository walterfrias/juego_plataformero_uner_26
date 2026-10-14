#!/usr/bin/env python3
"""
remove_zombie_end_all.py — saca los 6 zombies "ZombieEnd*" del tramo
final (agregados por wire_n1_tweaks_0915.py y wire_n1_tweaks_0915b.py).

Motivo: el usuario los probó 3 veces en el editor de GDevelop (incluso
reabriendo el proyecto de cero) y los sigue viendo rotos — 4 sprites
IDÉNTICOS y quietos, cuando deberían ser 6 distintos y la mitad
patrullando. Un test aparte (build exportado real vía gdexporter +
Chromium headless, scripts/_test_*.json ya borrados) mostró que el
stomp y el daño SÍ funcionan ahí — así que la sospecha es un problema
puntual del preview del editor de GDevelop con objetos/grupos armados
por script en vez de por UI, no del código en sí. Sin poder reproducir
esto en el entorno del usuario, se sacan directamente en vez de seguir
iterando a ciegas.

NO toca: horda a -2 vidas (wire_n1_tweaks_0915.py punto 1) ni los 3
virus nuevos (wire_virus.py) — eso quedó confirmado que funciona.

Edita game/game.json (backup .bak-<ts>, idempotente).
Uso: python3 scripts/remove_zombie_end_all.py   (GDevelop CERRADO)
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"
NAMES = [f"ZombieEnd{i}" for i in range(1, 7)]
VARS = [f"{n}Dir" for n in NAMES]


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    assert lay["name"] == "Level1"

    before_objs = len(lay["objects"])
    before_insts = len(lay["instances"])
    before_evs = len(lay["events"])

    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NAMES]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in NAMES]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in VARS]
    lay["events"] = [e for e in lay["events"]
                     if not e.get("_tw0915") and not e.get("_tw0915b")]
    for g in lay.get("objectsGroups", []):
        if g["name"] == "Zombies":
            g["objects"] = [o for o in g["objects"] if o["name"] not in NAMES]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NAMES]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print(f"objetos: {before_objs} -> {len(lay['objects'])}")
    print(f"instancias: {before_insts} -> {len(lay['instances'])}")
    print(f"eventos: {before_evs} -> {len(lay['events'])}")
    print("sacados:", NAMES)


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main()
