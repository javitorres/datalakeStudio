// Renders the captions and the title/end cards as 1920x1080 PNGs: node promo/cards.mjs <cards.json> <out dir>
// cards.json is written by build.py: [{name, kind: 'caption' | 'title' | 'end', kicker, title, sub}].
// Captions come out on a transparent background, to be overlaid on the clips.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Browser, sleep } from './cdp.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const LOGO = pathToFileURL(path.join(HERE, '..', 'client', 'src', 'assets', 'logo.svg')).href;
const [specFile, outDir] = process.argv.slice(2);
const cards = JSON.parse(fs.readFileSync(specFile, 'utf8'));

const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]);

// App palette: teal #0d846f, ink #17211f, canvas #f3f7f5, mint #e4f4ef. The app renders in Noto Sans.
const CSS = `
  html, body { margin: 0; width: 1920px; height: 1080px; background: transparent; font-family: 'Noto Sans', sans-serif; }
  #__promo_cursor { display: none !important; }
  .caption { position: absolute; left: 160px; bottom: 72px; display: flex; max-width: 1180px;
    background: rgba(255,255,255,.97); border-radius: 18px; overflow: hidden;
    box-shadow: 0 18px 50px rgba(23,33,31,.28), 0 2px 6px rgba(23,33,31,.12); }
  .caption .bar { width: 10px; background: #0d846f; flex: none; }
  .caption .body { padding: 22px 34px 24px 28px; }
  .kicker { color: #0d846f; font-size: 21px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
  .caption h1 { margin: 4px 0 0; color: #17211f; font-size: 46px; font-weight: 750; line-height: 1.12; letter-spacing: -.01em; }
  .caption p { margin: 8px 0 0; color: #5d6d68; font-size: 26px; line-height: 1.3; }
  .card { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: radial-gradient(1100px 700px at 50% 38%, #1f4a40 0%, #17211f 62%); color: #fff; text-align: center; }
  .card img { width: 150px; height: 150px; margin-bottom: 34px; }
  .card h1 { margin: 0; font-size: 104px; font-weight: 800; letter-spacing: -.02em; }
  .card h2 { margin: 18px 0 0; color: #9fdcc9; font-size: 44px; font-weight: 600; }
  .card p { margin: 44px 0 0; color: #b9c8c3; font-size: 28px; letter-spacing: .04em; }
  .card .url { margin-top: 26px; padding: 14px 30px; border: 2px solid #3f8f7c; border-radius: 14px; color: #fff;
    font-size: 36px; font-weight: 600; }
`;

function html(c) {
  if (c.kind === 'caption') {
    return `<div class="caption"><div class="bar"></div><div class="body">
      ${c.kicker ? `<div class="kicker">${esc(c.kicker)}</div>` : ''}<h1>${esc(c.title)}</h1>
      ${c.sub ? `<p>${esc(c.sub)}</p>` : ''}</div></div>`;
  }
  return `<div class="card"><img src="${LOGO}"><h1>${esc(c.title)}</h1>
    ${c.sub ? `<h2>${esc(c.sub)}</h2>` : ''}
    ${c.url ? `<div class="url">${esc(c.url)}</div>` : ''}
    ${c.kicker ? `<p>${esc(c.kicker)}</p>` : ''}</div>`;
}

fs.mkdirSync(outDir, { recursive: true });
const b = new Browser({ width: 1920, height: 1080, scale: 1, port: 9334 });
await b.launch();
try {
  await b.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  for (const c of cards) {
    const page = path.join(outDir, `${c.name}.html`);
    fs.writeFileSync(page, `<!doctype html><meta charset="utf-8"><style>${CSS}</style>${html(c)}`);
    await b.goto(pathToFileURL(page).href);
    await b.eval('document.fonts.ready.then(() => true)');
    await sleep(150);
    const { data } = await b.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(outDir, `${c.name}.png`), Buffer.from(data, 'base64'));
  }
} finally {
  await b.close();
}
console.log(`${cards.length} cards -> ${outDir}`);
