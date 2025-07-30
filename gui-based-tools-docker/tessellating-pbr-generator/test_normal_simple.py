"""Simple test for normal module without full config dependencies."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
import numpy as np

# Import just what we need
from src.utils.filters import height_to_normal, sobel_filter, enhance_details


def test_sobel_filter():
    """Test Sobel filter functionality."""
    print("Testing Sobel filter...")
    
    # Create a simple test pattern
    test_image = np.zeros((100, 100), dtype=np.float32)
    test_image[40:60, 40:60] = 1.0  # White square in center
    
    grad_x, grad_y = sobel_filter(test_image)
    
    print(f"✓ Sobel filter applied successfully")
    print(f"  Gradient X shape: {grad_x.shape}, range: [{grad_x.min():.2f}, {grad_x.max():.2f}]")
    print(f"  Gradient Y shape: {grad_y.shape}, range: [{grad_y.min():.2f}, {grad_y.max():.2f}]")


def test_height_to_normal():
    """Test height to normal conversion."""
    print("\nTesting height to normal conversion...")
    
    # Create a simple height map - circular gradient
    size = 256
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)
    
    # Distance from center
    distance = np.sqrt(xx**2 + yy**2)
    height_map = 1.0 - np.clip(distance, 0, 1)
    
    # Convert to normal map
    normal_map = height_to_normal(height_map, strength=1.0)
    
    print(f"✓ Height to normal conversion successful")
    print(f"  Normal map shape: {normal_map.shape}")
    print(f"  Value ranges:")
    print(f"    R (X): [{normal_map[:,:,0].min():.3f}, {normal_map[:,:,0].max():.3f}]")
    print(f"    G (Y): [{normal_map[:,:,1].min():.3f}, {normal_map[:,:,1].max():.3f}]")
    print(f"    B (Z): [{normal_map[:,:,2].min():.3f}, {normal_map[:,:,2].max():.3f}]")
    
    # Save the test normal map
    normal_image = Image.fromarray((normal_map * 255).astype(np.uint8), mode='RGB')
    normal_image.save("/workspace/ext/tessellating-pbr-generator/output/test_normal_simple.png")
    print(f"✓ Saved test normal map to output/test_normal_simple.png")


def test_enhance_details():
    """Test detail enhancement."""
    print("\nTesting detail enhancement...")
    
    # Create test image with noise
    test_image = np.random.randn(100, 100) * 0.1 + 0.5
    test_image = np.clip(test_image, 0, 1)
    
    enhanced = enhance_details(test_image, detail_strength=0.5)
    
    print(f"✓ Detail enhancement successful")
    print(f"  Original std dev: {test_image.std():.4f}")
    print(f"  Enhanced std dev: {enhanced.std():.4f}")


def main():
    """Run all tests."""
    print("Running simple normal module tests...\n")
    
    test_sobel_filter()
    test_height_to_normal()
    test_enhance_details()
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()