#!/usr/bin/env python3
"""
swap_player_placeholder.py  —  reemplaza el sprite procedural del Player
("Val", de gen_player.py) por un personaje CC0 mejor animado, SOLO como
placeholder para testear con una experiencia más linda mientras el usuario
dibuja el definitivo a mano.

Personaje: "Mask Dude" de **Pixel Adventure 1** (Pixel Frog),
licencia **CC0 / dominio público** (https://pixelfrog-assets.itch.io/pixel-adventure-1).
Se baja de un mirror en GitHub (marpor/PixelAdventure).

Qué hace:
  - baja 5 spritesheets (Idle/Run/Jump/Fall/Hit), 32x32 por frame
  - corta cada frame y lo reubica en canvas 32x34 con los pies en y=34
    (misma convención que el resto de los sprites del juego)
  - escribe game/assets/Player/Player_{Idle,Run,Jump,Fall,Hit,Death}_*.png
    (Death = copia de Hit, no hay death en el pack)
  - edita game/game.json (backup .bak-<ts>): rehace las 6 animaciones del
    objeto Player y sus resources. NO toca behavior, instancia ni eventos
    (los nombres de animación Idle/Run/Jump/Fall/Hit no cambian).
  - deja game/assets/Player/CREDITS.txt

Revertir al Val procedural:  python3 scripts/gen_player.py && python3 scripts/wire_player.py

Correr desde la raíz del repo:  python3 scripts/swap_player_placeholder.py
Después, en GDevelop: Cerrar proyecto sin guardar + Abrir game/game.json.
"""
import json
import datetime
import shutil
import os
import urllib.request
from PIL import Image

GAME = "game/game.json"
ASSETS = "game/assets/Player"
BASE_URL = ("https://raw.githubusercontent.com/marpor/PixelAdventure/HEAD/"
            "PixelAdventure/Main%20Characters/Mask%20Dude")

# (nombre anim, nombre archivo en el pack, loop, timeBetweenFrames)
SHEETS = [
    ("Idle", "Idle",  True,  0.11),
    ("Run",  "Run",   True,  0.045),
    ("Jump", "Jump",  False, 0.10),
    ("Fall", "Fall",  True,  0.10),
    ("Hit",  "Hit",   False, 0.06),
]
TARGET_W, TARGET_H = 32, 34


def fetch(pack_name):
    url = f"{BASE_URL}/{pack_name}%20(32x32).png"
    dst = f"/tmp/_pa_{pack_name}.png"
    urllib.request.urlretrieve(url, dst)
    return Image.open(dst).convert("RGBA")


def slice_and_align(sheet):
    """corta el sheet horizontal en frames 32x32 y los baja a pies=y=34 en 32x34."""
    n = sheet.width // 32
    out = []
    for i in range(n):
        fr = sheet.crop((i * 32, 0, i * 32 + 32, 32))
        bbox = fr.getbbox()
        canvas = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
        if bbox:
            dy = TARGET_H - bbox[3]                 # pie del contenido -> borde inferior
            canvas.alpha_composite(fr, (0, dy))
        out.append(canvas)
    return out


def sprite(img):
    return {"hasCustomCollisionMask": False, "image": img, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def main():
    os.makedirs(ASSETS, exist_ok=True)

    # limpiar frames viejos del Player (gen_player.py los regenera si hace falta)
    for f in os.listdir(ASSETS):
        if f.startswith("Player_") and f.endswith(".png"):
            os.remove(os.path.join(ASSETS, f))

    counts = {}
    for anim, pack_name, _, _ in SHEETS:
        frames = slice_and_align(fetch(pack_name))
        for i, fr in enumerate(frames, 1):
            fr.save(os.path.join(ASSETS, f"Player_{anim}_{i}.png"))
        counts[anim] = len(frames)
        print(f"  {anim}: {len(frames)} frames")

    # Death = copia de Hit
    for i in range(1, counts["Hit"] + 1):
        shutil.copy(os.path.join(ASSETS, f"Player_Hit_{i}.png"),
                    os.path.join(ASSETS, f"Player_Death_{i}.png"))
    counts["Death"] = counts["Hit"]
    print(f"  Death: {counts['Death']} frames (copia de Hit)")

    anims_meta = [
        ("Idle", counts["Idle"], 0.11,  True),
        ("Run",  counts["Run"],  0.045, True),
        ("Jump", counts["Jump"], 0.10,  False),
        ("Fall", counts["Fall"], 0.10,  True),
        ("Hit",  counts["Hit"],  0.06,  False),
        ("Death", counts["Death"], 0.09, False),
    ]

    with open(os.path.join(ASSETS, "CREDITS.txt"), "w") as fh:
        fh.write(
            "Player sprite (PLACEHOLDER temporal):\n"
            '  "Mask Dude" - Pixel Adventure 1, por Pixel Frog\n'
            "  https://pixelfrog-assets.itch.io/pixel-adventure-1\n"
            "  Licencia: CC0 / dominio publico (sin atribucion obligatoria)\n"
            "  Mirror de descarga: github.com/marpor/PixelAdventure\n\n"
            "Se reemplaza por el personaje definitivo dibujado a mano.\n"
            "Para volver al Val procedural: scripts/gen_player.py + scripts/wire_player.py\n"
        )

    # --- game.json ---
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]

    res = d["resources"]["resources"]
    res[:] = [r for r in res if not r["name"].startswith("Player_")]
    for anim, n, _, _ in anims_meta:
        for i in range(1, n + 1):
            res.append({"file": f"assets/Player/Player_{anim}_{i}.png",
                        "kind": "image", "metadata": "", "name": f"Player_{anim}_{i}.png",
                        "smoothed": False, "userAdded": True})

    p = [o for o in lay["objects"] if o["name"] == "Player"][0]
    p["animations"] = [{
        "name": anim, "useMultipleDirections": False,
        "directions": [{
            "looping": loop, "timeBetweenFrames": tbf,
            "sprites": [sprite(f"Player_{anim}_{i}.png") for i in range(1, n + 1)],
        }],
    } for anim, n, tbf, loop in anims_meta]
    print("Player anims:", [(a["name"], len(a["directions"][0]["sprites"])) for a in p["animations"]])

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("resources:", len(res))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
