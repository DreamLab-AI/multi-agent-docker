"""
Quick test to verify the test suite is properly configured.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """Test that all modules can be imported."""
    # Test main module imports
    from src.generator import PBRGenerator
    from src.texture_maps.normal_map import NormalMapGenerator
    from src.texture_maps.roughness_map import RoughnessMapGenerator
    from src.texture_maps.height_map import HeightMapGenerator
    from src.texture_maps.ao_map import AOMapGenerator
    from src.texture_maps.metallic_map import MetallicMapGenerator
    from src.tessellation.seamless_tiling import SeamlessTiling
    
    assert PBRGenerator is not None
    assert NormalMapGenerator is not None


def test_fixtures(sample_image, temp_dir, material_config):
    """Test that fixtures are working correctly."""
    assert sample_image is not None
    assert sample_image.size == (256, 256)
    
    assert os.path.exists(temp_dir)
    assert os.path.isdir(temp_dir)
    
    assert isinstance(material_config, dict)
    assert 'properties' in material_config


def test_environment():
    """Test that environment is properly configured."""
    # Check Python version
    assert sys.version_info >= (3, 8)
    
    # Check that we can import required packages
    import PIL
    import numpy
    import openai
    
    assert PIL is not None
    assert numpy is not None
    assert openai is not None


@pytest.mark.parametrize("value,expected", [
    (0, 0),
    (255, 255),
    (128, 128),
])
def test_parametrized(value, expected):
    """Test parametrized test functionality."""
    assert value == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])