#!/usr/bin/env python3
"""
wire_top5.py — tabla de los 5 mejores puntajes con iniciales de 3 letras,
como en los arcades (decidido el 25/10).

Cuándo se anota: la partida termina al volver al MainMenu (victoria final,
Game Over → ESC, o M desde la pausa). El puntaje que cuenta es el último que
mostró el HUD (global PuntajeCorte = Puntaje + LevelScore del nivel en
curso, se actualiza cada frame en L1/L2/L3), así coincide con lo que vio el
jugador. Reintentar con R sigue siendo la misma partida (no anota). "Jugar"
marca PartidaViva = 1; el menú la consume una sola vez.

Si el puntaje entra en el top 5, el panel del menú pasa a "INGRESÁ TUS
INICIALES": ↑↓ (W/S) cambia la letra, → / D / Enter / J / Espacio pasa a la
siguiente, ← / A / Backspace vuelve. Con la tercera se guarda, la fila
titila 2.5 s y vuelve el menú. Arranca con las últimas iniciales usadas.

La tabla "TOP 5" va arriba a la izquierda del menú (arriba a la derecha está
la Luna) y reemplaza al "RÉCORD 000000" de wire_score_hud.py: el puesto 1 es
el récord. El global Record (el de "¡NUEVO RÉCORD!" en la victoria) se
mantiene igual al puesto 1.

Storage "PacienteZero": top_p1..5 (puntos), top_n1..5 (iniciales), ini
(últimas iniciales), record. Si había un récord viejo sin iniciales, entra
como "---".

Idempotente: grupo propio por escena + una acción en el evento "Jugar"
(se quita antes de volver a ponerla). Correr DESPUÉS de wire_score_hud.py.
Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_top5.py    (desde la raíz del repo)
"""
import datetime
import json
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado
from wire_score_hud import (AMBER, BT_TEXT, BT_TINT, GAME, LINE_H, W, WHITE, act,
                            btext, comment, ev, find_event, inst, pad6, put_instances,
                            put_object, set_var)

GROUP = "Top 5 con iniciales (wire_top5.py)"
LEVELS = ["Level1", "Level2", "Level3"]
N = 5
ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
STORE = '"PacienteZero"'
DIM = "150;156;170"
MOSTRAR_GUARDADO = 2.5   # s que titila la fila nueva antes de volver al menú

# panel del menú (MenuPanel, 172x92 en 154,100): todo centrado en x 240
PANEL_Y = 100
LETRA_X = [210, 234, 258]   # 3 letras a escala 2 (12 px de avance)
LETRA_Y = PANEL_Y + 36

KEYS_UP = ['"Up"', '"w"']
KEYS_DOWN = ['"Down"', '"s"']
KEYS_NEXT = ['"Right"', '"d"', '"Return"', '"Space"', '"j"']
KEYS_PREV = ['"Left"', '"a"', '"Back"']
KEYS_SALIR = ['"Return"', '"Space"', '"j"', '"Escape"']


def key(k):
    return act("KeyFromTextJustPressed", ["", k])


def var(name, op, val):
    return act("VarScene", [name, op, val])


def gvar(name, op, val):
    return act("VarGlobal", [name, op, val])


def cmp(a, op, b):
    return act("BuiltinCommonInstructions::CompareNumbers", [a, op, b])


def set_scene(name, op, val):
    return act("ModVarScene", [name, op, val])


def set_global(name, op, val):
    return act("ModVarGlobal", [name, op, val])


def set_global_str(name, op, val):
    return act("ModVarGlobalTxt", [name, op, val])


def sonido(pitch, vol="0.5"):
    return act("PlaySound", ["", "sfx_select.wav", "no", f"GlobalVariable(SfxVolume) * {vol}", pitch])


def letra(i):
    return f'SubStr("{ABC}", Variable(IniL{i}), 1)'


INICIALES = " + ".join(letra(i) for i in (1, 2, 3))
BLINK = "mod(floor(TimeFromStart() * 4), 2)"


def global_var(g, name, kind="number"):
    gv = g.setdefault("variables", [])
    if not any(v["name"] == name for v in gv):
        gv.append({"name": name, "type": kind, "value": "" if kind == "string" else 0})


def replace_group(lay, events):
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({"type": "BuiltinCommonInstructions::Group", "name": GROUP,
                          "source": "", "creationTime": 0, "folded": True,
                          "color": {"b": 110, "g": 206, "r": 255}, "events": events})


