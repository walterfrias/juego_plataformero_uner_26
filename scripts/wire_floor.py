#!/usr/bin/env python3
"""
wire_floor.py  —  cambia la textura del objeto `Ground` (Tiled Sprite) de
`Tiled_Flooring.png` (placeholder marrón) a `sidewalk.png` (vereda noche).

Requiere que exista el asset (correr antes `gen_floor.py`):
  game/assets/City/sidewalk.png

Edita game/game.json directo. Backup game/game.json.bak-<ts>. Idempotente.

No toca la instancia, el tamaño (320x16) ni el comportamiento Platform:
solo el campo `texture` del objeto y agrega el resource.

Correr desde la raíz del repo:  python3 scripts/wire_floor.py
Después, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.
"""
import json
import datetime
import shutil
import os

GAME = "game/game.json"
NEW_TEXTURE = "sidewalk.png"
RESOURCE_FILE = "assets/City/sidewalk.png"


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))

    res = d["resources"]["resources"]
    if NEW_TEXTURE not in {r["name"] for r in res}:
        res.append({"file": RESOURCE_FILE, "kind": "image", "metadata": "",
                    "name": NEW_TEXTURE, "smoothed": False, "userAdded": True})

    ground = [o for o in d["layouts"][0]["objects"] if o["name"] == "Ground"][0]
    old = ground["texture"]
    ground["texture"] = NEW_TEXTURE

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    json.load(open(GAME))
    print(f"Ground.texture: {old} -> {ground['texture']}")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    assert os.path.exists("game/" + RESOURCE_FILE), "falta sidewalk.png: corré gen_floor.py primero"
    main()
