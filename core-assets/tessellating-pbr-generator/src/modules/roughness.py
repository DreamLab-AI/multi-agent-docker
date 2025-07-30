"""Roughness texture generation module.

This module generates roughness maps from diffuse textures following PBR principles.
The roughness map controls micro-surface roughness for specular reflections.
"""

import numpy as np
from PIL import Image
from typing import Tuple, Optional


class RoughnessModule:
    """Generates roughness maps from diffuse textures.
    
    The roughness map controls how rough or smooth a surface appears by affecting
    specular reflections. In Blender's Principled BSDF:
    - 0.0 = perfectly smooth (mirror-like)
    - 1.0 = completely rough (diffuse-like)
    
    This module derives roughness from the diffuse texture's luminance values,
    with material-specific adjustments.
    """
    
    def __init__(self, roughness_range: Tuple[float, float] = (0.0, 1.0),
                 material_type: Optional[str] = None,
                 base_value: Optional[float] = None,
                 variation: Optional[float] = None,
                 invert: bool = False,
                 directional: bool = False,
                 direction_angle: float = 0.0):
        """Initialize the roughness module.
        
        Args:
            roughness_range: Min and max roughness values to map to (legacy)
            material_type: Material type for specific adjustments (e.g., 'metal', 'stone')
            base_value: Base roughness value (0-1)
            variation: Amount of variation around base value
            invert: Whether to invert the roughness mapping
            directional: Whether to apply directional roughness (e.g., brushed metal)
            direction_angle: Angle for directional roughness in degrees
        """
        # Use advanced parameters if provided, otherwise fall back to legacy
        if base_value is not None and variation is not None:
            self.base_value = base_value
            self.variation = variation
            self.roughness_range = (
                max(0.0, base_value - variation),
                min(1.0, base_value + variation)
            )
        else:
            self.roughness_range = roughness_range
            min_val, max_val = roughness_range
            self.base_value = (min_val + max_val) / 2
            self.variation = (max_val - min_val) / 2
        
        self.material_type = material_type
        self.invert = invert
        self.directional = directional
        self.direction_angle = direction_angle
        
        # Material-specific presets
        self.material_presets = {
            'stone': {'invert': True, 'contrast': 1.2},
            'metal': {'invert': False, 'contrast': 0.8},
            'wood': {'invert': True, 'contrast': 1.0},
            'fabric': {'invert': True, 'contrast': 1.3},
            'plastic': {'invert': False, 'contrast': 0.7},
            'concrete': {'invert': True, 'contrast': 1.1}
        }
    
    def generate(self, diffuse_image: Image.Image) -> Image.Image:
        """Generate a roughness map from a diffuse texture.
        
        Process:
        1. Convert to grayscale using perceptual luminance
        2. Apply material-specific adjustments
        3. Map to roughness range
        4. Return as grayscale image
        
        Args:
            diffuse_image: PIL Image of the diffuse texture
            
        Returns:
            PIL Image: Grayscale roughness map
        """
        # Convert to RGB if not already
        if diffuse_image.mode != 'RGB':
            diffuse_image = diffuse_image.convert('RGB')
        
        # Convert to numpy array
        diffuse_array = np.array(diffuse_image, dtype=np.float32) / 255.0
        
        # Extract luminance using ITU-R BT.709 coefficients
        # This gives perceptually accurate grayscale conversion
        luminance = (0.2126 * diffuse_array[:, :, 0] + 
                    0.7152 * diffuse_array[:, :, 1] + 
                    0.0722 * diffuse_array[:, :, 2])
        
        # Apply material-specific processing
        roughness = self._process_for_material(luminance)
        
        # Apply advanced inversion if configured
        if self.invert:
            roughness = 1.0 - roughness
        
        # Map to target roughness range
        roughness = self._map_to_range(roughness)
        
        # Apply directional roughness if configured
        if self.directional:
            roughness = self._apply_directional_roughness(roughness)
        
        # Add subtle noise for micro-variation (optional, very subtle)
        roughness = self._add_micro_variation(roughness)
        
        # Ensure values are in valid range
        roughness = np.clip(roughness, 0.0, 1.0)
        
        # Convert back to image
        roughness_uint8 = (roughness * 255).astype(np.uint8)
        roughness_image = Image.fromarray(roughness_uint8, mode='L')
        
        return roughness_image
    
    def _process_for_material(self, luminance: np.ndarray) -> np.ndarray:
        """Apply material-specific processing to luminance values.
        
        Args:
            luminance: Normalized luminance array
            
        Returns:
            Processed roughness values
        """
        # Get material preset or use defaults
        preset = self.material_presets.get(self.material_type, 
                                          {'invert': True, 'contrast': 1.0})
        
        # Start with luminance
        roughness = luminance.copy()
        
        # Only invert based on preset if not using advanced config
        # (advanced invert is handled in generate())
        if not hasattr(self, 'invert') and preset['invert']:
            roughness = 1.0 - roughness
        
        # Apply contrast adjustment
        if preset['contrast'] != 1.0:
            # Adjust contrast around midpoint
            roughness = 0.5 + (roughness - 0.5) * preset['contrast']
        
        # Material-specific adjustments
        if self.material_type == 'metal':
            # Metals tend to be smoother overall
            roughness = roughness * 0.7  # Reduce overall roughness
            
        elif self.material_type == 'stone':
            # Enhance high-frequency details for stone
            # Use local standard deviation as additional roughness
            from scipy.ndimage import generic_filter
            std_dev = generic_filter(luminance, np.std, size=3)
            roughness = roughness * 0.8 + std_dev * 0.2
            
        elif self.material_type == 'wood':
            # Wood grain should influence roughness
            # Enhance contrast along grain direction
            from scipy.ndimage import gaussian_filter1d
            # Assume horizontal grain (could be parameterized)
            smooth_horizontal = gaussian_filter1d(roughness, sigma=2, axis=1)
            roughness = roughness * 0.7 + smooth_horizontal * 0.3
            
        elif self.material_type == 'fabric':
            # Fabric is generally very rough
            roughness = np.maximum(roughness, 0.6)  # Minimum roughness
        
        return roughness
    
    def _map_to_range(self, values: np.ndarray) -> np.ndarray:
        """Map normalized values to the target roughness range.
        
        Args:
            values: Normalized array (0-1)
            
        Returns:
            Values mapped to roughness_range
        """
        min_rough, max_rough = self.roughness_range
        
        # Linear interpolation to target range
        mapped = min_rough + values * (max_rough - min_rough)
        
        return mapped
    
    def _add_micro_variation(self, roughness: np.ndarray, 
                            amount: float = 0.02) -> np.ndarray:
        """Add subtle noise for micro-surface variation.
        
        Args:
            roughness: Roughness array
            amount: Amount of noise to add (0-1)
            
        Returns:
            Roughness with micro-variation
        """
        if amount <= 0:
            return roughness
        
        # Use configured variation if available
        noise_amount = self.variation if hasattr(self, 'variation') else amount
        
        # Generate subtle noise
        noise = np.random.normal(0, noise_amount, roughness.shape)
        
        # Add noise
        roughness_with_noise = roughness + noise
        
        return roughness_with_noise
    
    def _apply_directional_roughness(self, roughness: np.ndarray) -> np.ndarray:
        """Apply directional roughness pattern (e.g., for brushed metal).
        
        Args:
            roughness: Base roughness array
            
        Returns:
            Roughness with directional pattern
        """
        from scipy.ndimage import gaussian_filter1d
        import scipy.ndimage as ndimage
        
        # Convert angle to radians
        angle_rad = np.radians(self.direction_angle)
        
        # Create directional pattern
        if abs(self.direction_angle) < 45 or abs(self.direction_angle - 180) < 45:
            # Mostly horizontal
            directional = gaussian_filter1d(roughness, sigma=3, axis=1)
        elif abs(self.direction_angle - 90) < 45 or abs(self.direction_angle - 270) < 45:
            # Mostly vertical
            directional = gaussian_filter1d(roughness, sigma=3, axis=0)
        else:
            # Arbitrary angle - rotate, blur, rotate back
            rotated = ndimage.rotate(roughness, -self.direction_angle, reshape=False)
            blurred = gaussian_filter1d(rotated, sigma=3, axis=1)
            directional = ndimage.rotate(blurred, self.direction_angle, reshape=False)
        
        # Blend with original based on directionality strength
        return roughness * 0.3 + directional * 0.7
    
    def generate_from_height(self, height_map: Image.Image) -> Image.Image:
        """Alternative method: Generate roughness from a height map.
        
        This method derives roughness from the rate of change in the height map.
        Areas with rapid height changes are rougher.
        
        Args:
            height_map: Grayscale height map
            
        Returns:
            Roughness map
        """
        if height_map.mode != 'L':
            height_map = height_map.convert('L')
        
        height_array = np.array(height_map, dtype=np.float32) / 255.0
        
        # Calculate gradients
        from scipy.ndimage import sobel
        grad_x = sobel(height_array, axis=0)
        grad_y = sobel(height_array, axis=1)
        
        # Magnitude of gradients indicates rate of change
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Normalize and map to roughness
        gradient_magnitude = gradient_magnitude / gradient_magnitude.max()
        roughness = self._map_to_range(gradient_magnitude)
        
        # Ensure valid range
        roughness = np.clip(roughness, 0.0, 1.0)
        
        # Convert to image
        roughness_uint8 = (roughness * 255).astype(np.uint8)
        return Image.fromarray(roughness_uint8, mode='L')