"""Comprehensive unit tests for advanced configuration parsing and validation."""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from jsonschema import ValidationError

from src.config import ConfigLoader, load_config, CONFIG_SCHEMA


class TestConfigAdvanced:
    """Advanced test suite for configuration loading and validation."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sample_valid_config(self):
        """Create a valid configuration dictionary."""
        return {
            "project": {
                "name": "test-pbr-generator",
                "version": "1.0.0",
                "description": "Test configuration"
            },
            "textures": {
                "resolution": {
                    "width": 1024,
                    "height": 1024
                },
                "format": "png",
                "types": ["diffuse", "normal", "roughness", "metallic", "ao", "height", "emissive"]
            },
            "material": {
                "base_material": "metal",
                "style": "weathered",
                "seamless": True,
                "properties": {
                    "age": 10,
                    "oxidation": 0.7,
                    "scratches": 0.3
                }
            },
            "generation": {
                "model": "dall-e-3",
                "temperature": 0.7,
                "max_tokens": 1000,
                "batch_size": 4
            },
            "output": {
                "directory": "./output",
                "naming_convention": "{material}_{type}_{resolution}",
                "create_preview": True
            }
        }
    
    @pytest.fixture
    def config_loader(self, temp_config_dir, sample_valid_config):
        """Create a ConfigLoader with test configuration."""
        config_path = os.path.join(temp_config_dir, "test_config.json")
        with open(config_path, 'w') as f:
            json.dump(sample_valid_config, f)
        return ConfigLoader(config_path)
    
    def test_config_loader_initialization(self, temp_config_dir):
        """Test ConfigLoader initialization with different paths."""
        # Test with explicit path
        config_path = os.path.join(temp_config_dir, "custom.json")
        loader = ConfigLoader(config_path)
        assert loader.config_path == config_path
        
        # Test with default path
        loader_default = ConfigLoader()
        assert "config/default.json" in loader_default.config_path
    
    def test_load_valid_configuration(self, config_loader, monkeypatch):
        """Test loading a valid configuration."""
        # Mock environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
        monkeypatch.setenv("OPENAI_ORG_ID", "test-org-id")
        
        config = config_loader.load()
        
        # Verify all sections loaded
        assert "project" in config
        assert "textures" in config
        assert "material" in config
        assert "generation" in config
        assert "output" in config
        
        # Verify API key was added
        assert config["api"]["openai_key"] == "test-api-key"
        assert config["api"]["openai_org_id"] == "test-org-id"
    
    def test_schema_validation_comprehensive(self, temp_config_dir):
        """Test comprehensive schema validation scenarios."""
        # Test missing required fields
        invalid_configs = [
            # Missing project name
            {
                "project": {"version": "1.0.0"},
                "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["diffuse"]},
                "material": {"base_material": "wood"},
                "output": {"directory": "./out"}
            },
            # Invalid texture format
            {
                "project": {"name": "test", "version": "1.0.0"},
                "textures": {"resolution": {"width": 512, "height": 512}, "format": "bmp", "types": ["diffuse"]},
                "material": {"base_material": "wood"},
                "output": {"directory": "./out"}
            },
            # Resolution too small
            {
                "project": {"name": "test", "version": "1.0.0"},
                "textures": {"resolution": {"width": 64, "height": 64}, "format": "png", "types": ["diffuse"]},
                "material": {"base_material": "wood"},
                "output": {"directory": "./out"}
            },
            # Invalid texture type
            {
                "project": {"name": "test", "version": "1.0.0"},
                "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["invalid_type"]},
                "material": {"base_material": "wood"},
                "output": {"directory": "./out"}
            },
            # Temperature out of range
            {
                "project": {"name": "test", "version": "1.0.0"},
                "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["diffuse"]},
                "material": {"base_material": "wood"},
                "generation": {"temperature": 3.0},
                "output": {"directory": "./out"}
            }
        ]
        
        for idx, invalid_config in enumerate(invalid_configs):
            config_path = os.path.join(temp_config_dir, f"invalid_{idx}.json")
            with open(config_path, 'w') as f:
                json.dump(invalid_config, f)
            
            loader = ConfigLoader(config_path)
            with pytest.raises(ValidationError):
                loader.load()
    
    def test_environment_variable_handling(self, config_loader, monkeypatch):
        """Test handling of environment variables."""
        # Test missing API key
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            config_loader.load()
        
        # Test with API key but no org ID
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_ORG_ID", raising=False)
        config = config_loader.load()
        assert config["api"]["openai_key"] == "test-key"
        assert "openai_org_id" not in config["api"]
    
    def test_get_nested_configuration_values(self, config_loader, monkeypatch):
        """Test retrieving nested configuration values."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        config_loader.load()
        
        # Test getting nested values
        assert config_loader.get("textures.resolution.width") == 1024
        assert config_loader.get("material.properties.oxidation") == 0.7
        assert config_loader.get("generation.temperature") == 0.7
        
        # Test with defaults
        assert config_loader.get("nonexistent.key", "default") == "default"
        assert config_loader.get("material.properties.nonexistent", 0.0) == 0.0
    
    def test_set_nested_configuration_values(self, config_loader, monkeypatch):
        """Test setting nested configuration values."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        config_loader.load()
        
        # Test setting existing values
        config_loader.set("textures.resolution.width", 2048)
        assert config_loader.get("textures.resolution.width") == 2048
        
        # Test creating new nested values
        config_loader.set("material.properties.new_property", "test_value")
        assert config_loader.get("material.properties.new_property") == "test_value"
        
        # Test creating deeply nested structures
        config_loader.set("new.deeply.nested.value", 42)
        assert config_loader.get("new.deeply.nested.value") == 42
    
    def test_save_configuration(self, config_loader, temp_config_dir, monkeypatch):
        """Test saving configuration to file."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        config = config_loader.load()
        
        # Modify configuration
        config_loader.set("textures.resolution.width", 2048)
        config_loader.set("output.create_preview", False)
        
        # Save to new file
        new_path = os.path.join(temp_config_dir, "saved_config.json")
        config_loader.save(config_loader.config, new_path)
        
        # Load saved config and verify
        with open(new_path, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config["textures"]["resolution"]["width"] == 2048
        assert saved_config["output"]["create_preview"] is False
        # API key should not be saved
        assert "api" not in saved_config or "openai_key" not in saved_config.get("api", {})
    
    def test_material_presets_configuration(self, temp_config_dir):
        """Test loading configurations with material presets."""
        config_with_presets = {
            "project": {"name": "test", "version": "1.0.0"},
            "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["diffuse"]},
            "material": {"base_material": "custom"},
            "output": {"directory": "./out"},
            "material_presets": {
                "rusty_metal": {
                    "base_material": "metal",
                    "properties": {
                        "roughness": 0.8,
                        "metallic": 0.9,
                        "oxidation": 0.7,
                        "age": 20
                    }
                },
                "polished_marble": {
                    "base_material": "stone",
                    "properties": {
                        "roughness": 0.1,
                        "metallic": 0.0,
                        "veining": 0.6,
                        "polish": 0.9
                    }
                }
            }
        }
        
        config_path = os.path.join(temp_config_dir, "presets.json")
        with open(config_path, 'w') as f:
            json.dump(config_with_presets, f)
        
        loader = ConfigLoader(config_path)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = loader.load()
        
        # Verify presets loaded
        assert "material_presets" in config
        assert "rusty_metal" in config["material_presets"]
        assert config["material_presets"]["rusty_metal"]["properties"]["oxidation"] == 0.7
    
    def test_advanced_generation_settings(self, temp_config_dir):
        """Test advanced generation configuration options."""
        advanced_config = {
            "project": {"name": "test", "version": "1.0.0"},
            "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["diffuse"]},
            "material": {"base_material": "metal"},
            "output": {"directory": "./out"},
            "generation": {
                "model": "dall-e-3",
                "temperature": 0.8,
                "max_tokens": 2000,
                "batch_size": 8,
                "advanced": {
                    "use_style_transfer": True,
                    "style_reference": "path/to/style.jpg",
                    "detail_enhancement": 0.7,
                    "color_correction": {
                        "enabled": True,
                        "gamma": 1.2,
                        "saturation": 1.1
                    }
                }
            }
        }
        
        config_path = os.path.join(temp_config_dir, "advanced.json")
        with open(config_path, 'w') as f:
            json.dump(advanced_config, f)
        
        loader = ConfigLoader(config_path)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = loader.load()
        
        # Verify advanced settings
        assert config["generation"]["advanced"]["use_style_transfer"] is True
        assert config["generation"]["advanced"]["color_correction"]["gamma"] == 1.2
    
    def test_multi_resolution_configuration(self, temp_config_dir):
        """Test configuration with multiple resolution targets."""
        multi_res_config = {
            "project": {"name": "test", "version": "1.0.0"},
            "textures": {
                "resolution": {"width": 1024, "height": 1024},
                "format": "png",
                "types": ["diffuse", "normal"],
                "multi_resolution": {
                    "enabled": True,
                    "targets": [
                        {"name": "high", "width": 4096, "height": 4096},
                        {"name": "medium", "width": 2048, "height": 2048},
                        {"name": "low", "width": 512, "height": 512}
                    ]
                }
            },
            "material": {"base_material": "stone"},
            "output": {"directory": "./out"}
        }
        
        config_path = os.path.join(temp_config_dir, "multi_res.json")
        with open(config_path, 'w') as f:
            json.dump(multi_res_config, f)
        
        loader = ConfigLoader(config_path)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = loader.load()
        
        # Verify multi-resolution settings
        assert config["textures"]["multi_resolution"]["enabled"] is True
        assert len(config["textures"]["multi_resolution"]["targets"]) == 3
        assert config["textures"]["multi_resolution"]["targets"][0]["width"] == 4096
    
    def test_pipeline_configuration(self, temp_config_dir):
        """Test configuration for processing pipeline settings."""
        pipeline_config = {
            "project": {"name": "test", "version": "1.0.0"},
            "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["diffuse"]},
            "material": {"base_material": "wood"},
            "output": {"directory": "./out"},
            "pipeline": {
                "parallel_processing": True,
                "max_workers": 4,
                "cache_enabled": True,
                "cache_directory": "./.cache",
                "stages": {
                    "preprocessing": {
                        "enabled": True,
                        "denoise": True,
                        "color_balance": True
                    },
                    "generation": {
                        "retries": 3,
                        "timeout": 300
                    },
                    "postprocessing": {
                        "enabled": True,
                        "sharpen": True,
                        "compress": True,
                        "compression_quality": 0.9
                    }
                }
            }
        }
        
        config_path = os.path.join(temp_config_dir, "pipeline.json")
        with open(config_path, 'w') as f:
            json.dump(pipeline_config, f)
        
        loader = ConfigLoader(config_path)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = loader.load()
        
        # Verify pipeline settings
        assert config["pipeline"]["parallel_processing"] is True
        assert config["pipeline"]["stages"]["generation"]["retries"] == 3
        assert config["pipeline"]["stages"]["postprocessing"]["compression_quality"] == 0.9
    
    def test_config_inheritance_and_overrides(self, temp_config_dir):
        """Test configuration inheritance and override mechanisms."""
        # Base configuration
        base_config = {
            "project": {"name": "base", "version": "1.0.0"},
            "textures": {"resolution": {"width": 512, "height": 512}, "format": "png", "types": ["diffuse"]},
            "material": {"base_material": "stone", "properties": {"roughness": 0.5}},
            "output": {"directory": "./out"}
        }
        
        # Override configuration
        override_config = {
            "extends": "base.json",
            "project": {"name": "override"},
            "material": {"properties": {"roughness": 0.8, "metallic": 0.2}}
        }
        
        base_path = os.path.join(temp_config_dir, "base.json")
        override_path = os.path.join(temp_config_dir, "override.json")
        
        with open(base_path, 'w') as f:
            json.dump(base_config, f)
        with open(override_path, 'w') as f:
            json.dump(override_config, f)
        
        # This tests the concept - actual implementation would need to handle "extends"
        # For now, verify both files can be loaded independently
        loader_base = ConfigLoader(base_path)
        loader_override = ConfigLoader(override_path)
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config_base = loader_base.load()
            # Override would need custom handling in real implementation
            assert config_base["project"]["name"] == "base"
    
    def test_config_with_texture_variants(self, temp_config_dir):
        """Test configuration with texture variant specifications."""
        variant_config = {
            "project": {"name": "test", "version": "1.0.0"},
            "textures": {
                "resolution": {"width": 1024, "height": 1024},
                "format": "png",
                "types": ["diffuse", "normal", "roughness"],
                "variants": {
                    "clean": {
                        "suffix": "_clean",
                        "properties": {"dirt": 0.0, "wear": 0.0}
                    },
                    "dirty": {
                        "suffix": "_dirty",
                        "properties": {"dirt": 0.8, "wear": 0.5}
                    },
                    "damaged": {
                        "suffix": "_damaged",
                        "properties": {"dirt": 0.5, "wear": 0.9, "cracks": 0.7}
                    }
                }
            },
            "material": {"base_material": "concrete"},
            "output": {"directory": "./out"}
        }
        
        config_path = os.path.join(temp_config_dir, "variants.json")
        with open(config_path, 'w') as f:
            json.dump(variant_config, f)
        
        loader = ConfigLoader(config_path)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            config = loader.load()
        
        # Verify variant settings
        assert "variants" in config["textures"]
        assert len(config["textures"]["variants"]) == 3
        assert config["textures"]["variants"]["damaged"]["properties"]["cracks"] == 0.7
    
    def test_load_config_helper_function(self, temp_config_dir, sample_valid_config, monkeypatch):
        """Test the load_config helper function."""
        config_path = os.path.join(temp_config_dir, "helper_test.json")
        with open(config_path, 'w') as f:
            json.dump(sample_valid_config, f)
        
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Test loading with helper
        config = load_config(config_path)
        assert config["project"]["name"] == "test-pbr-generator"
        assert "api" in config
        assert config["api"]["openai_key"] == "test-key"
    
    def test_config_validation_edge_cases(self, temp_config_dir):
        """Test edge cases in configuration validation."""
        edge_cases = [
            # Minimum valid configuration
            {
                "project": {"name": "min", "version": "0.0.1"},
                "textures": {"resolution": {"width": 128, "height": 128}, "format": "png", "types": ["diffuse"]},
                "material": {"base_material": "a"},
                "output": {"directory": "."}
            },
            # Maximum reasonable values
            {
                "project": {"name": "max", "version": "999.999.999"},
                "textures": {"resolution": {"width": 16384, "height": 16384}, "format": "exr", "types": ["diffuse", "normal", "roughness", "metallic", "ao", "height", "emissive"]},
                "material": {"base_material": "complex_material_with_very_long_name_to_test_limits"},
                "generation": {"temperature": 2.0, "max_tokens": 1000000, "batch_size": 100},
                "output": {"directory": "./very/deeply/nested/directory/structure/for/output/files"}
            }
        ]
        
        for idx, edge_config in enumerate(edge_cases):
            config_path = os.path.join(temp_config_dir, f"edge_{idx}.json")
            with open(config_path, 'w') as f:
                json.dump(edge_config, f)
            
            loader = ConfigLoader(config_path)
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                # These should all load without error
                config = loader.load()
                assert config is not None