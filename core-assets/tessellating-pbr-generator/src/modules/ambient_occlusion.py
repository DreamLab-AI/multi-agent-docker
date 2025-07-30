"""Ambient occlusion generation module.

Generates ambient occlusion (AO) maps that simulate shadows in crevices and cavities.
AO maps enhance the perception of depth and detail in 3D models by darkening areas
where ambient light would naturally be occluded.
"""

from typing import Optional, Dict, Any
from PIL import Image
import numpy as np
from scipy import ndimage

from .base import TextureGenerator
from ..types.common import TextureType
from ..types.config import Config
from ..utils.filters import gaussian_blur
from ..utils.logging import get_logger


logger = get_logger(__name__)


class AmbientOcclusionModule(TextureGenerator):
    """Generates ambient occlusion maps from height data.
    
    Ambient occlusion maps encode accessibility to ambient light:
    - White (1.0) = fully exposed to ambient light
    - Black (0.0) = fully occluded from ambient light
    
    This module derives AO from height maps using cavity detection
    and ambient shadow simulation.
    """
    
    def __init__(self, config: Config):
        """Initialize the ambient occlusion module.
        
        Args:
            config: Configuration object with material properties
        """
        super().__init__(config)
        
        # AO strength/intensity from config
        self.ao_strength = self.material_properties.ao_intensity
        
        # Material-specific AO characteristics
        self.material_presets = {
            'stone': {'cavity_scale': 2.0, 'global_scale': 4.0, 'min_ao': 0.3},
            'brick': {'cavity_scale': 1.5, 'global_scale': 3.0, 'min_ao': 0.2},
            'wood': {'cavity_scale': 1.0, 'global_scale': 2.0, 'min_ao': 0.5},
            'metal': {'cavity_scale': 0.5, 'global_scale': 1.0, 'min_ao': 0.7},
            'fabric': {'cavity_scale': 0.8, 'global_scale': 1.5, 'min_ao': 0.6},
            'concrete': {'cavity_scale': 1.8, 'global_scale': 3.5, 'min_ao': 0.35}
        }
    
    @property
    def texture_type(self) -> TextureType:
        """Return the texture type this generator produces."""
        return TextureType.AMBIENT_OCCLUSION
    
    def generate(self, input_data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Generate ambient occlusion map from height data.
        
        Args:
            input_data: Dictionary that may contain:
                - height_map: PIL Image or numpy array of height data
                - diffuse_map: PIL Image (fallback if no height map)
                
        Returns:
            Ambient occlusion map as grayscale PIL Image
        """
        logger.info(f"Generating ambient occlusion map at {self.resolution}")
        
        # Get height map from input data
        height_map = None
        if input_data:
            if "height_map" in input_data:
                height_map = self._process_height_input(input_data["height_map"])
            elif "diffuse_map" in input_data:
                # Derive from diffuse if no height map
                height_map = self._derive_height_from_diffuse(input_data["diffuse_map"])
        
        if height_map is None:
            logger.warning("No height data provided, creating neutral AO map")
            return self._create_neutral_ao_map()
        
        # Generate AO from height
        ao_array = self._calculate_ambient_occlusion(height_map)
        
        # Apply material-specific adjustments
        ao_array = self._apply_material_properties(ao_array)
        
        # Apply AO strength
        ao_array = self._apply_ao_strength(ao_array)
        
        # Ensure values are in valid range
        ao_array = np.clip(ao_array, 0.0, 1.0)
        
        # Convert to PIL Image
        ao_image = Image.fromarray(
            (ao_array * 255).astype(np.uint8),
            mode='L'
        )
        
        # Apply post-processing
        ao_image = self.process_image(ao_image)
        
        # Make seamless if configured
        if self.seamless:
            ao_image = self.make_seamless(ao_image)
        
        logger.info("Ambient occlusion map generation completed")
        return ao_image
    
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
        """Derive approximate height from diffuse map.
        
        Args:
            diffuse_map: PIL Image or numpy array (RGB)
            
        Returns:
            Derived height map as 2D numpy array (0-1)
        """
        logger.info("Deriving height from diffuse for AO calculation")
        
        if isinstance(diffuse_map, Image.Image):
            # Resize if needed
            if diffuse_map.size != (self.resolution.width, self.resolution.height):
                diffuse_map = diffuse_map.resize(
                    (self.resolution.width, self.resolution.height),
                    Image.Resampling.LANCZOS
                )
            
            # Convert to RGB if needed
            if diffuse_map.mode != 'RGB':
                diffuse_map = diffuse_map.convert('RGB')
            
            diffuse_array = np.array(diffuse_map, dtype=np.float32) / 255.0
        else:
            diffuse_array = diffuse_map.astype(np.float32)
            if diffuse_array.max() > 1.0:
                diffuse_array = diffuse_array / 255.0
        
        # Convert to luminance
        if len(diffuse_array.shape) == 3:
            luminance = (
                0.299 * diffuse_array[:, :, 0] +
                0.587 * diffuse_array[:, :, 1] +
                0.114 * diffuse_array[:, :, 2]
            )
        else:
            luminance = diffuse_array
        
        # Invert (darker = lower)
        height = 1.0 - luminance
        
        return height
    
    def _calculate_ambient_occlusion(self, height_map: np.ndarray) -> np.ndarray:
        """Calculate ambient occlusion from height map.
        
        This uses multiple techniques:
        1. Cavity detection from height derivatives
        2. Multi-scale occlusion simulation
        3. Gradient-based shading
        
        Args:
            height_map: Normalized height array (0-1)
            
        Returns:
            Ambient occlusion array (0-1)
        """
        # Get material preset
        preset = self.material_presets.get(
            self.config.material,
            {'cavity_scale': 1.5, 'global_scale': 3.0, 'min_ao': 0.4}
        )
        
        # 1. Calculate cavity AO (fine details)
        cavity_ao = self._calculate_cavity_ao(height_map, preset['cavity_scale'])
        
        # 2. Calculate global AO (larger features)
        global_ao = self._calculate_global_ao(height_map, preset['global_scale'])
        
        # 3. Calculate gradient-based shading
        gradient_ao = self._calculate_gradient_ao(height_map)
        
        # Combine different AO components
        ao = cavity_ao * 0.4 + global_ao * 0.4 + gradient_ao * 0.2
        
        # Apply minimum AO to prevent pure black
        min_ao = preset['min_ao']
        ao = ao * (1.0 - min_ao) + min_ao
        
        return ao
    
    def _calculate_cavity_ao(self, height_map: np.ndarray, scale: float) -> np.ndarray:
        """Calculate fine-scale cavity ambient occlusion.
        
        Args:
            height_map: Height array
            scale: Scale factor for cavity detection
            
        Returns:
            Cavity AO array
        """
        # Blur height map at cavity scale
        blurred = gaussian_blur(height_map, sigma=scale)
        
        # Find cavities (areas lower than surroundings)
        cavity_depth = blurred - height_map
        cavity_depth = np.maximum(cavity_depth, 0)
        
        # Convert depth to occlusion
        cavity_ao = 1.0 - cavity_depth * 10.0
        cavity_ao = np.clip(cavity_ao, 0, 1)
        
        return cavity_ao
    
    def _calculate_global_ao(self, height_map: np.ndarray, scale: float) -> np.ndarray:
        """Calculate large-scale ambient occlusion.
        
        Args:
            height_map: Height array
            scale: Scale factor for global features
            
        Returns:
            Global AO array
        """
        # Multiple blur passes for smooth falloff
        ao = height_map.copy()
        
        for i in range(3):
            blur_sigma = scale * (i + 1)
            blurred = gaussian_blur(height_map, sigma=blur_sigma)
            
            # Accumulate occlusion
            ao = ao * 0.7 + blurred * 0.3
        
        # Enhance contrast
        ao = np.power(ao, 1.5)
        
        return ao
    
    def _calculate_gradient_ao(self, height_map: np.ndarray) -> np.ndarray:
        """Calculate gradient-based ambient occlusion.
        
        Steep slopes receive more occlusion.
        
        Args:
            height_map: Height array
            
        Returns:
            Gradient AO array
        """
        # Calculate height gradients
        grad_x = ndimage.sobel(height_map, axis=0)
        grad_y = ndimage.sobel(height_map, axis=1)
        
        # Gradient magnitude
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Normalize and invert (high gradient = more occlusion)
        gradient_mag = gradient_mag / (gradient_mag.max() + 1e-6)
        gradient_ao = 1.0 - gradient_mag * 0.5
        
        # Smooth the result
        gradient_ao = gaussian_blur(gradient_ao, sigma=1.0)
        
        return gradient_ao
    
    def _apply_material_properties(self, ao: np.ndarray) -> np.ndarray:
        """Apply material-specific adjustments to AO.
        
        Args:
            ao: Raw AO array
            
        Returns:
            Adjusted AO array
        """
        if self.config.material == 'stone' or self.config.material == 'brick':
            # Enhance mortar lines and cracks
            ao = self._enhance_crevices(ao)
            
        elif self.config.material == 'wood':
            # Soften AO along grain direction
            ao = self._soften_along_grain(ao)
            
        elif self.config.material == 'metal':
            # Metals have subtle AO
            ao = ao * 0.5 + 0.5  # Compress range
            
        elif self.config.material == 'fabric':
            # Add weave pattern to AO
            ao = self._add_fabric_weave_ao(ao)
        
        return ao
    
    def _apply_ao_strength(self, ao: np.ndarray) -> np.ndarray:
        """Apply the configured AO strength/intensity.
        
        Args:
            ao: AO array
            
        Returns:
            AO with applied strength
        """
        # Blend with white based on strength
        # strength=0 -> pure white, strength=1 -> full AO
        # Use ao_intensity if available (from advanced config), otherwise ao_strength
        intensity = getattr(self, 'ao_intensity', self.ao_strength)
        ao = 1.0 - (1.0 - ao) * intensity
        
        return ao
    
    def _enhance_crevices(self, ao: np.ndarray) -> np.ndarray:
        """Enhance AO in crevices for stone/brick materials.
        
        Args:
            ao: AO array
            
        Returns:
            Enhanced AO
        """
        # Find deep areas
        deep_mask = ao < 0.5
        
        # Enhance occlusion in deep areas
        ao[deep_mask] = ao[deep_mask] * 0.8
        
        return ao
    
    def _soften_along_grain(self, ao: np.ndarray) -> np.ndarray:
        """Soften AO along wood grain direction.
        
        Args:
            ao: AO array
            
        Returns:
            Softened AO
        """
        from scipy.ndimage import gaussian_filter1d
        
        # Assume horizontal grain
        softened = gaussian_filter1d(ao, sigma=2, axis=1)
        
        # Blend with original
        ao = ao * 0.6 + softened * 0.4
        
        return ao
    
    def _add_fabric_weave_ao(self, ao: np.ndarray) -> np.ndarray:
        """Add fabric weave pattern to AO.
        
        Args:
            ao: AO array
            
        Returns:
            AO with weave pattern
        """
        # Create weave pattern
        y, x = np.ogrid[:ao.shape[0], :ao.shape[1]]
        
        weave = (
            np.sin(x * 0.1) * 0.05 +
            np.sin(y * 0.1) * 0.05
        )
        
        # Subtract from AO (deepen weave)
        ao = ao - weave * 0.1
        
        return np.clip(ao, 0, 1)
    
    def _create_neutral_ao_map(self) -> Image.Image:
        """Create a neutral (mostly white) AO map.
        
        Returns:
            Neutral AO map as PIL Image
        """
        # Create array filled with mostly white (0.9)
        ao_array = np.full(
            (self.resolution.height, self.resolution.width),
            0.9,
            dtype=np.float32
        )
        
        # Add very subtle variation
        noise = np.random.normal(0, 0.02, ao_array.shape)
        ao_array += noise
        ao_array = np.clip(ao_array, 0, 1)
        
        return Image.fromarray(
            (ao_array * 255).astype(np.uint8),
            mode='L'
        )