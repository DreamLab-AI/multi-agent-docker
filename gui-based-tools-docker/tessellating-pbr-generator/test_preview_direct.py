#!/usr/bin/env python3
"""Direct test for preview generation functionality."""

import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def simple_pbr_preview_test():
    """Test preview generation with direct implementation."""
    print("Testing PBR preview generation...")
    
    # Create test output directory
    test_output = Path("test_preview_direct")
    test_output.mkdir(exist_ok=True)
    
    # Create simple mock textures
    width, height = 128, 128
    
    # Mock diffuse texture (stone-like)
    diffuse = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(diffuse)
    for y in range(height):
        for x in range(width):
            # Create stone-like pattern
            base = 120
            noise = np.random.randint(-40, 40)
            r = max(20, min(200, base + noise))
            g = max(15, min(180, base - 10 + noise))
            b = max(10, min(160, base - 30 + noise))
            draw.point((x, y), (r, g, b))
    
    diffuse_path = test_output / "diffuse.png"
    diffuse.save(str(diffuse_path))
    
    # Mock normal map (bluish with some variation)
    normal = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(normal)
    for y in range(height):
        for x in range(width):
            # Normal map colors (mostly blue with slight variations)
            r = 128 + np.random.randint(-10, 10)
            g = 128 + np.random.randint(-10, 10)
            b = 255 + np.random.randint(-20, 0)  # Keep blue high
            draw.point((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(200, min(255, b))))
    
    normal_path = test_output / "normal.png"
    normal.save(str(normal_path))
    
    # Mock roughness (varied grayscale)
    roughness = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(roughness)
    for y in range(height):
        for x in range(width):
            gray = 80 + np.random.randint(-20, 60)
            gray = max(40, min(200, gray))
            draw.point((x, y), (gray, gray, gray))
    
    roughness_path = test_output / "roughness.png"
    roughness.save(str(roughness_path))
    
    # Mock metallic (mostly dark with some variation)
    metallic = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(metallic)
    for y in range(height):
        for x in range(width):
            gray = 30 + np.random.randint(-10, 20)
            gray = max(10, min(80, gray))
            draw.point((x, y), (gray, gray, gray))
    
    metallic_path = test_output / "metallic.png"
    metallic.save(str(metallic_path))
    
    # Mock AO (light with some darker areas)
    ao = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(ao)
    for y in range(height):
        for x in range(width):
            gray = 200 + np.random.randint(-50, 20)
            gray = max(100, min(255, gray))
            draw.point((x, y), (gray, gray, gray))
    
    ao_path = test_output / "ao.png"
    ao.save(str(ao_path))
    
    print(f"Created mock textures in {test_output}")
    
    # Now create a simple sphere preview
    preview_width, preview_height = 512, 512
    preview = render_sphere_preview(
        diffuse_path, normal_path, roughness_path, metallic_path, ao_path,
        preview_width, preview_height
    )
    
    # Add text overlay
    preview = add_info_overlay(preview, "Test Stone Material", {
        'diffuse': str(diffuse_path),
        'normal': str(normal_path),
        'roughness': str(roughness_path),
        'metallic': str(metallic_path),
        'ao': str(ao_path)
    })
    
    # Save preview
    preview_path = test_output / "preview.png"
    preview.save(str(preview_path))
    
    print(f"✅ Preview generated: {preview_path}")
    print(f"Preview file size: {preview_path.stat().st_size} bytes")
    
    return True

