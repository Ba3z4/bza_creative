import assert from 'node:assert/strict';
import worker from '../src/worker.js';

const oldHost = 'https://bza-creative.ingluisbaeza.workers.dev';
const site = 'https://www.bzacreative.com';
const calls = [];
const env = { ASSETS: { fetch: async request => { calls.push(request); return new Response('asset'); } } };
let cases = 0;

async function expectRedirect(url, location, method = 'GET') {
  calls.length = 0;
  const response = await worker.fetch(new Request(url, { method }), env);
  assert.equal(response.status, 301, `${method} ${url}: permanent redirect`);
  assert.equal(response.headers.get('Location'), location, `${method} ${url}: exact Location`);
  assert.equal(calls.length, 0, `${method} ${url}: does not touch assets`);
  cases++;
}

async function expectAssets(url, method = 'GET') {
  calls.length = 0;
  const request = new Request(url, { method });
  const response = await worker.fetch(request, env);
  assert.equal(calls.length, 1, `${url}: served from assets`);
  assert.equal(calls[0], request, `${url}: request passed unchanged`);
  assert.equal(response.status, 200, `${url}: asset response returned`);
  assert.equal(await response.text(), 'asset', `${url}: asset body returned`);
  cases++;
}

const campaign = '/campana/?utm_source=instagram&utm_medium=organic_social&utm_campaign=lanzamiento_bza_2026&utm_content=bio';
await expectRedirect(`${oldHost}/`, `${site}/`);
await expectRedirect(oldHost, `${site}/`);
await expectRedirect(`${oldHost}${campaign}`, `${site}${campaign}`);
await expectRedirect(`${oldHost}/servicios?utm_content=post%20uno&ref=%C3%B1#faq`, `${site}/servicios?utm_content=post%20uno&ref=%C3%B1`);
await expectRedirect(`${oldHost}/assets/og-bza-creative.png`, `${site}/assets/og-bza-creative.png`);
await expectRedirect('https://BZA-Creative.ingluisbaeza.workers.dev/enfoque/', `${site}/enfoque/`);
await expectRedirect(`${oldHost}${campaign}`, `${site}${campaign}`, 'HEAD');

await expectAssets(`${site}/`);
await expectAssets(`${site}${campaign}`);
await expectAssets('https://bzacreative.com/servicios/');
await expectAssets('https://abc123-bza-creative.ingluisbaeza.workers.dev/campana/');
await expectAssets('http://localhost:8787/');
await expectAssets(`${site}/`, 'HEAD');

console.log(`Verified ${cases} worker cases: workers.dev redirects 301 to ${site} with path and query; other hosts are served from dist.`);
