#!/usr/bin/env python3
"""
wire_main_menu_v2.py — rediseño visual del MainMenu con la estética del juego.

Antes: texto blanco sobre fondo liso. Ahora es una escena "runner" de noche:
  - cielo con luna enferma y bruma verde (gen_menu_ui.py),
  - skyline de Buenos Aires (city_far / city_near) con parallax,
    obelisco de fondo, vereda y faroles que se desplazan,
  - Lio corriendo y la horda (hincha, policía, médico, zombie F)
    persiguiéndolo, virus flotando en el cielo,
  - logo pixel-art y panel "cinta de cuarentena" con JUGAR / OPCIONES /
    SALIR navegable (^ v / W S) y un virus como cursor,
  - opciones con barras de volumen (11 estados, sprites) en vez de texto.

Se conserva la lógica que ya existía: estado único GLOBAL SettingsOpen,
visibilidad declarativa por grupos MenuUI / OptionsUI, música del menú,
atajos (ENTER/ESPACIO/J juega, O opciones, ESC sale/vuelve) y el Link a la
hoja externa SettingsControls (volumen compartido con la pausa de Level1).

Requiere haber corrido antes:  python3 scripts/gen_menu_ui.py
Edita game/game.json (backup .bak-<ts>, idempotente: reconstruye MainMenu
entero). GDevelop tiene que estar CERRADO.
Uso:  python3 scripts/wire_main_menu_v2.py [--preview]   (desde la raíz)
      --preview no toca el JSON: compone la escena con PIL en
      game/assets/Menu/_preview_{menu,opciones}.png para revisar el layout.
"""
import copy
import datetime
import json
import os
import shutil
import sys

GAME = "game/game.json"
MENU_DIR = "assets/Menu"
W, H = 480, 270

# --- layout (una sola fuente para el JSON y el preview) ---
PANEL = (154, 100, 172, 92)            # x, y, w, h
ITEM_Y0, ITEM_DY = 114, 23             # JUGAR / OPCIONES / SALIR
ITEMS = [("MMJugar", "jugar", 62), ("MMOpciones", "opciones", 98), ("MMSalir", "salir", 62)]
GROUND_Y = 238
HORDE = [("MenuZHin", "HordaZombieHin", 40), ("MenuZPol", "HordaZombiePol", 88),
         ("MenuZMed", "HordaZombieMed", 136), ("MenuZF", "ZombieF", 186)]
LIO_X = 318

MENU_IMAGES = (["menu_sky.png", "menu_logo.png", "menu_sub.png", "menu_panel.png",
                "menu_opt_title.png", "menu_opt_music.png", "menu_opt_sfx.png",
                "menu_hint.png", "menu_opt_hint.png"]
               + [f"menu_{k}_{s}.png" for _, k, _ in ITEMS for s in "ns"]
               + [f"menu_bar_{i}.png" for i in range(11)])

MENU_UI = ["MMJugar", "MMOpciones", "MMSalir", "MenuCursor", "MMHint"]
OPTIONS_UI = ["OptTitle", "OptMusicLbl", "OptSfxLbl", "OptMusicBar", "OptSfxBar", "OptHint"]


# ---------- helpers de JSON (mismo formato que los otros wire_*.py) ----------
def cond(t, params, **extra):
    d = {"type": {"value": t}, "parameters": params}
    d.update(extra)
    return d


act = cond


def std(conds, acts, sub=None):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}
    if sub:
        e["events"] = sub
    return e


def comment(txt):
    return {"type": "BuiltinCommonInstructions::Comment",
            "color": {"b": 0, "g": 0, "r": 0, "textB": 0, "textG": 0, "textR": 0},
            "comment": txt}


def any_key(*keys):
    if len(keys) == 1:
        return cond("KeyFromTextJustPressed", ["", f'"{keys[0]}"'])
    return cond("BuiltinCommonInstructions::Or", [],
                subInstructions=[cond("KeyFromTextJustPressed", ["", f'"{k}"']) for k in keys])


def frame(img):
    return {"hasCustomCollisionMask": False, "image": img, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def anim(name, imgs, dt=0.1, loop=True):
    return {"name": name, "useMultipleDirections": False,
            "directions": [{"looping": loop, "timeBetweenFrames": dt,
                            "sprites": [frame(i) for i in imgs]}]}


def sprite(name, anims):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False, "variables": [],
            "effects": [], "behaviors": [], "animations": anims}


def tiled(name, texture, w, h):
    return {"assetStoreId": "", "height": h, "name": name, "texture": texture,
            "type": "TiledSpriteObject::TiledSprite", "width": w,
            "variables": [], "effects": [], "behaviors": []}


