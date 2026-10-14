#!/usr/bin/env python3
"""
palette_night.py  —  paleta noche compartida por los generadores de tiles del
piso / costanera (gen_floor.py, gen_costanera.py). Un solo lugar para que el
cordón, el muro del malecón y el agua sean el mismo mundo.

Base de escena: (16, 20, 40)  — fondo de Level1.
"""

BG = (16, 20, 40, 255)

# --- hormigón (cordón + muro del malecón: mismo material) ---
CONCRETE_LIT   = (80, 86, 104, 255)   # canto iluminado (borde del cordón)
CONCRETE_HI    = (64, 70, 88, 255)
CONCRETE       = (52, 57, 72, 255)
CONCRETE_DK    = (43, 47, 60, 255)
CONCRETE_STAIN = (36, 40, 52, 255)    # manchas de humedad
FORMLINE       = (28, 31, 42, 255)    # juntas / líneas de encofrado

# --- agua del Río de la Plata (de noche) ---
WATER_DEEP  = (20, 28, 48, 255)
WATER       = (28, 40, 64, 255)
WATER_HI    = (42, 58, 88, 255)
WATER_GLINT = (94, 118, 148, 255)
FOAM        = (118, 138, 162, 255)
FOAM_DIM    = (74, 88, 110, 255)

# --- caño de desagüe + chorro ---
PIPE_RIM_LIT = (74, 80, 96, 255)
PIPE_RIM     = (48, 52, 66, 255)
PIPE_RIM_DK  = (34, 37, 48, 255)
PIPE_HOLE    = (12, 14, 22, 255)
PIPE_HOLE_HI = (22, 26, 38, 255)      # apenas de luz dentro del caño

STREAM_CORE  = (108, 132, 158, 255)
STREAM       = (72, 94, 122, 255)
STREAM_EDGE  = (44, 58, 80, 255)
SPLASH       = (126, 146, 168, 255)

# --- muro roto: hierros / rebar expuestos ---
REBAR       = (58, 54, 56, 255)
REBAR_HI    = (92, 76, 62, 255)     # óxido apenas iluminado
REBAR_DK    = (28, 26, 30, 255)
RUBBLE      = (48, 52, 64, 255)     # cascotes de hormigón (= CONCRETE_DK-ish)
