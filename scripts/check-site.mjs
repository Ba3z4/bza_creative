import assert from 'node:assert/strict';
import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('../dist/', import.meta.url)));
const pages = [];
async function walk(directory) {
  for (const item of await readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, item.name);
    if (item.isDirectory()) await walk(file);
    else if (file.endsWith('.html')) pages.push(file);
  }
}
await walk(root);
const titles = new Set();
const descriptions = new Set();
let references = 0;
for (const file of pages) {
  const html = await readFile(file, 'utf8');
  const relative = path.relative(root, file);
  assert.equal((html.match(/<h1\b/g) || []).length, 1, `${relative}: one primary heading`);
  const title = html.match(/<title>([^<]+)<\/title>/)?.[1];
  assert.ok(title && !titles.has(title), `${relative}: unique title`);
  titles.add(title);
  const description = html.match(/name="description" content="([^"]+)"/)?.[1];
  assert.ok(description && !descriptions.has(description), `${relative}: unique description`);
  descriptions.add(description);
  assert.match(html, /aria-current="page"/, `${relative}: current page indicator`);
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, `${relative}: no duplicate IDs`);
  for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const value = match[1];
    if (/^(https?:|data:|mailto:|tel:)/.test(value)) continue;
    const [target, fragment] = value.split('#');
    let resolved = target ? path.resolve(path.dirname(file), target) : file;
    assert.ok(resolved === root || resolved.startsWith(root + path.sep), `${relative}: asset stays inside dist`);
    const info = await stat(resolved).catch(() => null);
    assert.ok(info, `${relative}: missing ${value}`);
    if (info.isDirectory()) resolved = path.join(resolved, 'index.html');
    const destination = await readFile(resolved);
    if (fragment) assert.ok(destination.toString().includes(`id="${fragment}"`), `${relative}: missing anchor ${value}`);
    references++;
  }
  for (const match of html.matchAll(/href="(https:\/\/wa.me\/[^"?]+)/g)) {
    assert.equal(match[1], 'https://wa.me/523342781554', `${relative}: correct contact number`);
  }
}
assert.equal(pages.length, 4, 'Home and three detail pages exist');
console.log(`Verified ${pages.length} pages and ${references} local links/assets; unique metadata and valid WhatsApp links.`);
