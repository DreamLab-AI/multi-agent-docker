"""Preview generation for PBR materials using simple 3D rendering."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Dict, Optional, Tuple
import math
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PBRPreviewGenerator:
    """Generate preview images for PBR materials using simple raytracing."""
    
    def __init__(self, width: int = 512, height: int = 512):
        """Initialize the preview generator.
        
        Args:
            width: Width of the preview image
            height: Height of the preview image
        """
        self.width = width
        self.height = height
        
    def generate_preview(
        self, 
        textures: Dict[str, str],
        output_path: str,
        material_name: str = "Material"
    ) -> bool:
        """Generate a preview image showing the PBR material on a sphere.
        
        Args:
            textures: Dictionary mapping texture types to file paths
                     Keys: 'diffuse', 'normal', 'roughness', 'metallic', 'ao', 'height'
            output_path: Path where the preview will be saved
            material_name: Name of the material for display
            
        Returns:
            True if preview was generated successfully, False otherwise
        """
        try:
            logger.info(f"Generating preview for {material_name}")
            
            # Load textures
            loaded_textures = self._load_textures(textures)
            
            # Create the preview image
            preview = self._render_sphere_preview(loaded_textures)
            
            # Add material information
            preview = self._add_material_info(preview, material_name, textures)
            
            # Save the preview
            preview.save(output_path)
            logger.info(f"Preview saved to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return False
    
    def _load_textures(self, texture_paths: Dict[str, str]) -> Dict[str, Optional[Image.Image]]:
        """Load texture images from file paths.
        
        Args:
            texture_paths: Dictionary mapping texture types to file paths
            
        Returns:
            Dictionary mapping texture types to PIL Images
        """
        loaded = {}
        
        for tex_type, path in texture_paths.items():
            if path and Path(path).exists():
                try:
                    img = Image.open(path).convert('RGB')
                    # Resize to preview resolution for performance
                    img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                    loaded[tex_type] = img
                    logger.debug(f"Loaded {tex_type} texture from {path}")
                except Exception as e:
                    logger.error(f"Error loading {tex_type} texture: {e}")
                    loaded[tex_type] = None
            else:
                loaded[tex_type] = None
                
        return loaded
    
    def _render_sphere_preview(self, textures: Dict[str, Optional[Image.Image]]) -> Image.Image:
        """Render a sphere with the PBR material applied.
        
        This uses a simple raytracing approach to render a sphere with:
        - Diffuse texture mapping
        - Normal mapping for surface detail
        - Roughness affecting specular highlights
        - Metallic properties
        - Ambient occlusion
        
        Args:
            textures: Dictionary of loaded texture images
            
        Returns:
            Rendered preview image
        """
        # Create output image
        output = Image.new('RGB', (self.width, self.height), (50, 50, 50))
        pixels = output.load()
        
        # Get texture data as numpy arrays for faster access
        diffuse_data = np.array(textures.get('diffuse', None)) if textures.get('diffuse') else None
        normal_data = np.array(textures.get('normal', None)) if textures.get('normal') else None
        roughness_data = np.array(textures.get('roughness', None)) if textures.get('roughness') else None
        metallic_data = np.array(textures.get('metallic', None)) if textures.get('metallic') else None
        ao_data = np.array(textures.get('ao', None)) if textures.get('ao') else None
        
        # Sphere parameters
        center_x, center_y = self.width // 2, self.height // 2
        radius = min(self.width, self.height) * 0.35
        
        # Lighting setup
        light_dir = np.array([0.5, -0.5, -0.7])
        light_dir = light_dir / np.linalg.norm(light_dir)
        light_color = np.array([1.0, 1.0, 1.0])
        ambient_light = np.array([0.1, 0.1, 0.1])
        
        # Camera/view direction
        view_dir = np.array([0, 0, -1])
        
        # Render each pixel
        for y in range(self.height):
            for x in range(self.width):
                # Calculate ray from pixel to sphere center
                dx = x - center_x
                dy = y - center_y
                
                # Check if ray hits sphere
                dist_sq = dx * dx + dy * dy
                if dist_sq <= radius * radius:
                    # Calculate Z coordinate on sphere surface
                    z = math.sqrt(radius * radius - dist_sq)
                    
                    # Calculate normal at this point
                    normal = np.array([dx, dy, z])
                    normal = normal / np.linalg.norm(normal)
                    
                    # Calculate UV coordinates for texture mapping
                    u = 0.5 + math.atan2(dx, z) / (2 * math.pi)
                    v = 0.5 - math.asin(dy / radius) / math.pi
                    
                    # Sample textures at UV coordinates
                    tex_x = int(u * (self.width - 1))
                    tex_y = int(v * (self.height - 1))
                    
                    # Get diffuse color
                    if diffuse_data is not None:
                        diffuse_color = diffuse_data[tex_y, tex_x] / 255.0
                    else:
                        diffuse_color = np.array([0.5, 0.5, 0.5])
                    
                    # Apply normal mapping
                    if normal_data is not None:
                        normal_sample = normal_data[tex_y, tex_x] / 255.0
                        # Convert from [0,1] to [-1,1]
                        normal_sample = normal_sample * 2.0 - 1.0
                        # Perturb the surface normal
                        normal = self._apply_normal_map(normal, normal_sample)
                    
                    # Get material properties
                    if roughness_data is not None:
                        roughness = roughness_data[tex_y, tex_x, 0] / 255.0
                    else:
                        roughness = 0.5
                        
                    if metallic_data is not None:
                        metallic = metallic_data[tex_y, tex_x, 0] / 255.0
                    else:
                        metallic = 0.0
                        
                    if ao_data is not None:
                        ao = ao_data[tex_y, tex_x, 0] / 255.0
                    else:
                        ao = 1.0
                    
                    # Calculate lighting
                    color = self._calculate_pbr_lighting(
                        normal, view_dir, light_dir, light_color,
                        diffuse_color, roughness, metallic, ao, ambient_light
                    )
                    
                    # Convert to 8-bit color
                    color = np.clip(color * 255, 0, 255).astype(int)
                    pixels[x, y] = tuple(color)
        
        return output
    
    def _apply_normal_map(self, surface_normal: np.ndarray, normal_sample: np.ndarray) -> np.ndarray:
        """Apply normal map to surface normal.
        
        Args:
            surface_normal: Original surface normal
            normal_sample: Normal map sample in tangent space
            
        Returns:
            Perturbed normal
        """
        # Simple approximation - blend the normals
        # In a full implementation, we'd calculate proper tangent space
        perturbed = surface_normal + normal_sample * 0.5
        return perturbed / np.linalg.norm(perturbed)
    
    def _calculate_pbr_lighting(
        self,
        normal: np.ndarray,
        view_dir: np.ndarray,
        light_dir: np.ndarray,
        light_color: np.ndarray,
        diffuse_color: np.ndarray,
        roughness: float,
        metallic: float,
        ao: float,
        ambient: np.ndarray
    ) -> np.ndarray:
        """Calculate PBR lighting for a surface point.
        
        Simplified PBR lighting calculation including:
        - Diffuse (Lambert)
        - Specular (simplified GGX)
        - Fresnel effect
        - Metallic workflow
        
        Args:
            normal: Surface normal
            view_dir: View direction
            light_dir: Light direction
            light_color: Light color
            diffuse_color: Base color from diffuse texture
            roughness: Roughness value
            metallic: Metallic value
            ao: Ambient occlusion value
            ambient: Ambient light color
            
        Returns:
            Final color
        """
        # Calculate basic vectors
        h = (view_dir - light_dir) / np.linalg.norm(view_dir - light_dir)
        ndotl = max(0, np.dot(normal, -light_dir))
        ndotv = max(0, np.dot(normal, view_dir))
        ndoth = max(0, np.dot(normal, h))
        vdoth = max(0, np.dot(view_dir, h))
        
        # Fresnel (Schlick approximation)
        f0 = np.array([0.04, 0.04, 0.04])  # Non-metallic F0
        f0 = f0 * (1 - metallic) + diffuse_color * metallic
        fresnel = f0 + (1 - f0) * pow(1 - vdoth, 5)
        
        # Distribution (simplified GGX)
        alpha = roughness * roughness
        alpha_sq = alpha * alpha
        denom = ndoth * ndoth * (alpha_sq - 1) + 1
        distribution = alpha_sq / (math.pi * denom * denom + 0.0001)
        
        # Geometry (simplified)
        k = (roughness + 1) * (roughness + 1) / 8
        geometry = ndotl / (ndotl * (1 - k) + k + 0.0001)
        
        # Specular BRDF
        specular = (distribution * geometry * fresnel) / (4 * ndotv * ndotl + 0.0001)
        
        # Diffuse BRDF
        kd = (1 - fresnel) * (1 - metallic)
        diffuse = kd * diffuse_color / math.pi
        
        # Combine
        color = (diffuse + specular) * light_color * ndotl
        
        # Add ambient with AO
        color += ambient * diffuse_color * ao
        
        return color
    
    def _add_material_info(
        self, 
        image: Image.Image, 
        material_name: str,
        textures: Dict[str, str]
    ) -> Image.Image:
        """Add material information overlay to the preview.
        
        Args:
            image: The rendered preview image
            material_name: Name of the material
            textures: Dictionary of texture paths
            
        Returns:
            Image with overlay
        """
        # Create a copy to draw on
        result = image.copy()
        draw = ImageDraw.Draw(result)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font_size = max(12, self.height // 40)
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size - 2)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        # Add material name
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        
        # Draw title with shadow
        title = f"{material_name} Preview"
        x, y = 10, 10
        draw.text((x+1, y+1), title, font=font, fill=shadow_color)
        draw.text((x, y), title, font=font, fill=text_color)
        
        # Add texture list
        y += 30
        texture_types = ['diffuse', 'normal', 'roughness', 'metallic', 'ao', 'height']
        for tex_type in texture_types:
            if tex_type in textures and textures[tex_type]:
                status = "✓"
                color = (100, 255, 100)
            else:
                status = "✗"
                color = (255, 100, 100)
                
            text = f"{status} {tex_type.capitalize()}"
            draw.text((x+1, y+1), text, font=small_font, fill=shadow_color)
            draw.text((x, y), text, font=small_font, fill=color)
            y += 20
        
        return result


def generate_material_preview(
    material_name: str,
    texture_paths: Dict[str, str],
    output_dir: str,
    preview_size: Tuple[int, int] = (512, 512)
) -> Optional[str]:
    """Generate a preview image for a PBR material.
    
    Args:
        material_name: Name of the material
        texture_paths: Dictionary mapping texture types to file paths
        output_dir: Directory where preview will be saved
        preview_size: Size of the preview image (width, height)
        
    Returns:
        Path to the generated preview, or None if generation failed
    """
    try:
        generator = PBRPreviewGenerator(preview_size[0], preview_size[1])
        
        output_path = Path(output_dir) / "preview.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = generator.generate_preview(
            textures=texture_paths,
            output_path=str(output_path),
            material_name=material_name
        )
        
        return str(output_path) if success else None
        
    except Exception as e:
        logger.error(f"Failed to generate preview: {e}")
        return None