def wire_level(lay):
    replace_group(lay, [
        comment("Último puntaje que mostró el HUD: es el que cuenta para el top 5 si la "
                "partida termina acá (wire_top5.py)."),
        ev([], [set_global("PuntajeCorte", "=",
                           "GlobalVariable(Puntaje) + Variable(LevelScore) * (1 - Variable(Won))")]),
    ])


def carga_events():
    """lee la tabla del navegador una vez por sesión."""
    acts = []
    for i in range(1, N + 1):
        acts += [set_scene("IniTmpP", "=", "0"),
                 act("LireFichierExp", [STORE, f'"top_p{i}"', "", "IniTmpP"]),
                 set_global(f"TopP{i}", "=", "Variable(IniTmpP)"),
                 act("ModVarSceneTxt", ["IniTmpN", "=", '"---"']),
                 act("LireFichierTxt", [STORE, f'"top_n{i}"', "", "IniTmpN"]),
                 set_global_str(f"TopN{i}", "=", "VariableString(IniTmpN)")]
    acts += [act("ModVarSceneTxt", ["IniTmpN", "=", '""']),
             act("LireFichierTxt", [STORE, '"ini"', "", "IniTmpN"]),
             set_global_str("TopIni", "=", "VariableString(IniTmpN)"),
             set_global("TopLoaded", "=", "1")]
    return [
        ev([gvar("TopLoaded", "=", "0")], acts, [
            # récord de antes del top 5 (sin iniciales)
            ev([gvar("TopP1", "<=", "0"), gvar("Record", ">", "0")],
               [set_global("TopP1", "=", "GlobalVariable(Record)"),
                set_global_str("TopN1", "=", '"---"')]),
        ]),
        ev([], [set_global("Record", "=", "max(GlobalVariable(Record), GlobalVariable(TopP1))")]),
    ]


def entrada_events():
    """al llegar al menú con una partida terminada: ¿entra en el top 5?"""
    p = "GlobalVariable(PuntajeCorte)"
    pos = [set_scene("IniPos", "=", str(N))]
    pos_evs = [ev([gvar(f"TopP{i}", "<", p)], [set_scene("IniPos", "=", str(i))])
               for i in range(N - 1, 0, -1)]
    # corre para abajo los que quedan detrás (de abajo hacia arriba)
    corre = [ev([var("IniPos", "<=", str(i - 1))],
                [set_global(f"TopP{i}", "=", f"GlobalVariable(TopP{i - 1})"),
                 set_global_str(f"TopN{i}", "=", f"GlobalVariableString(TopN{i - 1})")])
             for i in range(N, 1, -1)]
    pone = [ev([var("IniPos", "=", str(i))], [set_global(f"TopP{i}", "=", p)]) for i in range(1, N + 1)]
    ultimas = [set_scene(f"IniL{i}", "=",
                         f'max(0, StrFind("{ABC}", SubStr(GlobalVariableString(TopIni), {i - 1}, 1)))')
               for i in (1, 2, 3)]
    entra = ev([gvar("PuntajeCorte", ">", "GlobalVariable(TopP5)"), gvar("PuntajeCorte", ">", "0")],
               pos + ultimas + [set_scene("IniSlot", "=", "0"),
                                set_scene("IniFase", "=", "1"),
                                set_global("SettingsOpen", "=", "2")],
               pos_evs + corre + pone)
    return [ev([act("BuiltinCommonInstructions::Once", []), gvar("PartidaViva", "=", "1")],
               [set_global("PartidaViva", "=", "0")], [entra])]


