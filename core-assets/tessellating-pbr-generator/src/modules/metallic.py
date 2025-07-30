"""Metallic texture generation module.

Generates metallic maps for PBR workflows.
Metallic maps control the metallic vs. dielectric properties of materials:
- White (1.0) = fully metallic (conductive)
- Black (0.0) = fully dielectric (non-conductive)
"""

from typing import Optional, Dict, Any
from PIL import Image
import numpy as np

from .base import TextureGenerator
from ..types.common import TextureType
from ..types.config import Config
from ..utils.filters import gaussian_blur
from ..utils.logging import get_logger


logger = get_logger(__name__)


class MetallicModule(TextureGenerator):
    """Generates metallic maps for PBR materials.
    
    The metallic map is typically a uniform value for most materials since
    surfaces are usually either metallic or non-metallic. Mixed materials
    (like rusted metal or metal with paint) can have varying metallic values.
    """
    
    def __init__(self, config: Config):
        """Initialize the metallic module.
        
        Args:
            config: Configuration object with material properties
        """
        super().__init__(config)
        
        # Get metallic config from advanced or legacy properties
        if hasattr(self.material_properties, 'generation') and self.material_properties.generation:
            metallic_config = self.material_properties.generation.metallic
            self.metallic_value = metallic_config.base_value
            self.metallic_variation = metallic_config.variation
            self.metallic_patterns = metallic_config.patterns
        else:
            # Legacy support
            self.metallic_value = self.material_properties.metallic_value or 0.0
            self.metallic_variation = 0.0
            self.metallic_patterns = None
        
        # Material-specific metallic patterns
        self.material_presets = {
            'metal': {
                'base_metallic': 1.0,
                'variation': 0.05,
                'rust_chance': 0.1,
                'pattern': 'uniform'
            },
            'stone': {
                'base_metallic': 0.0,
                'variation': 0.0,
                'mineral_chance': 0.05,
                'pattern': 'uniform'
            },
            'wood': {
                'base_metallic': 0.0,
                'variation': 0.0,
                'pattern': 'uniform'
            },
            'concrete': {
                'base_metallic': 0.0,
                'variation': 0.02,
                'rebar_chance': 0.02,
                'pattern': 'uniform'
            },
            'fabric': {
                'base_metallic': 0.0,
                'variation': 0.0,
                'thread_metallic': 0.1,
                'pattern': 'uniform'
            },
            'plastic': {
                'base_metallic': 0.0,
                'variation': 0.0,
                'pattern': 'uniform'
            },
            'gold': {
                'base_metallic': 1.0,
                'variation': 0.02,
                'pattern': 'uniform'
            },
            'copper': {
                'base_metallic': 1.0,
                'variation': 0.03,
                'oxidation_chance': 0.15,
                'pattern': 'patina'
            },
            'brass': {
                'base_metallic': 1.0,
                'variation': 0.02,
                'tarnish_chance': 0.1,
                'pattern': 'uniform'
            }
        }
    
    @property
    def texture_type(self) -> TextureType:
        """Return the texture type this generator produces."""
        return TextureType.METALLIC
    
    def generate(self, input_data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Generate metallic map.
        
        Args:
            input_data: Dictionary that may contain:
                - diffuse_map: PIL Image for deriving wear patterns
                - height_map: PIL Image for surface variation
                
        Returns:
            Metallic map as grayscale PIL Image
        """
        logger.info(f"Generating metallic map at {self.resolution}")
        
        # Get preset for material
        preset = self.material_presets.get(
            self.config.material,
            {'base_metallic': self.metallic_value, 'variation': 0.0, 'pattern': 'uniform'}
        )
        
        # Override with config value if explicitly set and not default
        if self.metallic_value != 0.0 or preset['base_metallic'] == 0.0:
            base_metallic = self.metallic_value
        else:
            base_metallic = preset['base_metallic']
        
        # Use configured variation if available
        if hasattr(self, 'metallic_variation') and self.metallic_variation > 0:
            preset['variation'] = self.metallic_variation
        
        # Generate base metallic map
        metallic_array = self._generate_base_metallic(base_metallic, preset)
        
        # Apply material-specific patterns
        if preset['pattern'] != 'uniform' or preset.get('variation', 0) > 0:
            metallic_array = self._apply_material_pattern(
                metallic_array, preset, input_data
            )
        
        # Add wear and weathering effects for metals
        if base_metallic > 0.5 and input_data:
            metallic_array = self._add_wear_effects(metallic_array, preset, input_data)
        
        # Ensure values are in valid range
        metallic_array = np.clip(metallic_array, 0.0, 1.0)
        
        # Convert to PIL Image
        metallic_image = Image.fromarray(
            (metallic_array * 255).astype(np.uint8),
            mode='L'
        )
        
        # Apply post-processing
        metallic_image = self.process_image(metallic_image)
        
        # Make seamless if configured
        if self.seamless:
            metallic_image = self.make_seamless(metallic_image)
        
        logger.info("Metallic map generation completed")
        return metallic_image
    
    def _generate_base_metallic(self, base_value: float, preset: Dict) -> np.ndarray:
        """Generate base metallic array with optional variation.
        
        Args:
            base_value: Base metallic value (0-1)
            preset: Material preset dictionary
            
        Returns:
            Base metallic array
        """
        # Create uniform base
        metallic = np.full(
            (self.resolution.height, self.resolution.width),
            base_value,
            dtype=np.float32
        )
        
        # Add subtle variation if specified
        variation = preset.get('variation', 0.0)
        if variation > 0:
            noise = np.random.normal(0, variation, metallic.shape)
            metallic += noise
            metallic = np.clip(metallic, 0, 1)
        
        # Apply custom patterns if configured
        if hasattr(self, 'metallic_patterns') and self.metallic_patterns:
            metallic = self._apply_custom_patterns(metallic, self.metallic_patterns)
        
        return metallic
    
    def _apply_material_pattern(
        self, 
        metallic: np.ndarray, 
        preset: Dict,
        input_data: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Apply material-specific patterns to metallic map.
        
        Args:
            metallic: Base metallic array
            preset: Material preset
            input_data: Optional input textures
            
        Returns:
            Metallic array with patterns
        """
        pattern_type = preset.get('pattern', 'uniform')
        
        if pattern_type == 'patina':
            # Copper patina pattern
            metallic = self._add_patina_pattern(metallic, preset)
            
        elif self.config.material == 'concrete' and preset.get('rebar_chance', 0) > 0:
            # Exposed rebar in concrete
            metallic = self._add_rebar_exposure(metallic, preset)
            
        elif self.config.material == 'stone' and preset.get('mineral_chance', 0) > 0:
            # Metallic minerals in stone
            metallic = self._add_mineral_veins(metallic, preset)
            
        elif self.config.material == 'fabric' and preset.get('thread_metallic', 0) > 0:
            # Metallic threads in fabric
            metallic = self._add_metallic_threads(metallic, preset)
        
        return metallic
    
    def _add_wear_effects(
        self, 
        metallic: np.ndarray, 
        preset: Dict,
        input_data: Dict[str, Any]
    ) -> np.ndarray:
        """Add wear and weathering effects to metallic surfaces.
        
        Args:
            metallic: Metallic array
            preset: Material preset
            input_data: Input textures (diffuse, height)
            
        Returns:
            Metallic with wear effects
        """
        # Get height map for wear patterns
        height_map = None
        if "height_map" in input_data:
            height_map = self._process_height_input(input_data["height_map"])
        elif "diffuse_map" in input_data:
            # Derive from diffuse luminance
            height_map = self._derive_height_from_diffuse(input_data["diffuse_map"])
        
        if height_map is not None:
            # Rust/oxidation on exposed areas
            if preset.get('rust_chance', 0) > 0:
                metallic = self._add_rust_pattern(metallic, height_map, preset['rust_chance'])
            
            # Oxidation for copper
            if preset.get('oxidation_chance', 0) > 0:
                metallic = self._add_oxidation(metallic, height_map, preset['oxidation_chance'])
            
            # Tarnish for brass
            if preset.get('tarnish_chance', 0) > 0:
                metallic = self._add_tarnish(metallic, height_map, preset['tarnish_chance'])
        
        return metallic
    
    def _add_patina_pattern(self, metallic: np.ndarray, preset: Dict) -> np.ndarray:
        """Add patina pattern for aged copper.
        
        Args:
            metallic: Metallic array
            preset: Material preset
            
        Returns:
            Metallic with patina
        """
        # Create organic patina pattern
        y, x = np.ogrid[:metallic.shape[0], :metallic.shape[1]]
        
        # Multiple scales of noise for organic look
        pattern = np.zeros_like(metallic)
        for scale in [10, 20, 40]:
            noise = np.sin(x / scale) * np.cos(y / scale)
            pattern += noise * (1.0 / scale)
        
        # Normalize and threshold
        pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min())
        patina_mask = pattern > 0.6
        
        # Reduce metallic where patina forms
        metallic[patina_mask] *= 0.3
        
        # Smooth transitions
        metallic = gaussian_blur(metallic, sigma=2.0)
        
        return metallic
    
    def _add_rebar_exposure(self, metallic: np.ndarray, preset: Dict) -> np.ndarray:
        """Add exposed rebar pattern in concrete.
        
        Args:
            metallic: Metallic array
            preset: Material preset
            
        Returns:
            Metallic with rebar
        """
        rebar_chance = preset.get('rebar_chance', 0.02)
        
        # Create random cracks where rebar might show
        crack_mask = np.random.random(metallic.shape) < rebar_chance
        
        # Dilate to create crack-like patterns
        from scipy.ndimage import binary_dilation
        structure = np.ones((3, 3))
        crack_mask = binary_dilation(crack_mask, structure=structure, iterations=2)
        
        # Rebar is metallic
        metallic[crack_mask] = 0.9
        
        # Blur edges slightly
        metallic = gaussian_blur(metallic, sigma=0.5)
        
        return metallic
    
    def _add_mineral_veins(self, metallic: np.ndarray, preset: Dict) -> np.ndarray:
        """Add metallic mineral veins in stone.
        
        Args:
            metallic: Metallic array
            preset: Material preset
            
        Returns:
            Metallic with mineral veins
        """
        mineral_chance = preset.get('mineral_chance', 0.05)
        
        # Create vein-like patterns
        y, x = np.ogrid[:metallic.shape[0], :metallic.shape[1]]
        
        # Sinusoidal veins
        veins = np.sin(x * 0.02 + np.sin(y * 0.01) * 2) * \
                np.cos(y * 0.02 + np.cos(x * 0.01) * 2)
        
        # Threshold and add noise
        vein_mask = veins > 0.8
        vein_mask = vein_mask & (np.random.random(metallic.shape) < mineral_chance)
        
        # Minerals have slight metallic properties
        metallic[vein_mask] = 0.2
        
        return metallic
    
    def _add_metallic_threads(self, metallic: np.ndarray, preset: Dict) -> np.ndarray:
        """Add metallic thread pattern in fabric.
        
        Args:
            metallic: Metallic array
            preset: Material preset
            
        Returns:
            Metallic with thread pattern
        """
        thread_metallic = preset.get('thread_metallic', 0.1)
        
        # Create woven pattern
        y, x = np.ogrid[:metallic.shape[0], :metallic.shape[1]]
        
        # Horizontal and vertical threads
        h_threads = np.sin(y * 0.5) > 0.9
        v_threads = np.sin(x * 0.5) > 0.9
        
        # Some threads are metallic
        thread_mask = (h_threads | v_threads) & (np.random.random(metallic.shape) < 0.3)
        
        metallic[thread_mask] = thread_metallic
        
        return metallic
    
    def _add_rust_pattern(
        self, 
        metallic: np.ndarray, 
        height_map: np.ndarray,
        rust_chance: float
    ) -> np.ndarray:
        """Add rust pattern to metal, reducing metallic value.
        
        Args:
            metallic: Metallic array
            height_map: Height map for wear patterns
            rust_chance: Probability of rust
            
        Returns:
            Metallic with rust
        """
        # Rust forms in low areas and edges
        edges = self._detect_edges(height_map)
        low_areas = height_map < np.percentile(height_map, 30)
        
        # Combine conditions
        rust_prone = edges | low_areas
        rust_mask = rust_prone & (np.random.random(metallic.shape) < rust_chance)
        
        # Expand rust patches
        from scipy.ndimage import binary_dilation
        rust_mask = binary_dilation(rust_mask, iterations=3)
        
        # Rust is non-metallic
        metallic[rust_mask] *= 0.1
        
        # Smooth transitions
        metallic = gaussian_blur(metallic, sigma=1.5)
        
        return metallic
    
    def _add_oxidation(
        self, 
        metallic: np.ndarray, 
        height_map: np.ndarray,
        oxidation_chance: float
    ) -> np.ndarray:
        """Add oxidation pattern to copper.
        
        Args:
            metallic: Metallic array
            height_map: Height map
            oxidation_chance: Probability of oxidation
            
        Returns:
            Metallic with oxidation
        """
        # Oxidation forms gradually from edges
        edges = self._detect_edges(height_map)
        
        # Create gradual oxidation pattern
        from scipy.ndimage import distance_transform_edt
        edge_distance = distance_transform_edt(~edges)
        edge_distance = edge_distance / edge_distance.max()
        
        # Oxidation probability decreases with distance from edges
        oxidation_prob = (1 - edge_distance) * oxidation_chance
        oxidation_mask = np.random.random(metallic.shape) < oxidation_prob
        
        # Oxidized copper is less metallic
        metallic[oxidation_mask] *= 0.4
        
        return metallic
    
    def _add_tarnish(
        self, 
        metallic: np.ndarray, 
        height_map: np.ndarray,
        tarnish_chance: float
    ) -> np.ndarray:
        """Add tarnish pattern to brass.
        
        Args:
            metallic: Metallic array
            height_map: Height map
            tarnish_chance: Probability of tarnish
            
        Returns:
            Metallic with tarnish
        """
        # Tarnish in exposed areas
        exposed = height_map > np.percentile(height_map, 70)
        tarnish_mask = exposed & (np.random.random(metallic.shape) < tarnish_chance)
        
        # Tarnish reduces metallic slightly
        metallic[tarnish_mask] *= 0.7
        
        # Add some variation
        noise = np.random.normal(0, 0.05, metallic.shape)
        metallic += noise
        
        return np.clip(metallic, 0, 1)
    
    def _process_height_input(self, height_input: Any) -> np.ndarray:
        """Process height input to normalized numpy array.
        
        Args:
            height_input: PIL Image or numpy array
            
        Returns:
            Normalized height map as 2D numpy array (0-1)
        """
        if isinstance(height_input, Image.Image):
            if height_input.mode != 'L':
                height_input = height_input.convert('L')
            
            if height_input.size != (self.resolution.width, self.resolution.height):
                height_input = height_input.resize(
                    (self.resolution.width, self.resolution.height),
                    Image.Resampling.LANCZOS
                )
            
            height_array = np.array(height_input, dtype=np.float32) / 255.0
        elif isinstance(height_input, np.ndarray):
            height_array = height_input.astype(np.float32)
            if height_array.max() > 1.0:
                height_array = height_array / 255.0
        else:
            raise ValueError(f"Unsupported height input type: {type(height_input)}")
        
        return height_array
    
    def _derive_height_from_diffuse(self, diffuse_map: Any) -> np.ndarray:
        """Derive height from diffuse luminance.
        
        Args:
            diffuse_map: PIL Image or numpy array
            
        Returns:
            Height array
        """
        if isinstance(diffuse_map, Image.Image):
            if diffuse_map.size != (self.resolution.width, self.resolution.height):
                diffuse_map = diffuse_map.resize(
                    (self.resolution.width, self.resolution.height),
                    Image.Resampling.LANCZOS
                )
            
            if diffuse_map.mode != 'RGB':
                diffuse_map = diffuse_map.convert('RGB')
            
            diffuse_array = np.array(diffuse_map, dtype=np.float32) / 255.0
        else:
            diffuse_array = diffuse_map.astype(np.float32)
            if diffuse_array.max() > 1.0:
                diffuse_array = diffuse_array / 255.0
        
        # Extract luminance
        if len(diffuse_array.shape) == 3:
            luminance = (
                0.299 * diffuse_array[:, :, 0] +
                0.587 * diffuse_array[:, :, 1] +
                0.114 * diffuse_array[:, :, 2]
            )
        else:
            luminance = diffuse_array
        
        # Invert for height
        return 1.0 - luminance
    
    def _apply_custom_patterns(self, metallic: np.ndarray, patterns: Dict[str, Any]) -> np.ndarray:
        """Apply custom metallic patterns from configuration.
        
        Args:
            metallic: Base metallic array
            patterns: Pattern configuration dictionary
            
        Returns:
            Metallic array with custom patterns
        """
        # Example pattern types that could be configured
        if 'scratches' in patterns:
            scratch_config = patterns['scratches']
            # Add scratch patterns based on config
            scratch_density = scratch_config.get('density', 0.1)
            scratch_depth = scratch_config.get('depth', 0.3)
            
            # Create random scratches
            scratches = np.random.random(metallic.shape) < scratch_density
            metallic[scratches] *= (1.0 - scratch_depth)
        
        if 'spots' in patterns:
            spot_config = patterns['spots']
            # Add spot patterns (e.g., wear spots on metal)
            spot_density = spot_config.get('density', 0.05)
            spot_size = spot_config.get('size', 3)
            
            spots = np.random.random(metallic.shape) < spot_density
            from scipy.ndimage import binary_dilation
            spots = binary_dilation(spots, iterations=spot_size)
            metallic[spots] *= 0.5
        
        return metallic
    
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges in an image.
        
        Args:
            image: Input array
            
        Returns:
            Boolean edge mask
        """
        from scipy import ndimage
        
        # Sobel edge detection
        edges_x = ndimage.sobel(image, axis=0)
        edges_y = ndimage.sobel(image, axis=1)
        edges = np.hypot(edges_x, edges_y)
        
        # Threshold
        threshold = np.percentile(edges, 85)
        return edges > threshold