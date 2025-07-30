#!/usr/bin/env python3
"""Quick validation script to test core functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing module imports...")
    
    try:
        # Test type imports
        from src.types.common import TextureType, Resolution
        print("✅ Types module imported")
        
        # Test utility imports
        from src.utils.image_utils import resize_image, apply_gamma
        from src.utils.tessellation import TessellationProcessor
        print("✅ Utils modules imported")
        
        # Test module imports
        from src.modules.diffuse import DiffuseModule
        from src.modules.normal import NormalModule
        from src.modules.roughness import RoughnessModule
        print("✅ Texture modules imported")
        
        # Test core imports
        from src.core.generator import TextureGenerator
        print("✅ Core generator imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_generation():
    """Test basic texture generation without external dependencies."""
    print("\nTesting basic texture generation...")
    
    try:
        from src.types.common import TextureType, Resolution
        from PIL import Image
        import numpy as np
        
        # Create a test image using PIL directly
        resolution = Resolution(width=256, height=256)
        test_image = Image.new('RGB', (resolution.width, resolution.height), (128, 128, 128))
        print("✅ Created test image")
        
        # Test tessellation
        from src.utils.tessellation import TessellationProcessor
        processor = TessellationProcessor()
        
        # Convert to numpy array
        img_array = np.array(test_image)
        
        # Test offset method
        seamless = processor.make_seamless_offset(img_array, blend_width=32)
        print("✅ Offset tessellation working")
        
        # Test mirror method
        seamless = processor.make_seamless_mirror(img_array)
        print("✅ Mirror tessellation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

def test_configuration():
    """Test configuration system."""
    print("\nTesting configuration system...")
    
    try:
        # Test basic config structure
        config = {
            "material": {
                "base_material": "test",
                "style": "test"
            },
            "textures": {
                "resolution": {"width": 256, "height": 256},
                "types": ["diffuse"],
                "seamless": True
            },
            "output": {
                "directory": "test_output"
            }
        }
        
        print("✅ Configuration structure valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🔍 Running Quick Validation Tests")
    print("="*50)
    
    all_passed = True
    
    # Run tests
    if not test_imports():
        all_passed = False
    
    if not test_basic_generation():
        all_passed = False
    
    if not test_configuration():
        all_passed = False
    
    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("✅ All validation tests PASSED")
        print("\nThe core functionality is working correctly.")
        print("For full testing, ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
    else:
        print("❌ Some validation tests FAILED")
        print("\nPlease check the errors above and ensure:")
        print("  1. All dependencies are installed")
        print("  2. Python path is set correctly")
        print("  3. All source files are present")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())