def inst(name, x, y, z, w=0, h=0):
    return {"angle": 0, "customSize": bool(w), "height": h, "layer": "", "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def sel_is(n):
    return cond("VarScene", ["MenuSel", "=", str(n)])


SETTINGS_CLOSED = cond("VarGlobal", ["SettingsOpen", "=", "0"])
SFX = "GlobalVariable(SfxVolume)"


# ---------- escena ----------
def build_objects(d):
    level1 = next(l for l in d["layouts"] if l["name"] == "Level1")
    by_name = {o["name"]: o for o in level1["objects"]}

    def reuse(new_name, src_name, anim_name):
        """copia las animaciones de un objeto de Level1 (mismas imágenes), sin behaviors."""
        src = by_name[src_name]
        a = next(x for x in src["animations"] if x["name"] == anim_name)
        return sprite(new_name, [copy.deepcopy(a)])

    virus_frames = [f"virus_{i}.png" for i in range(1, 7)]
    objs = [
        sprite("MenuSky", [anim("Idle", ["menu_sky.png"])]),
        tiled("MenuCityFar", "city_far.png", W, 70),
        tiled("MenuCityNear", "city_near.png", W, 96),
        sprite("MenuObelisco", [anim("Idle", ["obelisco.png"])]),
        tiled("MenuGround", "sidewalk.png", W, H - GROUND_Y),
        sprite("MenuFarol", [anim("Idle", ["farol.png"])]),
        sprite("MenuVirus", [anim("Idle", virus_frames, 0.12)]),
        reuse("MenuLio", "Player", "Run"),
        *[reuse(n, src, "Walk") for n, src, _ in HORDE],
        sprite("MenuLogo", [anim("Idle", ["menu_logo.png"])]),
        sprite("MenuSub", [anim("Idle", ["menu_sub.png"])]),
        sprite("MenuPanel", [anim("Idle", ["menu_panel.png"])]),
        *[sprite(n, [anim("n", [f"menu_{k}_n.png"]), anim("s", [f"menu_{k}_s.png"])])
          for n, k, _ in ITEMS],
        sprite("MenuCursor", [anim("Idle", virus_frames, 0.08)]),
        sprite("MMHint", [anim("Idle", ["menu_hint.png"])]),
        sprite("OptTitle", [anim("Idle", ["menu_opt_title.png"])]),
        sprite("OptMusicLbl", [anim("Idle", ["menu_opt_music.png"])]),
        sprite("OptSfxLbl", [anim("Idle", ["menu_opt_sfx.png"])]),
        *[sprite(n, [anim(f"v{i}", [f"menu_bar_{i}.png"]) for i in range(11)])
          for n in ("OptMusicBar", "OptSfxBar")],
        sprite("OptHint", [anim("Idle", ["menu_opt_hint.png"])]),
    ]
    return objs


def layout_instances():
    px, py, pw, ph = PANEL
    lx = px + 12
    bx = px + pw - 103 - 9
    ins = [
        inst("MenuSky", 0, 0, 0),
        inst("MenuCityFar", 0, 128, 1, W, 70),
        inst("MenuObelisco", 404, GROUND_Y - 122, 2),
        inst("MenuCityNear", 0, GROUND_Y - 96, 3, W, 96),
        inst("MenuGround", 0, GROUND_Y, 4, W, H - GROUND_Y),
        inst("MenuFarol", 70, GROUND_Y - 56, 5),
        inst("MenuFarol", 330, GROUND_Y - 56, 5),
        inst("MenuVirus", 60, 74, 6),
        inst("MenuVirus", 118, 30, 6),
        inst("MenuVirus", 350, 96, 6),
        inst("MenuLio", LIO_X, GROUND_Y - 34, 11),
        *[inst(n, x, GROUND_Y - 34, 10) for n, _, x in HORDE],
        inst("MenuLogo", (W - 145) // 2, 10, 20),
        inst("MenuSub", (W - 153) // 2, 86, 20),
        inst("MenuPanel", px, py, 20),
        *[inst(n, px + (pw - w) // 2, ITEM_Y0 + i * ITEM_DY, 21) for i, (n, _, w) in enumerate(ITEMS)],
        inst("MenuCursor", px + 10, ITEM_Y0 + 1, 22),
        inst("MMHint", (W - 261) // 2, 254, 30),
        inst("OptTitle", px + (pw - 98) // 2, py + 12, 21),
        inst("OptMusicLbl", lx, py + 44, 21),
        inst("OptMusicBar", bx, py + 44, 21),
        inst("OptSfxLbl", lx, py + 66, 21),
        inst("OptSfxBar", bx, py + 66, 21),
        inst("OptHint", (W - 219) // 2, 254, 30),
    ]
    return ins


def scroll_wrap(obj, speed, min_x, reset_x):
    return [
        std([], [act("SetX", [obj, "+", f"-{speed} * TimeDelta()"])]),
        std([cond("PosX", [obj, "<", str(min_x)])], [act("SetX", [obj, "=", str(reset_x)])]),
    ]


def build_events():
    px, py, pw, ph = PANEL
    ev = [
        std([cond("BuiltinCommonInstructions::Once", [])],
            [act("PlayMusicOnChannel", ["", "music_menu.wav", "1", "yes",
                                        "GlobalVariable(MusicVolume)", "1"])]),
        comment("MainMenu - estado unico: variable GLOBAL SettingsOpen (0 = menu principal, "
                "1 = opciones). Los inputs SOLO cambian el estado; la visibilidad y el arranque "
                "del juego se derivan de el. Level1 reutiliza SettingsOpen en la pausa. "
                "MenuSel (escena) = item resaltado: 0 JUGAR, 1 OPCIONES, 2 SALIR."),
        std([cond("BuiltinCommonInstructions::Once", [])],
            [act("ModVarGlobal", ["SettingsOpen", "=", "0"]),
             act("ModVarScene", ["MenuSel", "=", "0"])]),

        comment("Fondo animado (runner): parallax de la ciudad, vereda y faroles que pasan, "
                "virus flotando, la horda persiguiendo a Lio con un vaiven leve."),
        std([], [act("TiledSpriteObject::XOffset", ["MenuCityFar", "+", "6 * TimeDelta()"]),
                 act("TiledSpriteObject::XOffset", ["MenuCityNear", "+", "14 * TimeDelta()"]),
                 act("TiledSpriteObject::XOffset", ["MenuGround", "+", "42 * TimeDelta()"])]),
        *scroll_wrap("MenuFarol", 42, -24, 500),
        *scroll_wrap("MenuVirus", 9, -20, 496),
        std([], [act("SetX", [n, "=", f"{x} + sin(TimeFromStart() * 0.9 + {i * 1.7:.1f}) * 7"])
                 for i, (n, _, x) in enumerate(HORDE)]
            + [act("SetX", ["MenuLio", "=", f"{LIO_X} + sin(TimeFromStart() * 0.6) * 5"])]),

        comment("Visibilidad declarativa: se recalcula sola desde SettingsOpen. Una sola "
                "fuente de verdad -> los dos estados no se pueden desincronizar."),
        std([SETTINGS_CLOSED], [act("Show", ["MenuUI", ""]), act("Hide", ["OptionsUI"])]),
        std([cond("VarGlobal", ["SettingsOpen", "=", "1"])],
            [act("Hide", ["MenuUI"]), act("Show", ["OptionsUI", ""])]),

        comment("Resaltado derivado de MenuSel: item seleccionado en verde + cursor virus."),
        *[std([sel_is(i)],
              [act("SetAnimationName", [n, '"s"' if j == i else '"n"']) for j, (n, _, _) in enumerate(ITEMS)])
          for i in range(len(ITEMS))],
        std([], [act("SetY", ["MenuCursor", "=", f"{ITEM_Y0 + 1} + Variable(MenuSel) * {ITEM_DY}"])]),
        std([], [act("SetAnimationName", ["OptMusicBar", '"v" + ToString(GlobalVariable(MusicVolume) / 10)']),
                 act("SetAnimationName", ["OptSfxBar", '"v" + ToString(GlobalVariable(SfxVolume) / 10)'])]),

        comment("Inputs: SOLO cambian el estado o arrancan el juego."),
        std([any_key("Up", "w"), SETTINGS_CLOSED],
            [act("ModVarScene", ["MenuSel", "-", "1"]),
             act("PlaySound", ["", "sfx_select.wav", "no", f"{SFX} * 0.5", "1.3"])]),
        std([any_key("Down", "s"), SETTINGS_CLOSED],
            [act("ModVarScene", ["MenuSel", "+", "1"]),
             act("PlaySound", ["", "sfx_select.wav", "no", f"{SFX} * 0.5", "1.3"])]),
        std([cond("VarScene", ["MenuSel", "<", "0"])], [act("ModVarScene", ["MenuSel", "=", "2"])]),
        std([cond("VarScene", ["MenuSel", ">", "2"])], [act("ModVarScene", ["MenuSel", "=", "0"])]),
        std([any_key("Return", "Space", "j"), SETTINGS_CLOSED],
            [act("PlaySound", ["", "sfx_select.wav", "no", SFX, "1"])],
            sub=[std([sel_is(0)], [act("Scene", ["", '"Tutorial"', "no"])]),
                 std([sel_is(1)], [act("ModVarGlobal", ["SettingsOpen", "=", "1"])]),
                 std([sel_is(2)], [act("Quit", [""])])]),
        std([any_key("Escape"), SETTINGS_CLOSED],
            [act("PlaySound", ["", "sfx_select.wav", "no", SFX, "1"]), act("Quit", [""])]),
        std([any_key("o"), SETTINGS_CLOSED],
            [act("ModVarScene", ["MenuSel", "=", "1"]),
             act("PlaySound", ["", "sfx_select.wav", "no", SFX, "1"]),
             act("ModVarGlobal", ["SettingsOpen", "=", "1"])]),
        std([any_key("Escape"), cond("VarGlobal", ["SettingsOpen", "=", "1"])],
            [act("PlaySound", ["", "sfx_select.wav", "no", SFX, "1"]),
             act("ModVarGlobal", ["SettingsOpen", "=", "0"])]),

        comment("Volumen: logica compartida con la pausa de Level1, en la hoja de eventos "
                "externa SettingsControls."),
        {"type": "BuiltinCommonInstructions::Link", "include": {"includeConfig": 0},
         "target": "SettingsControls"},
    ]
    return ev


def apply(d):
    mm = next(l for l in d["layouts"] if l["name"] == "MainMenu")
    objs = build_objects(d)
    mm["objects"] = objs
    mm["instances"] = layout_instances()
    mm["objectsGroups"] = [{"name": "MenuUI", "objects": [{"name": n} for n in MENU_UI]},
                           {"name": "OptionsUI", "objects": [{"name": n} for n in OPTIONS_UI]}]
    mm["objectsFolderStructure"] = {"folderName": "__ROOT",
                                    "children": [{"objectName": o["name"]} for o in objs]}
    mm["variables"] = [{"name": "MenuSel", "type": "number", "value": 0}]
    mm["r"], mm["v"], mm["b"] = 8, 10, 22
    mm["events"] = build_events()

    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for img in MENU_IMAGES:
        if img not in have:
            res.append({"file": f"{MENU_DIR}/{img}", "kind": "image", "metadata": "",
                        "name": img, "smoothed": False, "userAdded": True})
    # sanity: todas las imágenes referenciadas existen como recurso y en disco
    files = {r["name"]: r["file"] for r in res}
    for o in objs:
        imgs = [s["image"] for a in o.get("animations", []) for dd in a["directions"] for s in dd["sprites"]]
        imgs += [o["texture"]] if "texture" in o else []
        for i in imgs:
            assert i in files, f"recurso faltante: {i}"
            assert os.path.exists(os.path.join("game", files[i])), f"archivo faltante: {files[i]}"


# ---------- preview (PIL) ----------
def preview(d, options=False, t=0.0):
    from PIL import Image
    files = {r["name"]: os.path.join("game", r["file"]) for r in d["resources"]["resources"]}
    for img in MENU_IMAGES:
        files.setdefault(img, os.path.join("game", MENU_DIR, img))
    objs = {o["name"]: o for o in build_objects(d)}
    hidden = set(MENU_UI if options else OPTIONS_UI)
    canvas = Image.new("RGBA", (W, H), (8, 10, 22, 255))
    for i in sorted(layout_instances(), key=lambda i: i["zOrder"]):
        if i["name"] in hidden:
            continue
        o = objs[i["name"]]
        if "texture" in o:
            tex = Image.open(files[o["texture"]]).convert("RGBA")
            for x in range(0, i["width"], tex.width):
                for y in range(0, i["height"], tex.height):
                    canvas.alpha_composite(tex.crop((0, 0, min(tex.width, i["width"] - x),
                                                     min(tex.height, i["height"] - y))), (x, i["y"] + y))
            continue
        want = "s" if i["name"] == "MMJugar" else ("v7" if i["name"].endswith("Bar") else None)
        a = next((a for a in o["animations"] if a["name"] == want), o["animations"][0])
        im = Image.open(files[a["directions"][0]["sprites"][0]["image"]]).convert("RGBA")
        canvas.alpha_composite(im, (int(i["x"]), int(i["y"])))
    return canvas.resize((W * 2, H * 2), Image.NEAREST)


def main():
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    d = json.load(open(GAME))
    if "--preview" in sys.argv:
        for name, opt in (("menu", False), ("opciones", True)):
            p = f"game/{MENU_DIR}/_preview_{name}.png"
            preview(d, opt).save(p)
            print("preview", p)
        return
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    apply(d)
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    mm = next(l for l in d["layouts"] if l["name"] == "MainMenu")
    print("MainMenu:", len(mm["objects"]), "objetos,", len(mm["instances"]), "instancias,",
          len(mm["events"]), "eventos")


if __name__ == "__main__":
    main()
