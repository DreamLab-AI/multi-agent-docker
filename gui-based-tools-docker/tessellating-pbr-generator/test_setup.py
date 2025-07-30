#!/usr/bin/env python3
"""Test script to verify the Python setup and configuration."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config, ConfigLoader
from src.types.config import Config
from src.types.common import TextureType, TextureFormat, Resolution

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    # Test core imports
    try:
        from src.core import generate_textures
        print("✓ Core imports successful")
    except ImportError as e:
        print(f"✗ Core import failed: {e}")
    
    # Test interface imports
    try:
        from src.interfaces import OpenAIInterface, BlenderInterface
        print("✓ Interface imports successful")
    except ImportError as e:
        print(f"✗ Interface import failed: {e}")
    
    # Test module imports
    try:
        from src.modules import (
            DiffuseModule, NormalModule, RoughnessModule,
            MetallicModule, AmbientOcclusionModule, HeightModule
        )
        print("✓ Module imports successful")
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
    
    # Test utils imports
    try:
        from src.utils import setup_logger, get_logger, validate_config
        print("✓ Utils imports successful")
    except ImportError as e:
        print(f"✗ Utils import failed: {e}")

def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration loading...")
    
    try:
        # Debug config path
        from src.config import ConfigLoader
        loader = ConfigLoader()
        print(f"Config path: {loader.config_path}")
        
        # Load default config
        config_dict = load_config()
        print("✓ Configuration loaded successfully")
        
        # Create Config object
        config = Config.from_dict(config_dict)
        print("✓ Config object created successfully")
        
        # Test config values
        print(f"\nConfiguration details:")
        print(f"  Project: {config.project_name} v{config.project_version}")
        print(f"  Material: {config.material} ({config.style})")
        print(f"  Resolution: {config.texture_config.resolution}")
        print(f"  Format: {config.texture_config.format.value}")
        print(f"  Texture types: {[t.value for t in config.texture_config.types]}")
        print(f"  Output directory: {config.output_directory}")
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")

def test_types():
    """Test type definitions."""
    print("\nTesting type definitions...")
    
    # Test TextureType enum
    print(f"Available texture types: {[t.value for t in TextureType]}")
    
    # Test TextureFormat enum
    print(f"Available formats: {[f.value for f in TextureFormat]}")
    
    # Test Resolution
    res = Resolution(2048, 2048)
    print(f"Resolution: {res}")
    
    # Test Resolution from string
    res2 = Resolution.from_string("1024x1024")
    print(f"Resolution from string: {res2}")

def test_environment():
    """Test environment setup."""
    print("\nTesting environment...")
    
    import os
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file found")
    else:
        print("✗ .env file not found (using .env.example as template)")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✓ OpenAI API key is set")
    else:
        print("✗ OpenAI API key not set (required for generation)")

def main():
    """Run all tests."""
    print("=== Tessellating PBR Generator Setup Test ===\n")
    
    test_imports()
    test_config_loading()
    test_types()
    test_environment()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()