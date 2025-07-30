#!/usr/bin/env python3
"""Test script to verify the complete texture generation pipeline."""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import directly without going through src __init__.py
import importlib.util

# Helper to import modules directly
def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the needed modules
types_config = import_module_from_file("types_config", os.path.join(current_dir, "src/types/config.py"))
types_common = import_module_from_file("types_common", os.path.join(current_dir, "src/types/common.py"))
texture_config = import_module_from_file("texture_config", os.path.join(current_dir, "src/types/texture_config.py"))
generator = import_module_from_file("generator", os.path.join(current_dir, "src/core/generator.py"))

Config = types_config.Config
TextureType = types_common.TextureType
Resolution = types_common.Resolution
ImageFormat = types_common.ImageFormat
TextureConfig = texture_config.TextureConfig
generate_textures = generator.generate_textures


async def test_pipeline():
    """Test the complete texture generation pipeline."""
    print("Testing Tessellating PBR Generator Pipeline")
    print("=" * 50)
    
    # Create test configuration
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not set. Using test mode.")
        print("To test with real OpenAI generation, set your API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print()
        api_key = "test-key"
    
    config = Config(
        material="brick wall",
        style="weathered",
        api_key=api_key,
        output_directory="./test_output",
        texture_config=TextureConfig(
            resolution=Resolution(width=512, height=512),
            format=ImageFormat.PNG,
            types=[
                TextureType.DIFFUSE,
                TextureType.NORMAL,
                TextureType.ROUGHNESS,
                TextureType.METALLIC,
                TextureType.AO,
                TextureType.HEIGHT
            ]
        )
    )
    
    # Create output directory
    Path(config.output_directory).mkdir(exist_ok=True)
    
    print(f"Configuration:")
    print(f"  Material: {config.material}")
    print(f"  Style: {config.style}")
    print(f"  Resolution: {config.texture_config.resolution.width}x{config.texture_config.resolution.height}")
    print(f"  Texture types: {[t.value for t in config.texture_config.types]}")
    print(f"  Output directory: {config.output_directory}")
    print()
    
    # Run the generator
    print("Starting texture generation...")
    try:
        results = await generate_textures(config)
        
        print("\nResults:")
        print("-" * 50)
        
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.texture_type.value}:")
            print(f"  Success: {result.success}")
            if result.success:
                print(f"  File: {result.file_path}")
                print(f"  Time: {result.generation_time:.2f}s")
            else:
                print(f"  Error: {result.error_message}")
            print()
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total = len(results)
        print(f"Summary: {successful}/{total} textures generated successfully")
        
        if successful < total:
            print("\nNote: Some textures failed. This might be due to:")
            print("- Missing OPENAI_API_KEY environment variable")
            print("- Incomplete module implementations")
            print("- Network connectivity issues")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_pipeline())