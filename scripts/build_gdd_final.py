#!/usr/bin/env python3
"""
build_gdd_final.py — arma el GDD final (HTML → PDF) a partir de los .md de
gdd_final/, con el diseño del avance del 18/09 (avance_devolucion/avance_gdd.html:
portada oscura, páginas crema, Press Start 2P + Nunito).

A diferencia del avance (páginas de alto fijo armadas a mano), el contenido
FLUYE entre páginas: cada capítulo empieza en página nueva y la numeración la
pone el navegador (@page con cajas de margen, Chrome ≥ 131).

Los .md usan un Markdown chico (títulos, tablas, listas, citas, código,
imágenes) que convierte md_a_html(). Extras:
  ![](obj:Level2/Piston)      imagen del primer cuadro de un objeto de game.json
  <!-- mapa:Level1 -->        las tiras del mapa del nivel (gen_mapas_gdd.py)
  <!-- galeria:personajes --> tiras de caminata de los zombies, Lio y el jefe
  <!-- galeria:notas -->      el arte de las 7 notas
  <!-- paleta:lio -->         muestras de color (PALETAS)
  <!-- props:Level1 -->       galería de objetos del escenario (PROPS)
  <!-- capturas:menus -->     capturas del juego (CAPTURAS, de scripts/capturas_gdd.py)

Salida: gdd_final/gdd_final.html y "gdd_final/Paciente Zero - GDD final.pdf".
Requiere: python3 scripts/gen_mapas_gdd.py (los mapas) y el puppeteer de
~/Escritorio/gdevelop-mcp. Uso:  python3 scripts/build_gdd_final.py
"""
import html
import json
import os
import re
import subprocess
import sys

from PIL import Image

DIR = "gdd_final"
GAME = "game/game.json"
HTML_OUT = f"{DIR}/gdd_final.html"
PDF_OUT = f"{DIR}/Paciente Zero - GDD final.pdf"
PUPPETEER = os.path.expanduser("~/Escritorio/gdevelop-mcp/node_modules/puppeteer")
PIE = "Paciente Zero — GDD final · UNER 2026"

# (categoría de la tabla de Thompson, archivo .md o (archivo, secciones de ##))
CAPITULOS = [
    ("Entrega", "cumplimiento_consigna.md"),
    ("Marketing", ("otros_apartados.md", ["1. Marketing"])),
    ("DDJ", "historia.md"),
    ("Artístico", ("otros_apartados.md", ["2. Apariencia y ambientación"])),
    ("Juego", "mecanica.md"),
    ("Juego", "controles_hud_menus.md"),
    ("Técnico · Juego", ("otros_apartados.md", ["3. Sistema de cámara", "4. Mundo y física del juego"])),
    ("Juego", "personajes.md"),
    ("Técnico · Artístico", ("otros_apartados.md", ["5. Animaciones"])),
    ("Juego", "walkthrough.md"),
    ("Técnico", ("otros_apartados.md", ["6. Diseño de programación", "7. Diseño de sonido"])),
    ("Apéndice", "game_testing.md"),
    ("Apéndice", ("otros_apartados.md", ["8. Créditos", "9. Historial de revisiones"])),
]

