# scripts/

Utilidades del proyecto. Todo es **Python 3 + Pillow (PIL)**:

```bash
pip install pillow        # o: sudo dnf install python3-pillow
```

Correr **siempre desde la raíz del repo** (`juego_plataformero_uner_26/`).

Por qué existen: el arte pixel se dibuja a mano en **Pixaki (iPad)**, pero
el corte, el encaje y los placeholders se hacen con scripts. Y como el MCP
`gdevelop` no conecta en estas sesiones, el `game/game.json` se edita
directo (es un JSON); esos scripts dejan un backup `*.bak-<timestamp>`
antes de tocar nada.

> ⚠️ GDevelop **no relee el archivo del disco**. Después de correr
> cualquier script que toque `game.json`: en el editor, **Archivo →
> Cerrar proyecto** (sin guardar) → **Archivo → Abrir** → `game/game.json`.

---

## Generadores de arte placeholder

| Script | Crea | Medidas |
|---|---|---|
| `gen_city_bg.py` | `game/assets/City/city_far.png`, `city_near.png`, **`obelisco.png`** (Obelisco de Buenos Aires) | 224×70, 224×96, 18×122 |
| `gen_street_props.py` | `game/assets/City/farol.png`, `tacho.png` | 20×56, 16×18 |
| `gen_floor.py` | `game/assets/City/sidewalk.png` (vereda de noche con cordón, tileable) | 24×16 |
| `gen_zombie_female.py` | `game/assets/Zombie_F/Zombie_F_Walk_1..10.png` + spritesheet — zombie femenina, shamble de 10 frames (arrastra los pies, mueve la cabeza) | 32×34 ×10 |
| `gen_zombie_male.py` | `game/assets/Zombie_M/Zombie_M_Walk_1..8.png` + spritesheet — zombie masculino, caminata con renguera de 8 frames (pierna tiesa, cabeza caída) | 32×34 ×8 |
| `gen_player.py` | `game/assets/Player/Player_{Idle×4,Run×6,Jump×4,Fall×2,Hit×1,Death×3}.png` — personaje principal "Val", 20 frames, campera naranja | 32×34 ×20 |

Los skylines se dibujan con **wraparound** (lo que cruza un borde se
redibuja en `x ± ancho`) → tilean sin costura horizontal.

Para reemplazar por arte propio: dibujá en Pixaki con las mismas medidas,
mismo nombre de archivo, exportá encima. No hace falta tocar `game.json`.

```bash
python3 scripts/gen_city_bg.py
python3 scripts/gen_street_props.py
```

## Procesado de sprites dibujados a mano

| Script | Qué hace |
|---|---|
| `slice_spritesheet.py` | corta una tira de frames en PNGs sueltos |
| `align_frames_to_floor.py` | agranda el canvas a una altura y pega los "pies" al borde inferior (para que apoye en el piso igual que los frames del pack CC0) |

```bash
# cortar el walk del zombie (spritesheet 160x32 -> 5 frames de 32x32)
python3 scripts/slice_spritesheet.py \
    game/assets/Big_Zombie/zombie1.png 32 32 \
    game/assets/Big_Zombie/Big_Zombie_Walk_

# emparejarlos a 34px de alto (los frames CC0 son 32x34)
python3 scripts/align_frames_to_floor.py 34 \
    game/assets/Big_Zombie/Big_Zombie_Walk_*.png
```

## Revisión de arte (QA)

`qa_pixelart.py` — genera PNGs de inspección, no toca los assets:

```bash
# onion skin: frames superpuestos y tintados (gris = no se mueve)
python3 scripts/qa_pixelart.py onion SHEET.png 32 34 /tmp/onion.png

# chequeo de tileado: pega la textura x2 y marca la unión
python3 scripts/qa_pixelart.py tile assets/City/city_near.png /tmp/tile.png

# ver un sprite grande sin interpolación, sobre damero
python3 scripts/qa_pixelart.py scale assets/City/farol.png /tmp/farol.png 18
```

## Wiring a game.json (registro reproducible)

| Script | Qué mete en el proyecto |
|---|---|
| `wire_city_background.py` | color de escena azul noche + capas `BG_far`/`BG_near` (scroll 1:1) + `CityFar`/`CityNear`/`Obelisco` |
| `wire_street_props.py` | capa `Decor` + objetos `Farol`/`Tacho` + instancias |
| `wire_floor.py` | cambia la textura del objeto `Ground` a `sidewalk.png` |
| `wire_camera_follow.py` | suelo con tamaño explícito que cubre el nivel + cámara que sigue al `Player` (`CenterCameraOnObject` + `ClampCamera`) |
| `fix_event_params.py` | comilla nombres de texto en eventos (animación, timer) que el MCP dejó sin comillas y quedaban en rojo en el "Diagnostic report" |
| `wire_zombie_female.py` | objeto `ZombieF` + animación Walk (10f) + variable + instancia + patrulla + grupo `Zombies` (Zombie+ZombieF) para que stomp/daño valgan para los dos |
| `wire_zombie_male.py` | objeto `ZombieM` + animación Walk (8f) + variable + instancia + patrulla; lo suma al grupo `Zombies` |
| `wire_player.py` | reemplaza el sprite del `Player` (Knight_Male) por el de `gen_player.py`: 6 animaciones, baja la instancia a y=76, agrega eventos de animación al saltar/caer, quita los resources Knight |

```bash
python3 scripts/gen_city_bg.py          # 1. assets
python3 scripts/gen_street_props.py
python3 scripts/gen_floor.py
python3 scripts/wire_city_background.py # 2. wiring (en este orden)
python3 scripts/wire_street_props.py
python3 scripts/wire_floor.py
python3 scripts/wire_camera_follow.py
```

> El **parallax con profundidad** se sacó por ahora (dependía de eventos
> `SetCameraX` con formato sin verificar). El fondo scrollea plano 1:1.
> Los eventos de `wire_camera_follow.py` (`CenterCameraOnObject`,
> `ClampCamera`) también son formato reconstruido — si salen en rojo en
> el editor, agregalos a mano (2 clicks).

Ambos `wire_*` son **idempotentes** (no duplican si ya está puesto) y
dejan backup `game/game.json.bak-<timestamp>`.

El wiring del **walk del zombie** (animación `Walk` en el objeto Zombie +
evento `SetAnimationName`) se hizo inline en la sesión del 2026-08-30;
está descripto paso a paso en `reseach.md`.
