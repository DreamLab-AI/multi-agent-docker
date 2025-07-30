# OpenAI API Integration Test Plan

## Overview
This document outlines the integration testing approach for the OpenAI API components of the tessellating texture generator.

## Test Environment Setup

### Prerequisites
- OpenAI API test key (with limited quota)
- Mock server for API simulation
- Network traffic interceptor for request validation
- Image analysis tools for output validation

## Test Scenarios

### 1. Basic API Connection Tests

#### Test 1.1: Valid API Key Authentication
```javascript
test('should authenticate with valid API key', async () => {
  const client = new OpenAIClient(process.env.OPENAI_TEST_KEY);
  const result = await client.testConnection();
  expect(result.authenticated).toBe(true);
});
```

#### Test 1.2: Invalid API Key Handling
```javascript
test('should handle invalid API key gracefully', async () => {
  const client = new OpenAIClient('invalid-key');
  await expect(client.testConnection()).rejects.toThrow('Invalid API key');
});
```

### 2. Texture Generation Tests

#### Test 2.1: Single Texture Generation
```javascript
test('should generate single texture successfully', async () => {
  const material = fixtures.materials.concrete[0];
  const result = await generator.generateTexture(material);
  
  expect(result).toHaveProperty('url');
  expect(result).toHaveProperty('metadata');
  expect(result.metadata.tessellates).toBe(true);
});
```

#### Test 2.2: Batch Generation with Concurrency
```javascript
test('should handle concurrent batch generation', async () => {
  const materials = fixtures.materials.brick.slice(0, 3);
  const results = await generator.generateBatch(materials, {
    maxConcurrent: 3
  });
  
  expect(results).toHaveLength(3);
  results.forEach(result => {
    expect(result.status).toBe('success');
  });
});
```

### 3. Error Handling and Retry Logic

#### Test 3.1: Rate Limit Handling
```javascript
test('should handle rate limits with exponential backoff', async () => {
  // Mock rate limit response
  mockAPI.onNext().replyWithError(429);
  mockAPI.onNext().replyWithSuccess();
  
  const result = await generator.generateWithRetry(material);
  expect(result.retryCount).toBe(1);
  expect(result.success).toBe(true);
});
```

#### Test 3.2: Network Failure Recovery
```javascript
test('should recover from network failures', async () => {
  // Simulate network timeout
  mockAPI.onNext().timeout();
  mockAPI.onNext().replyWithSuccess();
  
  const result = await generator.generateWithRetry(material);
  expect(result.success).toBe(true);
});
```

### 4. Prompt Optimization Tests

#### Test 4.1: Prompt Length Validation
```javascript
test('should optimize prompts within API limits', async () => {
  const longDescription = 'a'.repeat(2000);
  const material = { ...fixtures.materials.stone[0], description: longDescription };
  
  const prompt = generator.buildPrompt(material);
  expect(prompt.length).toBeLessThan(1000);
  expect(prompt).toContain('seamless');
  expect(prompt).toContain('tileable');
});
```

#### Test 4.2: Tessellation Keywords
```javascript
test('should include tessellation keywords in prompts', async () => {
  const prompt = generator.buildPrompt(fixtures.materials.aluminum[0]);
  
  const keywords = ['seamless', 'tileable', 'repeating', 'no visible seams'];
  keywords.forEach(keyword => {
    expect(prompt.toLowerCase()).toContain(keyword);
  });
});
```

### 5. Response Validation Tests

#### Test 5.1: Image URL Validation
```javascript
test('should validate generated image URLs', async () => {
  const result = await generator.generateTexture(material);
  
  expect(result.url).toMatch(/^https:\/\/.+\.(png|jpg|jpeg)$/);
  expect(await validateImageURL(result.url)).toBe(true);
});
```

#### Test 5.2: Metadata Extraction
```javascript
test('should extract and store generation metadata', async () => {
  const result = await generator.generateTexture(material);
  
  expect(result.metadata).toMatchObject({
    materialId: material.id,
    generatedAt: expect.any(Date),
    prompt: expect.any(String),
    modelVersion: expect.any(String)
  });
});
```

### 6. Performance and Load Tests

#### Test 6.1: Response Time Monitoring
```javascript
test('should generate textures within acceptable time', async () => {
  const startTime = Date.now();
  const result = await generator.generateTexture(material);
  const duration = Date.now() - startTime;
  
  expect(duration).toBeLessThan(30000); // 30 seconds
  expect(result.success).toBe(true);
});
```

#### Test 6.2: Memory Usage
```javascript
test('should not exceed memory limits during batch generation', async () => {
  const initialMemory = process.memoryUsage().heapUsed;
  
  await generator.generateBatch(fixtures.materials.concrete);
  
  const finalMemory = process.memoryUsage().heapUsed;
  const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024; // MB
  
  expect(memoryIncrease).toBeLessThan(500); // 500MB limit
});
```

### 7. Edge Case Tests

#### Test 7.1: Empty Material Properties
```javascript
test('should handle materials with minimal properties', async () => {
  const minimalMaterial = { id: 'test', category: 'stone' };
  const result = await generator.generateTexture(minimalMaterial);
  
  expect(result.success).toBe(true);
  expect(result.url).toBeDefined();
});
```

#### Test 7.2: Special Characters in Prompts
```javascript
test('should sanitize special characters in prompts', async () => {
  const material = {
    ...fixtures.materials.brick[0],
    name: 'Brick with <script>alert()</script> tags'
  };
  
  const prompt = generator.buildPrompt(material);
  expect(prompt).not.toContain('<script>');
  expect(prompt).not.toContain('</script>');
});
```

## Mock Strategies

### API Response Mocking
```javascript
const mockAPI = {
  success: (data) => ({
    status: 200,
    body: fixtures.apiResponses.success_responses.texture_generation
  }),
  
  rateLimit: () => ({
    status: 429,
    body: fixtures.apiResponses.error_responses.rate_limit
  }),
  
  serverError: () => ({
    status: 500,
    body: fixtures.apiResponses.error_responses.server_error
  })
};
```

### Network Simulation
```javascript
const networkConditions = {
  fast: { latency: 50, bandwidth: 10000 },
  slow: { latency: 2000, bandwidth: 500 },
  offline: { latency: Infinity, bandwidth: 0 }
};
```

## Continuous Integration Setup

### GitHub Actions Workflow
```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
      - name: Install dependencies
        run: npm install
      - name: Run integration tests
        env:
          OPENAI_TEST_KEY: ${{ secrets.OPENAI_TEST_KEY }}
        run: npm run test:integration
```

## Success Metrics

### Test Coverage Goals
- API Client: 95% coverage
- Error Handling: 100% coverage
- Retry Logic: 100% coverage
- Prompt Building: 90% coverage

### Performance Targets
- Average generation time: < 15 seconds
- Success rate: > 95%
- Retry success rate: > 99%
- Memory efficiency: < 500MB per batch

## Monitoring and Reporting

### Test Results Dashboard
- Real-time test execution status
- Historical pass/fail trends
- Performance metrics over time
- API usage tracking

### Alert Conditions
- Test failure rate > 5%
- Response time > 30 seconds
- Memory usage > 1GB
- API errors > 10 per hour