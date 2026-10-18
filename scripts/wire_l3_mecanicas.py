#!/usr/bin/env python3
"""
wire_l3_mecanicas.py  —  peligros de calle del Nivel 3 (18/10), en lugar de los
pozos: toldo que rebota, charco electrificado y vapor del subte que sube a unas
marquesinas. (Las macetas que caían de los balcones se sacaron: pedido del
usuario; siguen en MINE para limpiar corridas viejas.) Ubicación y tiempos en l3_recorrido.py;
arte en gen_l3_mecanicas.py.

Todo se calcula con TimeFromStart() (se congela con time scale 0: pausa,
notas): cada mecánica tiene un ciclo t = mod(TimeFromStart() + Fase, período).

  - TOLDO que rebota: caer encima (IsFalling, pies cerca del borde de arriba)
    → BounceVel = −440 (el rebote del pisotón usa −330): sube ≈ 80 px. El
    toldo se hunde un instante (cuadro 2). No es plataforma.
  - CHARCO electrificado (Corrientes, bajo los cables): pisarlo es como caer a
    un pozo: −1 vida y al checkpoint. Chispazos animados en la punta del cable
    y un chispazo que suena si Lio está cerca.
  - POLICÍA ZOMBIE que dispara a mansalva (calle del hospital): un tiro cada
    ~1.7 s hacia donde mira mientras patrulla, con aviso (destello chico
    en la mano + clic del gatillo, 0.5 s). Balas horizontales que salen de la
    mano, a la altura del pecho (150 px/s): se esquivan con un salto planeado (con la mochila); −1 vida y empujón. Solo si Lio está
    a menos de 240 px. Var Tiro (0 quieto, 1 aviso, 2..3 disparando) + timer Fuego.
  - VAPOR del subte (llegada): ciclo de VAPOR_T s: aviso (bocanadas suaves,
    no eleva) → sopla (eleva a 150 px/s, como el ducto de aire de L2) → nada.
    Lio flota con los pies en VAPOR_TOP y se baja de costado a una MARQUESINA
    (plataforma que se atraviesa desde abajo) para pasar por arriba de los
    zombies que marchan.

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_l3_mecanicas": true). Re-correr después de wire_l3_recorrido.py.
Uso:  python3 scripts/wire_l3_mecanicas.py   (raíz del repo, GDevelop CERRADO)
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
MARK = "_l3_mecanicas"
OX = R.OFFSET_X
T = "TimeFromStart()"
MINE = {"Maceta", "Sombra", "ToldoRebote", "Charco", "Chispa", "Rejilla", "Vapor", "Marquesina", "Bala", "Destello"}
RES = (["charco.png", "toldo_rebote_1.png", "toldo_rebote_2.png",
        "rejilla_subte.png", "vapor.png", "marquesina.png", "bala.png", "destello_1.png", "destello_2.png"]
       + [f"chispa_{k}.png" for k in (1, 2, 3)])
REBOTE = -440                        # BounceVel del toldo (el pisotón usa −330)
# policía zombie que dispara a mansalva (18/10): TIROS balas cada TIRO_CADA s hacia
# donde mira, con aviso (destello chico + clic del gatillo) de TIRO_AVISO s. Las balas van
# horizontales desde la mano (altura del pecho) y se esquivan saltando. Solo si Lio está cerca.
# Disparo SUELTO cada ~1.7 s (TIRO_CADA de espera + TIRO_AVISO) desde la mano, al pecho.
# Robot con la mochila (planeo; en L3 Lio siempre la tiene): sin daño 7/7 saltando entre
# 20 y 56 px antes de la bala. Ráfaga de 3 pegada al pecho: ~2/6 (ventana muy chica);
# ráfaga de 2: 5/7. Sin mochila nada de esto se puede esquivar: probar con TieneMochila = 1.
TIRO_CADA, TIRO_AVISO, TIRO_ENTRE, TIROS = 1.2, 0.5, 0.12, 1
BALA_VEL, BALA_VIDA, TIRO_ALCANCE = 150, 2.0, 240
# el arma: la mano del brazo extendido del sprite (32x34), a la altura del pecho. Primero
# salía de la cintura (bala a las piernas, y ≈ 138) y "no se veía natural de un disparo"
# (usuario 18/10). Con la mochila (planeo) la ráfaga al pecho también se esquiva saltando.
MANO_X, MANO_Y = 16, 13
LIFT = 150                           # px/s que sube el vapor (el ducto de L2: 140)


def ins(value, params, inverted=False):
    d = {"type": {"value": value}, "parameters": params}
    if inverted:
        d["type"]["inverted"] = True
    return d


def cmp(a, op, b):
    return ins("BuiltinCommonInstructions::CompareNumbers", [a, op, str(b)])


def ev(conds, acts, subs=(), mark=False):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}
    if subs:
        e["events"] = list(subs)
    if mark:
        e[MARK] = True
    return e


def foreach(obj, subs):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": [], "actions": [], "events": list(subs), MARK: True}


def sprite_obj(tpl, name, images, tbf=1.0, loop=False, variables=(), behaviors=()):
    o = copy.deepcopy(tpl)
    o.update(name=name, effects=[], behaviors=list(behaviors),
             variables=[{"name": k, "type": "number", "value": 0} for k in variables])
    spr = o["animations"][0]["directions"][0]["sprites"][0]
    o["animations"] = [{"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": loop, "timeBetweenFrames": tbf,
        "sprites": [dict(spr, image=im, hasCustomCollisionMask=False, customCollisionMask=[], points=[])
                    for im in images]}]}]
    return o


def tiled_obj(tpl, name, texture, variables=()):
    o = copy.deepcopy(tpl)
    o.update(name=name, texture=texture, effects=[], behaviors=[],
             variables=[{"name": k, "type": "number", "value": 0} for k in variables])
    return o


def inst(name, x, y, z, w=None, h=None, vars_=(), layer=""):
    return {"angle": 0, "customSize": w is not None, "height": h or 0, "layer": layer,
            "name": name, "persistentUuid": str(uuid.uuid4()), "width": w or 0, "x": x, "y": y,
            "zOrder": z, "numberProperties": [], "stringProperties": [],
            "initialVariables": [{"name": k, "type": "number", "value": v} for k, v in vars_]}


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lays = {x["name"]: x for x in d["layouts"]}
    l1, sc = lays["Level1"], lays["Level3"]
    # recursos de las macetas (sacadas): sin esto quedaban registrados sin archivo
    d["resources"]["resources"] = [r for r in d["resources"]["resources"]
                                   if r["name"] not in ("maceta.png", "sombra.png")]
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for nm in RES:
        if nm not in have:
            res.append({"file": f"assets/City/{nm}", "kind": "image", "metadata": "",
                        "name": nm, "smoothed": False, "userAdded": True})
    for nm in ("sfx_disparo.wav", "sfx_gatillo.wav"):           # gen_sfx.py → policia_sfx()
        if nm not in have:
            res.append({"file": f"assets/audio/{nm}", "kind": "audio", "metadata": "", "name": nm,
                        "preloadAsMusic": False, "preloadAsSound": True, "preloadInCache": True,
                        "userAdded": True})

    # ---- limpieza (idempotente) ----
    sc["objects"] = [o for o in sc["objects"] if o["name"] not in MINE]
    sc["instances"] = [i for i in sc["instances"] if i["name"] not in MINE]
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    fs = sc.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in MINE]

    # ---- objetos ----
    o1 = {o["name"]: o for o in l1["objects"]}
    spr, til = o1["Tacho"], o1["Embankment"]
    jumpthru = copy.deepcopy(o1["Toldo"]["behaviors"])          # plataforma que se atraviesa desde abajo
    objs = [
        sprite_obj(spr, "ToldoRebote", ["toldo_rebote_1.png", "toldo_rebote_2.png"]),
        tiled_obj(til, "Charco", "charco.png"),
        sprite_obj(spr, "Chispa", [f"chispa_{k}.png" for k in (1, 2, 3)], tbf=0.07, loop=True),
        sprite_obj(spr, "Rejilla", ["rejilla_subte.png"]),
        tiled_obj(til, "Vapor", "vapor.png", variables=("Fase",)),
        sprite_obj(spr, "Marquesina", ["marquesina.png"], behaviors=jumpthru),
        sprite_obj(spr, "Bala", ["bala.png"], variables=("VX",)),
        sprite_obj(spr, "Destello", ["destello_1.png", "destello_2.png"], variables=("Dur",)),
    ]
    sc["objects"] += objs
    if "children" in fs:
        fs["children"] += [{"objectName": o["name"]} for o in objs]

    # ---- instancias ----
    F = R.FLOOR
    new = []
    for x, y in R.TOLDOS:
        new.append(inst("ToldoRebote", x + OX, y - 2, 0))
    for x0, x1 in R.CHARCOS:
        new.append(inst("Charco", x0 + OX, F - 6, 2, x1 - x0, 8))
        new.append(inst("Chispa", x0 + OX + 10, F - 13, 3))
        new.append(inst("Chispa", (x0 + x1) / 2 + OX, F - 13, 3))
    for x, fase in R.VAPORES:
        new.append(inst("Rejilla", x + OX, F - 3, 2))
        new.append(inst("Vapor", x + OX + 2, R.VAPOR_TOP, 4, 28, F - R.VAPOR_TOP, vars_=[("Fase", fase)]))
    for x, y, w in R.MARQUESINAS:
        new.append(inst("Marquesina", x + OX, y, 1, w, 10))
    sc["instances"] += new

    # ---- eventos ----
    tv = f"mod({T} + Vapor.Variable(Fase), {R.VAPOR_T})"
    playing = [ins("VarScene", ["Over", "=", "0"]), ins("VarScene", ["Won", "=", "0"])]
    pcx = "(Player.X() + Player.Width() / 2)"
    events = [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "Peligros de calle (wire_l3_mecanicas.py): toldo que rebota, "
                    "charco electrificado, vapor del subte + marquesinas. Ciclos con TimeFromStart().",
         "comment2": "", MARK: True},
        # --- toldo que rebota ---
        ev([ins("CollisionNP", ["Player", "ToldoRebote", "", "", ""]),
            ins("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
            ins("PosY", ["Player", "<", "ToldoRebote.Y() - 16"])],
           [ins("ModVarScene", ["BounceVel", "=", str(REBOTE)]),
            ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed", ["Player", "PlatformerObject", "=", "0"]),
            ins("ChangeSprite", ["ToldoRebote", "=", "1"]),
            ins("ResetObjectTimer", ["ToldoRebote", '"Rebote"']),
            ins("PlaySound", ["", "sfx_jump.wav", "no", "GlobalVariable(SfxVolume)", "0.75"])], mark=True),
        ev([ins("ObjectTimer", ["ToldoRebote", '"Rebote"', "0.15"])], [ins("ChangeSprite", ["ToldoRebote", "=", "0"])],
           mark=True),
        # --- charco electrificado: como caer a un pozo ---
        ev([ins("CollisionNP", ["Player", "Charco", "", "", ""]), *playing], [
            ins("ModVarScene", ["Lives", "-", "1"]),
            ins("SetX", ["Player", "=", "Variable(CheckX)"]), ins("SetY", ["Player", "=", "Variable(CheckY)"]),
            ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed", ["Player", "PlatformerObject", "=", "0"]),
            ins("ModVarScene", ["BounceVel", "=", "0"]),
            ins("PlaySound", ["", "sfx_chispazo.wav", "no", "GlobalVariable(SfxVolume)", "0.6"]),
            ins("PlaySound", ["", "sfx_hurt.wav", "no", "GlobalVariable(SfxVolume)", "1"])], mark=True),
        # chispazo que suena cerca (cada ~0.6-1.2 s, vol por distancia)
        foreach("Chispa", [ev([ins("ObjectTimer", ["Chispa", '"Zap"', "Chispa.Variable(Next)"]),
                               cmp(f"abs({pcx} - Chispa.X())", "<", 200)],
            [ins("ResetObjectTimer", ["Chispa", '"Zap"']),
             ins("ModVarObjet", ["Chispa", "Next", "=", "0.6 + Random(60) / 100"]),
             ins("PlaySound", ["", "sfx_chispazo.wav", "no",
                               f"GlobalVariable(SfxVolume) * 0.4 * clamp(1 - abs({pcx} - Chispa.X()) / 200, 0, 1)",
                               "RandomFloatInRange(1.0, 1.6)"])])]),
        # --- vapor del subte ---
        foreach("Vapor", [
            ev([], [ins("TiledSpriteObject::YOffset", ["Vapor", "+", "70 * TimeDelta()"]),
                    ins("TiledSpriteObject::SetOpacity", ["Vapor", "=",
                        f"round(225 * clamp(ceil({tv} - {R.VAPOR_AVISO}), 0, 1) * clamp(ceil({R.VAPOR_AVISO + R.VAPOR_ON} - {tv}), 0, 1)"
                        f" + 70 * clamp(ceil({R.VAPOR_AVISO} - {tv}), 0, 1))"])],
               subs=[ev([cmp(tv, ">=", R.VAPOR_AVISO), cmp(tv, "<", R.VAPOR_AVISO + R.VAPOR_ON),
                         ins("CollisionNP", ["Player", "Vapor", "", "", ""])],
                        [ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                             ["Player", "PlatformerObject", "=", "0"]),
                         ins("SetY", ["Player", "-", f"{LIFT} * TimeDelta()"])])]),
        ]),
    ]
    # --- el policía zombie dispara a mansalva ---
    mano_x = f"ZombiePol.X() + {MANO_X} + ZombiePol.Variable(Dir) * {MANO_X}"
    mano_y = f"ZombiePol.Y() + {MANO_Y}"

    def destello(frame, dur):
        return [ins("Create", ["", "Destello", f"{mano_x} - 5", f"{mano_y} - 5", ""]),
                ins("ChangeSprite", ["Destello", "=", str(frame)]),
                ins("ModVarObjet", ["Destello", "Dur", "=", str(dur)]),
                ins("ResetObjectTimer", ["Destello", '"Vida"'])]

    disparos = []
    for k in range(TIROS):
        ultimo = k == TIROS - 1
        disparos.append(ev([ins("NumberObjectVariable", ["ZombiePol", "Tiro", "=", str(1 + k)]),
                            ins("ObjectTimer", ["ZombiePol", '"Fuego"', str(round(TIRO_AVISO + k * TIRO_ENTRE, 2))])], [
            ins("Create", ["", "Bala", mano_x, mano_y, ""]),
            ins("ModVarObjet", ["Bala", "VX", "=", f"ZombiePol.Variable(Dir) * {BALA_VEL}"]),
            ins("SetAngle", ["Bala", "=", "90 - 90 * ZombiePol.Variable(Dir)"]),   # 0° a la derecha, 180° a la izquierda
            ins("ResetObjectTimer", ["Bala", '"Vida"']),
            *destello(1, 0.07),
            ins("PlaySound", ["", "sfx_disparo.wav", "no", "GlobalVariable(SfxVolume) * 0.7",
                              "RandomFloatInRange(0.9, 1.1)"]),
            ins("ModVarObjet", ["ZombiePol", "Tiro", "=", "0" if ultimo else str(2 + k)]),
            *([ins("ResetObjectTimer", ["ZombiePol", '"Fuego"'])] if ultimo else []),
        ]))
    pcx_ = "(Player.X() + Player.Width() / 2)"
    events += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": f"Policía zombie que dispara a mansalva: cada {TIRO_CADA} s, aviso de {TIRO_AVISO} s "
                    f"(destello + clic) y {TIROS} balas hacia donde mira; se esquivan saltando.",
         "comment2": "", MARK: True},
        ev([ins("BuiltinCommonInstructions::Once", [])], [ins("ResetObjectTimer", ["ZombiePol", '"Fuego"'])], mark=True),
        foreach("ZombiePol", [
            # aviso: si Lio está cerca y pasó el tiempo entre ráfagas
            ev([ins("NumberObjectVariable", ["ZombiePol", "Tiro", "=", "0"]),
                ins("ObjectTimer", ["ZombiePol", '"Fuego"', str(TIRO_CADA)]),
                cmp(f"abs({pcx_} - (ZombiePol.X() + 16))", "<", TIRO_ALCANCE),
                cmp("abs((Player.Y() + Player.Height() / 2) - (ZombiePol.Y() + 17))", "<", 70), *playing], [
                ins("ModVarObjet", ["ZombiePol", "Tiro", "=", "1"]),
                ins("ResetObjectTimer", ["ZombiePol", '"Fuego"']),
                *destello(0, TIRO_AVISO - 0.05),
                ins("PlaySound", ["", "sfx_gatillo.wav", "no", "GlobalVariable(SfxVolume) * 0.8", "1"])]),
            *disparos,
        ]),
        # balas: avanzan, se apagan a los BALA_VIDA s, le pegan a Lio
        ev([], [ins("SetX", ["Bala", "+", "Bala.Variable(VX) * TimeDelta()"])], mark=True),
        ev([ins("ObjectTimer", ["Bala", '"Vida"', str(BALA_VIDA)])], [ins("Delete", ["Bala", ""])], mark=True),
        ev([ins("CollisionNP", ["Player", "Bala", "", "", ""]),
            ins("ObjectTimer", ["Player", '"Invuln"', "1"]), *playing], [
            ins("ModVarScene", ["Lives", "-", "1"]), ins("ResetObjectTimer", ["Player", '"Invuln"']),
            ins("SetAnimationName", ["Player", '"Hit"']),
            ins("PlaySound", ["", "sfx_hurt.wav", "no", "GlobalVariable(SfxVolume)", "1"]),
            ins("SetY", ["Player", "+", "-20"]), ins("SetX", ["Player", "+", f"Bala.Variable(VX) / 5"]),
            ins("Delete", ["Bala", ""])], mark=True),
        ev([ins("CollisionNP", ["Player", "Bala", "", "", ""])], [ins("Delete", ["Bala", ""])], mark=True),
        ev([ins("ObjectTimer", ["Destello", '"Vida"', "Destello.Variable(Dur)"])], [ins("Delete", ["Destello", ""])],
           mark=True),
    ]
    pol = next((o for o in sc["objects"] if o["name"] == "ZombiePol"), None)
    assert pol, "no hay ZombiePol en L3: corré wire_l3_recorrido.py primero"
    if not any(v["name"] == "Tiro" for v in pol["variables"]):
        pol["variables"].append({"name": "Tiro", "type": "number", "value": 0})
    sc["events"] += events
    # la var Next de la chispa (intervalo del sonido)
    ch = next(o for o in sc["objects"] if o["name"] == "Chispa")
    ch["variables"] = [{"name": "Next", "type": "number", "value": 0.8}]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    cnt = {}
    for i in new:
        cnt[i["name"]] = cnt.get(i["name"], 0) + 1
    print("Level3: mecánicas de calle", cnt)


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/charco.png"), "corré gen_l3_mecanicas.py primero"
    main()
