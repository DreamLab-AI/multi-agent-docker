"""
Unit tests for tessellation and seamless tiling functionality.
"""

import pytest
import numpy as np
from PIL import Image
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.tessellation.seamless_tiling import SeamlessTiling


class TestSeamlessTiling:
    """Test seamless tiling functionality."""
    
    def test_seamless_tiling_basic(self, sample_image):
        """Test basic seamless tiling operation."""
        tiling = SeamlessTiling()
        seamless = tiling.make_seamless(sample_image)
        
        assert isinstance(seamless, Image.Image)
        assert seamless.size == sample_image.size
        assert seamless.mode == sample_image.mode
    
    def test_edge_matching(self, sample_image):
        """Test that edges match after tiling."""
        tiling = SeamlessTiling()
        seamless = tiling.make_seamless(sample_image)
        
        # Convert to array
        seamless_array = np.array(seamless)
        height, width = seamless_array.shape[:2]
        
        # Check that opposite edges are similar
        # Left edge should match right edge
        left_edge = seamless_array[:, 0]
        right_edge = seamless_array[:, -1]
        
        # Top edge should match bottom edge
        top_edge = seamless_array[0, :]
        bottom_edge = seamless_array[-1, :]
        
        # They should be very similar (not necessarily identical due to blending)
        # Using a tolerance for the comparison
        if len(seamless_array.shape) == 3:  # RGB
            left_right_diff = np.mean(np.abs(left_edge - right_edge))
            top_bottom_diff = np.mean(np.abs(top_edge - bottom_edge))
        else:  # Grayscale
            left_right_diff = np.mean(np.abs(left_edge - right_edge))
            top_bottom_diff = np.mean(np.abs(top_edge - bottom_edge))
        
        # Should be reasonably close
        assert left_right_diff < 50  # Adjust threshold as needed
        assert top_bottom_diff < 50
    
    def test_grayscale_tiling(self, grayscale_image):
        """Test seamless tiling with grayscale images."""
        tiling = SeamlessTiling()
        seamless = tiling.make_seamless(grayscale_image)
        
        assert isinstance(seamless, Image.Image)
        assert seamless.mode == 'L'
        assert seamless.size == grayscale_image.size
    
    def test_blend_width_parameter(self, sample_image):
        """Test different blend width parameters."""
        tiling = SeamlessTiling()
        
        # Test with different blend widths
        narrow_blend = tiling.make_seamless(sample_image, blend_width=10)
        wide_blend = tiling.make_seamless(sample_image, blend_width=50)
        
        # Both should produce valid images
        assert narrow_blend.size == sample_image.size
        assert wide_blend.size == sample_image.size
        
        # Visual difference should exist but both should be seamless
        narrow_array = np.array(narrow_blend)
        wide_array = np.array(wide_blend)
        
        # They should be different
        assert not np.array_equal(narrow_array, wide_array)
    
    def test_tiling_preserves_features(self):
        """Test that tiling preserves important image features."""
        # Create an image with a clear feature
        test_image = Image.new('RGB', (200, 200), 'white')
        pixels = test_image.load()
        
        # Draw a circle in the center
        center_x, center_y = 100, 100
        radius = 30
        for x in range(200):
            for y in range(200):
                if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                    pixels[x, y] = (255, 0, 0)  # Red circle
        
        tiling = SeamlessTiling()
        seamless = tiling.make_seamless(test_image)
        
        # The circle should still be visible
        seamless_array = np.array(seamless)
        red_pixels = np.sum(seamless_array[:, :, 0] > 200)
        
        # Should have roughly the same amount of red pixels
        original_red = np.sum(np.array(test_image)[:, :, 0] > 200)
        assert abs(red_pixels - original_red) / original_red < 0.2  # Within 20%
    
    def test_tile_multiple_times(self, sample_image):
        """Test creating a larger tiled pattern."""
        tiling = SeamlessTiling()
        seamless = tiling.make_seamless(sample_image)
        
        # Create a 2x2 tile
        width, height = seamless.size
        tiled = Image.new(seamless.mode, (width * 2, height * 2))
        
        # Paste the seamless texture 4 times
        tiled.paste(seamless, (0, 0))
        tiled.paste(seamless, (width, 0))
        tiled.paste(seamless, (0, height))
        tiled.paste(seamless, (width, height))
        
        # Check that seams are not visible
        tiled_array = np.array(tiled)
        
        # Check vertical seam in the middle
        left_of_seam = tiled_array[:, width-1]
        right_of_seam = tiled_array[:, width]
        vertical_diff = np.mean(np.abs(left_of_seam - right_of_seam))
        
        # Check horizontal seam in the middle
        top_of_seam = tiled_array[height-1, :]
        bottom_of_seam = tiled_array[height, :]
        horizontal_diff = np.mean(np.abs(top_of_seam - bottom_of_seam))
        
        # Differences should be minimal
        assert vertical_diff < 10
        assert horizontal_diff < 10
    
    def test_different_image_sizes(self):
        """Test tiling with various image sizes."""
        tiling = SeamlessTiling()
        
        sizes = [(128, 128), (256, 256), (512, 512), (256, 512)]
        
        for size in sizes:
            test_img = Image.new('RGB', size, 'blue')
            seamless = tiling.make_seamless(test_img)
            
            assert seamless.size == size
            assert seamless.mode == 'RGB'
    
    def test_method_consistency(self, sample_image):
        """Test that the same input produces consistent results."""
        tiling = SeamlessTiling()
        
        # Generate twice with same parameters
        result1 = tiling.make_seamless(sample_image, blend_width=30)
        result2 = tiling.make_seamless(sample_image, blend_width=30)
        
        # Should produce identical results
        assert np.array_equal(np.array(result1), np.array(result2))
    
    def test_normal_map_tiling(self):
        """Test tiling specifically for normal maps."""
        # Create a simple normal map (blue-ish image)
        normal_map = Image.new('RGB', (256, 256), (128, 128, 255))
        
        # Add some variation
        pixels = normal_map.load()
        for x in range(0, 256, 32):
            for y in range(256):
                pixels[x, y] = (140, 128, 255)  # Slight X normal
        
        tiling = SeamlessTiling()
        seamless_normal = tiling.make_seamless(normal_map)
        
        # Check that it's still a valid normal map
        normal_array = np.array(seamless_normal)
        
        # Blue channel should still be dominant (Z component)
        assert np.mean(normal_array[:, :, 2]) > 200
        
        # Should maintain normalized vectors (approximately)
        # Normal maps encode unit vectors, so magnitude should be ~1
        # when converted back from [0,255] to [-1,1]
        sample_pixel = normal_array[128, 128]
        normal_vector = (sample_pixel / 255.0) * 2 - 1
        magnitude = np.linalg.norm(normal_vector)
        
        assert 0.8 < magnitude < 1.2  # Allow some tolerance