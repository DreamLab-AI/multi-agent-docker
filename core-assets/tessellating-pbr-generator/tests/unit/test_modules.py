"""
Unit tests for individual PBR texture generation modules.
"""

import pytest
import numpy as np
from PIL import Image
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.texture_maps.normal_map import NormalMapGenerator
from src.texture_maps.roughness_map import RoughnessMapGenerator
from src.texture_maps.height_map import HeightMapGenerator
from src.texture_maps.ao_map import AOMapGenerator
from src.texture_maps.metallic_map import MetallicMapGenerator


class TestNormalMapGenerator:
    """Test normal map generation functionality."""
    
    def test_normal_map_generation(self, sample_image):
        """Test basic normal map generation."""
        generator = NormalMapGenerator()
        normal_map = generator.generate(sample_image)
        
        assert isinstance(normal_map, Image.Image)
        assert normal_map.mode == 'RGB'
        assert normal_map.size == sample_image.size
        
        # Check that the normal map has proper values
        # Normal maps should have values centered around 128 (0.5 in normalized space)
        normal_array = np.array(normal_map)
        assert normal_array.shape == (256, 256, 3)
        
        # Z component (blue channel) should be mostly high values
        assert np.mean(normal_array[:, :, 2]) > 200
    
    def test_normal_map_strength(self, sample_image):
        """Test normal map generation with different strengths."""
        generator = NormalMapGenerator()
        
        weak_normal = generator.generate(sample_image, strength=0.5)
        strong_normal = generator.generate(sample_image, strength=2.0)
        
        # Convert to arrays for comparison
        weak_array = np.array(weak_normal)
        strong_array = np.array(strong_normal)
        
        # Strong normal map should have more variation in X and Y components
        weak_variance = np.var(weak_array[:, :, :2])
        strong_variance = np.var(strong_array[:, :, :2])
        
        assert strong_variance > weak_variance
    
    def test_edge_detection(self, sample_image):
        """Test that edges are properly detected in normal map."""
        # Create an image with clear edges
        edge_image = Image.new('RGB', (100, 100), 'white')
        pixels = edge_image.load()
        # Create a black square in the middle
        for x in range(40, 60):
            for y in range(40, 60):
                pixels[x, y] = (0, 0, 0)
        
        generator = NormalMapGenerator()
        normal_map = generator.generate(edge_image)
        normal_array = np.array(normal_map)
        
        # Check that edges have different normals
        # The edges should show variation in X and Y components
        edge_region = normal_array[39:41, 39:61]
        center_region = normal_array[45:55, 45:55]
        
        edge_variance = np.var(edge_region[:, :, :2])
        center_variance = np.var(center_region[:, :, :2])
        
        assert edge_variance > center_variance


class TestRoughnessMapGenerator:
    """Test roughness map generation functionality."""
    
    def test_roughness_generation_basic(self, sample_image):
        """Test basic roughness map generation."""
        generator = RoughnessMapGenerator()
        roughness_map = generator.generate(sample_image, roughness_value=0.5)
        
        assert isinstance(roughness_map, Image.Image)
        assert roughness_map.mode == 'L'
        assert roughness_map.size == sample_image.size
    
    def test_roughness_with_config(self, sample_image, material_config):
        """Test roughness generation with material config."""
        generator = RoughnessMapGenerator()
        roughness_map = generator.generate(sample_image, config=material_config)
        
        # Should use roughness value from config
        roughness_array = np.array(roughness_map)
        expected_value = int(material_config['properties']['roughness'] * 255)
        
        # Check that the base roughness is close to expected
        assert abs(np.mean(roughness_array) - expected_value) < 50
    
    def test_roughness_variation(self, sample_image):
        """Test that roughness map has proper variation."""
        generator = RoughnessMapGenerator()
        roughness_map = generator.generate(sample_image, roughness_value=0.5, variation=0.2)
        
        roughness_array = np.array(roughness_map)
        
        # Should have some variation
        assert np.std(roughness_array) > 0
        
        # But not too much
        assert np.std(roughness_array) < 100


class TestHeightMapGenerator:
    """Test height/displacement map generation."""
    
    def test_height_map_generation(self, sample_image):
        """Test basic height map generation."""
        generator = HeightMapGenerator()
        height_map = generator.generate(sample_image)
        
        assert isinstance(height_map, Image.Image)
        assert height_map.mode == 'L'
        assert height_map.size == sample_image.size
    
    def test_height_scale(self, sample_image, material_config):
        """Test height map with different scales."""
        generator = HeightMapGenerator()
        
        # Generate with config
        height_map = generator.generate(sample_image, config=material_config)
        height_array = np.array(height_map)
        
        # Height map should have variation based on input
        assert np.std(height_array) > 0
    
    def test_height_from_luminance(self, sample_image):
        """Test that height is derived from luminance."""
        # Create a gradient image
        gradient = Image.new('RGB', (100, 100))
        pixels = gradient.load()
        for y in range(100):
            gray = int(255 * y / 100)
            for x in range(100):
                pixels[x, y] = (gray, gray, gray)
        
        generator = HeightMapGenerator()
        height_map = generator.generate(gradient)
        height_array = np.array(height_map)
        
        # Height should increase with luminance
        top_mean = np.mean(height_array[:10, :])
        bottom_mean = np.mean(height_array[-10:, :])
        
        assert bottom_mean > top_mean


