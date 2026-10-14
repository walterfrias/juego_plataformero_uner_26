#!/usr/bin/env python3
"""
wire_player.py  —  reemplaza el sprite del Player (Knight_Male) por el
personaje nuevo de gen_player.py, y agrega el switch de animación al saltar.

Requiere los assets (correr antes `gen_player.py`):
  game/assets/Player/Player_{Idle,Run,Jump,Fall,Hit,Death}_*.png

Que hace (edita game/game.json, backup .bak-<ts>, idempotente):
  - resources: Player_*.png (20). Quita los resources `Knight Male_*`
    (quedan sin usar; los .png siguen en disco).
  - objeto `Player`: reemplaza las animaciones por
      Idle(4) Run(6) Jump(4) Fall(2) Hit(1) Death(3)
    Mantiene los nombres Idle/Run/Hit (los eventos ya los usan) y suma
    Jump/Fall/Death. NO toca el behavior PlatformerObject (física intacta).
  - instancia `Player`: y 82 -> 76 (sprite ahora 32x34, pies en y=110).
  - eventos nuevos (después de los de Run/Idle, para que ganen):
      si el Player está cayendo   -> animación "Fall"
      si el Player está saltando  -> animación "Jump"

⚠️ Los tipos de condición IsJumping / IsFalling se asumen con el mismo
prefijo que el IsMovingEvenALittle que ya usa el proyecto
(`PlatformBehavior::PlatformerObjectBehavior::...`). Si salen en rojo en
el Diagnostic report, avisar.

Correr desde la raíz del repo:  python3 scripts/wire_player.py
Después, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.
"""
import json
import datetime
import shutil
import os

GAME = "game/game.json"

ANIMS = [
    ("Idle", 4, 0.14, True),
    ("Run", 6, 0.09, True),
    ("Jump", 4, 0.08, False),
    ("Fall", 2, 0.10, True),
    ("Hit", 1, 0.10, False),
    ("Death", 3, 0.16, False),
]
PB = "PlatformBehavior::PlatformerObjectBehavior"


def sprite(img):
    return {"hasCustomCollisionMask": False, "image": img, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts}


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    # --- resources ---
    res = d["resources"]["resources"]
    res[:] = [r for r in res if not r["name"].startswith("Knight Male_")]
    have = {r["name"] for r in res}
    for name, n, _, _ in ANIMS:
        for i in range(1, n + 1):
            rn = f"Player_{name}_{i}.png"
            if rn not in have:
                res.append({"file": f"assets/Player/Player_{name}_{i}.png",
                            "kind": "image", "metadata": "", "name": rn,
                            "smoothed": False, "userAdded": True})

    # --- objeto Player: reemplazar animaciones (conservar behaviors) ---
    p = [o for o in lay["objects"] if o["name"] == "Player"][0]
    p["animations"] = [{
        "name": name, "useMultipleDirections": False,
        "directions": [{
            "looping": loop, "timeBetweenFrames": tbf,
            "sprites": [sprite(f"Player_{name}_{i}.png") for i in range(1, n + 1)],
        }],
    } for name, n, tbf, loop in ANIMS]
    print("Player anims:", [a["name"] for a in p["animations"]])

    # --- instancia: bajar la Y para el sprite 32x34 ---
    inst = [i for i in lay["instances"] if i["name"] == "Player"][0]
    if inst["y"] == 82:
        inst["y"] = 76
    print("Player instance y:", inst["y"])

    # --- eventos Jump / Fall (después de los de Run/Idle) ---
    have_jf = any(
        a.get("type", {}).get("value") == "SetAnimationName"
        and a.get("parameters", [None, None])[1] in ('"Jump"', '"Fall"')
        for e in lay["events"] for a in e.get("actions", []))
    if not have_jf:
        # insertarlos justo después del último evento que setea Run o Idle
        idx = 0
        for k, e in enumerate(lay["events"]):
            for a in e.get("actions", []):
                if a.get("type", {}).get("value") == "SetAnimationName" \
                        and a.get("parameters", [None, None])[1] in ('"Run"', '"Idle"'):
                    idx = k + 1
        jf = [
            std([{"type": {"value": f"{PB}::IsFalling"}, "parameters": ["Player", "PlatformerObject"]}],
                [{"type": {"value": "SetAnimationName"}, "parameters": ["Player", '"Fall"']}]),
            std([{"type": {"value": f"{PB}::IsJumping"}, "parameters": ["Player", "PlatformerObject"]}],
                [{"type": {"value": "SetAnimationName"}, "parameters": ["Player", '"Jump"']}]),
        ]
        lay["events"][idx:idx] = jf
        print(f"eventos Jump/Fall insertados en índice {idx}")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print("resources:", len(res), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    assert os.path.exists("game/assets/Player/Player_Idle_1.png"), \
        "faltan los frames: corré gen_player.py primero"
    main()
