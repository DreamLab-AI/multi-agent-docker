import bpy
import time

def start_job():
    """
    This function is called by a timer after Blender has started.
    It enables the MCP addon and starts the MCP server.
    """
    try:
        print("MCP AUTOSTART: Enabling 'addon' module...")
        bpy.ops.preferences.addon_enable(module='addon')
        print("MCP AUTOSTART: Addon enabled.")

        # A small delay to ensure the operator is fully registered after enabling the addon
        time.sleep(1)

        print("MCP AUTOSTART: Calling operator to start server...")
        bpy.ops.blendermcp.start_server()
        print("MCP AUTOSTART: Server start command issued successfully.")

    except Exception as e:
        print(f"!!! MCP AUTOSTART ERROR: Failed to start server: {e}")
        # Log to a file for easier debugging inside the container
        with open("/tmp/mcp_autostart_error.log", "w") as f:
            f.write(str(e))

    # This timer should only run once
    return None

# Register a timer to run our start_job function 5 seconds after Blender starts.
# This gives Blender enough time to initialize completely before we try to run operators.
bpy.app.timers.register(start_job, first_interval=5.0)

print("MCP AUTOSTART: Autostart script loaded. Server will start in 5 seconds.")