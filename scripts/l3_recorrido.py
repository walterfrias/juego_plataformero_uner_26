#!/usr/bin/env python3
"""
l3_recorrido.py  —  diseño del Nivel 3 nuevo (18/10) como DATOS: Lio sale
del laboratorio, cruza el centro de noche y llega al Obelisco, donde pelea
con Paciente Zero. Lo dibuja la maqueta y lo va a leer el script de cableo,
así el diseño está en un solo lugar.

Coordenadas del mundo de Level3: el piso está en y = 150 (en L1/L2 es 110:
todo lo que viene de L1 va +40 en y). La arena del jefe (hoy x 0..480) se
corre al final del recorrido (ARENA_X0..ARENA_X1).

Reglas de diseño (salto medido de Lio): huecos ≤ 28 px sin ayuda (≈20 si se
espera en el borde), escalones ≤ 28 px; todo hueco más ancho lleva puente o
cables. Sin mecánicas nuevas: solo piezas que ya existen en L1/L2.
"""
FLOOR = 150
DY_L1 = 40                     # objetos traídos de L1: y + 40
ARENA_X0, ARENA_X1 = 2100, 2580
# En el juego el recorrido va en x NEGATIVAS y la arena queda donde estaba
# (0..480): así no se toca la lógica del jefe (topes 4/412, embestida) ni los
# scripts que ya trabajan sobre L3. Coordenada del juego = x de diseño + OFFSET_X.
OFFSET_X = -ARENA_X0
LAB_END = 320                  # hasta acá es interior del lab; después, la calle

# tramos (para los carteles de la maqueta y como guía del ritmo)
TRAMOS = [
    (0, LAB_END, "1. Salida del laboratorio"),
    (LAB_END, 760, "2. La calle del hospital"),
    (760, 1200, "3. La plaza"),
    (1200, 1720, "4. Obra en la 9 de Julio"),
    (1720, ARENA_X0, "5. Llegando al Obelisco"),
    (ARENA_X0, ARENA_X1, "6. Arena: Paciente Zero"),
]

# pisos: (x0, x1, tipo) — "lab" = lab_floor; "calle" = vereda + muro debajo
PISOS = [
    (-40, 330, "lab"),
    (330, 520, "calle"),
    (548, 900, "calle"),            # hueco 520..548 (28 px, se salta)
    (988, 1290, "calle"),           # hueco 900..988 con puente (PuenteA, 88 px)
    (1500, 1880, "calle"),          # obra 1290..1500: postes y cables por arriba
    (1906, ARENA_X1 + 40, "calle"),  # hueco 1880..1906 (26 px) antes de la arena
]

# huecos: qué se ve al fondo
HUECOS = [
    (520, 548, "escombros"),
    (900, 988, "escombros"),
    (1290, 1500, "hierros"),
    (1880, 1906, "escombros"),
]

# objetos: (nombre, x, y, extra) — y = esquina de arriba; los de L1 ya con +40.
# Zombies: los de la calle son los de la horda de L2 (policía, hincha, repartidor);
# en el lab, el médico. MinX/MaxX = patrulla (x de diseño).
PROPS = [
    # 1. lab: un médico zombie, tubos del lab, la pared rota de salida
    ("ZombieMed", 170, FLOOR - 34, {"MinX": 120, "MaxX": 280}),
    ("WallBreakR", 312, FLOOR - 60, {}),
    # 2. calle del hospital
    ("Tacho", 380, FLOOR - 18, {"fuego": True}),
    ("Farol", 450, FLOOR - 56, {}),
    ("Virus", 534, 96, {"patron": "ascensor"}),        # sobre el hueco de 28 px
    ("ZombiePol", 620, FLOOR - 34, {"MinX": 570, "MaxX": 740}),
    ("Farol", 700, FLOOR - 56, {}),
    ("Tacho", 820, FLOOR - 18, {"fuego": True}),
    # 3. plaza: árboles que se pisan, banco, puente sobre el hueco ancho
    ("ArbolBajo", 780, FLOOR - 44, {}),
    ("BancoPlaza", 850, FLOOR - 15, {}),
    ("PuenteA", 900, FLOOR, {}),
    ("Virus", 944, 104, {"patron": "pendulo"}),
    ("ArbolAlto", 1030, FLOOR - 82, {}),
    ("ZombieHin", 1080, FLOOR - 34, {"MinX": 1000, "MaxX": 1180}),
    ("ArbolBajo", 1170, FLOOR - 44, {}),
    # 4. obra en la 9 de Julio: subir por un poste, cruzar por los cables, bajar
    ("Poste", 1272, 62, {}),
    ("Cable", 1272, 70, {"w": 246}),           # arranca encima del primer poste y termina pasando el segundo
    ("Poste", 1500, 62, {}),
    ("Virus", 1395, 50, {"patron": "circulo"}),
    ("Tacho", 1560, FLOOR - 18, {"fuego": True}),
    ("ZombieRep", 1640, FLOOR - 34, {"MinX": 1560, "MaxX": 1840}),
    # 5. llegando al Obelisco: marcha de zombies, fuego, alambre de la barricada
    ("Farol", 1760, FLOOR - 56, {}),
    ("ZombieHin", 1830, FLOOR - 34, {"MinX": 1700, "MaxX": 1840, "Dir": -1}),   # marchan hacia Lio
    ("Tacho", 1960, FLOOR - 18, {"fuego": True}),
    ("ZombiePol", 2010, FLOOR - 34, {"MinX": 1930, "MaxX": 2050, "Dir": -1}),
    ("BarbedWire", 2060, FLOOR - 14, {"w": 40}),
    # 6. arena
    ("PacienteZero", ARENA_X0 + 360, 82, {}),
]
CHECKPOINTS = [330, 988, 1500, 1906, ARENA_X0 - 20]   # x de los checkpoints (Lio sobre el piso)
OBELISCO_ARENA = (ARENA_X0 + 214, 2.0)               # x y escala del Obelisco grande del fondo
