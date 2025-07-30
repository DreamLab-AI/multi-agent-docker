"""Base module for texture generation."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

from ..types.config import Config, MaterialProperties
from ..types.common import TextureType


class TextureGenerator(ABC):
    """Base class for texture generation modules."""
    
    def __init__(self, config: Config):
        """Initialize the texture generator.
        
        Args:
            config: Configuration object containing generation parameters
        """
        self.config = config
        self.material_properties = config.material_properties
        self.resolution = config.texture_config.resolution
        self.seamless = config.texture_config.seamless
    
    @property
    @abstractmethod
    def texture_type(self) -> TextureType:
        """Return the texture type this generator produces."""
        pass
    
    @abstractmethod
    def generate(self, input_data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Generate the texture.
        
        Args:
            input_data: Optional input data (e.g., height map for normal generation)
            
        Returns:
            Generated texture as PIL Image
        """
        pass
    
    def process_image(self, image: Image.Image) -> Image.Image:
        """Apply common processing steps to the generated image.
        
        Args:
            image: Input PIL Image
            
        Returns:
            Processed PIL Image
        """
        # Ensure correct resolution
        if image.size != (self.resolution.width, self.resolution.height):
            image = image.resize(
                (self.resolution.width, self.resolution.height),
                Image.Resampling.LANCZOS
            )
        
        # Convert to appropriate mode if needed
        if self.texture_type == TextureType.NORMAL:
            if image.mode != 'RGB':
                image = image.convert('RGB')
        
        return image
    
    def make_seamless(self, image: Image.Image, blend_width: int = 64) -> Image.Image:
        """Make the texture seamless by blending edges.
        
        Args:
            image: Input PIL Image
            blend_width: Width of the blending region in pixels
            
        Returns:
            Seamless PIL Image
        """
        if not self.seamless:
            return image
        
        # Import and use the advanced tessellation module
        from .tessellation import TessellationModule
        tess = TessellationModule()
        
        # Use the frequency blend method for best results
        return tess.make_seamless(image, blend_mode='frequency', blend_width=blend_width)