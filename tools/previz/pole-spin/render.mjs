// Render scene.html frame by frame in headless Chromium, then encode with ffmpeg (grain + vignette).
//   node pole-spin/render.mjs [out.mp4] [--stills 0.5,2,5]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const args = process.argv.slice(2);
const stillsIdx = args.indexOf('--stills');
const stills = stillsIdx >= 0 ? args[stillsIdx + 1].split(',').map(Number) : null;
const out = path.resolve(args.find((a, i) => !a.startsWith('--') && i !== stillsIdx + 1) || path.join(here, 'out', 'pole-spin-previz.mp4'));
const FPS = 30;

const types = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
page.on('pageerror', (e) => console.error('page error:', e.message));
await page.goto(`http://localhost:${port}/pole-spin/scene.html`);
await page.waitForFunction(() => window.ready, null, { timeout: 60000 });
const grab = async (t) => {
  const url = await page.evaluate((t) => { window.renderAt(t); return document.querySelector('canvas').toDataURL('image/jpeg', 0.93); }, t);
  return Buffer.from(url.split(',')[1], 'base64');
};

fs.mkdirSync(path.dirname(out), { recursive: true });
if (stills) {
  for (const t of stills) fs.writeFileSync(path.join(path.dirname(out), `still-${t}.jpg`), await grab(t));
} else {
  const frames = path.join(root, 'frames'); fs.rmSync(frames, { recursive: true, force: true }); fs.mkdirSync(frames);
  const total = Math.round((await page.evaluate(() => window.DURATION)) * FPS);
  for (let i = 0; i < total; i++) {
    fs.writeFileSync(path.join(frames, `f${String(i).padStart(4, '0')}.jpg`), await grab(i / FPS));
    if (i % 30 === 0) console.log(`frame ${i}/${total}`);
  }
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(frames, 'f%04d.jpg'),
    '-vf', 'scale=1080:1920:flags=lanczos,noise=alls=6:allf=t,vignette=PI/4.5',
    '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: 'inherit' });
  console.log('wrote', out);
}
await browser.close(); server.close();
