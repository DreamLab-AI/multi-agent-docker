# PBR Importer Visual Usage Guide

## Quick Start Guide

### Step 1: Generate PBR Textures

First, use the tessellating-pbr-generator to create your texture sets:

```bash
# Generate a stone PBR texture set
python main.py generate stone --size 1024 --seamless

# Output will be in: output/stone/
# Files created:
# - stone_diffuse_1024x1024.png
# - stone_normal_1024x1024.png  
# - stone_roughness_1024x1024.png
# - stone_metallic_1024x1024.png
# - stone_height_1024x1024.png
# - stone_ao_1024x1024.png
```

### Step 2: Install the Blender Addon

1. Open Blender (3.0+)
2. Go to **Edit → Preferences**
3. Select **Add-ons** tab
4. Click **Install...** button
5. Navigate to `blender/pbr_importer.py`
6. Click **Install Add-on**
7. Enable the addon by checking the box

### Step 3: Import PBR Texture Set

1. **Create or select an object** to apply the material to:
   ```
   Shift+A → Mesh → UV Sphere (or any mesh)
   ```

2. **Import the PBR set**:
   ```
   File → Import → PBR Texture Set
   ```

3. **Navigate to your texture folder**:
   ```
   Select the folder: output/stone/
   ```

4. **Configure import options**:
   - ✅ Create New Material
   - ✅ Apply to Selected Objects  
   - Displacement Scale: 0.1
   - AO Mix Factor: 0.5

5. **Click "Import PBR Texture Set"**

## Node Setup Explanation

The addon creates this node structure automatically:

```
┌─────────────────┐
│ Diffuse Texture │ ─────┐
└─────────────────┘      │    ┌──────────┐     ┌────────────────┐
                         ├───►│ Mix RGB  │────►│                │
┌─────────────────┐      │    │(Multiply)│     │   Principled   │
│   AO Texture    │ ─────┘    └──────────┘     │     BSDF      │
└─────────────────┘                             │                │
                                                │ • Base Color   │
┌─────────────────┐    ┌──────────────┐       │ • Roughness    │    ┌──────────┐
│ Normal Texture  │───►│ Normal Map   │───────►│ • Normal       │───►│ Material │
└─────────────────┘    └──────────────┘        │ • Metallic     │    │  Output  │
                                                │                │    └──────────┘
┌─────────────────┐                            └────────────────┘           │
│Roughness Texture│────────────────────────────►                           │
└─────────────────┘                                                         │
                                                                           │
┌─────────────────┐                                                        │
│Metallic Texture │────────────────────────────►                          │
└─────────────────┘                                                        │
                                                                           │
┌─────────────────┐    ┌──────────────┐                                  │
│ Height Texture  │───►│ Displacement │──────────────────────────────────┘
└─────────────────┘    └──────────────┘
```

## Common Workflows

### 1. Basic Material Import

```python
# Minimal setup - just import and apply
File → Import → PBR Texture Set
Select folder → Import
```

### 2. Multiple Materials on One Object

```python
# Add multiple material slots
1. Select object
2. Properties → Material Properties → "+" (Add slot)
3. Import different PBR sets for each slot
4. Assign faces to different materials in Edit mode
```

### 3. Batch Import for Library

```python
# Import multiple materials at once
1. Create multiple objects
2. Select first object → Import PBR set
3. Select next object → Import different PBR set
4. Repeat for all materials
```

## Tips and Tricks

### Optimizing Displacement

1. **For close-up details**:
   - Add Subdivision Surface modifier (2-3 levels)
   - Set Displacement Scale: 0.05-0.15
   - Use Adaptive Subdivision (Cycles only)

2. **For distant objects**:
   - Use bump mapping instead (disconnect displacement)
   - Or use very low Displacement Scale: 0.01-0.05

### Material Variations

Create variations by adjusting after import:

1. **Roughness variation**:
   ```
   Add ColorRamp after Roughness texture
   Adjust contrast for more/less rough areas
   ```

2. **Color variation**:
   ```
   Add Hue/Saturation node after Diffuse
   Adjust hue for color variants
   ```

3. **Wear and tear**:
   ```
   Mix two PBR sets using a grunge mask
   Blend between clean and worn materials
   ```

## Viewport Display Settings

For best preview results:

1. **Shading Mode**: Set to Material Preview or Rendered
2. **HDRI Lighting**: Use built-in HDRIs for realistic lighting
3. **Viewport Sampling**: Increase for better quality (but slower)

### Recommended Viewport Settings:

```
Shading → Material Preview
Options → World Opacity: 0.5
Options → Backface Culling: Off
Scene Lights: On
Scene World: Off
```

## Performance Optimization

### For Large Scenes

1. **Texture Resolution**:
   - Use 2K textures for most objects
   - 4K only for hero/close-up objects
   - 1K or 512px for background objects

2. **Displacement**:
   - Use bump mapping for distant objects
   - True displacement only where needed
   - Consider baking displacement to normal maps

3. **Memory Usage**:
   - Pack textures into .blend file for portability
   - Use Image → Pack All
   - Or keep external for easier updates

## Troubleshooting Guide

### Issue: Black or Pink Materials

**Solution**:
- Check texture paths are correct
- Ensure textures are in supported formats
- Verify color space settings

### Issue: No Displacement Visible

**Solution**:
1. Add Subdivision Surface modifier
2. In Material Settings → Settings → Displacement: "Displacement Only"
3. Increase subdivision levels
4. Check displacement scale isn't too low

### Issue: Normal Map Looks Wrong

**Solution**:
- Ensure Normal Map node is present
- Check texture is set to Non-Color
- Verify normal map follows OpenGL standard
- Try adjusting Normal Map strength

## Advanced Customization

### Modifying the Addon

To add custom features:

1. **Add new texture types**:
   ```python
   # In find_texture_files(), add to texture_types dict:
   'emissive': ['emissive', 'emission', 'glow']
   ```

2. **Custom node setups**:
   ```python
   # In create_material(), add custom nodes:
   if 'emissive' in texture_files:
       # Add emission setup
   ```

3. **Presets system**:
   ```python
   # Add material presets for common setups
   presets = {
       'stone': {'roughness': 0.8, 'displacement': 0.15},
       'metal': {'roughness': 0.2, 'displacement': 0.05}
   }
   ```

## Integration Examples

### With Geometry Nodes

```python
# Use PBR materials with procedural geometry
1. Create Geometry Nodes modifier
2. Use Set Material node
3. Reference imported PBR material
```

### With Python Scripting

```python
import bpy

# Automated material assignment
for obj in bpy.data.objects:
    if 'stone' in obj.name.lower():
        bpy.context.view_layer.objects.active = obj
        bpy.ops.import_texture.pbr_set(
            filepath="/path/to/stone/textures/"
        )
```

## Best Practices

1. **Naming Convention**: Keep consistent texture naming
2. **Folder Organization**: One folder per material
3. **Resolution Matching**: All maps same resolution
4. **Color Space**: Always check after import
5. **Test Renders**: Do test renders at different distances

## Conclusion

The PBR Texture Set Importer streamlines the workflow from texture generation to final render. With automatic detection and proper node setup, you can focus on creative work rather than technical setup.

For more help, see:
- Main documentation: `README.md`
- Example scripts: `example_usage.py`
- Texture generator docs: `../docs/`