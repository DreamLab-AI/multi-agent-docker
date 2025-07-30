"""Tessellation utilities for seamless texture tiling."""

from typing import Tuple
from PIL import Image
import numpy as np
from ..utils.logging import get_logger


logger = get_logger(__name__)


def apply_tessellation(image: Image.Image, blend_width: int = 50) -> Image.Image:
    """Apply tessellation to make an image tile seamlessly.
    
    This is a basic implementation that blends edges to create seamless tiling.
    A more advanced implementation would use Wang tiles or other algorithms.
    
    Args:
        image: Input PIL Image
        blend_width: Width of the blend region at edges
        
    Returns:
        Tessellated PIL Image that tiles seamlessly
    """
    logger.info(f"Applying tessellation with blend width: {blend_width}")
    
    # Convert to numpy array
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Create a copy for blending
    result = img_array.copy()
    
    # Blend horizontal edges
    for y in range(height):
        for x in range(blend_width):
            # Calculate blend factor (0 to 1)
            blend = x / blend_width
            
            # Blend left edge with right edge
            left_x = x
            right_x = width - blend_width + x
            
            # Linear interpolation
            if len(img_array.shape) == 3:  # RGB image
                result[y, left_x] = (
                    blend * img_array[y, left_x] +
                    (1 - blend) * img_array[y, right_x]
                ).astype(np.uint8)
                
                result[y, right_x] = (
                    (1 - blend) * img_array[y, left_x] +
                    blend * img_array[y, right_x]
                ).astype(np.uint8)
            else:  # Grayscale
                result[y, left_x] = int(
                    blend * img_array[y, left_x] +
                    (1 - blend) * img_array[y, right_x]
                )
                
                result[y, right_x] = int(
                    (1 - blend) * img_array[y, left_x] +
                    blend * img_array[y, right_x]
                )
    
    # Blend vertical edges
    for x in range(width):
        for y in range(blend_width):
            # Calculate blend factor
            blend = y / blend_width
            
            # Blend top edge with bottom edge
            top_y = y
            bottom_y = height - blend_width + y
            
            # Linear interpolation
            if len(img_array.shape) == 3:  # RGB image
                result[top_y, x] = (
                    blend * result[top_y, x] +
                    (1 - blend) * result[bottom_y, x]
                ).astype(np.uint8)
                
                result[bottom_y, x] = (
                    (1 - blend) * result[top_y, x] +
                    blend * result[bottom_y, x]
                ).astype(np.uint8)
            else:  # Grayscale
                result[top_y, x] = int(
                    blend * result[top_y, x] +
                    (1 - blend) * result[bottom_y, x]
                )
                
                result[bottom_y, x] = int(
                    (1 - blend) * result[top_y, x] +
                    blend * result[bottom_y, x]
                )
    
    # Convert back to PIL Image
    return Image.fromarray(result)


def create_wang_tiles(image: Image.Image, tile_size: Tuple[int, int] = (256, 256)) -> dict:
    """Create Wang tiles from an image for more advanced tessellation.
    
    This is a placeholder for a more sophisticated tessellation algorithm.
    
    Args:
        image: Input PIL Image
        tile_size: Size of each tile
        
    Returns:
        Dictionary of Wang tiles
    """
    logger.info("Wang tiles generation not yet implemented")
    # TODO: Implement Wang tiles algorithm
    # This would create multiple tile variations that can be
    # arranged to create seamless patterns with more variety
    return {"base": image}