#!/usr/bin/env python3
"""
wire_jefe_jeringa.py  —  pelea nueva con Paciente Zero: "que se clave la jeringa"
(19/10). La anterior (camina → carga → embiste → expuesto donde cayera) "no se
entendía ni era entretenida" y el expuesto contra el borde quedaba debajo de las
estatuas; el usuario la descartó entera.

La idea: al científico no se lo puede pisar cuando uno quiere. Hay que hacer que
EMBISTA y clave la jeringa en una PIRÁMIDE: ahí queda trabado y se lo pisa desde
el busto de al lado (o bajando de la pirámide).

Estados (scene var BossState; las animaciones son las de wire_jefe.py):
  0 CAMINA   hacia Lio (Walk). A los T_CAMINA s → 1.
  1 APUNTA   aviso: se agacha y levanta la jeringa (Carga) + contorno rojo +
             chispazo grave. Queda mirando para donde va a embestir.
  2 EMBISTE  en línea recta (Embiste; Walk hasta el 28/10). Si llega a la pirámide de ese lado habiendo
             recorrido >= ARRANQUE px → 3. Si no (salió pegado a la pirámide) frena
             y vuelve a 0. Pegarle de costado a Lio = −1 vida (como siempre).
  3 CLAVADO  (Expuesto, estrellitas) T_CLAVADO s. Única ventana: pisotón = −1 vida
             del jefe, se desclava y retrocede. De costado NO lastima (está trabado).
             En la primera fase, cartel "PISALO!" que titila sobre la cabeza.
Fases (una por vida): 3 = lento; 2 = más rápido y al desclavarse escupe virus
(wire_minivirus.py, sin cambios);
1 = se inyecta: x1.15 de tamaño, más rápido y embiste DOS veces seguidas: la
primera hacia el lado CONTRARIO a Lio, rebota en esa pirámide, apunta 0.4 s y la
segunda viene hacia Lio y se clava de su lado (de busto a busto no se llega).

Arena: la zona donde queda clavado (al pie de cada pirámide) estaba debajo de los
bustos (plataforma y 96) → no se lo podía pisar, el bug del 18/10. Los bustos (y su
Estante, borde y bandera) se corren 22 px hacia el centro: arriba del jefe clavado
queda libre y el busto sirve de trampolín para saltarle encima.

Además: los virus que caen del cielo paran mientras está clavado (ventana limpia).
Los zombies de la arena (wire_l3_arena_zombies.py) entraban recién desde la fase 2;
desde el 28/10 entran desde el comienzo, como una invasión (pedido del usuario).

Edita game/game.json (backup .bak-<ts>, idempotente). Los eventos de la pelea vieja
se guardan en scripts/jefe_pelea_vieja.json; REVERT=1 los restaura (los bustos
quedan donde están). Correr DESPUÉS de toda la cadena de L3 (wire_jefe.py incluido).
Uso:  python3 scripts/wire_jefe_jeringa.py   (raíz del repo, GDevelop CERRADO)
"""
import copy
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdevelop_cerrado import asegurar_gdevelop_cerrado  # noqa: E402

GAME = "game/game.json"
VIEJA = "scripts/jefe_pelea_vieja.json"
BOSS = "PacienteZero"
GRUPO = "Jefe: que se clave la jeringa (wire_jefe_jeringa.py)"
CARTEL = "PisaloText"

PISO = 150
# caras de las pirámides donde se clava: fin de la losa izq. (Estante 40..104) y comienzo
# de la der. (376..440). El cuerpo del jefe (máscara) va de 24/72 a 45/72 del ancho y se
# espeja al mirar a la izquierda (27/72..48/72). Hasta el 28/10 la imagen tenía 48 de ancho
# (12/48..33/48); se ensanchó para la motosierra grande, que ahora se mete en la pirámide.
CARA_IZQ, CARA_DER = 104, 376
TOPE_IZQ = f"{CARA_IZQ} - {BOSS}.Width() * 0.375"
TOPE_DER = f"{CARA_DER} - {BOSS}.Width() * 0.625"
ARRANQUE = 48            # px mínimos de embestida para clavarse (si sale pegado, frena)
# bustos: x nueva de su Estante (y 96). Antes 110 / 306 (debajo quedaba el jefe clavado)
BUSTO_IZQ, BUSTO_DER = 132, 284
BANDERA_DX = {"izq": 4, "der": 56}   # la bandera del pie, relativa al busto (wire_l3_caos.py)

