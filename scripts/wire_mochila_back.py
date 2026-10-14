#!/usr/bin/env python3
"""
wire_mochila_back.py — la mochila puesta (MochilaWorn) va en la espalda de
Lio y lo sigue cuando se da vuelta.

Problemas que arregla (14/10):
  - Iba fija en Player.X()+1 / Player.Y()+13: nunca se daba vuelta, así que
    yendo a la izquierda quedaba adelante del pecho.
  - Muy baja: el +13 y el 8x12 estaban pensados sin la escala del Player
    (se ve a 18x25), así que llegaba hasta los pies.
  - En el Tutorial tenía z=2 (por delante del Player, z=1).

Qué hace (por escena):
  - MochilaWorn a 7x10, z = z del Player - 1 (detrás).
  - En los eventos que ya dan vuelta al Player (control Left/Right +
    FlipX), agrega FlipX de MochilaWorn y la var de escena MochilaFlip
    (0 = mira a la derecha, 1 = a la izquierda). Así se usa la misma lógica
    que el Player, sin depender de una condición "está volteado".
  - Posición: hombros a cintura, del lado de la espalda:
      X = Player.X() + 1 + 9 * MochilaFlip,  Y = Player.Y() + 10

Idempotente. Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_mochila_back.py [Escena ...] [--game ruta]
      (por defecto: Level1)
"""
import datetime
import json
import shutil
import sys

from wire_score_hud import act, find_event, has_cond, set_var

args = sys.argv[1:]
GAME = "game/game.json"
if "--game" in args:
    i = args.index("--game")
    GAME = args[i + 1]
    del args[i:i + 2]
SCENES = args or ["Level1"]

W, H = 7, 10
X = "Player.X() + 1 + 9 * Variable(MochilaFlip)"
Y = "Player.Y() + 10"
CTRL = "PlatformBehavior::PlatformerObjectBehavior::IsUsingControl"


def flip_event(lay, control, flipped):
    return find_event(lay, lambda e: has_cond(e, CTRL, "Player", "PlatformerObject", f'"{control}"')
                      and any(a["type"]["value"] == "FlipX" and a["parameters"] == ["Player", flipped]
                              for a in e.get("actions", [])), f"giro {control}")


def wire(lay):
    set_var(lay, "MochilaFlip")
    player_z = next(i["zOrder"] for i in lay["instances"] if i["name"] == "Player")
    for i in lay["instances"]:
        if i["name"] == "MochilaWorn":
            i.update(customSize=True, width=W, height=H, zOrder=player_z - 1)

    for control, flipped, val in (("Left", "yes", "1"), ("Right", "no", "0")):
        e = flip_event(lay, control, flipped)
        e["actions"] = [a for a in e["actions"]
                        if a["parameters"][:1] not in (["MochilaWorn"], ["MochilaFlip"])]
        e["actions"] += [act("FlipX", ["MochilaWorn", flipped]),
                         act("ModVarScene", ["MochilaFlip", "=", val])]

    follow = find_event(lay, lambda e: has_cond(e, "VarScene", "CanGlide", "=", "1")
                        and any(a["parameters"][:1] == ["MochilaWorn"] and a["type"]["value"] == "SetX"
                                for a in e.get("actions", [])), "mochila sigue al Player")
    for a in follow["actions"]:
        if a["parameters"][:1] == ["MochilaWorn"] and a["type"]["value"] == "SetX":
            a["parameters"] = ["MochilaWorn", "=", X]
        if a["parameters"][:1] == ["MochilaWorn"] and a["type"]["value"] == "SetY":
            a["parameters"] = ["MochilaWorn", "=", Y]


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    lays = {l["name"]: l for l in g["layouts"]}
    for name in SCENES:
        wire(lays[name])
        print(f"{name}: mochila en la espalda ({W}x{H}, sigue el giro)")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
