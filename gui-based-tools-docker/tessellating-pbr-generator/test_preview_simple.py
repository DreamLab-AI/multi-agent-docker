#!/usr/bin/env python3
"""Simple test for preview generation without dependencies."""

import sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from utils.preview import generate_material_preview
    from utils.logging import setup_logger, get_logger
    
    def test_preview_simple():
        """Test preview generation with simple mock textures."""
        setup_logger(debug=True)
        logger = get_logger(__name__)
        
        logger.info("Testing simple preview generation...")
        
        # Create test output directory
        test_output = Path("test_simple_preview")
        test_output.mkdir(exist_ok=True)
        
        # Create simple mock textures
        width, height = 128, 128
        texture_paths = {}
        
        # Mock diffuse (brown/tan)
        diffuse = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(diffuse)
        for y in range(height):
            for x in range(width):
                # Simple noise pattern
                base = 120
                noise = np.random.randint(-30, 30)
                r = max(0, min(255, base + noise))
                g = max(0, min(255, base - 10 + noise))
                b = max(0, min(255, base - 30 + noise))
                draw.point((x, y), (r, g, b))
        
        diffuse_path = test_output / "diffuse.png"
        diffuse.save(str(diffuse_path))
        texture_paths['diffuse'] = str(diffuse_path)
        
        # Mock normal map (bluish)
        normal = Image.new('RGB', (width, height), (128, 128, 255))
        normal_path = test_output / "normal.png"
        normal.save(str(normal_path))
        texture_paths['normal'] = str(normal_path)
        
        # Mock roughness (gray)
        roughness = Image.new('RGB', (width, height), (100, 100, 100))
        roughness_path = test_output / "roughness.png"
        roughness.save(str(roughness_path))
        texture_paths['roughness'] = str(roughness_path)
        
        # Mock metallic (dark)
        metallic = Image.new('RGB', (width, height), (20, 20, 20))
        metallic_path = test_output / "metallic.png"
        metallic.save(str(metallic_path))
        texture_paths['metallic'] = str(metallic_path)
        
        # Mock AO (light gray)
        ao = Image.new('RGB', (width, height), (180, 180, 180))
        ao_path = test_output / "ao.png"
        ao.save(str(ao_path))
        texture_paths['ao'] = str(ao_path)
        
        logger.info(f"Created mock textures: {list(texture_paths.keys())}")
        
        # Generate preview
        preview_path = generate_material_preview(
            material_name="Simple Test Material",
            texture_paths=texture_paths,
            output_dir=str(test_output),
            preview_size=(512, 512)
        )
        
        if preview_path and Path(preview_path).exists():
            logger.info(f"✅ Preview generated successfully: {preview_path}")
            file_size = Path(preview_path).stat().st_size
            logger.info(f"Preview file size: {file_size} bytes")
            return True
        else:
            logger.error("❌ Failed to generate preview")
            return False
    
    if __name__ == "__main__":
        success = test_preview_simple()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Could not import preview module")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)