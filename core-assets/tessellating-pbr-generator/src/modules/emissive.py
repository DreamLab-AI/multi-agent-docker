"""Emissive texture generation module.

Generates emissive maps for self-illuminating materials in PBR workflows.
Emissive maps control which parts of a material emit light:
- White (1.0) = full emission (bright self-illumination)
- Black (0.0) = no emission (standard material)
"""

from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import colorsys

from .base import TextureGenerator
from ..types.common import TextureType
from ..types.config import Config
from ..utils.filters import gaussian_blur
from ..utils.logging import get_logger


logger = get_logger(__name__)


class EmissiveModule(TextureGenerator):
    """Generates emissive maps for self-illuminating materials.
    
    The emissive map defines areas that emit light, useful for:
    - Neon signs and LED displays
    - Lava and molten materials
    - Computer screens and displays
    - Bioluminescent materials
    - Energy fields and sci-fi effects
    - Fire and plasma effects
    """
    
    def __init__(self, config: Config):
        """Initialize the emissive module.
        
        Args:
            config: Configuration object with material properties
        """
        super().__init__(config)
        
        # Base emission properties from config
        self.emission_intensity = getattr(
            self.material_properties, 
            'emission_intensity', 
            1.0
        )
        self.emission_color = getattr(
            self.material_properties,
            'emission_color',
            (1.0, 1.0, 1.0)  # Default white
        )
        
        # Material-specific emissive presets
        self.material_presets = {
            'neon': {
                'pattern': 'bright_regions',
                'intensity': 2.0,
                'color_mode': 'saturated',
                'threshold': 0.7,
                'glow_radius': 8,
                'pulse': 0.1
            },
            'led': {
                'pattern': 'discrete_points',
                'intensity': 3.0,
                'color_mode': 'preserve',
                'grid_size': 32,
                'led_size': 4,
                'variations': 0.1
            },
            'lava': {
                'pattern': 'temperature_map',
                'intensity': 1.5,
                'color_mode': 'heat_gradient',
                'min_temp': 0.3,
                'max_temp': 1.0,
                'flow_variation': 0.3
            },
            'screen': {
                'pattern': 'uniform_panel',
                'intensity': 0.8,
                'color_mode': 'preserve',
                'panel_detection': True,
                'edge_fade': 5,
                'backlight_bleed': 0.1
            },
            'plasma': {
                'pattern': 'energy_field',
                'intensity': 2.5,
                'color_mode': 'energy',
                'turbulence': 0.7,
                'frequency': 0.02,
                'glow_falloff': 1.5
            },
            'bioluminescent': {
                'pattern': 'organic_glow',
                'intensity': 1.2,
                'color_mode': 'bioluminescent',
                'spot_density': 0.02,
                'spot_size_range': (5, 20),
                'pulse_variation': 0.2
            },
            'fire': {
                'pattern': 'flame_emission',
                'intensity': 2.0,
                'color_mode': 'fire_gradient',
                'flame_height': 0.7,
                'turbulence': 0.4,
                'heat_zones': 3
            },
            'electric': {
                'pattern': 'electric_arc',
                'intensity': 3.0,
                'color_mode': 'electric_blue',
                'arc_density': 0.01,
                'branch_probability': 0.3,
                'fade_speed': 0.8
            },
            'crystal': {
                'pattern': 'crystalline_glow',
                'intensity': 1.5,
                'color_mode': 'prismatic',
                'facet_threshold': 0.6,
                'internal_glow': 0.4,
                'edge_intensity': 1.2
            },
            'radioactive': {
                'pattern': 'radiation_glow',
                'intensity': 1.8,
                'color_mode': 'toxic_green',
                'contamination_spots': 0.03,
                'decay_radius': 15,
                'pulse_frequency': 0.5
            }
        }
    
    @property
    def texture_type(self) -> TextureType:
        """Return the texture type this generator produces."""
        return TextureType.EMISSIVE
    
    def generate(self, input_data: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Generate emissive map.
        
        Args:
            input_data: Dictionary that may contain:
                - diffuse_map: PIL Image for deriving emission areas
                - height_map: PIL Image for material thickness
                - mask_map: PIL Image for explicit emission regions
                
        Returns:
            Emissive map as RGB PIL Image
        """
        logger.info(f"Generating emissive map at {self.resolution}")
        
        # Get preset for material
        preset = self.material_presets.get(
            self.config.material,
            {
                'pattern': 'bright_regions',
                'intensity': self.emission_intensity,
                'color_mode': 'preserve'
            }
        )
        
        # Override intensity if explicitly set
        if self.emission_intensity != 1.0:
            preset['intensity'] = self.emission_intensity
        
        # Generate base emissive map based on pattern
        emissive_array = self._generate_emissive_pattern(preset, input_data)
        
        # Apply color based on mode
        emissive_array = self._apply_emission_color(emissive_array, preset)
        
        # Add material-specific effects
        emissive_array = self._apply_material_effects(emissive_array, preset)
        
        # Apply intensity scaling
        emissive_array *= preset['intensity']
        
        # Ensure values are in valid range
        emissive_array = np.clip(emissive_array, 0.0, 1.0)
        
        # Convert to PIL Image
        emissive_image = Image.fromarray(
            (emissive_array * 255).astype(np.uint8),
            mode='RGB'
        )
        
        # Apply post-processing
        emissive_image = self.process_image(emissive_image)
        
        # Add glow effect if specified
        if preset.get('glow_radius', 0) > 0:
            emissive_image = self._add_glow_effect(
                emissive_image, 
                preset['glow_radius']
            )
        
        # Make seamless if configured
        if self.seamless:
            emissive_image = self.make_seamless(emissive_image)
        
        logger.info("Emissive map generation completed")
        return emissive_image
    
    def _generate_emissive_pattern(
        self, 
        preset: Dict,
        input_data: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Generate base emissive pattern based on material type.
        
        Args:
            preset: Material preset configuration
            input_data: Optional input textures
            
        Returns:
            Emissive pattern as RGB array
        """
        pattern_type = preset['pattern']
        
        # Initialize empty RGB array
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        if pattern_type == 'bright_regions':
            emissive = self._pattern_bright_regions(preset, input_data)
            
        elif pattern_type == 'discrete_points':
            emissive = self._pattern_discrete_points(preset)
            
        elif pattern_type == 'temperature_map':
            emissive = self._pattern_temperature_map(preset, input_data)
            
        elif pattern_type == 'uniform_panel':
            emissive = self._pattern_uniform_panel(preset, input_data)
            
        elif pattern_type == 'energy_field':
            emissive = self._pattern_energy_field(preset)
            
        elif pattern_type == 'organic_glow':
            emissive = self._pattern_organic_glow(preset)
            
        elif pattern_type == 'flame_emission':
            emissive = self._pattern_flame_emission(preset)
            
        elif pattern_type == 'electric_arc':
            emissive = self._pattern_electric_arc(preset)
            
        elif pattern_type == 'crystalline_glow':
            emissive = self._pattern_crystalline_glow(preset, input_data)
            
        elif pattern_type == 'radiation_glow':
            emissive = self._pattern_radiation_glow(preset)
        
        return emissive
    
    def _pattern_bright_regions(
        self, 
        preset: Dict,
        input_data: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Extract bright regions from diffuse map for emission.
        
        Used for neon signs, illuminated text, etc.
        """
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        if input_data and 'diffuse_map' in input_data:
            diffuse = self._process_input_image(input_data['diffuse_map'])
            
            # Calculate luminance
            luminance = np.dot(diffuse[..., :3], [0.299, 0.587, 0.114])
            
            # Threshold bright areas
            threshold = preset.get('threshold', 0.7)
            bright_mask = luminance > threshold
            
            # Use original colors in bright areas
            emissive[bright_mask] = diffuse[bright_mask]
            
            # Smooth edges
            for i in range(3):
                emissive[:, :, i] = gaussian_blur(emissive[:, :, i], sigma=1.0)
        
        return emissive
    
    def _pattern_discrete_points(self, preset: Dict) -> np.ndarray:
        """Generate LED-like discrete emission points."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        grid_size = preset.get('grid_size', 32)
        led_size = preset.get('led_size', 4)
        variations = preset.get('variations', 0.1)
        
        # Create LED grid
        for y in range(0, self.resolution.height, grid_size):
            for x in range(0, self.resolution.width, grid_size):
                # Add slight position variation
                offset_x = int(np.random.uniform(-2, 2))
                offset_y = int(np.random.uniform(-2, 2))
                
                center_x = min(max(x + offset_x, led_size), 
                             self.resolution.width - led_size)
                center_y = min(max(y + offset_y, led_size), 
                             self.resolution.height - led_size)
                
                # Draw LED
                for dy in range(-led_size, led_size + 1):
                    for dx in range(-led_size, led_size + 1):
                        px = center_x + dx
                        py = center_y + dy
                        
                        if (0 <= px < self.resolution.width and 
                            0 <= py < self.resolution.height):
                            
                            # Circular LED shape
                            dist = np.sqrt(dx**2 + dy**2)
                            if dist <= led_size:
                                intensity = 1.0 - (dist / led_size)
                                intensity = intensity ** 2  # Falloff
                                
                                # Add color variation
                                color = np.array([1.0, 1.0, 1.0])
                                if variations > 0:
                                    color += np.random.uniform(-variations, variations, 3)
                                    color = np.clip(color, 0, 1)
                                
                                emissive[py, px] = color * intensity
        
        return emissive
    
    def _pattern_temperature_map(
        self, 
        preset: Dict,
        input_data: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Generate temperature-based emission for lava/molten materials."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        # Generate or use height map as temperature base
        if input_data and 'height_map' in input_data:
            height = self._process_input_image(input_data['height_map'], grayscale=True)
            temperature = height[:, :, 0]
        else:
            # Generate procedural temperature map
            temperature = self._generate_noise_pattern(
                scale=50,
                octaves=4,
                persistence=0.6
            )
        
        # Add flow variation
        flow_var = preset.get('flow_variation', 0.3)
        if flow_var > 0:
            flow_noise = self._generate_noise_pattern(scale=20, octaves=2)
            temperature = temperature * (1 - flow_var) + flow_noise * flow_var
        
        # Map to temperature range
        min_temp = preset.get('min_temp', 0.3)
        max_temp = preset.get('max_temp', 1.0)
        temperature = min_temp + temperature * (max_temp - min_temp)
        
        # Apply to all channels (will be colored later)
        for i in range(3):
            emissive[:, :, i] = temperature
        
        return emissive
    
    def _pattern_uniform_panel(
        self, 
        preset: Dict,
        input_data: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Generate uniform emission for screen/panel materials."""
        emissive = np.ones(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        # Panel detection from diffuse
        if preset.get('panel_detection', True) and input_data and 'diffuse_map' in input_data:
            diffuse = self._process_input_image(input_data['diffuse_map'])
            
            # Detect panel regions (usually darker/uniform areas)
            luminance = np.dot(diffuse[..., :3], [0.299, 0.587, 0.114])
            
            # Calculate local variance
            from scipy.ndimage import generic_filter
            variance = generic_filter(luminance, np.var, size=5)
            
            # Low variance = likely panel area
            panel_mask = variance < 0.01
            
            # Only emit in panel areas
            for i in range(3):
                emissive[:, :, i] *= panel_mask
        
        # Edge fade
        edge_fade = preset.get('edge_fade', 5)
        if edge_fade > 0:
            emissive = self._apply_edge_fade(emissive, edge_fade)
        
        # Backlight bleed
        bleed = preset.get('backlight_bleed', 0.1)
        if bleed > 0:
            # Add slight variations
            noise = self._generate_noise_pattern(scale=100, octaves=1)
            emissive *= (1.0 - bleed) + noise[:, :, np.newaxis] * bleed
        
        return emissive
    
    def _pattern_energy_field(self, preset: Dict) -> np.ndarray:
        """Generate plasma/energy field emission pattern."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        turbulence = preset.get('turbulence', 0.7)
        frequency = preset.get('frequency', 0.02)
        
        # Generate turbulent energy pattern
        y, x = np.ogrid[:self.resolution.height, :self.resolution.width]
        
        # Multiple frequencies of distortion
        pattern = np.zeros((self.resolution.height, self.resolution.width))
        
        for i in range(3):
            freq = frequency * (2 ** i)
            phase = np.random.uniform(0, 2 * np.pi)
            
            wave_x = np.sin(x * freq + phase)
            wave_y = np.cos(y * freq + phase * 0.7)
            
            pattern += (wave_x * wave_y) / (i + 1)
        
        # Add turbulent noise
        noise = self._generate_noise_pattern(scale=30, octaves=4)
        pattern = pattern * (1 - turbulence) + noise * turbulence
        
        # Normalize and apply falloff
        pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min())
        falloff = preset.get('glow_falloff', 1.5)
        pattern = pattern ** falloff
        
        # Apply to all channels
        for i in range(3):
            emissive[:, :, i] = pattern
        
        return emissive
    
    def _pattern_organic_glow(self, preset: Dict) -> np.ndarray:
        """Generate bioluminescent organic glow pattern."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        spot_density = preset.get('spot_density', 0.02)
        size_range = preset.get('spot_size_range', (5, 20))
        
        # Generate random glowing spots
        num_spots = int(self.resolution.width * self.resolution.height * spot_density)
        
        for _ in range(num_spots):
            # Random position
            cx = np.random.randint(0, self.resolution.width)
            cy = np.random.randint(0, self.resolution.height)
            
            # Random size
            size = np.random.uniform(*size_range)
            
            # Create glowing spot
            y, x = np.ogrid[:self.resolution.height, :self.resolution.width]
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            
            # Gaussian falloff
            spot = np.exp(-(dist**2) / (2 * size**2))
            
            # Add pulsation variation
            pulse = preset.get('pulse_variation', 0.2)
            intensity = 1.0 - pulse + np.random.uniform(0, pulse)
            
            # Random color tint (slight)
            color = np.array([1.0, 1.0, 1.0])
            color += np.random.uniform(-0.1, 0.1, 3)
            color = np.clip(color, 0, 1)
            
            # Add to emissive
            for i in range(3):
                emissive[:, :, i] += spot * intensity * color[i]
        
        return np.clip(emissive, 0, 1)
    
    def _pattern_flame_emission(self, preset: Dict) -> np.ndarray:
        """Generate flame/fire emission pattern."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        flame_height = preset.get('flame_height', 0.7)
        turbulence = preset.get('turbulence', 0.4)
        
        # Height gradient (bottom = hot, top = cool)
        y_gradient = np.linspace(1, 0, self.resolution.height)
        y_gradient = y_gradient[:, np.newaxis]
        y_gradient = y_gradient ** 2  # Concentrate at bottom
        
        # Add turbulent displacement
        displacement = self._generate_noise_pattern(scale=40, octaves=3)
        displacement = (displacement - 0.5) * turbulence * self.resolution.height * 0.1
        
        # Apply displacement to gradient
        y_coords = np.arange(self.resolution.height)[:, np.newaxis]
        y_displaced = y_coords + displacement
        
        # Remap gradient with displacement
        flame_shape = np.zeros_like(y_gradient)
        for i in range(self.resolution.height):
            for j in range(self.resolution.width):
                y_pos = int(y_displaced[i, j])
                if 0 <= y_pos < self.resolution.height:
                    flame_shape[i, j] = y_gradient[y_pos, 0]
        
        # Apply height cutoff
        flame_shape *= (y_gradient > (1 - flame_height))
        
        # Add flicker
        flicker = self._generate_noise_pattern(scale=20, octaves=2)
        flame_shape = flame_shape * (0.7 + flicker * 0.3)
        
        # Apply to all channels (will be colored later)
        for i in range(3):
            emissive[:, :, i] = flame_shape
        
        return emissive
    
    def _pattern_electric_arc(self, preset: Dict) -> np.ndarray:
        """Generate electric arc emission pattern."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        arc_density = preset.get('arc_density', 0.01)
        branch_prob = preset.get('branch_probability', 0.3)
        
        # Number of main arcs
        num_arcs = max(1, int(self.resolution.width * arc_density))
        
        for _ in range(num_arcs):
            # Random start and end points
            start_x = np.random.randint(0, self.resolution.width)
            start_y = np.random.randint(0, self.resolution.height // 2)
            end_x = np.random.randint(0, self.resolution.width)
            end_y = np.random.randint(self.resolution.height // 2, self.resolution.height)
            
            # Draw jagged arc
            points = self._generate_lightning_path(
                (start_x, start_y), 
                (end_x, end_y),
                branch_prob
            )
            
            # Draw arc with glow
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                
                # Draw line segment with thickness
                self._draw_glowing_line(emissive, p1, p2, thickness=2, intensity=1.0)
                
                # Chance of branching
                if np.random.random() < branch_prob:
                    # Create branch
                    branch_end = (
                        p2[0] + np.random.randint(-50, 50),
                        p2[1] + np.random.randint(-30, 30)
                    )
                    branch_points = self._generate_lightning_path(
                        p2, branch_end, branch_prob * 0.5
                    )
                    
                    for j in range(len(branch_points) - 1):
                        self._draw_glowing_line(
                            emissive, 
                            branch_points[j], 
                            branch_points[j + 1],
                            thickness=1,
                            intensity=0.7
                        )
        
        return emissive
    
    def _pattern_crystalline_glow(
        self, 
        preset: Dict,
        input_data: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Generate crystalline/gem glow emission."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        # Use diffuse for crystal facets
        if input_data and 'diffuse_map' in input_data:
            diffuse = self._process_input_image(input_data['diffuse_map'])
            
            # Detect edges/facets
            edges = self._detect_crystal_facets(diffuse)
            
            # Facets emit more
            facet_threshold = preset.get('facet_threshold', 0.6)
            edge_intensity = preset.get('edge_intensity', 1.2)
            
            emissive[edges > facet_threshold] = edge_intensity
            
            # Internal glow
            internal = preset.get('internal_glow', 0.4)
            if internal > 0:
                # Use color information
                emissive += diffuse * internal
        
        else:
            # Procedural crystal pattern
            pattern = self._generate_crystal_pattern()
            for i in range(3):
                emissive[:, :, i] = pattern
        
        return np.clip(emissive, 0, 1)
    
    def _pattern_radiation_glow(self, preset: Dict) -> np.ndarray:
        """Generate radioactive material glow."""
        emissive = np.zeros(
            (self.resolution.height, self.resolution.width, 3),
            dtype=np.float32
        )
        
        contamination = preset.get('contamination_spots', 0.03)
        decay_radius = preset.get('decay_radius', 15)
        
        # Create contamination spots
        spots = np.random.random((self.resolution.height, self.resolution.width))
        spots = spots < contamination
        
        # Expand spots with decay
        from scipy.ndimage import distance_transform_edt
        distances = distance_transform_edt(~spots)
        
        # Exponential decay from spots
        glow = np.exp(-distances / decay_radius)
        
        # Add pulsing
        pulse_freq = preset.get('pulse_frequency', 0.5)
        pulse = self._generate_noise_pattern(scale=80, octaves=2)
        glow = glow * (0.7 + pulse * 0.3)
        
        # Apply to all channels
        for i in range(3):
            emissive[:, :, i] = glow
        
        return emissive
    
    def _apply_emission_color(
        self, 
        emissive: np.ndarray,
        preset: Dict
    ) -> np.ndarray:
        """Apply color to the emission based on material type.
        
        Args:
            emissive: Base emission pattern
            preset: Material preset
            
        Returns:
            Colored emission array
        """
        color_mode = preset.get('color_mode', 'preserve')
        
        if color_mode == 'preserve':
            # Keep original colors
            pass
            
        elif color_mode == 'saturated':
            # Increase saturation for neon effect
            emissive = self._increase_saturation(emissive, factor=2.0)
            
        elif color_mode == 'heat_gradient':
            # Temperature gradient (black -> red -> orange -> yellow -> white)
            emissive = self._apply_heat_gradient(emissive)
            
        elif color_mode == 'fire_gradient':
            # Fire colors (dark red -> orange -> yellow)
            emissive = self._apply_fire_gradient(emissive)
            
        elif color_mode == 'energy':
            # Energy/plasma colors (blue -> purple -> white)
            emissive = self._apply_energy_gradient(emissive)
            
        elif color_mode == 'bioluminescent':
            # Bioluminescent colors (cyan -> green -> blue)
            emissive = self._apply_bio_gradient(emissive)
            
        elif color_mode == 'electric_blue':
            # Electric blue with white core
            emissive = self._apply_electric_color(emissive)
            
        elif color_mode == 'toxic_green':
            # Radioactive green glow
            emissive = self._apply_toxic_color(emissive)
            
        elif color_mode == 'prismatic':
            # Rainbow/prismatic effect
            emissive = self._apply_prismatic_color(emissive)
        
        # Apply configured emission color as tint
        if hasattr(self, 'emission_color') and self.emission_color != (1.0, 1.0, 1.0):
            for i in range(3):
                emissive[:, :, i] *= self.emission_color[i]
        
        return emissive
    
    def _apply_material_effects(
        self, 
        emissive: np.ndarray,
        preset: Dict
    ) -> np.ndarray:
        """Apply material-specific effects to emission.
        
        Args:
            emissive: Emission array
            preset: Material preset
            
        Returns:
            Emission with effects
        """
        # Pulsing effect
        if preset.get('pulse', 0) > 0:
            pulse_amount = preset['pulse']
            # Simple sine wave modulation (would animate in engine)
            modulation = 1.0 - pulse_amount * 0.5
            emissive *= modulation
        
        # Add noise/grain for realism
        if self.config.material in ['lava', 'fire', 'plasma']:
            noise = np.random.normal(0, 0.02, emissive.shape)
            emissive += noise
        
        return np.clip(emissive, 0, 1)
    
    def _add_glow_effect(self, image: Image.Image, radius: int) -> Image.Image:
        """Add glow/bloom effect to emissive areas.
        
        Args:
            image: Input image
            radius: Glow radius in pixels
            
        Returns:
            Image with glow
        """
        # Convert to array
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # Create glow layer
        glow = img_array.copy()
        
        # Apply gaussian blur for glow
        glow = gaussian_blur(glow, sigma=radius)
        
        # Screen blend mode
        result = 1.0 - (1.0 - img_array) * (1.0 - glow * 0.5)
        
        # Convert back
        result = np.clip(result * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(result, mode='RGB')
    
    # Utility methods
    
    def _process_input_image(
        self, 
        image: Any,
        grayscale: bool = False
    ) -> np.ndarray:
        """Process input image to normalized numpy array.
        
        Args:
            image: PIL Image or numpy array
            grayscale: Convert to grayscale
            
        Returns:
            Normalized array
        """
        if isinstance(image, Image.Image):
            if image.size != (self.resolution.width, self.resolution.height):
                image = image.resize(
                    (self.resolution.width, self.resolution.height),
                    Image.Resampling.LANCZOS
                )
            
            if grayscale and image.mode != 'L':
                image = image.convert('L')
            elif not grayscale and image.mode != 'RGB':
                image = image.convert('RGB')
            
            array = np.array(image, dtype=np.float32) / 255.0
        else:
            array = image.astype(np.float32)
            if array.max() > 1.0:
                array = array / 255.0
        
        # Ensure 3D array for RGB
        if not grayscale and len(array.shape) == 2:
            array = np.stack([array] * 3, axis=-1)
        elif grayscale and len(array.shape) == 2:
            array = array[:, :, np.newaxis]
        
        return array
    
    def _generate_noise_pattern(
        self,
        scale: float = 50,
        octaves: int = 4,
        persistence: float = 0.5
    ) -> np.ndarray:
        """Generate Perlin-like noise pattern.
        
        Args:
            scale: Base scale of noise
            octaves: Number of octaves
            persistence: Amplitude scaling per octave
            
        Returns:
            Noise array (0-1)
        """
        noise = np.zeros((self.resolution.height, self.resolution.width))
        
        amplitude = 1.0
        frequency = 1.0 / scale
        
        for _ in range(octaves):
            # Generate octave
            y, x = np.ogrid[:self.resolution.height, :self.resolution.width]
            
            # Use sine waves for simple noise
            octave = (
                np.sin(x * frequency * 2 * np.pi) * 
                np.cos(y * frequency * 2 * np.pi)
            )
            
            # Add randomness
            phase = np.random.random((self.resolution.height, self.resolution.width))
            octave += np.sin(phase * 2 * np.pi) * 0.5
            
            noise += octave * amplitude
            
            amplitude *= persistence
            frequency *= 2.0
        
        # Normalize to 0-1
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        return noise
    
    def _increase_saturation(self, rgb: np.ndarray, factor: float) -> np.ndarray:
        """Increase color saturation.
        
        Args:
            rgb: RGB array
            factor: Saturation multiplier
            
        Returns:
            Saturated RGB array
        """
        # Convert to HSV
        hsv = np.zeros_like(rgb)
        
        for i in range(rgb.shape[0]):
            for j in range(rgb.shape[1]):
                r, g, b = rgb[i, j]
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                
                # Increase saturation
                s = min(1.0, s * factor)
                
                # Convert back
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                rgb[i, j] = [r, g, b]
        
        return rgb
    
    def _apply_heat_gradient(self, intensity: np.ndarray) -> np.ndarray:
        """Apply heat/temperature gradient coloring.
        
        Args:
            intensity: Grayscale intensity array
            
        Returns:
            RGB heat gradient
        """
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        # Get intensity from first channel if RGB
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        # Heat gradient colors
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                if val < 0.25:
                    # Black to dark red
                    rgb[i, j] = [val * 4, 0, 0]
                elif val < 0.5:
                    # Dark red to bright red
                    t = (val - 0.25) * 4
                    rgb[i, j] = [1.0, t * 0.2, 0]
                elif val < 0.75:
                    # Red to orange/yellow
                    t = (val - 0.5) * 4
                    rgb[i, j] = [1.0, 0.2 + t * 0.8, t * 0.2]
                else:
                    # Yellow to white
                    t = (val - 0.75) * 4
                    rgb[i, j] = [1.0, 1.0, 0.2 + t * 0.8]
        
        return rgb
    
    def _apply_fire_gradient(self, intensity: np.ndarray) -> np.ndarray:
        """Apply fire color gradient.
        
        Args:
            intensity: Grayscale intensity array
            
        Returns:
            RGB fire gradient
        """
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                if val < 0.5:
                    # Dark red to orange
                    t = val * 2
                    rgb[i, j] = [0.5 + t * 0.5, t * 0.5, 0]
                else:
                    # Orange to yellow
                    t = (val - 0.5) * 2
                    rgb[i, j] = [1.0, 0.5 + t * 0.5, t * 0.8]
        
        return rgb
    
    def _apply_energy_gradient(self, intensity: np.ndarray) -> np.ndarray:
        """Apply energy/plasma gradient coloring."""
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                # Blue to purple to white
                if val < 0.5:
                    t = val * 2
                    rgb[i, j] = [t * 0.5, t * 0.3, 0.5 + t * 0.5]
                else:
                    t = (val - 0.5) * 2
                    rgb[i, j] = [0.5 + t * 0.5, 0.3 + t * 0.7, 1.0]
        
        return rgb
    
    def _apply_bio_gradient(self, intensity: np.ndarray) -> np.ndarray:
        """Apply bioluminescent gradient coloring."""
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                # Cyan to green to blue variations
                hue = 0.4 + val * 0.2  # Green to cyan range
                r, g, b = colorsys.hsv_to_rgb(hue, 0.8, val)
                rgb[i, j] = [r, g, b]
        
        return rgb
    
    def _apply_electric_color(self, intensity: np.ndarray) -> np.ndarray:
        """Apply electric blue coloring."""
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                # Electric blue with white core
                if val > 0.8:
                    # White core
                    rgb[i, j] = [1.0, 1.0, 1.0]
                else:
                    # Blue glow
                    rgb[i, j] = [val * 0.4, val * 0.6, val]
        
        return rgb
    
    def _apply_toxic_color(self, intensity: np.ndarray) -> np.ndarray:
        """Apply toxic/radioactive green coloring."""
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                # Toxic green
                rgb[i, j] = [val * 0.2, val, val * 0.1]
        
        return rgb
    
    def _apply_prismatic_color(self, intensity: np.ndarray) -> np.ndarray:
        """Apply prismatic/rainbow coloring."""
        rgb = np.zeros((*intensity.shape[:2], 3))
        
        if len(intensity.shape) == 3:
            intensity = intensity[:, :, 0]
        
        for i in range(intensity.shape[0]):
            for j in range(intensity.shape[1]):
                val = intensity[i, j]
                
                if val > 0:
                    # Position-based hue
                    hue = ((i + j) / (intensity.shape[0] + intensity.shape[1])) % 1.0
                    r, g, b = colorsys.hsv_to_rgb(hue, 0.9, val)
                    rgb[i, j] = [r, g, b]
        
        return rgb
    
    def _detect_crystal_facets(self, image: np.ndarray) -> np.ndarray:
        """Detect crystal facets/edges.
        
        Args:
            image: Input image
            
        Returns:
            Edge strength map
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image
        
        # Sobel edge detection
        from scipy import ndimage
        edges_x = ndimage.sobel(gray, axis=0)
        edges_y = ndimage.sobel(gray, axis=1)
        edges = np.hypot(edges_x, edges_y)
        
        # Normalize
        edges = edges / edges.max() if edges.max() > 0 else edges
        
        return edges
    
    def _generate_crystal_pattern(self) -> np.ndarray:
        """Generate procedural crystal pattern.
        
        Returns:
            Crystal pattern array
        """
        # Voronoi-like pattern for crystal facets
        points = []
        num_crystals = 20
        
        for _ in range(num_crystals):
            x = np.random.randint(0, self.resolution.width)
            y = np.random.randint(0, self.resolution.height)
            points.append((x, y))
        
        # Create distance field
        pattern = np.ones((self.resolution.height, self.resolution.width))
        
        for i in range(self.resolution.height):
            for j in range(self.resolution.width):
                # Find closest point
                min_dist = float('inf')
                for px, py in points:
                    dist = np.sqrt((i - py)**2 + (j - px)**2)
                    min_dist = min(min_dist, dist)
                
                # Create facet pattern
                pattern[i, j] = 1.0 - min(min_dist / 50, 1.0)
        
        return pattern
    
    def _generate_lightning_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        branch_prob: float
    ) -> list:
        """Generate jagged lightning path between points.
        
        Args:
            start: Start point (x, y)
            end: End point (x, y)
            branch_prob: Branching probability
            
        Returns:
            List of path points
        """
        points = [start]
        
        # Number of segments
        distance = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        segments = max(5, int(distance / 20))
        
        for i in range(1, segments):
            # Linear interpolation
            t = i / segments
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            
            # Add randomness
            offset = distance / segments * 0.3
            x += np.random.uniform(-offset, offset)
            y += np.random.uniform(-offset, offset)
            
            points.append((int(x), int(y)))
        
        points.append(end)
        return points
    
    def _draw_glowing_line(
        self,
        image: np.ndarray,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
        thickness: int = 1,
        intensity: float = 1.0
    ):
        """Draw a glowing line segment.
        
        Args:
            image: Target image array
            p1: Start point
            p2: End point
            thickness: Line thickness
            intensity: Glow intensity
        """
        # Simple line drawing with thickness
        x1, y1 = p1
        x2, y2 = p2
        
        # Bresenham's line algorithm with thickness
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            # Draw thick point
            for tx in range(-thickness, thickness + 1):
                for ty in range(-thickness, thickness + 1):
                    px = x1 + tx
                    py = y1 + ty
                    
                    if (0 <= px < self.resolution.width and 
                        0 <= py < self.resolution.height):
                        
                        # Distance from center for falloff
                        dist = np.sqrt(tx**2 + ty**2)
                        if dist <= thickness:
                            falloff = 1.0 - (dist / thickness)
                            image[py, px] = np.minimum(
                                image[py, px] + intensity * falloff,
                                1.0
                            )
            
            if x1 == x2 and y1 == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    def _apply_edge_fade(self, image: np.ndarray, fade_width: int) -> np.ndarray:
        """Apply edge fading to image.
        
        Args:
            image: Input image
            fade_width: Width of fade in pixels
            
        Returns:
            Image with faded edges
        """
        h, w = image.shape[:2]
        
        # Create fade mask
        fade_mask = np.ones((h, w))
        
        # Fade edges
        for i in range(fade_width):
            fade_value = i / fade_width
            
            # Top and bottom
            fade_mask[i, :] *= fade_value
            fade_mask[h - 1 - i, :] *= fade_value
            
            # Left and right
            fade_mask[:, i] *= fade_value
            fade_mask[:, w - 1 - i] *= fade_value
        
        # Apply mask
        if len(image.shape) == 3:
            for c in range(image.shape[2]):
                image[:, :, c] *= fade_mask
        else:
            image *= fade_mask
        
        return image