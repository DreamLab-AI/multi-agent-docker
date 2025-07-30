"""
Example Usage of PBR Texture Set Importer
=========================================

This script demonstrates how to use the PBR importer addon programmatically
in Blender. Run this script in Blender's Text Editor.
"""

import bpy
import os
from pathlib import Path


def setup_scene():
    """Set up a simple scene for testing PBR materials"""
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Create a UV sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        location=(0, 0, 0),
        segments=32,
        ring_count=16
    )
    sphere = bpy.context.active_object
    sphere.name = "PBR_Test_Sphere"
    
    # Add subdivision surface modifier for better displacement
    subdiv = sphere.modifiers.new("Subdivision", 'SUBSURF')
    subdiv.levels = 2
    subdiv.render_levels = 3
    
    # Create a plane as ground
    bpy.ops.mesh.primitive_plane_add(
        size=10,
        location=(0, 0, -1.5)
    )
    plane = bpy.context.active_object
    plane.name = "Ground_Plane"
    
    # Set up the viewport shading
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    space.shading.use_scene_lights = True
                    space.shading.use_scene_world = False
    
    # Add an HDRI for better lighting (optional)
    world = bpy.data.worlds['World']
    world.use_nodes = True
    bg_node = world.node_tree.nodes['Background']
    bg_node.inputs[1].default_value = 0.5  # Reduce strength
    
    # Select the sphere for material application
    bpy.context.view_layer.objects.active = sphere
    sphere.select_set(True)
    plane.select_set(False)


def import_pbr_textures(texture_folder):
    """Import PBR textures using the addon"""
    # Ensure the addon is enabled
    addon_name = "pbr_importer"
    if addon_name not in bpy.context.preferences.addons:
        print("PBR Importer addon is not installed or enabled!")
        return False
    
    # Import the PBR texture set
    try:
        bpy.ops.import_texture.pbr_set(
            filepath=str(texture_folder),
            create_new_material=True,
            apply_to_selected=True,
            displacement_scale=0.1,
            ao_mix_factor=0.5
        )
        print(f"Successfully imported PBR textures from: {texture_folder}")
        return True
    except Exception as e:
        print(f"Error importing textures: {e}")
        return False


def setup_displacement():
    """Configure displacement settings for better results"""
    # Get the active object
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        return
    
    # Enable displacement in material settings
    if obj.active_material:
        obj.active_material.cycles.displacement_method = 'DISPLACEMENT'
    
    # Set up displacement in modifier (for viewport)
    # This is handled by the subdivision modifier we added earlier


def render_preview(output_path):
    """Render a preview of the material"""
    # Set up render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'  # or 'BLENDER_EEVEE'
    scene.cycles.samples = 128  # Lower for preview
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 50  # 50% for faster preview
    
    # Set output path
    scene.render.filepath = str(output_path)
    scene.render.image_settings.file_format = 'PNG'
    
    # Render
    bpy.ops.render.render(write_still=True)
    print(f"Preview rendered to: {output_path}")


def main():
    """Main execution function"""
    # Example texture folder path - update this to your actual path
    texture_folder = Path("/path/to/your/pbr/textures/stone/")
    
    # You can also use relative path from the blend file
    # blend_file_path = Path(bpy.data.filepath).parent
    # texture_folder = blend_file_path / "textures" / "stone"
    
    # Set up the test scene
    print("Setting up test scene...")
    setup_scene()
    
    # Import PBR textures
    print(f"Importing PBR textures from: {texture_folder}")
    if import_pbr_textures(texture_folder):
        # Configure displacement
        setup_displacement()
        
        # Optional: Render a preview
        # output_path = texture_folder.parent / "preview_render.png"
        # render_preview(output_path)
        
        print("PBR material import completed!")
    else:
        print("Failed to import PBR textures")


# Example: Import multiple texture sets
def batch_import_example():
    """Example of importing multiple PBR sets"""
    base_folder = Path("/path/to/pbr/library/")
    material_folders = ["stone", "metal", "wood", "fabric"]
    
    for mat_name in material_folders:
        texture_folder = base_folder / mat_name
        if texture_folder.exists():
            # Create a cube for each material
            bpy.ops.mesh.primitive_cube_add(
                location=(len(bpy.data.objects) * 2.5, 0, 0)
            )
            
            # Import and apply the material
            import_pbr_textures(texture_folder)


# Run the main function
if __name__ == "__main__":
    main()
    
    # Uncomment to run batch import example
    # batch_import_example()