# Controles, información en pantalla y sistemas de menú

> Apartados "Controles", "Información dentro del juego" y "Sistemas de
> menú" de la plantilla del DDJ (Thompson, pág. 107). Hacen también de
> manual de uso (punto 5 de la consigna, opcional).

## Controles

El juego se juega solo con teclado; el mouse sirve solo en las pantallas de
fin de nivel. Cada acción tiene dos teclas: las **flechas** o **WASD**, y
**Espacio** o **J** para saltar. Con WASD + J, una mano mueve y la otra salta.

### Jugando

| Acción | Teclas | Detalle |
|---|---|---|
| Caminar | ← → / A D | Velocidad máxima 95 px/s. En el piso encerado del Nivel 2 cuesta frenar. |
| Saltar | Espacio / J | ~37 px de alto. Parado salta ~28 px de largo; con carrera, 40–45. |
| Planear | **Mantener** Espacio / J mientras cae | Solo con la mochila puesta: la caída máxima baja de 600 a 80 px/s. No sube, solo cae más despacio. |
| Trepar | ↑ ↓ / W S | En postes de luz y escaleras. |
| Pisotón | Caerle encima a un zombie | Única forma de eliminarlo. Rebota a Lio hacia arriba; encadenar pisotones sin tocar el piso suma más puntos. |
| Pausa | ESC / P | Congela el juego y el reloj. |

### En la pausa

| Acción | Teclas |
|---|---|
| Volumen de música | ← → |
| Volumen de efectos | ↑ ↓ |
| Reiniciar el nivel | R |
| Volver al menú principal | M |
| Abrir la mochila (pruebas del brote) | I |
| Reanudar | ESC / P |

**Dentro de la mochila:** ← → elige la nota; I, ESC o P vuelven a la pausa.

### Notas, fin de nivel y menús

| Pantalla | Teclas |
|---|---|
| Nota recién agarrada | Se cierra **al soltar** J, Espacio, Enter o ESC (después de medio segundo), o sola a los 6 s. Se cierra al soltar para que Lio no salte al volver al juego. |
| Victoria | Espacio o click: siguiente nivel (en el Nivel 3, al menú) · R: repetir el nivel · ESC: menú |
| Game Over | R o click: reintentar el nivel · ESC: menú |
| Menú principal | ↑ ↓ / W S: elegir · Enter, Espacio o J: aceptar · O: opciones · ESC: salir |
| Opciones | ← →: música · ↑ ↓: efectos · ESC: volver |
| Iniciales del TOP 5 | ↑ ↓ / W S: cambiar letra · → / D / Enter / J / Espacio: siguiente · ← / A / Backspace: anterior |

## Información en pantalla (HUD)

Todo en una fuente pixel propia, en la capa de interfaz (no se mueve con la
cámara).

| Dónde | Qué muestra |
|---|---|
| Arriba a la izquierda | **Corazones**: las vidas (empieza con 3; hasta 4 con la vida extra de los antídotos). |
| Al lado de los corazones (L1, L2 y L3) | **Frasco + "n/4"**: antídotos del nivel; el número se pone verde con 4/4. |
| Arriba a la derecha | **PUNTOS 000000** en ámbar: el total de la partida más lo ganado en el nivel. |
| Debajo de los puntos | **TIEMPO m:ss**: el reloj del nivel; se pone **rojo** al pasar el tiempo par (ya no da bonus). |
| Arriba al centro (L3) | **PACIENTE ZERO n/3**: la vida del jefe, en rojo, cuando empieza la pelea. |
| Sobre el zombie o el frasco | **Números arcade** ("+100", "+200"…) que saltan, titilan y desaparecen. |
| En la arena (L3) | Cartel **"¡PISALO!"** titilando mientras el jefe está clavado (primera fase). |
| Sobre Lio | La **mochila en la espalda**, que se da vuelta con él. |

<!-- capturas:hud -->

Algunas señales van en el propio mundo, no en el HUD:
- **Contorno rojo y gas:** zombie contagiado (hay que pisarlo dos veces).
- **Contorno que parpadea:** está por escupir un virus.
- **Contorno rojo y chispazo en el jefe:** está por embestir.
- **Luces verdes / rojas:** pistones (firme / está por bajar).
- **Bordes de plataforma** que se iluminan cuando Lio se acerca.

## Sistemas de menú

```
MENÚ PRINCIPAL ──Jugar──► TUTORIAL ──► NIVEL 1 ──► NIVEL 2 ──► NIVEL 3 ──► MENÚ
   │  └─Opciones (volúmenes)              │ ▲          (victoria de cada nivel)
   │                                      ▼ │
   │                           PAUSA ─ I ─► MOCHILA (pruebas)
   └─ al volver con un puntaje del TOP 5: INGRESÁ TUS INICIALES
```

<!-- capturas:menus -->


- **Menú principal.** Fondo animado (ciudad en movimiento, zombies que
  caminan, Lio, el Obelisco y la Luna). Panel con **Jugar / Opciones /
  Salir** y, arriba a la izquierda, la tabla **TOP 5**. "Jugar" empieza una
  partida nueva: puntaje en 0, notas y mochila reseteadas.
- **Opciones.** Volumen de música y de efectos, en barras de 0 a 10. Se
  guardan para toda la sesión y valen también en la pausa.
- **Pausa** (en los tres niveles). Panel con los volúmenes y la ayuda de
  teclas. Desde ahí se reinicia, se vuelve al menú o se abre la mochila.
- **Mochila (inventario).** Título "MOCHILA - PRUEBAS n/7", la nota elegida
  en grande ("???" si todavía no se encontró) y una fila de 7 casilleros
  con cursor.
- **Nota recién agarrada.** El mundo se congela y aparece la nota en papel.
  Al cerrarla: "GUARDADA EN LA MOCHILA".
- **Victoria.** Cartel propio de cada nivel:
  - L1: "¡LLEGASTE AL LABORATORIO!";
  - L2: "¡LLEGASTE AL CORAZÓN DEL LAB!";
  - L3: "¡DERROTASTE AL PACIENTE ZERO! BUENOS AIRES ESTÁ A SALVO".

  Debajo va el **desglose del puntaje**: nivel, meta +1000, vidas ×500,
  tiempo con su bonus, antídotos 4/4 +1000, pruebas 7/7 +1000 (solo en L3)
  y el total, con "¡NUEVO RÉCORD!" si corresponde.
- **Game Over.** Al quedarse sin vidas. Reintentar repite el nivel con el
  puntaje que se traía. Lo ganado en ese nivel se descarta, para que no se
  pueda acumular repitiendo.
- **TOP 5 con iniciales.** La partida termina al volver al menú (ganando el
  Nivel 3, desde el Game Over o desde la pausa). Si el puntaje entra en la
  tabla, el panel del menú pide **3 letras**, como en los arcades: la fila
  nueva se completa mientras se escribe y titila al guardarse. Arranca con
  las últimas iniciales usadas. La tabla queda guardada en el navegador.