def render_sphere_preview(diffuse_path, normal_path, roughness_path, metallic_path, ao_path, width, height):
    """Render a simple sphere with PBR materials."""
    # Load textures
    diffuse_img = Image.open(diffuse_path).resize((width, height))
    normal_img = Image.open(normal_path).resize((width, height))
    roughness_img = Image.open(roughness_path).resize((width, height))
    metallic_img = Image.open(metallic_path).resize((width, height))
    ao_img = Image.open(ao_path).resize((width, height))
    
    # Convert to numpy arrays
    diffuse_data = np.array(diffuse_img) / 255.0
    normal_data = np.array(normal_img) / 255.0
    roughness_data = np.array(roughness_img)[:,:,0] / 255.0
    metallic_data = np.array(metallic_img)[:,:,0] / 255.0
    ao_data = np.array(ao_img)[:,:,0] / 255.0
    
    # Create output image
    output = Image.new('RGB', (width, height), (30, 30, 30))
    pixels = output.load()
    
    # Sphere parameters
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) * 0.35
    
    # Light direction (from top-left, slightly forward)
    light_dir = np.array([0.5, -0.5, -0.7])
    light_dir = light_dir / np.linalg.norm(light_dir)
    
    # Render each pixel
    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq <= radius * radius:
                # Calculate Z coordinate on sphere
                z = math.sqrt(radius * radius - dist_sq)
                
                # Surface normal
                normal = np.array([dx, dy, z])
                normal = normal / np.linalg.norm(normal)
                
                # UV coordinates for texture sampling
                u = 0.5 + math.atan2(dx, z) / (2 * math.pi)
                v = 0.5 - math.asin(dy / radius) / math.pi
                
                # Sample textures
                tex_x = int(u * (width - 1))
                tex_y = int(v * (height - 1))
                
                # Get material properties
                diffuse_color = diffuse_data[tex_y, tex_x]
                roughness = roughness_data[tex_y, tex_x]
                metallic = metallic_data[tex_y, tex_x]
                ao = ao_data[tex_y, tex_x]
                
                # Simple lighting calculation
                # Lambertian diffuse
                ndotl = max(0, np.dot(normal, -light_dir))
                
                # Simple specular (Phong-like)
                view_dir = np.array([0, 0, -1])
                reflect_dir = 2 * np.dot(normal, -light_dir) * normal + light_dir
                spec_power = 20 * (1 - roughness) + 1
                specular = pow(max(0, np.dot(reflect_dir, view_dir)), spec_power)
                
                # Combine lighting
                ambient = 0.1
                diffuse_light = ndotl * 0.8
                specular_light = specular * 0.5 * (1 - roughness)
                
                # Apply metallic workflow
                base_color = diffuse_color * (1 - metallic)
                spec_color = diffuse_color * metallic + np.array([0.04, 0.04, 0.04]) * (1 - metallic)
                
                # Final color
                color = base_color * (ambient + diffuse_light) + spec_color * specular_light
                color = color * ao  # Apply ambient occlusion
                
                # Gamma correction and clamp
                color = np.power(color, 1.0/2.2)
                color = np.clip(color * 255, 0, 255).astype(int)
                
                pixels[x, y] = tuple(color)
    
    return output

def add_info_overlay(image, material_name, texture_paths):
    """Add material information overlay."""
    result = image.copy()
    draw = ImageDraw.Draw(result)
    
    # Use default font
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Add material name
    text_color = (255, 255, 255)
    shadow_color = (0, 0, 0)
    
    title = f"{material_name} Preview"
    x, y = 10, 10
    
    # Draw with shadow
    if font:
        draw.text((x+1, y+1), title, font=font, fill=shadow_color)
        draw.text((x, y), title, font=font, fill=text_color)
    else:
        draw.text((x+1, y+1), title, fill=shadow_color)
        draw.text((x, y), title, fill=text_color)
    
    # Add texture list
    y += 25
    for tex_type in ['diffuse', 'normal', 'roughness', 'metallic', 'ao']:
        if tex_type in texture_paths:
            status = "✓"
            color = (100, 255, 100)
        else:
            status = "✗"
            color = (255, 100, 100)
        
        text = f"{status} {tex_type.capitalize()}"
        if font:
            draw.text((x+1, y+1), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=color)
        else:
            draw.text((x+1, y+1), text, fill=shadow_color)
            draw.text((x, y), text, fill=color)
        y += 18
    
    return result

if __name__ == "__main__":
    try:
        success = simple_pbr_preview_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)