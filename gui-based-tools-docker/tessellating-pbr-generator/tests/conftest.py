"""
Pytest configuration and fixtures for PBR generator tests.
"""

import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from unittest.mock import Mock, patch
import json


@pytest.fixture
def sample_image():
    """Create a sample RGB image for testing."""
    # Create a 256x256 test image with some patterns
    width, height = 256, 256
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add some patterns for testing
    # Gradient in red channel
    for y in range(height):
        image[y, :, 0] = int(255 * y / height)
    
    # Stripes in green channel
    for x in range(0, width, 32):
        image[:, x:x+16, 1] = 255
    
    # Noise in blue channel
    np.random.seed(42)
    image[:, :, 2] = np.random.randint(0, 256, (height, width))
    
    return Image.fromarray(image)


@pytest.fixture
def grayscale_image():
    """Create a sample grayscale image for testing."""
    width, height = 256, 256
    # Create gradient pattern
    gradient = np.zeros((height, width), dtype=np.uint8)
    for y in range(height):
        gradient[y, :] = int(255 * y / height)
    
    return Image.fromarray(gradient, mode='L')


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def material_config():
    """Sample material configuration."""
    return {
        "type": "metal",
        "properties": {
            "roughness": 0.3,
            "metallic": 0.9,
            "height_scale": 0.02,
            "ao_intensity": 0.8
        }
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('openai.OpenAI') as mock:
        client = Mock()
        mock.return_value = client
        
        # Mock image generation response
        mock_response = Mock()
        mock_response.data = [Mock(url="https://mock-url.com/image.png")]
        client.images.generate.return_value = mock_response
        
        yield client


@pytest.fixture
def mock_image_download():
    """Mock image download from URL."""
    def _mock_download(url):
        # Return our sample image for any URL
        width, height = 512, 512
        image = np.zeros((height, width, 3), dtype=np.uint8)
        # Create a simple pattern
        image[:256, :256] = [255, 0, 0]    # Red
        image[:256, 256:] = [0, 255, 0]    # Green
        image[256:, :256] = [0, 0, 255]    # Blue
        image[256:, 256:] = [255, 255, 0]  # Yellow
        return Image.fromarray(image)
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b'fake-image-data'
        mock_get.return_value = mock_response
        
        with patch('PIL.Image.open', side_effect=lambda x: _mock_download(None)):
            yield _mock_download


@pytest.fixture
def test_config_path(temp_dir):
    """Create a test configuration file."""
    config = {
        "materials": {
            "stone": {
                "properties": {
                    "roughness": 0.8,
                    "metallic": 0.0,
                    "height_scale": 0.05,
                    "ao_intensity": 0.7
                }
            },
            "metal": {
                "properties": {
                    "roughness": 0.2,
                    "metallic": 1.0,
                    "height_scale": 0.01,
                    "ao_intensity": 0.5
                }
            }
        },
        "generation": {
            "default_size": 512,
            "quality": "high"
        }
    }
    
    config_path = os.path.join(temp_dir, 'test_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    return config_path


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset any singleton instances between tests."""
    # If we have any singleton patterns, reset them here
    yield
    # Cleanup code here if needed


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for different scenarios."""
    def _mock_response(scenario='success'):
        if scenario == 'success':
            return Mock(
                data=[Mock(
                    url="https://mock-url.com/generated-image.png",
                    revised_prompt="A detailed PBR texture..."
                )]
            )
        elif scenario == 'error':
            raise Exception("OpenAI API Error")
        elif scenario == 'rate_limit':
            from openai import RateLimitError
            raise RateLimitError("Rate limit exceeded")
        elif scenario == 'timeout':
            import time
            time.sleep(5)
            return _mock_response('success')
    
    return _mock_response


@pytest.fixture
def sample_material_types():
    """Sample material type configurations for testing."""
    return {
        'metal': {
            'roughness': 0.2,
            'metallic': 1.0,
            'base_color': [0.8, 0.8, 0.8],
            'height_scale': 0.01
        },
        'wood': {
            'roughness': 0.7,
            'metallic': 0.0,
            'base_color': [0.4, 0.2, 0.1],
            'height_scale': 0.02
        },
        'stone': {
            'roughness': 0.9,
            'metallic': 0.0,
            'base_color': [0.5, 0.5, 0.5],
            'height_scale': 0.05
        },
        'plastic': {
            'roughness': 0.4,
            'metallic': 0.0,
            'base_color': [0.1, 0.3, 0.8],
            'height_scale': 0.005
        }
    }


@pytest.fixture
def sample_texture_suite():
    """Create a complete suite of test textures."""
    textures = {}
    size = (512, 512)
    
    # Diffuse/Albedo
    diffuse = np.random.randint(50, 200, (*size, 3), dtype=np.uint8)
    textures['diffuse'] = Image.fromarray(diffuse)
    
    # Normal map (blue-ish with variations)
    normal = np.ones((*size, 3), dtype=np.uint8) * 128
    normal[:, :, 2] = 255  # Blue channel dominant
    # Add some variation
    normal[:, :, 0] = np.random.randint(100, 155, size, dtype=np.uint8)
    normal[:, :, 1] = np.random.randint(100, 155, size, dtype=np.uint8)
    textures['normal'] = Image.fromarray(normal)
    
    # Roughness (grayscale)
    roughness = np.random.randint(50, 200, size, dtype=np.uint8)
    textures['roughness'] = Image.fromarray(roughness, mode='L')
    
    # Metallic (mostly dark with some bright spots)
    metallic = np.zeros(size, dtype=np.uint8)
    metallic[100:150, 100:150] = 255  # Metallic region
    textures['metallic'] = Image.fromarray(metallic, mode='L')
    
    # Height/Displacement
    height = np.zeros(size, dtype=np.uint8)
    for i in range(0, size[0], 50):
        height[i:i+25, :] = 128
    textures['height'] = Image.fromarray(height, mode='L')
    
    # Ambient Occlusion
    ao = np.ones(size, dtype=np.uint8) * 200
    # Add some darker areas
    ao[200:300, 200:300] = 100
    textures['ao'] = Image.fromarray(ao, mode='L')
    
    # Emissive (mostly black with some bright areas)
    emissive = np.zeros((*size, 3), dtype=np.uint8)
    emissive[400:450, 400:450] = [255, 200, 100]  # Glowing region
    textures['emissive'] = Image.fromarray(emissive)
    
    return textures


@pytest.fixture
def mock_pipeline_config():
    """Mock configuration for full pipeline testing."""
    return {
        "project": {
            "name": "test-pipeline",
            "version": "1.0.0"
        },
        "textures": {
            "resolution": {"width": 512, "height": 512},
            "format": "png",
            "types": ["diffuse", "normal", "roughness", "metallic", "ao", "height", "emissive"]
        },
        "material": {
            "base_material": "metal",
            "seamless": True,
            "properties": {
                "age": 5,
                "wear": 0.3
            }
        },
        "generation": {
            "model": "dall-e-3",
            "parallel": True,
            "batch_size": 4
        },
        "output": {
            "directory": "./test_output",
            "naming_convention": "{material}_{type}_{timestamp}"
        }
    }


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    import psutil
    import os
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.metrics = {}
        
        def start(self):
            self.start_time = time.time()
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def stop(self, test_name):
            if self.start_time is None:
                return
            
            elapsed = time.time() - self.start_time
            process = psutil.Process(os.getpid())
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = end_memory - self.start_memory
            
            self.metrics[test_name] = {
                'duration': elapsed,
                'memory_used': memory_used,
                'timestamp': time.time()
            }
            
            return self.metrics[test_name]
        
        def get_report(self):
            return self.metrics
    
    return PerformanceMonitor()


@pytest.fixture
def ci_cd_mock_responses():
    """Mock responses specifically for CI/CD testing without real API calls."""
    return {
        'openai_generate': {
            'url': 'https://ci-mock.com/texture.png',
            'revised_prompt': 'CI/CD test texture generation'
        },
        'image_data': {
            'diffuse': np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8),
            'normal': np.ones((512, 512, 3), dtype=np.uint8) * [128, 128, 255],
            'roughness': np.random.randint(100, 200, (512, 512), dtype=np.uint8),
            'metallic': np.zeros((512, 512), dtype=np.uint8),
            'height': np.random.randint(0, 256, (512, 512), dtype=np.uint8),
            'ao': np.ones((512, 512), dtype=np.uint8) * 200,
            'emissive': np.zeros((512, 512, 3), dtype=np.uint8)
        }
    }


@pytest.fixture
def edge_case_images():
    """Collection of edge case images for robust testing."""
    edge_cases = {}
    
    # Completely black image
    edge_cases['black'] = Image.new('RGB', (256, 256), (0, 0, 0))
    
    # Completely white image
    edge_cases['white'] = Image.new('RGB', (256, 256), (255, 255, 255))
    
    # Single pixel image
    edge_cases['single_pixel'] = Image.new('RGB', (1, 1), (128, 128, 128))
    
    # Very small image
    edge_cases['tiny'] = Image.new('RGB', (8, 8), (100, 100, 100))
    
    # Non-square image
    edge_cases['wide'] = Image.new('RGB', (512, 128), (150, 150, 150))
    edge_cases['tall'] = Image.new('RGB', (128, 512), (150, 150, 150))
    
    # High dynamic range simulation (values will be clipped)
    hdr_data = np.random.normal(128, 100, (256, 256, 3))
    hdr_data = np.clip(hdr_data, 0, 255).astype(np.uint8)
    edge_cases['hdr_sim'] = Image.fromarray(hdr_data)
    
    # Transparent image
    transparent = np.zeros((256, 256, 4), dtype=np.uint8)
    transparent[:, :, 3] = np.random.randint(0, 256, (256, 256))
    edge_cases['transparent'] = Image.fromarray(transparent, mode='RGBA')
    
    return edge_cases