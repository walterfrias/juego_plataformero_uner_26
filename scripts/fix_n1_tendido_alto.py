#!/usr/bin/env python3
"""
fix_n1_tendido_alto.py  —  los dos primeros tramos del tendido de L1, más arriba
(28/10, pedidos del usuario).

1.er tramo (postes x 862 / 960, cable 864..976): sube POSTE_ALTO_SUBE = 56 px.
   Pisando a los primeros zombies (ZombieD, ZombieN) con J apretada, el rebote dejaba
   los pies de Lio en y −13 sobre ese tramo y caía arriba del cable (y 30): se
   salteaba el antídoto de abajo (x 890) y tenía que volver para atrás. Con el cable
   en y −26 el rebote ya no llega.
2.º tramo (postes x 960 / 1165, cable 962..1181, sobre el árbol alto de x 1050 y
   donde empieza la pintada de Patricio Rey): sube TRAMO2_SUBE = 18 px, "un poco más
   arriba del árbol" (la copa llega a y 30, justo a la altura del cable).

La cámara de L1 muestra y −65..205 (FixCamera): todo sigue a la vista.
Postes, con la base donde estaba (copias del objeto Poste: misma escalera; imágenes
de gen_tendido.py + gen_luz_luna.py):
  x 862, 960   PosteAlto   (+56): arriba el 1.er tramo, la cruceta de abajo el 2.º
  x 1165       PosteMedio  (+18): arriba el 2.º tramo, la de abajo el 3.º (no cambia)
La barra del borde por cercanía (PlatEdge) de cada cable sube con él.

Edita game/game.json (backup .bak-<ts>, idempotente, REVERT=1 lo deja como antes).
Si se re-corre wire_tendido.py, volver a correr este después.
Uso:  python3 scripts/fix_n1_tendido_alto.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402
from gen_tendido import POSTE_ALTO_SUBE, POSTE_H, POSTE_W, TRAMO2_SUBE  # noqa: E402

GAME = "game/game.json"
# objeto: (imagen, cuánto más alto que el Poste común)
OBJS = {"PosteAlto": ("poste_alto_luna.png", POSTE_ALTO_SUBE),
        "PosteMedio": ("poste_medio_luna.png", TRAMO2_SUBE)}
POSTES = {862: "PosteAlto", 960: "PosteAlto", 1165: "PosteMedio"}     # x → objeto
CABLES = {864: (112, POSTE_ALTO_SUBE), 962: (219, TRAMO2_SUBE)}       # x → (ancho, cuánto sube)
POSTE_Y, CABLE_Y, EDGE_Y = 22, 30, 27            # los de wire_tendido.py / wire_bordes_plataforma.py


def main(revert=False):
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lay = next(x for x in d["layouts"] if x["name"] == "Level1")
    res = d["resources"]["resources"]
    fs = lay.get("objectsFolderStructure", {})

    # ---- limpieza (idempotente / revert) ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in OBJS]
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in OBJS]
    imgs = {img for img, _ in OBJS.values()}
    res[:] = [r for r in res if r["name"] not in imgs]

    if not revert:
        poste = next(o for o in lay["objects"] if o["name"] == "Poste")
        for name, (img, sube) in OBJS.items():
            res.append({"file": f"assets/City/{img}", "kind": "image", "metadata": "",
                        "name": img, "smoothed": False, "userAdded": True})
            o = copy.deepcopy(poste)
            o["name"] = name
            h = POSTE_H + sube
            for a in o["animations"]:
                for dr in a["directions"]:
                    for s in dr["sprites"]:
                        s["image"] = img
                        s["customCollisionMask"] = [[{"x": x, "y": y} for x, y in
                                                     [(3, 3), (POSTE_W - 3, 3), (POSTE_W - 3, h - 4), (3, h - 4)]]]
            lay["objects"].append(o)
            if "children" in fs:
                fs["children"].append({"objectName": name})

    # ---- instancias ----
    n = {"postes": 0, "cables": 0, "bordes": 0}
    for i in lay["instances"]:
        x = round(i["x"])
        if i["name"] in ("Poste", *OBJS) and x in POSTES:
            obj = "Poste" if revert else POSTES[x]
            i["name"] = obj
            i["y"] = POSTE_Y - (0 if revert else OBJS[obj][1])
            n["postes"] += 1
        elif i["name"] in ("Cable", "PlatEdge") and x in CABLES and round(i["width"]) == CABLES[x][0]:
            sube = 0 if revert else CABLES[x][1]
            i["y"] = (CABLE_Y if i["name"] == "Cable" else EDGE_Y) - sube
            n["cables" if i["name"] == "Cable" else "bordes"] += 1
    assert n == {"postes": 3, "cables": 2, "bordes": 2}, n

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else
          f"Level1: 1.er tramo +{POSTE_ALTO_SUBE} px (cable y {CABLE_Y - POSTE_ALTO_SUBE}), "
          f"2.º tramo +{TRAMO2_SUBE} px (cable y {CABLE_Y - TRAMO2_SUBE})")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    for img, _ in OBJS.values():
        assert os.path.exists(f"game/assets/City/{img}"), "corré gen_tendido.py y gen_luz_luna.py primero"
    main(revert=os.environ.get("REVERT") == "1")
