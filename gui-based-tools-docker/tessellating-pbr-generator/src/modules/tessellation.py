"""Advanced tessellation module for creating seamlessly tiling textures."""

import numpy as np
from PIL import Image, ImageFilter
from typing import Optional, Tuple
import scipy.ndimage as ndimage


class TessellationModule:
    """Module for creating seamlessly tiling textures using advanced algorithms."""
    
    def __init__(self):
        """Initialize the tessellation module."""
        pass
    
    def make_seamless(self, image: Image.Image, blend_mode: str = 'frequency', 
                     blend_width: Optional[int] = None) -> Image.Image:
        """Make an image seamlessly tileable using advanced blending techniques.
        
        Args:
            image: Input PIL Image
            blend_mode: Blending mode ('frequency' (default), 'offset', 'mirror')
            blend_width: Width of blending region (auto-calculated if None)
            
        Returns:
            Seamlessly tiling PIL Image
        """
        if blend_mode == 'offset':
            return self._offset_blend(image, blend_width)
        elif blend_mode == 'mirror':
            return self._mirror_blend(image, blend_width)
        elif blend_mode == 'frequency':
            return self._frequency_blend(image)
        else:
            raise ValueError(f"Unknown blend mode: {blend_mode}")
    
    def _offset_blend(self, image: Image.Image, blend_width: Optional[int] = None) -> Image.Image:
        """Create seamless texture using offset method with feathered blending.
        
        This is the most reliable method for most texture types.
        """
        # Convert to numpy array
        arr = np.array(image, dtype=np.float32)
        if len(arr.shape) == 2:  # Grayscale
            arr = arr[:, :, np.newaxis]
        
        h, w, c = arr.shape
        
        # Auto-calculate blend width if not provided (20% of smallest dimension)
        if blend_width is None:
            blend_width = min(w, h) // 5
            blend_width = max(64, min(blend_width, 256))  # Clamp between 64-256
        
        # Create four tiles by offsetting
        half_w = w // 2
        half_h = h // 2
        
        # Split image into 4 quadrants
        tl = arr[:half_h, :half_w]  # Top-left
        tr = arr[:half_h, half_w:]  # Top-right
        bl = arr[half_h:, :half_w]  # Bottom-left
        br = arr[half_h:, half_w:]  # Bottom-right
        
        # Rearrange quadrants to offset by half
        offset_arr = np.zeros_like(arr)
        offset_arr[:half_h, :half_w] = br
        offset_arr[:half_h, half_w:] = bl
        offset_arr[half_h:, :half_w] = tr
        offset_arr[half_h:, half_w:] = tl
        
        # Create smooth blending mask
        # Horizontal blend
        blend_h = np.ones(w)
        for i in range(blend_width):
            t = i / blend_width
            # Smooth S-curve for better blending
            weight = t * t * (3 - 2 * t)
            blend_h[half_w - blend_width//2 + i] = weight
            blend_h[half_w + blend_width//2 - i - 1] = weight
        
        # Vertical blend
        blend_v = np.ones(h)
        for i in range(blend_width):
            t = i / blend_width
            weight = t * t * (3 - 2 * t)
            blend_v[half_h - blend_width//2 + i] = weight
            blend_v[half_h + blend_width//2 - i - 1] = weight
        
        # Create 2D mask
        mask = blend_v[:, np.newaxis] * blend_h[np.newaxis, :]
        mask = ndimage.gaussian_filter(mask, sigma=blend_width/8)
        mask = mask[:, :, np.newaxis]
        
        # Blend original and offset
        result = arr * (1 - mask) + offset_arr * mask
        
        # Fix edges to ensure perfect tiling
        edge_blend = min(16, blend_width // 4)
        
        # Blend left and right edges
        for i in range(edge_blend):
            weight = i / edge_blend
            result[:, i] = result[:, i] * weight + result[:, w - edge_blend + i] * (1 - weight)
            result[:, w - edge_blend + i] = result[:, i]
        
        # Blend top and bottom edges
        for i in range(edge_blend):
            weight = i / edge_blend
            result[i, :] = result[i, :] * weight + result[h - edge_blend + i, :] * (1 - weight)
            result[h - edge_blend + i, :] = result[i, :]
        
        # Convert back to PIL Image
        if c == 1:
            result = result[:, :, 0]
            return Image.fromarray(result.astype(np.uint8), 'L')
        else:
            result = result.astype(np.uint8)
            return Image.fromarray(result, 'RGB' if c == 3 else 'RGBA')
    
    def _mirror_blend(self, image: Image.Image, blend_width: Optional[int] = None) -> Image.Image:
        """Create seamless texture using mirror blending at edges."""
        arr = np.array(image, dtype=np.float32)
        if len(arr.shape) == 2:
            arr = arr[:, :, np.newaxis]
        
        h, w, c = arr.shape
        
        if blend_width is None:
            blend_width = min(w, h) // 8
            blend_width = max(16, min(blend_width, 64))
        
        result = arr.copy()
        
        # Create blending gradients
        blend_x = np.linspace(0, 1, blend_width)
        blend_y = np.linspace(0, 1, blend_width)
        
        # Blend horizontal edges with mirrored content
        for i in range(blend_width):
            weight = blend_x[i] ** 2  # Quadratic for smoother blend
            # Left edge
            result[:, i] = arr[:, i] * weight + arr[:, blend_width - i] * (1 - weight)
            # Right edge
            result[:, w - i - 1] = arr[:, w - i - 1] * weight + arr[:, w - blend_width + i] * (1 - weight)
        
        # Blend vertical edges with mirrored content
        for i in range(blend_width):
            weight = blend_y[i] ** 2
            # Top edge
            result[i, :] = result[i, :] * weight + result[blend_width - i, :] * (1 - weight)
            # Bottom edge
            result[h - i - 1, :] = result[h - i - 1, :] * weight + result[h - blend_width + i, :] * (1 - weight)
        
        # Convert back to PIL Image
        if c == 1:
            result = result[:, :, 0]
            return Image.fromarray(result.astype(np.uint8), 'L')
        else:
            return Image.fromarray(result.astype(np.uint8), 'RGB' if c == 3 else 'RGBA')
    
    def _frequency_blend(self, image: Image.Image) -> Image.Image:
        """Create seamless texture using frequency domain approach.
        
        This method works well for organic and noise-based textures.
        """
        arr = np.array(image, dtype=np.float32)
        if len(arr.shape) == 3:
            # Process each channel separately
            channels = []
            for c in range(arr.shape[2]):
                channels.append(self._frequency_blend_channel(arr[:, :, c]))
            result = np.stack(channels, axis=2)
            return Image.fromarray(result.astype(np.uint8), 
                                 'RGB' if arr.shape[2] == 3 else 'RGBA')
        else:
            # Grayscale
            result = self._frequency_blend_channel(arr)
            return Image.fromarray(result.astype(np.uint8), 'L')
    
    def _frequency_blend_channel(self, channel: np.ndarray) -> np.ndarray:
        """Apply frequency domain blending to a single channel."""
        h, w = channel.shape
        
        # Apply window function to reduce edge artifacts
        window_x = np.hanning(w)
        window_y = np.hanning(h)
        window = window_y[:, np.newaxis] * window_x[np.newaxis, :]
        
        # Blend edges with center
        windowed = channel * window + np.mean(channel) * (1 - window)
        
        # Apply FFT
        fft = np.fft.fft2(windowed)
        
        # Shift zero frequency to center
        fft_shifted = np.fft.fftshift(fft)
        
        # Create high-pass filter to preserve details
        y, x = np.ogrid[-h/2:h/2, -w/2:w/2]
        # Gaussian high-pass filter
        sigma = min(w, h) / 8
        highpass = 1 - np.exp(-(x*x + y*y) / (2 * sigma * sigma))
        
        # Apply filter
        fft_filtered = fft_shifted * highpass
        
        # Inverse transform
        fft_ishifted = np.fft.ifftshift(fft_filtered)
        result = np.fft.ifft2(fft_ishifted).real
        
        # Normalize
        result = (result - result.min()) / (result.max() - result.min()) * 255
        
        return result
    
    def _blend_four_corners(self, arr: np.ndarray, x: int, y: int, 
                           w: int, h: int, weight: float) -> np.ndarray:
        """Blend four corners for perfect tiling at corner regions."""
        # Get the four corner values that need to match
        tl = arr[y, x]  # Top-left
        tr = arr[y, w - (w - x)]  # Top-right wrapped
        bl = arr[h - (h - y), x]  # Bottom-left wrapped
        br = arr[h - (h - y), w - (w - x)]  # Bottom-right wrapped
        
        # Weighted average of all four corners
        return tl * (1 - weight) + (tr + bl + br) * (weight / 3)
    
    def validate_tiling(self, image: Image.Image, threshold: float = 0.1) -> Tuple[bool, float]:
        """Validate if an image tiles seamlessly.
        
        Args:
            image: PIL Image to validate
            threshold: Maximum allowed edge difference (0-1)
            
        Returns:
            Tuple of (is_seamless, max_edge_difference)
        """
        arr = np.array(image, dtype=np.float32) / 255.0
        
        if len(arr.shape) == 3:
            # For color images, check each channel
            diffs = []
            for c in range(arr.shape[2]):
                diffs.append(self._check_edge_diff(arr[:, :, c]))
            max_diff = max(diffs)
        else:
            max_diff = self._check_edge_diff(arr)
        
        is_seamless = max_diff < threshold
        return is_seamless, max_diff
    
    def _check_edge_diff(self, channel: np.ndarray) -> float:
        """Check maximum difference at edges when tiled."""
        h, w = channel.shape
        
        # Check horizontal edges
        h_diff = np.max(np.abs(channel[:, 0] - channel[:, -1]))
        
        # Check vertical edges
        v_diff = np.max(np.abs(channel[0, :] - channel[-1, :]))
        
        return max(h_diff, v_diff)
    
    def create_test_pattern(self, size: Tuple[int, int] = (512, 512)) -> Image.Image:
        """Create a test pattern to verify tiling functionality.
        
        Args:
            size: Output size (width, height)
            
        Returns:
            Test pattern as PIL Image
        """
        w, h = size
        
        # Create a pattern with features that make seams obvious
        arr = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Add diagonal stripes
        for i in range(0, max(w, h) * 2, 40):
            for t in range(-5, 6):
                y = np.arange(h)
                x = (i - y + t) % w
                valid = (x >= 0) & (x < w)
                arr[y[valid], x[valid]] = [255, 100, 0]
        
        # Add some circles
        center_x, center_y = w // 3, h // 3
        radius = min(w, h) // 6
        y, x = np.ogrid[:h, :w]
        mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2
        arr[mask] = [0, 255, 100]
        
        # Add another circle
        center_x, center_y = 2 * w // 3, 2 * h // 3
        mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2
        arr[mask] = [100, 0, 255]
        
        return Image.fromarray(arr, 'RGB')