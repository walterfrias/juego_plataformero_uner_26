# Apéndice — Game Testing / QA

> Responde al foco que la cátedra pidió desde la Pre-Alfa (29/09):
> **validación de mecánicas**, **detección temprana de errores** y
> **playtesting** con usuarios reales. Va como apéndice del DDJ (Thompson,
> pág. 107: "Apéndices").

## Método

El juego se probó de cuatro maneras, que se complementan:

| Método | Qué detecta | Cómo se hizo |
|---|---|---|
| **Playtest a mano** (desarrollador) | Sensación, ritmo, lo que "no se entiende" | Jugar cada cambio en el navegador, y periódicamente el juego de punta a punta. |
| **Playtest con otras personas** | Frustración, dificultad, lectura de la interfaz | Los docentes jugaron y aprobaron el Nivel 1. Una jugadora de 10 años probó el juego. |
| **Pruebas automáticas en el juego real** | Errores de lógica, valores mal calculados, regresiones | El juego exportado a HTML5 se maneja con un navegador automático (Puppeteer): se simulan las teclas y se leen las posiciones y variables reales. Para el timing fino se usó un **robot dentro del juego**, que reacciona en el mismo cuadro, porque desde afuera llegaba tarde. |
| **Revisión del código compilado** | Fallas silenciosas del motor | Después de cada cambio se busca en el JavaScript que genera GDevelop si alguna instrucción quedó descartada ("Unknown instruction"). El validador del proyecto no las detecta. |

Una regla que salió de la experiencia: **mover a Lio con teclas de verdad, no
teletransportarlo**. Así apareció una nota que estaba en un lugar al que no
se podía llegar jugando (ver abajo).

## 1. Validación de mecánicas

| Mecánica | Prueba | Resultado |
|---|---|---|
| Salto | Medido en el juego: alto y largo, parado y con carrera | ~37 px de alto; **~28 px de largo parado**, 40–45 con carrera. Todos los huecos se diseñaron con estos números: ≤ 28 px sin ayuda; más anchos llevan puente, cables o pistones. |
| Pisotón y contagio | Pisar zombies sanos e infectados; 3 virus seguidos al mismo zombie | Sano: muere. Infectado: necesita 2 pisotones. Límite de contagios por zombie: 1 en L1, 2 en L2, sin límite en L3 (verificado en los 3). |
| Horda (L1) | Montarla, chocarla de costado, caer al río | Se cruza encima; el choque saca 1 vida; caer vuelve al checkpoint. La horda pasa en bucle: nunca queda el jugador sin forma de cruzar. |
| Piso encerado (L2) | Distancia de frenado | 71 px de deslizamiento contra 3 px en el piso normal. |
| Pistones (L2) | Robot "jugador prudente": se frena en el borde, salta parado y nunca salta a un pistón en rojo | **10/10 cruces** de los dos pozos sin perder vidas. Quedarse quieto sobre un pistón: cae a los ~2,4 s. |
| Policía que dispara (L3) | Robot con la mochila esquivando los tiros | **7/7** esquivados con un salto planeado. |
| Toldo, charco y vapor (L3) | Teclas reales | El toldo sube a Lio ~84 px; el charco saca 1 vida y lo devuelve al checkpoint; el vapor lo deja en la marquesina. |
| Jefe (L3) | Robot que lo pisa desde el busto en las 3 fases | Se clava en x 89 / 343, el pisotón entra en las 3 fases, la doble embestida termina del lado de Lio, suelta la nota 7. |
| Pausa, notas y reloj | Abrir y cerrar en los 3 niveles; medir el reloj | Congelan el juego y el reloj; al cerrar una nota Lio no salta. |
| Puntaje y TOP 5 | 7 partidas seguidas, recargar la página, Game Over → ESC | La tabla se ordena bien, persiste y anota el puntaje que mostraba el HUD. |
| Flujo de escenas | Menú → Tutorial → L1 → L2 → L3 → menú, con victoria, Game Over y reintento | Completo, sin pantallas sin salida. |

## 2. Errores encontrados y corregidos

### Diseño de niveles

| Problema | Cómo se detectó | Arreglo |
|---|---|---|
| Hueco imposible en el Nivel 2 | Cálculo con el salto medido | Rediseñado según el alcance real del salto. |
| Estantes de L2 inalcanzables | Prueba automática | Reubicados al alcance del salto. |
| La nota 6 (arriba del gabinete) no se podía agarrar jugando | Moviendo a Lio con teclas, no teletransportándolo | La nota pasó al piso, después del gabinete. |
| Una plataforma invisible "flotaba" en el aire en L1 (el piso de la horda, activo cuando la horda no estaba) | Playtest: "plataforma invisible pasando a la anciana" | Solo es plataforma mientras la horda corre. |
| La salida del ducto de L2 quedaba a 18 px de un pozo: con la flecha apretada, Lio caía | Prueba con teclas | Salida movida: 82 px de piso antes del pozo. |
| El tubo roto del ducto estallaba con Lio llegando y el virus le salía encima: golpe seguro | Prueba con teclas | Ahora estalla cuando Lio pasa por encima: el virus sale detrás y se lo puede dejar atrás corriendo. |
| El jefe expuesto contra el borde quedaba debajo de las estatuas y costaba pisarlo (2 de 3 pisotones no llegaban) | Simulación | Pelea nueva: se clava en un lugar visible, y los bustos se corrieron 22 px. |
| Con el contagio sin límite, al rato todos los zombies estaban infectados | Playtest | Cura a los 6 s, inmunidad de 3 s y límite de contagios por nivel. |

