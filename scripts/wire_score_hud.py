#!/usr/bin/env python3
"""
wire_score_hud.py — sistema de puntaje + HUD unificado de Level1/2/3 y
récord en el MainMenu, con la fuente bitmap del juego (gen_font.py).

Puntaje (decidido el 09/10):
  - stomp +100, antídoto +250. Cadena de stomps sin tocar el piso (como
    Super Mario Bros.): 100, 200, 400, 800 y después 1000 cada uno; el
    sonido del stomp sube de tono con la cadena. Número estilo arcade sobre el
    zombie/frasco (salta, titila blanco/dorado y parpadea antes de irse);
  - al ganar el nivel: meta +1000, +500 por vida restante, +1000 si se
    juntaron los 4 antídotos del nivel; en la victoria final (L3), +1000
    si se juntaron las 7 pruebas del brote (globals Nota1..7, wire_notas.py);
  - lo del nivel vive en la var de escena LevelScore y se suma al global
    Puntaje recién al ganar. Morir / Game Over / reintentar descarta lo
    del nivel; [R] después de ganar le resta lo sumado (no se puede
    farmear repitiendo); "Jugar" en el menú pone Puntaje en 0;
  - un solo récord (global Record) en el almacenamiento del navegador
    (storage "PacienteZero", clave "record"); se lee una vez por partida
    en cualquier escena (RecordLoaded) para no pisarlo con uno menor si se
    arranca por una escena que no es el menú.

HUD (capa UI): corazones como estaban | ícono + "n/4" antídotos (L1/L2)
| "PUNTOS 000000" arriba a la derecha. En L3 el cartel del jefe pasa a la
fuente bitmap, centrado arriba. En la victoria, desglose debajo del
cartel (VictoryScore). MainMenu: "RÉCORD 000000" arriba a la derecha.

Reemplaza el primer corte que había a mano en Level1 (PuntajeText, los
ModVarGlobal Puntaje y el reset en Once). Idempotente: los eventos nuevos
van en un grupo propio que se reemplaza entero, y las acciones que agrega
a eventos existentes se quitan antes de volver a ponerlas.
Si se corre wire_levels23.py --force, volver a correr este script.

Requiere:  python3 scripts/gen_font.py
Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_score_hud.py    (desde la raíz del repo)
"""
import datetime
import json
import shutil

GAME = "game/game.json"
LEVELS = ["Level1", "Level2", "Level3"]
GROUP = "HUD y puntaje (wire_score_hud.py)"
W = 480

# tipos de instrucción del objeto BitmapText (verificados en el JS compilado)
BT_TEXT = "BitmapText::BitmapTextObject::SetText"
BT_TINT = "BitmapText::SetTint"

AMBER = "255;206;110"    # mismo acento que el menú (luz de farol)
WHITE = "236;238;230"
TOXIC = "132;214;92"     # verde virus = 4/4 antídotos
RED = "240;120;120"

FONT_IMG, FONT_FNT = "hud_font.png", "hud_font.fnt"
FINAL_LEVEL = "Level3"
N_NOTAS, NOTAS_BONUS = 7, 1000
STORE = ['"PacienteZero"', '"record"']
CW = 6   # avance por carácter de la fuente (monoespaciada)


def text_w(s):
    return len(s) * CW + 2


def pad6(expr):
    return f'StrRepeat("0", 6 - StrLength(ToString({expr}))) + ToString({expr})'


def act(t, params, inverted=False):
    d = {"type": {"value": t}, "parameters": params}
    if inverted:
        d["type"]["inverted"] = True
    return d


def ev(conds, acts, subs=None):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}
    if subs:
        e["events"] = subs
    return e


def comment(txt):
    return {"type": "BuiltinCommonInstructions::Comment",
            "color": {"b": 0, "g": 0, "r": 0, "textB": 0, "textG": 0, "textR": 0},
            "comment": txt}


def btext(name, text, tint, align="left"):
    return {"assetStoreId": "", "name": name, "type": "BitmapText::BitmapTextObject",
            "variables": [], "effects": [], "behaviors": [],
            "content": {"text": text, "opacity": 255, "scale": 1, "fontSize": 20,
                        "tint": tint, "bitmapFontResourceName": FONT_FNT,
                        "textureAtlasResourceName": FONT_IMG, "align": align,
                        "verticalTextAlignment": "top"}}


