"""
Unit tests for the main PBR generator class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import json
from PIL import Image
import numpy as np
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.generator import PBRGenerator


class TestPBRGenerator:
    """Test the main PBR generator functionality."""
    
    def test_generator_initialization(self):
        """Test generator initialization with API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            assert generator.api_key == 'test-key'
    
    def test_generator_no_api_key(self):
        """Test generator raises error without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                PBRGenerator()
    
    def test_load_config(self, test_config_path):
        """Test loading configuration from file."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            config = generator._load_config(test_config_path)
            
            assert 'materials' in config
            assert 'stone' in config['materials']
            assert config['materials']['stone']['properties']['roughness'] == 0.8
    
    def test_get_material_config(self, test_config_path):
        """Test retrieving material configuration."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            generator.config = generator._load_config(test_config_path)
            
            stone_config = generator._get_material_config('stone')
            assert stone_config['properties']['roughness'] == 0.8
            
            # Test default material
            default_config = generator._get_material_config('unknown')
            assert default_config is not None
    
    @patch('openai.OpenAI')
    def test_generate_diffuse_map(self, mock_openai_class, mock_image_download):
        """Test diffuse map generation from OpenAI."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate diffuse map
            diffuse = generator.generate_diffuse_map(
                prompt="rocky surface",
                size=512
            )
            
            assert isinstance(diffuse, Image.Image)
            assert diffuse.size == (512, 512)
            
            # Check API was called correctly
            mock_client.images.generate.assert_called_once()
            call_args = mock_client.images.generate.call_args
            assert "rocky surface" in call_args[1]['prompt']
            assert call_args[1]['size'] == "512x512"
    
    @patch('openai.OpenAI')
    def test_generate_material_complete(self, mock_openai_class, mock_image_download, temp_dir):
        """Test complete material generation pipeline."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate complete material
            output_dir = os.path.join(temp_dir, 'test_material')
            generator.generate_material(
                prompt="metal surface",
                output_dir=output_dir,
                material_type="metal",
                size=256
            )
            
            # Check all files were created
            expected_files = [
                'metal_surface_diffuse.png',
                'metal_surface_normal.png',
                'metal_surface_roughness.png',
                'metal_surface_height.png',
                'metal_surface_ao.png',
                'metal_surface_metallic.png'
            ]
            
            for filename in expected_files:
                filepath = os.path.join(output_dir, filename)
                assert os.path.exists(filepath), f"Missing {filename}"
                
                # Verify it's a valid image
                img = Image.open(filepath)
                assert img.size == (256, 256)
    
    @patch('openai.OpenAI')
    def test_generate_with_config(self, mock_openai_class, mock_image_download, temp_dir, test_config_path):
        """Test generation with custom configuration."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            generator.config = generator._load_config(test_config_path)
            
            output_dir = os.path.join(temp_dir, 'configured_material')
            generator.generate_material(
                prompt="stone wall",
                output_dir=output_dir,
                material_type="stone",
                size=256
            )
            
            # Load roughness map and check it matches config
            roughness_path = os.path.join(output_dir, 'stone_wall_roughness.png')
            roughness_img = Image.open(roughness_path)
            roughness_array = np.array(roughness_img)
            
            # Stone has roughness 0.8 in config
            expected_roughness = int(0.8 * 255)
            mean_roughness = np.mean(roughness_array)
            
            # Should be roughly in the right range
            assert abs(mean_roughness - expected_roughness) < 100
    
    @patch('openai.OpenAI')
    def test_error_handling(self, mock_openai_class):
        """Test error handling in generation."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.images.generate.side_effect = Exception("API Error")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            with pytest.raises(Exception, match="API Error"):
                generator.generate_diffuse_map("test prompt")
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Test various prompt formats
            assert generator._sanitize_filename("simple prompt") == "simple_prompt"
            assert generator._sanitize_filename("with/slash") == "with_slash"
            assert generator._sanitize_filename("special!@#$%chars") == "special_chars"
            assert generator._sanitize_filename("   spaces   ") == "spaces"
            
            # Test length limit
            long_prompt = "a" * 100
            sanitized = generator._sanitize_filename(long_prompt)
            assert len(sanitized) <= 50
    
    @patch('openai.OpenAI')
    def test_size_options(self, mock_openai_class, mock_image_download):
        """Test different size options."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Test valid sizes
            for size in [256, 512, 1024]:
                generator.generate_diffuse_map("test", size=size)
                call_args = mock_client.images.generate.call_args
                assert call_args[1]['size'] == f"{size}x{size}"
            
            # Test invalid size (should default to 512)
            generator.generate_diffuse_map("test", size=999)
            call_args = mock_client.images.generate.call_args
            assert call_args[1]['size'] == "512x512"


class TestGeneratorIntegration:
    """Integration tests for the generator with all components."""
    
    @patch('openai.OpenAI')
    def test_full_pipeline(self, mock_openai_class, mock_image_download, temp_dir):
        """Test the complete generation pipeline end-to-end."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate materials for different types
            for material_type in ['stone', 'metal', 'wood']:
                output_dir = os.path.join(temp_dir, material_type)
                generator.generate_material(
                    prompt=f"{material_type} texture",
                    output_dir=output_dir,
                    material_type=material_type,
                    size=256
                )
                
                # Verify all maps exist
                base_name = f"{material_type}_texture"
                assert os.path.exists(os.path.join(output_dir, f"{base_name}_diffuse.png"))
                assert os.path.exists(os.path.join(output_dir, f"{base_name}_normal.png"))
                assert os.path.exists(os.path.join(output_dir, f"{base_name}_roughness.png"))
                assert os.path.exists(os.path.join(output_dir, f"{base_name}_height.png"))
                assert os.path.exists(os.path.join(output_dir, f"{base_name}_ao.png"))
                assert os.path.exists(os.path.join(output_dir, f"{base_name}_metallic.png"))
    
    @patch('openai.OpenAI')
    def test_batch_generation(self, mock_openai_class, mock_image_download, temp_dir):
        """Test generating multiple materials in sequence."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            prompts = [
                ("ancient stone", "stone"),
                ("rusty metal", "metal"),
                ("polished wood", "wood")
            ]
            
            for prompt, material_type in prompts:
                output_dir = os.path.join(temp_dir, material_type)
                generator.generate_material(
                    prompt=prompt,
                    output_dir=output_dir,
                    material_type=material_type,
                    size=256
                )
            
            # Verify all materials were generated
            assert len(os.listdir(temp_dir)) == 3
            
            # Check API was called for each
            assert mock_client.images.generate.call_count == 3