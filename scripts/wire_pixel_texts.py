#!/usr/bin/env python3
"""
wire_pixel_texts.py — los últimos textos con fuente suavizada (TextObject)
pasan a la fuente pixel del menú/HUD (BitmapText, gen_font.py) y se
reescriben.

  - Tutorial: IntroText (ámbar) + los 7 hints (blanco) + el contador
    TutAntiText arriba a la derecha como el HUD ("ANTÍDOTOS n/2", verde con
    2/2). Mismos nombres de objeto: el grupo TutHints y los eventos de
    zona no cambian.
  - Level1/2/3: GameOverText y VictoryText quedan como TÍTULO grande
    (escala 2, rojo / ámbar) y los controles pasan a un objeto nuevo
    (GameOverHelp / VictoryHelp, escala 1, blanco) que se muestra y oculta
    junto con el título, sobre un velo oscuro (EndDim, la imagen de
    PauseDim). Todo centrado; el desglose VictoryScore de wire_score_hud.py
    sigue en y=172, debajo.

Idempotente. Si se corre wire_levels23.py --force o wire_tutorial_v2.py,
volver a correr este script (después de wire_score_hud.py).

Requiere:  python3 scripts/gen_font.py   (glifos [ ] ( ) , ? ¿ ← → ↑ ↓)
Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_pixel_texts.py [ruta/game.json]
"""
import datetime
import json
import shutil
import sys

from wire_score_hud import (AMBER, BT_TEXT, BT_TINT, FONT_FNT, RED, TOXIC, W, WHITE, act,
                            btext, ev, find_event, inst, put_instances,
                            put_object, walk)

GAME = sys.argv[1] if len(sys.argv) > 1 else "game/game.json"
CW, LH = 6, 13          # avance por carácter y alto de línea de hud_font.fnt

TUTORIAL = {
    # nombre: (texto, tint, x, y)
    "IntroText": ("BUENOS AIRES CAYÓ ANTE EL VIRUS ZOMBIE.\n"
                  "LIO ES INMUNE: ¡LLEVALO HASTA EL ORIGEN!", AMBER, 12, 24),
    "HintMove": ("← → O A / D: CAMINAR", WHITE, 12, 58),
    "HintJump": ("ESPACIO O J: SALTAR\nAGARRÁ EL ANTÍDOTO DE ARRIBA", WHITE, 12, 24),
    "HintAnti": ("JUNTÁ LOS 4 ANTÍDOTOS DE CADA NIVEL\nY GANÁS UNA VIDA EXTRA", WHITE, 12, 24),
    "HintGlide": ("¡UNA MOCHILA DE REPARTIDOR! CON ELLA PODÉS PLANEAR:\n"
                  "MANTENÉ ESPACIO O J MIENTRAS CAÉS", WHITE, 12, 24),
    "HintClimb": ("↑ ↓ O W / S: TREPAR EL POSTE\nARRIBA HAY OTRO ANTÍDOTO", WHITE, 12, 24),
    "HintStomp": ("CAELES ENCIMA A LOS ZOMBIES PARA ELIMINARLOS.\n"
                  "DE COSTADO TE LASTIMAN (ACÁ NO, ES PRÁCTICA)", WHITE, 12, 24),
    "HintExit": ("ESC O P: PAUSA\nMETETE EN EL CARTEL PARA IR AL NIVEL 1", WHITE, 12, 24),
}
TUT_ANTI = "ANTÍDOTOS 0/2"

GAME_OVER = ("GAME OVER", "[R] O CLICK: REINTENTAR    [ESC]: MENÚ")
VICTORY = {
    "Level1": ("¡LLEGASTE AL LABORATORIO!",
               "[ESPACIO] O CLICK: NIVEL 2\n[R]: REPETIR    [ESC]: MENÚ"),
    "Level2": ("¡LLEGASTE AL CORAZÓN DEL LAB!",
               "[ESPACIO] O CLICK: NIVEL 3\n[R]: REPETIR    [ESC]: MENÚ"),
    "Level3": ("¡DERROTASTE AL PACIENTE ZERO!",
               "BUENOS AIRES ESTÁ A SALVO\n[ESPACIO], CLICK O [ESC]: MENÚ    [R]: REPETIR"),
}


def font_chars():
    with open(f"game/assets/UI/{FONT_FNT}", encoding="utf-8") as f:
        return {chr(int(tok[3:])) for line in f for tok in line.split() if tok.startswith("id=")
                and line.startswith("char ")}


def check(text, chars):
    missing = set(text.replace("\n", "")) - chars
    assert not missing, f"faltan glifos en {FONT_FNT}: {missing!r} (correr gen_font.py)"


def size(text, scale=1):
    lines = text.split("\n")
    return (max(len(s) for s in lines) * CW + 2) * scale, len(lines) * LH * scale


def btext_s(name, text, tint, align="left", scale=1):
    o = btext(name, text, tint, align)
    o["content"]["scale"] = scale
    return o


