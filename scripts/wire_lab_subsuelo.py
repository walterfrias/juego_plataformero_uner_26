#!/usr/bin/env python3
"""
wire_lab_subsuelo.py  —  Nivel 2 y arena del Nivel 3: el "bloque negro" de
debajo del piso del laboratorio pasa a ser el corte del edificio (pedido del
usuario 18/10: "laboratorios con coronavirus encerrados para que no sea un
bloque negro nada más").

Requiere: gen_lab_subsuelo.py (lab_subsuelo.png, contencion[_rota]_0..3.png,
contencion_vacia.png, contencion_glow.png) y wire_minivirus.py (objeto
MiniVirus en L2: el virus que se escapa ES un minivirus).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_lab_subsuelo": true), en Level2 y Level3:
  - LabSubsuelo (TiledSprite): una instancia por tramo de piso (Ground de
    96 px de alto), del mismo ancho, sobre las filas 16..95 de lab_floor.png
    (losa, ducto, cañerías, sala de contención). Los huecos quedan como
    estaban (vidrios rotos al fondo).
  - Contencion / ContencionRota (Sprite, 4 cuadros: el virus flota y gira
    dentro del tubo): repartidos al azar (semilla fija) sobre el piso de
    rejilla de la sala, ~1 de cada 4 roto. Un tubo a menos de PIT_SAFE px
    del borde de un hueco nunca es roto: el virus saldría con Lio saltando
    o sobre la camilla, y el knockback lo tiraría al hueco.
  - ContencionGlow: halo verde detrás de cada tubo, late despacio (los rotos
    titilan más rápido).
  - Solo en Level2 (BREAK_SCENES), los rotos ESTALLAN (18/10): cuando Lio
    pasa por encima o por delante (|dx| < TRIGGER = 20 px; con 80 estallaba
    con Lio llegando y en el corredor el virus le salía encima: golpe
    seguro), el tubo tiembla CRACK s con un
    crujido grave (aviso) y después estalla: animación "Vacia", chispazo
    agudo, se borra su halo y sale un MiniVirus desde adentro, apuntado a
    Lio (desde ahí lo maneja wire_minivirus.py: persigue, brilla, 8 s de
    vida, −1 vida al tocar). Cada tubo estalla una sola vez (var Estado
    0 sano / 1 temblando / 2 vacío). En L3 quedan de decorado: la arena del
    jefe ya tiene sus escupitajos.
  - DUCTO JUGABLE (solo Level2, tramo de piso 928..1350, 18/10): una ruta
    por debajo de las 3 patrullas de ese tramo.
      entrada: agujero de 28 px en el piso (966..994) con bordes de peligro
               (EscotillaBorde). Caer ahí NO mata (muerte = Y > 260; el
               corredor está en y 192) y se puede saltar.
      corredor: 966..1332 a la altura de la sala de contención. Piso
               invisible SubsueloPiso (plataforma) y techo = una losa de
               Ground de 16 px (el piso de arriba se sigue caminando). Los
               tubos de ese tramo van detrás de Lio (z < 1); el roto de
               x≈1132 estalla a su altura (hay que correr: 95 vs 55 px/s).
               El antídoto del estante alto (x 1195) baja al corredor: siguen
               siendo 4 (el total está fijo en el HUD y en el bonus).
      salida:  ducto de aire (AirFlow + Vent, los de siempre: 140 px/s hacia
               arriba) en 1236..1268, por un agujero en la losa: quedan 82
               px de piso hasta el hueco de 1350 (en 1300 la salida tiraba a
               Lio al pozo). Caer en él desde arriba lo vuelve a subir.
    Las paredes del corredor son Ground macizo (928..966 y 1268..1350) SIN
    subsuelo pintado, así se leen como pared. Ningún zombie cruza los
    agujeros (no tienen gravedad: flotarían): ZombieInv MinX 960→1000;
    ZombieEnf arranca en 1290 y patrulla 1272..1330, a la derecha de la
    salida (se lo puede pisar al bajar flotando). Las posiciones de los tubos se calculan con el
    piso ORIGINAL (no se corren por el ducto); el script restaura el Ground
    original antes de volver a aplicarlo (idempotente).
  Todo en la capa de juego (""), z 2..4: el piso (Ground) está en z 1 y
  nada jugable pasa por debajo del canto del piso. Sin comportamientos (no
  colisionan; wire_bordes_plataforma.py no los toma).
Re-correr después de `wire_levels23.py --force` (regenera L2/L3).
Uso:  python3 scripts/wire_lab_subsuelo.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import random
import shutil
import uuid

GAME = "game/game.json"
MARK = "_lab_subsuelo"
SCENES = ("Level2", "Level3")
SUB, TUBE, ROTA, GLOW = "LabSubsuelo", "Contencion", "ContencionRota", "ContencionGlow"
DPISO, DBORDE = "SubsueloPiso", "EscotillaBorde"
MINE = {SUB, TUBE, ROTA, GLOW, DPISO, DBORDE}
SLAB = 16            # filas de baldosa de lab_floor.png; el subsuelo va debajo
SUB_H = 80
GRATE = 66           # fila del piso de rejilla dentro de lab_subsuelo.png
TUBE_W, TUBE_H = 24, 40
GAP_MIN, GAP_MAX = 64, 150   # separación entre tubos
MARGIN = 18                  # distancia a los bordes de cada tramo
P_ROTA = 0.25
PIT_SAFE = 100               # px del centro del tubo al borde de un hueco
BREAK_SCENES = ("Level2",)
TRIGGER, CRACK = 20, 0.6     # px (|dx| Lio-tubo: Lio pasa por encima/delante) y s de temblor
T = "TimeFromStart()"
PCX = "(Player.X() + Player.Width() / 2)"
# ducto jugable de L2 (ver docstring)
DUCTO_SCENE = "Level2"
D_X0, D_X1, D_Y, D_H = 928, 1350, 110, 96      # tramo de piso original
D_IN = (966, 994)                              # boca (entrada)
D_OUT = (1236, 1268)                           # ducto de aire (salida); 82 px de piso hasta el hueco de 1350
D_FLOOR = D_Y + SLAB + GRATE                   # 192: piso de rejilla del corredor
D_AIR_TOP = 90                                 # Lio flota con los pies ~20 px sobre el piso
D_ANTI = (1180, D_FLOOR - 22)                  # antídoto (16x16 + margen)
# patrullas que cruzaban los agujeros: nombre -> (x inicial, MinX, MaxX); None = no cambia
# (originales: ZombieInv 1020, 960..1150; ZombieEnf 1250, 1180..1330)
D_PATROL = {"ZombieInv": (None, 1000, 1150), "ZombieEnf": (1290, 1272, 1330)}   # valores absolutos: idempotente
D_NS = uuid.UUID("5b1d0c70-18a0-4c2d-9b1e-000000000000")
PCY = "(Player.Y() + Player.Height() / 2)"
RES = (["lab_subsuelo.png", "contencion_glow.png", "contencion_vacia.png", "escotilla_borde.png"]
       + [f"contencion_{i}.png" for i in range(4)]
       + [f"contencion_rota_{i}.png" for i in range(4)])


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts, events=()):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
         "actions": acts, MARK: True}
    if events:
        e["events"] = list(events)
    return e


def foreach(obj, acts, conds=(), subs=()):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    inner = {"type": "BuiltinCommonInstructions::Standard", "conditions": list(conds), "actions": acts}
    if subs:
        inner["events"] = list(subs)
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], "events": [inner], MARK: True}


def sound(pitch, vol):
    return ins("PlaySound", ["", "sfx_chispazo.wav", "no", f"GlobalVariable(SfxVolume) * {vol}", str(pitch)])


def break_events():
    """Tubos rotos que estallan y sueltan un minivirus (solo BREAK_SCENES)."""
    cx = f"({ROTA}.Variable(BaseX) + {TUBE_W // 2})"
    cy = f"({ROTA}.Y() + {TUBE_H // 2})"
    playing = [ins("VarScene", ["Over", "=", "0"]), ins("VarScene", ["Won", "=", "0"])]
    spawn = std([], [
        ins("Create", ["", "MiniVirus", f"{cx} - 8", f"{cy} - 8", ""]),
        ins("ChangePlan", ["MiniVirus", "=", "900"]),
        ins("ModVarObjet", ["MiniVirus", "Ang", "=", f"atan2({PCY} - {cy}, {PCX} - {cx})"]),
        ins("ModVarObjet", ["MiniVirus", "Next", "=", "1"]),      # primer tramo recto hacia Lio
        ins("ResetObjectTimer", ["MiniVirus", '"Life"']),
        ins("ResetObjectTimer", ["MiniVirus", '"Retarget"']),
    ])
    # el halo de ESTE tubo: está 12 px a su izquierda (ver wire_scene)
    glow_off = std([ins("PosX", [GLOW, ">=", f"{ROTA}.Variable(BaseX) - 13"]),
                    ins("PosX", [GLOW, "<=", f"{ROTA}.Variable(BaseX) - 11"])],
                   [ins("Delete", [GLOW, ""])])
    for e in (spawn, glow_off):
        del e[MARK]
    burst = std([ins("ObjectTimer", [ROTA, '"Crack"', str(CRACK)])], [
        ins("ModVarObjet", [ROTA, "Estado", "=", "2"]),
        ins("SetX", [ROTA, "=", f"{ROTA}.Variable(BaseX)"]),
        ins("SetAnimationName", [ROTA, '"Vacia"']),
        sound(1.8, 0.9),
    ], [spawn, glow_off])
    del burst[MARK]
    return [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": f"Tubos rotos (wire_lab_subsuelo.py): Lio a menos de {TRIGGER} px -> tiembla "
                    f"{CRACK} s con crujido -> estalla (Vacia), se apaga su halo y sale un MiniVirus "
                    "apuntado a Lio. Una vez por tubo (Estado 0/1/2).",
         "comment2": "", MARK: True},
        # 0 -> 1: Lio se acerca, empieza a temblar
        foreach(ROTA, [
            ins("ModVarObjet", [ROTA, "Estado", "=", "1"]),
            ins("ModVarObjet", [ROTA, "BaseX", "=", f"{ROTA}.X()"]),
            ins("ResetObjectTimer", [ROTA, '"Crack"']),
            sound(0.45, 0.6),
        ], conds=[ins("NumberObjectVariable", [ROTA, "Estado", "=", "0"]),
                  ins("BuiltinCommonInstructions::CompareNumbers",
                      [f"abs({PCX} - ({ROTA}.X() + {TUBE_W // 2}))", "<", str(TRIGGER)])] + playing),
        # 1: temblor (1 px a cada lado) y, a los CRACK s, estalla
        foreach(ROTA, [
            ins("SetX", [ROTA, "=", f"{ROTA}.Variable(BaseX) + round(sin({T} * 70))"]),
        ], conds=[ins("NumberObjectVariable", [ROTA, "Estado", "=", "1"])], subs=[burst]),
    ]


def sprite_obj(base, name, frames, speed, variables=()):
    o = copy.deepcopy(base)
    o["name"] = name
    o["behaviors"] = []
    o["effects"] = []
    o["variables"] = [{"name": k, "type": "number", "value": v} for k, v in variables]
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": len(frames) > 1, "timeBetweenFrames": speed, "sprites": [{
            "hasCustomCollisionMask": False, "image": f, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []} for f in frames]}]}]
    return o


def rota_obj(base):
    """Tubo roto: anim Idle (virus adentro) + Vacia (después de estallar)."""
    o = sprite_obj(base, ROTA, [f"contencion_rota_{i}.png" for i in range(4)], 0.22,
                   [("Estado", 0), ("BaseX", 0)])
    o["animations"].append(sprite_obj(base, "_", ["contencion_vacia.png"], 1)["animations"][0])
    o["animations"][1]["name"] = "Vacia"
    return o


def inst(name, x, y, z, w=None, h=None, vars_=()):
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": "",
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def duid(tag):
    """uuid fijo para las instancias del ducto: así se reconocen al re-correr."""
    return str(uuid.uuid5(D_NS, tag))


D_TAGS = ["orig", "wall_l", "slab", "wall_r", "air", "vent", "piso", "borde_l", "borde_r"]


def restore_ducto(sc):
    """Deja el tramo como estaba antes del ducto (Ground macizo 928..1350)."""
    mine = {duid(t) for t in D_TAGS}
    sc["instances"] = [i for i in sc["instances"] if i.get("persistentUuid") not in mine]
    if not any(i["name"] == "Ground" and round(i["x"]) == D_X0 and round(i["height"]) == D_H
               for i in sc["instances"]):
        g = copy.deepcopy(next(i for i in sc["instances"] if i["name"] == "Ground"))
        g.update(x=D_X0, y=D_Y, width=D_X1 - D_X0, height=D_H, persistentUuid=duid("orig"))
        sc["instances"].append(g)


def apply_ducto(sc):
    inst_ = sc["instances"]
    orig = next(i for i in inst_ if i["name"] == "Ground" and round(i["x"]) == D_X0
                and round(i["height"]) == D_H)
    inst_.remove(orig)

    def piece(tag, x0, x1, h):
        g = copy.deepcopy(orig)
        g.update(x=x0, y=D_Y, width=x1 - x0, height=h, persistentUuid=duid(tag))
        return g
    inst_ += [piece("wall_l", D_X0, D_IN[0], D_H),       # pared izquierda (maciza)
              piece("slab", D_IN[1], D_OUT[0], SLAB),     # techo del corredor = piso de arriba
              piece("wall_r", D_OUT[1], D_X1, D_H)]       # pared derecha (maciza)

    # el subsuelo pintado de este tramo pasa a ser el fondo del corredor (detrás de Lio)
    strip = next(i for i in inst_ if i["name"] == SUB and round(i["x"]) == D_X0)
    strip.update(x=D_IN[0], width=D_OUT[1] - D_IN[0], zOrder=-3)
    for i in inst_:
        if i["name"] in (TUBE, ROTA) and D_X0 <= i["x"] <= D_X1:
            # un tubo metido en una pared: al corredor (con su halo, 12 px a la izq.)
            nx = min(max(i["x"], D_IN[1] + 8), D_OUT[0] - TUBE_W - 8)
            if nx != i["x"]:
                g = next(g for g in inst_ if g["name"] == GLOW and round(g["x"]) == round(i["x"]) - 12)
                g["x"], i["x"] = nx - 12, nx
    for i in inst_:
        if i["name"] in (TUBE, ROTA, GLOW) and D_X0 <= i["x"] + 12 <= D_X1:
            i["zOrder"] = -2 if i["name"] == GLOW else -1

    # piso invisible del corredor, bordes de la boca, ducto de aire de salida
    inst_.append(dict(inst(DPISO, D_IN[0], D_FLOOR, 0, D_OUT[1] - D_IN[0], 8), persistentUuid=duid("piso")))
    inst_.append(dict(inst(DBORDE, D_IN[0] - 4, D_Y, 2), persistentUuid=duid("borde_l")))
    inst_.append(dict(inst(DBORDE, D_IN[1], D_Y, 2), persistentUuid=duid("borde_r")))
    air = next(i for i in inst_ if i["name"] == "AirFlow")
    vent = next(i for i in inst_ if i["name"] == "Vent")
    inst_.append(dict(copy.deepcopy(air), x=D_OUT[0], y=D_AIR_TOP, width=D_OUT[1] - D_OUT[0],
                      height=D_FLOOR - D_AIR_TOP, persistentUuid=duid("air")))
    inst_.append(dict(copy.deepcopy(vent), x=D_OUT[0], y=D_FLOOR - 6, width=D_OUT[1] - D_OUT[0],
                      height=6, persistentUuid=duid("vent")))

    # antídoto del estante alto → corredor (busca en el tramo: idempotente)
    anti = next(i for i in inst_ if i["name"] == "Antidoto" and D_X0 <= i["x"] <= D_X1)
    anti.update(x=D_ANTI[0], y=D_ANTI[1])
    # patrullas que cruzaban los agujeros
    for name, (x, mn, mx) in D_PATROL.items():
        z = next(i for i in inst_ if i["name"] == name and D_X0 <= i["x"] <= D_X1)
        for var, val in (("MinX", mn), ("MaxX", mx)):
            if val is not None:
                next(v for v in z["initialVariables"] if v["name"] == var)["value"] = val
        if x is not None:
            z["x"] = x


def wire_scene(sc, seed, breaks):
    # ---- limpieza (idempotente) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]
    ducto = sc["name"] == DUCTO_SCENE
    if ducto:
        restore_ducto(sc)

    # ---- objetos ----
    ground = next(o for o in sc["objects"] if o["name"] == "Ground")
    sub = copy.deepcopy(ground)            # TiledSprite: misma forma, sin Platform
    sub["name"] = SUB
    sub["texture"] = "lab_subsuelo.png"
    sub["behaviors"] = []
    sub["effects"] = []
    sub["variables"] = []
    base = next(o for o in sc["objects"] if o["name"] == "LampGlow")   # un Sprite cualquiera
    sc["objects"] += [
        sub,
        sprite_obj(base, TUBE, [f"contencion_{i}.png" for i in range(4)], 0.28),
        rota_obj(base),
        sprite_obj(base, GLOW, ["contencion_glow.png"], 1, [("Seed", 0), ("Fast", 0)]),
    ]
    if ducto:
        piso = copy.deepcopy(sub)
        piso.update(name=DPISO, texture="lab_shelf.png",          # se oculta al empezar
                    behaviors=copy.deepcopy(ground["behaviors"]))   # plataforma maciza, como el piso
        sc["objects"] += [piso, sprite_obj(base, DBORDE, ["escotilla_borde.png"], 1)]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in (SUB, TUBE, ROTA, GLOW) + ((DPISO, DBORDE) if ducto else ())]

    # ---- instancias: un subsuelo por tramo de piso + tubos repartidos ----
    rnd = random.Random(seed)
    floors = sorted((i for i in sc["instances"] if i["name"] == "Ground"
                     and round(i.get("height", 0)) == 96 and i["y"] > 0), key=lambda i: i["x"])
    # bordes de los huecos entre tramos de piso
    edges = [e for a, b in zip(floors, floors[1:]) for e in (a["x"] + a["width"], b["x"])]
    new, n_rota = [], 0
    for g in floors:
        gx, gy, gw = g["x"], g["y"], g["width"]
        new.append(inst(SUB, gx, gy + SLAB, 2, gw, SUB_H))
        tube_y = gy + SLAB + GRATE - TUBE_H
        x = gx + MARGIN + rnd.randint(0, 40)
        while x + TUBE_W <= gx + gw - MARGIN:
            rota = rnd.random() < P_ROTA
            if any(abs(x + TUBE_W / 2 - e) < PIT_SAFE for e in edges):
                rota = False        # junto a un hueco: nunca roto (ver docstring)
            n_rota += rota
            seed_v = round(rnd.uniform(0, 6.28), 2)
            new.append(inst(GLOW, x - 12, tube_y - 8, 3, vars_=[("Seed", seed_v), ("Fast", int(rota))]))
            new.append(inst(ROTA if rota else TUBE, x, tube_y, 4))
            x += rnd.randint(GAP_MIN, GAP_MAX)
    sc["instances"] += new
    if ducto:
        apply_ducto(sc)

    # ---- eventos ----
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Subsuelo del lab (wire_lab_subsuelo.py): tubos de contención con virus "
                    "(cuadro inicial al azar para que no floten sincronizados) y halo verde que "
                    "late (los rotos titilan).",
         "comment2": "", MARK: True},
        std([ins("BuiltinCommonInstructions::Once", [])], [], [
            foreach(TUBE, [ins("ChangeSprite", [TUBE, "=", "RandomInRange(0, 3)"])]),
            foreach(ROTA, [ins("ChangeSprite", [ROTA, "=", "RandomInRange(0, 3)"])]),
        ]),
        foreach(GLOW, [ins("Opacity", [GLOW, "=",
            f"round(255 * (0.72 + 0.18 * sin({T} * (1.6 + {GLOW}.Variable(Fast) * 9) + {GLOW}.Variable(Seed))"
            # floor(0.5*sin + 0.7) = 1 solo si sin > 0.6: bajón corto (tubo roto)
            f" - {GLOW}.Variable(Fast) * 0.3 * floor(0.5 * sin({T} * 23 + {GLOW}.Variable(Seed) * 3) + 0.7)))"])]),
    ]
    if ducto:
        sc["events"].append(std([ins("BuiltinCommonInstructions::Once", [])], [ins("Hide", [DPISO])]))
    if breaks:
        assert any(o["name"] == "MiniVirus" for o in sc["objects"]), \
            f"{sc['name']} no tiene MiniVirus: corré wire_minivirus.py primero"
        sc["events"] += break_events()
    tubes = sum(1 for i in new if i["name"] in (TUBE, ROTA))
    print(f"{sc['name']}: {len(floors)} tramos de piso | {tubes} tubos ({n_rota} rotos"
          f"{', estallan' if breaks else ', decorado'})")


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm in RES:
        if nm not in have:
            res.append({"file": f"assets/Lab/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})
    for k, name in enumerate(SCENES):
        wire_scene(next(x for x in d["layouts"] if x["name"] == name), 1810 + k, name in BREAK_SCENES)
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Lab/lab_subsuelo.png"), "corré gen_lab_subsuelo.py primero"
    main()