# paletas (colores reales de los generadores: gen_*.py, palette_night.py y la ficha de Lio)
PALETAS = {
    "lio": ("Lio (de la ficha de personaje)", [
        ((24, 24, 34), "Contorno"), ((226, 178, 140), "Piel"), ((117, 170, 216), "Camiseta"),
        ((74, 120, 168), "Sombra camiseta"), ((232, 232, 226), "Short"), ((44, 40, 46), "Botines")]),
    "zombies": ("Familia zombie (todos los zombies)", [
        ((24, 24, 34), "Contorno"), ((150, 190, 150), "Piel"), ((108, 150, 116), "Sombra piel"),
        ((214, 74, 74), "Ojos"), ((120, 40, 44), "Boca")]),
    "jefe": ("Paciente Zero", [
        ((34, 32, 40), "Pelo"), ((66, 64, 78), "Brillo del pelo"), ((190, 198, 202), "Guardapolvo"),
        ((116, 172, 223), "Camiseta celeste"), ((232, 236, 240), "Camiseta blanca"),
        ((90, 200, 100), "Líquido de la jeringa"), ((220, 40, 40), "Contorno de aviso")]),
    "antidoto": ("Antídoto", [
        ((26, 22, 34), "Contorno"), ((52, 140, 92), "Líquido (sombra)"), ((96, 200, 128), "Líquido"),
        ((168, 240, 176), "Brillo"), ((110, 78, 46), "Corcho (sombra)"), ((150, 108, 66), "Corcho"),
        ((150, 176, 178), "Vidrio")]),
    "mochila": ("Mochila de repartidor", [
        ((26, 22, 34), "Contorno"), ((255, 90, 0), "Cuerpo (naranja)"), ((204, 62, 0), "Sombra"),
        ((255, 140, 60), "Brillo"), ((34, 30, 40), "Correas"), ((250, 246, 238), "Parche")]),
    "virus": ("Virus (un solo tono, con sombra y luz)", [
        ((18, 12, 26), "Contorno"), ((176, 58, 74), "Sombra"), ((206, 82, 96), "Base"),
        ((232, 114, 124), "Luz"), ((250, 156, 164), "Punta de espiga")]),
    "noche": ("Escenario de noche (base de los tres niveles)", [
        ((16, 20, 40), "Fondo / cielo"), ((36, 40, 66), "Nubes"), ((46, 52, 80), "Niebla"),
        ((52, 57, 72), "Hormigón"), ((80, 86, 104), "Canto iluminado"), ((28, 40, 64), "Río"),
        ((94, 118, 148), "Reflejo en el agua")]),
    "acentos": ("Acentos de luz (lo que se lee sobre la noche)", [
        ((255, 196, 120), "Farol de sodio (L1, L3)"), ((255, 150, 60), "Fuego"),
        ((255, 206, 110), "HUD / bordes en L1"), ((196, 238, 228), "Tubos del lab (L2)"),
        ((140, 230, 140), "Tanques y verde tóxico"), ((110, 210, 180), "Monitores (L2)"),
        ((255, 64, 52), "Alarma (L2, arena)")]),
}

# galerías de props: (objeto de game.json, nombre, descripción)
PROPS = {
    "Level1": ("Nivel 1 — La costanera", [
        ("Level1/Farol", "Farol", "luz de sodio; se lo pisa"), ("Level1/Poste", "Poste", "se trepa"),
        ("Level1/ArbolAlto", "Árbol alto", "copa atravesable"), ("Level1/ArbolBajo", "Árbol bajo", "copa atravesable"),
        ("Level1/BancoPlaza", "Banco", "atravesable"), ("Level1/Toldo", "Puesto con toldo", "techo atravesable"),
        ("Level1/Balcon", "Balcón", "atravesable"), ("Level1/EscaleraIncendio", "Escalera de incendio", "atravesable"),
        ("Level1/Colchon", "Colchón", "rebota"), ("Level1/Tacho", "Tacho con fuego", "luz y calor"),
        ("Level1/PuenteA", "Puente", "macizo, sobre el agua"), ("Level1/PuenteC", "Puente alto", "macizo"),
        ("Level1/DrainPipe", "Desagüe", "del muro de la costanera"), ("Level1/WallBreakL", "Muro roto", "borde del río"),
        ("Level1/Meta", "Meta", "fin del nivel"), ("Level1/Grafiti_Malvinas", "Pintada", "en el muro")]),
    "Level2": ("Nivel 2 — El laboratorio", [
        ("Level2/Piston", "Pistón", "verde = firme, rojo = baja"), ("Level2/Contencion", "Tubo de contención", "con un virus adentro"),
        ("Level2/ContencionRota", "Tubo roto", "estalla al pasar"), ("Level2/Estante", "Estante", "atravesable"),
        ("Level2/Gabinete", "Gabinete", "se pasa con el ducto"), ("Level2/Vent", "Rejilla del ducto", "el aire eleva"),
        ("Level2/WetSign", "Piso mojado", "aviso de piso encerado"), ("Level2/GlassSpikes", "Vidrios rotos", "fondo de los pozos"),
        ("Level2/EscotillaBorde", "Escotilla", "boca del corredor"), ("Level2/LampFixture", "Tubo fluorescente", "estable, intermitente o roto")]),
    "Level3": ("Nivel 3 — Del lab al Obelisco", [
        ("Level3/FachadaFrances", "Edificio francés", "fachada"), ("Level3/FachadaDeptos", "Departamentos", "fachada de los 60"),
        ("Level3/FachadaPh", "PH", "fachada"), ("Level3/FachadaBar", "Bar de esquina", "vidrieras cálidas"),
        ("Level3/ToldoRebote", "Toldo", "rebota ~84 px"), ("Level3/Marquesina", "Marquesina", "atravesable"),
        ("Level3/Charco", "Charco electrificado", "−1 vida"), ("Level3/AutoQuemado", "Auto quemado", "decorado"),
        ("Level3/Patrullero", "Patrullero", "con sirena"), ("Level3/Colectivo", "Colectivo", "cruzado en la plaza"),
        ("Level3/TaxiVolcado", "Taxi volcado", "decorado"), ("Level3/BanderaMastil", "Bandera", "8 en el nivel"),
        ("Level3/EstatuaColumnaIzq", "Pirámide", "el jefe se clava acá"), ("Level3/EstatuaBustoIzq", "Busto con barbijo", "trampolín"),
        ("Level3/ObeliscoGrande", "Obelisco", "centro de la arena"), ("Level3/Barricada", "Barricada", "cierra la arena")]),
}

