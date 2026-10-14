# Documento de Diseño — Paciente Zero

> Prototipo de plataformas 2D — UNER, Multimedia y Juegos Web.
> Motor: GDevelop. Trabajo individual.
> Este documento cubre los puntos 9.a y 9.b de `consigna.md` (temática/
> narrativa y ficha de personaje), y de paso el resto del diseño
> necesario para cumplir los puntos 3, 6 y 7 (niveles, menú de
> opciones, sonido).
>
> Título confirmado: **Paciente Zero** (2026-09-02). El resto de
> textos narrativos (diario, diálogos) sigue siendo propuesta
> editable.

## 1. Tema y narrativa

Un brote zombie golpea la **Ciudad de Buenos Aires**. El/la
protagonista es **el/la único/a humano/a inmune al virus** y se abre
paso desde la calle hasta el foco de la infección, enfrentando oleadas
de infectados cada vez más densas, para encontrar y derrotar al
**Paciente Zero**: la persona (o experimento) que originó el brote.

Motivación del villano: Paciente Zero es un científico que provocó
el brote de forma deliberada, buscando dominar el mundo controlando
a los infectados — no fue un accidente de laboratorio.

Tono: **arcade retro pixel-art**, más cercano a "Zombies Ate My
Neighbors" que a survival horror — ligereza y ritmo de plataformas
clásico, no terror.

Arco narrativo en 3 niveles + tutorial:

| Escena | Rol narrativo |
|---|---|
| Tutorial | Punto de partida seguro (ej. una casa/refugio) donde se enseñan los controles sin peligro real. |
| Nivel 1 — La calle | Primer contacto con el brote. Zombies sueltos, pocos obstáculos. Introduce la mecánica de stomp. |
| Nivel 2 — El interior | Un hospital o laboratorio, donde se empieza a entender el origen del brote (pistas ambientales, opcional). Más densidad de enemigos y algún hazard de plataforma (pinchos, huecos). |
| Nivel 3 — Confrontación | Arena final. Combate contra el Paciente Zero. |

## 2. Ficha del personaje jugable

- **Nombre:** Lio (guiño a Messi, coherente con la ambientación
  argentina; renombrado 2026-09-13, antes d10ego/guiño a Maradona)
- **Rol:** único/a humano/a inmune al virus, sin entrenamiento de
  combate — su única arma es su propio peso: elimina zombies saltando
  sobre sus cabezas (stomp), igual que un plataformero clásico.
- **Vidas:** 3 (confirmado)
- **Daño:** pierde una vida al tocar un zombie por el costado o
  recibir un golpe; invulnerabilidad breve tras recibir daño
  (estándar en GDevelop: timer + parpadeo).
- **Movimiento:** correr, saltar — behavior nativo `Platformer
  Character` de GDevelop, sin habilidades extra (doble salto, dash)
  para no ampliar el scope de animación.
- **Animaciones necesarias (mínimo):** idle, run, jump (subida),
  fall (bajada), hit/damage, death. El stomp puede reusar el frame de
  "fall" — no hace falta una animación de ataque dedicada, coherente
  con la mecánica elegida.
- **Tamaño de sprite:** 32×34 (canvas final; base 32×32 estirada a
  32×34 para igualar la escala de `Zombie_O` y el resto de los
  sprites del juego).

## 3. Enemigos

### Zombie (infectado)
- **Un solo comportamiento, varias variantes visuales.** Todos
  patrullan una plataforma de punta a punta (invierten dirección al
  llegar al borde de su tramo), mueren de un stomp y dañan al jugador
  por contacto lateral. Lo que cambia entre variantes es el *aspecto*
  y la *velocidad de patrulla* (una lectura rápida de personaje: un
  oficinista, una anciana encorvada, un obrero rengo, un corredor
  volcado hacia adelante, un adolescente con tics, etc.), no las reglas.
- Sirven para poblar la ciudad y dar variedad de silueta sin sumar
  mecánicas nuevas ni trabajo de diseño por enemigo.
- Animaciones por variante: walk (8 frames), death (reusa un frame de
  walk o squash simple).

### Paciente Zero (jefe final, Nivel 3)
- Versión mutada/más grande del zombie común — puede reusar la
  paleta y la estructura de sprite de los zombies para ahorrar trabajo
  de arte, escalado o con detalles extra.
