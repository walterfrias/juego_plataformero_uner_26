#!/usr/bin/env python3
"""
wire_l3_recorrido.py  —  Nivel 3 nuevo (18/10): Lio sale del laboratorio,
cruza el centro de noche y pelea con Paciente Zero al pie del Obelisco. El
diseño (pisos, huecos, props, zombies, virus, checkpoints) está como datos
en scripts/l3_recorrido.py; acá solo se cablea.

Requiere: gen_l3_calle.py (valla, andamio_tablon, estatuas, obelisco) y el kit de
L1/L2 ya cableado (noche de L1, zombies y virus de L2).

Idea central: el recorrido va en x NEGATIVAS (−2140..0) y la arena del jefe
queda donde estaba (0..480). Así no se toca la lógica del jefe (topes 4/412,
embestida, escupitajos, cartel de vida) ni los scripts que ya trabajan sobre
la arena.

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_l3_recorrido": true), en Level3:
  - el lab queda solo en el tramo de salida: piso de lab, LabFar/LabNear y la
    pared izquierda corridos a −2180..−1788 (las luces del lab las pone
    wire_lab_luces.py y el subsuelo wire_lab_subsuelo.py, con su config).
  - calle: Vereda (copia del piso de L1, plataforma) + MuroCalle debajo (corte de
    calle: asfalto, caños, tierra); fachadas porteñas detrás (BG_near) en la calle
    del hospital, Corrientes y el comienzo de la llegada ("entre edificios, no en
    la costanera", usuario 18/10); la plaza y la arena quedan abiertas;
    huecos con escombros/hierros al fondo; puente, postes y cables de L1.
  - fondo de noche de L1 en una capa nueva BG_city, con el parallax de L1 (en
    el tramo del lab lo tapa la pared del lab, que está adelante), más dos filas
    de edificios con detalle entre la silueta y las fachadas (CiudadTrasera
    f 0.70, CiudadMedia f 0.85; gen_l3_ciudad_capas.py).
  - zombies de TODOS los niveles (personal del lab, vecinos de L1, horda de L2;
    grupo Zombies: patrulla, pisotón, choque, contagio, gas) y
    virus de L2 (grupo Virus: golpe a Lio). El vuelo con patrón lo pone
    wire_virus_patron.py y los escupitajos de los infectados wire_minivirus.py.
  - arena: el Obelisco (obelisco_cerca.png) al fondo y estatuas de la vía pública
    (monumento con columna y pedestal con busto, a cada lado) cuyas superficies
    coinciden con las 6 plataformas de la pelea (Estante, invisibles).
  - el jefe DUERME hasta que Lio entra a la arena (x ≥ ARENA_GATE): ahí se
    cierra una valla detrás (Barricada: solo imagen; el límite es un evento que
    no deja que X < 0, porque como plataforma no frenaba), la cámara
    se traba en 0..480, el checkpoint pasa a la arena y aparece su cartel de
    vida. Sus eventos de estado (0..3) llevan la condición BossActivo = 1.
Re-correr después: wire_virus_patron.py → wire_minivirus.py →
wire_lab_luces.py → wire_lab_subsuelo.py → wire_lab_ambiente.py.
NO usar `wire_levels23.py --force` sin adaptarlo: regenera L3 como arena sola.
Uso:  python3 scripts/wire_l3_recorrido.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import shutil
import uuid

import l3_recorrido as R
from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
MARK = "_l3_recorrido"
OX = R.OFFSET_X                       # x de diseño → x del juego
LEFT = R.PISOS[0][0] + OX             # borde izquierdo del nivel (−2140)
LAB_X1 = R.LAB_END + OX - 8           # donde termina la pared del lab (−1788)
ARENA_GATE = 10                       # Lio con X ≥ esto: entró a la arena
START_X, START_Y = 40 + OX, 116       # arranque (y de Lio parado en el piso)
ARENA_CHECK_X = 30                    # checkpoint una vez adentro de la arena
WALL_TOP = -25                        # paredes y valla: del borde de arriba de la cámara...
WALL_H = R.FLOOR - WALL_TOP           # ...hasta el piso (desde un tablón no se saltan)
CAM = 'CameraCenterX("")'
T = "TimeFromStart()"

# objetos copiados de L1 (mismo nombre salvo los renombrados)
FROM_L1 = ["NocheCielo", "CityFarthest", "CityFar", "CityNear", "NocheNubes", "Luna",
           "NocheIncendio", "NocheHumo", "GapDebris", "RebarSpikes", "PuenteA", "Poste", "Cable",
           "Tacho", "NocheFuego", "NocheFuegoGlow", "Farol", "NocheFarolCono", "ArbolBajo",
           "ArbolAlto", "BancoPlaza", "WallBreakR", "BarbedWire"]
RENAMED_L1 = {"Ground": "Vereda", "Embankment": "MuroCalle", "Obelisco": "ObeliscoGrande"}
# dos filas de edificios entre la silueta lejana y las fachadas (gen_l3_ciudad_capas.py):
# nombre → (textura, alto, z en BG_city). "Entre edificios": en el centro casi no se ve el cielo
# (z con lugar entre medio: wire_l3_luces.py pone resplandores y fuegos en 9, 11, 12 y 14)
CAPAS = {"CiudadTrasera": ("ciudad_trasera.png", 210, 10), "CiudadMedia": ("ciudad_media.png", 200, 13)}
# zombies: en el nivel final vuelven todos (l3_recorrido.PROPS). Los de L2 ya tienen el
# sistema del grupo Zombies; los de L1 traen contagio y escupitajo pero no las variables
# de patrulla (en L1 usaban una variable de escena por zombie): se las agrega.
ZOMBIES_L2 = ["ZombieMed", "ZombieEnf", "ZombieInv", "ZombiePol", "ZombieHin", "ZombieRep"]
ZOMBIES_L1 = {"ZombieM": "ZombieM", "ZombieF": "ZombieF", "ZombieV": "ZombieV", "ZombieD": "ZombieD",
              "ZombieN": "ZombieN", "ZombieO": "ZombieO", "ZombieJ": "ZombieEnd1"}   # nombre en L3 → objeto de L1
ZOMBIES = ZOMBIES_L2 + list(ZOMBIES_L1)
# multitud de fondo (l3_recorrido.FONDO): copias chicas y oscuras, en su propio grupo
# (ZombiesFondo, NO en Zombies: no golpean ni se pisan), en BG_near delante de las fachadas
FONDO_TIPOS = sorted({t for t, *_ in R.FONDO})
FONDO_OBJS = {t: "Fondo" + t for t in FONDO_TIPOS}           # ZombieF → FondoZombieF
# los cuadros son SILUETAS (gen_l3_siluetas.py): forma plana oscura, borde de luna y ojos
# rojos. Primero eran los sprites teñidos y competían con los jugables (usuario 18/10)
VIRUS = ["Virus1", "Virus2", "Virus3"]
FROM_L2 = ZOMBIES_L2 + VIRUS + ["InfectedGasFX"]
PIR_PAD = 14                       # = gen_l3_calle.PIR_PAD
ESTATUAS = ["EstatuaColumnaIzq", "EstatuaBustoIzq", "EstatuaColumnaDer", "EstatuaBustoDer"]
NEW = ["Barricada", "AndamioPoste", "PozoCalle"] + ESTATUAS + list(CAPAS)    # AndamioPoste: ya no se crea; queda para limpiar corridas viejas
FACHADAS = {m: f"Fachada{m.capitalize()}" for m in R.FACHADA_W}     # frances → FachadaFrances…
NEW += list(FACHADAS.values())
MINE = set(FROM_L1) | set(RENAMED_L1.values()) | set(FROM_L2) | set(NEW) | set(ZOMBIES_L1) | set(FONDO_OBJS.values())
CITY_LAYER = "BG_city"
RES = ["valla.png", "andamio_tablon.png", "obelisco_cerca.png",
       "calle_subsuelo.png", "calle_pozo.png", "ciudad_trasera.png", "ciudad_media.png"] + \
      [f"fachada_{m}.png" for m in R.FACHADA_W] + \
      [f"estatua_{k}_{lado}.png" for k in ("columna", "busto") for lado in ("izq", "der")]

# capa y z de cada objeto (los de L1 como en L1; el fondo, todo en BG_city)
PLACE = {
    "NocheCielo": (CITY_LAYER, -10), "Luna": (CITY_LAYER, -1), "CityFarthest": (CITY_LAYER, 0),
    "NocheHumo": (CITY_LAYER, 1), "NocheIncendio": (CITY_LAYER, 2), "NocheNubes": (CITY_LAYER, 4),
    "CityFar": (CITY_LAYER, 6), "CityNear": (CITY_LAYER, 8),
    **{n: (CITY_LAYER, z) for n, (_, _, z) in CAPAS.items()},
    "ObeliscoGrande": ("Decor", 0),
    "Tacho": ("Decor", 1), "NocheFuego": ("Decor", 3), "Farol": ("Decor", 1),
    "ArbolBajo": ("Decor", 1), "ArbolAlto": ("Decor", 1),
    "NocheFuegoGlow": ("Atmos", 1), "NocheFarolCono": ("Atmos", 0),
    "MuroCalle": ("", -3), "RebarSpikes": ("", -1), "GapDebris": ("", 0), "PuenteA": ("", 0),
    "Poste": ("", 0), "Cable": ("", 0), "BancoPlaza": ("", 0), "WallBreakR": ("", 0),
    "BarbedWire": ("", 0), "Vereda": ("", 1), "Barricada": ("", 2), "PozoCalle": ("", -4),
    # fachadas: delante de la ciudad del fondo, detrás de faroles/tachos/zombies
    **{n: ("BG_near", 0) for n in FACHADAS.values()},
    **{n: ("Decor", 1) for n in ESTATUAS},
}
# parallax (como L1): f = cuánto se mueve respecto de la cámara
PARALLAX = {"NocheCielo": 1.0, "CityFarthest": 0.12, "CityFar": 0.30, "CityNear": 0.55,
            "CiudadTrasera": 0.70, "CiudadMedia": 0.85}
FIRE_BASES = [LEFT + 300 * k for k in range(9)]          # incendios lejanos a lo largo del nivel


def ins(value, params, inverted=False):
    d = {"type": {"value": value}, "parameters": params}
    if inverted:
        d["type"]["inverted"] = True
    return d


def std(conds, acts, events=(), mark=True):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}
    if events:
        e["events"] = list(events)
    if mark:
        e[MARK] = True
    return e


def foreach(obj, acts, conds=()):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], "events": [std(list(conds), acts, mark=False)], MARK: True}


def inst(name, x, y, w=None, h=None, vars_=(), z=None, layer=None):
    ly, zz = PLACE.get(name, ("", 2))
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": ly if layer is None else layer,
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": zz if z is None else z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def has_cond(e, value, params):
    return any(c["type"]["value"] == value and c["parameters"][:len(params)] == params
               for c in e.get("conditions", []))


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lays = {x["name"]: x for x in d["layouts"]}
    l1, l2, sc = lays["Level1"], lays["Level2"], lays["Level3"]
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm in RES:
        if nm not in have:
            res.append({"file": f"assets/City/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})

    # ---------- limpieza (idempotente) ----------
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    sc["layers"] = [ly for ly in sc["layers"] if ly["name"] != CITY_LAYER]
    sc["objectsGroups"] = [g for g in sc.get("objectsGroups", []) if g["name"] not in ("Zombies", "Virus", "ZombiesFondo")]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]
    for e in sc["events"]:                                   # condición BossActivo de una corrida anterior
        e["conditions"] = [c for c in e.get("conditions", [])
                           if not (c["type"]["value"] == "VarScene" and c["parameters"][0] == "BossActivo")]
    if not any(v["name"] == "BossActivo" for v in sc["variables"]):
        sc["variables"].append({"name": "BossActivo", "type": "number", "value": 0})

    # ---------- objetos ----------
    o1 = {o["name"]: o for o in l1["objects"]}
    o2 = {o["name"]: o for o in l2["objects"]}
    new_objs = [copy.deepcopy(o1[n]) for n in FROM_L1]
    for src, dst in RENAMED_L1.items():
        o = copy.deepcopy(o1[src])
        o["name"] = dst
        new_objs.append(o)
    # el Obelisco de la arena: arte propio (gen_l3_calle.py), sin el Adjustment que
    # en L1 lo oscurece por estar lejos
    ob = next(o for o in new_objs if o["name"] == "ObeliscoGrande")
    ob["effects"] = []
    ob["animations"][0]["directions"][0]["sprites"] = [dict(
        ob["animations"][0]["directions"][0]["sprites"][0], image="obelisco_cerca.png")]
    new_objs += [copy.deepcopy(o2[n]) for n in FROM_L2]
    for name, src in ZOMBIES_L1.items():
        z = copy.deepcopy(o1[src])
        z["name"] = name
        have_v = {v["name"] for v in z.get("variables", [])}
        z["variables"] = z.get("variables", []) + [
            {"name": k, "type": "number", "value": 0} for k in ("Dir", "MinX", "MaxX", "Speed") if k not in have_v]
        new_objs.append(z)
    # la valla es solo imagen: el límite de la arena lo ponen eventos (ver CLAMP abajo).
    # Como plataforma no frenaba: tocando el piso por el costado, el motor la tomaba
    # como piso y dejaba de tratarla como obstáculo (y a la pared derecha de 350 px
    # la "subía": Lio aparecía arriba de la pared). Medido 18/10.
    valla = copy.deepcopy(o1["Ground"])
    valla.update(name="Barricada", texture="valla.png", effects=[], variables=[], behaviors=[])
    new_objs.append(valla)
    # debajo de la vereda: corte de calle (asfalto, caños, tierra) en vez del muro de la costanera
    muro = next(o for o in new_objs if o["name"] == "MuroCalle")
    muro.update(texture="calle_subsuelo.png", effects=[])
    for name, (tex, _, _) in CAPAS.items():        # filas de edificios: copias de CityNear sin su Adjustment
        c = copy.deepcopy(o1["CityNear"])
        c.update(name=name, texture=tex, effects=[])
        new_objs.append(c)
    pozo = copy.deepcopy(muro)                     # interior de los pozos (si no, se ve el cielo)
    pozo.update(name="PozoCalle", texture="calle_pozo.png")
    new_objs.append(pozo)
    # fachadas porteñas (gen_l3_fachadas.py): un Sprite por modelo
    for m, name in FACHADAS.items():
        f = copy.deepcopy(o1["Tacho"])
        f.update(name=name, effects=[], behaviors=[], variables=[])
        spr = f["animations"][0]["directions"][0]["sprites"][0]
        f["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
            "looping": False, "timeBetweenFrames": 1,
            "sprites": [dict(spr, image=f"fachada_{m}.png", hasCustomCollisionMask=False,
                             customCollisionMask=[], points=[])]}]}]
        new_objs.append(f)
    # estatuas de la arena (gen_l3_calle.py): un Sprite por monumento
    for name in ESTATUAS:
        k = "columna" if "Columna" in name else "busto"
        lado = "izq" if name.endswith("Izq") else "der"
        f = copy.deepcopy(o1["Tacho"])
        f.update(name=name, effects=[], behaviors=[], variables=[])
        spr = f["animations"][0]["directions"][0]["sprites"][0]
        f["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
            "looping": False, "timeBetweenFrames": 1,
            "sprites": [dict(spr, image=f"estatua_{k}_{lado}.png", hasCustomCollisionMask=False,
                             customCollisionMask=[], points=[])]}]}]
        new_objs.append(f)
    sc["objects"] += new_objs
    if "children" in fs:
        fs["children"] += [{"objectName": o["name"]} for o in new_objs]
    res_file = {r["name"]: r["file"] for r in res}
    for t, name in FONDO_OBJS.items():                       # multitud de fondo (siluetas)
        src = next(o for o in new_objs if o["name"] == t)
        z = copy.deepcopy(src)
        z.update(name=name, effects=[], behaviors=[],
                 variables=[{"name": k, "type": "number", "value": 0} for k in ("Dir", "MinX", "MaxX", "Speed")])
        for anim in z["animations"]:
            for spr in anim["directions"][0]["sprites"]:
                sil = "silueta_" + os.path.basename(res_file[spr["image"]])
                if sil not in have:
                    res.append({"file": f"assets/Siluetas/{sil}", "kind": "image", "metadata": "",
                                "name": sil, "smoothed": False, "userAdded": True})
                    have.add(sil)
                spr["image"] = sil
        new_objs.append(z)
    sc["objects"] += new_objs[-len(FONDO_OBJS):]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in FONDO_OBJS.values()]
    sc["objectsGroups"] += [
        {"name": "ZombiesFondo", "objects": [{"name": n} for n in FONDO_OBJS.values()]},
        {"name": "Zombies", "objects": [{"name": n} for n in ZOMBIES]},
        {"name": "Virus", "objects": [{"name": n} for n in VIRUS]},
    ]
    # estantes del lab → tablones (mismo tamaño y colisión; invisibles, los "pisa" una estatua)
    next(o for o in sc["objects"] if o["name"] == "Estante")["texture"] = "andamio_tablon.png"

    # capa del fondo de la ciudad, detrás de todo
    base_layer = copy.deepcopy(next(ly for ly in sc["layers"] if ly["name"] == "BG_far"))
    base_layer.update(name=CITY_LAYER, effects=[])
    sc["layers"].insert(0, base_layer)

    # ---------- lo que ya estaba: el lab va al tramo de salida ----------
    grounds = [i for i in sc["instances"] if i["name"] == "Ground"]
    floor = next(i for i in grounds if round(i["height"]) == 96)
    lab_x0, lab_x1 = R.PISOS[0][0] + OX, R.PISOS[0][1] + OX
    floor.update(x=lab_x0, width=lab_x1 - lab_x0)
    # paredes del nivel: eran Ground de 350 px de alto (y −200..150) y NO frenaban: al
    # tocarlas el motor subía a Lio arriba de la pared (y −225) y lo dejaba caer del
    # otro lado (medido 18/10). Con y −25..150 (borde de arriba de la cámara → piso,
    # como la valla) frenan. La de la izquierda va al borde del nivel.
    walls = sorted((i for i in grounds if round(i["height"]) in (350, WALL_H)), key=lambda i: i["x"])
    walls[0]["x"] = LEFT - 40
    for w in walls:
        w.update(y=WALL_TOP, height=WALL_H)
    for name in ("LabFar", "LabNear"):
        i = next(i for i in sc["instances"] if i["name"] == name)
        i.update(x=LEFT - 100, width=LAB_X1 - (LEFT - 100))
    player = next(i for i in sc["instances"] if i["name"] == "Player")
    player.update(x=START_X, y=124)

    # ---------- instancias nuevas ----------
    new = []
    for x0, x1, tipo in R.PISOS[1:]:                         # calle (el primero es el lab)
        new.append(inst("Vereda", x0 + OX, R.FLOOR, x1 - x0, 16))
        new.append(inst("MuroCalle", x0 + OX, R.FLOOR + 16, x1 - x0, 80))
    for x0, x1, tipo in R.HUECOS:
        new.append(inst("PozoCalle", x0 + OX, R.FLOOR, x1 - x0, 96))
        if tipo == "hierros":
            new.append(inst("RebarSpikes", x0 + OX, 200, x1 - x0, 46))
        else:
            new.append(inst("GapDebris", (x0 + x1) / 2 - 24 + OX, 202))
    vi = iter(VIRUS)
    for name, x, y, ex in R.PROPS:
        gx = x + OX
        if name.startswith("Zombie"):
            new.append(inst(name, gx, y, vars_=[
                ("Dir", ex.get("Dir", 1)), ("MinX", ex["MinX"] + OX), ("MaxX", ex["MaxX"] + OX),
                ("Speed", ex.get("Speed", 22)), ("Infected", 0)]))
        elif name == "Virus":
            new.append(inst(next(vi), gx, y, z=6))          # el patrón lo pone wire_virus_patron.py
        elif name in ("Cable", "BarbedWire"):
            new.append(inst(name, gx, y, ex["w"], 7 if name == "Cable" else 14))
        elif name == "PacienteZero":
            continue                                        # el jefe ya está en la arena
        else:
            new.append(inst(name, gx, y))
            if name == "Farol":
                new.append(inst("NocheFarolCono", gx - 22, y + 4))
            if name == "Tacho" and ex.get("fuego"):
                new.append(inst("NocheFuego", gx + 2, y - 11))
                new.append(inst("NocheFuegoGlow", gx - 52, y - 40, vars_=[("Seed", round(gx % 6.28, 2))]))
    # multitud de fondo: más chicos, con los pies 2 px DEBAJO del borde de la vereda (que
    # está en una capa de adelante y les tapa la punta: parados detrás del cordón). Con
    # los pies 6 px más arriba parecía que flotaban (usuario 18/10)
    fw, fh = round(32 * R.FONDO_ESCALA), round(34 * R.FONDO_ESCALA)
    for k, (t, x, mn, mx, vel) in enumerate(R.FONDO):
        new.append(inst(FONDO_OBJS[t], x + OX, R.FLOOR + 2 - fh, fw, fh, layer="BG_near", z=2, vars_=[
            ("Dir", 1 if k % 2 else -1), ("MinX", mn + OX), ("MaxX", mx + OX), ("Speed", vel)]))
    # fondo de la ciudad (de todo el ancho; el lab lo tapa en el tramo de salida)
    w_all = 480 + 300 - (LEFT - 300)
    l1i = {i["name"]: i for i in l1["instances"]}
    for n in ("NocheCielo", "CityFarthest", "CityFar", "CityNear"):
        new.append(inst(n, LEFT - 300, l1i[n]["y"] + R.DY_L1, w_all, l1i[n]["height"]))
    new.append(inst("NocheNubes", LEFT - 300, -60, w_all, 80))
    for name, (_, alto, _) in CAPAS.items():       # apoyadas en el piso (las tapan vereda y fachadas)
        new.append(inst(name, LEFT - 300, R.FLOOR - alto, w_all, alto))
    new.append(inst("Luna", 0, -24))
    for k, b in enumerate(FIRE_BASES):
        new.append(inst("NocheIncendio", b, l1i["NocheIncendio"]["y"] + R.DY_L1,
                        vars_=[("Base", b), ("Seed", round(1.3 + k * 1.7, 2))]))
        new.append(inst("NocheHumo", b + 38, l1i["NocheHumo"]["y"] + R.DY_L1, vars_=[("Base", b + 38)]))
    # fachadas (la fila de abajo de cada imagen apoya en el piso)
    alto = {"frances": 168, "deptos": 150, "ph": 84, "bar": 120}
    for m, x in R.FACHADAS:
        new.append(inst(FACHADAS[m], x + OX, R.FLOOR - alto[m]))
    # arena: el Obelisco (48x176, tamaño nativo, apoyado en el piso)
    new.append(inst("ObeliscoGrande", R.OBELISCO_ARENA + OX - 24, R.FLOOR - 176))
    # estatuas de la vía pública (pedido del usuario 18/10; antes eran andamios): sus
    # superficies coinciden EXACTO con las 6 plataformas de la pelea (Estante, que
    # quedan invisibles): columna = pedestal (y 122) + capitel (y 70); busto = y 96
    est = [i for i in sc["instances"] if i["name"] == "Estante"]
    for lado, sel in (("Izq", lambda e: e["x"] < 240), ("Der", lambda e: e["x"] >= 240)):
        grupo = [e for e in est if sel(e)]
        base = next(e for e in grupo if round(e["y"]) == 122)
        alta = next(e for e in grupo if round(e["y"]) == 70)
        busto = next(e for e in grupo if round(e["y"]) == 96)
        # la columna pasó a ser una pirámide monolito (18/10): la imagen tiene PIR_PAD px de
        # faldón a cada lado (gen_l3_calle.py)
        new.append(inst(f"EstatuaColumna{lado}", min(base["x"], alta["x"]) - PIR_PAD, 20))
        new.append(inst(f"EstatuaBusto{lado}", busto["x"], 70))
    # barricada a la entrada de la arena (se cierra al entrar)
    new.append(inst("Barricada", -16, WALL_TOP, 16, WALL_H))
    sc["instances"] += new

    # ---------- eventos ----------
    evs = sc["events"]
    # arranque: checkpoint inicial en el comienzo del recorrido
    for e in evs:
        if has_cond(e, "BuiltinCommonInstructions::Once", []):
            for a in e.get("actions", []):
                if a["type"]["value"] == "ModVarScene" and a["parameters"][0] == "CheckX":
                    a["parameters"][2] = str(START_X)
    # cámara: la de la arena sola (0..480) pasa a depender de BossActivo
    cam_evs = [e for e in evs if any(a["type"]["value"] == "FixCamera" for a in e.get("actions", []))]
    for e in cam_evs:
        evs.remove(e)
    cam = lambda x0: ins("FixCamera", ["", "Player", str(x0), "-25", "480", "245", "yes", "", ""])
    evs.insert(1, std([ins("VarScene", ["BossActivo", "=", "1"])], [cam(0)]))
    evs.insert(1, std([ins("VarScene", ["BossActivo", "=", "0"])], [cam(LEFT)]))
    # el jefe duerme: condición BossActivo = 1 en su máquina de estados (0..3).
    # Los pisotones sobre él (CollisionNP) no hace falta: con Lio afuera no chocan.
    n_gated = 0
    for e in evs:
        cs = e.get("conditions", [])
        if (e.get("type") == "BuiltinCommonInstructions::Standard"
                and any(c["type"]["value"] == "VarScene" and c["parameters"][0] == "BossState" for c in cs)
                and not any(c["type"]["value"] == "CollisionNP" for c in cs)):
            e["conditions"].insert(0, ins("VarScene", ["BossActivo", "=", "1"]))
            n_gated += 1
    assert n_gated == 4, f"esperaba 4 eventos de estado del jefe, hay {n_gated}"

    # sistemas copiados de L2: zombies (pisotón, choque, contagio, gas, patrulla) y golpe de virus
    def from_l2(e):
        s = json.dumps(e)
        return (not any(k.startswith("_") for k in e) and e.get("type") != "BuiltinCommonInstructions::Group"
                and ('"Zombies"' in s or ('"Virus"' in s and "CollisionNP" in s and '"Player"' in s)))
    copied = [dict(copy.deepcopy(e), **{MARK: True}) for e in l2["events"] if from_l2(e)]
    # 4 pisotón/choque + 4 contagio/gas + 2 patrulla + 2 golpe de virus
    assert len(copied) == 12, f"esperaba 12 eventos de zombies/virus en L2, hay {len(copied)}"

    cp = sorted(c + OX for c in R.CHECKPOINTS)
    checkpoints = [std([ins("PosX", ["Player", ">", str(x)]), ins("PosY", ["Player", "<", "140"]),
                        ins("VarScene", ["CheckX", "<", str(x)])],
                       [ins("ModVarScene", ["CheckX", "=", str(x)])]) for x in cp]
    arena = std([ins("PosX", ["Player", ">=", str(ARENA_GATE)]), ins("VarScene", ["BossActivo", "=", "0"]),
                 ins("VarScene", ["Over", "=", "0"])], [
        ins("ModVarScene", ["BossActivo", "=", "1"]),
        ins("ModVarScene", ["BossState", "=", "0"]),
        ins("ResetObjectTimer", ["PacienteZero", '"BossT"']),
        ins("ResetObjectTimer", ["PacienteZero", '"BossHurt"']),
        ins("ModVarScene", ["CheckX", "=", str(ARENA_CHECK_X)]),
        ins("Show", ["Barricada", ""]),
        ins("Show", ["BossHPText", ""]),
    ])
    parallax = [ins("TiledSpriteObject::XOffset", [n, "=", f"round(-{1 - f:.2f} * {CAM})"])
                for n, f in PARALLAX.items() if n != "NocheCielo"]
    parallax += [ins("TiledSpriteObject::XOffset", ["NocheCielo", "=", f"round(-{CAM})"]),
                 ins("TiledSpriteObject::XOffset", ["NocheNubes", "=", f"round(-0.98 * {CAM} + {T} * 3.0)"]),
                 # luna: en pantalla x = 100 + 240 − 0.03·cam → entre 333 y 397 en todo el nivel
                 ins("SetX", ["Luna", "=", f"round(100 + 0.97 * {CAM})"])]
    flick = lambda o, base, a, b: (f"round(255 * ({base} + {a} * sin({T} * 3.1 + {o}.Variable(Seed)) "
                                   f"+ {b} * sin({T} * 7.3 + {o}.Variable(Seed) * 2)))")
    evs += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Recorrido del Nivel 3 (wire_l3_recorrido.py, diseño en l3_recorrido.py): salida del lab "
                    "→ centro → arena del Obelisco. El jefe duerme hasta que Lio entra (BossActivo).",
         "comment2": "", MARK: True},
        std([ins("BuiltinCommonInstructions::Once", [])], [
            ins("Hide", ["Barricada"]), ins("Hide", ["Estante"]),   # los tablones: los "pisa" la estatua
            ins("ModVarScene", ["CheckY", "=", str(START_Y)])]),
        # límites por evento (determinista): borde izquierdo del nivel, valla de la arena
        # una vez adentro y pared derecha (Lio mide 18 de ancho)
        std([ins("PosX", ["Player", "<", str(LEFT)])], [ins("SetX", ["Player", "=", str(LEFT)])]),
        std([ins("PosX", ["Player", "<", "0"]), ins("VarScene", ["BossActivo", "=", "1"])],
            [ins("SetX", ["Player", "=", "0"])]),
        std([ins("PosX", ["Player", ">", str(480 - 18)])], [ins("SetX", ["Player", "=", str(480 - 18)])]),
        *checkpoints, arena, *copied,
        std([], parallax),
        foreach("NocheIncendio", [
            ins("SetX", ["NocheIncendio", "=", f"round(NocheIncendio.Variable(Base) + 0.80 * {CAM})"]),
            ins("Opacity", ["NocheIncendio", "=", flick("NocheIncendio", 0.78, 0.12, 0.1)])]),
        foreach("NocheHumo", [ins("SetX", ["NocheHumo", "=", f"round(NocheHumo.Variable(Base) + 0.80 * {CAM})"])]),
        foreach("NocheFuegoGlow", [ins("Opacity", ["NocheFuegoGlow", "=", flick("NocheFuegoGlow", 0.8, 0.12, 0.08)])]),
        # multitud de fondo: tinte oscuro y frío al empezar, y su propia patrulla
        std([ins("BuiltinCommonInstructions::Once", [])], [ins("SetAnimationName", ["ZombiesFondo", '"Walk"'])]),
        {"type": "BuiltinCommonInstructions::ForEach", "object": "ZombiesFondo", "objectsToPick": "ZombiesFondo",
         "conditions": [], "actions": [], MARK: True, "events": [std([], [
             ins("SetX", ["ZombiesFondo", "+", "ZombiesFondo.Variable(Dir) * ZombiesFondo.Variable(Speed) * TimeDelta()"])], [
             std([ins("PosX", ["ZombiesFondo", ">", "ZombiesFondo.Variable(MaxX)"]),
                  ins("NumberObjectVariable", ["ZombiesFondo", "Dir", "=", "1"])],
                 [ins("ModVarObjet", ["ZombiesFondo", "Dir", "=", "-1"]), ins("FlipX", ["ZombiesFondo", "yes"])], mark=False),
             std([ins("PosX", ["ZombiesFondo", "<", "ZombiesFondo.Variable(MinX)"]),
                  ins("NumberObjectVariable", ["ZombiesFondo", "Dir", "=", "-1"])],
                 [ins("ModVarObjet", ["ZombiesFondo", "Dir", "=", "1"]), ins("FlipX", ["ZombiesFondo", "no"])], mark=False),
         ], mark=False)]},
        # al final: mientras el jefe duerme, su cartel no se ve (la pausa lo vuelve a mostrar)
        std([ins("VarScene", ["BossActivo", "=", "0"])], [ins("Hide", ["BossHPText"])]),
    ]
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    counts = {}
    for i in new:
        counts[i["name"]] = counts.get(i["name"], 0) + 1
    print(f"Level3: nivel {LEFT}..480 | objetos +{len(new_objs)} | instancias +{len(new)} | "
          f"eventos de L2 copiados {len(copied)} | checkpoints {cp} | jefe: {n_gated} eventos dormidos")
    print("  ", {k: v for k, v in counts.items() if k.startswith(("Zombie", "Virus", "Vereda", "Puente", "Poste"))})


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/valla.png"), "corré gen_l3_calle.py primero"
    main()
