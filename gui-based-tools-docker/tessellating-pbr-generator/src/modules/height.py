"""Height/displacement map generation module.

Generates height/displacement maps from diffuse textures.
Height maps represent surface elevation and are used for:
- Normal map generation
- Displacement mapping in 3D rendering
- Ambient occlusion calculation
"""

from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

from .base import TextureGenerator
from ..types.common import TextureType
from ..types.config import Config
from ..utils.filters import gaussian_blur, enhance_details
from ..utils.logging import get_logger


logger = get_logger(__name__)


class HeightModule(TextureGenerator):
    """Generates height maps from diffuse textures.
    
    Height maps encode surface elevation where:
    - White (1.0) = highest elevation
    - Black (0.0) = lowest elevation
    
    This module derives height from diffuse luminance with material-specific
    adjustments for realistic displacement.
    """
    
    def __init__(self, config: Config):
        """Initialize the height module.
        
        Args:
            config: Configuration object with material properties
        """
        super().__init__(config)
        
        # Get height config from advanced or legacy properties
        if hasattr(self.material_properties, 'generation') and self.material_properties.generation:
            height_config = self.material_properties.generation.height
            self.depth_scale = height_config.depth_scale
            self.blur_radius = height_config.blur_radius
            # Keep height_scale for backward compatibility
            self.height_scale = self.depth_scale
        else:
            # Legacy support from additional_properties
            self.height_scale = self.material_properties.additional_properties.get(
                'height_scale', 1.0
            )
            self.depth_scale = self.height_scale
            self.blur_radius = 0.0
        
        # Material-specific presets for height interpretation
        self.material_presets = {
            'stone': {'invert': True, 'contrast': 1.5, 'blur': 1.0},
            'brick': {'invert': True, 'contrast': 1.8, 'blur': 0.5},
            'wood': {'invert': True, 'contrast': 1.2, 'blur': 2.0},
            'metal': {'invert': False, 'contrast': 0.5, 'blur': 3.0},
            'fabric': {'invert': True, 'contrast': 0.8, 'blur': 1.5},
            'concrete': {'invert': True, 'contrast': 1.3, 'blur': 1.0}
        }
    
    @property
    def texture_type(self) -> TextureType:
        """Return the texture type this generator produces."""
        return TextureType.HEIGHT
    
    def generate(self, input_data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Generate height map from diffuse texture.
        
        Args:
            input_data: Dictionary that may contain:
                - diffuse_map: PIL Image of the diffuse texture
                
        Returns:
            Height map as grayscale PIL Image
        """
        logger.info(f"Generating height map at {self.resolution}")
        
        # Get diffuse map from input data
        diffuse_map = None
        if input_data and "diffuse_map" in input_data:
            diffuse_map = input_data["diffuse_map"]
        
        if diffuse_map is None:
            logger.warning("No diffuse map provided, creating neutral height map")
            return self._create_neutral_height_map()
        
        # Process diffuse to extract height
        height_array = self._extract_height_from_diffuse(diffuse_map)
        
        # Apply material-specific processing
        height_array = self._process_for_material(height_array)
        
        # Apply height scale
        if self.height_scale != 1.0:
            height_array = self._apply_height_scale(height_array)
        
        # Add surface detail
        height_array = self._add_surface_detail(height_array)
        
        # Ensure values are in valid range
        height_array = np.clip(height_array, 0.0, 1.0)
        
        # Convert to PIL Image
        height_image = Image.fromarray(
            (height_array * 255).astype(np.uint8),
            mode='L'
        )
        
        # Apply post-processing
        height_image = self.process_image(height_image)
        
        # Make seamless if configured
        if self.seamless:
            height_image = self.make_seamless(height_image)
        
        logger.info("Height map generation completed")
        return height_image
    
    def _extract_height_from_diffuse(self, diffuse_map: Image.Image) -> np.ndarray:
        """Extract height information from diffuse map using luminance.
        
        Args:
            diffuse_map: PIL Image (RGB)
            
        Returns:
            Height data as 2D numpy array (0-1)
        """
        # Ensure correct size
        if diffuse_map.size != (self.resolution.width, self.resolution.height):
            diffuse_map = diffuse_map.resize(
                (self.resolution.width, self.resolution.height),
                Image.Resampling.LANCZOS
            )
        
        # Convert to RGB if needed
        if diffuse_map.mode != 'RGB':
            diffuse_map = diffuse_map.convert('RGB')
        
        # Convert to numpy array
        diffuse_array = np.array(diffuse_map, dtype=np.float32) / 255.0
        
        # Extract luminance using perceptual weights
        luminance = (
            0.299 * diffuse_array[:, :, 0] +
            0.587 * diffuse_array[:, :, 1] +
            0.114 * diffuse_array[:, :, 2]
        )
        
        return luminance
    
    def _process_for_material(self, height: np.ndarray) -> np.ndarray:
        """Apply material-specific processing to height data.
        
        Args:
            height: Height array (0-1)
            
        Returns:
            Processed height array
        """
        # Get material preset
        preset = self.material_presets.get(
            self.config.material,
            {'invert': True, 'contrast': 1.0, 'blur': 1.0}
        )
        
        # Invert if needed (dark areas = cavities for most materials)
        if preset['invert']:
            height = 1.0 - height
        
        # Apply initial blur to reduce noise
        blur_sigma = preset.get('blur', 1.0)
        # Override with configured blur if available
        if hasattr(self, 'blur_radius') and self.blur_radius > 0:
            blur_sigma = self.blur_radius
        
        if blur_sigma > 0:
            height = gaussian_blur(height, sigma=blur_sigma)
        
        # Apply contrast enhancement
        if preset['contrast'] != 1.0:
            # Enhance contrast around midpoint
            height = 0.5 + (height - 0.5) * preset['contrast']
        
        # Material-specific adjustments
        if self.config.material == 'stone' or self.config.material == 'brick':
            # Enhance cracks and mortar lines
            height = self._enhance_cracks(height)
            
        elif self.config.material == 'wood':
            # Enhance wood grain
            height = self._enhance_wood_grain(height)
            
        elif self.config.material == 'metal':
            # Metals have minimal height variation
            height = height * 0.3 + 0.35  # Compress to middle range
            
        elif self.config.material == 'fabric':
            # Fabric has consistent weave depth
            height = self._enhance_fabric_weave(height)
        
        return height
    
    def _apply_height_scale(self, height: np.ndarray) -> np.ndarray:
        """Apply height scale factor while preserving relative heights.
        
        Args:
            height: Height array (0-1)
            
        Returns:
            Scaled height array
        """
        # Find the mean height
        mean_height = np.mean(height)
        
        # Scale around the mean to preserve relative heights
        scaled = mean_height + (height - mean_height) * self.height_scale
        
        # Ensure we don't exceed valid range
        return np.clip(scaled, 0.0, 1.0)
    
    def _add_surface_detail(self, height: np.ndarray) -> np.ndarray:
        """Add fine surface detail to the height map.
        
        Args:
            height: Height array (0-1)
            
        Returns:
            Height with added detail
        """
        # Extract and enhance high-frequency details
        detailed = enhance_details(height, detail_strength=0.3, blur_sigma=3.0)
        
        # Blend with original
        height = height * 0.7 + detailed * 0.3
        
        return height
    
    def _enhance_cracks(self, height: np.ndarray) -> np.ndarray:
        """Enhance crack-like features for stone/brick materials.
        
        Args:
            height: Height array
            
        Returns:
            Enhanced height array
        """
        # Use edge detection to find potential cracks
        from scipy import ndimage
        edges = ndimage.sobel(height)
        edges = np.abs(edges)
        
        # Darken areas with high edge response (cracks)
        crack_mask = edges > np.percentile(edges, 90)
        height[crack_mask] *= 0.6
        
        # Blur slightly to smooth transitions
        height = gaussian_blur(height, sigma=0.5)
        
        return height
    
    def _enhance_wood_grain(self, height: np.ndarray) -> np.ndarray:
        """Enhance wood grain patterns.
        
        Args:
            height: Height array
            
        Returns:
            Enhanced height array
        """
        # Apply directional blur to emphasize grain
        from scipy.ndimage import gaussian_filter1d
        
        # Assume horizontal grain (could be parameterized)
        grain_enhanced = gaussian_filter1d(height, sigma=3, axis=1)
        
        # Blend with original to preserve some detail
        height = height * 0.4 + grain_enhanced * 0.6
        
        # Add subtle variation along grain
        noise = np.random.normal(0, 0.02, height.shape)
        height += noise
        
        return np.clip(height, 0, 1)
    
    def _enhance_fabric_weave(self, height: np.ndarray) -> np.ndarray:
        """Enhance fabric weave patterns.
        
        Args:
            height: Height array
            
        Returns:
            Enhanced height array
        """
        # Create a subtle grid pattern for weave
        y, x = np.ogrid[:height.shape[0], :height.shape[1]]
        
        # Create crossing sine waves for warp and weft
        weave_pattern = (
            np.sin(x * 0.1) * 0.05 +
            np.sin(y * 0.1) * 0.05
        )
        
        # Add weave pattern to height
        height += weave_pattern
        
        # Compress range slightly
        height = height * 0.8 + 0.1
        
        return np.clip(height, 0, 1)
    
    def _create_neutral_height_map(self) -> Image.Image:
        """Create a neutral (mid-gray) height map.
        
        Returns:
            Neutral height map as PIL Image
        """
        # Create array filled with middle gray (0.5)
        height_array = np.full(
            (self.resolution.height, self.resolution.width),
            0.5,
            dtype=np.float32
        )
        
        # Add very subtle noise for realism
        noise = np.random.normal(0, 0.01, height_array.shape)
        height_array += noise
        height_array = np.clip(height_array, 0, 1)
        
        return Image.fromarray(
            (height_array * 255).astype(np.uint8),
            mode='L'
        )