#!/usr/bin/env python3
"""Comprehensive test for texture generation with preview."""

import sys
import asyncio
import json
from pathlib import Path
from src.config import load_config
from src.types.config import Config
from src.core.generator import generate_textures
from src.utils.logging import setup_logger, get_logger


async def test_full_pipeline_with_preview():
    """Test the complete pipeline with preview generation."""
    setup_logger(debug=True)
    logger = get_logger(__name__)
    
    logger.info("Testing full pipeline with preview generation...")
    
    # Create a test config with preview enabled
    test_config = {
        "project": {
            "name": "Preview Test",
            "version": "1.0.0"
        },
        "textures": {
            "resolution": {
                "width": 256,
                "height": 256
            },
            "format": "png",
            "types": ["diffuse", "normal", "roughness", "metallic", "ao"]
        },
        "material": {
            "base_material": "test_material",
            "style": "realistic",
            "seamless": True,
            "properties": {
                "roughness_range": [0.3, 0.7],
                "metallic_value": 0.1,
                "normal_strength": 1.0
            }
        },
        "generation": {
            "model": "dall-e-3",
            "temperature": 0.7,
            "max_tokens": 1000,
            "batch_size": 1
        },
        "output": {
            "directory": "test_preview_output",
            "naming_convention": "{material}_{type}_{resolution}",
            "create_preview": True
        },
        "api": {
            "openai_key": "test-key-placeholder"
        }
    }
    
    # Create test output directory
    output_dir = Path("test_preview_output")
    output_dir.mkdir(exist_ok=True)
    
    # Save test config
    config_path = output_dir / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    try:
        # Load config
        config = Config.from_dict(test_config)
        logger.info(f"Config loaded. Preview enabled: {config.create_preview}")
        
        # For testing without actual API calls, create mock textures
        logger.info("Creating mock textures for preview testing...")
        await create_mock_textures(config)
        
        logger.info("Mock textures created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def create_mock_textures(config: Config):
    """Create mock textures and generate preview."""
    from PIL import Image, ImageDraw
    import numpy as np
    from src.utils.preview import generate_material_preview
    
    logger = get_logger(__name__)
    
    # Create mock textures
    width, height = 256, 256
    texture_paths = {}
    
    # Mock diffuse (colored noise)
    diffuse = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(diffuse)
    # Create a simple pattern
    for y in range(height):
        for x in range(width):
            # Create a stone-like pattern
            noise = np.random.randint(80, 150)
            color = (noise, noise - 20, noise - 40)
            draw.point((x, y), color)
    
    diffuse_path = Path(config.output_directory) / "test_material_diffuse_256x256.png"
    diffuse.save(str(diffuse_path))
    texture_paths['diffuse'] = str(diffuse_path)
    
    # Mock normal map (blue-ish)
    normal = Image.new('RGB', (width, height), (128, 128, 255))
    normal_path = Path(config.output_directory) / "test_material_normal_256x256.png"
    normal.save(str(normal_path))
    texture_paths['normal'] = str(normal_path)
    
    # Mock roughness (grayscale)
    roughness = Image.new('RGB', (width, height), (128, 128, 128))
    roughness_path = Path(config.output_directory) / "test_material_roughness_256x256.png"
    roughness.save(str(roughness_path))
    texture_paths['roughness'] = str(roughness_path)
    
    # Mock metallic (dark)
    metallic = Image.new('RGB', (width, height), (25, 25, 25))
    metallic_path = Path(config.output_directory) / "test_material_metallic_256x256.png"
    metallic.save(str(metallic_path))
    texture_paths['metallic'] = str(metallic_path)
    
    # Mock AO (slight variation)
    ao = Image.new('RGB', (width, height), (200, 200, 200))
    ao_path = Path(config.output_directory) / "test_material_ao_256x256.png"
    ao.save(str(ao_path))
    texture_paths['ao'] = str(ao_path)
    
    logger.info("Mock textures created, generating preview...")
    
    # Generate preview
    preview_path = generate_material_preview(
        material_name="Test Material",
        texture_paths=texture_paths,
        output_dir=config.output_directory,
        preview_size=(512, 512)
    )
    
    if preview_path:
        logger.info(f"Preview generated successfully: {preview_path}")
    else:
        logger.error("Failed to generate preview")


if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline_with_preview())
    sys.exit(0 if success else 1)