#!/usr/bin/env python3
"""
wire_l3_caos.py  —  banderas argentinas y caos en la calle del Nivel 3 (18/10).
Pedido del usuario: "agreguemos banderas de argentina por los monumentos y
edificios (sin ser exagerado) y autos prendidos fuego o caos en la calle".
Todo es DECORADO: sin colisión, la jugabilidad no cambia.

Requiere: gen_l3_caos.py (arte) y wire_l3_recorrido.py (fachadas, estatuas).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_l3_caos": true), en Level3:
  - BANDERAS (8 en todo el nivel): colgadas de un balcón de los edificios
    franceses y de una ventana del bar (se mecen), una en un mástil que sale de
    la pared de los deptos y otra en la terraza del PH (flamean), y una a cada
    lado de la arena, en el pedestal del prócer. Capa BG_near z 1 (delante de
    la fachada, detrás de la multitud de fondo); las de la arena en Decor z 0.
  - CAOS EN LA CALLE: en el asfalto de adelante (debajo de la vereda, capa ""
    detrás de todo lo jugable): autos quemados con llamas por las ventanillas
    y su resplandor sobre el asfalto que titila, un patrullero abandonado con
    la sirena roja/azul (y su reflejo), un colectivo cruzado, un taxi volcado,
    conos, cubiertas y escombros. z: resplandor −2; carril de atrás autos 2, llamas 3;
    carril de adelante (patrulleros al doble) llamas 0 detrás del auto 1.
Ubicación: CALLE y BANDERAS abajo (x de diseño, como l3_recorrido.py).
Re-correr después de wire_l3_recorrido.py.
Uso:  python3 scripts/wire_l3_caos.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import uuid

from PIL import Image

import l3_recorrido as R
from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
MARK = "_l3_caos"
OX = R.OFFSET_X
T = "TimeFromStart()"
# dos carriles: lo chico (escala 1) en el de ATRÁS, arriba de la línea amarilla (y ≈ 202),
# pegado al cordón (pedido del usuario 18/10); lo de ESCALA en el de adelante (PISO_CERCA).
# Está delante de la vereda (z 2/3 > 1) pero no la tapa: lo más alto (llamas) llega a y ≈ 160,
# dentro del cordón, debajo de los pies de Lio (y 150).
CALLE_PISO = 199
# objetos: nombre → (imágenes, s entre cuadros, loop)
OBJS = {
    "BanderaBalcon": ([f"bandera_balcon_{k}.png" for k in (1, 2)], 0.6, True),
    "BanderaMastil": ([f"bandera_mastil_{k}.png" for k in (1, 2, 3, 4)], 0.16, True),
    "BanderaPie": ([f"bandera_pie_{k}.png" for k in (1, 2, 3, 4)], 0.16, True),
    "AutoQuemado": (["auto_quemado.png"], 1.0, False),
    "FuegoAuto": ([f"fuego_auto_{k}.png" for k in (1, 2, 3)], 0.1, True),
    "LuzFuegoCalle": (["luz_fuego_calle.png"], 1.0, False),
    "TaxiVolcado": (["taxi_volcado.png"], 1.0, False),
    "Patrullero": ([f"patrullero_{k}.png" for k in (1, 2)], 0.35, True),
    "LuzSirena": ([f"luz_sirena_{k}.png" for k in (1, 2)], 0.35, True),
    "HumoAuto": ([f"humo_auto_{k}.png" for k in range(1, 7)], 0.14, True),
    "Colectivo": (["colectivo.png"], 1.0, False),
    "Cono": (["cono.png"], 1.0, False),
    "Neumatico": (["neumatico.png"], 1.0, False),
    "Escombro": (["escombro.png"], 1.0, False),
    "VirusFondo": ([f"virus_{k}.png" for k in range(1, 7)], 0.14, True),
}
ALTO = {"AutoQuemado": 24, "TaxiVolcado": 24, "Patrullero": 28, "Colectivo": 40,
        "Cono": 10, "Neumatico": 12, "Escombro": 8}
# más cerca de la cámara (pedido del usuario 18/10: "que el patrullero sea más grande"): al
# doble, píxel a píxel, y más abajo (las ruedas casi en el borde de la pantalla, y 246)
ESCALA = {"Patrullero": 2}
# dónde salen las llamas (FuegoAuto, 40x26): (x, y de la línea de las ventanillas) en
# píxeles del auto sin escalar; el humo (HumoAuto, 40x64) sale de arriba del fuego y solo
# en los autos de ESCALA (los cercanos a la cámara: en los chicos sería un manchón)
FUEGO_EN = {"AutoQuemado": (9, 11), "Patrullero": (10, 15)}
PISO_CERCA = 246
# la calle de adelante: (objeto, x de diseño, con fuego)
CALLE = [
    ("AutoQuemado", 410, True),                                   # calle del hospital
    ("Patrullero", 610, True), ("Cono", 760, False), ("Cono", 776, False),   # el del policía zombie
    ("Colectivo", 860, False),                                    # plaza: colectivo cruzado
    ("Neumatico", 1010, False), ("Escombro", 1030, False),
    ("TaxiVolcado", 1110, False),
    ("AutoQuemado", 1390, True),                                  # Corrientes
    ("Escombro", 1550, False), ("Cono", 1600, False),
    ("AutoQuemado", 1850, True),                                  # llegando al Obelisco
    ("AutoQuemado", 2150, True), ("Patrullero", 2420, True),      # arena
]
# banderas: (objeto, x, y del mundo de diseño (esquina de arriba), capa, z). Fachadas en
# l3_recorrido.FACHADAS: francés (top y −18) balcones en y 42/74/106 locales, ventanas en
# x 12/46/80; la bandera cuelga de la baranda (y local + 17). Bar (top y 30): ventana de
# arriba x 40. Deptos 1318 (top y 0): mástil entre ventanas. PH 1834 (top y 66): terraza.
FR_TOP, BAR_TOP, DEP_TOP, PH_TOP = R.FLOOR - 168, R.FLOOR - 120, R.FLOOR - 150, R.FLOOR - 84
BANDERAS = [
    ("BanderaBalcon", 506 + 47, FR_TOP + 74 + 17, "BG_near", 1),
    ("BanderaBalcon", 618 + 43, BAR_TOP + 16, "BG_near", 1),
    ("BanderaBalcon", 1206 + 81, FR_TOP + 42 + 17, "BG_near", 1),
    ("BanderaMastil", 1318 + 45, DEP_TOP + 52 - 26, "BG_near", 1),
    ("BanderaBalcon", 1722 + 13, FR_TOP + 74 + 17, "BG_near", 1),
    ("BanderaPie", 1834 + 56, PH_TOP + 12 - 50, "BG_near", 1),
    # arena: en el pedestal del prócer (superficie y 96), del lado de afuera
    ("BanderaPie", R.ARENA_X0 + 136, 96 - 50, "Decor", 0),     # bustos corridos (wire_jefe_jeringa.py)
    ("BanderaPie", R.ARENA_X0 + 340, 96 - 50, "Decor", 0),
]


# coronavirus gigantes en el cielo de la arena, alrededor del Obelisco (18/10: "unos
# coronavirus cerca del Obelisco que sean parte del fondo"): el sprite del virus (16x16)
# agrandado píxel a píxel, apagado (tinte + opacidad), DETRÁS del Obelisco y las estatuas
# (Decor z −1), flotan y giran despacio. No son objetos del grupo Virus: no hacen nada.
# (x, y en coordenadas de la arena 0..480, escala, fase)
# 19/10: "muy desproporcionados, si están atrás tienen que ser más chicos" → x3/x2 pasan a
# x1/x0.75, con el mismo centro (wire_l3_publico.py hace lo mismo sobre game.json)
VIRUS_FONDO = [(156, 28, 1, 0.0), (310, 32, 0.75, 1.7), (182, 84, 0.75, 3.1), (298, 100, 1, 4.4),
               (358, 6, 0.75, 2.3), (102, 62, 0.75, 5.2)]


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def foreach(obj, acts):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], MARK: True,
            "events": [{"type": "BuiltinCommonInstructions::Standard", "conditions": [], "actions": acts}]}


def sprite_obj(tpl, name, images, tbf, loop, variables=()):
    o = copy.deepcopy(tpl)
    o.update(name=name, effects=[], behaviors=[],
             variables=[{"name": k, "type": "number", "value": 0} for k in variables])
    spr = o["animations"][0]["directions"][0]["sprites"][0]
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": loop, "timeBetweenFrames": tbf,
        "sprites": [dict(spr, image=im, hasCustomCollisionMask=False, customCollisionMask=[], points=[])
                    for im in images]}]}]
    return o


def inst(name, x, y, z, layer, vars_=(), size=None):
    w, h = size or (0, 0)
    return {"angle": 0, "customSize": size is not None, "height": h, "layer": layer, "name": name,
            "persistentUuid": str(uuid.uuid4()), "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lays = {x["name"]: x for x in d["layouts"]}
    sc = lays["Level3"]
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for imgs, *_ in OBJS.values():
        for nm in imgs:
            if nm not in have:
                res.append({"file": f"assets/City/{nm}", "kind": "image", "metadata": "",
                            "name": nm, "smoothed": False, "userAdded": True})

    # ---- limpieza (idempotente) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in OBJS]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in OBJS]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in OBJS]

    # ---- objetos ----
    tpl = next(o for o in lays["Level1"]["objects"] if o["name"] == "Tacho")
    obj_vars = {"LuzFuegoCalle": ("Seed",), "VirusFondo": ("BX", "BY", "Ph")}
    objs = [sprite_obj(tpl, n, imgs, tbf, loop, variables=obj_vars.get(n, ()))
            for n, (imgs, tbf, loop) in OBJS.items()]
    sc["objects"] += objs
    if "children" in fs:
        fs["children"] += [{"objectName": o["name"]} for o in objs]

    # ---- instancias ----
    new, seed = [], 0.0
    for name, x, fuego in CALLE:
        esc = ESCALA.get(name)
        if esc:                                     # más cerca de la cámara: más grande, más abajo, adelante
            img = Image.open(f"game/assets/City/{OBJS[name][0][0]}")
            gx, gy = x + OX, PISO_CERCA - ALTO[name] * esc
            new.append(inst(name, gx, gy, 1, "", size=(img.width * esc, img.height * esc)))
        else:
            gx, gy = x + OX, CALLE_PISO - ALTO[name]
            new.append(inst(name, gx, gy, 2, ""))
        if fuego:
            seed += 1.7
            e = esc or 1
            fx, fy = FUEGO_EN[name]
            sz = (lambda w, h: (w * e, h * e) if esc else None)          # noqa: E731
            # en los cercanos el fuego va DETRÁS de la carrocería (z 0 < 1): asoma por arriba
            # del techo y la sirena sigue titilando adelante
            new.append(inst("FuegoAuto", gx + fx * e, gy + (fy - 26) * e, 0 if esc else 3, "", size=sz(40, 26)))
            new.append(inst("LuzFuegoCalle", gx + (30 - 65) * e, gy + (12 - 34) * e, -2, "",
                            vars_=[("Seed", round(seed % 6.28, 2))], size=sz(130, 56)))
            if esc:      # humo delante de todo (Atmos), sale del fuego y se desvanece a media pantalla
                new.append(inst("HumoAuto", gx + (fx + 6) * e, gy + (fy - 26 - 40) * e, 0, "Atmos",
                                size=sz(40, 64)))
        if name == "Patrullero":
            e = esc or 1
            new.append(inst("LuzSirena", gx + (29 - 48) * e, gy + (6 - 24) * e, -2, "",
                            size=(96 * e, 44 * e) if esc else None))
    for name, x, y, layer, z in BANDERAS:
        new.append(inst(name, x + OX, y, z, layer))
    for x, y, esc, fase in VIRUS_FONDO:
        new.append(inst("VirusFondo", x, y, -1, "Decor", size=(16 * esc, 16 * esc),
                        vars_=[("BX", x), ("BY", y), ("Ph", fase)]))
    sc["instances"] += new

    # ---- eventos: el resplandor de los autos titila como el de los tachos ----
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Caos en la calle (wire_l3_caos.py): el resplandor de los autos quemados titila.",
         "comment2": "", MARK: True},
        foreach("LuzFuegoCalle", [ins("Opacity", ["LuzFuegoCalle", "=",
                f"round(255 * (0.8 + 0.12 * sin({T} * 3.4 + LuzFuegoCalle.Variable(Seed)) "
                f"+ 0.08 * sin({T} * 8.1 + LuzFuegoCalle.Variable(Seed) * 2)))"])]),
        # virus del fondo: apagados (tinte frío y verdoso + opacidad), flotan y giran despacio
        {"type": "BuiltinCommonInstructions::Standard", MARK: True, "events": [],
         "conditions": [ins("BuiltinCommonInstructions::Once", [])],
         "actions": [ins("ChangeColor", ["VirusFondo", '"110;140;120"'])]},
        foreach("VirusFondo", [
            ins("SetX", ["VirusFondo", "=", f"VirusFondo.Variable(BX) + 5 * sin({T} * 0.45 + VirusFondo.Variable(Ph))"]),
            ins("SetY", ["VirusFondo", "=", f"VirusFondo.Variable(BY) + 7 * sin({T} * 0.7 + VirusFondo.Variable(Ph) * 1.3)"]),
            ins("SetAngle", ["VirusFondo", "=", f"{T} * 9 + VirusFondo.Variable(Ph) * 57"]),
            ins("Opacity", ["VirusFondo", "=", "175"])]),
    ]
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    cnt = {}
    for i in new:
        cnt[i["name"]] = cnt.get(i["name"], 0) + 1
    print("Level3: caos y banderas", cnt)


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/bandera_balcon_1.png"), "corré gen_l3_caos.py primero"
    main()
