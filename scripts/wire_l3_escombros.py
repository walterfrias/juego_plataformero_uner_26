#!/usr/bin/env python3
"""
wire_l3_escombros.py  —  escombros y tachos rotos en la calle del Nivel 3 (28/10).
Pedido del usuario: "agrega algunos escombros, quizás tachos de basura rotos en la
calle, que se vea algo de caos". Todo DECORADO: sin colisión ni eventos.

Requiere: gen_l3_escombros.py (arte).

Tres alturas, como el resto de la calle (wire_l3_caos.py):
  - VEREDA (capa Decor z 0, detrás de Lio y de los tachos con fuego): apoyado en el
    piso (y 150). Lejos del toldo, el charco, los respiraderos del vapor y la valla.
  - ASFALTO, carril de atrás (capa "" z 2, apoyado en y 199, como los conos y el
    escombro de wire_l3_caos.py), en los huecos entre autos, colectivo y conos.
  - CARRIL DE ADELANTE (28/10): algunos al doble y más abajo (y 246), como los
    patrulleros: más cerca de la cámara.
Ubicación en VEREDA / ASFALTO / CERCA (x de diseño, como l3_recorrido.py).

Es independiente de wire_l3_caos.py (objetos propios): re-correr ese NO hace falta y
no conviene (borra el HumoAuto de wire_l3_arena_9dejulio.py). Idempotente.
Edita game/game.json (backup .bak-<ts>). REVERT=1 los saca.
Uso:  python3 scripts/wire_l3_escombros.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import sys
import uuid

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l3_recorrido as R  # noqa: E402
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402

GAME = "game/game.json"
OBJS = {"TachoVolcado": "tacho_volcado.png", "TachoRoto": "tacho_roto.png",
        "BolsasBasura": "bolsas_basura.png", "EscombrosPila": "escombros_pila.png",
        "BasuraSuelta": "basura_suelta.png"}
PISO_VEREDA, PISO_CALLE = R.FLOOR, 199
# (objeto, x de diseño). Ojo con: toldo 596..642, banco 850, charco 1290..1500 (bajo el
# cable), vapores 1748 / 1880 (28 px), valla 2060; tachos con fuego 380, 820, 1560, 1960
VEREDA = [
    ("BasuraSuelta", 345),                                        # salida del lab
    ("TachoVolcado", 404), ("BasuraSuelta", 428),                 # junto al tacho que arde
    ("BolsasBasura", 520),
    ("EscombrosPila", 660),                                       # pasando el toldo
    ("BasuraSuelta", 735),
    ("TachoRoto", 890), ("BasuraSuelta", 910),                    # plaza, al lado del banco
    ("BolsasBasura", 1085),
    ("TachoVolcado", 1215),
    ("EscombrosPila", 1525),                                      # Corrientes, pasando el charco
    ("BolsasBasura", 1590),
    ("TachoRoto", 1680),
    ("BasuraSuelta", 1800),                                       # entre los dos respiraderos
    ("TachoVolcado", 1984),
    ("EscombrosPila", 2028),
]
# carril de atrás: autos 410, colectivo 860..984, cubierta 1010, escombro 1030, taxi
# 1110..1168, autos 1390 / 1850 / 2150 (60 px), conos 760 / 776 / 1600
ASFALTO = [
    ("EscombrosPila", 486), ("BasuraSuelta", 700),
    ("TachoVolcado", 1190), ("BasuraSuelta", 1300),
    ("EscombrosPila", 1470), ("TachoVolcado", 1700),
    ("BasuraSuelta", 1990), ("EscombrosPila", 2050),
]
# carril de ADELANTE (28/10, "acercá algunos a la cámara para que se vean más grandes"):
# al doble, píxel a píxel, apoyados en y 246 como los patrulleros de wire_l3_caos.py
# (PISO_CERCA), capa "" z 1. Libre el patrullero de adelante (610..738) y su resplandor.
ESCALA_CERCA, PISO_CERCA = 2, 246
CERCA = [
    ("EscombrosPila", 470), ("TachoVolcado", 820), ("BolsasBasura", 1000),
    ("BasuraSuelta", 1240), ("TachoRoto", 1330), ("EscombrosPila", 1560),
    ("TachoVolcado", 1780), ("BolsasBasura", 1950),
]
# algunos de los de adelante, PRENDIDOS FUEGO (28/10: de cerca y oscuros "se perdían"
# contra el asfalto). Con objetos que ya existen en L3: NocheFuego (la llama de los tachos
# de la vereda, 12x16) al doble, LuzFuegoCalle (el resplandor de los autos, 130x56: titila
# con el evento de wire_l3_caos.py, por la var Seed) y HumoAuto (40x64) en Atmos.
# (x del CERCA) → (dónde nace la llama, en px del sprite SIN escalar desde su esquina de
# arriba, z de la llama: 0 detrás del objeto, adentro del tacho; 2 delante)
FUEGOS = {
    ("TachoVolcado", 820): ((15, 5), 2),        # por la boca del tacho tirado
    ("TachoRoto", 1330): ((8, 3), 0),           # desde adentro, por arriba del aro
    ("BolsasBasura", 1950): ((12, 4), 2),       # la pila de bolsas
}
LLAMA_W, LLAMA_H = 12, 16                       # NocheFuego; la base de la llama es su fila de abajo


def sprite_obj(tpl, name, image):
    o = copy.deepcopy(tpl)
    o.update(name=name, effects=[], behaviors=[], variables=[])
    spr = o["animations"][0]["directions"][0]["sprites"][0]
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": False, "timeBetweenFrames": 1,
        "sprites": [dict(spr, image=image, hasCustomCollisionMask=False, customCollisionMask=[], points=[])]}]}]
    return o


def inst(name, x, y, z, layer, size=None, vars_=()):
    w, h = size or (0, 0)
    return {"angle": 0, "customSize": size is not None, "height": h, "layer": layer, "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def fuegos(alto):
    """llama, resplandor y humo de cada pieza de FUEGOS (objetos de otros scripts: se
    reconocen por nombre + posición para poder sacarlos al re-correr)."""
    e, out = ESCALA_CERCA, []
    for k, ((name, x), ((fx, fy), z)) in enumerate(FUEGOS.items()):
        gx, gy = x + R.OFFSET_X, PISO_CERCA - alto[name] * e
        cx, base = gx + fx * e, gy + fy * e                  # centro y base de la llama
        out.append(inst("NocheFuego", cx - LLAMA_W * e // 2, base - LLAMA_H * e, z, "",
                        size=(LLAMA_W * e, LLAMA_H * e)))
        out.append(inst("LuzFuegoCalle", cx - 65, base - 34, -2, "", vars_=[("Seed", 0.9 + k * 2.1)]))
        out.append(inst("HumoAuto", cx - 20, base - LLAMA_H * e - 50, 0, "Atmos"))
    return out


def es_fuego_mio(i, mios):
    return (i["name"], round(i["x"]), round(i["y"]), i["layer"]) in mios


def main(revert=False):
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    sc = next(x for x in d["layouts"] if x["name"] == "Level3")
    res = d["resources"]["resources"]
    fs = sc.get("objectsFolderStructure", {})

    # ---- limpieza (idempotente / revert) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in OBJS]
    tam = {n: Image.open(f"game/assets/City/{img}").size for n, img in OBJS.items()}
    alto = {n: h for n, (_, h) in tam.items()}
    fuego = fuegos(alto)
    mios = {(i["name"], round(i["x"]), round(i["y"]), i["layer"]) for i in fuego}
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in OBJS and not es_fuego_mio(i, mios)]
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in OBJS]
    res[:] = [r for r in res if r["name"] not in OBJS.values()]
    if not revert:
        tpl = next(o for o in sc["objects"] if o["name"] == "Escombro")
        for name, img in OBJS.items():
            res.append({"file": f"assets/City/{img}", "kind": "image", "metadata": "",
                        "name": img, "smoothed": False, "userAdded": True})
            sc["objects"].append(sprite_obj(tpl, name, img))
            if "children" in fs:
                fs["children"].append({"objectName": name})
        sc["instances"] += [inst(n, x + R.OFFSET_X, PISO_VEREDA - alto[n], 0, "Decor") for n, x in VEREDA]
        sc["instances"] += [inst(n, x + R.OFFSET_X, PISO_CALLE - alto[n], 2, "") for n, x in ASFALTO]
        e = ESCALA_CERCA
        sc["instances"] += [inst(n, x + R.OFFSET_X, PISO_CERCA - alto[n] * e, 1, "",
                                 size=(tam[n][0] * e, tam[n][1] * e)) for n, x in CERCA]
        sc["instances"] += fuego

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else f"Level3: {len(VEREDA)} en la vereda, {len(ASFALTO)} en el asfalto, "
          f"{len(CERCA)} cerca de la cámara (x{ESCALA_CERCA}), {len(FUEGOS)} prendidos fuego")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/tacho_volcado.png"), "corré gen_l3_escombros.py primero"
    main(revert=os.environ.get("REVERT") == "1")
