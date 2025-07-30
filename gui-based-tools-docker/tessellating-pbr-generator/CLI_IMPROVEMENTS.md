# CLI Improvements Documentation

## Overview

The Tessellating PBR Generator now includes comprehensive CLI improvements for better user experience:

## New Features

### 1. Progress Bars with tqdm
- **Overall progress** showing texture generation completion
- **Individual texture progress** with step-by-step updates
- **API call progress** with time indicators
- **Real-time estimates** for remaining work

### 2. Color-Coded Output
- **🟢 Green**: Success messages and completed tasks
- **🟡 Yellow**: Warnings and non-critical issues  
- **🔴 Red**: Errors and failed operations
- **🔵 Blue**: General information and status updates
- **🟣 Magenta**: API operations and external calls

### 3. New Command Line Flags

#### `--verbose`
Enables detailed output with:
- Timestamps for all operations
- Extended debugging information
- Step-by-step process details
- Performance metrics

#### `--quiet` 
Minimizes output to only essential information:
- Simple progress indicators
- Final summary only
- Error messages when needed

#### `--no-color`
Disables colored output for:
- Terminal compatibility
- Log file output  
- Automated environments

#### `--debug`
Enhanced debug logging with:
- Internal state information
- API request/response details
- Processing pipeline steps

### 4. Summary Report
At completion, displays:
- **Total generation time**
- **Success/failure counts**  
- **Generated file locations**
- **Warning messages**
- **Performance statistics**

## Usage Examples

### Basic Usage
```bash
python main.py --material brick --resolution 1024x1024
```

### Verbose Mode
```bash
python main.py --material wood --verbose --types diffuse normal roughness
```

### Quiet Mode for Automation
```bash
python main.py --material metal --quiet --output /batch/textures/
```

### Debug Mode
```bash
python main.py --material fabric --debug --verbose
```

### No Color for Logging
```bash
python main.py --material stone --no-color > generation.log
```

## Progress Display Examples

### Overall Progress
```
Generating brick textures: 60%|██████    | 3/5 [01:23<00:55, 1.2texture/s]
```

### Individual Texture Steps
```
  → diffuse - Calling OpenAI API ⟳: 67%|██████▋   | 2/3 [00:15<00:07, 2.1step/s]
```

### API Progress
```
API: Generating diffuse texture: 00:23s
```

## Summary Report Format

```
============================================================
📊 GENERATION SUMMARY
============================================================

⏱️  Total Time: 145.32 seconds
✅ Successful: 4 textures
❌ Failed: 1 textures

📁 Generated Textures:
  ✓ diffuse: /output/brick_diffuse_1024x1024.png
  ✓ normal: /output/brick_normal_1024x1024.png
  ✓ metallic: /output/brick_metallic_1024x1024.png
  ✓ ambient_occlusion: /output/brick_ao_1024x1024.png
  ✗ roughness: API rate limit exceeded

⚠️  Warnings:
  • API rate limit approached - consider using --delay flag
  • Roughness generation failed - using fallback algorithm

============================================================
```

## Implementation Details

### Enhanced Logging Module (`src/utils/logging.py`)
- **ColoredFormatter**: ANSI color codes for terminal output
- **ProgressLogger**: Wrapper for progress tracking integration
- **Verbose/Debug modes**: Configurable detail levels
- **Summary generation**: Formatted final reports

### Progress Tracking Module (`src/utils/progress.py`)
- **ProgressTracker**: Main progress coordination class
- **StepProgressBar**: Context manager for multi-step processes
- **API Progress**: Specialized progress for external calls
- **Time Estimation**: Remaining work calculations

### Updated Main Entry (`main.py`)
- New command line arguments
- Progress tracker integration
- Conditional output based on verbosity
- Enhanced error handling with user-friendly messages

### Updated Generator (`src/core/generator.py`)
- **generate_textures_with_progress()**: Progress-enabled generation
- **_generate_diffuse_map_with_progress()**: API call progress tracking
- **_derive_pbr_maps_with_progress()**: Multi-texture derivation progress
- Integration with tqdm for real-time updates

## Benefits

1. **Better User Experience**: Clear visual feedback during long operations
2. **Debugging Support**: Detailed logging when issues occur
3. **Automation Friendly**: Quiet mode for scripted usage
4. **Professional Output**: Color-coded, formatted results
5. **Performance Insights**: Time tracking and estimation
6. **Error Visibility**: Clear indication of what succeeded/failed

## Backward Compatibility

All existing command line arguments continue to work unchanged. The new features are additive and optional.