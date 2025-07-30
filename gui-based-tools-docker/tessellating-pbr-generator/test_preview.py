#!/usr/bin/env python3
"""Test script for preview generation functionality."""

import sys
import asyncio
from pathlib import Path
from src.config import load_config
from src.types.config import Config
from src.utils.preview import generate_material_preview
from src.utils.logging import setup_logger, get_logger


async def test_preview_generation():
    """Test the preview generation with sample textures."""
    setup_logger(debug=True)
    logger = get_logger(__name__)
    
    logger.info("Testing preview generation...")
    
    # Create test output directory
    test_output = Path("test_preview_output")
    test_output.mkdir(exist_ok=True)
    
    # Check if we have any existing textures in the output directory
    output_dir = Path("output")
    if not output_dir.exists():
        logger.warning("No output directory found. Generate some textures first.")
        return False
    
    # Find existing texture files
    texture_files = list(output_dir.glob("*.png"))
    if not texture_files:
        logger.warning("No texture files found in output directory.")
        return False
    
    # Try to identify texture types from filenames
    texture_paths = {}
    for file_path in texture_files:
        filename = file_path.name.lower()
        if 'diffuse' in filename:
            texture_paths['diffuse'] = str(file_path)
        elif 'normal' in filename:
            texture_paths['normal'] = str(file_path)
        elif 'roughness' in filename:
            texture_paths['roughness'] = str(file_path)
        elif 'metallic' in filename:
            texture_paths['metallic'] = str(file_path)
        elif 'ao' in filename:
            texture_paths['ao'] = str(file_path)
        elif 'height' in filename:
            texture_paths['height'] = str(file_path)
    
    logger.info(f"Found textures: {list(texture_paths.keys())}")
    
    # Generate preview
    preview_path = generate_material_preview(
        material_name="Test Material",
        texture_paths=texture_paths,
        output_dir=str(test_output),
        preview_size=(512, 512)
    )
    
    if preview_path:
        logger.info(f"Preview generated successfully: {preview_path}")
        return True
    else:
        logger.error("Failed to generate preview")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_preview_generation())
    sys.exit(0 if success else 1)