### Fallas técnicas (la mayoría "en silencio": el juego no da error, simplemente no hace lo que debería)

| Síntoma | Causa | Arreglo |
|---|---|---|
| La pausa no abría | Dos eventos que se deshacían en el mismo cuadro: uno abría, el otro cerraba | Un evento con un estado intermedio. |
| La cura del contagio nunca corría | Un evento "para cada objeto" que el motor compilaba vacío | Corregida la clave que lee el motor. |
| "4 zombies rotos" al final de L1 | Una condición sobre un objeto filtra sus instancias, y las acciones solo afectaban a las filtradas | Separar la acción en un evento sin esa condición. |
| El río de L1 nunca se movió; la niebla quedaba opaca | Acciones de un tipo de objeto sin el prefijo de su extensión: se descartaban al compilar | Prefijo correcto, verificado en el código compilado. |
| Cambiar de escena, efectos y timers fallaban sin aviso | Parámetros de texto sin comillas (o con comillas de más) | Verificación sistemática del código compilado. |
| Con WASD no se podía trepar ningún poste | El motor decide "agarrarse" con otra tecla (Ladder), no con "arriba" | La W simula también esa tecla. |
| Al cerrar una nota con J, Lio saltaba solo | La tecla quedaba registrada al volver al juego | Las notas se cierran al **soltar** la tecla, con los controles bloqueados mientras están abiertas. |
| En el Tutorial, Lio quedaba cayendo lento para siempre | El planeo no se apagaba en un caso | Corregido el estado del planeo. |
| Al re-ejecutar algunos scripts, el puntaje de L3 se perdía | El script era de cuando L3 era solo la arena | Cableado para los 3 niveles. |

Un error de proceso también dejó regla: el **editor de GDevelop tiene que
estar cerrado** antes de modificar el proyecto por script. Una vez se perdió
trabajo porque el editor, al guardar, pisó los cambios. Desde entonces los
scripts verifican que esté cerrado y se cortan si lo encuentran abierto.

## 3. Playtesting: lo que cambió por el feedback

| Quién | Qué dijo / qué se vio | Qué se cambió |
|---|---|---|
| Docentes | Probaron el Nivel 1 | **Aprobado**; se tomó como base de calidad para L2 y L3. |
| Jugadora de 10 años | Con los virus volando al azar, "tenés que esperar a que se vaya para pasar": **frustrante** (en la simulación, esperas de hasta 4–5 s) | Los virus pasan a **recorridos fijos** (ascensor, péndulo, ocho, círculo): espera máxima ~1 s, se aprende el ritmo. Los minivirus siguen persiguiendo, para que haya contraste. |
| Desarrollador | Las plataformas no se distinguían del fondo: "no se nota qué se pisa" | **Bordes que se iluminan** al acercarse Lio, y luz de borde en árboles y faroles. |
| Desarrollador | Las camillas móviles del L2 "flotaban" y "no son de las partes más entretenidas" | Reemplazadas por **pistones hidráulicos** con aviso de luces (piden timing, no solo esperar). |
| Desarrollador | Pelea con el jefe de punta a punta: "no es entretenida y no se entiende" | **Pelea nueva**: se clava la jeringa, fases por vida, cartel "¡PISALO!". |
| Desarrollador | L1 con minivirus: muy entretenido con varios a la vez, pero el final se hacía difícil | Vida del minivirus en L1 bajada de 8 a 5 s. |
| Desarrollador | El disparo del policía desde la cintura "no se veía natural"; las ráfagas dejaban una ventana de salto demasiado chica | Un solo tiro desde la mano, a la altura del pecho, con aviso de 0,5 s. |
| Desarrollador | Los pozos en la calle del Nivel 3 "no tenían sentido en una calle del centro" | Peligros de calle: toldo, charco electrificado, vapor del subte. |

## 4. Playtest final y datos que faltan

**[falta dato]** El playtest de punta a punta para medir la duración
(punto 4 de la consigna). El juego ya lo facilita:
- el **reloj** de cada nivel queda en el desglose de la victoria;
- el **TOP 5** registra el puntaje de cada partida.

**Planilla propuesta** (una por persona):

| Dato | L1 | L2 | L3 |
|---|---|---|---|
| Tiempo del reloj al ganar | | | |
| Game Over (cantidad) | | | |
| Antídotos (n/4) | | | — |
| Pruebas encontradas | /3 | /3 | /1 |
| ¿Dónde se trabó o se frustró? | | | |

Preguntas al terminar:
1. ¿Entendiste cuándo podías pisar al jefe?
2. ¿Se entendía el rojo de los pistones?
3. ¿Leíste las notas? ¿Te dieron ganas de buscar las que faltaban?
4. ¿Qué fue lo más divertido y lo más molesto?
