#!/usr/bin/env python3
"""
set_resolution_480x270.py  —  sube la resolucion interna de 224x126 a 480x270
para que el personaje (32px) ocupe ~11% del alto en vez de ~24%.

Cambios (edita game/game.json, backup .bak-<ts>):
  - properties.windowWidth/Height: 224/126 -> 480/270
  - camara: reemplaza los 2 eventos (CenterCameraOnObject + ClampCamera) por
    un solo FixCamera(Player, -100,-65, 2600,205). La caja tiene alto = 270
    (= alto de vista) => la Y de camara queda fija: el piso (y=110) queda a
    ~65% de la pantalla, con aire arriba para ver saltos. X sigue al Player.
  - Ground: instancia de 16px -> 110px de alto, para que el piso tenga cuerpo
    hacia abajo y no se vea el vacio bajo la linea de piso.

Revertir:  restaurar el .bak-<ts>, o correr este script con REVERT=1.

Correr desde la raiz del repo:  python3 scripts/set_resolution_480x270.py
Despues en GDevelop: cerrar sin guardar + abrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"

NEW_W, NEW_H = 480, 270
OLD_W, OLD_H = 224, 126
GROUND_H_NEW = 110
GROUND_H_OLD = 16

# FixCamera: caja que encierra la vista. alto 270 == vista -> fija la Y.
CAM_BOX = (-100, -65, 2600, 205)   # left, top, right, bottom


def fixcamera_event():
    return {
        "type": "BuiltinCommonInstructions::Standard",
        "conditions": [],
        "actions": [{
            "type": {"value": "FixCamera"},
            "parameters": ["", "Player",
                           str(CAM_BOX[0]), str(CAM_BOX[1]),
                           str(CAM_BOX[2]), str(CAM_BOX[3]),
                           "yes", "", ""],
        }],
    }


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    p = d["properties"]
    lay = d["layouts"][0]

    w, h = (OLD_W, OLD_H) if revert else (NEW_W, NEW_H)
    p["windowWidth"] = w
    p["windowHeight"] = h
    print(f"resolucion -> {w}x{h}")

    # --- Ground instance height ---
    gh = GROUND_H_OLD if revert else GROUND_H_NEW
    for i in lay["instances"]:
        if i["name"] == "Ground":
            i["height"] = gh
            i["customSize"] = True
    print(f"Ground alto -> {gh}")

    # --- camara ---
    evs = lay["events"]
    # sacar cualquier evento cuyas acciones sean SOLO camara (Center/Clamp/Fix)
    cam_types = {"CenterCameraOnObject", "ClampCamera", "FixCamera"}

    def is_cam_only(e):
        acts = e.get("actions", [])
        return acts and all(a.get("type", {}).get("value") in cam_types for a in acts) \
            and not e.get("conditions") and not e.get("events")

    kept = [e for e in evs if not is_cam_only(e)]
    removed = len(evs) - len(kept)

    if revert:
        # volver a los 2 eventos originales
        cam_evs = [
            {"type": "BuiltinCommonInstructions::Standard", "conditions": [],
             "actions": [{"type": {"value": "CenterCameraOnObject"},
                          "parameters": ["", "Player", "", "", ""]}]},
            {"type": "BuiltinCommonInstructions::Standard", "conditions": [],
             "actions": [{"type": {"value": "ClampCamera"},
                          "parameters": ["", "0", "0", "2400", "126", "", ""]}]},
        ]
    else:
        cam_evs = [fixcamera_event()]

    # reinsertarlos al principio (despues de un evento 0 vacio si existe)
    ins = 1 if (kept and not kept[0].get("actions") and not kept[0].get("conditions")
                and not kept[0].get("events")) else 0
    kept[ins:ins] = cam_evs
    lay["events"] = kept
    print(f"eventos camara: -{removed} +{len(cam_evs)}  (total {len(kept)})")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