- **Patrón de combate** (pensado para la mecánica de solo-stomp):
  1. Telegrafía un ataque (ej. se agacha 1 segundo antes de embestir).
  2. Ataca (embestida horizontal o "pisada" que el jugador esquiva
     saltando).
  3. Tras el ataque queda expuesto un instante — única ventana para
     stompearlo.
  - Necesita **3 stomps** para morir, con breve invulnerabilidad
    entre cada uno (mismo patrón que jefes clásicos de plataformas
    tipo Bowser/Koopa).
- Animaciones mínimas: idle/telegraph, ataque, hit, death.

## 4. Niveles — estructura y tiempos

Objetivo: **30 minutos totales** de juego (punto 4 de la consigna).

| Nivel | Duración estimada | Contenido |
|---|---|---|
| Tutorial | ~3–5 min | Correr, saltar, stomp de práctica sobre 1-2 zombies "de entrenamiento", sin posibilidad real de perder. |
| Nivel 1 | ~7–8 min | Plataformas simples, zombies de patrulla (varias variantes visuales del mismo comportamiento), checkpoint a mitad de nivel. |
| Nivel 2 | ~7–8 min | Más densidad de zombies, 1 hazard nuevo (pinchos/huecos), checkpoint. |
| Nivel 3 (boss) | ~7–8 min | Arena de combate contra Paciente Zero + pantalla de victoria. |

Total: ~24–29 min, dentro del margen pedido.

## 5. Menú de opciones (punto 6 de la consigna)

Mínimo viable:
- Volumen de música
- Volumen de efectos (SFX)
- Reiniciar nivel actual
- Salir / volver al menú principal

## 6. Coleccionables y narrativa ambiental

Decidido en la lluvia de ideas del HCD (ver `HIGH_CONCEPT.md`).

### Antídotos (único coleccionable de gameplay)
- Frascos repartidos por los niveles, en rutas alternativas / plataformas
  opcionales (no en el camino directo a la meta).
- Contador en el HUD: ícono del frasco + `n/4` (se pone verde con 4/4).
- **4 antídotos por nivel; juntar los 4 = 1 vida extra** (confirmado
  2026-09-02).
- Juntar todos los de un nivel = +1000 en la pantalla de victoria.
- ~~Sin tabla de récords ni guardado en disco~~ → cambiado el 09/10:
  hay puntaje y un único récord (ver "Puntaje" abajo).

### Puntaje y récord (decidido 2026-10-09)
- Stomp +100, antídoto +250 (con "+100"/"+250" flotante).
- Al ganar el nivel: meta +1000, +500 por vida restante, +1000 si se
  juntaron los 4 antídotos. Desglose en la pantalla de victoria.
- Lo ganado en un nivel se suma al total recién al ganar: morir, Game
  Over o reintentar lo descartan (no se puede farmear). El total vuelve a
  0 al apretar "Jugar".
- Un solo récord guardado en el navegador (sin nombres ni tabla), que
  se muestra en el menú principal y como "¡NUEVO RÉCORD!" al ganar.
- HUD: corazones | antídotos `n/4` | `PUNTOS 000000` (L3: cartel del
  jefe centrado arriba), en la pixel font del menú.

### Mochila de repartidor (power-up de planeo, confirmado 2026-09-12)
- Prop de escenario ambientado en la ciudad (delivery), no un
  coleccionable de conteo como el antídoto: es un ítem único por nivel
  que **desbloquea una habilidad para el resto del nivel** al agarrarlo.
- Efecto: mientras cae, si el jugador mantiene apretado Salto (Space),
  la velocidad máxima de caída baja de 600 a 80 px/s (behavior
  `PlatformerObjectBehavior`, propiedad `MaxFallingSpeed`) — planeo /
  caída lenta. No agrega tecla nueva ni animación nueva (reusa el
  frame de Fall).
- No es doble salto ni vuelo libre: sigue sin poder subir, solo cae
  más despacio. Mantiene la decisión original de no ampliar el scope
  de animación (ver §2), a costa de tocar una sola propiedad física.
- Sprite: pixel-art propio (Python + Pillow, `scripts/gen_mochila.py`),
  estética de mochila térmica de delivery en naranja vivo con parche
  blanco y una "R", correas negras. No es un asset CC0 ni generado por
  IA — mismo criterio que zombies y antídoto.
