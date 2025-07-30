"""Normal map generation module."""

from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

from .base import TextureGenerator
from ..types.common import TextureType
from ..types.config import Config
from ..utils.filters import height_to_normal, enhance_details
from ..utils.logging import get_logger


logger = get_logger(__name__)


class NormalModule(TextureGenerator):
    """Generates normal maps from height or diffuse data."""
    
    @property
    def texture_type(self) -> TextureType:
        """Return the texture type this generator produces."""
        return TextureType.NORMAL
    
    def generate(self, input_data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Generate normal map from height data or create a default one.
        
        Args:
            input_data: Dictionary that may contain:
                - height_map: PIL Image or numpy array of height data
                - diffuse_map: PIL Image to derive normals from (if no height)
                
        Returns:
            Normal map as PIL Image (RGB)
        """
        logger.info(f"Generating normal map at {self.resolution}")
        
        # Get height map from input data
        height_map = None
        if input_data:
            if "height_map" in input_data:
                height_map = self._process_height_input(input_data["height_map"])
            elif "diffuse_map" in input_data:
                # Fall back to deriving from diffuse if no height map
                height_map = self._derive_height_from_diffuse(input_data["diffuse_map"])
        
        # If no height map available, create a neutral normal map
        if height_map is None:
            logger.warning("No height data provided, creating neutral normal map")
            return self._create_neutral_normal_map()
        
        # Get normal generation parameters
        if hasattr(self.material_properties, 'generation') and self.material_properties.generation:
            normal_config = self.material_properties.generation.normal
            strength = normal_config.strength
            blur_radius = normal_config.blur_radius
            invert_height = normal_config.invert_height
        else:
            # Fall back to legacy properties
            strength = self.material_properties.normal_strength or 1.0
            blur_radius = 0.0
            invert_height = False
        
        # Invert height if configured
        if invert_height:
            height_map = 1.0 - height_map
        
        # Convert height to normal
        normal_array = height_to_normal(
            height_map,
            strength=strength,
            invert_y=False,  # Use standard tangent space
            blur_radius=blur_radius
        )
        
        # Optional: Enhance details for more pronounced normals
        if strength > 1.5:
            normal_array = self._enhance_normal_details(normal_array)
        
        # Convert to PIL Image
        normal_image = Image.fromarray(
            (normal_array * 255).astype(np.uint8),
            mode='RGB'
        )
        
        # Apply post-processing
        normal_image = self.process_image(normal_image)
        
        # Make seamless if configured
        if self.seamless:
            normal_image = self.make_seamless(normal_image)
        
        logger.info("Normal map generation completed")
        return normal_image
    
    def _process_height_input(self, height_input: Any) -> np.ndarray:
        """Process height input to normalized numpy array.
        
        Args:
            height_input: PIL Image or numpy array
            
        Returns:
            Normalized height map as 2D numpy array (0-1)
        """
        if isinstance(height_input, Image.Image):
            # Convert PIL Image to grayscale numpy array
            if height_input.mode != 'L':
                height_input = height_input.convert('L')
            
            # Resize if needed
            if height_input.size != (self.resolution.width, self.resolution.height):
                height_input = height_input.resize(
                    (self.resolution.width, self.resolution.height),
                    Image.Resampling.LANCZOS
                )
            
            height_array = np.array(height_input, dtype=np.float32) / 255.0
        elif isinstance(height_input, np.ndarray):
            height_array = height_input.astype(np.float32)
            # Normalize if needed
            if height_array.max() > 1.0:
                height_array = height_array / 255.0
        else:
            raise ValueError(f"Unsupported height input type: {type(height_input)}")
        
        return height_array
    
    def _derive_height_from_diffuse(self, diffuse_map: Any) -> np.ndarray:
        """Derive approximate height from diffuse map using luminance.
        
        Args:
            diffuse_map: PIL Image or numpy array (RGB)
            
        Returns:
            Derived height map as 2D numpy array (0-1)
        """
        logger.info("Deriving height from diffuse map")
        
        if isinstance(diffuse_map, Image.Image):
            # Resize if needed
            if diffuse_map.size != (self.resolution.width, self.resolution.height):
                diffuse_map = diffuse_map.resize(
                    (self.resolution.width, self.resolution.height),
                    Image.Resampling.LANCZOS
                )
            diffuse_array = np.array(diffuse_map, dtype=np.float32) / 255.0
        else:
            diffuse_array = diffuse_map.astype(np.float32)
            if diffuse_array.max() > 1.0:
                diffuse_array = diffuse_array / 255.0
        
        # Convert to luminance (approximate height)
        if len(diffuse_array.shape) == 3:
            # Use standard luminance weights
            height = (
                0.299 * diffuse_array[:, :, 0] +
                0.587 * diffuse_array[:, :, 1] +
                0.114 * diffuse_array[:, :, 2]
            )
        else:
            height = diffuse_array
        
        # Invert if needed (darker = lower)
        height = 1.0 - height
        
        # Enhance contrast for better normal extraction
        height = np.power(height, 0.8)
        
        return height
    
    def _create_neutral_normal_map(self) -> Image.Image:
        """Create a neutral normal map (pointing straight up).
        
        Returns:
            Neutral normal map as PIL Image
        """
        # Create array filled with neutral normal color (0.5, 0.5, 1.0)
        normal_array = np.ones(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        normal_array[:, :, 0] = 0.5  # X (R)
        normal_array[:, :, 1] = 0.5  # Y (G)
        normal_array[:, :, 2] = 1.0  # Z (B)
        
        return Image.fromarray(
            (normal_array * 255).astype(np.uint8),
            mode='RGB'
        )
    
    def _enhance_normal_details(self, normal_array: np.ndarray) -> np.ndarray:
        """Enhance fine details in the normal map.
        
        Args:
            normal_array: Normal map as 3D array (0-1)
            
        Returns:
            Enhanced normal map
        """
        # Convert back to normal vectors
        normal_x = (normal_array[:, :, 0] * 2.0) - 1.0
        normal_y = (normal_array[:, :, 1] * 2.0) - 1.0
        normal_z = (normal_array[:, :, 2] * 2.0) - 1.0
        
        # Enhance X and Y components
        normal_x = enhance_details(normal_x, detail_strength=0.3)
        normal_y = enhance_details(normal_y, detail_strength=0.3)
        
        # Re-normalize
        magnitude = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        normal_x /= magnitude
        normal_y /= magnitude
        normal_z /= magnitude
        
        # Convert back to RGB encoding
        enhanced = np.stack([
            (normal_x + 1.0) * 0.5,
            (normal_y + 1.0) * 0.5,
            (normal_z + 1.0) * 0.5
        ], axis=-1)
        
        return enhanced