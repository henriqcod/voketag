import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

/**
 * LOW ENHANCEMENT: Load testing with k6
 * 
 * Tests system performance under various load scenarios:
 * - Baseline load
 * - Spike testing
 * - Stress testing
 * - Soak testing
 * 
 * Run: k6 run load-tests/scan-service.js
 */

// Custom metrics
const errorRate = new Rate('errors');
const scanDuration = new Trend('scan_duration');
const antifraudBlocks = new Counter('antifraud_blocks');

// Test configuration
export const options = {
  stages: [
    // Warm-up
    { duration: '30s', target: 10 },
    
    // Ramp up to baseline
    { duration: '1m', target: 50 },
    
    // Baseline load
    { duration: '3m', target: 50 },
    
    // Spike test
    { duration: '30s', target: 200 },
    { duration: '1m', target: 200 },
    { duration: '30s', target: 50 },
    
    // Cool down
    { duration: '30s', target: 0 },
  ],
  
  thresholds: {
    // HTTP errors should be less than 1%
    http_req_failed: ['rate<0.01'],
    
    // 95% of requests should be below 200ms
    http_req_duration: ['p(95)<200'],
    
    // 99% of requests should be below 500ms
    'http_req_duration{scenario:baseline}': ['p(99)<500'],
    
    // Custom metrics
    errors: ['rate<0.01'],
    scan_duration: ['p(95)<100'],
  },
  
  // Test scenarios
  scenarios: {
    // Baseline: Normal traffic
    baseline: {
      executor: 'ramping-vus',
      stages: [
        { duration: '1m', target: 50 },
        { duration: '3m', target: 50 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
    
    // Spike: Sudden traffic increase
    spike: {
      executor: 'ramping-vus',
      startTime: '5m',
      stages: [
        { duration: '10s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '10s', target: 0 },
      ],
    },
    
    // Stress: Gradual increase until breaking point
    stress: {
      executor: 'ramping-vus',
      startTime: '8m',
      stages: [
        { duration: '2m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '2m', target: 300 },
        { duration: '2m', target: 400 },
        { duration: '1m', target: 0 },
      ],
    },
  },
};

// Configuration
const BASE_URL = __ENV.BASE_URL || 'https://api.voketag.com';
const SCAN_ENDPOINT = `${BASE_URL}/v1/scan`;

// Test UUIDs
const TEST_UUIDS = [
  '550e8400-e29b-41d4-a716-446655440000',
  '550e8400-e29b-41d4-a716-446655440001',
  '550e8400-e29b-41d4-a716-446655440002',
  '550e8400-e29b-41d4-a716-446655440003',
  '550e8400-e29b-41d4-a716-446655440004',
];

export default function () {
  // Select random UUID
  const uuid = TEST_UUIDS[Math.floor(Math.random() * TEST_UUIDS.length)];
  
  group('Scan Request', () => {
    const startTime = new Date();
    
    const response = http.get(`${SCAN_ENDPOINT}/${uuid}`, {
      headers: {
        'X-Forwarded-For': generateRandomIP(),
        'User-Agent': 'k6-load-test',
      },
      tags: {
        name: 'scan',
      },
    });
    
    const duration = new Date() - startTime;
    
    // Record metrics
    scanDuration.add(duration);
    
    // Check response
    const success = check(response, {
      'status is 200': (r) => r.status === 200,
      'response time < 200ms': (r) => r.timings.duration < 200,
      'response has body': (r) => r.body.length > 0,
      'response is JSON': (r) => r.headers['Content-Type']?.includes('application/json'),
    });
    
    if (!success) {
      errorRate.add(1);
    } else {
      errorRate.add(0);
    }
    
    // Parse response
    try {
      const body = JSON.parse(response.body);
      
      // Check if antifraud blocked
      if (body === null) {
        antifraudBlocks.add(1);
      }
      
      // Validate response structure
      if (body) {
        check(body, {
          'has tag_id': (b) => b.tag_id !== undefined,
          'has scan_count': (b) => typeof b.scan_count === 'number',
          'scan_count > 0': (b) => b.scan_count > 0,
        });
      }
    } catch (e) {
      console.error('Failed to parse response:', e);
      errorRate.add(1);
    }
  });
  
  // Think time (simulate user behavior)
  sleep(Math.random() * 2 + 1); // 1-3 seconds
}

// Helper: Generate random IP address
function generateRandomIP() {
  return `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
}

// Setup function (runs once at start)
export function setup() {
  console.log('🚀 Starting load test...');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Test duration: ~15 minutes`);
  
  // Warm-up request
  const response = http.get(`${BASE_URL}/v1/health`);
  
  if (response.status !== 200) {
    throw new Error('Service not healthy, aborting test');
  }
  
  return {
    startTime: new Date(),
  };
}

// Teardown function (runs once at end)
export function teardown(data) {
  const duration = (new Date() - data.startTime) / 1000;
  console.log(`✅ Load test completed in ${duration}s`);
}
