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
    (1200, 1720, "4. Obra en Corrientes"),
    (1720, ARENA_X0, "5. Llegando al Obelisco"),
    (ARENA_X0, ARENA_X1, "6. Arena: Paciente Zero"),
]

# pisos: (x0, x1, tipo) — "lab" = lab_floor; "calle" = vereda + corte de calle debajo.
# Sin pozos desde el 18/10 (en una calle del centro no tenían sentido): la calle es
# continua y los desafíos son peligros de calle (ver MECÁNICAS más abajo).
PISOS = [
    (-40, 330, "lab"),
    (330, ARENA_X1 + 40, "calle"),
]
HUECOS = []

# objetos: (nombre, x, y, extra) — y = esquina de arriba; los de L1 ya con +40.
# Zombies: en el nivel final VUELVEN TODOS (18/10, pedido del usuario): el personal del
# lab (L2), los vecinos de L1 y la horda de la calle (L2), uno de cada tipo y la marcha
# mezclada al final. MinX/MaxX = patrulla (x de diseño); Speed por personaje (la anciana
# lenta como en L1, el corredor rápido); por defecto 22. Ningún zombie pisa el charco ni
# patrulla a menos de 40 px de un checkpoint (si no, golpea a Lio apenas reaparece).
PROPS = [
    # 1. lab: un médico zombie, tubos del lab, la pared rota de salida
    ("ZombieMed", 130, FLOOR - 34, {"MinX": 100, "MaxX": 190}),
    ("ZombieEnf", 250, FLOOR - 34, {"MinX": 210, "MaxX": 280, "Speed": 26}),
    ("ZombieInv", 180, FLOOR - 34, {"MinX": 140, "MaxX": 260, "Speed": 12}),
    ("WallBreakR", 312, FLOOR - 60, {}),
    # 2. calle del hospital
    ("Tacho", 380, FLOOR - 18, {"fuego": True}),
    ("Farol", 450, FLOOR - 56, {}),
    ("Virus", 534, 96, {"patron": "ascensor"}),        # sube y baja: se pasa cuando está arriba
    ("ZombieM", 400, FLOOR - 34, {"MinX": 380, "MaxX": 490}),
    ("ZombieF", 470, FLOOR - 34, {"MinX": 420, "MaxX": 500, "Speed": 18}),
    ("ZombiePol", 620, FLOOR - 34, {"MinX": 570, "MaxX": 700}),
    ("ZombieN", 700, FLOOR - 34, {"MinX": 650, "MaxX": 720, "Speed": 16}),
    ("Farol", 700, FLOOR - 56, {}),
    ("Tacho", 820, FLOOR - 18, {"fuego": True}),
    # 3. plaza: árboles que se pisan, banco, puente sobre el hueco ancho
    ("ArbolBajo", 780, FLOOR - 44, {}),
    ("BancoPlaza", 850, FLOOR - 15, {}),
    ("Virus", 944, 104, {"patron": "pendulo"}),
    ("ArbolAlto", 1030, FLOOR - 82, {}),
    ("ZombieV", 860, FLOOR - 34, {"MinX": 800, "MaxX": 900, "Speed": 8}),        # la anciana
    ("ZombieD", 1080, FLOOR - 34, {"MinX": 1000, "MaxX": 1150}),
    ("ZombieM", 950, FLOOR - 34, {"MinX": 910, "MaxX": 1010, "Speed": 18}),
    ("ZombieEnf", 1140, FLOOR - 34, {"MinX": 1100, "MaxX": 1160, "Speed": 20}),   # se escapó del hospital
    ("ArbolBajo", 1170, FLOOR - 44, {}),
    # 4. obra en Corrientes: subir por un poste, cruzar por los cables (abajo, el charco electrificado), bajar
    ("Poste", 1272, 62, {}),
    ("Cable", 1272, 70, {"w": 246}),           # arranca encima del primer poste y termina pasando el segundo
    ("Poste", 1500, 62, {}),
    ("Virus", 1395, 50, {"patron": "circulo"}),
    ("Tacho", 1560, FLOOR - 18, {"fuego": True}),
    ("ZombieRep", 1600, FLOOR - 34, {"MinX": 1520, "MaxX": 1680}),
    ("ZombieJ", 1650, FLOOR - 34, {"MinX": 1540, "MaxX": 1680, "Speed": 45}),   # el corredor
    # 5. llegando al Obelisco: marcha de zombies, fuego, alambre de la barricada
    ("Farol", 1760, FLOOR - 56, {}),
    # la marcha mezclada (avanza hacia Lio; por arriba, el vapor y las marquesinas)
    ("ZombieN", 1800, FLOOR - 34, {"MinX": 1765, "MaxX": 1860, "Dir": -1, "Speed": 18}),
    ("ZombieO", 1870, FLOOR - 34, {"MinX": 1760, "MaxX": 1900, "Dir": -1, "Speed": 18}),
    ("ZombieHin", 1950, FLOOR - 34, {"MinX": 1880, "MaxX": 2040, "Dir": -1, "Speed": 18}),
    ("ZombieV", 2010, FLOOR - 34, {"MinX": 1980, "MaxX": 2050, "Dir": -1, "Speed": 8}),
    ("ZombieInv", 1790, FLOOR - 34, {"MinX": 1765, "MaxX": 1830, "Dir": -1, "Speed": 14}),
    ("Tacho", 1960, FLOOR - 18, {"fuego": True}),
    ("BarbedWire", 2060, FLOOR - 14, {"w": 40}),
    # 6. arena
    ("PacienteZero", ARENA_X0 + 360, 82, {}),
]
# fachadas porteñas detrás de la vereda (gen_l3_fachadas.py; capa BG_near): "entre
# edificios, no en la costanera" (usuario 18/10). La plaza y la llegada al Obelisco
# quedan abiertas: el cambio de cerrado a abierto marca que se llega.
FACHADA_W = {"frances": 112, "deptos": 96, "ph": 80, "bar": 104}