HP = "Variable(BossHP)"
FASE = f"(3 - {HP})"                         # 0, 1, 2
VEL_CAMINA = f"(35 + {FASE} * 10)"
VEL_EMBISTE = f"(170 + {FASE} * 35)"
T_CAMINA = f"(1.6 - {FASE} * 0.3)"
T_APUNTA = f"(1.0 - {FASE} * 0.15)"
T_APUNTA_2 = "0.4"                           # fase 3, la segunda embestida
T_CLAVADO = f"(3.0 - {FASE} * 0.4)"
T_TOPE = "2.0"                               # embestida que no llega a ningún lado
ESCALA_FINAL = "1.15"


def ins(value, params, inverted=False):
    i = {"type": {"value": value}, "parameters": [str(p) for p in params]}
    if inverted:
        i["type"]["inverted"] = True
    return i


def std(conds, acts, subs=()):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": list(conds),
            "actions": list(acts), "events": list(subs)}


def var(name, op, value):
    return ins("VarScene", [name, op, value])


def setv(name, op, value):
    return ins("ModVarScene", [name, op, value])


def anim(name):
    return [ins("SetAnimationName", [BOSS, f'"{name}"']), ins("PlayAnimation", [BOSS])]


def timer(seconds):
    return ins("ObjectTimer", [BOSS, '"BossT"', seconds])


def reset():
    return ins("ResetObjectTimer", [BOSS, '"BossT"'])


def sfx(name, vol="1", pitch="1"):
    return ins("PlaySound", ["", name, "no", f"GlobalVariable(SfxVolume) * {vol}", pitch])


def activo():
    return [var("BossActivo", "=", "1"), var("Won", "=", "0"), var("BossDown", "=", "0")]


def mirar_a_lio():
    """BossDir y el espejado según de qué lado está Lio."""
    centro = f"{BOSS}.X() + {BOSS}.Width() * 0.5"
    return [
        std([ins("PosX", ["Player", "<", centro])],
            [setv("BossDir", "=", "-1"), ins("FlipX", [BOSS, "yes"])]),
        std([ins("PosX", ["Player", ">=", centro])],
            [setv("BossDir", "=", "1"), ins("FlipX", [BOSS, "no"])]),
    ]


def clavarse(lado):
    """llega a la pirámide de `lado` embistiendo: se clava (o, en la fase 3 y primera
    vez, rebota y vuelve a apuntar para el otro lado)."""
    izq = lado == "izq"
    tope = TOPE_IZQ if izq else TOPE_DER
    lejos = f"abs({BOSS}.X() - Variable(BossX0))"
    llega = [var("BossDir", "=", "-1" if izq else "1"),
             ins("PosX", [BOSS, "<=" if izq else ">=", tope])]
    impacto = [ins("SetX", [BOSS, "=", tope]),
               ins("Create", ["", "ZombiePoofFX", f"{CARA_IZQ} - 8" if izq else f"{CARA_DER} - 8",
                              f"{BOSS}.Y() + {BOSS}.Height() * 0.35", ""]),
               sfx("sfx_disparo.wav", "0.8", "0.55"), reset()]
    largo = ins("BuiltinCommonInstructions::CompareNumbers", [lejos, ">=", str(ARRANQUE)])
    sigue = var("BossState", "=", "2")       # cada caso cambia de estado: no encadenar dos
    return std(llega, [], [
        # salió pegado a la pirámide: no hubo embestida, frena
        std([sigue, ins("BuiltinCommonInstructions::CompareNumbers", [lejos, "<", str(ARRANQUE)])],
            [ins("SetX", [BOSS, "=", tope]), setv("BossState", "=", "0"), reset(),
             setv("BossCharges", "=", "0"), *anim("Walk")]),
        # fase 3, primera embestida: rebota, se da vuelta y vuelve a apuntar
        std([sigue, largo, var("BossHP", "=", "1"), var("BossCharges", "=", "0")],
            [*impacto, setv("BossCharges", "=", "1"), setv("BossDir", "*", "-1"),
             ins("FlipX", [BOSS, "no" if izq else "yes"]), setv("BossState", "=", "1"),
             ins("EnableEffect", [BOSS, '"InfectedOutline"', "yes"]), *anim("Carga")]),
        # se clava (fases 3 y 2, o la segunda embestida de la fase 1)
        std([sigue, largo, var("BossCharges", "=", "1")],
            [*impacto, setv("BossState", "=", "3"), setv("BossCharges", "=", "0"), *anim("Expuesto")]),
        std([sigue, largo, var("BossHP", ">=", "2"), var("BossCharges", "=", "0")],
            [*impacto, setv("BossState", "=", "3"), *anim("Expuesto")]),
    ])


