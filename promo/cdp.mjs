// Minimal Chrome DevTools Protocol driver for recording the promo (Node >= 22, no dependencies).
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// A visible cursor (headless Chrome has none) and a click ripple, injected into every page.
const CURSOR_JS = `
(() => {
  if (window.__promoCursor) return;
  const install = () => {
    const c = document.createElement('div');
    c.id = '__promo_cursor';
    c.innerHTML = '<svg width="28" height="28" viewBox="0 0 28 28"><path d="M5 3 L5 22 L10 17 L13.5 25 L17 23.5 L13.5 15.5 L20.5 15.5 Z" fill="#17211f" stroke="white" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position: 'fixed', left: '0px', top: '0px', zIndex: 2147483647, pointerEvents: 'none',
      transform: 'translate(-5px,-3px)', filter: 'drop-shadow(0 2px 3px rgba(0,0,0,.25))'});
    document.documentElement.appendChild(c);
    window.__promoCursor = {x: innerWidth * 0.55, y: innerHeight * 0.6};
    c.style.left = window.__promoCursor.x + 'px';
    c.style.top = window.__promoCursor.y + 'px';
  };
  if (document.body) install(); else addEventListener('DOMContentLoaded', install);
  window.__promoMove = (x, y, ms) => new Promise((done) => {
    const c = document.getElementById('__promo_cursor');
    const from = {...window.__promoCursor};
    const t0 = performance.now();
    const step = (t) => {
      const k = Math.min(1, (t - t0) / ms);
      const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      const px = from.x + (x - from.x) * e, py = from.y + (y - from.y) * e;
      c.style.left = px + 'px';
      c.style.top = py + 'px';
      window.__promoCursor = {x: px, y: py};
      if (k < 1) requestAnimationFrame(step); else done();
    };
    requestAnimationFrame(step);
  });
  window.__promoRipple = (x, y) => {
    const r = document.createElement('div');
    Object.assign(r.style, {position: 'fixed', left: (x - 18) + 'px', top: (y - 18) + 'px', width: '36px', height: '36px',
      borderRadius: '50%', background: 'rgba(13,132,111,.35)', zIndex: 2147483646, pointerEvents: 'none',
      transition: 'transform .45s ease-out, opacity .45s ease-out'});
    document.documentElement.appendChild(r);
    requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 500);
  };
  // Center of the first visible element matching a selector and, optionally, containing a text
  window.__promoFind = (selector, text) => {
    const els = [...document.querySelectorAll(selector)].filter((el) => {
      const b = el.getBoundingClientRect();
      return b.width > 0 && b.height > 0 && (!text || el.textContent.trim().includes(text));
    });
    if (!els.length) return null;
    const el = text ? els.sort((a, b) => a.textContent.length - b.textContent.length)[0] : els[0];
    let b = el.getBoundingClientRect();
    // Out of the viewport, or covered by something else (a sticky toolbar): bring it to the middle
    const hit = (r) => { const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return h && (h === el || el.contains(h)); };
    if (b.top < 0 || b.bottom > innerHeight || b.left < 0 || b.right > innerWidth || !hit(b)) {
      el.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'instant'});
      b = el.getBoundingClientRect();
    }
    return {x: b.left + b.width / 2, y: b.top + b.height / 2, w: b.width, h: b.height};
  };
})();`;

export class Browser {
  constructor({ width = 1600, height = 900, scale = 1.2, port = 9333 } = {}) {
    Object.assign(this, { width, height, scale, port, id: 0, pending: new Map(), handlers: new Map() });
  }

