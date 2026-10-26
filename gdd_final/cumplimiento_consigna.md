# Cumplimiento de la consigna y cambios desde el avance

> Los diez puntos de la consigna oficial de la cátedra y dónde se
> cumple cada uno en el juego y en este documento.

## Cumplimiento de la consigna

| # | La consigna pide | Cómo lo cumple Paciente Zero | Dónde verlo | Estado |
|---|---|---|---|---|
| 1 | Género **plataformas 2D** | Plataformero 2D de acción arcade: correr, saltar, trepar y planear (comportamiento *Platformer Character* de GDevelop). Se combate solo cayéndoles encima a los zombies. | Mecánica de juego; Walkthrough | ✅ |
| 2 | Modalidad, **preferentemente grupal** | **Trabajo individual.** La consigna lo plantea como preferencia, no como requisito. Se eligió por experiencias anteriores con grupos donde no todos participaban parejo. | Portada | ✅ (individual) |
| 3 | Al menos **3 niveles + un tutorial** de práctica | Tutorial (el refugio, sin forma real de perder) + **Nivel 1** La costanera + **Nivel 2** El laboratorio + **Nivel 3** Del laboratorio al Obelisco, con el jefe final. | Walkthrough y mapas | ✅ |
| 4 | Duración total de **30 minutos** | Contenido: 3 niveles largos (2600, 3800 y 2620 px), 4 antídotos y 3 notas por nivel en rutas opcionales y una pelea final en 3 fases. Un reloj en pantalla mide el tiempo de cada nivel. **La primera partida completa lleva entre 15 y 30 minutos, según la habilidad del jugador.** | Resumen del Walkthrough; Game Testing | ✅ (15–30 min) |
| 5 | **Manual de uso** (opcional) | No hay un manual aparte: los controles se enseñan jugando en el Tutorial, cartel por cartel, y la pausa tiene la ayuda con todas las teclas. El apartado Controles de este GDD los reúne. | Controles; Tutorial | ✅ (opcional) |
| 6 | **Menú de opciones** | **Menú principal:** Jugar / Opciones / Salir y la tabla TOP 5. **Opciones:** volumen de música (← →) y de efectos (↑ ↓). **Pausa** (ESC o P), en los 3 niveles: los mismos dos volúmenes, R reiniciar, M volver al menú, I abrir la mochila con las pruebas, ESC/P reanudar. | Sistemas de menú | ✅ |
| 7 | **Sonidos:** de fondo y de colisiones, como mínimo | **De fondo:** música del menú y loop de los niveles, más ambiente: zumbido de los tubos del lab, crepitar del fuego. **De colisión:** pisotón (sube de tono con la cadena), daño, agarrar antídoto o nota. **Además:** salto, victoria, game over, chispazo, gatillo y disparo del policía. Todo generado por código, sin bancos de sonidos ni IA. | Diseño de sonido | ✅ |
| 8 | Motor **web** (GDevelop o Construct3) | **GDevelop**, nombrado en la consigna. Exportado a HTML5: se juega en el navegador y está publicado en itch.io. | Diseño de programación; Plataforma | ✅ |
| 9a | GDD: **tema o temática con narrativa propia** | Buenos Aires tomada por un virus zombie; Lio, el único inmune, va del río al Obelisco a enfrentar al científico que lo soltó en pleno festejo. La historia se cuenta sin diálogos, con **7 notas del diario del villano** repartidas por los niveles. | Sinopsis de la historia; Guión (las 7 notas) | ✅ |
| 9b | GDD: **ficha del personaje** | Ficha de Lio en el capítulo Personajes, actualizada desde la primera entrega: rol, arquetipo, habilidad, sprite, paleta y animaciones, más el antídoto y la mochila con sus paletas. | Personajes | ✅ |
| 10 | **Video pitch** de hasta 5 minutos | Pendiente; se graba sobre el build final. | — | ⏳ pendiente |

### Instancias de seguimiento

| Fecha | Entrega |
|---|---|
| Sep. 2026 | Ficha de personaje (primera entrega) |
| 18/09/2026 | Avance del GDD + High Concept, para devolución |
| 29/09/2026 | Pre-entrega Pre-Alfa: prototipo con core loop, física y niveles; foco en Game Testing |
| 03/11/2026 | Entrega final: juego, GDD final y video pitch |

## Cambios desde el avance (18/09)

El avance era una versión de trabajo, con el Nivel 1 jugable y el resto en
diseño. Lo que cambió desde entonces:

**Contenido nuevo**
- **Nivel 2 — El laboratorio:** pozos con vidrios, piso encerado, pistones
  hidráulicos, tubos de contención que estallan, ductos de aire y un corredor
  opcional por el subsuelo.
- **Nivel 3 — Del laboratorio al Obelisco:** recorrido por el centro entre
  edificios, con peligros de calle (toldo que rebota, charco electrificado,
  vapor del subte) en lugar de pozos, y vuelven todos los zombies del juego.
- **Tutorial** implementado (en el avance figuraba "en desarrollo").
- **Paciente Zero definitivo:** el científico con la camiseta de Argentina.
  Reemplaza la "versión mutada del zombie" del avance. Pelea propia en 3
  fases: se clava la jeringa en las pirámides y ahí se lo pisa.
- **Las 7 pruebas del brote** con texto definitivo (en el avance: "~2–3 por
  nivel, placeholder"). Se leen al agarrarlas y se releen en la mochila.
- **Enemigos:** de 8 a 13 tipos de zombie (el personal del laboratorio,
  hincha, repartidor y el policía que dispara), el contagio virus↔zombie
  con su minivirus, y la multitud de fondo de L3.

**Sistemas nuevos**
- Puntaje con cadena de pisotones, desglose en la victoria, **reloj con bonus
  por rapidez** y **TOP 5 con iniciales** de 3 letras.
- La mochila acompaña a Lio en todo el juego: planeo e inventario de las
  pruebas.
- HUD unificado en fuente pixel propia.

**Correcciones de lo que decía el avance**
- La persecución sobre la horda es del **Nivel 1**, no "de cada nivel".
- Los virus voladores ya no vuelan al azar: siguen **recorridos fijos**
  (ascensor, péndulo, ocho, círculo). Esperar un vuelo al azar resultó
  frustrante en el playtest.
- El Nivel 2 no tiene "pinchos": los peligros son pozos con vidrios rotos y
  las mecánicas del laboratorio.
- La duración ya no es una estimación: se mide con el reloj del juego.

**Lo que había quedado pendiente en el avance, y quedó resuelto:**
- arte del jefe;
- texto final de las notas;
- número de notas por nivel (3 / 3 / 1);
- ajuste del cruce sobre la horda (la horda pasa en bucle y hay checkpoint
  antes del río).