def eventos():
    centro = f"{BOSS}.X() + {BOSS}.Width() * 0.5"
    ev = [
        {"type": "BuiltinCommonInstructions::Comment", "color": {"b": 109, "g": 230, "r": 255,
         "textB": 0, "textG": 0, "textR": 0},
         "comment": "Pelea con Paciente Zero: 0 camina, 1 apunta (aviso), 2 embiste, 3 clavado en "
                    "una pirámide (única ventana para pisarlo). Una fase por vida. "
                    "Generado por wire_jefe_jeringa.py.", "comment2": ""},
        std([ins("BuiltinCommonInstructions::Once", [])],
            [reset(), ins("ResetObjectTimer", [BOSS, '"BossHurt"']), *anim("Walk"),
             setv("BossCharges", "=", "0"), ins("Hide", [CARTEL])]),
        # los pies siempre en el piso (crece en la fase 3) y dentro de la arena, entre pirámides
        std([], [ins("SetY", [BOSS, "=", f"{PISO} - {BOSS}.Height()"])]),
        std([ins("PosX", [BOSS, "<", TOPE_IZQ])], [ins("SetX", [BOSS, "=", TOPE_IZQ])]),
        std([ins("PosX", [BOSS, ">", TOPE_DER])], [ins("SetX", [BOSS, "=", TOPE_DER])]),

        # 0 CAMINA
        std([*activo(), var("BossState", "=", "0")],
            [ins("SetX", [BOSS, "+", f"Variable(BossDir) * {VEL_CAMINA} * TimeDelta()"])],
            [*mirar_a_lio(),
             std([timer(T_CAMINA)],
                 [setv("BossState", "=", "1"), reset(), setv("BossCharges", "=", "0"),
                  ins("EnableEffect", [BOSS, '"InfectedOutline"', "yes"]),
                  sfx("sfx_chispazo.wav", "0.7", "0.4"), *anim("Carga")],
                 # fase 1: la primera embestida va para el lado CONTRARIO a Lio; rebota y la
                 # segunda viene hacia él y se clava de su lado (cruzar de un busto al otro no
                 # se puede: planeando, Lio cae en x 268 y el busto der. empieza en 284)
                 [std([var("BossHP", "=", "1")], [setv("BossDir", "*", "-1")],
                      [std([var("BossDir", "=", "-1")], [ins("FlipX", [BOSS, "yes"])]),
                       std([var("BossDir", "=", "1")], [ins("FlipX", [BOSS, "no"])])])])]),
        # 1 APUNTA → 2 EMBISTE
        std([*activo(), var("BossState", "=", "1"), var("BossCharges", "=", "0"), timer(T_APUNTA)],
            [setv("BossState", "=", "2"), reset(), setv("BossX0", "=", f"{BOSS}.X()"),
             ins("EnableEffect", [BOSS, '"InfectedOutline"', "no"]),
             sfx("sfx_gatillo.wav", "0.8", "0.7"), *anim("Embiste")]),
        std([*activo(), var("BossState", "=", "1"), var("BossCharges", "=", "1"), timer(T_APUNTA_2)],
            [setv("BossState", "=", "2"), reset(), setv("BossX0", "=", f"{BOSS}.X()"),
             ins("EnableEffect", [BOSS, '"InfectedOutline"', "no"]),
             sfx("sfx_gatillo.wav", "0.8", "0.7"), *anim("Embiste")]),
        # 2 EMBISTE
        std([*activo(), var("BossState", "=", "2")],
            [ins("SetX", [BOSS, "+", f"Variable(BossDir) * {VEL_EMBISTE} * TimeDelta()"])],
            [clavarse("izq"), clavarse("der"),
             std([var("BossState", "=", "2"), timer(T_TOPE)],
                 [setv("BossState", "=", "0"), reset(), setv("BossCharges", "=", "0"), *anim("Walk")])]),
        # 3 CLAVADO: se desclava solo y retrocede un poco
        std([*activo(), var("BossState", "=", "3"), timer(T_CLAVADO)],
            [setv("BossState", "=", "0"), reset(), *anim("Walk"),
             ins("SetX", [BOSS, "-", "Variable(BossDir) * 14"])]),

        # pisotón con el jefe NO clavado: rebota y no le hace nada (sirve para esquivar)
        std([ins("CollisionNP", ["Player", BOSS, "", "", ""]),
             ins("PosY", ["Player", "<", f"{BOSS}.Y()"]),
             ins("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
             var("BossState", "!=", "3")],
            [ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                 ["Player", "PlatformerObject", "=", "0"]),
             setv("BounceVel", "=", "-380"), sfx("sfx_stomp.wav")]),
        # pisotón con el jefe clavado: −1 vida, se desclava y retrocede; Lio queda 1 s a salvo
        std([ins("CollisionNP", ["Player", BOSS, "", "", ""]),
             ins("PosY", ["Player", "<", f"{BOSS}.Y()"]),
             ins("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
             var("BossState", "=", "3"), ins("ObjectTimer", [BOSS, '"BossHurt"', "1"])],
            [setv("BossHP", "-", "1"), ins("ResetObjectTimer", [BOSS, '"BossHurt"']),
             ins("Create", ["", "ZombiePoofFX", centro, f"{BOSS}.Y()", ""]),
             setv("BossState", "=", "0"), reset(), setv("BossCharges", "=", "0"),
             ins("SetX", [BOSS, "-", "Variable(BossDir) * 24"]),
             ins("ResetObjectTimer", ["Player", '"Invuln"']),
             ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                 ["Player", "PlatformerObject", "=", "0"]),
             setv("BounceVel", "=", "-380"), sfx("sfx_stomp.wav"), *anim("Walk")],
            [std([var("BossHP", "=", "1")],      # última fase: se inyecta y crece
                 [ins("ChangeScale", [BOSS, "=", ESCALA_FINAL]),
                  sfx("sfx_chispazo.wav", "1", "0.3")])]),
        # de costado: −1 vida y knockback (no si está clavado: está trabado)
        *[std([ins("CollisionNP", ["Player", BOSS, "", "", ""]),
               ins("PosY", ["Player", ">=", f"{BOSS}.Y()"]),
               ins("ObjectTimer", ["Player", '"Invuln"', "1"]),
               var("BossState", "!=", "3"), var("BossDown", "=", "0"),
               ins("PosX", ["Player", op, centro])],
              [setv("Lives", "-", "1"), ins("ResetObjectTimer", ["Player", '"Invuln"']),
               ins("SetAnimationName", ["Player", '"Hit"']), sfx("sfx_hurt.wav"),
               ins("SetX", ["Player", "+", dx]), ins("SetY", ["Player", "+", "-30"])])
          for op, dx in ((">=", "90"), ("<", "-90"))],

        # cartel "PISALO!" sobre la cabeza, titilando, mientras está clavado en la primera fase
        std([], [ins("Hide", [CARTEL])]),
        std([var("BossState", "=", "3"), var("BossHP", "=", "3"), var("BossDown", "=", "0"),
             ins("BuiltinCommonInstructions::CompareNumbers", ["mod(TimeFromStart() * 3, 2)", "<", "1.3"])],
            [ins("Show", [CARTEL, ""]),
             ins("SetX", [CARTEL, "=", f"{centro} - {CARTEL}.Width() * 0.5"]),
             ins("SetY", [CARTEL, "=", f"{BOSS}.Y() - {CARTEL}.Height() - 6"])]),
    ]
    return {"type": "BuiltinCommonInstructions::Group", "name": GRUPO, "source": "",
            "creationTime": 0, "folded": True, "color": {"b": 60, "g": 60, "r": 200},
            "conditions": [], "events": ev}