# capturas del juego (scripts/capturas_gdd.py): grupo -> [(archivo, epígrafe)]
CAPTURAS = {
    "hud": [("l1_hud", "Jugando en el Nivel 1: vidas, antídotos 2/4, puntos y reloj.")],
    "menus": [("menu", "Menú principal con la tabla TOP 5."),
              ("iniciales", "Al terminar una partida que entra en el TOP 5: las tres iniciales."),
              ("pausa", "Pausa: volúmenes y ayuda de teclas."),
              ("mochila", "La mochila (pausa → I): 4 de 7 pruebas encontradas."),
              ("nota", "Una prueba recién agarrada: el juego se congela."),
              ("victoria", "Victoria del Nivel 1 con el desglose del puntaje.")],
    "niveles": [("l1_inicio", "Nivel 1: el arranque en la costanera, con la pintada de Malvinas."),
                ("l1_rio", "Nivel 1: puentes sobre el río, el Obelisco a lo lejos."),
                ("l2_lab", "Nivel 2: el laboratorio, con los tubos de contención abajo."),
                ("l2_alarma", "Nivel 2: la zona de alarma del final."),
                ("l3_calle", "Nivel 3: la calle del hospital, entre edificios."),
                ("l3_llegada", "Nivel 3: llegando al Obelisco, vapor del subte y marquesinas.")],
    "mecanicas": [("l1_horda", "Nivel 1: Lio cruza el río corriendo sobre la horda."),
                  ("l2_pistones", "Nivel 2: los pistones sobre el pozo."),
                  ("l2_subsuelo", "Nivel 2: el corredor del subsuelo (ruta opcional)."),
                  ("l3_corrientes", "Nivel 3: postes y cables sobre el charco electrificado.")],
    "jefe": [("jefe", "Paciente Zero apunta: contorno rojo, está por embestir."),
             ("jefe_clavado", "Clavado en la pirámide, con estrellitas: la ventana para pisarlo.")],
}

ZOMBIES = [("Vecina", "f"), ("Obrero rengo", "m"), ("Arrastrada", "d"), ("Adolescente", "n"),
           ("Anciana", "v"), ("Obrero de obra", "o"), ("Corredor", "j"), ("Médico", "med"),
           ("Enfermera", "enf"), ("Investigador", "inv"), ("Hincha", "hin"),
           ("Repartidor", "rep"), ("Policía", "pol")]

# --------------------------------------------------------------- objetos del juego
_g = json.load(open(GAME, encoding="utf-8"))
_res = {r["name"]: r["file"] for r in _g["resources"]["resources"]}
_lays = {l["name"]: l for l in _g["layouts"]}


def img_objeto(ref):
    """"Level2/Piston" -> ruta (relativa a gdd_final/) del primer cuadro."""
    escena, nombre = ref.split("/")
    o = next(o for o in _lays[escena]["objects"] if o["name"] == nombre)
    if o["type"] == "Sprite":
        r = o["animations"][0]["directions"][0]["sprites"][0]["image"]
    elif o["type"] == "TiledSpriteObject::TiledSprite":
        r = o["texture"]
    else:
        raise SystemExit(f"{ref}: el objeto no tiene imagen ({o['type']})")
    return "../game/" + _res[r]


def asset(p):
    return "../game/assets/" + p


# --------------------------------------------------------------- Markdown chico
def inline(s):
    s = html.escape(s, quote=False)

    def imagen(m):
        src = m.group(2)
        src = img_objeto(src[4:]) if src.startswith("obj:") else src
        return f'<img class="ico" alt="{m.group(1)}" src="{src}">'
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", imagen, s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    return s