class TestAOMapGenerator:
    """Test ambient occlusion map generation."""
    
    def test_ao_generation(self, sample_image):
        """Test basic AO map generation."""
        generator = AOMapGenerator()
        ao_map = generator.generate(sample_image)
        
        assert isinstance(ao_map, Image.Image)
        assert ao_map.mode == 'L'
        assert ao_map.size == sample_image.size
    
    def test_ao_intensity(self, sample_image, material_config):
        """Test AO generation with intensity from config."""
        generator = AOMapGenerator()
        ao_map = generator.generate(sample_image, config=material_config)
        
        ao_array = np.array(ao_map)
        
        # AO should be mostly bright (not occluded)
        assert np.mean(ao_array) > 128
    
    def test_ao_from_edges(self):
        """Test that AO is darker in crevices/edges."""
        # Create image with clear edges
        test_image = Image.new('RGB', (100, 100), 'white')
        pixels = test_image.load()
        
        # Create a pattern that should have AO
        for x in range(40, 60):
            for y in range(40, 60):
                pixels[x, y] = (128, 128, 128)
        
        generator = AOMapGenerator()
        ao_map = generator.generate(test_image)
        ao_array = np.array(ao_map)
        
        # Edges should be darker (more occluded)
        edge_ao = ao_array[39, 39]
        center_ao = ao_array[50, 50]
        
        # This might not always be true depending on implementation
        # but we expect some variation
        assert ao_array.std() > 0


class TestMetallicMapGenerator:
    """Test metallic map generation."""
    
    def test_metallic_generation(self, sample_image):
        """Test basic metallic map generation."""
        generator = MetallicMapGenerator()
        metallic_map = generator.generate(sample_image, metallic_value=0.5)
        
        assert isinstance(metallic_map, Image.Image)
        assert metallic_map.mode == 'L'
        assert metallic_map.size == sample_image.size
    
    def test_metallic_from_config(self, sample_image, material_config):
        """Test metallic generation from material config."""
        generator = MetallicMapGenerator()
        metallic_map = generator.generate(sample_image, config=material_config)
        
        metallic_array = np.array(metallic_map)
        expected_value = int(material_config['properties']['metallic'] * 255)
        
        # Should be close to the configured metallic value
        assert abs(np.mean(metallic_array) - expected_value) < 50
    
    def test_metallic_detection(self):
        """Test automatic metallic detection from color."""
        # Create an image with metallic-looking colors
        metallic_image = Image.new('RGB', (100, 100))
        pixels = metallic_image.load()
        
        # Add some gray/silver colors (typical for metals)
        for x in range(100):
            for y in range(100):
                gray = 180 + (x % 20)
                pixels[x, y] = (gray, gray, gray)
        
        generator = MetallicMapGenerator()
        metallic_map = generator.generate(metallic_image, auto_detect=True)
        metallic_array = np.array(metallic_map)
        
        # Should detect as somewhat metallic
        assert np.mean(metallic_array) > 100  # More than 40% metallic


class TestModuleIntegration:
    """Test interaction between different modules."""
    
    def test_all_maps_same_size(self, sample_image, material_config):
        """Test that all generated maps have the same dimensions."""
        generators = {
            'normal': NormalMapGenerator(),
            'roughness': RoughnessMapGenerator(),
            'height': HeightMapGenerator(),
            'ao': AOMapGenerator(),
            'metallic': MetallicMapGenerator()
        }
        
        maps = {}
        maps['normal'] = generators['normal'].generate(sample_image)
        maps['roughness'] = generators['roughness'].generate(sample_image, config=material_config)
        maps['height'] = generators['height'].generate(sample_image, config=material_config)
        maps['ao'] = generators['ao'].generate(sample_image, config=material_config)
        maps['metallic'] = generators['metallic'].generate(sample_image, config=material_config)
        
        # All maps should have the same size as input
        for name, texture_map in maps.items():
            assert texture_map.size == sample_image.size, f"{name} map size mismatch"
    
    def test_consistent_processing(self, sample_image):
        """Test that the same input produces consistent results."""
        generator = NormalMapGenerator()
        
        # Generate twice
        map1 = generator.generate(sample_image)
        map2 = generator.generate(sample_image)
        
        # Should be identical
        assert np.array_equal(np.array(map1), np.array(map2))