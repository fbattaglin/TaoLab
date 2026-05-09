/**
 * Post-build organizer.
 *
 * Vite's multi-page build emits `<entry>.html` files at the root of `dist/`
 * sharing a single `assets/` folder. Streamlit's `declare_component(path=…)`
 * serves *only* the files under the directory you point at — anything
 * referenced via `../assets/` 404s, because the parent directory is outside
 * the served root.
 *
 * To keep each component self-contained we reorganise the build into:
 *
 *   dist/
 *     stepper/
 *       index.html
 *       assets/...   (full copy)
 *     verdict/
 *       index.html
 *       assets/...   (full copy)
 *     prescription/
 *       index.html
 *       assets/...   (full copy)
 *
 * The shared React/Tailwind chunk (~150 KB) is duplicated three times. That's
 * acceptable: total dist remains under 600 KB and each component loads
 * without cross-directory hops.
 */

import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const distDir = join(here, "..", "dist");
const sharedAssets = join(distDir, "assets");

const components = ["stepper", "verdict", "prescription"];

for (const name of components) {
  const srcHtml = join(distDir, `${name}.html`);
  if (!existsSync(srcHtml)) {
    console.warn(`[post-build] missing ${srcHtml}; skipping`);
    continue;
  }

  const targetDir = join(distDir, name);
  if (existsSync(targetDir)) rmSync(targetDir, { recursive: true });
  mkdirSync(targetDir, { recursive: true });

  // Rewrite asset references in the HTML to use a same-directory `assets/`.
  let html = readFileSync(srcHtml, "utf8");
  html = html.replaceAll('href="./assets/', 'href="assets/');
  html = html.replaceAll('src="./assets/', 'src="assets/');
  html = html.replaceAll('href="../assets/', 'href="assets/');
  html = html.replaceAll('src="../assets/', 'src="assets/');
  html = html.replaceAll('href="/assets/', 'href="assets/');
  html = html.replaceAll('src="/assets/', 'src="assets/');
  writeFileSync(join(targetDir, "index.html"), html, "utf8");

  // Bundle a self-contained copy of the shared assets next to index.html.
  if (existsSync(sharedAssets)) {
    cpSync(sharedAssets, join(targetDir, "assets"), { recursive: true });
  }

  rmSync(srcHtml);
}

// Drop the now-orphaned shared assets folder so the dist tree is tidy.
if (existsSync(sharedAssets)) {
  rmSync(sharedAssets, { recursive: true });
}

console.log(`[post-build] organised: ${components.join(", ")}`);
