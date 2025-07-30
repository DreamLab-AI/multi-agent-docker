"""Test script to verify the complete texture generation pipeline."""

import asyncio
import os
from pathlib import Path
from .types.config import Config, TextureConfig, MaterialProperties
from .types.common import TextureType, Resolution, TextureFormat as ImageFormat
from .core.generator import generate_textures


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
    
    # Create material properties
    material_props = MaterialProperties(
        roughness_range=(0.3, 0.8),
        metallic_value=0.1,
        normal_strength=1.0,
        ao_intensity=0.8
    )
    
    # Create texture config
    texture_config = TextureConfig(
        resolution=Resolution(width=512, height=512),
        format=ImageFormat.PNG,
        types=[
            TextureType.DIFFUSE,
            TextureType.NORMAL,
            TextureType.ROUGHNESS,
            TextureType.METALLIC,
            TextureType.AMBIENT_OCCLUSION,
            TextureType.HEIGHT
        ]
    )
    
    config = Config(
        project_name="Test Project",
        project_version="1.0.0",
        texture_config=texture_config,
        material="brick wall",
        style="weathered",
        material_properties=material_props,
        model="dall-e-3",
        output_directory="./test_output",
        naming_convention="{material}_{type}_{resolution}",
        api_key=api_key
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


def main():
    """Run the test."""
    asyncio.run(test_pipeline())


if __name__ == "__main__":
    main()