def inst(name, x, y, z, layer="UI"):
    return {"angle": 0, "customSize": False, "height": 0, "layer": layer, "name": name,
            "width": 0, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def walk(evs):
    for e in evs:
        yield e
        yield from walk(e.get("events", []))


def params_of(e, kind):
    return [(c["type"]["value"], c["parameters"]) for c in e.get(kind, [])]


def find_event(lay, pred, what):
    hits = [e for e in walk(lay["events"]) if pred(e)]
    assert len(hits) == 1, f"{lay['name']}: esperaba 1 evento '{what}', hay {len(hits)}"
    return hits[0]


def has_cond(e, t, *p):
    return any(ct == t and all(cp[i] == v for i, v in enumerate(p))
               for ct, cp in params_of(e, "conditions"))


MINE = ("LevelScore", "Puntaje", "PtsPopup")


def strip_mine(e):
    """quita acciones que puso este script (o el corte viejo de Level1)."""
    if "actions" not in e:
        return
    e["actions"] = [a for a in e["actions"]
                    if not any(m in json.dumps(a["parameters"]) for m in MINE)
                    and a["parameters"][:1] not in (["StompChain"], ["StompPts"])]


def popup_actions(src, text_expr):
    """número arcade sobre el objeto: centrado, por delante de todo."""
    return [act("Create", ["", "PtsPopup", f"{src}.X()", f"{src}.Y() - 12", ""]),
            act(BT_TEXT, ["PtsPopup", "=", text_expr]),
            act("SetX", ["PtsPopup", "=", f"{src}.X() + {src}.Width() / 2 - PtsPopup.Width() / 2"]),
            act("ChangePlan", ["PtsPopup", "=", "1000"]),
            act("ResetObjectTimer", ["PtsPopup", '"Pts"'])]


def popup_events():
    """estilo arcade: salta rápido y frena, titila blanco/dorado y
    parpadea antes de desaparecer (0.9 s en total)."""
    t = 'PtsPopup.ObjectTimerElapsedTime("Pts")'
    tick = f"mod(floor({t} * 15), 2)"
    return [
        ev([act("ObjectTimer", ["PtsPopup", '"Pts"', "0.25"], inverted=True)],
           [act("SetY", ["PtsPopup", "-", "64 * TimeDelta()"])]),
        {"type": "BuiltinCommonInstructions::ForEach", "object": "PtsPopup",
         "objectsToPick": "PtsPopup", "conditions": [], "actions": [],
         "events": [
             ev([act("BuiltinCommonInstructions::CompareNumbers", [tick, "=", "0"])],
                [act(BT_TINT, ["PtsPopup", f'"{WHITE}"'])]),
             ev([act("BuiltinCommonInstructions::CompareNumbers", [tick, "=", "1"])],
                [act(BT_TINT, ["PtsPopup", f'"{AMBER}"'])]),
             ev([act("ObjectTimer", ["PtsPopup", '"Pts"', "0.6"]),
                 act("BuiltinCommonInstructions::CompareNumbers", [tick, "=", "1"])],
                [act("Hide", ["PtsPopup"])]),
             ev([act("BuiltinCommonInstructions::CompareNumbers", [tick, "=", "0"])],
                [act("Show", ["PtsPopup", ""])]),
         ]},
        ev([act("ObjectTimer", ["PtsPopup", '"Pts"', "0.9"])], [act("Delete", ["PtsPopup", ""])]),
    ]


def set_var(lay, name, value=0):
    vs = lay.setdefault("variables", [])
    if not any(v["name"] == name for v in vs):
        vs.append({"name": name, "type": "number", "value": value})


def put_object(lay, obj):
    idx = {o["name"]: i for i, o in enumerate(lay["objects"])}
    if obj["name"] in idx:
        lay["objects"][idx[obj["name"]]] = obj
    else:
        lay["objects"].append(obj)
        fs = lay.get("objectsFolderStructure", {})
        if "children" in fs:
            fs["children"].append({"objectName": obj["name"]})


def drop_object(lay, name):
    lay["objects"] = [o for o in lay["objects"] if o["name"] != name]
    lay["instances"] = [i for i in lay["instances"] if i["name"] != name]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") != name]


def put_instances(lay, insts):
    names = {i["name"] for i in insts}
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in names] + insts


