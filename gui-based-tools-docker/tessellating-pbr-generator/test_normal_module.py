"""Test script for the normal module implementation."""

from PIL import Image
import numpy as np
from src.modules.normal import NormalModule
from src.types.config import Config, TextureConfig, MaterialProperties, Resolution
from src.types.common import TextureType, TextureFormat


def create_test_config():
    """Create a test configuration."""
    return Config(
        project_name="test",
        project_version="1.0.0",
        texture_config=TextureConfig(
            resolution=Resolution(512, 512),
            format=TextureFormat.PNG,
            types=[TextureType.NORMAL],
            seamless=True
        ),
        material="stone",
        style="realistic",
        material_properties=MaterialProperties(
            normal_strength=1.0
        ),
        model="dalle-3",
        output_directory="output",
        naming_convention="{material}_{type}_{resolution}"
    )


def create_test_height_map(width=512, height=512):
    """Create a simple test height map with some patterns."""
    # Create a simple pattern - circular gradient
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    xx, yy = np.meshgrid(x, y)
    
    # Distance from center
    distance = np.sqrt(xx**2 + yy**2)
    
    # Create height pattern (inverted so center is high)
    height_map = 1.0 - np.clip(distance, 0, 1)
    
    # Add some noise
    noise = np.random.randn(height, width) * 0.05
    height_map += noise
    height_map = np.clip(height_map, 0, 1)
    
    return height_map


def main():
    """Test the normal module."""
    print("Testing Normal Module...")
    
    # Create config
    config = create_test_config()
    
    # Create normal module
    normal_module = NormalModule(config)
    
    # Test 1: Generate from height map
    print("\nTest 1: Generate normal map from height data")
    height_map = create_test_height_map()
    
    normal_map = normal_module.generate({
        "height_map": height_map
    })
    
    normal_map.save("/workspace/ext/tessellating-pbr-generator/output/test_normal_from_height.png")
    print(f"✓ Saved normal map from height: {normal_map.size}, mode: {normal_map.mode}")
    
    # Test 2: Generate neutral normal map
    print("\nTest 2: Generate neutral normal map (no input)")
    neutral_normal = normal_module.generate()
    neutral_normal.save("/workspace/ext/tessellating-pbr-generator/output/test_normal_neutral.png")
    print(f"✓ Saved neutral normal map: {neutral_normal.size}, mode: {neutral_normal.mode}")
    
    # Test 3: Test with existing height image if available
    height_image_path = "/workspace/ext/tessellating-pbr-generator/output/stone_height_1024x1024.png"
    try:
        height_image = Image.open(height_image_path)
        print(f"\nTest 3: Generate normal map from existing height image")
        
        normal_from_image = normal_module.generate({
            "height_map": height_image
        })
        
        normal_from_image.save("/workspace/ext/tessellating-pbr-generator/output/test_normal_from_existing.png")
        print(f"✓ Saved normal map from existing height: {normal_from_image.size}, mode: {normal_from_image.mode}")
    except FileNotFoundError:
        print("\nTest 3: Skipped (no existing height map found)")
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()