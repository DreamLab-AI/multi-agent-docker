#!/usr/bin/env python3
"""Example of how to use the preview generation feature."""

import asyncio
from pathlib import Path

# Example of using the --preview flag with the main application
print("PBR Material Preview Generation Examples")
print("=" * 50)

print("\n1. Using the command line interface:")
print("   python main.py --preview")
print("   python main.py --material stone --preview")
print("   python main.py --config config/stone.json --preview")

print("\n2. Preview will be automatically generated when:")
print("   - The --preview flag is used")
print("   - create_preview is set to true in the config file")

print("\n3. The preview shows:")
print("   ✓ A 3D sphere with your PBR material applied")
print("   ✓ Realistic lighting showing material properties")
print("   ✓ A list of which texture types were generated")
print("   ✓ Visual feedback on diffuse, normal, roughness, metallic, AO maps")

print("\n4. Preview features:")
print("   • Simple raytracing-based sphere rendering")
print("   • Proper PBR lighting calculations")
print("   • Normal mapping support")
print("   • Roughness and metallic workflow")
print("   • Ambient occlusion integration")
print("   • Material information overlay")

print("\n5. Technical details:")
print("   • Preview resolution: 512x512 pixels")
print("   • Output file: preview.png in the output directory")
print("   • Uses PIL/Pillow for rendering (no external 3D dependencies)")
print("   • Implements simplified PBR lighting model")
print("   • Supports all standard PBR texture types")

print("\n6. Configuration example:")
config_example = '''
{
  "output": {
    "directory": "my_materials",
    "create_preview": true
  }
}
'''
print("   Add to your config file:")
print(config_example)

print("\n7. Integration in your workflow:")
print("""
   The preview generation is automatically integrated into the 
   texture generation pipeline. When enabled, it will:
   
   a) Generate all requested PBR textures
   b) Apply tessellation for seamless tiling
   c) Create a 3D preview showing the final material
   d) Save everything to the output directory
   
   This gives you immediate visual feedback on how your 
   generated material will look in a 3D environment.
""")

print("\nPreview generation is now ready to use!")
print("Run: python test_preview_direct.py to see a working example")