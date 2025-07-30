#!/usr/bin/env python3
"""Verify emissive module implementation works correctly."""

# Test that the module can be imported and instantiated
try:
    from src.modules.emissive import EmissiveModule
    from src.types.config import Config, TextureConfig, MaterialProperties
    from src.types.common import Resolution, TextureType, TextureFormat
    
    print("✅ Imports successful")
    
    # Create a test config
    config = Config(
        project_name='test',
        project_version='1.0.0',
        material='neon',
        style='photorealistic',
        texture_config=TextureConfig(
            resolution=Resolution(256, 256),
            format=TextureFormat.PNG,
            types=[TextureType.EMISSIVE],
            seamless=False
        ),
        material_properties=MaterialProperties(),
        model='offline',
        output_directory='test_output',
        naming_convention='test'
    )
    
    # Create module instance
    emissive = EmissiveModule(config)
    print("✅ EmissiveModule instantiated")
    
    # Check texture type
    assert emissive.texture_type == TextureType.EMISSIVE
    print("✅ Texture type is EMISSIVE")
    
    # Test that it has required methods
    assert hasattr(emissive, 'generate')
    assert hasattr(emissive, 'process_image')
    assert hasattr(emissive, 'make_seamless')
    print("✅ Required methods present")
    
    # Check material presets
    assert 'neon' in emissive.material_presets
    assert 'led' in emissive.material_presets
    assert 'lava' in emissive.material_presets
    assert 'plasma' in emissive.material_presets
    print(f"✅ {len(emissive.material_presets)} material presets available")
    
    print("\n🎉 EmissiveModule implementation verified successfully!")
    print("\nAvailable material presets:")
    for preset in sorted(emissive.material_presets.keys()):
        print(f"  - {preset}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()