#!/usr/bin/env python3
"""
wire_camera_follow.py  —  arregla dos bugs viejos de la escena:

  (1) El SUELO no cubría la pantalla. Causa: la instancia de `Ground`
      (Tiled Sprite) tenía `customSize:false`, y en ese caso GDevelop la
      dibuja del tamaño de la TEXTURA (16px, ahora 24px), no del ancho
      del objeto (320). -> se pasa a customSize:true con ancho explícito
      que cubre todo el nivel.

  (2) La CÁMARA no seguía al jugador (se iba de pantalla). No había
      ningún evento de cámara. -> se agrega "Centrar la cámara en Player"
      + "Limitar la cámara" a los bordes del nivel.

Además: se sacan los 2 eventos de parallax `SetCameraX` (formato sin
verificar, posiblemente inválidos) y las capas BG pasan a
`followBaseLayerCamera:true` -> el fondo scrollea 1:1 con el mundo, sin
eventos. El parallax con profundidad se puede reintroducir después, ya
validado en el editor.

Edita game/game.json directo. Backup game/game.json.bak-<ts>. Idempotente.
Correr desde la raíz del repo:  python3 scripts/wire_camera_follow.py
Después, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.

⚠️ Los eventos `CenterCameraOnObject` / `ClampCamera` se arman con el
formato de parámetros reconstruido. Si en el editor salen en rojo:
borralos y agregalos a mano (ver instrucciones que te paso aparte).
"""
import json
import datetime
import shutil
import os

GAME = "game/game.json"

LEVEL_LEFT = 0
LEVEL_RIGHT = 2400          # ancho jugable del nivel (placeholder)
GROUND_X = -200
GROUND_W = LEVEL_RIGHT - GROUND_X + 200
SCENE_TOP = 0
SCENE_BOTTOM = 126


def is_setcamerax(evt):
    for a in evt.get("actions", []):
        if a.get("type", {}).get("value") == "SetCameraX":
            return True
    return False


def has_action(events, type_value):
    for e in events:
        for a in e.get("actions", []):
            if a.get("type", {}).get("value") == type_value:
                return True
    return False


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    # (1) Ground: tamaño explícito
    g = [i for i in lay["instances"] if i["name"] == "Ground"][0]
    g["customSize"] = True
    g["width"] = GROUND_W
    g["height"] = 16
    g["x"] = GROUND_X
    g["y"] = 110
    print(f"Ground -> customSize True, x={GROUND_X} w={GROUND_W} h=16")

    # capas BG: seguir la cámara base 1:1 (sin eventos de parallax)
    for l in lay["layers"]:
        if l["name"] in ("BG_far", "BG_near"):
            l["followBaseLayerCamera"] = True

    # sacar los eventos de parallax SetCameraX
    before = len(lay["events"])
    lay["events"] = [e for e in lay["events"] if not is_setcamerax(e)]
    print(f"eventos SetCameraX removidos: {before - len(lay['events'])}")

    # (2) cámara sigue al jugador + límites
    # NOTA: estas acciones llevan un parámetro vacío inicial ("") y DESPUÉS
    # sus parámetros reales. Deducido del "Diagnostic report" de GDevelop:
    #   CenterCameraOnObject:  ["", object, anchorForces, layer, camera]
    #   ClampCamera:           ["", left, top, right, bottom, layer, camera]
    new_events = []
    if not has_action(lay["events"], "CenterCameraOnObject"):
        new_events.append({
            "type": "BuiltinCommonInstructions::Standard", "conditions": [],
            "actions": [{"type": {"value": "CenterCameraOnObject"},
                         "parameters": ["", "Player", "", "", ""]}]})
    if not has_action(lay["events"], "ClampCamera"):
        new_events.append({
            "type": "BuiltinCommonInstructions::Standard", "conditions": [],
            "actions": [{"type": {"value": "ClampCamera"},
                         "parameters": ["", str(LEVEL_LEFT), str(SCENE_TOP),
                                        str(LEVEL_RIGHT), str(SCENE_BOTTOM), "", ""]}]})
    lay["events"][1:1] = new_events
    print(f"eventos de cámara agregados: {len(new_events)}")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print("OK. eventos totales:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
