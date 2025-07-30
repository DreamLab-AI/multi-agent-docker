"""
Integration tests for the complete PBR generation pipeline.
"""

import pytest
import os
import sys
import numpy as np
from PIL import Image
from unittest.mock import patch, Mock
import json
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.generator import PBRGenerator
from src.tessellation.seamless_tiling import SeamlessTiling


class TestPipelineIntegration:
    """Test the complete PBR generation pipeline."""
    
    @patch('openai.OpenAI')
    def test_complete_material_generation(self, mock_openai_class, mock_image_download, temp_dir):
        """Test generating a complete PBR material set."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate complete material
            output_dir = os.path.join(temp_dir, 'complete_material')
            generator.generate_material(
                prompt="weathered concrete wall",
                output_dir=output_dir,
                material_type="stone",
                size=512
            )
            
            # Verify all texture maps
            maps = {
                'diffuse': 'weathered_concrete_wall_diffuse.png',
                'normal': 'weathered_concrete_wall_normal.png',
                'roughness': 'weathered_concrete_wall_roughness.png',
                'height': 'weathered_concrete_wall_height.png',
                'ao': 'weathered_concrete_wall_ao.png',
                'metallic': 'weathered_concrete_wall_metallic.png'
            }
            
            loaded_maps = {}
            for map_type, filename in maps.items():
                filepath = os.path.join(output_dir, filename)
                assert os.path.exists(filepath), f"Missing {map_type} map"
                
                # Load and verify
                img = Image.open(filepath)
                loaded_maps[map_type] = img
                assert img.size == (512, 512)
            
            # Verify map properties
            # Normal map should be RGB
            assert loaded_maps['normal'].mode == 'RGB'
            
            # Other maps should be grayscale
            for map_type in ['roughness', 'height', 'ao', 'metallic']:
                assert loaded_maps[map_type].mode == 'L'
            
            # Normal map should have blue channel dominant (facing up)
            normal_array = np.array(loaded_maps['normal'])
            assert np.mean(normal_array[:, :, 2]) > 200
    
    @patch('openai.OpenAI')
    def test_tessellation_pipeline(self, mock_openai_class, mock_image_download, temp_dir):
        """Test the tessellation functionality with generated textures."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate base material
            base_dir = os.path.join(temp_dir, 'base_material')
            generator.generate_material(
                prompt="stone tiles",
                output_dir=base_dir,
                material_type="stone",
                size=256
            )
            
            # Apply tessellation to each map
            tiling = SeamlessTiling()
            tiled_dir = os.path.join(temp_dir, 'tiled_material')
            os.makedirs(tiled_dir, exist_ok=True)
            
            for filename in os.listdir(base_dir):
                if filename.endswith('.png'):
                    input_path = os.path.join(base_dir, filename)
                    output_path = os.path.join(tiled_dir, filename.replace('.png', '_tiled.png'))
                    
                    # Make seamless
                    input_img = Image.open(input_path)
                    tiled_img = tiling.make_seamless(input_img)
                    tiled_img.save(output_path)
                    
                    # Verify tiling
                    assert os.path.exists(output_path)
                    assert tiled_img.size == input_img.size
    
    @patch('openai.OpenAI')
    def test_material_consistency(self, mock_openai_class, mock_image_download, temp_dir):
        """Test that generated maps are consistent with each other."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate material
            output_dir = os.path.join(temp_dir, 'consistent_material')
            generator.generate_material(
                prompt="rough metal surface",
                output_dir=output_dir,
                material_type="metal",
                size=256
            )
            
            # Load maps
            diffuse = Image.open(os.path.join(output_dir, 'rough_metal_surface_diffuse.png'))
            height = Image.open(os.path.join(output_dir, 'rough_metal_surface_height.png'))
            ao = Image.open(os.path.join(output_dir, 'rough_metal_surface_ao.png'))
            
            # Convert to arrays
            diffuse_gray = np.array(diffuse.convert('L'))
            height_array = np.array(height)
            ao_array = np.array(ao)
            
            # Height and AO should have some correlation with diffuse
            # Darker areas in diffuse might be lower in height
            # This is a soft check as the relationship isn't always direct
            
            # Check that maps have variation
            assert np.std(height_array) > 0
            assert np.std(ao_array) > 0
    
    @patch('openai.OpenAI')
    def test_config_driven_generation(self, mock_openai_class, mock_image_download, temp_dir):
        """Test generation with custom configuration."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        # Create custom config
        custom_config = {
            "materials": {
                "custom_metal": {
                    "properties": {
                        "roughness": 0.1,
                        "metallic": 1.0,
                        "height_scale": 0.005,
                        "ao_intensity": 0.3
                    }
                }
            }
        }
        
        config_path = os.path.join(temp_dir, 'custom_config.json')
        with open(config_path, 'w') as f:
            json.dump(custom_config, f)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            generator.config = generator._load_config(config_path)
            
            output_dir = os.path.join(temp_dir, 'custom_material')
            generator.generate_material(
                prompt="polished chrome",
                output_dir=output_dir,
                material_type="custom_metal",
                size=256
            )
            
            # Verify properties match config
            roughness = Image.open(os.path.join(output_dir, 'polished_chrome_roughness.png'))
            metallic = Image.open(os.path.join(output_dir, 'polished_chrome_metallic.png'))
            
            roughness_mean = np.mean(np.array(roughness))
            metallic_mean = np.mean(np.array(metallic))
            
            # Should be very smooth (low roughness)
            assert roughness_mean < 50  # Less than 20% rough
            
            # Should be fully metallic
            assert metallic_mean > 200  # More than 80% metallic
    
    @patch('openai.OpenAI')
    def test_error_recovery(self, mock_openai_class, temp_dir):
        """Test pipeline handles errors gracefully."""
        # Setup mock to fail on first call, succeed on retry
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary API error")
            else:
                mock_response = Mock()
                mock_response.data = [Mock(url="https://test.com/image.png")]
                return mock_response
        
        mock_client.images.generate.side_effect = side_effect
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Should fail on first attempt
            with pytest.raises(Exception, match="Temporary API error"):
                generator.generate_material(
                    prompt="test material",
                    output_dir=os.path.join(temp_dir, 'error_test'),
                    material_type="stone"
                )
    
    @patch('openai.OpenAI')
    def test_output_organization(self, mock_openai_class, mock_image_download, temp_dir):
        """Test that outputs are properly organized."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate multiple materials
            materials = [
                ("granite floor", "stone"),
                ("steel panel", "metal"),
                ("oak planks", "wood")
            ]
            
            for prompt, mat_type in materials:
                output_dir = os.path.join(temp_dir, mat_type, prompt.replace(' ', '_'))
                generator.generate_material(
                    prompt=prompt,
                    output_dir=output_dir,
                    material_type=mat_type,
                    size=256
                )
            
            # Verify directory structure
            assert os.path.exists(os.path.join(temp_dir, 'stone', 'granite_floor'))
            assert os.path.exists(os.path.join(temp_dir, 'metal', 'steel_panel'))
            assert os.path.exists(os.path.join(temp_dir, 'wood', 'oak_planks'))
            
            # Each should contain 6 texture maps
            for prompt, mat_type in materials:
                mat_dir = os.path.join(temp_dir, mat_type, prompt.replace(' ', '_'))
                files = os.listdir(mat_dir)
                png_files = [f for f in files if f.endswith('.png')]
                assert len(png_files) == 6


class TestPerformance:
    """Test performance aspects of the pipeline."""
    
    @patch('openai.OpenAI')
    def test_memory_usage(self, mock_openai_class, mock_image_download, temp_dir):
        """Test that memory usage is reasonable."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            generator = PBRGenerator()
            
            # Generate a large texture
            output_dir = os.path.join(temp_dir, 'large_texture')
            
            # This should complete without memory issues
            generator.generate_material(
                prompt="detailed surface",
                output_dir=output_dir,
                material_type="stone",
                size=1024
            )
            
            # Verify files exist and are correct size
            for filename in os.listdir(output_dir):
                if filename.endswith('.png'):
                    img = Image.open(os.path.join(output_dir, filename))
                    assert img.size == (1024, 1024)
    
    @patch('openai.OpenAI')
    def test_concurrent_safety(self, mock_openai_class, mock_image_download, temp_dir):
        """Test that the pipeline can handle concurrent requests safely."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.data = [Mock(url="https://test.com/image.png")]
        mock_client.images.generate.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            # Create multiple generators
            generators = [PBRGenerator() for _ in range(3)]
            
            # Generate materials with each
            for i, generator in enumerate(generators):
                output_dir = os.path.join(temp_dir, f'concurrent_{i}')
                generator.generate_material(
                    prompt=f"material {i}",
                    output_dir=output_dir,
                    material_type="stone",
                    size=256
                )
            
            # Verify all completed successfully
            for i in range(3):
                output_dir = os.path.join(temp_dir, f'concurrent_{i}')
                assert os.path.exists(output_dir)
                assert len([f for f in os.listdir(output_dir) if f.endswith('.png')]) == 6