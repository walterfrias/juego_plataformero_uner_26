#!/usr/bin/env python3
"""
capturas_gdd.py — capturas del juego corriendo para el GDD final
(gdd_final/capturas/*.png, 960x540: la pantalla de 480x270 al doble).

Exporta game/game.json con gdexport a un directorio temporal, le inyecta
window.__game (como scripts/jugar_web.sh), lo sirve en un puerto libre y
con Puppeteer pone cada escena en el estado que se quiere mostrar: el menú
con una tabla TOP 5 de ejemplo, Lio en distintos tramos de cada nivel, la
pausa, la mochila, una nota recién agarrada, la victoria con el desglose y
la pelea con el jefe. No modifica game.json. En la copia temporal se apaga
la marca "Made with GDevelop" (si no, tapa una esquina de cada captura).

Uso:  python3 scripts/capturas_gdd.py      (GDevelop cerrado no hace falta:
      solo lee el proyecto; exporta lo que está GUARDADO)
"""
import json
import os
import shutil
import socket
import subprocess
import tempfile

GDEXPORT = os.path.expanduser("~/Escritorio/gdevelop-mcp/node_modules/.bin/gdexport")
PUPPETEER = os.path.expanduser("~/Escritorio/gdevelop-mcp/node_modules/puppeteer")
OUT = os.path.abspath("gdd_final/capturas")

