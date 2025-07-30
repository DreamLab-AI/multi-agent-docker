"""Main texture generation function - generates diffuse and derives other maps."""

import asyncio
import time
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from ..types.config import Config
from ..types.results import GenerationResult
from ..types.common import TextureType
from ..interfaces.openai_api import OpenAIInterface
from ..utils.file_handlers import save_texture
from ..utils.logging import get_logger
from ..utils.image_utils import resize_image
from ..utils.progress import api_progress

if TYPE_CHECKING:
    from ..utils.progress import ProgressTracker
# Tessellation utilities
from ..utils.tessellation import apply_tessellation
from PIL import Image
import numpy as np

# Import preview generation
from ..utils.preview import generate_material_preview

# Import all texture generation modules
from ..modules import (
    DiffuseModule,
    NormalModule,
    RoughnessModule,
    MetallicModule,
    AmbientOcclusionModule,
    HeightModule,
    EmissiveModule
)


logger = get_logger(__name__)


async def generate_textures_with_progress(config: Config, progress_tracker: Optional['ProgressTracker'] = None) -> List[GenerationResult]:
    """Generate PBR textures with progress tracking.
    
    This is the main entry point that includes progress tracking.
    
    Args:
        config: Configuration object with all settings.
        progress_tracker: Optional progress tracker for UI feedback.
        
    Returns:
        List of generation results for all texture types.
    """
    if progress_tracker:
        return await _generate_textures_with_progress(config, progress_tracker)
    else:
        return await generate_textures(config)


async def generate_textures(config: Config) -> List[GenerationResult]:
    """Generate PBR textures based on configuration.
    
    This function orchestrates the entire texture generation process:
    1. Generates the diffuse/albedo map from OpenAI
    2. Passes it through tessellation (placeholder)
    3. Derives other PBR maps from the tessellated diffuse
    
    Args:
        config: Configuration object with all settings.
        
    Returns:
        List of generation results for all texture types.
    """
    logger.info(f"Starting texture generation for material: {config.material}")
    results = []
    
    try:
        # Step 1: Generate diffuse map from OpenAI
        logger.info("Step 1: Generating diffuse map from OpenAI")
        diffuse_result = await _generate_diffuse_map(config)
        results.append(diffuse_result)
        
        if not diffuse_result.success:
            logger.error(f"Failed to generate diffuse map: {diffuse_result.error_message}")
            return results
            
        # Step 2: Apply tessellation to the diffuse map (placeholder)
        logger.info("Step 2: Applying tessellation to diffuse map")
        tessellated_diffuse_path = await _apply_tessellation(diffuse_result.file_path, config)
        
        # Step 3: Derive other PBR maps from tessellated diffuse
        logger.info("Step 3: Deriving PBR maps from tessellated diffuse")
        derived_results = await _derive_pbr_maps(tessellated_diffuse_path, config)
        results.extend(derived_results)
        
        # Step 4: Generate preview if requested
        if config.create_preview:
            logger.info("Step 4: Generating material preview")
            await _generate_preview(results, config)
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Texture generation complete. {successful}/{len(results)} textures generated successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error during texture generation: {e}")
        # Add error result for any pending textures
        for texture_type in config.texture_config.types:
            if not any(r.texture_type == texture_type for r in results):
                results.append(GenerationResult(
                    texture_type=texture_type,
                    file_path="",
                    generation_time=0.0,
                    success=False,
                    error_message=str(e)
                ))
    
    return results


