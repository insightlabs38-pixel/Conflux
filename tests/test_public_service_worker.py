import subprocess
from pathlib import Path

import pytest

WORKER = Path(__file__).resolve().parents[1] / "src/web/styles/sw.js"


@pytest.mark.parametrize("scenario", ["normal", "no-store", "not-found", "offline"])
def test_public_worker_respects_response_visibility_and_offline_history(scenario):
    script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const listeners = {};
const scenario = process.argv[2];
const request = {method: 'GET', url: 'https://local.test/e/event/results/'};
let cached = new Response('previous');
const cache = {
  async put(key, value) { cached = value; },
  async delete(key) { cached = undefined; },
};
const network = scenario === 'not-found'
  ? new Response('hidden', {status: 404})
  : new Response('fresh', {
    headers: scenario === 'no-store' ? {'Cache-Control': 'private, no-store'} : {}
  });
const pending = [];
let returned;
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {
  self: {
    location: {origin: 'https://local.test'},
    addEventListener(name, handler) {listeners[name] = handler;}
  },
  caches: {async open() {return cache;}, async match() {return cached;}},
  async fetch() {if (scenario === 'offline') throw Error('offline'); return network;},
  URL, Response,
});
listeners.fetch({
  request, respondWith(value) {returned = value;}, waitUntil(value) {pending.push(value);}
});
(async () => {
  const response = await returned;
  await Promise.all(pending);
  if (scenario === 'offline') {
    assert.equal(await response.text(), 'previous');
  } else {
    assert.equal(response, network);
    if (scenario === 'normal') assert.equal(await cached.text(), 'fresh');
    else assert.equal(cached, undefined);
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
"""
    result = subprocess.run(
        ["node", "-e", script, str(WORKER), scenario], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
