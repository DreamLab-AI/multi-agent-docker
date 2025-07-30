"""Offline test to verify module integration without OpenAI API."""

import asyncio
import os
from pathlib import Path
from PIL import Image
import numpy as np
from .types.config import Config, TextureConfig, MaterialProperties
from .types.common import TextureType, Resolution, TextureFormat
from .core.generator import _derive_pbr_maps, _get_texture_path


async def test_offline_pipeline():
    """Test the PBR derivation pipeline with a mock diffuse texture."""
    print("Testing Offline PBR Derivation Pipeline")
    print("=" * 50)
    
    # Create test configuration
    material_props = MaterialProperties(
        roughness_range=(0.3, 0.8),
        metallic_value=0.1,
        normal_strength=1.0,
        ao_intensity=0.8
    )
    
    # Create texture config
    texture_config = TextureConfig(
        resolution=Resolution(width=256, height=256),
        format=TextureFormat.PNG,
        types=[
            TextureType.NORMAL,
            TextureType.ROUGHNESS,
            TextureType.METALLIC,
            TextureType.AMBIENT_OCCLUSION,
            TextureType.HEIGHT
        ]
    )
    
    config = Config(
        project_name="Offline Test",
        project_version="1.0.0",
        texture_config=texture_config,
        material="test_material",
        style="test",
        material_properties=material_props,
        model="dall-e-3",
        output_directory="./test_offline_output",
        naming_convention="{material}_{type}_{resolution}",
        api_key="test-key"
    )
    
    # Create output directory
    Path(config.output_directory).mkdir(exist_ok=True)
    
    # Create a mock diffuse texture
    print("Creating mock diffuse texture...")
    mock_diffuse = create_mock_diffuse_texture(256, 256)
    mock_diffuse_path = Path(config.output_directory) / "mock_diffuse.png"
    mock_diffuse.save(str(mock_diffuse_path))
    print(f"Mock diffuse saved to: {mock_diffuse_path}")
    
    # Test the derivation pipeline
    print("\nTesting PBR map derivation...")
    try:
        results = await _derive_pbr_maps(str(mock_diffuse_path), config)
        
        print("\nResults:")
        print("-" * 50)
        
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.texture_type.value}:")
            print(f"  Success: {result.success}")
            if result.success:
                print(f"  File: {result.file_path}")
                print(f"  Time: {result.generation_time:.2f}s")
            else:
                print(f"  Error: {result.error_message}")
            print()
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total = len(results)
        print(f"Summary: {successful}/{total} PBR maps derived successfully")
        
        # Check if files were created
        if successful > 0:
            print("\nGenerated files:")
            for file in Path(config.output_directory).glob("*.png"):
                print(f"  - {file.name}")
        
    except Exception as e:
        print(f"Error during derivation: {e}")
        import traceback
        traceback.print_exc()


def create_mock_diffuse_texture(width: int, height: int) -> Image.Image:
    """Create a simple procedural texture for testing."""
    # Create a simple brick-like pattern
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create brick pattern
    brick_height = 32
    brick_width = 64
    mortar_width = 4
    
    # Base color
    brick_color = np.array([150, 80, 60])  # Reddish brown
    mortar_color = np.array([120, 120, 120])  # Gray
    
    # Fill with mortar
    img_array[:, :] = mortar_color
    
    # Draw bricks
    for y in range(0, height, brick_height + mortar_width):
        # Offset every other row
        offset = (brick_width // 2) if (y // (brick_height + mortar_width)) % 2 else 0
        
        for x in range(-brick_width + offset, width, brick_width + mortar_width):
            # Draw brick
            x1 = max(0, x)
            y1 = y
            x2 = min(width, x + brick_width)
            y2 = min(height, y + brick_height)
            
            if x1 < x2 and y1 < y2:
                # Add some variation
                variation = np.random.randint(-20, 20, size=3)
                color = np.clip(brick_color + variation, 0, 255)
                img_array[y1:y2, x1:x2] = color
    
    # Add some noise for texture
    noise = np.random.normal(0, 10, img_array.shape)
    img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)


def main():
    """Run the offline test."""
    asyncio.run(test_offline_pipeline())


if __name__ == "__main__":
    main()