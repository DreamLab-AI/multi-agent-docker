"""Image filtering utilities for texture processing."""

import numpy as np
from scipy import ndimage
from typing import Tuple


def sobel_filter(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Apply Sobel filter to detect edges in x and y directions.
    
    Args:
        image: Input image as numpy array (grayscale)
        
    Returns:
        Tuple of (gradient_x, gradient_y) arrays
    """
    # Sobel kernels
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
    
    # Apply filters
    grad_x = ndimage.convolve(image, sobel_x)
    grad_y = ndimage.convolve(image, sobel_y)
    
    return grad_x, grad_y


def height_to_normal(
    height_map: np.ndarray, 
    strength: float = 1.0,
    invert_y: bool = False,
    blur_radius: float = 0.0
) -> np.ndarray:
    """Convert height map to normal map using gradient calculation.
    
    Args:
        height_map: Height map as 2D numpy array (normalized 0-1)
        strength: Normal strength factor (higher = more pronounced normals)
        invert_y: Whether to invert Y axis (for different coordinate systems)
        blur_radius: Blur radius to apply before normal calculation (0 = no blur)
        
    Returns:
        Normal map as 3D numpy array (RGB, values 0-1)
    """
    # Ensure height map is normalized
    if height_map.max() > 1.0:
        height_map = height_map / 255.0
    
    # Apply blur if requested
    if blur_radius > 0:
        height_map = gaussian_blur(height_map, sigma=blur_radius)
    
    # Apply Sobel filter to get gradients
    grad_x, grad_y = sobel_filter(height_map)
    
    # Scale gradients by strength
    grad_x *= strength
    grad_y *= strength
    
    # Invert Y if needed (some applications use different conventions)
    if invert_y:
        grad_y = -grad_y
    
    # Create normal vectors
    # Normal = normalize(vec3(-dh/dx, -dh/dy, 1))
    normal_x = -grad_x
    normal_y = -grad_y
    normal_z = np.ones_like(height_map)
    
    # Normalize the vectors
    magnitude = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    normal_x /= magnitude
    normal_y /= magnitude
    normal_z /= magnitude
    
    # Convert from [-1, 1] to [0, 1] range for RGB encoding
    normal_map = np.stack([
        (normal_x + 1.0) * 0.5,  # R channel
        (normal_y + 1.0) * 0.5,  # G channel
        (normal_z + 1.0) * 0.5   # B channel
    ], axis=-1)
    
    return normal_map


def gaussian_blur(image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian blur to an image.
    
    Args:
        image: Input image as numpy array
        sigma: Standard deviation for Gaussian kernel
        
    Returns:
        Blurred image as numpy array
    """
    return ndimage.gaussian_filter(image, sigma=sigma)


def enhance_details(
    image: np.ndarray, 
    detail_strength: float = 0.5,
    blur_sigma: float = 2.0
) -> np.ndarray:
    """Enhance fine details in an image using high-pass filtering.
    
    Args:
        image: Input image as numpy array
        detail_strength: Strength of detail enhancement (0-1)
        blur_sigma: Sigma for base blur
        
    Returns:
        Enhanced image as numpy array
    """
    # Create a blurred version
    blurred = gaussian_blur(image, sigma=blur_sigma)
    
    # Calculate high-frequency details
    details = image - blurred
    
    # Add details back with strength factor
    enhanced = image + details * detail_strength
    
    # Clip to valid range
    return np.clip(enhanced, 0, 1)