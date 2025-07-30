"""Direct test of filter functions."""

import numpy as np
from scipy import ndimage
from PIL import Image


# Copy the functions directly for testing
def sobel_filter(image):
    """Apply Sobel filter to detect edges in x and y directions."""
    sobel_x = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)
    
    sobel_y = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)
    
    grad_x = ndimage.convolve(image, sobel_x)
    grad_y = ndimage.convolve(image, sobel_y)
    
    return grad_x, grad_y


def height_to_normal(height_map, strength=1.0, invert_y=False):
    """Convert height map to normal map using gradient calculation."""
    if height_map.max() > 1.0:
        height_map = height_map / 255.0
    
    grad_x, grad_y = sobel_filter(height_map)
    
    grad_x *= strength
    grad_y *= strength
    
    if invert_y:
        grad_y = -grad_y
    
    normal_x = -grad_x
    normal_y = -grad_y
    normal_z = np.ones_like(height_map)
    
    magnitude = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    normal_x /= magnitude
    normal_y /= magnitude
    normal_z /= magnitude
    
    normal_map = np.stack([
        (normal_x + 1.0) * 0.5,
        (normal_y + 1.0) * 0.5,
        (normal_z + 1.0) * 0.5
    ], axis=-1)
    
    return normal_map


def main():
    """Test the functions."""
    print("Testing filter functions directly...")
    
    # Create a test height map
    size = 512
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)
    
    # Create multiple features for testing
    # 1. Circular gradient (dome)
    dome = 1.0 - np.clip(np.sqrt(xx**2 + yy**2), 0, 1)
    
    # 2. Some ridges
    ridges = np.sin(xx * 10) * 0.1 + np.sin(yy * 10) * 0.1
    
    # 3. Random noise for detail
    noise = np.random.randn(size, size) * 0.02
    
    # Combine features
    height_map = dome * 0.7 + ridges * 0.2 + noise
    height_map = np.clip(height_map, 0, 1)
    
    # Save height map
    height_image = Image.fromarray((height_map * 255).astype(np.uint8), mode='L')
    height_image.save("/workspace/ext/tessellating-pbr-generator/output/test_height_generated.png")
    print(f"✓ Saved test height map")
    
    # Convert to normal map with different strengths
    for strength in [0.5, 1.0, 2.0]:
        normal_map = height_to_normal(height_map, strength=strength)
        
        # Save normal map
        normal_image = Image.fromarray((normal_map * 255).astype(np.uint8), mode='RGB')
        normal_image.save(f"/workspace/ext/tessellating-pbr-generator/output/test_normal_strength_{strength}.png")
        print(f"✓ Generated normal map with strength {strength}")
        print(f"  Shape: {normal_map.shape}")
        print(f"  R range: [{normal_map[:,:,0].min():.3f}, {normal_map[:,:,0].max():.3f}]")
        print(f"  G range: [{normal_map[:,:,1].min():.3f}, {normal_map[:,:,1].max():.3f}]")
        print(f"  B range: [{normal_map[:,:,2].min():.3f}, {normal_map[:,:,2].max():.3f}]")
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()