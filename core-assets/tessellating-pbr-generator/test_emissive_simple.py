#!/usr/bin/env python3
"""Simple test to verify emissive module implementation."""

import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from PIL import Image
import numpy as np
from types.config import Config, TextureConfig, MaterialProperties
from types.common import Resolution
from modules.emissive import EmissiveModule


def test_basic_emissive():
    """Test basic emissive generation."""
    print("Testing basic emissive generation...")
    
    # Create config
    config = Config(
        material='neon',
        texture_config=TextureConfig(
            resolution=Resolution(256, 256),
            seamless=False
        ),
        material_properties=MaterialProperties(
            emission_intensity=2.0
        )
    )
    
    # Create module
    emissive = EmissiveModule(config)
    
    # Generate without input (procedural)
    result = emissive.generate()
    
    assert isinstance(result, Image.Image)
    assert result.size == (256, 256)
    assert result.mode == 'RGB'
    
    print("✓ Basic generation successful")
    return result


def test_emissive_with_diffuse():
    """Test emissive generation from diffuse input."""
    print("\nTesting emissive from diffuse...")
    
    # Create test diffuse with bright regions
    diffuse = Image.new('RGB', (256, 256), (20, 20, 20))
    pixels = diffuse.load()
    
    # Add bright neon-like text
    for x in range(50, 150):
        for y in range(50, 80):
            pixels[x, y] = (255, 0, 128)  # Pink neon
    
    for x in range(50, 150):
        for y in range(100, 130):
            pixels[x, y] = (0, 255, 255)  # Cyan neon
    
    # Create config
    config = Config(
        material='neon',
        texture_config=TextureConfig(
            resolution=Resolution(256, 256),
            seamless=False
        ),
        material_properties=MaterialProperties()
    )
    
    # Generate emissive
    emissive = EmissiveModule(config)
    result = emissive.generate({'diffuse_map': diffuse})
    
    # Check that bright areas are preserved
    result_array = np.array(result)
    assert np.max(result_array) > 200  # Should have bright areas
    
    print("✓ Diffuse-based generation successful")
    return result


def test_material_presets():
    """Test different material presets."""
    print("\nTesting material presets...")
    
    materials = ['led', 'lava', 'plasma', 'fire', 'electric', 'bioluminescent']
    results = {}
    
    for material in materials:
        config = Config(
            material=material,
            texture_config=TextureConfig(
                resolution=Resolution(256, 256),
                seamless=True
            ),
            material_properties=MaterialProperties()
        )
        
        emissive = EmissiveModule(config)
        result = emissive.generate()
        
        assert result is not None
        results[material] = result
        print(f"✓ {material} preset generated")
    
    return results


if __name__ == '__main__':
    print("Testing Emissive Module Implementation")
    print("=" * 40)
    
    try:
        # Run tests
        basic = test_basic_emissive()
        basic.save('test_output/emissive_basic.png')
        
        diffuse_based = test_emissive_with_diffuse()
        diffuse_based.save('test_output/emissive_from_diffuse.png')
        
        presets = test_material_presets()
        for material, img in presets.items():
            img.save(f'test_output/emissive_{material}_preset.png')
        
        print("\n✅ All tests passed!")
        print(f"Generated {len(presets) + 2} test images in test_output/")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)