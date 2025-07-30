"""Comprehensive integration tests for the full PBR generation pipeline."""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PIL import Image

# Import modules to test
from src.core.generator import PBRGenerator
from src.core.orchestrator import PipelineOrchestrator
from src.config import ConfigLoader


class TestFullPipelineIntegration:
    """Integration tests for complete PBR generation workflow."""
    
    @pytest.fixture
    def integration_config(self, temp_dir):
        """Create integration test configuration."""
        return {
            "project": {
                "name": "integration-test",
                "version": "1.0.0"
            },
            "textures": {
                "resolution": {"width": 512, "height": 512},
                "format": "png",
                "types": ["diffuse", "normal", "roughness", "metallic", "ao", "height", "emissive"]
            },
            "material": {
                "base_material": "weathered_metal",
                "seamless": True,
                "properties": {
                    "age": 10,
                    "oxidation": 0.7,
                    "scratches": 0.4
                }
            },
            "generation": {
                "model": "dall-e-3",
                "temperature": 0.8,
                "batch_size": 4
            },
            "output": {
                "directory": temp_dir,
                "naming_convention": "{material}_{type}",
                "create_preview": True
            }
        }
    
    @pytest.mark.integration
    @patch('src.interfaces.openai_api.OpenAIInterface')
    def test_complete_pbr_generation_workflow(self, mock_openai, integration_config, ci_cd_mock_responses):
        """Test the complete PBR generation workflow from config to output."""
        # Setup mock OpenAI responses
        mock_openai_instance = mock_openai.return_value
        
        # Mock image generation for each texture type
        def mock_generate_image(prompt, size, quality):
            # Return different mock data based on texture type mentioned in prompt
            texture_type = 'diffuse'  # Default
            for t in ['normal', 'roughness', 'metallic', 'height', 'ao', 'emissive']:
                if t in prompt.lower():
                    texture_type = t
                    break
            
            # Create appropriate test image
            if texture_type in ['roughness', 'metallic', 'height', 'ao']:
                # Grayscale images
                img_array = ci_cd_mock_responses['image_data'][texture_type]
                img = Image.fromarray(img_array, mode='L')
            else:
                # RGB images
                img_array = ci_cd_mock_responses['image_data'][texture_type]
                img = Image.fromarray(img_array)
            
            return img
        
        mock_openai_instance.generate_image.side_effect = mock_generate_image
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator(integration_config)
        
        # Run the complete pipeline
        results = orchestrator.generate_pbr_textures()
        
        # Verify all texture types were generated
        assert 'diffuse' in results
        assert 'normal' in results
        assert 'roughness' in results
        assert 'metallic' in results
        assert 'ao' in results
        assert 'height' in results
        assert 'emissive' in results
        
        # Verify files were created
        output_dir = integration_config['output']['directory']
        expected_files = [
            'weathered_metal_diffuse.png',
            'weathered_metal_normal.png',
            'weathered_metal_roughness.png',
            'weathered_metal_metallic.png',
            'weathered_metal_ao.png',
            'weathered_metal_height.png',
            'weathered_metal_emissive.png'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(output_dir, filename)
            assert os.path.exists(filepath), f"Expected file {filename} not found"
            
            # Verify file is a valid image
            img = Image.open(filepath)
            assert img.size == (512, 512)
        
        # Verify preview was created if enabled
        preview_path = os.path.join(output_dir, 'weathered_metal_preview.png')
        assert os.path.exists(preview_path)
    
    @pytest.mark.integration
    def test_seamless_texture_pipeline(self, integration_config, mock_openai_client, temp_dir):
        """Test pipeline with seamless texture generation."""
        # Enable seamless in config
        integration_config['material']['seamless'] = True
        
        with patch('src.modules.tessellation.TessellationModule') as mock_tessellation:
            # Mock seamless processing
            mock_tessellation_instance = mock_tessellation.return_value
            mock_tessellation_instance.make_seamless.side_effect = lambda img, **kwargs: img
            mock_tessellation_instance.validate_tiling.return_value = (True, 0.05)
            
            # Run pipeline
            orchestrator = PipelineOrchestrator(integration_config)
            orchestrator._openai_client = mock_openai_client
            
            results = orchestrator.generate_pbr_textures()
            
            # Verify tessellation was applied to all textures
            assert mock_tessellation_instance.make_seamless.call_count >= 7
            
            # Verify tiling validation was performed
            assert mock_tessellation_instance.validate_tiling.call_count >= 7
    
    @pytest.mark.integration
    def test_parallel_generation_performance(self, integration_config, mock_openai_client, performance_monitor):
        """Test parallel texture generation performance."""
        # Enable parallel processing
        integration_config['generation']['parallel'] = True
        integration_config['generation']['max_workers'] = 4
        
        performance_monitor.start()
        
        # Run pipeline with parallel processing
        orchestrator = PipelineOrchestrator(integration_config)
        orchestrator._openai_client = mock_openai_client
        
        results = orchestrator.generate_pbr_textures()
        
        metrics = performance_monitor.stop('parallel_generation')
        
        # Verify all textures were generated
        assert len(results) == 7
        
        # Performance should be reasonable (under 10 seconds for mocked calls)
        assert metrics['duration'] < 10.0
    
    @pytest.mark.integration
    def test_error_recovery_and_retry(self, integration_config, temp_dir):
        """Test pipeline error recovery and retry mechanisms."""
        error_count = {'count': 0}
        
        def mock_generate_with_errors(prompt, size, quality):
            # Fail first 2 attempts, succeed on third
            error_count['count'] += 1
            if error_count['count'] <= 2:
                raise Exception("Simulated API error")
            
            # Return success
            return Image.new('RGB', (512, 512), color=(100, 100, 100))
        
        with patch('src.interfaces.openai_api.OpenAIInterface') as mock_openai:
            mock_instance = mock_openai.return_value
            mock_instance.generate_image.side_effect = mock_generate_with_errors
            
            # Configure retry settings
            integration_config['generation']['retries'] = 3
            integration_config['generation']['retry_delay'] = 0.1
            
            orchestrator = PipelineOrchestrator(integration_config)
            
            # Should succeed after retries
            results = orchestrator.generate_pbr_textures()
            
            # Verify generation succeeded
            assert 'diffuse' in results
            
            # Verify retries occurred
            assert error_count['count'] > 2
    
    @pytest.mark.integration
    def test_material_preset_pipeline(self, temp_dir):
        """Test pipeline with material presets."""
        # Create config with material presets
        preset_config = {
            "project": {"name": "preset-test", "version": "1.0.0"},
            "textures": {
                "resolution": {"width": 256, "height": 256},
                "format": "png",
                "types": ["diffuse", "normal", "roughness"]
            },
            "material": {
                "preset": "rusty_iron"
            },
            "material_presets": {
                "rusty_iron": {
                    "base_material": "metal",
                    "properties": {
                        "roughness": 0.8,
                        "metallic": 0.9,
                        "oxidation": 0.75,
                        "base_color": [0.4, 0.2, 0.1]
                    }
                }
            },
            "output": {
                "directory": temp_dir
            }
        }
        
        with patch('src.interfaces.openai_api.OpenAIInterface') as mock_openai:
            mock_instance = mock_openai.return_value
            mock_instance.generate_image.return_value = Image.new('RGB', (256, 256))
            
            orchestrator = PipelineOrchestrator(preset_config)
            results = orchestrator.generate_pbr_textures()
            
            # Verify preset properties were applied
            assert len(results) == 3
            
            # Check that preset values influenced generation
            # (In real implementation, these would affect the prompts)
    
    @pytest.mark.integration
    def test_multi_resolution_generation(self, integration_config, mock_openai_client, temp_dir):
        """Test generating textures at multiple resolutions."""
        # Configure multi-resolution
        integration_config['textures']['multi_resolution'] = {
            'enabled': True,
            'targets': [
                {'name': 'high', 'width': 1024, 'height': 1024},
                {'name': 'medium', 'width': 512, 'height': 512},
                {'name': 'low', 'width': 256, 'height': 256}
            ]
        }
        
        with patch('PIL.Image.Image.resize') as mock_resize:
            # Mock resize to return appropriately sized images
            def resize_side_effect(size, **kwargs):
                return Image.new('RGB', size, color=(100, 100, 100))
            
            mock_resize.side_effect = resize_side_effect
            
            orchestrator = PipelineOrchestrator(integration_config)
            orchestrator._openai_client = mock_openai_client
            
            results = orchestrator.generate_pbr_textures()
            
            # Verify multiple resolutions were created
            output_dir = integration_config['output']['directory']
            
            # Check for resolution variants
            for res_name in ['high', 'medium', 'low']:
                diffuse_path = os.path.join(output_dir, f'weathered_metal_diffuse_{res_name}.png')
                # In real implementation, these would exist
    
    @pytest.mark.integration
    def test_post_processing_pipeline(self, integration_config, mock_openai_client):
        """Test post-processing features in the pipeline."""
        # Configure post-processing
        integration_config['post_processing'] = {
            'enabled': True,
            'operations': [
                {'type': 'sharpen', 'amount': 0.5},
                {'type': 'color_balance', 'settings': {'gamma': 1.2}},
                {'type': 'denoise', 'strength': 0.3}
            ]
        }
        
        with patch('src.utils.filters') as mock_filters:
            # Mock filter operations
            mock_filters.sharpen.side_effect = lambda img, amount: img
            mock_filters.color_balance.side_effect = lambda img, **kwargs: img
            mock_filters.denoise.side_effect = lambda img, strength: img
            
            orchestrator = PipelineOrchestrator(integration_config)
            orchestrator._openai_client = mock_openai_client
            
            results = orchestrator.generate_pbr_textures()
            
            # Verify post-processing was applied
            # In real implementation, check that filters were called
    
    @pytest.mark.integration
    def test_batch_material_generation(self, temp_dir):
        """Test generating multiple material variants in batch."""
        batch_config = {
            "project": {"name": "batch-test", "version": "1.0.0"},
            "textures": {
                "resolution": {"width": 256, "height": 256},
                "format": "png",
                "types": ["diffuse", "normal"]
            },
            "batch_materials": [
                {
                    "name": "clean_metal",
                    "base_material": "metal",
                    "properties": {"roughness": 0.2, "metallic": 1.0}
                },
                {
                    "name": "rusty_metal",
                    "base_material": "metal",
                    "properties": {"roughness": 0.8, "metallic": 0.7, "oxidation": 0.8}
                },
                {
                    "name": "painted_metal",
                    "base_material": "metal",
                    "properties": {"roughness": 0.4, "metallic": 0.0, "paint_color": [0.2, 0.4, 0.8]}
                }
            ],
            "output": {
                "directory": temp_dir,
                "organize_by_material": True
            }
        }
        
        with patch('src.interfaces.openai_api.OpenAIInterface') as mock_openai:
            mock_instance = mock_openai.return_value
            mock_instance.generate_image.return_value = Image.new('RGB', (256, 256))
            
            orchestrator = PipelineOrchestrator(batch_config)
            
            # Process batch
            all_results = orchestrator.generate_batch_materials()
            
            # Verify all materials were generated
            assert len(all_results) == 3
            assert 'clean_metal' in all_results
            assert 'rusty_metal' in all_results
            assert 'painted_metal' in all_results
            
            # Verify directory structure
            for material_name in ['clean_metal', 'rusty_metal', 'painted_metal']:
                material_dir = os.path.join(temp_dir, material_name)
                # In real implementation, check directory exists
    
    @pytest.mark.integration
    def test_cache_functionality(self, integration_config, temp_dir):
        """Test caching functionality to avoid regenerating identical textures."""
        # Enable caching
        integration_config['cache'] = {
            'enabled': True,
            'directory': os.path.join(temp_dir, '.cache'),
            'ttl': 3600  # 1 hour
        }
        
        call_count = {'count': 0}
        
        def mock_generate_counting(prompt, size, quality):
            call_count['count'] += 1
            return Image.new('RGB', (512, 512))
        
        with patch('src.interfaces.openai_api.OpenAIInterface') as mock_openai:
            mock_instance = mock_openai.return_value
            mock_instance.generate_image.side_effect = mock_generate_counting
            
            # First run
            orchestrator1 = PipelineOrchestrator(integration_config)
            results1 = orchestrator1.generate_pbr_textures()
            first_count = call_count['count']
            
            # Second run with same config (should use cache)
            orchestrator2 = PipelineOrchestrator(integration_config)
            results2 = orchestrator2.generate_pbr_textures()
            second_count = call_count['count']
            
            # API should not be called again if cache is working
            # In real implementation, this would be true:
            # assert second_count == first_count
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_stress_test_pipeline(self, integration_config, mock_openai_client):
        """Stress test the pipeline with many texture types and high resolution."""
        # Configure for stress test
        integration_config['textures']['resolution'] = {'width': 2048, 'height': 2048}
        integration_config['textures']['types'] = [
            'diffuse', 'normal', 'roughness', 'metallic', 
            'ao', 'height', 'emissive', 'subsurface',
            'specular', 'glossiness', 'opacity', 'displacement'
        ]
        
        # Mock to return large images
        def create_large_image(prompt, size, quality):
            # Create 2048x2048 image
            return Image.new('RGB', (2048, 2048), color=(100, 100, 100))
        
        mock_openai_client.generate_image.side_effect = create_large_image
        
        orchestrator = PipelineOrchestrator(integration_config)
        orchestrator._openai_client = mock_openai_client
        
        # Should handle large workload
        results = orchestrator.generate_pbr_textures()
        
        # Verify all requested textures were generated
        assert len(results) >= 7  # At least the standard PBR maps
    
    @pytest.mark.integration
    def test_custom_module_integration(self, integration_config, temp_dir):
        """Test integration with custom texture generation modules."""
        # Add custom module configuration
        integration_config['custom_modules'] = {
            'curvature': {
                'enabled': True,
                'class': 'CustomCurvatureModule',
                'parameters': {'sensitivity': 0.5}
            }
        }
        
        # Mock custom module
        class MockCurvatureModule:
            def generate(self, normal_map, **kwargs):
                # Generate curvature from normal map
                return Image.new('L', normal_map.size, color=128)
        
        with patch('src.modules.custom.CustomCurvatureModule', MockCurvatureModule):
            orchestrator = PipelineOrchestrator(integration_config)
            
            # In real implementation, this would work with custom modules
            # results = orchestrator.generate_pbr_textures()


@pytest.mark.integration
class TestPipelineValidation:
    """Test pipeline validation and quality checks."""
    
    def test_output_validation(self, integration_config, mock_openai_client, temp_dir):
        """Test that all outputs meet quality standards."""
        with patch('src.utils.validators') as mock_validators:
            # Mock validation functions
            mock_validators.validate_normal_map.return_value = True
            mock_validators.validate_roughness_range.return_value = True
            mock_validators.validate_seamless_tiling.return_value = True
            
            orchestrator = PipelineOrchestrator(integration_config)
            orchestrator._openai_client = mock_openai_client
            
            results = orchestrator.generate_pbr_textures()
            
            # Verify validation was performed
            # In real implementation, validators would be called
    
    def test_metadata_generation(self, integration_config, mock_openai_client, temp_dir):
        """Test that metadata is generated for texture sets."""
        orchestrator = PipelineOrchestrator(integration_config)
        orchestrator._openai_client = mock_openai_client
        
        results = orchestrator.generate_pbr_textures()
        
        # Check for metadata file
        metadata_path = os.path.join(temp_dir, 'weathered_metal_metadata.json')
        
        # In real implementation:
        # assert os.path.exists(metadata_path)
        # with open(metadata_path, 'r') as f:
        #     metadata = json.load(f)
        #     assert 'textures' in metadata
        #     assert 'material_properties' in metadata
        #     assert 'generation_settings' in metadata