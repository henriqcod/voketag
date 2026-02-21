import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

/**
 * LOW ENHANCEMENT: Load testing for Factory API
 * 
 * Tests authenticated API endpoints under load:
 * - Product listing
 * - Product creation
 * - Batch management
 * - CSV upload simulation
 */

// Custom metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');

export const options = {
  stages: [
    { duration: '1m', target: 20 },
    { duration: '3m', target: 20 },
    { duration: '1m', target: 0 },
  ],
  
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
    errors: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://api.voketag.com';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'test_jwt_token';

export default function () {
  const headers = {
    'Authorization': `Bearer ${AUTH_TOKEN}`,
    'Content-Type': 'application/json',
  };
  
  group('Product Operations', () => {
    // List products
    const listResponse = http.get(`${BASE_URL}/v1/products?limit=10`, {
      headers,
      tags: { name: 'list_products' },
    });
    
    check(listResponse, {
      'list status 200': (r) => r.status === 200,
      'list has products': (r) => JSON.parse(r.body).length > 0,
    });
    
    sleep(1);
    
    // Create product
    const productData = {
      name: `Load Test Product ${Date.now()}`,
      sku: `LOAD-TEST-${Date.now()}`,
      description: 'Created by load test',
    };
    
    const createResponse = http.post(
      `${BASE_URL}/v1/products`,
      JSON.stringify(productData),
      {
        headers,
        tags: { name: 'create_product' },
      }
    );
    
    const createSuccess = check(createResponse, {
      'create status 201': (r) => r.status === 201,
      'create has id': (r) => JSON.parse(r.body).id !== undefined,
    });
    
    if (!createSuccess) {
      errorRate.add(1);
    }
    
    sleep(1);
    
    // Get product by ID
    if (createResponse.status === 201) {
      const product = JSON.parse(createResponse.body);
      
      const getResponse = http.get(`${BASE_URL}/v1/products/${product.id}`, {
        headers,
        tags: { name: 'get_product' },
      });
      
      check(getResponse, {
        'get status 200': (r) => r.status === 200,
        'get has correct id': (r) => JSON.parse(r.body).id === product.id,
      });
    }
  });
  
  group('Batch Operations', () => {
    // List batches
    const listResponse = http.get(`${BASE_URL}/v1/batches?limit=10`, {
      headers,
      tags: { name: 'list_batches' },
    });
    
    check(listResponse, {
      'list batches 200': (r) => r.status === 200,
    });
    
    sleep(1);
  });
  
  // Think time
  sleep(Math.random() * 2 + 1);
}

export function setup() {
  console.log('🚀 Starting Factory API load test...');
  
  // Verify authentication
  const response = http.get(`${BASE_URL}/v1/products?limit=1`, {
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  });
  
  if (response.status === 401) {
    throw new Error('Authentication failed. Set AUTH_TOKEN environment variable.');
  }
  
  return { startTime: new Date() };
}

export function teardown(data) {
  const duration = (new Date() - data.startTime) / 1000;
  console.log(`✅ Factory API load test completed in ${duration}s`);
}