def lista(items, i=0, base=0):
    """items: [(indent, ordenada, texto)]; devuelve (html, índice siguiente)."""
    tag = "ol" if items[i][1] else "ul"
    out = [f"<{tag}>"]
    while i < len(items) and items[i][0] >= base:
        ind, _, txt = items[i]
        if ind > base:
            sub, i = lista(items, i, ind)
            out[-1] = out[-1][:-5] + sub + "</li>"
            continue
        out.append(f"<li>{inline(txt)}</li>")
        i += 1
    out.append(f"</{tag}>")
    return "".join(out), i


def md_a_html(md, extras):
    lines = md.split("\n")
    out, par, i = [], [], 0

    def cerrar_par():
        if par:
            out.append(f"<p>{inline(' '.join(par))}</p>")
            par.clear()
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if st.startswith("```"):
            cerrar_par()
            j = i + 1
            while not lines[j].strip().startswith("```"):
                j += 1
            txt = chr(10).join(lines[i + 1:j])
            cls = "nota" if txt.startswith("PRUEBA") else "diagrama"   # notas del diario en papel
            out.append(f'<pre class="{cls}">{html.escape(txt)}</pre>')
            i = j + 1
            continue
        if st.startswith("<!--"):
            cerrar_par()
            m = re.match(r"<!--\s*(\w+):(\w+)\s*-->", st)
            if m:
                out.append(extras(m.group(1), m.group(2)))
            i += 1
            continue
        m = re.match(r"(#{1,4})\s+(.*)", st)
        if m and not ln.startswith(" "):
            cerrar_par()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            i += 1
            continue
        if st.startswith(">"):
            cerrar_par()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<blockquote>{inline(" ".join(q))}</blockquote>')
            continue
        if st.startswith("|"):
            cerrar_par()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            sep = lambda r: all(re.match(r"^:?-+:?$", c) for c in r)
            head, body = rows[0], [r for r in rows[1:] if not sep(r)]
            if all(not h for h in head):
                th = ""        # tabla sin encabezado (ficha clave | valor)
            else:
                th = "<thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in head) + "</tr></thead>"
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(f"<table>{th}<tbody>{tb}</tbody></table>")
            continue
        if re.match(r"\s*(- |\d+\. )", ln):
            cerrar_par()
            items = []
            while i < len(lines) and lines[i].strip():
                l2 = lines[i]
                mm = re.match(r"(\s*)(- |\d+\. )(.*)", l2)
                if mm:
                    items.append([len(mm.group(1)), mm.group(2) != "- ", mm.group(3)])
                elif items:
                    items[-1][2] += " " + l2.strip()
                i += 1
            out.append(lista([tuple(x) for x in items])[0])
            continue
        if not st:
            cerrar_par()
        else:
            par.append(st)
        i += 1
    cerrar_par()
    return "\n".join(out)


# --------------------------------------------------------------- imágenes extra
def mapa(nivel):
    n = 1
    tiras = []
    while os.path.exists(f"{DIR}/mapas/{nivel}_{n}.png"):
        tiras.append(f'<img class="mapa" src="mapas/{nivel}_{n}.png">')
        n += 1
    if not tiras:
        raise SystemExit(f"faltan los mapas de {nivel}: python3 scripts/gen_mapas_gdd.py")
    return '<div class="mapas">' + "".join(tiras) + "</div>"


def galeria_personajes():
    cards = []
    lio = "".join(f'<img src="{asset(f"Player/Player_{a}_1.png")}">' for a in ("Idle", "Run", "Fall", "Hit", "Death"))
    cards.append(f'<div class="card ancho"><h4>Lio</h4><div class="imgwrap">{lio}</div>'
                 f'<div class="meta">Idle · Run · Jump/Fall · Hit · Death</div></div>')
    jefe = "".join(f'<img src="{asset(f"Jefe/jefe_{a}.png")}">' for a in ("walk_1", "walk_3", "carga_3", "expuesto_1"))
    cards.append(f'<div class="card ancho"><h4>Paciente Zero</h4><div class="imgwrap">{jefe}</div>'
                 f'<div class="meta">Walk · Carga · Expuesto (48×51)</div></div>')
    for nombre, k in ZOMBIES:
        cards.append(f'<div class="card"><h4>{nombre}</h4><div class="imgwrap">'
                     f'<img class="sheet" src="{asset(f"Zombie_{k.upper() if len(k) == 1 else k.capitalize()}/zombie_{k}_walk_sheet.png")}">'
                     f'</div></div>')
    virus = "".join(f'<img src="{img_objeto(r)}">' for r in ("Level1/Virus1", "Level1/Antidoto", "Level1/Mochila", "Level1/NotaPick"))
    cards.append(f'<div class="card ancho"><h4>Virus, antídoto, mochila y prueba</h4><div class="imgwrap">{virus}</div></div>')
    return '<div class="gallery">' + "".join(cards) + "</div>"