async def _generate_textures_with_progress(config: Config, progress_tracker: 'ProgressTracker') -> List[GenerationResult]:
    """Generate PBR textures with detailed progress tracking.
    
    Args:
        config: Configuration object with all settings.
        progress_tracker: Progress tracker for UI feedback.
        
    Returns:
        List of generation results for all texture types.
    """
    logger.info(f"Starting texture generation for material: {config.material}")
    results = []
    
    try:
        # Step 1: Generate diffuse map from OpenAI
        progress_tracker.start_texture("diffuse", steps=3)
        progress_tracker.update_step("Preparing OpenAI request", "processing")
        
        diffuse_result = await _generate_diffuse_map_with_progress(config, progress_tracker)
        results.append(diffuse_result)
        
        if not diffuse_result.success:
            progress_tracker.complete_texture("diffuse", success=False, error=diffuse_result.error_message)
            logger.error(f"Failed to generate diffuse map: {diffuse_result.error_message}")
            return results
        
        progress_tracker.complete_texture("diffuse", success=True)
            
        # Step 2: Apply tessellation to the diffuse map
        tessellated_diffuse_path = await _apply_tessellation(diffuse_result.file_path, config)
        
        # Step 3: Derive other PBR maps from tessellated diffuse
        derived_results = await _derive_pbr_maps_with_progress(tessellated_diffuse_path, config, progress_tracker)
        results.extend(derived_results)
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Texture generation complete. {successful}/{len(results)} textures generated successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error during texture generation: {e}")
        # Add error result for any pending textures
        for texture_type in config.texture_config.types:
            if not any(r.texture_type == texture_type for r in results):
                results.append(GenerationResult(
                    texture_type=texture_type,
                    file_path="",
                    generation_time=0.0,
                    success=False,
                    error_message=str(e)
                ))
    
    return results