def centered(name, text, y, scale=1, z=30):
    return inst(name, (W - size(text, scale)[0]) // 2, y, z)


def wire_tutorial(lay, chars):
    for name, (text, tint, _, _) in TUTORIAL.items():
        check(text, chars)
        put_object(lay, btext_s(name, text, tint))
    put_object(lay, btext_s("TutAntiText", TUT_ANTI, WHITE))
    old = {i["name"]: i for i in lay["instances"] if i["name"] in TUTORIAL or i["name"] == "TutAntiText"}
    insts = [inst(n, x, y, old[n]["zOrder"] if n in old else 30) for n, (_, _, x, y) in TUTORIAL.items()]
    insts.append(inst("TutAntiText", W - 8 - size(TUT_ANTI)[0], 6, 30))
    put_instances(lay, insts)

    cnt = find_event(lay, lambda e: any(a["parameters"][:1] == ["TutAntiText"]
                                        and a["type"]["value"] in ("TextObject::String", BT_TEXT)
                                        for a in e.get("actions", [])), "contador del tutorial")
    cnt["actions"] = [a for a in cnt["actions"] if a["parameters"][:1] != ["TutAntiText"]]
    cnt["actions"].append(act(BT_TEXT, ["TutAntiText", "=",
                                        '"ANTÍDOTOS " + ToString(Variable(Antidotes)) + "/2"']))
    cnt["events"] = [ev([act("VarScene", ["Antidotes", ">=", "2"])],
                        [act(BT_TINT, ["TutAntiText", f'"{TOXIC}"'])])]


def follow(lay, title, helper):
    """cada Show/Hide del título también muestra/oculta el objeto de ayuda."""
    for e in walk(lay["events"]):
        acts = e.get("actions", [])
        acts[:] = [a for a in acts if a["parameters"][:1] != [helper]]
        i = 0
        while i < len(acts):
            a = acts[i]
            if a["type"]["value"] in ("Show", "Hide") and a["parameters"][:1] == [title]:
                acts.insert(i + 1, act(a["type"]["value"], [helper] + a["parameters"][1:]))
                i += 1
            i += 1


def wire_level(lay, chars):
    name = lay["name"]
    vtitle, vhelp = VICTORY[name]
    gtitle, ghelp = GAME_OVER
    for t in (vtitle, vhelp, gtitle, ghelp):
        check(t, chars)
    put_object(lay, btext_s("VictoryText", vtitle, AMBER, "center", 2))
    put_object(lay, btext_s("VictoryHelp", vhelp, WHITE, "center"))
    put_object(lay, btext_s("GameOverText", gtitle, RED, "center", 2))
    put_object(lay, btext_s("GameOverHelp", ghelp, WHITE, "center"))
    # título grande, controles abajo y, en la victoria, el desglose en y=172
    put_instances(lay, [centered("VictoryText", vtitle, 100, 2),
                        centered("VictoryHelp", vhelp, 132),
                        centered("GameOverText", gtitle, 104, 2),
                        centered("GameOverHelp", ghelp, 138)])
    # velo oscuro detrás (misma imagen que PauseDim): el texto no se pierde
    # contra el fondo; queda por debajo del HUD y de los carteles (z 30)
    dim = json.loads(json.dumps(next(o for o in lay["objects"] if o["name"] == "PauseDim")))
    dim["name"] = "EndDim"
    put_object(lay, dim)
    d = inst("EndDim", 0, 0, 29)
    d.update(customSize=True, width=W, height=270)
    put_instances(lay, [d])
    follow(lay, "VictoryText", "VictoryHelp")
    follow(lay, "GameOverText", "GameOverHelp")
    for e in walk(lay["events"]):
        acts = e.get("actions", [])
        acts[:] = [a for a in acts if a["parameters"][:1] != ["EndDim"]]
        if any(a["type"]["value"] in ("Show", "Hide") and a["parameters"][:1] in (["VictoryText"], ["GameOverText"])
               for a in acts):
            kind = next(a["type"]["value"] for a in acts
                        if a["parameters"][:1] in (["VictoryText"], ["GameOverText"]))
            acts.append(act(kind, ["EndDim", ""] if kind == "Show" else ["EndDim"]))
    # los Help son nuevos: tienen que arrancar ocultos como sus títulos
    for title, helper in (("VictoryText", "VictoryHelp"), ("GameOverText", "GameOverHelp")):
        hides = [a for e in walk(lay["events"]) for a in e.get("actions", [])
                 if a["type"]["value"] == "Hide" and a["parameters"][:1] == [helper]]
        assert hides, f"{name}: no encontré el Hide inicial de {title}"


def main():
    chars = font_chars()
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    lays = {l["name"]: l for l in g["layouts"]}
    wire_tutorial(lays["Tutorial"], chars)
    print("Tutorial: intro + 7 hints + contador en fuente pixel")
    for name in VICTORY:
        wire_level(lays[name], chars)
        print(f"{name}: carteles de victoria y Game Over en fuente pixel")
    left = [(l["name"], o["name"]) for l in g["layouts"] for o in l["objects"]
            if o["type"] == "TextObject::Text"]
    print("TextObject que quedan:", left or "ninguno")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