def galeria_notas():
    """el arte real de cada nota (con el texto horneado, gen_notas.py)."""
    figs = "".join(f'<figure><img src="{asset(f"UI/Notas/nota_{n}.png")}"></figure>' for n in range(1, 8))
    return f'<div class="notas">{figs}</div>'


def hexa(c):
    return "#%02X%02X%02X" % c


def paleta(nombre):
    titulo, colores = PALETAS[nombre]
    items = "".join(f'<div class="item"><div class="swatch" style="background:{hexa(c)}"></div>'
                    f'<b>{hexa(c)}</b><br>{uso}</div>' for c, uso in colores)
    return f'<div class="paleta"><h4>{titulo}</h4><div class="palette">{items}</div></div>'


def props(nivel):
    titulo, lista_ = PROPS[nivel]
    cards = []
    for ref, nombre, desc in lista_:
        src = img_objeto(ref)
        w, h = Image.open(os.path.join(DIR, src)).size
        k = max(1, min(3, 100 // w, 60 // h))   # escala entera: el pixel art no se deforma
        cards.append(f'<div class="prop"><div class="imgwrap"><img src="{src}" style="width:{w * k}px"></div>'
                     f'<div class="name">{nombre}</div><div class="dims">{w}×{h} · {desc}</div></div>')
    return f'<h3>{titulo}</h3><div class="propgrid">{"".join(cards)}</div>'


def capturas(grupo):
    figs = "".join(f'<figure><img src="capturas/{f}.png"><figcaption>{t}</figcaption></figure>'
                   for f, t in CAPTURAS[grupo])
    uno = " uno" if len(CAPTURAS[grupo]) == 1 else ""
    return f'<div class="capturas{uno}">{figs}</div>'


def extras(tipo, arg):
    if tipo == "paleta":
        return paleta(arg)
    if tipo == "props":
        return props(arg)
    if tipo == "capturas":
        return capturas(arg)
    if tipo == "mapa":
        return mapa(arg)
    if tipo == "galeria" and arg == "personajes":
        return galeria_personajes()
    if tipo == "galeria" and arg == "notas":
        return galeria_notas()
    raise SystemExit(f"marcador desconocido: {tipo}:{arg}")


# --------------------------------------------------------------- capítulos
def secciones(md, nombres):
    """de un .md con varios '## n. Título', devuelve esas secciones."""
    partes = re.split(r"(?m)^## ", md)
    elegidas = {p.split("\n", 1)[0].strip(): p.split("\n", 1)[1] for p in partes[1:]}
    return [(re.sub(r"^\d+\.\s*", "", n), elegidas[n]) for n in nombres]


def capitulo(cat, fuente):
    if isinstance(fuente, str):
        md = open(f"{DIR}/{fuente}", encoding="utf-8").read()
        m = re.match(r"#\s+(.*)\n", md)
        titulo, cuerpo = m.group(1), md[m.end():]
        if fuente == "otros_apartados.md":
            raise SystemExit("otros_apartados.md va por secciones")
    else:
        md = open(f"{DIR}/{fuente[0]}", encoding="utf-8").read()
        secs = secciones(md, fuente[1])
        titulo = " · ".join(t for t, _ in secs)
        cuerpo = "\n\n".join((f"## {t}\n{c}" if len(secs) > 1 else c) for t, c in secs)
        if fuente[1] == ["2. Apariencia y ambientación"]:
            cuerpo += ("\n\n## Así se ve\n\n<!-- capturas:niveles -->\n\n## Paleta\n\n<!-- paleta:noche -->\n\n"
                       "<!-- paleta:acentos -->\n\n## Objetos del escenario\n\nTodos dibujados por código, como en el "
                       "avance; tamaño en píxeles del juego.\n\n<!-- props:Level1 -->\n\n<!-- props:Level2 -->\n\n"
                       "<!-- props:Level3 -->\n")
    ident = re.sub(r"\W+", "-", titulo.lower()).strip("-")
    return titulo, ident, (f'<section class="capitulo" id="{ident}"><div class="pill pix">{cat}</div>'
                           f'<h1 class="pix">{inline(titulo)}</h1>{md_a_html(cuerpo, extras)}</section>')


# --------------------------------------------------------------- portada e índice
def portada():
    sprites = [("Level1/Player", "LIO"), ("Level1/ZombieF", ""), ("Level2/ZombieMed", ""),
               ("Level2/ZombieHin", ""), ("Level2/ZombiePol", ""), ("Level3/ZombieJ", ""),
               ("Level3/PacienteZero", "PACIENTE ZERO"), ("Level1/Virus1", ""), ("Level1/Antidoto", ""),
               ("Level1/Mochila", "")]
    celdas = "".join(f'<div class="cell"><img src="{img_objeto(r)}"><div class="lbl">{t}</div></div>' for r, t in sprites)
    return f"""
<section class="portada">
  <div class="uni">UNIVERSIDAD NACIONAL DE ENTRE RÍOS<br>
    <span>FACULTAD DE CIENCIAS DE LA ADMINISTRACIÓN</span><br>
    <span class="t">TECNICATURA UNIVERSITARIA EN DESARROLLO WEB</span></div>
  <p class="catedra">Cátedra:</p>
  <div class="pill pix">Multimedia y Juegos en Web</div>
  <p class="docentes">Docentes: Fabien M. Pineda · Hernan I. Hernandez · Juan I. Carubia</p>
  <h1 class="pix titulo">PACIENTE ZERO</h1>
  <div class="pill pix oscura">DOCUMENTO DE DISEÑO DEL JUEGO — ENTREGA FINAL</div>
  <div class="coverimgrow">{celdas}</div>
  <img class="franja" src="capturas/jefe.png">
  <p class="bajada">Plataformero 2D de acción arcade hecho en GDevelop. Buenos Aires tomada por un
  virus zombie: Lio, el único inmune, cruza la ciudad hasta el Obelisco para enfrentar al
  científico que empezó todo.</p>
  <div class="integrante"><p class="pix">Integrante: Walter Frías</p>
    <p class="m">Trabajo individual — Entrega final · Noviembre 2026</p></div>
  <div class="anio pix">2026</div>
</section>"""


def indice(caps):
    filas = "".join(f'<li><span class="cat">{c}</span><a href="#{i}">{t}</a></li>' for c, t, i in caps)
    return f"""
<section class="capitulo indice"><div class="pill pix">Contenido</div><h1 class="pix">Índice</h1>
<p>Los apartados siguen la plantilla del Documento de Diseño de Juego (DDJ) de
Thompson, <i>Videojuegos — Manual para diseñadores gráficos</i>, págs. 106–107.</p>
<ol class="toc">{filas}</ol>
</section>"""


CSS = open(os.path.join(os.path.dirname(__file__), "build_gdd_final.css"), encoding="utf-8").read()


def main():
    caps, cuerpo = [], []
    for cat, fuente in CAPITULOS:
        t, ident, h = capitulo(cat, fuente)
        caps.append((cat, t, ident))
        cuerpo.append(h)
    doc = (f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Paciente Zero — GDD final</title>'
           f'<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">'
           f'<style>{CSS.replace("%PIE%", PIE)}</style></head><body>'
           f'{portada()}{indice(caps)}{"".join(cuerpo)}</body></html>')
    open(HTML_OUT, "w", encoding="utf-8").write(doc)
    print(f"{HTML_OUT}: {len(caps)} capítulos")
    if "--solo-html" in sys.argv:
        return
    js = f"""
const p = require({json.dumps(PUPPETEER)});
(async () => {{
  const b = await p.launch({{headless: 'new', args: ['--allow-file-access-from-files']}});
  const pg = await b.newPage();
  await pg.goto('file://' + {json.dumps(os.path.abspath(HTML_OUT))}, {{waitUntil: 'networkidle0'}});
  await pg.evaluateHandle('document.fonts.ready');
  await pg.pdf({{path: {json.dumps(PDF_OUT)}, preferCSSPageSize: true, printBackground: true}});
  await b.close();
}})();"""
    subprocess.run(["node", "-e", js], check=True)
    pags = subprocess.run(["pdfinfo", PDF_OUT], capture_output=True, text=True).stdout
    print(PDF_OUT, re.search(r"Pages:\s+(\d+)", pags).group(1), "páginas")


if __name__ == "__main__":
    main()
