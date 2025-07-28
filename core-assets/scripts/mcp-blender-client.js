#!/usr/bin/env node

/**
 * MCP Server for Blender TCP Communication
 * 
 * This server acts as a bridge between Claude Code MCP and Blender running with
 * the MCP addon. It translates MCP tool calls to TCP messages for Blender.
 */

const net = require('net');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

// Configuration from environment variables
const BLENDER_HOST = process.env.BLENDER_HOST || 'blender_desktop';
const BLENDER_PORT = parseInt(process.env.BLENDER_PORT || '9876');
const CONNECTION_TIMEOUT = 30000; // 30 seconds
const RESPONSE_TIMEOUT = 60000; // 60 seconds for Blender operations

class BlenderMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'blender-tcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  async sendToBlender(command) {
    return new Promise((resolve, reject) => {
      const client = new net.Socket();
      let responseData = '';
      let hasResponded = false;

      // Set connection timeout
      const connectionTimer = setTimeout(() => {
        if (!hasResponded) {
          hasResponded = true;
          client.destroy();
          reject(new Error(`Connection timeout: Could not connect to Blender at ${BLENDER_HOST}:${BLENDER_PORT}`));
        }
      }, CONNECTION_TIMEOUT);

      // Set response timeout
      const responseTimer = setTimeout(() => {
        if (!hasResponded) {
          hasResponded = true;
          client.destroy();
          reject(new Error('Response timeout: Blender operation took too long'));
        }
      }, RESPONSE_TIMEOUT);

      client.connect(BLENDER_PORT, BLENDER_HOST, () => {
        clearTimeout(connectionTimer);
        // Send command as JSON without newline (addon expects raw JSON)
        client.write(JSON.stringify(command));
      });

      client.on('data', (data) => {
        responseData += data.toString();
        
        // Check if we have a complete JSON response
        try {
          const response = JSON.parse(responseData);
          clearTimeout(responseTimer);
          hasResponded = true;
          client.end();
          resolve(response);
        } catch (e) {
          // Not complete JSON yet, continue accumulating
        }
      });

      client.on('error', (err) => {
        clearTimeout(connectionTimer);
        clearTimeout(responseTimer);
        if (!hasResponded) {
          hasResponded = true;
          reject(new Error(`Connection error: ${err.message}`));
        }
      });

      client.on('close', () => {
        clearTimeout(connectionTimer);
        clearTimeout(responseTimer);
        if (!hasResponded) {
          hasResponded = true;
          if (responseData) {
            try {
              const response = JSON.parse(responseData);
              resolve(response);
            } catch (e) {
              reject(new Error(`Invalid response from Blender: ${responseData}`));
            }
          } else {
            reject(new Error('Connection closed without response'));
          }
        }
      });
    });
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'blender_execute',
          description: 'Execute Python code in Blender',
          inputSchema: {
            type: 'object',
            properties: {
              code: {
                type: 'string',
                description: 'Python code to execute in Blender',
              },
            },
            required: ['code'],
          },
        },
        {
          name: 'blender_get_info',
          description: 'Get information about the current Blender scene',
          inputSchema: {
            type: 'object',
            properties: {
              info_type: {
                type: 'string',
                enum: ['scene', 'objects', 'materials', 'meshes', 'modifiers'],
                description: 'Type of information to retrieve',
              },
            },
            required: ['info_type'],
          },
        },
        {
          name: 'blender_create_object',
          description: 'Create a new object in Blender',
          inputSchema: {
            type: 'object',
            properties: {
              object_type: {
                type: 'string',
                enum: ['mesh', 'curve', 'surface', 'meta', 'text', 'armature', 'lattice', 'empty', 'light', 'camera'],
                description: 'Type of object to create',
              },
              name: {
                type: 'string',
                description: 'Name for the new object',
              },
              location: {
                type: 'array',
                items: { type: 'number' },
                minItems: 3,
                maxItems: 3,
                description: 'Location [x, y, z]',
              },
            },
            required: ['object_type', 'name'],
          },
        },
        {
          name: 'blender_modify_object',
          description: 'Modify properties of an existing object',
          inputSchema: {
            type: 'object',
            properties: {
              object_name: {
                type: 'string',
                description: 'Name of the object to modify',
              },
              properties: {
                type: 'object',
                description: 'Properties to modify (e.g., location, rotation, scale)',
              },
            },
            required: ['object_name', 'properties'],
          },
        },
        {
          name: 'blender_render',
          description: 'Render the current scene or animation',
          inputSchema: {
            type: 'object',
            properties: {
              output_path: {
                type: 'string',
                description: 'Output file path for the render',
              },
              animation: {
                type: 'boolean',
                description: 'Render animation instead of single frame',
                default: false,
              },
              start_frame: {
                type: 'integer',
                description: 'Start frame for animation',
              },
              end_frame: {
                type: 'integer',
                description: 'End frame for animation',
              },
            },
            required: ['output_path'],
          },
        },
        {
          name: 'blender_save',
          description: 'Save the current Blender file',
          inputSchema: {
            type: 'object',
            properties: {
              filepath: {
                type: 'string',
                description: 'Path to save the .blend file',
              },
            },
            required: ['filepath'],
          },
        },
        {
          name: 'blender_load',
          description: 'Load a Blender file',
          inputSchema: {
            type: 'object',
            properties: {
              filepath: {
                type: 'string',
                description: 'Path to the .blend file to load',
              },
            },
            required: ['filepath'],
          },
        },
        {
          name: 'blender_screenshot',
          description: 'Take a screenshot of the current viewport',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let command;
        
        // Map MCP tool names to Blender addon command types
        switch (name) {
          case 'blender_execute':
            command = {
              type: 'execute_code',
              params: { code: args.code }
            };
            break;
          case 'blender_get_info':
            if (args.info_type === 'scene') {
              command = { type: 'get_scene_info', params: {} };
            } else if (args.info_type === 'objects' && args.object_name) {
              command = { type: 'get_object_info', params: { name: args.object_name } };
            } else {
              command = { type: 'get_scene_info', params: {} };
            }
            break;
          case 'blender_screenshot':
            command = { type: 'get_viewport_screenshot', params: {} };
            break;
          default:
            // For other tools, try to execute as Python code
            command = {
              type: 'execute_code',
              params: { code: this.generatePythonCode(name, args) }
            };
        }

        const response = await this.sendToBlender(command);

        if (response.status === 'success') {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(response.result, null, 2),
              },
            ],
          };
        } else {
          return {
            content: [
              {
                type: 'text',
                text: `Error: ${response.message || 'Unknown error occurred'}`,
              },
            ],
            isError: true,
          };
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Failed to communicate with Blender: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  generatePythonCode(toolName, args) {
    // Generate Python code for tools that map to Blender operations
    switch (toolName) {
      case 'blender_create_object':
        return this.generateCreateObjectCode(args);
      case 'blender_modify_object':
        return this.generateModifyObjectCode(args);
      case 'blender_render':
        return this.generateRenderCode(args);
      case 'blender_save':
        return `bpy.ops.wm.save_mainfile(filepath="${args.filepath}")`;
      case 'blender_load':
        return `bpy.ops.wm.open_mainfile(filepath="${args.filepath}")`;
      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  }

  generateCreateObjectCode(args) {
    const { object_type, name, location = [0, 0, 0] } = args;
    const loc = `location=(${location[0]}, ${location[1]}, ${location[2]})`;
    
    const typeMap = {
      'mesh': 'bpy.ops.mesh.primitive_cube_add',
      'curve': 'bpy.ops.curve.primitive_bezier_curve_add',
      'surface': 'bpy.ops.surface.primitive_nurbs_surface_sphere_add',
      'meta': 'bpy.ops.object.metaball_add',
      'text': 'bpy.ops.object.text_add',
      'armature': 'bpy.ops.object.armature_add',
      'lattice': 'bpy.ops.object.lattice_add',
      'empty': 'bpy.ops.object.empty_add',
      'light': 'bpy.ops.object.light_add',
      'camera': 'bpy.ops.object.camera_add',
    };
    
    const createOp = typeMap[object_type] || 'bpy.ops.mesh.primitive_cube_add';
    return `
${createOp}(${loc})
obj = bpy.context.active_object
obj.name = "${name}"
print(f"Created {obj.type} object: {obj.name}")
`;
  }

  generateModifyObjectCode(args) {
    const { object_name, properties } = args;
    let code = `
obj = bpy.data.objects.get("${object_name}")
if obj:
`;
    
    for (const [key, value] of Object.entries(properties)) {
      if (Array.isArray(value)) {
        code += `    obj.${key} = (${value.join(', ')})\n`;
      } else if (typeof value === 'string') {
        code += `    obj.${key} = "${value}"\n`;
      } else {
        code += `    obj.${key} = ${value}\n`;
      }
    }
    
    code += `    print(f"Modified object: {obj.name}")\n`;
    code += `else:\n    print(f"Object '${object_name}' not found")`;
    
    return code;
  }

  generateRenderCode(args) {
    const { output_path, animation = false, start_frame = 1, end_frame = 250 } = args;
    
    if (animation) {
      return `
bpy.context.scene.frame_start = ${start_frame}
bpy.context.scene.frame_end = ${end_frame}
bpy.context.scene.render.filepath = "${output_path}"
bpy.ops.render.render(animation=True)
print(f"Rendered animation to: ${output_path}")
`;
    } else {
      return `
bpy.context.scene.render.filepath = "${output_path}"
bpy.ops.render.render(write_still=True)
print(f"Rendered frame to: ${output_path}")
`;
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    // Log startup info to stderr (not stdout, which is used for MCP protocol)
    console.error(`Blender MCP Server started`);
    console.error(`Will connect to Blender at ${BLENDER_HOST}:${BLENDER_PORT}`);
  }
}

// Handle errors gracefully
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Start the server
const server = new BlenderMCPServer();
server.run().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});