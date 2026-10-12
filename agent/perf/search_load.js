// k6 run -e BASE_URL=... -e TOKEN=... perf/search_load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = { vus: 10, duration: '30s',
  thresholds: { http_req_duration: ['p(95)<500'], http_req_failed: ['rate<0.01'] } };
const queries = ['Dolo', 'paracetamol', 'high blood pressure', 'penicillin allergy', 'diabeetes']; // replace with real ones
export default function () {
  const q = queries[Math.floor(Math.random() * queries.length)];
  const r = http.post(`${__ENV.BASE_URL || 'http://127.0.0.1:5000'}${__ENV.SEARCH_PATH || '/api/search'}`,
    JSON.stringify({ query: q, patient_id: __ENV.PATIENT || 'P001' }),
    { headers: { 'Content-Type': 'application/json', [__ENV.AUTH_HEADER || 'X-Token']: __ENV.TOKEN || '' } });
  check(r, { 'status 200': (x) => x.status === 200 });
  sleep(1);
}