  async launch() {
    this.profile = fs.mkdtempSync(path.join(os.tmpdir(), 'promo-chrome-'));
    this.proc = spawn('google-chrome', ['--headless=new', `--remote-debugging-port=${this.port}`,
      `--user-data-dir=${this.profile}`, '--lang=en-US', '--hide-scrollbars', '--no-first-run',
      '--no-default-browser-check', '--disable-extensions', `--force-device-scale-factor=${this.scale}`, '--enable-unsafe-swiftshader', '--use-angle=swiftshader',
      `--window-size=${this.width},${this.height}`, 'about:blank'],
    // --lang alone leaves native controls (the file input) in the system language on Linux
    { stdio: 'ignore', env: { ...process.env, LANG: 'en_US.UTF-8', LANGUAGE: 'en_US' } });
    let target;
    for (let i = 0; i < 100 && !target; i++) {
      await sleep(100);
      try {
        const list = await (await fetch(`http://127.0.0.1:${this.port}/json/list`)).json();
        target = list.find((t) => t.type === 'page');
      } catch { /* not up yet */ }
    }
    this.ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((r) => this.ws.addEventListener('open', r, { once: true }));
    this.ws.addEventListener('message', (m) => {
      const msg = JSON.parse(m.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(`${msg.error.message} (${JSON.stringify(msg.error.data || '')})`));
        else resolve(msg.result);
      } else if (msg.method && this.handlers.has(msg.method)) {
        this.handlers.get(msg.method)(msg.params);
      }
    });
    await this.send('Page.enable');
    await this.send('Runtime.enable');
    await this.send('Emulation.setDeviceMetricsOverride',
      { width: this.width, height: this.height, deviceScaleFactor: this.scale, mobile: false });
    await this.send('Page.addScriptToEvaluateOnNewDocument', { source: CURSOR_JS });
  }

  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }

  on(event, handler) { this.handlers.set(event, handler); }

  async eval(expression) {
    const r = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`${expression.slice(0, 80)}: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`);
    return r.result.value;
  }

  async goto(url) {
    await this.send('Page.navigate', { url });
    await this.waitFor('document.readyState === "complete" && !!window.__promoFind');
    await this.eval(CURSOR_JS);
  }

  async waitFor(expression, timeout = 60000) {
    const t0 = Date.now();
    for (;;) {
      try { if (await this.eval(`!!(${expression})`)) return; } catch { /* page navigating */ }
      if (Date.now() - t0 > timeout) throw new Error(`timeout waiting for ${expression}`);
      await sleep(100);
    }
  }

  async find(selector, text, timeout = 30000) {
    const call = `window.__promoFind(${JSON.stringify(selector)}, ${JSON.stringify(text || '')})`;
    await this.waitFor(call, timeout);
    await this.eval(call);   // scrolls it into view if needed
    await sleep(250);
    return this.eval(call);
  }

  async moveTo(x, y, ms = 650) {
    await this.eval(`window.__promoMove(${x}, ${y}, ${ms})`);
    await this.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  }

  async click(selector, text, { ms = 650, pause = 250 } = {}) {
    let p = await this.find(selector, text);
    await this.moveTo(p.x, p.y, ms);
    await sleep(pause);
    // The page may have scrolled or shifted meanwhile: measure again right before clicking
    const call = `window.__promoFind(${JSON.stringify(selector)}, ${JSON.stringify(text || '')})`;
    const q = await this.eval(call);
    if (q && (Math.abs(q.x - p.x) > 2 || Math.abs(q.y - p.y) > 2)) {
      p = q;
      await this.moveTo(p.x, p.y, 200);
    }
    await this.eval(`window.__promoRipple(${p.x}, ${p.y})`);
    for (const type of ['mousePressed', 'mouseReleased']) {
      await this.send('Input.dispatchMouseEvent', { type, x: p.x, y: p.y, button: 'left', clickCount: 1 });
    }
    return p;
  }

  async drag(x1, y1, x2, y2, ms = 900) {
    await this.moveTo(x1, y1);
    await this.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: x1, y: y1, button: 'left', clickCount: 1 });
    const steps = Math.round(ms / 16);
    for (let i = 1; i <= steps; i++) {
      const x = x1 + (x2 - x1) * i / steps, y = y1 + (y2 - y1) * i / steps;
      await this.eval(`(() => { const c = document.getElementById('__promo_cursor'); c.style.left='${x}px'; c.style.top='${y}px'; window.__promoCursor={x:${x},y:${y}}; })()`);
      await this.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, button: 'left', buttons: 1 });
      await sleep(16);
    }
    await this.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: x2, y: y2, button: 'left', clickCount: 1 });
  }

  async type(text, cps = 22) {
    for (const ch of text) {
      if (ch === '\n') {
        // A real Enter would accept an open autocompletion in the SQL editor
        await this.send('Input.insertText', { text: ch });
      } else {
        // Key events (not just inserted text) so keyup handlers in the app run too
        await this.send('Input.dispatchKeyEvent', { type: 'keyDown', key: ch, text: ch, unmodifiedText: ch });
        await this.send('Input.dispatchKeyEvent', { type: 'keyUp', key: ch });
      }
      await sleep(1000 / cps * (0.6 + Math.random() * 0.8));
    }
  }

  async key(key, modifiers = 0) {
    const codes = { Enter: 13, Tab: 9, Escape: 27, Backspace: 8, End: 35 };
    const base = { key, code: key, windowsVirtualKeyCode: codes[key] || key.toUpperCase().charCodeAt(0), modifiers };
    await this.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', ...base, ...(key === 'Enter' ? { text: '\r' } : {}) });
    await this.send('Input.dispatchKeyEvent', { type: 'keyUp', ...base });
  }

  async scroll(x, y, deltaY, steps = 12) {
    await this.moveTo(x, y, 400);
    for (let i = 0; i < steps; i++) {
      await this.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x, y, deltaX: 0, deltaY: deltaY / steps });
      await sleep(30);
    }
  }

  // Screencast: frames arrive when the page repaints; each one lasts until the next.
  async startRecording(dir) {
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    this.frames = [];
    this.frameDir = dir;
    this.on('Page.screencastFrame', async (f) => {
      const file = path.join(dir, `${String(this.frames.length).padStart(6, '0')}.jpg`);
      fs.writeFileSync(file, Buffer.from(f.data, 'base64'));
      this.frames.push({ file, t: f.metadata.timestamp });
      try { await this.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch { /* closing */ }
    });
    await this.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
    // A repaint so the first frame arrives right away
    await this.eval('document.documentElement.style.outline = "0px solid transparent"');
  }

  async stopRecording(outFile, fps = 30) {
    const tEnd = Date.now() / 1000;
    await this.send('Page.stopScreencast');
    const lines = [];
    this.frames.forEach((f, i) => {
      const next = i + 1 < this.frames.length ? this.frames[i + 1].t : tEnd;
      lines.push(`file '${f.file}'`, `duration ${Math.max(0.001, next - f.t).toFixed(4)}`);
    });
    lines.push(`file '${this.frames.at(-1).file}'`);
    const list = path.join(this.frameDir, 'list.txt');
    fs.writeFileSync(list, lines.join('\n') + '\n');
    await new Promise((resolve, reject) => {
      const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list,
        '-vf', `scale=1920:1080:flags=lanczos,fps=${fps},format=yuv420p`, '-c:v', 'libx264', '-crf', '14',
        '-preset', 'medium', outFile], { stdio: 'inherit' });
      ff.on('exit', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exit ${code}`))));
    });
    return { frames: this.frames.length, seconds: tEnd - this.frames[0].t };
  }

  async close() {
    const exited = new Promise((r) => this.proc.once('exit', r));
    try { await this.send('Browser.close'); } catch { /* already gone */ }
    this.proc.kill();
    await exited;
    await sleep(500);   // Chrome's helper processes may still be writing to the profile
    try { fs.rmSync(this.profile, { recursive: true, force: true, maxRetries: 5 }); } catch { /* left in /tmp */ }
  }
}

export { sleep };
