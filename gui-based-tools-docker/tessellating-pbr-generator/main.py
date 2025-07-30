#!/usr/bin/env python3
"""Main entry point for the Tessellating PBR Texture Generator."""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from src.config import load_config
from src.types.config import Config
from src.utils.logging import setup_logger, get_logger, print_summary
from src.utils.progress import ProgressTracker


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate seamless PBR textures using AI"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file (default: config/default.json)"
    )
    
    parser.add_argument(
        "-m", "--material",
        type=str,
        help="Material to generate (overrides config)"
    )
    
    parser.add_argument(
        "-r", "--resolution",
        type=str,
        help="Resolution (e.g., 2048x2048, overrides config)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output directory (overrides config)"
    )
    
    parser.add_argument(
        "-t", "--types",
        nargs="+",
        help="Texture types to generate (e.g., diffuse normal roughness)"
    )
    
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Generate preview image"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed progress"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimize output to only essential information"
    )
    
    return parser.parse_args()


async def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logger(debug=args.debug, verbose=args.verbose, no_color=args.no_color)
    logger = get_logger(__name__)
    
    # Track overall generation time
    generation_start_time = time.time()
    warnings = []
    
    if not args.quiet:
        logger.info("🎨 Starting Tessellating PBR Texture Generator")
    
    try:
        # Load configuration
        config_dict = load_config(args.config)
        
        # Override with command line arguments
        if args.material:
            config_dict["material"]["base_material"] = args.material
        
        if args.resolution:
            width, height = map(int, args.resolution.split('x'))
            config_dict["textures"]["resolution"]["width"] = width
            config_dict["textures"]["resolution"]["height"] = height
        
        if args.output:
            config_dict["output"]["directory"] = args.output
        
        if args.types:
            config_dict["textures"]["types"] = args.types
        
        if args.preview:
            config_dict["output"]["create_preview"] = True
        
        # Create Config object
        config = Config.from_dict(config_dict)
        
        # Log configuration
        if not args.quiet:
            logger.info(f"📦 Material: {config.material}")
            logger.info(f"🎭 Style: {config.style}")
            logger.info(f"📐 Resolution: {config.texture_config.resolution.width}x{config.texture_config.resolution.height}")
            logger.info(f"🗂️  Texture types: {[t.value for t in config.texture_config.types]}")
            logger.info(f"📁 Output directory: {config.output_directory}")
            
        # Initialize progress tracker
        progress_tracker = ProgressTracker(
            total_textures=len(config.texture_config.types),
            material_name=config.material
        )
        
        # Generate textures with progress tracking
        if not args.quiet:
            logger.info("🚀 Starting texture generation...")
        
        # Import generator here to avoid circular imports
        from src.core.generator import generate_textures_with_progress
        
        # Generate textures
        results = await generate_textures_with_progress(config, progress_tracker if not args.quiet else None)
        
        # Close progress tracker and get summary data
        summary_data = progress_tracker.close() if not args.quiet else {'total_time': time.time() - generation_start_time, 'warnings': warnings}
        
        # Print summary report
        if not args.quiet:
            print_summary(results, summary_data['total_time'], summary_data['warnings'])
        else:
            # Minimal output for quiet mode
            successful = sum(1 for r in results if r.success)
            logger.info(f"Generated {successful}/{len(results)} textures in {summary_data['total_time']:.1f}s")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())