async def _generate_diffuse_map(config: Config) -> GenerationResult:
    """Generate the diffuse/albedo map using OpenAI.
    
    Args:
        config: Configuration object.
        
    Returns:
        GenerationResult for the diffuse map.
    """
    start_time = time.time()
    
    try:
        # Initialize OpenAI interface
        openai_interface = OpenAIInterface(api_key=config.api_key, org_id=config.org_id)
        
        # Prepare the diffuse map prompt
        resolution = config.texture_config.resolution
        prompt = (
            f"A {resolution.width}x{resolution.height} photorealistic, seamless diffuse/albedo texture map "
            f"of {config.material} with a {config.style} style. "
            f"This should be the base color map without any lighting, shadows, or reflections. "
            f"The texture must tile seamlessly on all edges."
        )
        
        logger.debug(f"Diffuse prompt: {prompt}")
        
        # Generate the image
        image_data = await openai_interface.generate_image(
            prompt=prompt,
            model=config.model,
            size=f"{resolution.width}x{resolution.height}",
        )
        
        generation_time = time.time() - start_time
        
        if image_data:
            # Save the diffuse map
            file_path = _get_texture_path(config, TextureType.DIFFUSE)
            save_texture(image_data, str(file_path))
            logger.info(f"Diffuse map saved to: {file_path}")
            
            return GenerationResult(
                texture_type=TextureType.DIFFUSE,
                file_path=str(file_path),
                generation_time=generation_time,
                success=True
            )
        else:
            return GenerationResult(
                texture_type=TextureType.DIFFUSE,
                file_path="",
                generation_time=generation_time,
                success=False,
                error_message="Failed to generate diffuse map from OpenAI"
            )
            
    except Exception as e:
        logger.error(f"Error generating diffuse map: {e}")
        return GenerationResult(
            texture_type=TextureType.DIFFUSE,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _generate_diffuse_map_with_progress(config: Config, progress_tracker: 'ProgressTracker') -> GenerationResult:
    """Generate the diffuse/albedo map using OpenAI with progress tracking.
    
    Args:
        config: Configuration object.
        progress_tracker: Progress tracker for UI feedback.
        
    Returns:
        GenerationResult for the diffuse map.
    """
    start_time = time.time()
    
    try:
        # Initialize OpenAI interface
        openai_interface = OpenAIInterface(api_key=config.api_key, org_id=config.org_id)
        
        # Prepare the diffuse map prompt
        progress_tracker.update_step("Building prompt", "processing")
        resolution = config.texture_config.resolution
        prompt = (
            f"A {resolution.width}x{resolution.height} photorealistic, seamless diffuse/albedo texture map "
            f"of {config.material} with a {config.style} style. "
            f"This should be the base color map without any lighting, shadows, or reflections. "
            f"The texture must tile seamlessly on all edges."
        )
        
        logger.debug(f"Diffuse prompt: {prompt}")
        
        # Generate the image with progress indication
        progress_tracker.update_step("Calling OpenAI API", "processing")
        
        with api_progress("Generating diffuse texture"):
            image_data = await openai_interface.generate_image(
                prompt=prompt,
                model=config.model,
                size=f"{resolution.width}x{resolution.height}",
            )
        
        progress_tracker.update_step("Saving texture", "processing")
        generation_time = time.time() - start_time
        
        if image_data:
            # Save the diffuse map
            file_path = _get_texture_path(config, TextureType.DIFFUSE)
            save_texture(image_data, str(file_path))
            logger.info(f"Diffuse map saved to: {file_path}")
            
            progress_tracker.update_step("Saved successfully", "complete")
            
            return GenerationResult(
                texture_type=TextureType.DIFFUSE,
                file_path=str(file_path),
                generation_time=generation_time,
                success=True
            )
        else:
            progress_tracker.update_step("API call failed", "failed")
            return GenerationResult(
                texture_type=TextureType.DIFFUSE,
                file_path="",
                generation_time=generation_time,
                success=False,
                error_message="Failed to generate diffuse map from OpenAI"
            )
            
    except Exception as e:
        logger.error(f"Error generating diffuse map: {e}")
        progress_tracker.update_step(f"Error: {str(e)}", "failed")
        return GenerationResult(
            texture_type=TextureType.DIFFUSE,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _apply_tessellation(diffuse_path: str, config: Config) -> str:
    """Apply tessellation to the diffuse map.
    
    Args:
        diffuse_path: Path to the diffuse map.
        config: Configuration object.
        
    Returns:
        Path to the tessellated diffuse map.
    """
    logger.info("Applying tessellation for seamless tiling")
    
    try:
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Apply tessellation for seamless tiling
        tessellated_image = apply_tessellation(diffuse_image, blend_width=50)
        
        # Save tessellated version with suffix
        path_obj = Path(diffuse_path)
        tessellated_path = path_obj.parent / f"{path_obj.stem}_tessellated{path_obj.suffix}"
        tessellated_image.save(str(tessellated_path))
        
        logger.info(f"Tessellated diffuse saved to: {tessellated_path}")
        return str(tessellated_path)
        
    except Exception as e:
        logger.error(f"Error applying tessellation: {e}")
        logger.warning("Falling back to original diffuse map")
        return diffuse_path


async def _derive_pbr_maps(diffuse_path: str, config: Config) -> List[GenerationResult]:
    """Derive PBR maps from the tessellated diffuse map.
    
    Args:
        diffuse_path: Path to the tessellated diffuse map.
        config: Configuration object.
        
    Returns:
        List of GenerationResult for derived maps.
    """
    results = []
    
    # Map texture types to their derivation modules
    derivation_modules = {
        TextureType.NORMAL: _derive_normal_map,
        TextureType.ROUGHNESS: _derive_roughness_map,
        TextureType.METALLIC: _derive_metallic_map,
        TextureType.AMBIENT_OCCLUSION: _derive_ambient_occlusion_map,
        TextureType.HEIGHT: _derive_height_map,
        TextureType.EMISSIVE: _derive_emissive_map,
    }
    
    # Process each requested texture type (except diffuse which is already done)
    for texture_type in config.texture_config.types:
        if texture_type == TextureType.DIFFUSE:
            continue  # Already generated
            
        if texture_type in derivation_modules:
            logger.info(f"Deriving {texture_type.value} map")
            start_time = time.time()
            
            try:
                # Call the appropriate derivation module
                derive_func = derivation_modules[texture_type]
                result = await derive_func(diffuse_path, config, texture_type)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error deriving {texture_type.value} map: {e}")
                results.append(GenerationResult(
                    texture_type=texture_type,
                    file_path="",
                    generation_time=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                ))
        else:
            logger.warning(f"No derivation module for texture type: {texture_type.value}")
    
    return results


async def _derive_pbr_maps_with_progress(diffuse_path: str, config: Config, progress_tracker: 'ProgressTracker') -> List[GenerationResult]:
    """Derive PBR maps from the tessellated diffuse map with progress tracking.
    
    Args:
        diffuse_path: Path to the tessellated diffuse map.
        config: Configuration object.
        progress_tracker: Progress tracker for UI feedback.
        
    Returns:
        List of GenerationResult for derived maps.
    """
    results = []
    
    # Map texture types to their derivation modules
    derivation_modules = {
        TextureType.NORMAL: _derive_normal_map,
        TextureType.ROUGHNESS: _derive_roughness_map,
        TextureType.METALLIC: _derive_metallic_map,
        TextureType.AMBIENT_OCCLUSION: _derive_ambient_occlusion_map,
        TextureType.HEIGHT: _derive_height_map,
        TextureType.EMISSIVE: _derive_emissive_map,
    }
    
    # Process each requested texture type (except diffuse which is already done)
    for texture_type in config.texture_config.types:
        if texture_type == TextureType.DIFFUSE:
            continue  # Already generated
            
        if texture_type in derivation_modules:
            # Start progress tracking for this texture
            progress_tracker.start_texture(texture_type.value, steps=2)
            progress_tracker.update_step("Processing image data", "processing")
            
            logger.info(f"Deriving {texture_type.value} map")
            start_time = time.time()
            
            try:
                # Call the appropriate derivation module
                derive_func = derivation_modules[texture_type]
                result = await derive_func(diffuse_path, config, texture_type)
                results.append(result)
                
                # Complete progress tracking
                if result.success:
                    progress_tracker.complete_texture(texture_type.value, success=True)
                else:
                    progress_tracker.complete_texture(texture_type.value, success=False, error=result.error_message)
                
            except Exception as e:
                logger.error(f"Error deriving {texture_type.value} map: {e}")
                error_result = GenerationResult(
                    texture_type=texture_type,
                    file_path="",
                    generation_time=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                progress_tracker.complete_texture(texture_type.value, success=False, error=str(e))
        else:
            logger.warning(f"No derivation module for texture type: {texture_type.value}")
            progress_tracker.add_warning(f"No derivation module for texture type: {texture_type.value}")
    
    return results


async def _derive_normal_map(diffuse_path: str, config: Config, texture_type: TextureType) -> GenerationResult:
    """Derive normal map from diffuse using NormalModule."""
    start_time = time.time()
    file_path = _get_texture_path(config, texture_type)
    
    try:
        # Initialize the normal module
        normal_module = NormalModule(config)
        
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Generate normal map from diffuse
        normal_map = normal_module.generate(input_data={"diffuse_map": diffuse_image})
        
        # Save the normal map
        normal_map.save(str(file_path))
        logger.info(f"Normal map saved to: {file_path}")
        
        return GenerationResult(
            texture_type=texture_type,
            file_path=str(file_path),
            generation_time=time.time() - start_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating normal map: {e}")
        return GenerationResult(
            texture_type=texture_type,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _derive_roughness_map(diffuse_path: str, config: Config, texture_type: TextureType) -> GenerationResult:
    """Derive roughness map from diffuse using RoughnessModule."""
    start_time = time.time()
    file_path = _get_texture_path(config, texture_type)
    
    try:
        # Initialize the roughness module with material properties
        # Check if we have advanced generation config
        if hasattr(config.material_properties, 'generation') and config.material_properties.generation:
            roughness_config = config.material_properties.generation.roughness
            roughness_module = RoughnessModule(
                material_type=config.material,
                base_value=roughness_config.base_value,
                variation=roughness_config.variation,
                invert=roughness_config.invert,
                directional=roughness_config.directional,
                direction_angle=roughness_config.direction_angle
            )
        else:
            # Legacy initialization
            roughness_module = RoughnessModule(
                roughness_range=config.material_properties.roughness_range or (0.0, 1.0),
                material_type=config.material
            )
        
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Generate roughness map from diffuse
        roughness_map = roughness_module.generate(diffuse_image)
        
        # Save the roughness map
        roughness_map.save(str(file_path))
        logger.info(f"Roughness map saved to: {file_path}")
        
        return GenerationResult(
            texture_type=texture_type,
            file_path=str(file_path),
            generation_time=time.time() - start_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating roughness map: {e}")
        return GenerationResult(
            texture_type=texture_type,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _derive_metallic_map(diffuse_path: str, config: Config, texture_type: TextureType) -> GenerationResult:
    """Derive metallic map from diffuse using MetallicModule."""
    start_time = time.time()
    file_path = _get_texture_path(config, texture_type)
    
    try:
        # Initialize the metallic module
        metallic_module = MetallicModule(config)
        
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Generate metallic map from diffuse
        metallic_map = metallic_module.generate(input_data={"diffuse_map": diffuse_image})
        
        # Save the metallic map
        metallic_map.save(str(file_path))
        logger.info(f"Metallic map saved to: {file_path}")
        
        return GenerationResult(
            texture_type=texture_type,
            file_path=str(file_path),
            generation_time=time.time() - start_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating metallic map: {e}")
        return GenerationResult(
            texture_type=texture_type,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _derive_ambient_occlusion_map(diffuse_path: str, config: Config, texture_type: TextureType) -> GenerationResult:
    """Derive ambient occlusion map from diffuse using AmbientOcclusionModule."""
    start_time = time.time()
    file_path = _get_texture_path(config, texture_type)
    
    try:
        # Initialize the AO module
        ao_module = AmbientOcclusionModule(config)
        
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Generate AO map from diffuse
        ao_map = ao_module.generate(input_data={"diffuse_map": diffuse_image})
        
        # Save the AO map
        ao_map.save(str(file_path))
        logger.info(f"Ambient occlusion map saved to: {file_path}")
        
        return GenerationResult(
            texture_type=texture_type,
            file_path=str(file_path),
            generation_time=time.time() - start_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating ambient occlusion map: {e}")
        return GenerationResult(
            texture_type=texture_type,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _derive_height_map(diffuse_path: str, config: Config, texture_type: TextureType) -> GenerationResult:
    """Derive height/displacement map from diffuse using HeightModule."""
    start_time = time.time()
    file_path = _get_texture_path(config, texture_type)
    
    try:
        # Initialize the height module
        height_module = HeightModule(config)
        
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Generate height map from diffuse
        height_map = height_module.generate(input_data={"diffuse_map": diffuse_image})
        
        # Save the height map
        height_map.save(str(file_path))
        logger.info(f"Height map saved to: {file_path}")
        
        return GenerationResult(
            texture_type=texture_type,
            file_path=str(file_path),
            generation_time=time.time() - start_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating height map: {e}")
        return GenerationResult(
            texture_type=texture_type,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


async def _derive_emissive_map(diffuse_path: str, config: Config, texture_type: TextureType) -> GenerationResult:
    """Derive emissive map from diffuse using EmissiveModule."""
    start_time = time.time()
    file_path = _get_texture_path(config, texture_type)
    
    try:
        # Initialize the emissive module
        emissive_module = EmissiveModule(config)
        
        # Load the diffuse map
        diffuse_image = Image.open(diffuse_path)
        
        # Generate emissive map from diffuse
        emissive_map = emissive_module.generate(input_data={"diffuse_map": diffuse_image})
        
        # Save the emissive map
        emissive_map.save(str(file_path))
        logger.info(f"Emissive map saved to: {file_path}")
        
        return GenerationResult(
            texture_type=texture_type,
            file_path=str(file_path),
            generation_time=time.time() - start_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating emissive map: {e}")
        return GenerationResult(
            texture_type=texture_type,
            file_path="",
            generation_time=time.time() - start_time,
            success=False,
            error_message=str(e)
        )


def _get_texture_path(config: Config, texture_type: TextureType) -> Path:
    """Generate the file path for a texture.
    
    Args:
        config: Configuration object.
        texture_type: Type of texture.
        
    Returns:
        Path object for the texture file.
    """
    resolution = config.texture_config.resolution
    filename = config.naming_convention.format(
        material=config.material,
        type=texture_type.value,
        resolution=f'{resolution.width}x{resolution.height}'
    )
    return Path(config.output_directory) / f"{filename}.{config.texture_config.format.value}"


async def _generate_preview(results: List[GenerationResult], config: Config) -> Optional[str]:
    """Generate a preview image showing all PBR maps on a sphere.
    
    Args:
        results: List of generation results containing texture paths
        config: Configuration object
        
    Returns:
        Path to preview image if successful, None otherwise
    """
    try:
        # Build texture paths dictionary from results
        texture_paths = {}
        for result in results:
            if result.success and result.file_path:
                texture_type = result.texture_type.value
                texture_paths[texture_type] = result.file_path
        
        # Generate the preview
        preview_path = generate_material_preview(
            material_name=config.material,
            texture_paths=texture_paths,
            output_dir=config.output_directory,
            preview_size=(512, 512)  # TODO: Make this configurable
        )
        
        if preview_path:
            logger.info(f"Preview generated: {preview_path}")
        else:
            logger.warning("Failed to generate preview")
            
        return preview_path
        
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return None