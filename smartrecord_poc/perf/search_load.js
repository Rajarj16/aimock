// k6 run perf/search_load.js   (set BASE_URL / TOKEN for the real app)
import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = { vus: 10, duration: '30s',
  thresholds: { http_req_duration: ['p(95)<500'], http_req_failed: ['rate<0.01'] } };
const queries = ['Dolo', 'paracetamol', 'high blood pressure', 'penicillin allergy', 'diabeetes'];
export default function () {
  const q = queries[Math.floor(Math.random() * queries.length)];
  const r = http.post(`${__ENV.BASE_URL || 'http://127.0.0.1:5000'}/api/search`,
    JSON.stringify({ query: q, patient_id: 'P001' }),
    { headers: { 'Content-Type': 'application/json', 'X-Token': __ENV.TOKEN || 'demo-token' } });
  check(r, { 'status 200': (x) => x.status === 200, 'has results key': (x) => x.json('results') !== undefined });
  sleep(1);
}