def teclado_events():
    f1 = var("IniFase", "=", "1")
    evs = [ev([f1, var("IniSlot", "=", str(k))], [set_scene("IniCur", "=", f"Variable(IniL{k + 1})")])
           for k in range(3)]
    evs += [ev([f1, key(k)], [set_scene("IniCur", "=", "mod(Variable(IniCur) + 1, 26)"), sonido("1.3")])
            for k in KEYS_UP]
    evs += [ev([f1, key(k)], [set_scene("IniCur", "=", "mod(Variable(IniCur) + 25, 26)"), sonido("1.1")])
            for k in KEYS_DOWN]
    evs += [ev([f1, var("IniSlot", "=", str(k))], [set_scene(f"IniL{k + 1}", "=", "Variable(IniCur)")])
            for k in range(3)]
    evs += [ev([f1, key(k)], [set_scene("IniSlot", "+", "1"), sonido("1", "1")]) for k in KEYS_NEXT]
    evs += [ev([f1, key(k)], [set_scene("IniSlot", "=", "max(0, Variable(IniSlot) - 1)"), sonido("0.9")])
            for k in KEYS_PREV]
    # la fila nueva de la tabla muestra las letras mientras se eligen
    evs += [ev([var("IniFase", ">=", "1"), var("IniPos", "=", str(i))],
               [set_global_str(f"TopN{i}", "=", INICIALES)]) for i in range(1, N + 1)]
    # tercera letra confirmada: guardar todo
    guardar = [act("EcrireFichierExp", [STORE, f'"top_p{i}"', f"GlobalVariable(TopP{i})"])
               for i in range(1, N + 1)]
    guardar += [act("EcrireFichierTxt", [STORE, f'"top_n{i}"', f"GlobalVariableString(TopN{i})"])
                for i in range(1, N + 1)]
    guardar += [set_global_str("TopIni", "=", INICIALES),
                act("EcrireFichierTxt", [STORE, '"ini"', "GlobalVariableString(TopIni)"]),
                set_global("Record", "=", "max(GlobalVariable(Record), GlobalVariable(TopP1))"),
                act("EcrireFichierExp", [STORE, '"record"', "GlobalVariable(Record)"]),
                set_scene("IniFase", "=", "2"),
                set_scene("IniT", "=", "0"),
                act("PlaySound", ["", "sfx_pickup.wav", "no", "GlobalVariable(SfxVolume)", "1"])]
    evs.append(ev([f1, var("IniSlot", ">=", "3")], guardar))
    # guardado: la fila titila un rato y vuelve el menú (o antes con una tecla)
    f2 = var("IniFase", "=", "2")
    volver = [set_scene("IniFase", "=", "0"), set_global("SettingsOpen", "=", "0")]
    evs.append(ev([f2], [set_scene("IniT", "+", "TimeDelta()")]))
    evs.append(ev([f2, var("IniT", ">=", str(MOSTRAR_GUARDADO))], volver))
    evs += [ev([f2, var("IniT", ">=", "0.3"), key(k)], volver) for k in KEYS_SALIR]
    return evs


def pantalla_events():
    ini_objs = ["IniTitle", "IniMsg", "IniScore", "IniHint", "IniCursor"] + [f"IniL{i}Txt" for i in (1, 2, 3)]
    centrar = lambda o: act("SetX", [o, "=", f"{W // 2} - {o}.Width() / 2"])
    evs = [
        ev([var("IniFase", ">", "0")],
           [act("Hide", ["MenuUI"]), act("Hide", ["OptionsUI"])] + [act("Show", [o, ""]) for o in ini_objs]),
        ev([var("IniFase", "=", "0")], [act("Hide", [o]) for o in ini_objs]),
        ev([var("IniFase", ">", "0")],
           [act(BT_TEXT, ["IniScore", "=", f'"PUNTOS " + {pad6("GlobalVariable(PuntajeCorte)")}']),
            act(BT_TEXT, ["IniHint", "=", '"↑↓ LETRA   ← → MOVER   ENTER: ACEPTAR"'])]
           + [act(BT_TEXT, [f"IniL{i}Txt", "=", letra(i)]) for i in (1, 2, 3)]
           + [centrar(o) for o in ("IniTitle", "IniMsg", "IniScore", "IniHint")]),
        ev([var("IniPos", "=", "1")], [act(BT_TEXT, ["IniTitle", "=", '"¡NUEVO RÉCORD!"'])]),
        ev([var("IniPos", ">", "1")],
           [act(BT_TEXT, ["IniTitle", "=", '"¡PUESTO " + ToString(Variable(IniPos)) + " DEL TOP 5!"'])]),
        ev([var("IniFase", "=", "1")], [act(BT_TEXT, ["IniMsg", "=", '"INGRESÁ TUS INICIALES"'])]),
        ev([var("IniFase", "=", "2")], [act(BT_TEXT, ["IniMsg", "=", '"¡GUARDADO!"']), act("Hide", ["IniCursor"])]),
    ]
    # letra elegida en ámbar con un guion que titila debajo
    for k in range(3):
        evs.append(ev([var("IniSlot", "=", str(k))],
                      [act(BT_TINT, [f"IniL{k + 1}Txt", f'"{AMBER}"']),
                       act("SetX", ["IniCursor", "=", str(LETRA_X[k])])]))
        evs.append(ev([var("IniSlot", "!=", str(k))], [act(BT_TINT, [f"IniL{k + 1}Txt", f'"{WHITE}"'])]))
    evs.append(ev([cmp(BLINK, "=", "1")], [act("Hide", ["IniCursor"])]))
    return evs


