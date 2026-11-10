// Fast QA stills: node stills.mjs 120 450 900   (frames; COMP=Cover node stills.mjs 600 for another comp)
// Writes out/st/f0120.png ... at half size. One bundle for all frames, so it is much faster than `remotion still` per frame.
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";

const frames = process.argv.slice(2).map(Number).filter((n) => Number.isFinite(n));
if (!frames.length) { console.log("usage: node stills.mjs <frame> [frame...]"); process.exit(1); }
fs.mkdirSync("out/st", { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const id = process.env.COMP || "Film";
const composition = await selectComposition({ serveUrl, id, chromiumOptions: { gl: "angle" } });
for (const frame of frames) {
  try {
    await renderStill({ composition, serveUrl, frame, output: `out/st/f${String(frame).padStart(4, "0")}.png`, chromiumOptions: { gl: "angle" }, scale: 0.5 });
  } catch (e) {
    console.log("\nERR", frame, String(e.message).slice(0, 300));
  }
  process.stdout.write(frame + " ");
}
console.log("\ndone -> out/st/");
