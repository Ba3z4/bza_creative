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
const siteUrl = 'https://bzacreative.com/';
const titles = new Set();
const canonicals = new Set();
let pagesChecked = 0;
const decode = value => value?.replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const descriptions = new Set();
let references = 0;
for (const file of pages) {
  const html = await readFile(file, 'utf8');
  const relative = path.relative(root, file);
  if (/name="robots" content="noindex/.test(html)) continue;
  pagesChecked++;
  const canonical = html.match(/rel="canonical" href="([^"]+)"/)?.[1];
  assert.ok(canonical?.startsWith(siteUrl), `${relative}: canonical uses ${siteUrl}`);
  canonicals.add(canonical);
  const meta = property => decode(html.match(new RegExp(`property="${property}" content="([^"]*)"`))?.[1]);
  assert.equal(meta('og:url'), canonical, `${relative}: og:url matches canonical`);
  assert.equal(meta('og:image'), `${siteUrl}assets/og-bza-creative.png`, `${relative}: og:image`);
  for (const match of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
    assert.doesNotThrow(() => JSON.parse(match[1]), `${relative}: valid JSON-LD`);
  }
  assert.equal((html.match(/<h1\b/g) || []).length, 1, `${relative}: one primary heading`);
  const title = html.match(/<title>([^<]+)<\/title>/)?.[1];
  assert.ok(title && !titles.has(title), `${relative}: unique title`);
  titles.add(title);
  const description = html.match(/name="description" content="([^"]+)"/)?.[1];
  assert.ok(description && !descriptions.has(description), `${relative}: unique description`);
  descriptions.add(description);
  assert.equal(meta('og:title'), decode(title), `${relative}: og:title matches title`);
  assert.equal(meta('og:description'), decode(description), `${relative}: og:description matches description`);
  assert.match(html, /aria-current="page"/, `${relative}: current page indicator`);
  assert.match(html, /campaign\.js/, `${relative}: campaign attribution script`);
  assert.match(html, /<button type="button" class="footer-consent" data-consent-reset hidden>Preferencias de cookies<\/button>/, `${relative}: footer cookie preferences link`);
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
assert.equal(pagesChecked, 9, 'Home, campaign landing, four detail pages, two local landings and privacy notice exist');
const sitemap = await readFile(path.join(root, 'sitemap.xml'), 'utf8');
const listed = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(match => match[1]).sort();
assert.deepEqual(listed, [...canonicals].sort(), 'sitemap lists exactly the canonical URL of every public page');
console.log(`Verified ${pagesChecked} pages and ${references} local links/assets; unique metadata, Open Graph, sitemap and valid WhatsApp links.`);
