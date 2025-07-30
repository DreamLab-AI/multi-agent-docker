# PBR Texture Generator - Test Suite Documentation

## Overview

This test suite provides comprehensive coverage for the tessellating PBR texture generator, including unit tests, integration tests, and performance benchmarks.

## Test Structure

```
tests/
├── conftest.py          # Shared pytest fixtures and configuration
├── unit/                # Unit tests for individual modules
│   ├── test_emissive.py        # Emissive module tests
│   ├── test_config_advanced.py # Advanced configuration tests
│   ├── test_tessellation_default.py # Tessellation defaults tests
│   ├── test_generator.py       # Core generator tests
│   ├── test_modules.py         # Texture module tests
│   └── test_tessellation.py    # Basic tessellation tests
├── integration/         # Integration tests
│   ├── test_pipeline.py        # Pipeline integration tests
│   └── test_full_pipeline.py   # Comprehensive workflow tests
└── qa/                  # Quality assurance tests
    └── test_comprehensive.py   # Full system tests
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Types
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Using the test runner script
python run_tests.py --unit
python run_tests.py --integration
```

### Run Tests in Parallel
```bash
pytest -n auto  # Uses all available CPU cores
python run_tests.py --parallel 4  # Use 4 cores
```

## Test Features

### Mocked OpenAI API
All tests mock the OpenAI API to avoid costs:
- `mock_openai_client` fixture provides a mocked client
- `mock_image_download` simulates image downloads
- No actual API calls are made during testing

### Key Fixtures

1. **sample_image**: 256x256 RGB test image with patterns
2. **grayscale_image**: 256x256 grayscale gradient image
3. **temp_dir**: Temporary directory for test outputs
4. **material_config**: Sample material configuration
5. **test_config_path**: Creates a test configuration file

### Test Coverage

The test suite covers:

- **Unit Tests**:
  - Normal map generation (Sobel filters, edge detection)
  - Roughness map generation (config integration, variation)
  - Height map generation (luminance conversion)
  - Ambient occlusion simulation
  - Metallic map generation (auto-detection)
  - Main generator class (API mocking, config loading)
  - Seamless tiling algorithm

- **Integration Tests**:
  - Complete material generation pipeline
  - Tessellation with generated textures
  - Material consistency checks
  - Configuration-driven generation
  - Error handling and recovery
  - Output organization
  - Performance and memory usage

### Writing New Tests

1. Add unit tests to `tests/unit/`
2. Add integration tests to `tests/integration/`
3. Use provided fixtures for common operations
4. Always mock external API calls
5. Follow existing test patterns

### Test Configuration

See `pytest.ini` for test configuration options:
- Minimum coverage: 80%
- Test discovery patterns
- Coverage reporting
- Logging configuration

## Test Categories

### Unit Tests

Unit tests focus on individual components in isolation:

- **test_emissive.py**: Tests for the emissive texture generation module
  - Emissive map generation from RGB inputs
  - Color temperature mapping
  - Bloom effect application
  - HDR output support

- **test_config_advanced.py**: Advanced configuration parsing tests
  - Schema validation
  - Nested configuration access
  - Environment variable handling
  - Material presets
  - Multi-resolution configurations

- **test_tessellation_default.py**: Tessellation frequency default tests
  - Automatic blend width calculation
  - Different blend mode defaults
  - Edge case handling
  - Performance with large images

### Integration Tests

Integration tests verify component interactions:

- **test_full_pipeline.py**: Complete workflow testing
  - End-to-end PBR generation
  - Seamless texture pipeline
  - Parallel processing
  - Error recovery
  - Multi-resolution output

### Mock Responses for CI/CD

The test suite includes comprehensive mocking for CI/CD environments:

```python
# Example mock OpenAI response
@pytest.fixture
def mock_openai_response():
    def _mock_response(scenario='success'):
        if scenario == 'success':
            return Mock(
                data=[Mock(
                    url="https://mock-url.com/generated-image.png",
                    revised_prompt="A detailed PBR texture..."
                )]
            )
    return _mock_response
```

