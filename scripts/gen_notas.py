#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_notas.py  —  pruebas del brote (notas del diario de Paciente Zero).

Fuente única de los textos (copiados en GDD §6). 7 notas: 3 en L1, 3 en L2,
1 la suelta el jefe en L3. Se guardan en la mochila (inventario de la pausa).

Diseño:
  - papel con el texto ya horneado en la pixel font del HUD (glifos de
    gen_font.py, sin contorno: tinta sobre papel). Así no hace falta
    BitmapText multilínea ni escapar saltos de línea en los eventos.
  - 3 tipos de papel según la nota:
      diario   hoja de cuaderno arrancada (borde de arriba roto, renglones
               celestes, margen rojo), papel amarillento.
      remito   ticket térmico blanco con borde dentado arriba y abajo y
               línea de corte punteada bajo el título.
      registro hoja de laboratorio: banda verde arriba, cuadrícula tenue.
  - sello rojo "PRUEBA n/7" arriba a la derecha, gastado (faltan píxeles).
  - manchas verde virus semitransparentes (la paleta del antídoto/lab) y
    bordes envejecidos. Nada de sangre (público 12+).
  - pickup flotante: papel doblado con halo verde, mismo criterio que
    antidoto_* (bob + glint, 6 frames, ancla al centro).