- Wiring: `scripts/wire_mochila.py` (Nivel 1, 1 instancia en x=950,y=96,
  junto al 3er antídoto sobre el pozo de agua).
- Puesta: Lio la lleva en la espalda (`MochilaWorn`, 7x10, hombros a
  cintura) y se da vuelta con él (`scripts/wire_mochila_back.py`, 14/10).
  El Tutorial la presenta como "¡UNA MOCHILA DE REPARTIDOR!".
- **Inventario (decidido 2026-10-14):** además del planeo, la mochila es
  donde Lio guarda las **pruebas del brote** (ver abajo). Desde que la
  agarra en el Nivel 1 la conserva el resto del juego (planeo + inventario
  también en L2 y L3). Las pruebas se releen desde la pausa con I
  ("MOCHILA"). Implementado en L1, L2 y L3 (global `TieneMochila`: se
  pone en 1 al agarrarla en L1 y "Jugar" la vuelve a 0; si muere en L1
  después de agarrarla, el nivel arranca con ella puesta). La mochila del
  Tutorial es de práctica y no cuenta. **A playtestear:** el planeo puede
  facilitar los huecos de L2 (camillas) que se diseñaron sin él.

### Notas del diario de Paciente Zero = pruebas del brote (2026-10-14)
- **7 pruebas:** 3 en el Nivel 1, 3 en el Nivel 2 y 1 que suelta Paciente
  Zero al ser derrotado (Nivel 3). En L1 van después de la mochila
  (x≈950), que es donde Lio las guarda.
- **Al recogerlas:** el mundo se congela (time scale 0) y se ve la nota
  completa en estilo papel hasta 6 s; se cierra antes soltando J,
  Espacio, Enter o ESC (después de 0.5 s);
  después, aviso "GUARDADA EN LA MOCHILA".
- **Inventario (pausa → I: MOCHILA, 2026-10-14):** título "MOCHILA -
  PRUEBAS n/7", la nota elegida grande (o "???" si falta) y una fila de 7
  casilleros con cursor ámbar; ← → elige, I / ESC / P vuelven a la pausa.
- Opcionales: no hacen falta para terminar el juego, pero completan el
  trasfondo del villano. Bonus: **+1000 con las 7** en la victoria final
  (L3), línea "PRUEBAS 7/7 +1000" en el desglose (decidido 2026-10-14).
- Es el vehículo narrativo principal: evita diálogos largos, coherente
  con el ritmo arcade y con el libro (pág. 92).
- **Formato** (pixel font del HUD): solo mayúsculas, acentos y Ñ, signos
  `! ( ) + , - . / : ? ¡ ¿` (sin comillas, `#`, `;` ni apóstrofe);
  máx. 30 caracteres por línea y 8 líneas por nota. Firma "P.Z." (el
  villano no tiene nombre propio). Arte: `scripts/gen_notas.py`, que
  también tiene los textos (fuente única).

| # | Título | Dónde | Qué explica |
|---|---|---|---|
| 1 | EL PLAN | L1, x≈1230 | Origen del brote: lo soltó en el festejo |
| 2 | REMITO | L1, x≈1010, junto a la mochila (la 1.ª que se encuentra) | De dónde sale la mochila |
| 3 | MENSAJEROS | L1, x≈2220, zona de virus | Contagio virus↔zombie |
| 4 | PERSONAL | L2, arriba del estante largo (x≈1060) | Los zombies del laboratorio |
| 5 | EL ANTÍDOTO | L2, ducto opcional (x≈3400), bajo el antídoto escondido | Por qué hay antídotos sueltos |
| 6 | ANOMALÍA | L2, piso justo después del gabinete (x≈3168) | Por qué Lio es inmune / la cura |
| 7 | ÚLTIMA PÁGINA | L3, la suelta el jefe al morir; la victoria aparece al cerrarla | Motivación: dominar el mundo |