def tabla_events():
    objs = ["TopTitle"] + [f"TopRow{i}" for i in range(1, N + 1)]
    evs = [
        ev([gvar("TopP1", ">", "0")], [act("Show", [o, ""]) for o in objs]),
        ev([gvar("TopP1", "<=", "0"), var("IniFase", "=", "0")], [act("Hide", [o]) for o in objs]),
    ]
    for i in range(1, N + 1):
        row = f"TopRow{i}"
        evs += [
            ev([gvar(f"TopP{i}", ">", "0")],
               [act(BT_TEXT, [row, "=", f'"{i} " + GlobalVariableString(TopN{i}) + " " + '
                                        f'{pad6(f"GlobalVariable(TopP{i})")}']),
                act(BT_TINT, [row, f'"{WHITE}"'])]),
            ev([gvar(f"TopP{i}", "<=", "0")],
               [act(BT_TEXT, [row, "=", f'"{i} --- ------"']), act(BT_TINT, [row, f'"{DIM}"'])]),
            # la fila nueva titila en ámbar mientras se escribe y al guardar
            ev([var("IniFase", ">", "0"), var("IniPos", "=", str(i)), cmp(BLINK, "=", "0")],
               [act(BT_TINT, [row, f'"{AMBER}"'])]),
        ]
    return evs


def wire_menu(lay):
    for v in ("IniFase", "IniPos", "IniSlot", "IniCur", "IniL1", "IniL2", "IniL3", "IniT", "IniTmpP"):
        set_var(lay, v)
    vs = lay.setdefault("variables", [])
    if not any(v["name"] == "IniTmpN" for v in vs):
        vs.append({"name": "IniTmpN", "type": "string", "value": ""})

    # objetos: tabla arriba a la izquierda, pantalla de iniciales sobre el panel
    put_object(lay, btext("TopTitle", "TOP 5", AMBER))
    insts = [inst("TopTitle", 8, 6, 40, layer="")]
    for i in range(1, N + 1):
        put_object(lay, btext(f"TopRow{i}", f"{i} --- ------", WHITE))
        insts.append(inst(f"TopRow{i}", 8, 6 + LINE_H * i, 40, layer=""))
    for name, y, tint in (("IniTitle", PANEL_Y + 6, AMBER), ("IniMsg", PANEL_Y + 20, WHITE),
                          ("IniScore", PANEL_Y + 72, WHITE), ("IniHint", 256, WHITE)):
        put_object(lay, btext(name, "", tint))
        insts.append(inst(name, 0, y, 41, layer=""))
    for i, x in enumerate(LETRA_X, start=1):
        o = btext(f"IniL{i}Txt", "A", WHITE)
        o["content"]["scale"] = 2
        put_object(lay, o)
        insts.append(inst(f"IniL{i}Txt", x, LETRA_Y, 41, layer=""))
    cur = btext("IniCursor", "-", AMBER)
    cur["content"]["scale"] = 2
    put_object(lay, cur)
    insts.append(inst("IniCursor", LETRA_X[0], LETRA_Y + 16, 41, layer=""))
    put_instances(lay, insts)

    # "Jugar" abre una partida nueva
    jugar = find_event(lay, lambda e: any(a["type"]["value"] == "Scene" and a["parameters"][1] == '"Tutorial"'
                                          for a in e.get("actions", [])), "Jugar")
    jugar["actions"] = [a for a in jugar["actions"]
                        if a["parameters"][:1] not in (["PartidaViva"], ["PuntajeCorte"])]
    jugar["actions"][:0] = [set_global("PartidaViva", "=", "1"), set_global("PuntajeCorte", "=", "0")]

    replace_group(lay, [
        comment("Top 5 con iniciales: carga del navegador, entrada al terminar la partida, "
                "teclado, pantalla y tabla. Generado por wire_top5.py."),
        *carga_events(),
        *entrada_events(),
        *teclado_events(),
        *pantalla_events(),
        *tabla_events(),
    ])


def main():
    asegurar_gdevelop_cerrado()
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))

    for v in ("TopLoaded", "PartidaViva", "PuntajeCorte") + tuple(f"TopP{i}" for i in range(1, N + 1)):
        global_var(g, v)
    for v in ("TopIni",) + tuple(f"TopN{i}" for i in range(1, N + 1)):
        global_var(g, v, "string")

    lays = {l["name"]: l for l in g["layouts"]}
    for name in LEVELS:
        wire_level(lays[name])
        print(f"{name}: PuntajeCorte")
    wire_menu(lays["MainMenu"])
    print("MainMenu: tabla TOP 5 + iniciales")

    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
