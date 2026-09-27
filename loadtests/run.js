import http from 'k6/http';
import exec from 'k6/execution';
import { check } from 'k6';

const names = ['baseline', 'deadline_storm', 'judging_open', 'voting_spike', 'gallery_spike'];
if (__ENV.DISPOSABLE_TARGET !== '1' || !__ENV.PROFILE || !names.includes(__ENV.SCENARIO)) {
  throw new Error('Set DISPOSABLE_TARGET=1, PROFILE and one named SCENARIO');
}

const profile = JSON.parse(open(__ENV.PROFILE));
const name = __ENV.SCENARIO;
if (!profile[name] || !Array.isArray(profile[name].requests)) {
  throw new Error(`Profile must define requests for ${name}`);
}

const config = profile[name];
if (!config.requests.length || !Number.isInteger(config.vus) || config.vus < 1) {
  throw new Error(`${name} needs requests and a positive integer vus`);
}
const scenarios = {
  [name]: {
    executor: 'shared-iterations',
    exec: 'request',
    vus: config.vus,
    iterations: config.requests.length,
    maxDuration: config.maxDuration || '2m',
    tags: { scenario_name: name },
  },
};
const writes = new Set();
for (const item of config.requests) {
  if (!/^https?:\/\//.test(item.url) || !['GET', 'POST', 'PATCH'].includes(item.method)) {
    throw new Error(`${name} has an invalid URL or method`);
  }
  if (!Number.isInteger(item.expect) || item.expect < 200 || item.expect > 299) {
    throw new Error(`${name} request needs an explicit expected 2xx status`);
  }
  if (item.method !== 'GET') {
    const key = `${item.method}\n${item.url}\n${item.body || ''}`;
    if (writes.has(key)) {
      throw new Error(`${name} repeats a write request`);
    }
    writes.add(key);
  }
}

export const options = {
  scenarios,
  thresholds: {
    'checks': ['rate>0.999'],
    'http_req_failed': ['rate<0.001'],
  },
};

export function request() {
  const name = exec.scenario.name;
  const item = profile[name].requests[exec.scenario.iterationInTest];
  const params = { headers: item.headers || {}, tags: { scenario_name: name } };
  const response = http.request(item.method, item.url, item.body || null, params);
  check(response, { [`${name} status ${item.expect}`]: (r) => r.status === item.expect });
}
