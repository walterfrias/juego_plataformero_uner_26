// cover_pintada_captura.js — captura del Nivel 1 en la pintada "#YO APOYO LA LEY DE
// FINANCIAMIENTO UNIVERSITARIO" (Grafiti_Universidad, x 2370..2537, y 128..171) para
// los covers de gen_cover_pintada.py (28/10). Se captura el juego de verdad para que
// salga con su iluminación (noche, fuego, luna, niebla) y todo lo que hay alrededor.
//
// Sin HUD ni el cartel "Made with GDevelop"; Lio en el aire a la izquierda de la
// pintada, mirando a la derecha; el juego congelado (time scale 0) al capturar.
//
// Uso (con el juego exportado y servido, p. ej. scripts/jugar_web.sh -p 8791):
//   node scripts/cover_pintada_captura.js http://localhost:8791 promo/captura_pintada_960x540.png
// Escribe además <salida>.json con el borde izquierdo y de arriba de la cámara (en px
// del mundo), para que gen_cover_pintada.py recorte con la pintada centrada.
const path = require('path');
const fs = require('fs');
const puppeteer = require(path.join(process.env.HOME, 'Escritorio/gdevelop-mcp/node_modules/puppeteer'));

const [url, salida] = process.argv.slice(2);
const LIO = {x: 2318, y: 20};              // cae ~0.25 s antes de congelar: en el aire, delante del árbol (más a la derecha pisa a un zombie)

(async () => {
  const b = await puppeteer.launch({headless: 'new'});
  const pg = await b.newPage();
  await pg.setViewport({width: 960, height: 540});
  await pg.goto(`${url}/index.html?escena=Level1`);
  await pg.waitForFunction(() => window.__game && __game.getSceneStack().getCurrentScene()
      && __game.getSceneStack().getCurrentScene().getName() === 'Level1', {timeout: 60000});
  await new Promise(r => setTimeout(r, 2500));              // que pase el fundido de entrada
  await pg.evaluate(lio => {
    const s = __game.getSceneStack().getCurrentScene();
    const w = document.getElementById('watermark-link');
    if (w) (w.parentElement || w).remove();
    s.getLayer('UI').show(false);
    const p = s.getObjects('Player')[0];
    p.setPosition(lio.x, lio.y);
    p.flipX(false);
    p.getBehavior('PlatformerObject').setCurrentFallSpeed(0);
  }, LIO);
  await new Promise(r => setTimeout(r, 250));
  const cam = await pg.evaluate(() => {
    const s = __game.getSceneStack().getCurrentScene();
    s.getTimeManager().setTimeScale(0);
    const l = s.getLayer('');
    return {left: l.getCameraX() - l.getCameraWidth() / 2, top: l.getCameraY() - l.getCameraHeight() / 2};
  });
  await new Promise(r => setTimeout(r, 400));
  const canvas = await pg.$('canvas');
  await canvas.screenshot({path: salida});
  fs.writeFileSync(`${salida}.json`, JSON.stringify(cam));
  console.log('ok', salida, cam);
  await b.close();
})();
