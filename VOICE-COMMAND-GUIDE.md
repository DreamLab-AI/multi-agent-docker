# Claude Flow Voice Command Interface

## Overview

The Voice Command Interface provides hands-free control of Claude Flow using natural speech commands powered by OpenAI's Whisper model. Access the web interface at `http://localhost:8001` to control jobs, spawn agents, and manage workflows using voice.

## Features

- 🎙️ **Real-time Speech Recognition** - Using OpenAI Whisper for accurate transcription
- 🔌 **WebSocket Communication** - Low-latency bidirectional communication
- 🎨 **Visual Audio Feedback** - See your voice input with real-time visualization
- 🚀 **Quick Commands** - One-click buttons for common operations
- 📊 **Job Monitoring** - Real-time status of active jobs
- 🔄 **Auto-reconnect** - Maintains connection stability

## Architecture

```
Browser (Web UI)
    ↓ WebSocket
Voice Command Server (Port 8001)
    ├── Whisper Model (Speech-to-Text)
    ├── Command Parser
    └── Claude Flow Controller
        ↓ Subprocess
    Claude Flow CLI
        ├── Job Management
        ├── Agent Spawning
        └── Workflow Control
```

## Usage

### Starting the Voice Interface

1. **Access the Web Interface:**
   ```
   http://localhost:8001
   ```

2. **Allow Microphone Access:**
   - Browser will prompt for microphone permission
   - Required for voice commands

3. **Using Voice Commands:**
   - Click the large microphone button
   - Speak your command clearly
   - Button turns red while recording
   - Release to process command

### Voice Commands

#### Job Control
- **Start:** "Start a new blender job"
- **Stop:** "Stop the current job"
- **Pause:** "Pause execution"
- **Resume:** "Resume the paused job"
- **Status:** "What's the status?"

#### Agent Management
- **Spawn:** "Spawn 5 agents"
- **Orchestrate:** "Orchestrate a rendering task"

#### MCP Testing
- **Test All:** "Test all MCP servers"
- **Test Specific:** "Test blender connection"

#### Workflow
- **Create:** "Create a new workflow called animation pipeline"
- **Run:** "Run the animation pipeline workflow"

### Quick Command Buttons

The interface includes quick-access buttons for common commands:
- 📊 Status - Check system status
- 🚀 Start Blender - Launch Blender job
- 🤖 Spawn Agents - Create 5 agents
- 🔌 Test MCP - Test all connections
- ⏸️ Pause - Pause active job
- ▶️ Resume - Resume paused job
- ⏹️ Stop - Stop active job
- 📋 New Workflow - Create workflow

## Technical Details

### WebSocket Protocol

Messages follow this format:

**Audio Message (Client → Server):**
```json
{
  "type": "audio",
  "audio": [float32 array],
  "sampleRate": 16000
}
```

**Command Result (Server → Client):**
```json
{
  "type": "command_result",
  "success": true,
  "command": "start",
  "result": {
    "job_id": "job_20240118_123456",
    "message": "Started blender job"
  },
  "timestamp": "2024-01-18T12:34:56Z"
}
```

### Adding Custom Commands

To add new voice commands, edit the `ClaudeFlowController` class in `voice-command-server.py`:

```python
def __init__(self):
    self.command_map = {
        # Add your command here
        "my_command": self.my_command_handler,
    }

async def my_command_handler(self, text: str) -> Dict[str, Any]:
    # Implement command logic
    cmd = ["npx", "claude-flow@alpha", "my-command"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"message": "Command executed", "output": result.stdout}
```

### Whisper Model Configuration

The server uses Whisper "base" model by default. To change:

```python
# In voice-command-server.py
model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
```

Model trade-offs:
- **tiny**: Fastest, least accurate
- **base**: Good balance (default)
- **small**: Better accuracy, slower
- **medium**: High accuracy, much slower
- **large**: Best accuracy, requires GPU

## Troubleshooting

### Connection Issues
- Ensure voice server is running: `docker exec -it blender-mcp-container voice-log`
- Check logs: `docker logs blender-mcp-container | grep voice`
- Verify port 8001 is accessible

### Microphone Issues
- Check browser permissions
- Ensure no other application is using microphone
- Try different browser (Chrome recommended)

### Recognition Issues
- Speak clearly and avoid background noise
- Wait for visual feedback before speaking
- Check Whisper model is loaded in logs

### Performance
- First command may be slow (model loading)
- Consider using smaller Whisper model on CPU
- GPU acceleration improves response time

## Security Notes

1. **Microphone Access**: Only granted to localhost by default
2. **Command Validation**: All commands are validated before execution
3. **WebSocket Security**: Consider adding authentication for production
4. **Process Isolation**: Commands run in subprocess with limited scope

## Future Enhancements

- [ ] Voice feedback/TTS responses
- [ ] Multi-language support
- [ ] Custom wake word detection
- [ ] Voice command macros
- [ ] Integration with 3D viewports
- [ ] Real-time transcription display

## Example Workflow

1. **Start a complex rendering job with voice:**
   - "Start a new blender job"
   - "Spawn 8 agents"
   - "Orchestrate scene rendering with global illumination"

2. **Monitor and control:**
   - "What's the status?"
   - "Pause the job" (to check intermediate results)
   - "Resume execution"

3. **Complete workflow:**
   - "Create workflow called final render"
   - "Stop current job"
   - "Run workflow final render"

The voice interface makes it easy to control complex 3D workflows without switching context from your creative work!