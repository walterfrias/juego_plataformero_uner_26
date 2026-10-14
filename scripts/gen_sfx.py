#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
gen_sfx.py  —  efectos de sonido chiptune procedurales para "Paciente Zero"
(mismo criterio que el arte: generados con un script, sin descargas, estilo
8-bit arcade). numpy -> WAV 44.1 kHz mono 16-bit en game/assets/audio/.

SFX (consigna pide al menos los de colisión: stomp/kill y daño):
  sfx_jump.wav      salto del player (chirp ascendente corto)
  sfx_stomp.wav     matar zombie de un pisotón (barrido hacia abajo + ruido)
  sfx_hurt.wav      el player recibe daño / cae / queda atrás (buzz áspero)
  sfx_pickup.wav    juntar antídoto (arpegio brillante hacia arriba)
  sfx_victory.wav   llegar a la meta (fanfarria mayor)
  sfx_gameover.wav  perder (descenso menor lento)
  sfx_select.wav    confirmar en el menú (blip)
  sfx_zumbido.wav   zumbido de tubo fluorescente del lab (loop 2 s, 14/10)
  sfx_chispazo.wav  chispazo eléctrico de un tubo que falla (14/10)

MÚSICA — procedural, definitiva (CC0 descartado por completo, ver
AUDIO_CREDITS.txt):
  music_menu.wav    loop lento y sombrío (~8 s, seamless)
  music_level1.wav  loop con pulso, arpegio menor (~9.6 s, seamless)

