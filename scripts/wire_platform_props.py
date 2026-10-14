#!/usr/bin/env python3
"""
wire_platform_props.py  —  hace que Farol / ArbolBajo / ArbolAlto funcionen
como plataforma, igual que el puesto de feria: comportamiento Jumpthru
(atravesable) + máscara de colisión custom SOLO en la parte de arriba. El
player los cruza por abajo/al costado y sólo se apoya saltando encima.

**Sólo toca las DEFINICIONES de objeto** (comportamiento + máscara del
sprite). NO toca ninguna instancia: podés seguir duplicando / moviendo /
escalando estos objetos en el editor de GDevelop sin que esto los pise.

Edita game/game.json (backup .bak-<ts>, idempotente):
  - adaptCollisionMaskAutomatically -> false
  - a cada sprite: hasCustomCollisionMask + máscara del techo
  - behaviors: agrega Platform (Jumpthru) si no está

Revertir:  REVERT=1 python3 scripts/wire_platform_props.py
Uso:  python3 scripts/wire_platform_props.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"

# máscara = polígono de la franja superior del sprite (coords de píxel del sprite)
#   [(x, y), ...]  — convexo, 3-8 puntos
MASKS = {
    "Farol":     [(2, 1), (18, 1), (18, 8), (2, 8)],        # sprite 20x56, la luminaria
    "ArbolBajo": [(6, 2), (36, 2), (36, 9), (6, 9)],        # sprite 42x44, tope de la copa
    "ArbolAlto": [(8, 2), (40, 2), (40, 10), (8, 10)],      # sprite 48x82, tope de la copa
}
JUMPTHRU = {"name": "Platform", "type": "PlatformBehavior::PlatformBehavior",
            "platformType": "Jumpthru"}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    touched = []

    for o in lay["objects"]:
        name = o["name"]
        if name not in MASKS:
            continue
        touched.append(name)

        if revert:
            o["adaptCollisionMaskAutomatically"] = True
            o["behaviors"] = [b for b in o.get("behaviors", [])
                              if not (b.get("name") == "Platform"
                                      and b.get("type") == "PlatformBehavior::PlatformBehavior")]
            for anim in o.get("animations", []):
                for direction in anim.get("directions", []):
                    for spr in direction.get("sprites", []):
                        spr["hasCustomCollisionMask"] = False
                        spr["customCollisionMask"] = []
            continue

        o["adaptCollisionMaskAutomatically"] = False
        if not any(b.get("name") == "Platform" for b in o.get("behaviors", [])):
            o.setdefault("behaviors", []).append(dict(JUMPTHRU))
        poly = [{"x": x, "y": y} for x, y in MASKS[name]]
        for anim in o.get("animations", []):
            for direction in anim.get("directions", []):
                for spr in direction.get("sprites", []):
                    spr["hasCustomCollisionMask"] = True
                    spr["customCollisionMask"] = [poly]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print(("revert " if revert else "") + "OK — objetos:", touched)
    if not revert:
        missing = [n for n in MASKS if n not in touched]
        if missing:
            print("OJO: no encontrados en Level1 (¿faltan wire de esos objetos?):", missing)


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