JS = r"""
const puppeteer = require(%(pup)s);
const OUT = %(out)s, URL = %(url)s;
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await puppeteer.launch({headless: 'new', args: ['--autoplay-policy=no-user-gesture-required']});
  const p = await b.newPage(); await p.setViewport({width: 960, height: 540});
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(URL); await sleep(4000);
  const ev = (f, ...a) => p.evaluate(f, ...a);
  const escena = async n => {
    await ev(n => __game.getSceneStack().replace({sceneName: n, clear: true}), n);
    for (let i = 0; i < 60 && (await ev(() => __game.getSceneStack().getCurrentScene().getName())) !== n; i++) await sleep(300);
    await sleep(600);
  };
  const glob = vals => ev(v => { for (const k in v) { const x = __game.getVariables().get(k);
    typeof v[k] === 'string' ? x.setString(v[k]) : x.setNumber(v[k]); } }, vals);
  const vars = vals => ev(v => { const s = __game.getSceneStack().getCurrentScene();
    for (const k in v) s.getVariables().get(k).setNumber(v[k]); }, vals);
  const lio = (x, y) => ev((x, y) => { const s = __game.getSceneStack().getCurrentScene();
    const pl = s.getObjects('Player')[0]; pl.setPosition(x, y);
    pl.getBehavior('PlatformerObject').setCurrentFallSpeed(0); }, x, y);
  const tecla = async k => { await p.keyboard.down(k); await sleep(80); await p.keyboard.up(k); await sleep(250); };
  const foto = async n => { await p.screenshot({path: OUT + '/' + n + '.png'}); console.log('  ' + n); };

  // --- menú con una tabla TOP 5 de ejemplo y la pantalla de iniciales
  await glob({TopLoaded: 1, TopP1: 52300, TopN1: 'LIO', TopP2: 47150, TopN2: 'WAL', TopP3: 39800,
              TopN3: 'MEL', TopP4: 28400, TopN4: 'ANA', TopP5: 15200, TopN5: 'PZ0', TopIni: 'WAL', Record: 52300});
  await escena('MainMenu'); await sleep(1500); await foto('menu');
  await glob({PartidaViva: 1, PuntajeCorte: 44120});
  await escena('MainMenu'); await sleep(900); await foto('iniciales');
  await glob({TopP4: 28400, TopN4: 'ANA', TopP5: 15200, TopN5: 'PZ0', TopP3: 39800, TopN3: 'MEL'});

  // --- Nivel 1
  await glob({Puntaje: 0, TieneMochila: 0, Nota1: 1, Nota2: 1, Nota3: 1, Nota4: 1});
  await escena('Level1');
  await vars({LevelScore: 1350, Lives: 3, Antidotes: 2});
  await lio(150, 84); await sleep(1800); await foto('l1_inicio');
  await lio(700, 84); await sleep(1800); await foto('l1_hud');
  await lio(1320, 84); await sleep(300); await lio(1560, 84); await sleep(5500); await foto('l1_rio');
  // la horda: esperar a que llegue al río y subir a Lio encima
  for (let i = 0; i < 120; i++) {
    const hx = await ev(() => __game.getSceneStack().getCurrentScene().getObjects('HordaPiso')[0].getX());
    if (hx > 1700 && hx < 1760) break;
    await vars({Lives: 3}); await sleep(250);
  }
  await ev(() => { const s = __game.getSceneStack().getCurrentScene(), h = s.getObjects('HordaPiso')[0];
    const pl = s.getObjects('Player')[0]; pl.setPosition(h.getX() + h.getWidth() / 2, h.getY() - 40); });
  await sleep(700); await foto('l1_horda');
  await tecla('Escape'); await sleep(500); await foto('pausa');
  await tecla('i'); await sleep(500); await foto('mochila');
  await tecla('Escape'); await sleep(300); await tecla('Escape'); await sleep(400);
  await escena('Level1'); await glob({Nota2: 0});
  await escena('Level1');
  await lio(1004, 80); await sleep(900); await foto('nota');
  await escena('Level1');
  await vars({LevelScore: 4650, Lives: 3, Antidotes: 4, AntidoteBonus: 1, LevelTime: 212});
  await lio(2566, 60); await sleep(2500); await foto('victoria');

  // --- Nivel 2 (con la mochila)
  await glob({TieneMochila: 1});
  await escena('Level2');
  await vars({Lives: 4, LevelScore: 2200});
  await lio(1500, 76); await sleep(1800); await foto('l2_lab');
  await lio(1110, 158); await sleep(1500); await foto('l2_subsuelo');
  await lio(2440, 76); await sleep(1600); await foto('l2_pistones');
  await lio(3000, 76); await sleep(1500); await foto('l2_alarma');

  // --- Nivel 3
  await escena('Level3');
  await vars({Lives: 9});
  await lio(-1580, 116); await sleep(1800); await foto('l3_calle');
  await lio(-880, 116); await sleep(1500); await foto('l3_corrientes');
  await lio(-300, 116); await sleep(1500); await foto('l3_llegada');
  // el jefe: apunta (estado 1, contorno verde) y después se clava (estado 3)
  const estadoJefe = async n => { for (let i = 0; i < 100; i++) {
    if (await ev(() => __game.getSceneStack().getCurrentScene().getVariables().get('BossState').getAsNumber()) === n) return;
    await vars({Lives: 9}); await sleep(100); } };
  await lio(40, 116); await estadoJefe(1); await sleep(400); await foto('jefe');
  await estadoJefe(3); await sleep(500); await foto('jefe_clavado');
  console.log('errores JS:', errs.length ? errs : 'ninguno');
  await b.close();
})();
"""


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    tmp = tempfile.mkdtemp(prefix="pz-capturas-")
    try:
        subprocess.run([GDEXPORT, "-p", os.path.abspath("game/game.json"), "-o", tmp], check=True,
                       stdout=subprocess.DEVNULL)
        idx = os.path.join(tmp, "index.html")
        subprocess.run(["sed", "-i", r"/new gdjs.RuntimeGame(/a\        window.__game = game;", idx], check=True)
        data = os.path.join(tmp, "data.js")
        d = open(data, encoding="utf-8").read().replace('"showWatermark":true', '"showWatermark":false')
        open(data, "w", encoding="utf-8").write(d)
        os.makedirs(OUT, exist_ok=True)
        port = puerto_libre()
        srv = subprocess.Popen(["python3", "-m", "http.server", str(port)], cwd=tmp,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            js = JS % {"pup": json.dumps(PUPPETEER), "out": json.dumps(OUT),
                       "url": json.dumps(f"http://127.0.0.1:{port}/index.html")}
            subprocess.run(["node", "-e", js], check=True)
        finally:
            srv.terminate()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