Uso:  python3 scripts/gen_sfx.py     (desde la raíz del repo)
"""
import os
import wave
import struct
import numpy as np

SR = 44100
OUT = "game/assets/audio"
os.makedirs(OUT, exist_ok=True)


# ---------- síntesis ----------
def _phase(f0, f1, n):
    freq = np.linspace(f0, f1, n)
    return 2 * np.pi * np.cumsum(freq) / SR


def square(f0, f1, dur, duty=0.5):
    n = int(dur * SR)
    ph = _phase(f0, f1, n)
    return (((ph / (2 * np.pi)) % 1.0) < duty).astype(np.float64) * 2 - 1


def triangle(f0, f1, dur):
    n = int(dur * SR)
    ph = _phase(f0, f1, n)
    return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1


def noise(dur):
    return np.random.uniform(-1, 1, int(dur * SR))


def env(n, a=0.005, r=0.05, sustain=1.0):
    """envolvente ataque-sostén-release lineal."""
    e = np.full(n, sustain)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, sustain, na)
    if nr:
        e[-nr:] = np.linspace(sustain, 0, nr)
    return e


def note(freq, dur, wave="square", duty=0.5, vol=0.5, bend=1.0):
    y = square(freq, freq * bend, dur, duty) if wave == "square" else triangle(freq, freq * bend, dur)
    return y * env(len(y)) * vol


def seq(notes, wave="square", duty=0.5, vol=0.5):
    return np.concatenate([note(f, d, wave, duty, vol) for f, d in notes])


def save(name, y, fade_ms=3, loop=False, target=0.6):
    y = np.asarray(y, dtype=np.float64)
    peak = np.max(np.abs(y)) or 1.0
    y = y / peak * target                    # normalizar (square pega fuerte en RMS)
    fl = int(fade_ms / 1000 * SR)
    if fl and len(y) > 2 * fl:
        if loop:
            # crossfade cola->cabeza para que el loop no chasquee
            head = y[:fl].copy()
            y[:fl] *= np.linspace(0, 1, fl)
            y[-fl:] *= np.linspace(1, 0, fl)
            y[-fl:] += head * np.linspace(0, 1, fl)[::-1]
        else:
            y[:fl] *= np.linspace(0, 1, fl)
            y[-fl:] *= np.linspace(1, 0, fl)
    data = (np.clip(y, -1, 1) * 32767).astype(np.int16)
    path = f"{OUT}/{name}.wav"
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", s) for s in data))
    print(f"  {name}.wav  {len(data)/SR:.2f}s")


# ---------- SFX ----------
def sfx():
    save("sfx_jump", note(320, 0.13, "square", 0.5, 0.5, bend=2.2))

    st = square(520, 120, 0.16, 0.5) * env(int(0.16 * SR), r=0.09) * 0.55
    st = st + noise(0.16)[:len(st)] * env(len(st), a=0.001, r=0.05) * 0.18
    save("sfx_stomp", st)

    hu = square(240, 90, 0.28, 0.5) * env(int(0.28 * SR), r=0.14) * 0.5
    hu = hu + square(243, 91, 0.28, 0.5)[:len(hu)] * 0.2      # leve detune / batido
    hu = hu + noise(0.28)[:len(hu)] * env(len(hu), r=0.2) * 0.12
    save("sfx_hurt", hu)

    save("sfx_pickup", seq([(880, 0.05), (1108, 0.05), (1318, 0.09)], duty=0.35, vol=0.45))

    save("sfx_victory", seq([(523, 0.12), (659, 0.12), (784, 0.12), (1046, 0.32)],
                            duty=0.5, vol=0.42))

    save("sfx_gameover", seq([(440, 0.22), (349, 0.22), (294, 0.22), (220, 0.5)],
                             wave="triangle", vol=0.5))

    save("sfx_select", note(988, 0.06, "square", 0.5, 0.4, bend=1.0))


# ---------- música placeholder ----------
def _loop(chords, bpm, bass_oct=1, arp_wave="square", arp_vol=0.16,
          bass_vol=0.22, hat=False):
    beat = 60.0 / bpm
    bar = beat * 4
    out = []
    for root in chords:
        # tríada menor: root, +3 semis, +7 semis
        triad = [root * 2 ** (s / 12) for s in (0, 3, 7)]
        # arpegio 8 corcheas
        arp = np.concatenate([
            note(triad[i % 3] * 2, beat / 2, arp_wave, 0.35, arp_vol)
            for i in range(8)])
        bass = note(root / (2 ** (2 - bass_oct)), bar, "triangle", 0.5, bass_vol)
        n = min(len(arp), len(bass))
        mix = arp[:n] + bass[:n]
        if hat:
            h = np.zeros(n)
            step = int(beat / 2 * SR)
            for k in range(0, n - 300, step):
                h[k:k + 300] += noise(300 / SR) * np.linspace(1, 0, 300) * 0.05
            mix = mix + h
        out.append(mix)
    return np.concatenate(out)


def music():
    A2 = 110.0
    # menú: Am - F - C - G  (lento, sin hats)
    menu = _loop([A2, A2 * 2 ** (-4 / 12), A2 * 2 ** (3 / 12), A2 * 2 ** (-2 / 12)],
                 bpm=88, arp_vol=0.13, bass_vol=0.2)
    save("music_menu", menu, fade_ms=8, loop=True, target=0.42)
    # nivel 1: Am - Am - Dm - E  (con pulso)
    lvl = _loop([A2, A2, A2 * 2 ** (-7 / 12), A2 * 2 ** (-5 / 12)],
                bpm=132, arp_vol=0.17, bass_vol=0.24, hat=True)
    save("music_level1", lvl, fade_ms=6, loop=True, target=0.44)


def lab_sfx():
    """luces del laboratorio (wire_lab_luces.py). Generador aleatorio propio:
    así no cambia la secuencia de np.random de los SFX y la música de arriba."""
    rng = np.random.default_rng(1414)
    # zumbido de balasto: 120 Hz + armónicos, saturado suave, con un latido
    # lento (0.5 Hz) y un crujido de fondo que pulsa a 120 Hz. 2.0 s = 240
    # ciclos exactos: el loop cierra solo.
    t = np.arange(int(2.0 * SR)) / SR
    hum = sum(a * np.sin(2 * np.pi * f * t)
              for f, a in ((120, 0.5), (240, 0.28), (360, 0.15), (480, 0.07), (1080, 0.04)))
    hum = np.tanh(1.8 * hum) * (1 + 0.08 * np.sin(2 * np.pi * 0.5 * t))
    hum = hum + rng.uniform(-1, 1, len(t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 120 * t)) ** 4 * 0.06
    save("sfx_zumbido", hum, fade_ms=20, loop=True, target=0.5)

    # chispazo: clics de ruido que se apagan + un "zap" agudo que cae
    n = int(0.16 * SR)
    y = np.zeros(n)
    pos = 0
    for k in range(rng.integers(6, 9)):
        ln = int(SR * rng.uniform(0.002, 0.006))
        if pos + ln >= n:
            break
        y[pos:pos + ln] += rng.uniform(-1, 1, ln) * (1 - k / 9)
        pos += int(SR * rng.uniform(0.006, 0.022))
    y = np.diff(y, prepend=0) * 0.7 + y * 0.5                    # más agudo (pasa-altos casero)
    zap = square(1800, 600, 0.06, 0.3) * env(int(0.06 * SR), a=0.001, r=0.05) * 0.25
    y[:len(zap)] += zap
    y *= np.exp(-np.arange(n) / (0.05 * SR))
    save("sfx_chispazo", y, target=0.55)


def main():
    np.random.seed(0)
    print("SFX ->", OUT)
    sfx()
    print("Música (placeholder) ->", OUT)
    music()
    print("Luces del lab ->", OUT)
    lab_sfx()
    cred = f"{OUT}/AUDIO_CREDITS.txt"
    if not os.path.exists(cred):
        with open(cred, "w") as f:
            f.write(
                "AUDIO de Paciente Zero\n\n"
                "SFX (sfx_*.wav): generados por scripts/gen_sfx.py "
                "(chiptune procedural, numpy). Propios, sin licencia de terceros.\n\n"
                "MÚSICA (music_*.wav): PLACEHOLDER procedural de scripts/gen_sfx.py.\n"
                "Plan: reemplazar por pistas CC0 (Kenney Music, OpenGameArt, "
                "Sonniss GDC bundle). Dejar el archivo CC0 como music_menu / "
                "music_level1 (.ogg preferido) en esta carpeta y correr "
                "scripts/wire_audio.py de nuevo.\n"
                "Al usar CC0: anotar acá autor + fuente + link de licencia.\n")
        print("  AUDIO_CREDITS.txt")


if __name__ == "__main__":
    assert os.path.isdir("game/assets"), "corré desde la raíz del repo"
    main()