def replace_group(lay, events):
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({"type": "BuiltinCommonInstructions::Group", "name": GROUP,
                          "source": "", "creationTime": 0, "folded": True,
                          "color": {"b": 110, "g": 206, "r": 255},
                          "events": events})


def record_load_event():
    return ev([act("VarGlobal", ["RecordLoaded", "=", "0"])],
              [act("LireFichierExp", STORE + ["", "RecLoaded"]),
               act("ModVarGlobal", ["Record", "=",
                                    "max(GlobalVariable(Record), Variable(RecLoaded))"]),
               act("ModVarGlobal", ["RecordLoaded", "=", "1"])])


def wire_level(lay, antidotes):
    name = lay["name"]
    for v in ("LevelScore", "LevelBase", "AntiBonus", "NewRecord", "RecLoaded",
              "StompChain", "StompPts", "NotasBonus"):
        set_var(lay, v)

    # --- objetos / instancias del HUD ---
    drop_object(lay, "PuntajeText")
    score_txt = "PUNTOS 000000"
    put_object(lay, btext("HudScore", score_txt, AMBER))
    put_object(lay, btext("PtsPopup", "+100", AMBER))
    put_object(lay, btext("VictoryScore", "", WHITE, "center"))
    insts = [inst("HudScore", W - 8 - text_w(score_txt), 6, 30),
             inst("VictoryScore", 0, 172, 30)]
    if antidotes:
        icon = json.loads(json.dumps(next(o for o in lay["objects"] if o["name"] == "Antidoto")))
        icon["name"] = "HudAntiIcon"
        icon["behaviors"], icon["effects"], icon["variables"] = [], [], []
        put_object(lay, icon)
        put_object(lay, btext("HudAnti", "0/4", WHITE))
        insts += [inst("HudAntiIcon", 68, 4, 30), inst("HudAnti", 84, 6, 30)]
    if name == "Level3":
        boss_txt = "PACIENTE ZERO 3/3"
        put_object(lay, btext("BossHPText", boss_txt, RED))
        insts.append(inst("BossHPText", (W - text_w(boss_txt)) // 2, 6, 30))
        boss_ev = find_event(lay, lambda e: any(
            a["parameters"][:1] == ["BossHPText"] and a["type"]["value"] in ("TextObject::String", BT_TEXT)
            for a in e.get("actions", [])), "texto del jefe")
        for a in boss_ev["actions"]:
            if a["parameters"][:1] == ["BossHPText"]:
                a["type"]["value"] = BT_TEXT
                a["parameters"] = ["BossHPText", "=",
                                   '"PACIENTE ZERO " + ToString(Variable(BossHP)) + "/3"']
    put_instances(lay, insts)

    # --- corte viejo de Level1: reset en Once y PuntajeText ---
    lay["events"] = [e for e in lay["events"]
                     if not (e.get("type") == "BuiltinCommonInstructions::Standard"
                             and e.get("actions")
                             and all(any(m in json.dumps(a["parameters"]) for m in ("Puntaje", "PuntajeText"))
                                     for a in e["actions"]))]
    for e in walk(lay["events"]):
        strip_mine(e)

    # --- puntos en eventos existentes ---
    if name != "Level3":
        stomp = find_event(lay, lambda e: has_cond(e, "CollisionNP", "Player", "Zombies")
                           and has_cond(e, "NumberObjectVariable", "Zombies", "Infected", "=", "0"),
                           "stomp")
        k = next(i for i, a in enumerate(stomp["actions"]) if a["type"]["value"] == "Delete")
        # cadena de stomps sin tocar el piso: 100, 200, 400, 800, 1000, 1000...
        stomp["actions"][k:k] = \
            [act("ModVarScene", ["StompPts", "=", "min(1000, 100 * pow(2, Variable(StompChain)))"])] + \
            popup_actions("Zombies", "ToString(Variable(StompPts))") + \
            [act("ModVarScene", ["LevelScore", "+", "Variable(StompPts)"]),
             act("ModVarScene", ["StompChain", "+", "1"])]
        # el "boing" sube de tono con la cadena (1.0, 1.12, 1.24...)
        for a in stomp["actions"]:
            if a["type"]["value"] == "PlaySound" and "sfx_stomp" in a["parameters"][1]:
                a["parameters"][4] = "0.88 + min(Variable(StompChain), 5) * 0.12"
    if antidotes:
        pick = find_event(lay, lambda e: has_cond(e, "CollisionNP", "Player", "Antidoto"), "antídoto")
        k = next(i for i, a in enumerate(pick["actions"]) if a["type"]["value"] == "Delete")
        pick["actions"][k:k] = popup_actions("Antidoto", '"250"') + \
            [act("ModVarScene", ["LevelScore", "+", "250"])]
    # [R] después de ganar: devuelve lo sumado al ganar
    retry = find_event(lay, lambda e: has_cond(e, "KeyFromTextPressed", "", '"r"')
                       and has_cond(e, "VarScene", "Won", "=", "1"), "R tras ganar")
    retry["actions"].insert(0, act("ModVarGlobal", ["Puntaje", "-", "Variable(LevelScore)"]))

    # --- grupo de eventos nuevos ---
    # bonus por las 7 pruebas del brote (wire_notas.py): solo en la victoria
    # final, que es donde ya se pudieron juntar todas
    notas_bonus = []
    if name == FINAL_LEVEL:
        found = " + ".join(f"GlobalVariable(Nota{n})" for n in range(1, N_NOTAS + 1))
        notas_bonus = [
            ev([], [act("ModVarScene", ["NotasBonus", "=", "0"])]),
            ev([act("BuiltinCommonInstructions::CompareNumbers", [found, ">=", str(N_NOTAS)])],
               [act("ModVarScene", ["NotasBonus", "=", str(NOTAS_BONUS)]),
                act("ModVarScene", ["LevelScore", "+", str(NOTAS_BONUS)])])]
    total = "GlobalVariable(Puntaje)"
    shown = "GlobalVariable(Puntaje) + Variable(LevelScore) * (1 - Variable(Won))"
    victory = ev(
        [act("VarScene", ["Won", "=", "1"]), act("BuiltinCommonInstructions::Once", [])],
        [act("ModVarScene", ["LevelBase", "=", "Variable(LevelScore)"]),
         act("ModVarScene", ["LevelScore", "+", "1000 + Variable(Lives) * 500"]),
         act("ModVarScene", ["AntiBonus", "=", "0"]),
         act("ModVarScene", ["NewRecord", "=", "0"])],
        [
            ev([act("VarScene", ["Antidotes", ">=", "4"])],
               [act("ModVarScene", ["AntiBonus", "=", "1000"]),
                act("ModVarScene", ["LevelScore", "+", "1000"])]),
            *notas_bonus,
            ev([], [act("ModVarGlobal", ["Puntaje", "+", "Variable(LevelScore)"]),
                    act(BT_TEXT, ["VictoryScore", "=",
                                  '"NIVEL +" + ToString(Variable(LevelBase)) + NewLine() + '
                                  '"META +1000" + NewLine() + '
                                  '"VIDAS x" + ToString(Variable(Lives)) + " +" + ToString(Variable(Lives) * 500)'])]),
            ev([act("VarScene", ["AntiBonus", ">", "0"])],
               [act(BT_TEXT, ["VictoryScore", "+", 'NewLine() + "ANTÍDOTOS 4/4 +1000"'])]),
            ev([act("VarScene", ["NotasBonus", ">", "0"])],
               [act(BT_TEXT, ["VictoryScore", "+", f'NewLine() + "PRUEBAS {N_NOTAS}/{N_NOTAS} +{NOTAS_BONUS}"'])]),
            ev([act("VarGlobal", ["Puntaje", ">", "GlobalVariable(Record)"])],
               [act("ModVarGlobal", ["Record", "=", total]),
                act("EcrireFichierExp", STORE + ["GlobalVariable(Record)"]),
                act("ModVarScene", ["NewRecord", "=", "1"])]),
            ev([], [act(BT_TEXT, ["VictoryScore", "+", f'NewLine() + "TOTAL " + {pad6(total)}'])]),
            ev([act("VarScene", ["NewRecord", "=", "1"])],
               [act(BT_TEXT, ["VictoryScore", "+", 'NewLine() + "¡NUEVO RÉCORD!"'])]),
            ev([], [act("SetX", ["VictoryScore", "=", "240 - VictoryScore.Width() / 2"]),
                    act("Show", ["VictoryScore", ""])]),
        ])
    hud = [act(BT_TEXT, ["HudScore", "=", f'"PUNTOS " + {pad6(shown)}'])]
    subs = []
    if antidotes:
        hud.append(act(BT_TEXT, ["HudAnti", "=", 'ToString(Variable(Antidotes)) + "/4"']))
        subs = [ev([act("VarScene", ["Antidotes", ">=", "4"])], [act(BT_TINT, ["HudAnti", f'"{TOXIC}"'])]),
                ev([act("VarScene", ["Antidotes", "<", "4"])], [act(BT_TINT, ["HudAnti", f'"{WHITE}"'])])]
    replace_group(lay, [
        comment("Puntaje: lo del nivel va a LevelScore y pasa al global Puntaje al "
                "ganar (+1000 meta, +500 por vida, +1000 con 4/4 antídotos). "
                "Récord en storage PacienteZero/record. Generado por wire_score_hud.py."),
        record_load_event(),
        ev([act("BuiltinCommonInstructions::Once", [])], [act("Hide", ["VictoryScore"])]),
        victory,
        ev([], hud, subs or None),
        ev([act("PlatformBehavior::IsOnFloor", ["Player", "PlatformerObject"])],
           [act("ModVarScene", ["StompChain", "=", "0"])]),
        *popup_events(),
    ])


def wire_menu(lay):
    set_var(lay, "RecLoaded")
    rec_txt = "RÉCORD 000000"
    put_object(lay, btext("MenuRecord", rec_txt, AMBER))
    put_instances(lay, [inst("MenuRecord", W - 8 - text_w(rec_txt), 6, 40, layer="")])
    # "Jugar" arranca la partida en 0
    jugar = find_event(lay, lambda e: any(a["type"]["value"] == "Scene" and a["parameters"][1] == '"Tutorial"'
                                          for a in e.get("actions", [])), "Jugar")
    strip_mine(jugar)
    jugar["actions"].insert(0, act("ModVarGlobal", ["Puntaje", "=", "0"]))
    replace_group(lay, [
        comment("Récord guardado (storage PacienteZero/record). Generado por wire_score_hud.py."),
        record_load_event(),
        ev([], [act(BT_TEXT, ["MenuRecord", "=", f'"RÉCORD " + {pad6("GlobalVariable(Record)")}'])]),
        ev([act("VarGlobal", ["Record", "<=", "0"])], [act("Hide", ["MenuRecord"])]),
        ev([act("VarGlobal", ["Record", ">", "0"])], [act("Show", ["MenuRecord", ""])]),
    ])


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))

    res = g["resources"]["resources"]
    res[:] = [r for r in res if r["name"] not in (FONT_IMG, FONT_FNT)]
    res += [{"file": f"assets/UI/{FONT_IMG}", "kind": "image", "metadata": "", "name": FONT_IMG,
             "smoothed": False, "userAdded": True},
            {"file": f"assets/UI/{FONT_FNT}", "kind": "bitmapFont", "metadata": "", "name": FONT_FNT,
             "userAdded": True}]

    gv = g.setdefault("variables", [])
    for v in ("Puntaje", "Record", "RecordLoaded"):
        if not any(x["name"] == v for x in gv):
            gv.append({"name": v, "type": "number", "value": 0})

    lays = {l["name"]: l for l in g["layouts"]}
    for name in LEVELS:
        lay = lays[name]
        n_anti = sum(1 for i in lay["instances"] if i["name"] == "Antidoto")
        wire_level(lay, antidotes=n_anti > 0)
        print(f"{name}: HUD + puntaje ({n_anti} antídotos)")
    wire_menu(lays["MainMenu"])
    print("MainMenu: récord + reset en Jugar")

    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
