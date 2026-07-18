import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, "..", "out");

function walk(dir, callback) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, callback);
    } else {
      callback(full);
    }
  }
}

let removed = 0;
let saved = 0;

if (fs.existsSync(OUT_DIR)) {
  walk(OUT_DIR, (file) => {
    const basename = path.basename(file);
    if (basename.startsWith("__next")) {
      const stat = fs.statSync(file);
      fs.unlinkSync(file);
      removed += 1;
      saved += stat.size;
    }
  });
}

console.log(`[clean-build-traces] removed ${removed} files (${(saved / 1024 / 1024).toFixed(1)} MB)`);
