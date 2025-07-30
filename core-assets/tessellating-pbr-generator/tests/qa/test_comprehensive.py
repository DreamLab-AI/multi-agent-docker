#!/usr/bin/env python3
"""Comprehensive QA test script for the Tessellating PBR Texture Generator."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import load_config
from src.types.config import Config, TextureType
from src.core.generator import generate_textures
from src.utils.logging import setup_logger, get_logger


class ComprehensiveQATester:
    """Comprehensive QA testing for the PBR texture generator."""
    
    def __init__(self):
        self.test_results = []
        self.test_dir = Path("tests/qa/test_output")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        setup_logger(debug=True)
        self.logger = get_logger(__name__)
        
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.logger.info(f"{status}: {test_name}")
        if details:
            self.logger.info(f"  Details: {details}")
    
    def check_file_exists(self, filepath: Path) -> bool:
        """Check if a file exists."""
        return filepath.exists() and filepath.is_file()
    
    def check_image_properties(self, filepath: Path, expected_size: Tuple[int, int]) -> bool:
        """Check image properties."""
        try:
            with Image.open(filepath) as img:
                return img.size == expected_size
        except Exception as e:
            self.logger.error(f"Error checking image {filepath}: {e}")
            return False
    
    def check_seamless_tiling(self, filepath: Path, tolerance: float = 5.0) -> bool:
        """Check if an image tiles seamlessly."""
        try:
            with Image.open(filepath) as img:
                # Convert to numpy array
                arr = np.array(img)
                height, width = arr.shape[:2]
                
                # Check horizontal edges
                left_edge = arr[:, 0]
                right_edge = arr[:, -1]
                h_diff = np.mean(np.abs(left_edge.astype(float) - right_edge.astype(float)))
                
                # Check vertical edges
                top_edge = arr[0, :]
                bottom_edge = arr[-1, :]
                v_diff = np.mean(np.abs(top_edge.astype(float) - bottom_edge.astype(float)))
                
                # Both differences should be small for seamless tiling
                is_seamless = h_diff < tolerance and v_diff < tolerance
                
                if not is_seamless:
                    self.logger.debug(f"Seamless check failed - H diff: {h_diff:.2f}, V diff: {v_diff:.2f}")
                
                return is_seamless
                
        except Exception as e:
            self.logger.error(f"Error checking seamless tiling for {filepath}: {e}")
            return False
    
    async def test_cli_basic(self):
        """Test basic CLI functionality."""
        test_name = "CLI Basic Functionality"
        
        try:
            # Test help command
            result = subprocess.run(
                [sys.executable, "main.py", "--help"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "Generate seamless PBR textures" in result.stdout:
                self.log_test_result(test_name + " - Help", True)
            else:
                self.log_test_result(test_name + " - Help", False, f"Return code: {result.returncode}")
                
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_cli_material_generation(self, material: str, config_path: str = None):
        """Test CLI material generation."""
        test_name = f"CLI Material Generation - {material}"
        output_dir = self.test_dir / f"cli_{material}"
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Build command
            cmd = [
                sys.executable, "main.py",
                "-m", material,
                "-r", "512x512",
                "-o", str(output_dir),
                "-t", "diffuse", "normal", "roughness", "height", "ao"
            ]
            
            if config_path:
                cmd.extend(["-c", config_path])
            
            # Run command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_test_result(test_name, False, f"CLI failed: {result.stderr}")
                return
            
            # Check generated files
            expected_files = [
                f"{material}_diffuse_512x512_seamless.png",
                f"{material}_normal_512x512_seamless.png",
                f"{material}_roughness_512x512_seamless.png",
                f"{material}_height_512x512_seamless.png",
                f"{material}_ao_512x512_seamless.png"
            ]
            
            all_exist = True
            for filename in expected_files:
                filepath = output_dir / filename
                if not self.check_file_exists(filepath):
                    all_exist = False
                    self.log_test_result(f"{test_name} - File exists: {filename}", False)
                else:
                    # Check image properties
                    if self.check_image_properties(filepath, (512, 512)):
                        self.log_test_result(f"{test_name} - {filename} properties", True)
                    else:
                        self.log_test_result(f"{test_name} - {filename} properties", False)
                    
                    # Check seamless tiling
                    if self.check_seamless_tiling(filepath):
                        self.log_test_result(f"{test_name} - {filename} seamless", True)
                    else:
                        self.log_test_result(f"{test_name} - {filename} seamless", False)
            
            self.log_test_result(test_name, all_exist)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_api_generation(self, config_dict: Dict):
        """Test API-based texture generation."""
        test_name = f"API Generation - {config_dict['material']['base_material']}"
        
        try:
            # Create config
            config = Config.from_dict(config_dict)
            
            # Generate textures
            results = await generate_textures(config)
            
            if not results:
                self.log_test_result(test_name, False, "No textures generated")
                return
            
            # Check each result
            for result in results:
                filepath = Path(result.file_path)
                
                # Check file exists
                if not self.check_file_exists(filepath):
                    self.log_test_result(f"{test_name} - {result.texture_type.value} exists", False)
                    continue
                
                # Check resolution
                expected_size = (
                    config.texture_config.resolution.width,
                    config.texture_config.resolution.height
                )
                if self.check_image_properties(filepath, expected_size):
                    self.log_test_result(f"{test_name} - {result.texture_type.value} resolution", True)
                else:
                    self.log_test_result(f"{test_name} - {result.texture_type.value} resolution", False)
                
                # Check seamless if enabled
                if config.texture_config.seamless:
                    if self.check_seamless_tiling(filepath):
                        self.log_test_result(f"{test_name} - {result.texture_type.value} seamless", True)
                    else:
                        self.log_test_result(f"{test_name} - {result.texture_type.value} seamless", False)
            
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_config_loading(self):
        """Test configuration loading and validation."""
        test_name = "Configuration Loading"
        
        try:
            # Test default config
            default_config = load_config()
            if default_config:
                self.log_test_result(f"{test_name} - Default", True)
            else:
                self.log_test_result(f"{test_name} - Default", False)
            
            # Test custom configs
            config_dir = Path("examples/materials")
            if config_dir.exists():
                for config_file in config_dir.glob("*.json"):
                    try:
                        config = load_config(str(config_file))
                        self.log_test_result(f"{test_name} - {config_file.name}", True)
                    except Exception as e:
                        self.log_test_result(f"{test_name} - {config_file.name}", False, str(e))
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_texture_types(self):
        """Test all texture type generation."""
        test_name = "Texture Type Generation"
        
        texture_types = [
            TextureType.DIFFUSE,
            TextureType.NORMAL,
            TextureType.ROUGHNESS,
            TextureType.METALLIC,
            TextureType.HEIGHT,
            TextureType.AMBIENT_OCCLUSION,
            TextureType.EMISSIVE
        ]
        
        for texture_type in texture_types:
            config_dict = {
                "material": {
                    "base_material": "test_material",
                    "style": "realistic"
                },
                "textures": {
                    "resolution": {"width": 256, "height": 256},
                    "types": [texture_type.value],
                    "seamless": True,
                    "format": "png"
                },
                "output": {
                    "directory": str(self.test_dir / "texture_types"),
                    "prefix": "test",
                    "create_preview": False
                },
                "api": {
                    "provider": "offline",
                    "model": "test-model"
                }
            }
            
            try:
                config = Config.from_dict(config_dict)
                results = await generate_textures(config)
                
                if results and len(results) == 1:
                    self.log_test_result(f"{test_name} - {texture_type.value}", True)
                else:
                    self.log_test_result(f"{test_name} - {texture_type.value}", False, "No result")
                    
            except Exception as e:
                self.log_test_result(f"{test_name} - {texture_type.value}", False, str(e))
    
    async def test_edge_cases(self):
        """Test edge cases and error handling."""
        test_name = "Edge Cases"
        
        # Test invalid resolution
        try:
            config_dict = {
                "material": {"base_material": "test", "style": "test"},
                "textures": {
                    "resolution": {"width": -1, "height": -1},
                    "types": ["diffuse"]
                },
                "output": {"directory": str(self.test_dir)},
                "api": {"provider": "offline"}
            }
            config = Config.from_dict(config_dict)
            self.log_test_result(f"{test_name} - Invalid resolution", False, "Should have failed")
        except ValueError:
            self.log_test_result(f"{test_name} - Invalid resolution", True)
        
        # Test empty material
        try:
            config_dict = {
                "material": {"base_material": "", "style": "test"},
                "textures": {
                    "resolution": {"width": 256, "height": 256},
                    "types": ["diffuse"]
                },
                "output": {"directory": str(self.test_dir)},
                "api": {"provider": "offline"}
            }
            config = Config.from_dict(config_dict)
            self.log_test_result(f"{test_name} - Empty material", False, "Should have failed")
        except ValueError:
            self.log_test_result(f"{test_name} - Empty material", True)
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        report = {
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            },
            "tests": self.test_results
        }
        
        # Save report
        report_path = self.test_dir / "qa_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.logger.info("\n" + "="*60)
        self.logger.info("QA TEST SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests} ✅")
        self.logger.info(f"Failed: {failed_tests} ❌")
        self.logger.info(f"Success Rate: {report['summary']['success_rate']}")
        self.logger.info(f"Report saved to: {report_path}")
        
        # List failed tests
        if failed_tests > 0:
            self.logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    self.logger.info(f"  - {result['test']}: {result['details']}")
        
        return report


async def main():
    """Run comprehensive QA tests."""
    tester = ComprehensiveQATester()
    
    print("🔍 Starting Comprehensive QA Testing...")
    print("="*60)
    
    # Run all tests
    await tester.test_cli_basic()
    await tester.test_config_loading()
    await tester.test_texture_types()
    await tester.test_edge_cases()
    
    # Test different materials via CLI
    materials = ["stone", "metal", "wood", "fabric"]
    for material in materials:
        await tester.test_cli_material_generation(material)
    
    # Test API generation with different configs
    test_configs = [
        {
            "material": {"base_material": "brick", "style": "weathered"},
            "textures": {
                "resolution": {"width": 512, "height": 512},
                "types": ["diffuse", "normal", "roughness"],
                "seamless": True
            },
            "output": {"directory": str(tester.test_dir / "api_brick")},
            "api": {"provider": "offline"}
        },
        {
            "material": {"base_material": "concrete", "style": "rough"},
            "textures": {
                "resolution": {"width": 1024, "height": 1024},
                "types": ["diffuse", "height", "ao"],
                "seamless": True
            },
            "output": {"directory": str(tester.test_dir / "api_concrete")},
            "api": {"provider": "offline"}
        }
    ]
    
    for config in test_configs:
        await tester.test_api_generation(config)
    
    # Generate final report
    report = tester.generate_report()
    
    # Return exit code based on results
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)