def _fila(x0, modelos):
    out, x = [], x0
    for m in modelos:
        out.append((m, x))
        x += FACHADA_W[m]
    return out


FACHADAS = (_fila(330, ["deptos", "ph", "frances", "bar"])                        # calle del hospital
            + _fila(1206, ["frances", "deptos", "ph", "bar", "deptos"])           # obra en Corrientes
            + _fila(1722, ["frances", "ph", "deptos"]))                           # se abre hacia el Obelisco
# multitud de fondo (18/10, "que esté infestada"): zombies más chicos y oscuros por la
# vereda de enfrente, delante de las fachadas y detrás del plano de juego. NO tocan a
# Lio. (tipo, x, MinX, MaxX, velocidad) en x de diseño; la arena tiene público.
FONDO = [
    ("ZombieF", 360, 340, 470, 10), ("ZombieO", 560, 500, 700, 12), ("ZombieD", 720, 650, 760, 9),
    ("ZombieN", 830, 780, 960, 11), ("ZombieM", 1010, 960, 1150, 13), ("ZombieV", 1120, 1080, 1190, 6),
    ("ZombieHin", 1260, 1210, 1380, 12), ("ZombiePol", 1420, 1330, 1520, 10), ("ZombieRep", 1600, 1540, 1700, 14),
    ("ZombieF", 1760, 1730, 1880, 10), ("ZombieO", 1930, 1880, 2060, 12),
    ("ZombieN", 2130, 2110, 2200, 7), ("ZombieM", 2330, 2290, 2420, 8), ("ZombieD", 2490, 2440, 2560, 7),
]
FONDO_ESCALA = 0.8

CHECKPOINTS = [330, 760, 1200, 1720, ARENA_X0 - 20]   # x de los checkpoints: comienzo de cada tramo

# --- MECÁNICAS de calle (18/10), en lugar de los pozos (gen_l3_mecanicas.py →
# wire_l3_mecanicas.py). Todas calculadas con TimeFromStart(): se congelan en pausa.
# toldo que rebota: (x, y del borde de arriba). Caer encima → rebote alto (≈80 px)
TOLDOS = [(596, 118)]
# (las macetas que caían de los balcones se sacaron el 18/10, pedido del usuario)
# charco electrificado (cable de alta tensión caído): (x0, x1). Pisarlo = −1 vida y al checkpoint
CHARCOS = [(1290, 1500)]
# respiraderos del subte: (x, fase). Ciclo VAPOR_T s: aviso (bocanadas) → sopla y eleva → nada
VAPOR_T, VAPOR_AVISO, VAPOR_ON = 3.0, 0.4, 1.4
VAPOR_TOP = 56                   # hasta dónde sube el vapor (Lio flota con los pies ahí)
VAPORES = [(1748, 0.0), (1880, 1.5)]
# marquesinas (plataformas que se atraviesan desde abajo) a las que sube el vapor: (x, y, ancho)
MARQUESINAS = [(1780, 76, 72), (1912, 76, 72)]
OBELISCO_ARENA = ARENA_X0 + 232                      # x del CENTRO del Obelisco de la arena (obelisco_cerca.png, 48x176)
