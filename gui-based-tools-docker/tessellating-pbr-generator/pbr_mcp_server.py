#!/usr/bin/env python3
"""
PBR Generator TCP MCP Server - Provides PBR texture generation as a networked service.
Listens on TCP port 9878 and responds to MCP requests.
"""

import asyncio
import json
import socket
import sys
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add the src directory to the Python path for imports
sys.path.insert(0, '/opt/tessellating-pbr-generator/src')
sys.path.insert(0, '/opt/tessellating-pbr-generator')

from src.config import load_config
from src.types.config import Config
from src.core.generator import generate_textures
from src.utils.logging import setup_logger, get_logger

# Set up logging
setup_logger(debug=False, verbose=False, no_color=True)
logger = get_logger(__name__)

class PBRGeneratorServer:
    def __init__(self, host='0.0.0.0', port=9878):
        self.host = host
        self.port = port
        self.server = None

    async def handle_client(self, reader, writer):
        """Handle incoming client connections."""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"Client connected from {client_addr}")
        
        try:
            while True:
                # Read the JSON request
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    request = json.loads(data.decode('utf-8').strip())
                    logger.info(f"Received request: {request.get('tool', 'unknown')}")
                    
                    # Process the request
                    response = await self.process_request(request)
                    
                    # Send the response
                    response_json = json.dumps(response) + '\n'
                    writer.write(response_json.encode('utf-8'))
                    await writer.drain()
                    
                except json.JSONDecodeError:
                    error_response = {"error": "Invalid JSON received"}
                    writer.write((json.dumps(error_response) + '\n').encode('utf-8'))
                    await writer.drain()
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    error_response = {"error": f"Internal server error: {str(e)}"}
                    writer.write((json.dumps(error_response) + '\n').encode('utf-8'))
                    await writer.drain()
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"Client {client_addr} disconnected")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process an MCP request and return a response."""
        tool = request.get('tool')
        params = request.get('params', {})
        
        if tool == 'generate_material':
            return await self.generate_material(params)
        else:
            return {"error": f"Unknown tool: {tool}"}

    async def generate_material(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PBR material textures based on parameters."""
        start_time = time.time()
        
        try:
            # Validate required parameters
            material = params.get('material')
            if not material:
                return {"success": False, "error": "Missing required parameter: material"}

            # Set up default config path
            config_path = params.get('config') or '/opt/tessellating-pbr-generator/config/default.json'
            
            # Load base configuration
            try:
                config_dict = load_config(config_path)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return {"success": False, "error": f"Failed to load configuration: {str(e)}"}

            # Override with command line arguments
            config_dict["material"]["base_material"] = material

            # Handle resolution
            if 'resolution' in params:
                resolution_str = params['resolution']
                try:
                    width, height = map(int, resolution_str.split('x'))
                    config_dict["textures"]["resolution"]["width"] = width
                    config_dict["textures"]["resolution"]["height"] = height
                except ValueError:
                    return {"success": False, "error": f"Invalid resolution format: {resolution_str}"}

            # Handle output directory
            output_dir = params.get('output', '/workspace/pbr_outputs')
            config_dict["output"]["directory"] = output_dir
            
            # Ensure output directory exists
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Handle texture types
            if 'types' in params:
                config_dict["textures"]["types"] = params['types']

            # Handle preview option
            if params.get('preview'):
                config_dict["output"]["create_preview"] = True

            # Create Config object
            config = Config.from_dict(config_dict)
            
            logger.info(f"Generating textures for material: {config.material}")
            logger.info(f"Resolution: {config.texture_config.resolution.width}x{config.texture_config.resolution.height}")
            logger.info(f"Output directory: {config.output_directory}")

            # Generate textures
            results = await generate_textures(config)
            
            # Build response
            generation_time = time.time() - start_time
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            # Collect generated files
            generated_files = [r.file_path for r in successful_results if r.file_path]
            
            # Build detailed results
            texture_results = {}
            for result in results:
                texture_results[result.texture_type.value] = {
                    "success": result.success,
                    "file_path": result.file_path,
                    "generation_time": result.generation_time,
                    "error_message": result.error_message
                }

            if successful_results:
                return {
                    "success": True,
                    "generation_time": generation_time,
                    "generated_files": generated_files,
                    "texture_results": texture_results,
                    "summary": f"Generated {len(successful_results)}/{len(results)} textures successfully"
                }
            else:
                # All failed
                error_messages = [r.error_message for r in failed_results if r.error_message]
                return {
                    "success": False,
                    "error": f"All texture generation failed. Errors: {'; '.join(error_messages)}",
                    "generation_time": generation_time,
                    "texture_results": texture_results
                }

        except Exception as e:
            logger.error(f"Unexpected error during texture generation: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "generation_time": time.time() - start_time
            }

    async def start_server(self):
        """Start the TCP server."""
        try:
            self.server = await asyncio.start_server(
                self.handle_client, 
                self.host, 
                self.port
            )
            
            logger.info(f"PBR Generator MCP Server started on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

    async def stop_server(self):
        """Stop the TCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("PBR Generator MCP Server stopped")

async def main():
    """Main function to start the server."""
    server = PBRGeneratorServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.stop_server()

if __name__ == "__main__":
    asyncio.run(main())