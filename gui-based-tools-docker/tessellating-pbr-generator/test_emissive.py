#!/usr/bin/env python3
"""Test script for the emissive module implementation."""

import sys
from pathlib import Path
from PIL import Image
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from modules.emissive import EmissiveModule
from types.config import Config, TextureConfig, MaterialProperties
from types.common import Resolution


def create_test_diffuse(resolution: Resolution, pattern: str = 'neon') -> Image.Image:
    """Create a test diffuse texture with bright regions."""
    img = Image.new('RGB', (resolution.width, resolution.height), (20, 20, 20))
    
    if pattern == 'neon':
        # Create neon-like text pattern
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # Draw some bright text/shapes
        draw.rectangle([100, 100, 300, 200], fill=(255, 0, 128))
        draw.rectangle([350, 150, 450, 250], fill=(0, 255, 255))
        draw.ellipse([200, 300, 400, 500], fill=(255, 255, 0))
        
    elif pattern == 'lava':
        # Create lava-like pattern
        data = np.zeros((resolution.height, resolution.width, 3), dtype=np.uint8)
        # Create noise pattern
        y, x = np.ogrid[:resolution.height, :resolution.width]
        pattern = np.sin(x * 0.02) * np.cos(y * 0.02) + np.sin(x * 0.05) * np.cos(y * 0.03)
        pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min())
        # Apply heat colors
        data[:, :, 0] = (pattern * 255).astype(np.uint8)  # Red channel
        data[:, :, 1] = (pattern * 128).astype(np.uint8)  # Green channel
        img = Image.fromarray(data)
        
    return img


def test_emissive_materials():
    """Test various emissive material presets."""
    resolution = Resolution(512, 512)
    
    # Test materials
    test_materials = [
        ('neon', 'neon'),
        ('led', 'neon'),
        ('lava', 'lava'),
        ('screen', 'neon'),
        ('plasma', 'lava'),
        ('fire', 'lava'),
        ('crystal', 'neon'),
        ('radioactive', 'lava')
    ]
    
    for material, diffuse_pattern in test_materials:
        print(f"\nTesting {material} emissive pattern...")
        
        # Create config
        config = Config(
            material=material,
            texture_config=TextureConfig(
                resolution=resolution,
                seamless=False
            ),
            material_properties=MaterialProperties()
        )
        
        # Create module
        emissive = EmissiveModule(config)
        
        # Generate test diffuse
        diffuse_img = create_test_diffuse(resolution, diffuse_pattern)
        
        # Generate emissive map
        try:
            emissive_map = emissive.generate({
                'diffuse_map': diffuse_img
            })
            
            # Save result
            output_path = Path(f'test_output/emissive_{material}.png')
            output_path.parent.mkdir(exist_ok=True)
            emissive_map.save(output_path)
            print(f"  ✓ Saved to {output_path}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_procedural_emissive():
    """Test procedural emissive generation without input textures."""
    resolution = Resolution(512, 512)
    
    procedural_materials = ['led', 'plasma', 'electric', 'bioluminescent']
    
    for material in procedural_materials:
        print(f"\nTesting procedural {material} pattern...")
        
        config = Config(
            material=material,
            texture_config=TextureConfig(
                resolution=resolution,
                seamless=True  # Test seamless generation
            ),
            material_properties=MaterialProperties(
                emission_intensity=1.5
            )
        )
        
        emissive = EmissiveModule(config)
        
        try:
            # Generate without input data
            emissive_map = emissive.generate()
            
            output_path = Path(f'test_output/emissive_{material}_procedural.png')
            output_path.parent.mkdir(exist_ok=True)
            emissive_map.save(output_path)
            print(f"  ✓ Saved to {output_path}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


if __name__ == '__main__':
    print("Testing Emissive Module Implementation")
    print("=" * 40)
    
    test_emissive_materials()
    test_procedural_emissive()
    
    print("\n\nTest complete! Check test_output/ directory for generated emissive maps.")