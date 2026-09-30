// Derives standalone HTML prototypes + screenshots from the canvas boards.
// Usage (from repo root):  node docs/product-depth-v3/design/exports/r2.1/tools/build-exports.mjs [--shots] [--only Name]
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const DESIGN = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../../..");
const CANVAS = path.join(DESIGN, "exports/r2.1/canvas/project");
const idx = JSON.parse(fs.readFileSync(path.join(CANVAS, "canvas.json"), "utf8"));
const REF = (n) => {
  if (n.startsWith("Sys-")) return "system/prototypes";
  if (n.startsWith("Dark-")) return "references/dark-mode";
  if (n.startsWith("Resp-") || n.startsWith("Wide-")) return "references/responsive-wide";
  if (n.startsWith("Pairwise-")) return "references/judge-review";
  if (n.startsWith("Shell-")) return "references/app-shell";
  if (n.startsWith("Data-")) return "references/organizer-data-surface";
  if (n.startsWith("MyEvent")) return "references/participant-my-event";
  if (n.startsWith("Story-")) return "references/project-story-editor";
  if (n.startsWith("Judge-")) return "references/judge-review";
  if (n.startsWith("Deliberation")) return "references/deliberation-awards";
  if (n.startsWith("Public-Event")) return "references/public-event";
  if (n.startsWith("Public-Project")) return "references/public-project";
  if (n.startsWith("Builder-")) return "references/event-builder";
  if (n.startsWith("Onsite-")) return "references/onsite-mobile";
  if (n.startsWith("States-")) return "states";
  return "exports/r2.1";
};
// r2.1: same pipeline as r2 (outputs to exports/r2.1/qa).
const only = process.argv.includes("--only") ? process.argv[process.argv.indexOf("--only") + 1] : null;
const shots = process.argv.includes("--shots");
const cssTarget = path.join(DESIGN, "system/v3.css");
fs.copyFileSync(path.join(CANVAS, "v3.css"), cssTarget);
const out = [];
for (const file of idx.order) {
  const name = file.replace(".dc.html", "");
  if (only && name !== only) continue;
  const dir = path.join(DESIGN, REF(file));
  fs.mkdirSync(path.join(dir, "html"), { recursive: true });
  let s = fs.readFileSync(path.join(CANVAS, file), "utf8");
  const helm = (s.match(/<helmet>([\s\S]*?)<\/helmet>/) || [, ""])[1];
  s = s.replace(/<script src="\.\/support\.js"><\/script>\n?/, "")
    .replace(/<helmet>[\s\S]*?<\/helmet>\n?/, "")
    .replace(/<\/?x-dc>\n?/g, "")
    .replace(/<script type="text\/x-dc"[\s\S]*?<\/script>\n?/, "")
    .replace(/href="\.\/v3\.css"/, `href="${path.relative(path.join(dir, "html"), cssTarget)}"`)
    .replace("</head>", `${helm}\n<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>`);
  const dest = path.join(dir, "html", `${name}.html`);
  fs.writeFileSync(dest, s);
  out.push({ name, file, dest, box: idx.boards[file], dir });
}
if (shots) {
  const { chromium } = require(path.resolve(DESIGN, "../../../node_modules/@playwright/test"));
  const browser = await chromium.launch();
  const report = [];
  for (const o of out) {
    const page = await browser.newPage({ viewport: { width: o.box.w, height: o.box.h }, deviceScaleFactor: 1 });
    await page.goto("file://" + o.dest, { waitUntil: "load" }).catch(() => {});
    await page.waitForTimeout(150);
    const m = await page.evaluate(() => {
      const root = document.body.firstElementChild;
      const r = root.getBoundingClientRect();
      let maxB = 0, maxR = 0, clipped = 0;
      root.querySelectorAll("*").forEach((e) => {
        const b = e.getBoundingClientRect();
        if (b.width === 0 && b.height === 0) return;
        maxB = Math.max(maxB, b.bottom); maxR = Math.max(maxR, b.right);
      });
      return { rw: r.width, rh: r.height, sh: root.scrollHeight, sw: root.scrollWidth, maxB: Math.round(maxB), maxR: Math.round(maxR) };
    });
    fs.mkdirSync(path.join(o.dir, "screenshots"), { recursive: true });
    await page.screenshot({ path: path.join(o.dir, "screenshots", `${o.name}.png`), clip: { x: 0, y: 0, width: o.box.w, height: o.box.h } });
    report.push({ name: o.name, declared: `${o.box.w}x${o.box.h}`, root: `${Math.round(m.rw)}x${Math.round(m.rh)}`, scrollH: m.sh, scrollW: m.sw, contentBottom: m.maxB, contentRight: m.maxR });
    await page.close();
  }
  await browser.close();
  console.table(report);
  fs.mkdirSync(path.join(DESIGN, "exports/r2.1/qa"), { recursive: true });
  fs.writeFileSync(path.join(DESIGN, "exports/r2.1/qa/dimension-report" + (only ? "-" + only : "") + ".json"), JSON.stringify(report, null, 1));
}
console.log(`built ${out.length} standalone files`);