Crea (game/assets/UI/Notas/):
  nota_1..7.png        204x128  RGBA  nota completa (popup e inventario)
  nota_none.png        204x128  RGBA  nota no encontrada ("???")
  nota_pick_1..6.png   14x16    RGBA  pickup flotante
  nota_icon.png        9x11     RGBA  ícono chico (aviso / contador)
  nota_slot_found.png  22x26    RGBA  casillero del inventario (encontrada)
  nota_slot_empty.png  22x26    RGBA  casillero del inventario (falta)
  nota_cursor.png      26x30    RGBA  cursor ámbar del inventario
  notas_sheet.png      referencia con todo junto

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_notas.py  (desde la raíz)
"""
from PIL import Image, ImageDraw
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_font import G, ACCENTED, glyph_rows  # noqa: E402

OUT = "game/assets/UI/Notas"
os.makedirs(OUT, exist_ok=True)

T = (0, 0, 0, 0)
W, H = 204, 128
MAX_COLS = 30
MAX_LINES = 8
CW = 6            # 5 px de glifo + 1 de espacio
LINE_H = 11       # 9 filas (2 de acento + 7) + 2 de interlineado
TEXT_X = 14
TITLE_Y = 7
BODY_Y = 25

OUTL = (26, 22, 34, 255)
INK = (34, 40, 78, 255)           # tinta azul oscura
INK_FADE = (34, 40, 78, 150)
STAMP = (196, 44, 44, 255)
VIRUS = (96, 200, 128)            # verde antídoto / lab (sin alfa)
VIRUS_DK = (60, 130, 80)

PAPERS = {
    # base, sombra de borde, renglón, extra
    "diario":   dict(base=(232, 220, 182), edge=(196, 180, 138), rule=(150, 176, 206), margin=(214, 120, 110)),
    "remito":   dict(base=(236, 236, 228), edge=(200, 200, 192), rule=(170, 170, 166), margin=None),
    "registro": dict(base=(222, 230, 220), edge=(184, 196, 184), rule=(196, 210, 198), margin=None),
}

NOTAS = [
    ("EL PLAN", "diario", [
        "DÍA 1. EL VIRUS ESTÁ LISTO.",
        "LO SOLTARÉ EN EL OBELISCO,",
        "EN PLENO FESTEJO. MILES DE",
        "HINCHAS ABRAZADOS: EL MEJOR",
        "CONTAGIO ES LA ALEGRÍA.",
        "NADIE VA A SOSPECHAR DE UN",
        "CIENTÍFICO CON CAMISETA.",
        "- P.Z.",
    ]),
    ("REMITO", "remito", [
        "PEDIDO 0451 - LABORATORIO.",
        "12 DOCENAS DE EMPANADAS.",
        "DEJAR EN LA PUERTA. NO TOCAR",
        "TIMBRE. NO MIRAR LOS FRASCOS.",
        "NOTA DEL REPARTIDOR: HAY UN",
        "OLOR RARO Y LOS VIRUS VUELAN.",
        "NO VUELVO MÁS. ME QUEDO CON",
        "LA PROPINA Y LA MOCHILA.",
    ]),
    ("MENSAJEROS", "diario", [
        "DÍA 4. LOS VIRUS GRANDES",
        "VUELAN SOLOS Y BUSCAN GENTE.",
        "SI TOCAN A UN INFECTADO LO",
        "PONEN MÁS FUERTE Y MÁS VERDE.",
        "LOS LLAMO MIS MENSAJEROS.",
        "NO TRAEN CARTAS, TRAEN",
        "OBEDIENCIA.",
        "- P.Z.",
    ]),
    ("PERSONAL", "registro", [
        "REGISTRO DEL LABORATORIO.",
        "EL PRIMERO FUE EL MÉDICO DE",
        "GUARDIA. DESPUÉS LA ENFERMERA.",
        "DESPUÉS EL INVESTIGADOR QUE",
        "QUERÍA AVISAR A LA PRENSA.",
        "YA NO ME DISCUTEN NADA.",
        "POR FIN UN EQUIPO QUE ESCUCHA.",
        "- P.Z.",
    ]),
    ("EL ANTÍDOTO", "diario", [
        "DÍA 9. ALGUIEN DEL EQUIPO",
        "FABRICÓ UN ANTÍDOTO ANTES DE",
        "CAER. ROMPÍ LA FÓRMULA, PERO",
        "QUEDARON FRASCOS SUELTOS POR",
        "TODA LA CIUDAD.",
        "SI ALGUIEN LOS JUNTA...",
        "NO. NADIE ES TAN TONTO COMO",
        "PARA SALIR A LA CALLE.",
    ]),
    ("ANOMALÍA", "diario", [
        "DÍA 12. LAS CÁMARAS MUESTRAN",
        "A ALGUIEN QUE NO SE CONTAGIA.",
        "SALTA SOBRE MIS INFECTADOS",
        "COMO SI FUERA UN JUEGO.",
        "LLEVA UNA MOCHILA DE DELIVERY.",
        "SI ES INMUNE, SU SANGRE ES LA",
        "CURA. QUE NO LLEGUE HASTA ACÁ.",
        "- P.Z.",
    ]),
    ("ÚLTIMA PÁGINA", "diario", [
        "NO QUERÍA DESTRUIR EL MUNDO.",
        "QUERÍA QUE ME HICIERA CASO.",
        "UN EJÉRCITO QUE NO PROTESTA,",
        "NO VOTA, NO PIDE AUMENTO.",
        "EMPECÉ POR BUENOS AIRES",
        "PORQUE SI FUNCIONA ACÁ,",
        "FUNCIONA EN CUALQUIER LADO.",
        "¿QUIÉN SOS VOS PARA FRENARME?",
    ]),
]


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def check_text(txt):
    for ch in txt:
        if ch not in G and ch not in ACCENTED:
            raise SystemExit("glifo no soportado %r en %r" % (ch, txt))


def ink_text(img, x, y, txt, color=INK, drop=None):
    """Texto de la pixel font sin contorno. drop: random para tinta gastada."""
    px = img.load()
    for ch in txt:
        rows = glyph_rows(ch)
        for ry, row in enumerate(rows):
            for rx, c in enumerate(row):
                if c == " ":
                    continue
                if drop is not None and drop.random() < 0.12:
                    continue
                px[x + rx, y + ry] = color
        x += CW


def blend(img, x, y, c, a):
    """mezcla un píxel de color c con alfa a (0..1) sobre el papel."""
    px = img.load()
    if not (0 <= x < img.width and 0 <= y < img.height):
        return
    o = px[x, y]
    if o[3] == 0:
        return
    px[x, y] = tuple(round(o[i] * (1 - a) + c[i] * a) for i in range(3)) + (o[3],)


def stain(img, rnd, cx, cy, r, color, alpha):
    """mancha irregular: unión de círculos, borde más oscuro (se secó)."""
    blobs = [(cx, cy, r)] + [(cx + rnd.randint(-r, r), cy + rnd.randint(-r // 2, r // 2),
                              max(2, r // 2 + rnd.randint(-1, 2))) for _ in range(4)]
    inside = set()
    for (bx, by, br) in blobs:
        for y in range(by - br, by + br + 1):
            for x in range(bx - br, bx + br + 1):
                if (x - bx) ** 2 + (y - by) ** 2 <= br * br:
                    inside.add((x, y))
    for (x, y) in inside:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        blend(img, x, y, color, alpha * (1.6 if edge else 1.0))
    # gotitas
    for _ in range(3):
        a = rnd.random() * math.tau
        d = r + rnd.randint(2, 5)
        blend(img, round(cx + math.cos(a) * d), round(cy + math.sin(a) * d), color, alpha * 1.5)


def paper(kind, rnd):
    p = PAPERS[kind]
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    top, bot = 2, H - 3

    # silueta (con el borde de arriba roto en el diario, dentado en el remito)
    d.rectangle([2, top, W - 3, bot], fill=rgba(p["base"]))
    px = img.load()
    if kind == "diario":
        tear = 0
        for x in range(2, W - 2):
            tear = max(0, min(4, tear + rnd.choice((-1, 0, 0, 1))))
            for y in range(top, top + tear):
                px[x, y] = T
    elif kind == "remito":
        for x in range(2, W - 2):
            k = abs((x % 6) - 3)
            for y in range(top, top + k):
                px[x, y] = T
            for y in range(bot - k + 1, bot + 1):
                px[x, y] = T

    # envejecido: bordes más oscuros + moteado
    for y in range(H):
        for x in range(W):
            if px[x, y][3] == 0:
                continue
            dist = min(x - 2, W - 3 - x, y - top, bot - y)
            if dist < 4:
                blend(img, x, y, p["edge"], 0.55 - dist * 0.12)
            if rnd.random() < 0.05:
                blend(img, x, y, p["edge"], 0.35)

    # renglones / cuadrícula / banda
    if kind == "diario":
        for i in range(MAX_LINES):
            y = BODY_Y + i * LINE_H + 9
            for x in range(4, W - 4):
                blend(img, x, y, p["rule"], 0.7)
        y = TITLE_Y + 9 + 3
        for x in range(4, W - 4):
            blend(img, x, y, p["rule"], 0.9)
        for y in range(top, bot + 1):
            blend(img, TEXT_X - 4, y, p["margin"], 0.75)
    elif kind == "remito":
        y = TITLE_Y + 9 + 3
        for x in range(6, W - 6):
            if (x // 3) % 2 == 0:
                blend(img, x, y, p["rule"], 1.0)
    elif kind == "registro":
        for y in range(BODY_Y - 2, bot - 2, 6):
            for x in range(4, W - 4):
                blend(img, x, y, p["rule"], 0.8)
        for x in range(4, W - 4, 6):
            for y in range(BODY_Y - 2, bot - 2):
                blend(img, x, y, p["rule"], 0.8)
        for y in range(top, top + 19):
            for x in range(2, W - 2):
                blend(img, x, y, VIRUS_DK, 0.35)
    return img


def stamp(img, rnd, txt):
    """sello rojo con marco, gastado; arriba a la derecha."""
    w = len(txt) * CW + 5
    h = 15
    x0 = W - 8 - w
    y0 = 4
    layer = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(layer)
    d.rectangle([x0, y0, x0 + w, y0 + h], outline=STAMP)
    d.rectangle([x0 + 1, y0 + 1, x0 + w - 1, y0 + h - 1], outline=STAMP)
    ink_text(layer, x0 + 3, y0 + 3, txt, STAMP)
    lp = layer.load()
    for y in range(H):
        for x in range(W):
            c = lp[x, y]
            if c[3] and rnd.random() > 0.07:   # tinta que no agarró
                blend(img, x, y, c, 0.85)


def nota(i):
    title, kind, lines = NOTAS[i]
    rnd = random.Random(1000 + i)
    assert len(lines) <= MAX_LINES, title
    for t in [title] + lines:
        check_text(t)
        assert len(t) <= MAX_COLS, (len(t), t)

    img = paper(kind, rnd)
    # manchas de virus (antes del texto: la tinta queda arriba)
    for _ in range(rnd.randint(1, 2)):
        stain(img, rnd, rnd.randint(20, W - 20), rnd.randint(30, H - 14),
              rnd.randint(5, 9), VIRUS, 0.32)
    if i == 6:  # la última página: más castigada
        stain(img, rnd, W - 30, H - 22, 12, VIRUS_DK, 0.25)

    ink_text(img, TEXT_X, TITLE_Y, title, INK)
    stamp(img, rnd, "PRUEBA %d/7" % (i + 1))
    for n, line in enumerate(lines):
        ink_text(img, TEXT_X, BODY_Y + n * LINE_H, line, INK)
    _outline(img)
    return img


def nota_none():
    rnd = random.Random(999)
    img = paper("diario", rnd)
    px = img.load()
    for y in range(H):        # papel apagado, como en sombra
        for x in range(W):
            if px[x, y][3]:
                blend(img, x, y, (60, 64, 84), 0.55)
    q = Image.new("RGBA", (3 * CW, 9), T)
    ink_text(q, 0, 0, "???", INK_FADE)
    q = q.resize((q.width * 2, q.height * 2), Image.NEAREST)
    img.alpha_composite(q, ((W - q.width) // 2, (H - q.height) // 2))
    _outline(img)
    return img


def _outline(img):
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny] != OUTL:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = OUTL


# ---------------- pickup flotante ----------------
PW, PH, PN = 14, 16, 6
PAPER = (232, 220, 182, 255)
PAPER_S = (196, 180, 138, 255)
PAPER_HI = (250, 244, 222, 255)
GLOW = (96, 200, 128, 70)


def pick_frame(i):
    ph = i / PN * math.tau
    img = Image.new("RGBA", (PW, PH), T)
    d = ImageDraw.Draw(img)
    bob = round(math.sin(ph) * 1.5)
    top = 3 + bob
    d.ellipse([0, top - 2, PW - 1, top + 11], fill=GLOW)
    # hoja doblada en dos: mitad izquierda iluminada, derecha en sombra
    d.rectangle([2, top, 6, top + 9], fill=PAPER_HI)
    d.rectangle([7, top, 11, top + 9], fill=PAPER_S)
    d.line([(7, top), (7, top + 9)], fill=PAPER)
    # renglones escritos
    for k in range(3):
        d.line([(3, top + 2 + k * 2), (5, top + 2 + k * 2)], fill=INK)
        d.line([(8, top + 2 + k * 2), (10, top + 2 + k * 2)], fill=(80, 84, 110, 255))
    # puntito de sello rojo
    d.point([(10, top + 8)], fill=STAMP)
    if i == 2:
        d.line([(3, top + 7), (5, top + 5)], fill=(255, 255, 255, 220))
    elif i == 3:
        d.line([(8, top + 7), (10, top + 5)], fill=(255, 255, 255, 220))
    _outline(img)
    return img


def icon():
    img = Image.new("RGBA", (9, 11), T)
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, 7, 9], fill=PAPER)
    d.polygon([(5, 1), (7, 1), (7, 3)], fill=T)        # esquina doblada
    d.line([(5, 1), (5, 3), (7, 3)], fill=PAPER_S)
    for k in range(3):
        d.line([(2, 4 + k * 2), (5 if k == 0 else 6, 4 + k * 2)], fill=INK)
    _outline(img)
    return img


# ---------------- inventario (pausa -> MOCHILA) ----------------
SW, SH = 22, 26
CURSOR = (255, 206, 110, 255)     # ámbar del menú


def slot(found):
    """casillero de la fila de pruebas: papel chico o hueco con '?'."""
    img = Image.new("RGBA", (SW, SH), T)
    d = ImageDraw.Draw(img)
    if found:
        d.rectangle([3, 2, SW - 4, SH - 3], fill=PAPER)
        d.polygon([(SW - 8, 2), (SW - 4, 2), (SW - 4, 6)], fill=T)   # esquina doblada
        d.line([(SW - 8, 2), (SW - 8, 6), (SW - 4, 6)], fill=PAPER_S)
        for k in range(5):
            d.line([(5, 6 + k * 3), (SW - 7 if k == 0 else SW - 6, 6 + k * 3)], fill=INK)
        d.rectangle([SW - 9, SH - 8, SW - 6, SH - 6], fill=STAMP)
    else:
        d.rectangle([3, 2, SW - 4, SH - 3], fill=(40, 44, 62, 200))
        ink_text(img, (SW - 5) // 2, (SH - 9) // 2, "?", (110, 118, 146, 255))
    _outline(img)
    return img


def cursor():
    img = Image.new("RGBA", (SW + 4, SH + 4), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SW + 3, SH + 3], outline=CURSOR)
    d.rectangle([1, 1, SW + 2, SH + 2], outline=(180, 130, 50, 255))
    return img


def main():
    slot(True).save(f"{OUT}/nota_slot_found.png")
    slot(False).save(f"{OUT}/nota_slot_empty.png")
    cursor().save(f"{OUT}/nota_cursor.png")
    notas = [nota(i) for i in range(len(NOTAS))]
    for i, im in enumerate(notas, 1):
        im.save(f"{OUT}/nota_{i}.png")
    none = nota_none()
    none.save(f"{OUT}/nota_none.png")
    picks = [pick_frame(i) for i in range(PN)]
    for i, im in enumerate(picks, 1):
        im.save(f"{OUT}/nota_pick_{i}.png")
    ic = icon()
    ic.save(f"{OUT}/nota_icon.png")

    # hoja de referencia sobre el fondo de la escena
    cols = 4
    sheet = Image.new("RGBA", (cols * (W + 6) + 6, 2 * (H + 6) + 30), (16, 20, 40, 255))
    for k, im in enumerate(notas + [none]):
        sheet.alpha_composite(im, (6 + (k % cols) * (W + 6), 6 + (k // cols) * (H + 6)))
    y = 2 * (H + 6) + 8
    for k, im in enumerate(picks):
        sheet.alpha_composite(im, (6 + k * (PW + 4), y))
    sheet.alpha_composite(ic, (6 + PN * (PW + 4) + 8, y + 2))
    sheet.save(f"{OUT}/notas_sheet.png")
    print(f"{len(notas)} notas {W}x{H} + nota_none, {PN} pickups {PW}x{PH}, ícono  ->  {OUT}/")


if __name__ == "__main__":
    main()
