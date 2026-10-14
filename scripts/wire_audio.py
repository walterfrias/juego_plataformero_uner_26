#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportOptionalSubscript=false
"""
wire_audio.py  —  cablea el audio de "Paciente Zero" en game/game.json:
registra los recursos de game/assets/audio/ (los genera scripts/gen_sfx.py)
y engancha música + SFX a Level1 y MainMenu, con el volumen atado a las
variables globales `MusicVolume` / `SfxVolume` que ya maneja el menú de
opciones.

MÚSICA (canal 1, loop, volumen = GlobalVariable(MusicVolume)):
  - MainMenu: `music_menu`   (Trigger once)
  - Level1:   `music_level1` (Trigger once); se pausa/reanuda con ESC.
  Prefiere `music_*.ogg` sobre `music_*.wav` si existe (para swap por CC0).

SFX (PlaySound, volumen = GlobalVariable(SfxVolume)):
  - salto ................ evento nuevo: IsJumping flanco de subida (scene var WasJumping)
  - stomp / matar zombie . se agrega al evento de stomp existente
  - daño ................. al evento de daño + a caída al río + a quedarse atrás de la horda
  - antídoto ............. al evento de pickup
  - victoria / game over . a esos eventos
  - confirmar en el menú . al evento que arranca el juego

VOLUMEN EN VIVO: en el External Event `SettingsControls` (ya incluido por Link
en las dos escenas) se agrega `SetMusicChannelVolume 1 = MusicVolume` para que
la música siga el slider mientras lo movés. Los SFX leen `SfxVolume` en cada
disparo, no hace falta actualizarlos.

Eventos nuevos marcados `_audio` (+ detección por contenido si GDevelop borra
la marca). Idempotente. Revertir:  REVERT=1 python3 scripts/wire_audio.py
Uso:  python3 scripts/wire_audio.py    (desde la raíz del repo; corré gen_sfx.py antes)
Después en GDevelop: cerrar sin guardar y reabrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"
ADIR = "game/assets/audio"
MUSIC_CH = "1"

SFX = {  # clave lógica -> nombre de recurso (= archivo)
    "jump": "sfx_jump.wav",
    "stomp": "sfx_stomp.wav",
    "hurt": "sfx_hurt.wav",
    "pickup": "sfx_pickup.wav",
    "victory": "sfx_victory.wav",
    "gameover": "sfx_gameover.wav",
    "select": "sfx_select.wav",
}


def music_file(stem):
    for ext in (".ogg", ".wav"):
        if os.path.exists(f"{ADIR}/{stem}{ext}"):
            return f"{stem}{ext}"
    return f"{stem}.wav"   # nombre esperado aunque no exista aún


def A(t, params):
    return {"type": {"value": t}, "parameters": params}


def C(t, params, inverted=False):
    ty = {"value": t}
    if inverted:
        ty["inverted"] = True
    return {"type": ty, "parameters": params}


def std(conds, acts, mark=True):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}
    if mark:
        e["_audio"] = True
    return e


def play_sfx(res):
    return A("PlaySound", ["", res, "no", "GlobalVariable(SfxVolume)", "1"])


def play_music(res):
    return A("PlayMusicOnChannel",
             ["", res, MUSIC_CH, "yes", "GlobalVariable(MusicVolume)", "1"])


# ---------- detección ----------
def is_audio_event(e):
    if not isinstance(e, dict):
        return False
    if e.get("_audio") is True:
        return True
    j = json.dumps(e)
    return ('"PlayMusicOnChannel"' in j or '"SetMusicChannelVolume"' in j
            or "WasJumping" in j)


def has_action(e, t, res=None):
    for a in e.get("actions", []):
        if a["type"]["value"] == t and (res is None or (a["parameters"][1:2] == [res])):
            return True
    return False


def cond_has(e, t, pred=lambda _p: True):
    return any(c["type"]["value"] == t and pred(c["parameters"]) for c in e.get("conditions", []))


# ---------- localizadores (por contenido) ----------
def find(events, pred):
    for e in events:
        if e.get("type") == "BuiltinCommonInstructions::Standard" and pred(e):
            return e
    return None


def find_stomp(evs):
    return find(evs, lambda e: cond_has(e, "CollisionNP", lambda p: p[:2] == ["Player", "Zombies"])
                and cond_has(e, "PosY", lambda p: p == ["Player", "<", "Zombies.Y()"]))


def find_damage(evs):
    return find(evs, lambda e: cond_has(e, "CollisionNP", lambda p: p[:2] == ["Player", "Zombies"])
                and cond_has(e, "ObjectTimer"))


def find_pickup(evs):
    return find(evs, lambda e: cond_has(e, "CollisionNP", lambda p: p[:2] == ["Player", "Antidoto"]))


def find_victory(evs):
    return find(evs, lambda e: cond_has(e, "CollisionNP", lambda p: p[:2] == ["Player", "Meta"])
                and cond_has(e, "VarScene", lambda p: p == ["Won", "=", "0"]))


def find_gameover(evs):
    return find(evs, lambda e: cond_has(e, "VarScene", lambda p: p == ["Lives", "<=", "0"])
                and cond_has(e, "VarScene", lambda p: p == ["Over", "=", "0"]))


def find_fall(evs):
    return find(evs, lambda e: cond_has(e, "PosY", lambda p: p[0] == "Player" and p[1] == ">"
                                        and p[2] in ("260", "300"))
                and cond_has(e, "VarScene", lambda p: p[0] == "Over"))


def find_behind(evs):
    return find(evs, lambda e: cond_has(e, "VarScene", lambda p: p == ["HordaActive", "=", "1"])
                and cond_has(e, "PosX", lambda p: p[:2] == ["Player", "<"]
                             and "HordaPiso.X() -" in str(p[2])))


def find_pause_on(evs):
    return find(evs, lambda e: cond_has(e, "KeyFromTextJustPressed", lambda p: p[1] == '"Escape"')
                and cond_has(e, "VarScene", lambda p: p == ["Paused", "=", "0"]))


def find_pause_off(evs):
    return find(evs, lambda e: cond_has(e, "KeyFromTextJustPressed", lambda p: p[1] == '"Escape"')
                and cond_has(e, "VarScene", lambda p: p == ["Paused", "=", "1"]))


def find_startgame(evs):
    return find(evs, lambda e: any(a["type"]["value"] == "Scene"
                                   and a["parameters"][1] == '"Level1"' for a in e.get("actions", []))
                and cond_has(e, "VarGlobal", lambda p: p == ["SettingsOpen", "=", "0"]))


def append_once(e, action):
    """agrega `action` a e.actions si no está ya (por type+param sonido)."""
    t, res = action["type"]["value"], action["parameters"][1] if len(action["parameters"]) > 1 else None
    if not has_action(e, t, res):
        e["actions"].append(action)


# ---------- recursos ----------
def register_resources(d):
    res = d["resources"]["resources"]
    by_name = {r["name"] for r in res}
    wanted = []
    for stem in ("music_menu", "music_level1"):
        wanted.append((music_file(stem), True))
    for f in SFX.values():
        wanted.append((f, False))
    for fname, is_music in wanted:
        if fname in by_name:
            continue
        res.append({
            "file": f"assets/audio/{fname}",
            "kind": "audio",
            "metadata": "",
            "name": fname,
            "userAdded": True,
            "preloadAsSound": not is_music,
            "preloadAsMusic": is_music,
            "preloadInCache": not is_music,
        })


def unregister_resources(d):
    keep = set(SFX.values()) | {music_file("music_menu"), music_file("music_level1")}
    d["resources"]["resources"] = [
        r for r in d["resources"]["resources"]
        if not (r.get("kind") == "audio" and r["name"] in keep
                or (r.get("kind") == "audio" and r["name"].startswith(("sfx_", "music_"))))
    ]


# ---------- main ----------
def _save(d):
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


def _layout(d, name):
    return next(l for l in d["layouts"] if l["name"] == name)


def strip_base_sfx(e):
    """saca de un evento base los PlaySound/Pause/Resume que agregamos."""
    if not e:
        return
    def ours(a):
        t = a["type"]["value"]
        if t == "PlaySound" and str(a["parameters"][1]).startswith("sfx_"):
            return True
        if t in ("PauseMusicChannel", "ResumeMusicChannel") and a["parameters"][:2] == ["", MUSIC_CH]:
            return True
        return False
    e["actions"] = [a for a in e["actions"] if not ours(a)]


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    L1 = _layout(d, "Level1")
    MM = _layout(d, "MainMenu")
    ext = next(ee for ee in d["externalEvents"] if ee["name"] == "SettingsControls")

    # limpiar eventos nuestros (idempotente / revert)
    for container in (L1["events"], MM["events"], ext["events"]):
        container[:] = [e for e in container if not is_audio_event(e)]

    # base events (para append o strip)
    base = {
        "stomp": find_stomp(L1["events"]),
        "damage": find_damage(L1["events"]),
        "pickup": find_pickup(L1["events"]),
        "victory": find_victory(L1["events"]),
        "gameover": find_gameover(L1["events"]),
        "fall": find_fall(L1["events"]),
        "behind": find_behind(L1["events"]),
        "pause_on": find_pause_on(L1["events"]),
        "pause_off": find_pause_off(L1["events"]),
        "startgame": find_startgame(MM["events"]),
    }

    if revert:
        for e in base.values():
            strip_base_sfx(e)
        L1["variables"][:] = [v for v in L1["variables"] if v["name"] != "WasJumping"]
        unregister_resources(d)
        _save(d)
        print("revert OK: audio desconectado (los .wav quedan en game/assets/audio/)")
        return

    missing = [k for k, v in base.items() if v is None]
    assert not missing, f"no encontré eventos base: {missing}"

    register_resources(d)
    m_menu, m_lvl = music_file("music_menu"), music_file("music_level1")

    # --- Level1: música + pausa/reanudar ---
    L1["events"].insert(0, std([C("BuiltinCommonInstructions::Once", [])], [play_music(m_lvl)]))
    append_once(base["pause_on"], A("PauseMusicChannel", ["", MUSIC_CH]))
    append_once(base["pause_off"], A("ResumeMusicChannel", ["", MUSIC_CH]))

    # --- Level1: SFX en eventos base ---
    append_once(base["stomp"], play_sfx(SFX["stomp"]))
    append_once(base["damage"], play_sfx(SFX["hurt"]))
    append_once(base["pickup"], play_sfx(SFX["pickup"]))
    append_once(base["victory"], play_sfx(SFX["victory"]))
    append_once(base["gameover"], play_sfx(SFX["gameover"]))
    append_once(base["fall"], play_sfx(SFX["hurt"]))
    append_once(base["behind"], play_sfx(SFX["hurt"]))

    # --- Level1: salto (flanco de subida de IsJumping) ---
    if not any(v["name"] == "WasJumping" for v in L1["variables"]):
        L1["variables"].append({"name": "WasJumping", "type": "number", "value": 0})
    IS_JUMP = "PlatformBehavior::IsJumping"
    L1["events"].append(std(
        [C(IS_JUMP, ["Player", "PlatformerObject"]), C("VarScene", ["WasJumping", "=", "0"])],
        [play_sfx(SFX["jump"]), A("ModVarScene", ["WasJumping", "=", "1"])]))
    L1["events"].append(std(
        [C(IS_JUMP, ["Player", "PlatformerObject"], inverted=True)],
        [A("ModVarScene", ["WasJumping", "=", "0"])]))

    # --- MainMenu: música + blip al arrancar el juego ---
    MM["events"].insert(0, std([C("BuiltinCommonInstructions::Once", [])], [play_music(m_menu)]))
    base["startgame"]["actions"].insert(0, play_sfx(SFX["select"]))

    # --- SettingsControls: música sigue el slider en vivo ---
    ext["events"].append(std([], [
        A("SetMusicChannelVolume", ["", MUSIC_CH, "=", "GlobalVariable(MusicVolume)"])]))

    _save(d)
    n_res = sum(1 for r in d["resources"]["resources"] if r.get("kind") == "audio")
    print(f"audio cableado: {n_res} recursos, música {m_lvl} / {m_menu} (canal {MUSIC_CH})")
    print("  cerrá GDevelop sin guardar y reabrí game/game.json")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    if not os.path.isdir(ADIR):
        raise SystemExit("falta game/assets/audio/ — corré primero: python3 scripts/gen_sfx.py")
    main(revert=os.environ.get("REVERT") == "1")