## Enhanced Fixtures

Key fixtures available in `conftest.py`:

- `sample_image`: RGB test image with patterns
- `grayscale_image`: Grayscale gradient image
- `mock_openai_client`: Mocked OpenAI API client
- `sample_texture_suite`: Complete set of PBR textures
- `ci_cd_mock_responses`: Pre-defined responses for CI testing
- `performance_monitor`: Performance tracking utility
- `edge_case_images`: Collection of edge case test images
- `mock_openai_response`: Flexible mock response generator
- `sample_material_types`: Material configurations for testing

## Coverage Requirements

- Minimum coverage threshold: 80%
- Coverage reports generated in `htmlcov/`
- XML reports for CI integration

## CI/CD Integration

### GitHub Actions Workflow

The project includes a comprehensive GitHub Actions workflow (`.github/workflows/test.yml`):

- Multi-OS testing (Ubuntu, Windows, macOS)
- Python version matrix (3.8 - 3.11)
- Automated linting and type checking
- Coverage reporting to Codecov
- Performance benchmark tracking

### Running in CI Mode

```bash
# Set CI environment variable
export CI=true
export OPENAI_API_KEY=test-key-for-ci

# Run tests with CI configuration
python run_tests.py --ci --coverage
```

## Using the Test Runner Script

The `run_tests.py` script provides enhanced test execution:

```bash
# Run unit tests with coverage
python run_tests.py --unit --coverage

# Run integration tests in CI mode
python run_tests.py --integration --ci

# Run tests in parallel
python run_tests.py --parallel 4

# Run performance benchmarks
python run_tests.py --benchmark

# Run specific test file
python run_tests.py tests/unit/test_emissive.py

# Run with custom pytest arguments
python run_tests.py -- -k "test_frequency_blend"
```

## Writing New Tests

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<specific_behavior>`

### Example Test Structure

```python
class TestEmissiveModule:
    @pytest.fixture
    def emissive_module(self):
        return EmissiveModule()
    
    def test_generate_emissive_map(self, emissive_module, sample_image):
        # Arrange
        intensity = 1.0
        
        # Act
        result = emissive_module.generate(sample_image, intensity=intensity)
        
        # Assert
        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size
```

### Marking Tests

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_component_interaction():
    pass

@pytest.mark.slow
def test_performance_intensive():
    pass

@pytest.mark.requires_api
def test_external_api_call():
    pass

@pytest.mark.ci
def test_ci_appropriate():
    pass
```

## Performance Testing

Run performance benchmarks:

```bash
python run_tests.py --benchmark
```

Benchmarks test:
- Texture generation speed
- Tessellation algorithm performance
- Memory usage during processing
- Parallel processing efficiency

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Install dev requirements
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **API key errors in tests**: Tests should use mocked responses
   ```bash
   python run_tests.py --ci  # Uses mocked API
   ```

3. **Coverage failures**: Check untested code paths
   ```bash
   coverage report -m  # Show missing lines
   ```

4. **Import errors**: Ensure PYTHONPATH includes src
   ```bash
   export PYTHONPATH=$PYTHONPATH:./src
   ```

## Contributing Tests

When adding new features:

1. Write unit tests for new modules
2. Add integration tests for workflows
3. Include fixtures for test data
4. Update CI configuration if needed
5. Ensure tests pass in CI mode
6. Maintain or improve coverage

## Test Maintenance

- Review and update tests when APIs change
- Keep mock responses current
- Update fixtures for new requirements
- Monitor test execution time
- Refactor slow tests for efficiency

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:
- No external dependencies required
- All API calls are mocked
- Deterministic results
- Fast execution with parallel support
- Comprehensive GitHub Actions workflow
- Multi-platform and multi-version testing