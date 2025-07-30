# Test Execution Guide for Tessellating PBR Generator

## Quick Start

### Prerequisites
- Node.js 18.x or higher
- Python 3.9+ (for texture validation)
- OpenCV (for image analysis)
- Valid OpenAI API key for integration tests

### Installation
```bash
# Install dependencies
npm install

# Install Python dependencies for texture validation
pip install -r tests/requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libopencv-dev python3-opencv
```

## Running Tests

### All Tests
```bash
npm test
```

### Unit Tests Only
```bash
npm run test:unit

# With coverage
npm run test:unit:coverage

# Watch mode
npm run test:unit:watch
```

### Integration Tests
```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY=your-test-key
npm run test:integration

# With mock API
npm run test:integration:mock
```

### Texture Validation Tests
```bash
npm run test:texture-validation

# Specific material category
npm run test:texture-validation -- --category=concrete
```

### Performance Tests
```bash
npm run test:performance

# Stress test
npm run test:performance:stress

# Memory leak detection
npm run test:performance:memory
```

### Visual Regression Tests
```bash
# Requires Percy token
export PERCY_TOKEN=your-percy-token
npm run test:visual
```

## Test Categories Explained

### 1. Unit Tests
- **Location**: `tests/unit/`
- **Purpose**: Test individual functions and modules
- **Coverage Goal**: 95%+
- **Run Time**: < 30 seconds

Key test files:
- `prompt-generator.test.js` - Prompt building logic
- `texture-validator.test.js` - Texture validation algorithms
- `api-client.test.js` - OpenAI API wrapper
- `material-parser.test.js` - Materials.json parsing

### 2. Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test component interactions
- **Coverage Goal**: 80%+
- **Run Time**: 2-5 minutes

Key test files:
- `openai-integration.test.js` - Real API calls
- `file-system-integration.test.js` - File operations
- `end-to-end-generation.test.js` - Full workflow

### 3. Texture Validation Tests
- **Location**: `tests/texture-validation/`
- **Purpose**: Validate texture quality and tessellation
- **Success Criteria**: 100% seamless tiling
- **Run Time**: 1-2 minutes per material

Validation checks:
- Edge matching (< 2% deviation)
- Color consistency (< 5% variance)
- Pattern continuity (> 95% score)
- No visible artifacts

### 4. Performance Tests
- **Location**: `tests/performance/`
- **Purpose**: Ensure system performance
- **Targets**: < 30s generation, < 2GB memory
- **Run Time**: 10-15 minutes

Benchmarks:
- Single texture: < 15s
- Batch of 5: < 60s
- Memory per texture: < 200MB
- Concurrent limit: 3-5

### 5. Visual Regression Tests
- **Location**: `tests/visual-regression/`
- **Purpose**: Detect visual changes
- **Tool**: Percy.io
- **Run Time**: 5-10 minutes

## Test Data and Fixtures

### Material Fixtures
Located in `tests/fixtures/material-fixtures.json`:
- 4 concrete materials
- 3 brick materials
- 4 stone materials
- 4 aluminum materials

### Mock API Responses
Located in `tests/fixtures/mock-api-responses.json`:
- Success responses
- Error responses (rate limit, auth, server)
- Retry scenarios

### Test Images
Located in `tests/fixtures/images/`:
- `perfect-seamless.png` - Ideal tessellation
- `visible-seams.png` - Failed tessellation
- `texture-with-artifacts.png` - Quality issues

## Debugging Failed Tests

### Common Issues

#### 1. API Key Issues
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Use test key for CI
export OPENAI_API_KEY=test-key-123
```

#### 2. Timeout Errors
```javascript
// Increase timeout in jest.config.js
testTimeout: 60000 // 60 seconds
```

#### 3. Memory Issues
```bash
# Run with increased memory
NODE_OPTIONS="--max-old-space-size=4096" npm test
```

#### 4. Image Processing Errors
```bash
# Verify OpenCV installation
python -c "import cv2; print(cv2.__version__)"
```

### Debug Mode
```bash
# Run with debug output
DEBUG=* npm test

# Specific module debug
DEBUG=texture-validator npm test

# Verbose Jest output
npm test -- --verbose
```

## CI/CD Integration

### GitHub Actions
Tests run automatically on:
- Push to main/develop
- Pull requests
- Nightly schedule (2 AM UTC)

### Local CI Simulation
```bash
# Run tests as CI would
CI=true npm test

# Full CI pipeline locally
npm run ci:local
```

## Test Reports

### Coverage Reports
- HTML: `coverage/index.html`
- LCOV: `coverage/lcov.info`
- Console: Run with `--coverage`

### Performance Reports
- JSON: `test-results/performance.json`
- HTML: `test-results/performance.html`
- Benchmarks: `test-results/benchmarks.json`

### Visual Diffs
- Percy dashboard: https://percy.io/your-project
- Local diffs: `test-results/visual-diffs/`

## Troubleshooting

### Test Hanging
1. Check for unresolved promises
2. Verify mock cleanup
3. Use `--detectOpenHandles`

### Flaky Tests
1. Check for race conditions
2. Add proper timeouts
3. Use `waitFor` utilities
4. Mock external dependencies

### Memory Leaks
1. Run memory profiler
2. Check for circular references
3. Verify cleanup in afterEach
4. Use weak references where appropriate

## Best Practices

### Writing New Tests
1. Follow AAA pattern (Arrange, Act, Assert)
2. Use descriptive test names
3. One assertion per test (when possible)
4. Mock external dependencies
5. Clean up after tests

### Test Organization
```javascript
describe('Component Name', () => {
  describe('Method Name', () => {
    it('should do specific thing when condition', () => {
      // Test implementation
    });
  });
});
```

### Performance Considerations
- Use `beforeAll` for expensive setup
- Parallelize independent tests
- Mock heavy operations
- Use test data factories

## Continuous Improvement

### Monthly Review
- Analyze test execution times
- Review flaky test patterns
- Update performance baselines
- Refactor slow tests

### Metrics to Track
- Test execution time
- Flakiness rate
- Coverage trends
- Performance regression

## Support

For test-related issues:
1. Check this guide first
2. Review test output carefully
3. Search existing issues
4. Create detailed bug report

Remember: Good tests are the foundation of reliable software!