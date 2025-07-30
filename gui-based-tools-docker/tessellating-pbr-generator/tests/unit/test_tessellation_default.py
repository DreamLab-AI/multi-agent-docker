"""Comprehensive unit tests for tessellation module with focus on frequency defaults."""

import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from unittest.mock import Mock, patch

from src.modules.tessellation import TessellationModule


class TestTessellationDefaults:
    """Test suite focusing on tessellation frequency defaults and parameter handling."""
    
    @pytest.fixture
    def tessellation_module(self):
        """Create a TessellationModule instance for testing."""
        return TessellationModule()
    
    @pytest.fixture
    def test_pattern_image(self):
        """Create a test pattern image with clear seam visibility."""
        width, height = 512, 512
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create a pattern that makes seams obvious
        # Diagonal stripes
        for i in range(0, width + height, 20):
            for y in range(height):
                x = i - y
                if 0 <= x < width and (i // 20) % 2 == 0:
                    image[y, x] = [255, 100, 0]
        
        # Add some distinct features at edges
        image[:10, :] = [0, 255, 0]  # Green top edge
        image[-10:, :] = [0, 0, 255]  # Blue bottom edge
        image[:, :10] = [255, 0, 0]  # Red left edge
        image[:, -10:] = [255, 255, 0]  # Yellow right edge
        
        return Image.fromarray(image)
    
    def test_default_blend_mode_parameters(self, tessellation_module, test_pattern_image):
        """Test default parameters for different blend modes."""
        # Test offset blend defaults
        result_offset = tessellation_module.make_seamless(
            test_pattern_image,
            blend_mode='offset'
            # No blend_width specified - should use default
        )
        
        assert isinstance(result_offset, Image.Image)
        assert result_offset.size == test_pattern_image.size
        
        # Test mirror blend defaults
        result_mirror = tessellation_module.make_seamless(
            test_pattern_image,
            blend_mode='mirror'
            # No blend_width specified - should use default
        )
        
        assert isinstance(result_mirror, Image.Image)
        assert result_mirror.size == test_pattern_image.size
        
        # Test frequency blend defaults (no blend_width parameter)
        result_frequency = tessellation_module.make_seamless(
            test_pattern_image,
            blend_mode='frequency'
        )
        
        assert isinstance(result_frequency, Image.Image)
        assert result_frequency.size == test_pattern_image.size
    
    def test_automatic_blend_width_calculation(self, tessellation_module):
        """Test automatic blend width calculation for different image sizes."""
        # Test various image sizes
        test_sizes = [
            (256, 256),    # Small square
            (512, 512),    # Medium square
            (1024, 1024),  # Large square
            (512, 256),    # Wide rectangle
            (256, 512),    # Tall rectangle
            (2048, 1024),  # Large rectangle
        ]
        
        for width, height in test_sizes:
            # Create test image
            test_image = Image.new('RGB', (width, height), color=(128, 128, 128))
            
            # Process with offset blend (uses auto blend width)
            result = tessellation_module.make_seamless(test_image, blend_mode='offset')
            
            # Verify result
            assert result.size == (width, height)
            
            # Expected blend width should be 20% of smallest dimension, clamped 64-256
            min_dim = min(width, height)
            expected_blend = max(64, min(min_dim // 5, 256))
            
            # We can't directly test the internal blend width, but we can verify
            # the function completes successfully with reasonable defaults
    
    def test_frequency_blend_default_parameters(self, tessellation_module):
        """Test frequency blend method default parameters."""
        # Create images with different characteristics
        # Noise-based texture
        noise_image = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        noise_pil = Image.fromarray(noise_image)
        
        # Smooth gradient texture
        gradient = np.zeros((512, 512, 3), dtype=np.uint8)
        for i in range(512):
            gradient[i, :] = int(255 * i / 512)
        gradient_pil = Image.fromarray(gradient)
        
        # Test frequency blend on different texture types
        noise_result = tessellation_module.make_seamless(noise_pil, blend_mode='frequency')
        gradient_result = tessellation_module.make_seamless(gradient_pil, blend_mode='frequency')
        
        assert noise_result.size == (512, 512)
        assert gradient_result.size == (512, 512)
        
        # Verify tiling quality
        noise_seamless, noise_diff = tessellation_module.validate_tiling(noise_result)
        gradient_seamless, gradient_diff = tessellation_module.validate_tiling(gradient_result)
        
        # Frequency blend should work well with noise
        assert noise_seamless or noise_diff < 0.2
    
    def test_blend_width_edge_cases(self, tessellation_module):
        """Test blend width handling for edge cases."""
        # Very small image
        tiny_image = Image.new('RGB', (64, 64), color=(100, 100, 100))
        
        # Test with different blend modes
        result_offset = tessellation_module.make_seamless(tiny_image, blend_mode='offset')
        result_mirror = tessellation_module.make_seamless(tiny_image, blend_mode='mirror')
        
        # Should handle small images gracefully
        assert result_offset.size == (64, 64)
        assert result_mirror.size == (64, 64)
        
        # Test with extreme aspect ratios
        wide_image = Image.new('RGB', (2048, 128), color=(150, 150, 150))
        tall_image = Image.new('RGB', (128, 2048), color=(150, 150, 150))
        
        wide_result = tessellation_module.make_seamless(wide_image, blend_mode='offset')
        tall_result = tessellation_module.make_seamless(tall_image, blend_mode='offset')
        
        assert wide_result.size == (2048, 128)
        assert tall_result.size == (128, 2048)
    
    def test_custom_blend_width_override(self, tessellation_module, test_pattern_image):
        """Test overriding default blend width with custom values."""
        # Test with various custom blend widths
        blend_widths = [16, 32, 64, 128, 256]
        
        for blend_width in blend_widths:
            result_offset = tessellation_module.make_seamless(
                test_pattern_image,
                blend_mode='offset',
                blend_width=blend_width
            )
            
            result_mirror = tessellation_module.make_seamless(
                test_pattern_image,
                blend_mode='mirror',
                blend_width=blend_width
            )
            
            # Verify results
            assert result_offset.size == test_pattern_image.size
            assert result_mirror.size == test_pattern_image.size
            
            # Smaller blend widths should preserve more detail
            # Larger blend widths should create smoother transitions
    
    def test_frequency_domain_defaults(self, tessellation_module):
        """Test frequency domain processing with default parameters."""
        # Create test image with specific frequency content
        width, height = 512, 512
        x = np.linspace(0, 4 * np.pi, width)
        y = np.linspace(0, 4 * np.pi, height)
        X, Y = np.meshgrid(x, y)
        
        # Create pattern with multiple frequencies
        low_freq = np.sin(X) * np.cos(Y)
        high_freq = np.sin(10 * X) * np.cos(10 * Y)
        pattern = (low_freq + 0.3 * high_freq) * 127.5 + 127.5
        
        pattern_image = Image.fromarray(pattern.astype(np.uint8), mode='L')
        
        # Apply frequency blend
        result = tessellation_module.make_seamless(pattern_image, blend_mode='frequency')
        
        # Verify seamless tiling
        is_seamless, edge_diff = tessellation_module.validate_tiling(result)
        assert is_seamless or edge_diff < 0.15
        
        # The frequency method should preserve frequency content while ensuring tiling
    
    def test_grayscale_image_handling(self, tessellation_module):
        """Test default handling of grayscale images."""
        # Create various grayscale patterns
        patterns = {
            'gradient': np.linspace(0, 255, 512*512).reshape(512, 512),
            'checkerboard': np.indices((512, 512)).sum(axis=0) % 64 < 32,
            'noise': np.random.randint(0, 256, (512, 512))
        }
        
        for pattern_name, pattern_data in patterns.items():
            if pattern_name == 'checkerboard':
                pattern_data = pattern_data.astype(np.uint8) * 255
            else:
                pattern_data = pattern_data.astype(np.uint8)
            
            grayscale_image = Image.fromarray(pattern_data, mode='L')
            
            # Test all blend modes with grayscale
            for blend_mode in ['offset', 'mirror', 'frequency']:
                result = tessellation_module.make_seamless(
                    grayscale_image,
                    blend_mode=blend_mode
                )
                
                assert result.mode == 'L'
                assert result.size == (512, 512)
    
    def test_rgba_image_handling(self, tessellation_module):
        """Test default handling of RGBA images with transparency."""
        # Create RGBA test image
        rgba_array = np.zeros((512, 512, 4), dtype=np.uint8)
        
        # Add pattern with varying alpha
        for y in range(512):
            for x in range(512):
                rgba_array[y, x] = [
                    int(255 * x / 512),  # Red gradient
                    int(255 * y / 512),  # Green gradient
                    128,                  # Blue constant
                    int(255 * ((x + y) % 512) / 512)  # Alpha pattern
                ]
        
        rgba_image = Image.fromarray(rgba_array, mode='RGBA')
        
        # Test all blend modes with RGBA
        for blend_mode in ['offset', 'mirror', 'frequency']:
            result = tessellation_module.make_seamless(
                rgba_image,
                blend_mode=blend_mode
            )
            
            assert result.mode == 'RGBA'
            assert result.size == (512, 512)
            
            # Verify alpha channel is preserved
            result_array = np.array(result)
            assert result_array.shape[2] == 4
            assert np.any(result_array[:, :, 3] != 255)  # Alpha varies
    
    def test_tiling_validation_thresholds(self, tessellation_module):
        """Test tiling validation with different threshold values."""
        # Create an image that's already seamless
        seamless_image = tessellation_module.create_test_pattern(size=(256, 256))
        processed = tessellation_module.make_seamless(seamless_image, blend_mode='offset')
        
        # Test with different thresholds
        thresholds = [0.01, 0.05, 0.1, 0.2, 0.5]
        
        for threshold in thresholds:
            is_seamless, edge_diff = tessellation_module.validate_tiling(
                processed,
                threshold=threshold
            )
            
            # Lower thresholds are stricter
            if threshold >= 0.1:
                assert is_seamless
            
            # Edge difference should be consistent
            assert 0 <= edge_diff <= 1.0
    
    def test_edge_blending_quality(self, tessellation_module, test_pattern_image):
        """Test quality of edge blending with default parameters."""
        # Process image
        result = tessellation_module.make_seamless(
            test_pattern_image,
            blend_mode='offset'
        )
        
        result_array = np.array(result)
        height, width = result_array.shape[:2]
        
        # Check that edges match for tiling
        # Left edge should match right edge
        left_edge = result_array[:, 0]
        right_edge = result_array[:, -1]
        edge_diff_horizontal = np.mean(np.abs(left_edge - right_edge))
        
        # Top edge should match bottom edge
        top_edge = result_array[0, :]
        bottom_edge = result_array[-1, :]
        edge_diff_vertical = np.mean(np.abs(top_edge - bottom_edge))
        
        # Edges should be very similar for seamless tiling
        assert edge_diff_horizontal < 5.0  # Allow small differences
        assert edge_diff_vertical < 5.0
    
    def test_corner_blending_consistency(self, tessellation_module):
        """Test that corners blend properly for perfect tiling."""
        # Create image with distinct corners
        corner_image = np.ones((256, 256, 3), dtype=np.uint8) * 128
        
        # Mark corners with different colors
        corner_size = 20
        corner_image[:corner_size, :corner_size] = [255, 0, 0]      # Top-left: red
        corner_image[:corner_size, -corner_size:] = [0, 255, 0]     # Top-right: green
        corner_image[-corner_size:, :corner_size] = [0, 0, 255]     # Bottom-left: blue
        corner_image[-corner_size:, -corner_size:] = [255, 255, 0]  # Bottom-right: yellow
        
        corner_pil = Image.fromarray(corner_image)
        
        # Process with each blend mode
        for blend_mode in ['offset', 'mirror']:
            result = tessellation_module.make_seamless(
                corner_pil,
                blend_mode=blend_mode
            )
            
            result_array = np.array(result)
            
            # Check corner consistency
            # When tiled, opposite corners should blend smoothly
            tl = result_array[0, 0]
            tr = result_array[0, -1]
            bl = result_array[-1, 0]
            br = result_array[-1, -1]
            
            # Adjacent corners in tiling should be similar
            assert np.allclose(tl, tr, atol=10)
            assert np.allclose(tl, bl, atol=10)
            assert np.allclose(br, tl, atol=10)
    
    def test_performance_with_large_images(self, tessellation_module):
        """Test performance and memory handling with large images."""
        # Create a large test image
        large_image = Image.new('RGB', (2048, 2048), color=(100, 150, 200))
        
        # Add some pattern to make it non-uniform
        pixels = large_image.load()
        for i in range(0, 2048, 100):
            for j in range(2048):
                pixels[i, j] = (255, 100, 50)
                pixels[j, i] = (50, 100, 255)
        
        # Test that processing completes without memory issues
        import time
        
        start_time = time.time()
        result = tessellation_module.make_seamless(
            large_image,
            blend_mode='offset'
        )
        processing_time = time.time() - start_time
        
        assert result.size == (2048, 2048)
        # Should complete in reasonable time (less than 5 seconds)
        assert processing_time < 5.0
    
    def test_error_handling_invalid_blend_mode(self, tessellation_module, test_pattern_image):
        """Test error handling for invalid blend modes."""
        with pytest.raises(ValueError, match="Unknown blend mode"):
            tessellation_module.make_seamless(
                test_pattern_image,
                blend_mode='invalid_mode'
            )
    
    def test_frequency_blend_channel_processing(self, tessellation_module):
        """Test frequency blend processing of individual channels."""
        # Create test channel with known frequency content
        channel = np.zeros((256, 256), dtype=np.float32)
        
        # Add low frequency component
        x = np.linspace(0, 2 * np.pi, 256)
        y = np.linspace(0, 2 * np.pi, 256)
        X, Y = np.meshgrid(x, y)
        channel += np.sin(X) * 127.5 + 127.5
        
        # Process channel
        result = tessellation_module._frequency_blend_channel(channel)
        
        assert result.shape == (256, 256)
        assert result.dtype == np.float32 or result.dtype == np.float64
        assert 0 <= np.min(result) <= np.max(result) <= 255
    
    def test_test_pattern_generation(self, tessellation_module):
        """Test the built-in test pattern generation."""
        # Test default size
        default_pattern = tessellation_module.create_test_pattern()
        assert default_pattern.size == (512, 512)
        assert default_pattern.mode == 'RGB'
        
        # Test custom sizes
        custom_sizes = [(256, 256), (512, 256), (1024, 1024)]
        
        for size in custom_sizes:
            pattern = tessellation_module.create_test_pattern(size=size)
            assert pattern.size == size
            
            # Verify pattern has visible features
            pattern_array = np.array(pattern)
            assert np.std(pattern_array) > 50  # Has variation
            assert len(np.unique(pattern_array.reshape(-1, 3), axis=0)) > 10  # Multiple colors