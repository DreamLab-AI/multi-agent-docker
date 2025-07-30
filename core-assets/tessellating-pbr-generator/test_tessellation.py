"""Test script for the tessellation module."""

import os
from PIL import Image
import numpy as np

# Import the tessellation module directly to avoid import issues
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'modules'))
from tessellation import TessellationModule


def create_tiling_visualization(original: Image.Image, seamless: Image.Image, 
                               tiles: int = 2) -> Image.Image:
    """Create a visualization showing the tiled result."""
    w, h = original.size
    
    # Create output image that shows 2x2 tiles
    output = Image.new(original.mode, (w * tiles, h * tiles))
    
    # Tile the seamless image
    for y in range(tiles):
        for x in range(tiles):
            output.paste(seamless, (x * w, y * h))
    
    return output


def test_tessellation():
    """Test the tessellation module with various methods."""
    print("Testing Tessellation Module...")
    
    # Create tessellation module
    tess = TessellationModule()
    
    # Create test pattern
    print("\n1. Creating test pattern...")
    test_pattern = tess.create_test_pattern((512, 512))
    test_pattern.save("output/test_pattern_original.png")
    print("   Saved: output/test_pattern_original.png")
    
    # Test offset blend method
    print("\n2. Testing offset blend method...")
    seamless_offset = tess.make_seamless(test_pattern, blend_mode='offset')
    seamless_offset.save("output/test_pattern_seamless_offset.png")
    print("   Saved: output/test_pattern_seamless_offset.png")
    
    # Create tiled visualization
    tiled_offset = create_tiling_visualization(test_pattern, seamless_offset)
    tiled_offset.save("output/test_pattern_tiled_offset.png")
    print("   Saved: output/test_pattern_tiled_offset.png")
    
    # Validate tiling
    is_seamless, max_diff = tess.validate_tiling(seamless_offset)
    print(f"   Seamless validation: {is_seamless} (max edge diff: {max_diff:.4f})")
    
    # Test mirror blend method
    print("\n3. Testing mirror blend method...")
    seamless_mirror = tess.make_seamless(test_pattern, blend_mode='mirror')
    seamless_mirror.save("output/test_pattern_seamless_mirror.png")
    print("   Saved: output/test_pattern_seamless_mirror.png")
    
    tiled_mirror = create_tiling_visualization(test_pattern, seamless_mirror)
    tiled_mirror.save("output/test_pattern_tiled_mirror.png")
    print("   Saved: output/test_pattern_tiled_mirror.png")
    
    is_seamless, max_diff = tess.validate_tiling(seamless_mirror)
    print(f"   Seamless validation: {is_seamless} (max edge diff: {max_diff:.4f})")
    
    # Test frequency blend method
    print("\n4. Testing frequency blend method...")
    seamless_freq = tess.make_seamless(test_pattern, blend_mode='frequency')
    seamless_freq.save("output/test_pattern_seamless_frequency.png")
    print("   Saved: output/test_pattern_seamless_frequency.png")
    
    tiled_freq = create_tiling_visualization(test_pattern, seamless_freq)
    tiled_freq.save("output/test_pattern_tiled_frequency.png")
    print("   Saved: output/test_pattern_tiled_frequency.png")
    
    is_seamless, max_diff = tess.validate_tiling(seamless_freq)
    print(f"   Seamless validation: {is_seamless} (max edge diff: {max_diff:.4f})")
    
    # Test with existing texture if available
    existing_textures = [
        "output/stone_diffuse_1024x1024.png",
        "output/stone_height_1024x1024.png",
        "output/stone_roughness_1024x1024.png"
    ]
    
    for texture_path in existing_textures:
        if os.path.exists(texture_path):
            print(f"\n5. Testing with existing texture: {texture_path}")
            texture = Image.open(texture_path)
            
            # Resize to smaller for testing
            texture = texture.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Apply offset blend
            seamless = tess.make_seamless(texture, blend_mode='offset')
            
            # Save results
            base_name = os.path.basename(texture_path).replace('.png', '')
            seamless.save(f"output/{base_name}_seamless.png")
            print(f"   Saved: output/{base_name}_seamless.png")
            
            # Create tiled visualization
            tiled = create_tiling_visualization(texture, seamless)
            tiled.save(f"output/{base_name}_tiled.png")
            print(f"   Saved: output/{base_name}_tiled.png")
            
            # Validate
            is_seamless, max_diff = tess.validate_tiling(seamless)
            print(f"   Seamless validation: {is_seamless} (max edge diff: {max_diff:.4f})")
            
            break  # Just test one existing texture
    
    print("\n✅ Tessellation testing complete!")
    print("\nCheck the output/ directory for results:")
    print("- *_original.png: Original test pattern")
    print("- *_seamless_*.png: Seamless versions using different methods")
    print("- *_tiled_*.png: 2x2 tiled visualizations showing seamless tiling")


if __name__ == "__main__":
    test_tessellation()