def es_de_la_pelea_vieja(e):
    """los eventos 51..61 originales: estados 0-3, topes, pisotones y choques del jefe."""
    s = json.dumps(e)
    if e.get("type") != "BuiltinCommonInstructions::Standard" or BOSS not in s:
        return False
    conds = [c["type"]["value"] + json.dumps(c["parameters"]) for c in e.get("conditions", [])]
    acts = [a["type"]["value"] + json.dumps(a["parameters"]) for a in e.get("actions", [])]
    if any('"BossState"' in c for c in conds) and "BossSpit" not in s:
        return True                                                    # estados y pisotones
    if any(c.startswith("CollisionNP") and BOSS in c for c in conds):
        return True                                                    # choques
    if conds and all(c.startswith("PosX") and BOSS in c for c in conds) and len(conds) == 1 \
            and acts and acts[0].startswith("SetX") and len(acts) == 1:
        return True                                                    # topes de la arena
    if any(c.startswith("BuiltinCommonInstructions::Once") for c in conds) \
            and any('BossT' in a for a in acts) and len(acts) == 3:
        return True                                                    # arranque
    return False


def agregar_cond(evs, marca, cond):
    """agrega `cond` al evento cuyas condiciones incluyen el texto `marca` (idempotente)."""
    for e in evs:
        cs = json.dumps(e.get("conditions", []))
        if marca in cs:
            if json.dumps(cond["parameters"]) not in cs:
                e["conditions"].append(cond)
            return True
        if agregar_cond(e.get("events", []), marca, cond):
            return True
    return False