```
PRUEBA 1/7 - EL PLAN
DÍA 1. EL VIRUS ESTÁ LISTO.
LO SOLTARÉ EN EL OBELISCO,
EN PLENO FESTEJO. MILES DE
HINCHAS ABRAZADOS: EL MEJOR
CONTAGIO ES LA ALEGRÍA.
NADIE VA A SOSPECHAR DE UN
CIENTÍFICO CON CAMISETA.
- P.Z.
```
```
PRUEBA 2/7 - REMITO
PEDIDO 0451 - LABORATORIO.
12 DOCENAS DE EMPANADAS.
DEJAR EN LA PUERTA. NO TOCAR
TIMBRE. NO MIRAR LOS FRASCOS.
NOTA DEL REPARTIDOR: HAY UN
OLOR RARO Y LOS VIRUS VUELAN.
NO VUELVO MÁS. ME QUEDO CON
LA PROPINA Y LA MOCHILA.
```
```
PRUEBA 3/7 - MENSAJEROS
DÍA 4. LOS VIRUS GRANDES
VUELAN SOLOS Y BUSCAN GENTE.
SI TOCAN A UN INFECTADO LO
PONEN MÁS FUERTE Y MÁS VERDE.
LOS LLAMO MIS MENSAJEROS.
NO TRAEN CARTAS, TRAEN
OBEDIENCIA.
- P.Z.
```
```
PRUEBA 4/7 - PERSONAL
REGISTRO DEL LABORATORIO.
EL PRIMERO FUE EL MÉDICO DE
GUARDIA. DESPUÉS LA ENFERMERA.
DESPUÉS EL INVESTIGADOR QUE
QUERÍA AVISAR A LA PRENSA.
YA NO ME DISCUTEN NADA.
POR FIN UN EQUIPO QUE ESCUCHA.
- P.Z.
```
```
PRUEBA 5/7 - EL ANTÍDOTO
DÍA 9. ALGUIEN DEL EQUIPO
FABRICÓ UN ANTÍDOTO ANTES DE
CAER. ROMPÍ LA FÓRMULA, PERO
QUEDARON FRASCOS SUELTOS POR
TODA LA CIUDAD.
SI ALGUIEN LOS JUNTA...
NO. NADIE ES TAN TONTO COMO
PARA SALIR A LA CALLE.
```
```
PRUEBA 6/7 - ANOMALÍA
DÍA 12. LAS CÁMARAS MUESTRAN
A ALGUIEN QUE NO SE CONTAGIA.
SALTA SOBRE MIS INFECTADOS
COMO SI FUERA UN JUEGO.
LLEVA UNA MOCHILA DE DELIVERY.
SI ES INMUNE, SU SANGRE ES LA
CURA. QUE NO LLEGUE HASTA ACÁ.
- P.Z.
```
```
PRUEBA 7/7 - ÚLTIMA PÁGINA
NO QUERÍA DESTRUIR EL MUNDO.
QUERÍA QUE ME HICIERA CASO.
UN EJÉRCITO QUE NO PROTESTA,
NO VOTA, NO PIDE AUMENTO.
EMPECÉ POR BUENOS AIRES
PORQUE SI FUNCIONA ACÁ,
FUNCIONA EN CUALQUIER LADO.
¿QUIÉN SOS VOS PARA FRENARME?
```

## 7. Sonido (punto 7 de la consigna — mínimo música de fondo + colisiones)

- Música de fondo: 1 loop general (o 1 por nivel si da el tiempo).
- SFX obligatorios por la consigna (colisiones): stomp/kill de
  zombie, daño al jugador.
- SFX adicionales recomendados: salto, pickup de antídoto, golpe/hit
  del jefe, victoria.
- **Fuente: 100% procedural** (Python + numpy, `scripts/gen_sfx.py`,
  WAV sintetizado estilo chiptune) — mismo criterio que el arte
  (Pillow) y los sprites: nada de librerías CC0 de terceros ni de
  IA-audio. Decisión cerrada 2026-09-17/18: la música ya no es
  placeholder a reemplazar, es el audio definitivo.

## 8. Pendiente de definir

- Texto de cinemáticas, si las hay. Las notas del diario ya están
  escritas (7, ver §6, 2026-10-14).

### Ya confirmados (2026-09-02)
- Título: **Paciente Zero**. Nombre del jugable: **Lio** (renombrado
  2026-09-13, antes d10ego). Balance de antídotos: 4 por nivel, los
  4 = 1 vida extra (ver §6).
- Mecánica del hueco forzado (Nivel 1, Tier 2): si el jugador no está
  parado sobre la horda al cruzar y cae al río, **pierde 1 vida y
  reaparece en un checkpoint justo antes del hueco** (no es muerte
  instantánea ni un simple empujón). Implica agregar un spawn point /
  variable de checkpoint antes del tramo x[1730..1970] — pendiente de
  implementación, ver `reseach.md`.
