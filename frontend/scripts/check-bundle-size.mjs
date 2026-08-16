import { readdir, stat } from "node:fs/promises";
import { join } from "node:path";

const assetsDirectory = new URL("../dist/assets/", import.meta.url);
const files = await readdir(assetsDirectory);
const javascriptFiles = files.filter((file) => file.endsWith(".js"));
const budgets = {
  initial: 250 * 1024,
  map: 1_100 * 1024
};

for (const file of javascriptFiles) {
  const size = (await stat(join(assetsDirectory.pathname, file))).size;
  const budget = file.startsWith("MapView-") ? budgets.map : budgets.initial;
  if (size > budget) {
    throw new Error(
      `${file} is ${Math.ceil(size / 1024)} KB, above its ${Math.ceil(budget / 1024)} KB budget`
    );
  }
}

console.log(`Bundle budgets passed for ${javascriptFiles.length} JavaScript chunks.`);
