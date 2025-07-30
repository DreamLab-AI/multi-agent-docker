"""Simple test for tessellation to debug the algorithm."""

import numpy as np
from PIL import Image
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'modules'))
from tessellation import TessellationModule


def create_simple_gradient():
    """Create a simple gradient pattern."""
    size = 256
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Create a radial gradient
    center = size // 2
    for y in range(size):
        for x in range(size):
            dist = np.sqrt((x - center)**2 + (y - center)**2)
            intensity = int(255 * (1 - dist / (size/2)))
            intensity = max(0, min(255, intensity))
            arr[y, x] = [intensity, intensity, intensity]
    
    return Image.fromarray(arr, 'RGB')


def create_noise_pattern():
    """Create a noise pattern."""
    size = 256
    np.random.seed(42)
    arr = np.random.randint(0, 256, (size, size, 3), dtype=np.uint8)
    
    # Apply some smoothing
    from scipy.ndimage import gaussian_filter
    for c in range(3):
        arr[:, :, c] = gaussian_filter(arr[:, :, c], sigma=2.0)
    
    return Image.fromarray(arr, 'RGB')


def test_simple():
    """Test with simple patterns."""
    tess = TessellationModule()
    
    # Test 1: Gradient pattern
    print("Testing gradient pattern...")
    gradient = create_simple_gradient()
    gradient.save("output/test_gradient_original.png")
    
    # Try different blend widths
    for blend_width in [32, 64, 128]:
        seamless = tess.make_seamless(gradient, blend_mode='offset', blend_width=blend_width)
        seamless.save(f"output/test_gradient_seamless_bw{blend_width}.png")
        
        # Create 2x2 tile
        tiled = Image.new('RGB', (512, 512))
        for y in range(2):
            for x in range(2):
                tiled.paste(seamless, (x * 256, y * 256))
        tiled.save(f"output/test_gradient_tiled_bw{blend_width}.png")
        
        is_seamless, max_diff = tess.validate_tiling(seamless)
        print(f"  Blend width {blend_width}: seamless={is_seamless}, max_diff={max_diff:.4f}")
    
    # Test 2: Noise pattern
    print("\nTesting noise pattern...")
    noise = create_noise_pattern()
    noise.save("output/test_noise_original.png")
    
    for mode in ['offset', 'mirror', 'frequency']:
        seamless = tess.make_seamless(noise, blend_mode=mode)
        seamless.save(f"output/test_noise_seamless_{mode}.png")
        
        # Create 2x2 tile
        tiled = Image.new('RGB', (512, 512))
        for y in range(2):
            for x in range(2):
                tiled.paste(seamless, (x * 256, y * 256))
        tiled.save(f"output/test_noise_tiled_{mode}.png")
        
        is_seamless, max_diff = tess.validate_tiling(seamless)
        print(f"  Mode {mode}: seamless={is_seamless}, max_diff={max_diff:.4f}")


if __name__ == "__main__":
    test_simple()