def mover_bustos(lay):
    def mover(pred, x_nuevo):
        hechos = [i for i in lay["instances"] if pred(i)]
        for i in hechos:
            i["x"] = x_nuevo
        return len(hechos)
    n = 0
    for lado, x_viejo_max, x in (("izq", 240, BUSTO_IZQ), ("der", 480, BUSTO_DER)):
        en_lado = (lambda i, lo=x_viejo_max - 240, hi=x_viejo_max: lo <= i["x"] < hi)
        n += mover(lambda i: i["name"] == "Estante" and round(i["y"]) == 96 and en_lado(i), x)
        n += mover(lambda i: i["name"] == "PlatEdge" and round(i["y"]) == 93 and en_lado(i), x)
        nombre = "EstatuaBustoIzq" if lado == "izq" else "EstatuaBustoDer"
        n += mover(lambda i: i["name"] == nombre, x)
        n += mover(lambda i: i["name"] == "BanderaPie" and i["layer"] == "Decor" and en_lado(i),
                   x + BANDERA_DX[lado])
    return n


def main(revert=False):
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    with open(GAME) as f:
        texto = f.read()
    with open(f"{GAME}.bak-{ts}", "w") as f:
        f.write(texto)
    print("backup", f"{GAME}.bak-{ts}")
    d = json.loads(texto)
    lay = next(l for l in d["layouts"] if l["name"] == "Level3")
    evs = lay["events"]

    pos = next((k for k, e in enumerate(evs) if e.get("name") == GRUPO), None)
    if pos is not None:                                   # ya aplicado: sacar el grupo
        evs.pop(pos)
    else:                                                 # primera vez: sacar la pelea vieja
        viejos = [(k, e) for k, e in enumerate(evs) if es_de_la_pelea_vieja(e)]
        assert len(viejos) == 11, f"esperaba los 11 eventos de la pelea vieja, encontré {len(viejos)}"
        pos = viejos[0][0]
        json.dump({"posicion": pos, "eventos": [e for _, e in viejos]}, open(VIEJA, "w"),
                  indent=2, ensure_ascii=False)
        for k, _ in reversed(viejos):
            evs.pop(k)
        print(f"pelea vieja guardada en {VIEJA} ({len(viejos)} eventos)")

    lay["objects"] = [o for o in lay["objects"] if o["name"] != CARTEL]
    lay["instances"] = [i for i in lay["instances"] if i["name"] != CARTEL]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") != CARTEL]
    nombres = {v["name"] for v in lay["variables"]}

    if revert:
        vieja = json.load(open(VIEJA))
        evs[pos:pos] = vieja["eventos"]
        print("pelea vieja restaurada")
    else:
        evs.insert(pos, eventos())
        for v in ("BossCharges", "BossX0"):
            if v not in nombres:
                lay["variables"].append({"folded": True, "name": v, "type": "number", "value": 0})
        # el cartel: misma fuente que la vida del jefe, amarillo, en el plano de juego
        txt = copy.deepcopy(next(o for o in lay["objects"] if o["name"] == "BossHPText"))
        txt["name"] = CARTEL
        txt["content"]["text"] = "PISALO!"
        txt["content"]["tint"] = "250;220;90"
        lay["objects"].append(txt)
        if "children" in fs:
            fs["children"].append({"objectName": CARTEL})
        lay["instances"].append({"angle": 0, "customSize": False, "height": 0, "layer": "",
                                 "name": CARTEL, "width": 0, "x": 0, "y": -100, "zOrder": 20,
                                 "numberProperties": [], "stringProperties": [],
                                 "initialVariables": []})
        # virus del cielo en pausa mientras está clavado (los zombies de la arena ya no
        # esperan a la fase 2: 28/10, invasión desde el comienzo)
        assert agregar_cond(evs, '"ArenaVT", ">=", "4.0"', var("BossState", "!=", "3"))
        print("bustos movidos:", mover_bustos(lay), "instancias")

    with open(GAME, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    json.load(open(GAME))
    print("revert OK" if revert else "OK")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
