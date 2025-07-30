"""Test the roughness module implementation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PIL import Image
import numpy as np
from modules.roughness import RoughnessModule


def test_roughness_generation():
    """Test basic roughness map generation."""
    # Create a simple test diffuse image
    width, height = 256, 256
    test_image = Image.new('RGB', (width, height))
    
    # Create a gradient pattern for testing
    pixels = []
    for y in range(height):
        for x in range(width):
            # Create horizontal gradient
            value = int((x / width) * 255)
            pixels.append((value, value, value))
    
    test_image.putdata(pixels)
    
    # Test with different materials
    materials = ['stone', 'metal', 'wood', 'fabric']
    
    for material in materials:
        print(f"\nTesting {material} roughness generation...")
        
        # Create module with material preset
        module = RoughnessModule(
            roughness_range=(0.3, 0.8),
            material_type=material
        )
        
        # Generate roughness map
        roughness_map = module.generate(test_image)
        
        # Verify output
        assert roughness_map.mode == 'L', "Roughness map should be grayscale"
        assert roughness_map.size == (width, height), "Size should match input"
        
        # Check value range
        roughness_array = np.array(roughness_map) / 255.0
        min_val = roughness_array.min()
        max_val = roughness_array.max()
        
        print(f"  - Mode: {roughness_map.mode}")
        print(f"  - Size: {roughness_map.size}")
        print(f"  - Value range: [{min_val:.3f}, {max_val:.3f}]")
        
        # Save test output
        output_path = f"/workspace/ext/tessellating-pbr-generator/tests/test_roughness_{material}.png"
        roughness_map.save(output_path)
        print(f"  - Saved to: {output_path}")


def test_height_based_generation():
    """Test roughness generation from height map."""
    # Create a test height map with some variation
    width, height = 256, 256
    height_map = Image.new('L', (width, height))
    
    # Create a pattern with varying heights
    pixels = []
    for y in range(height):
        for x in range(width):
            # Create a wavy pattern
            value = int(128 + 100 * np.sin(x * 0.1) * np.sin(y * 0.1))
            pixels.append(value)
    
    height_map.putdata(pixels)
    
    print("\nTesting height-based roughness generation...")
    
    # Create module
    module = RoughnessModule(roughness_range=(0.2, 0.7))
    
    # Generate from height
    roughness_map = module.generate_from_height(height_map)
    
    # Verify output
    assert roughness_map.mode == 'L', "Roughness map should be grayscale"
    assert roughness_map.size == (width, height), "Size should match input"
    
    print(f"  - Mode: {roughness_map.mode}")
    print(f"  - Size: {roughness_map.size}")
    
    # Save test output
    output_path = "/workspace/ext/tessellating-pbr-generator/tests/test_roughness_from_height.png"
    roughness_map.save(output_path)
    print(f"  - Saved to: {output_path}")


if __name__ == "__main__":
    print("Testing Roughness Module Implementation")
    print("=" * 50)
    
    test_roughness_generation()
    test_height_based_generation()
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")