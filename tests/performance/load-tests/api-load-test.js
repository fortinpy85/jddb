import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '2m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 50 },  // Ramp up to 50 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete within 2s
    http_req_failed: ['rate<0.05'],    // Error rate must be below 5%
    errors: ['rate<0.05'],             // Custom error rate below 5%
  },
};

const BASE_URL = 'http://localhost:8000/api';

export default function () {
  // Test health endpoint
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  // Test jobs listing endpoint
  const jobsResponse = http.get(`${BASE_URL}/jobs?limit=20&skip=0`);
  check(jobsResponse, {
    'jobs listing status is 200': (r) => r.status === 200,
    'jobs listing response time < 1000ms': (r) => r.timings.duration < 1000,
    'jobs listing returns JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
  }) || errorRate.add(1);

  // Test search endpoint
  const searchResponse = http.get(`${BASE_URL}/search?q=manager&limit=10`);
  check(searchResponse, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 1500ms': (r) => r.timings.duration < 1500,
    'search returns JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
  }) || errorRate.add(1);

  // Test analytics endpoint
  const analyticsResponse = http.get(`${BASE_URL}/analytics/performance-summary`);
  check(analyticsResponse, {
    'analytics status is 200': (r) => r.status === 200,
    'analytics response time < 1000ms': (r) => r.timings.duration < 1000,
  }) || errorRate.add(1);

  // Test job statistics
  const statsResponse = http.get(`${BASE_URL}/jobs/statistics`);
  check(statsResponse, {
    'stats status is 200': (r) => r.status === 200,
    'stats response time < 800ms': (r) => r.timings.duration < 800,
  }) || errorRate.add(1);

  // Test Phase 2 monitoring endpoint
  const monitoringResponse = http.get(`${BASE_URL}/monitoring/health`);
  check(monitoringResponse, {
    'monitoring status is 200': (r) => r.status === 200,
    'monitoring response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  // Test translation memory health check
  const tmResponse = http.get(`${BASE_URL}/translation-memory/health`);
  check(tmResponse, {
    'translation memory status is 200': (r) => r.status === 200,
    'translation memory response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  // Simulate realistic user behavior with think time
  sleep(Math.random() * 2 + 1); // Random sleep between 1-3 seconds
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'load-test-summary.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options = {}) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;

  const summary = {
    'Test Duration': `${data.state.testRunDurationMs / 1000}s`,
    'Total Requests': data.metrics.http_reqs.values.count,
    'Failed Requests': data.metrics.http_req_failed.values.rate * 100 + '%',
    'Request Rate': `${data.metrics.http_reqs.values.rate.toFixed(2)}/s`,
    'Average Response Time': `${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`,
    '95th Percentile Response Time': `${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`,
    'Data Received': `${(data.metrics.data_received.values.count / 1024 / 1024).toFixed(2)}MB`,
    'Data Sent': `${(data.metrics.data_sent.values.count / 1024).toFixed(2)}KB`,
  };

  let output = '\n=== LOAD TEST SUMMARY ===\n';
  for (const [key, value] of Object.entries(summary)) {
    output += `${indent}${key}: ${value}\n`;
  }

  // Check thresholds
  output += '\n=== THRESHOLD RESULTS ===\n';
  for (const [metric, threshold] of Object.entries(data.thresholds || {})) {
    const status = threshold.ok ? '✓ PASS' : '✗ FAIL';
    output += `${indent}${metric}: ${status}\n`;
  }

  return output;
}