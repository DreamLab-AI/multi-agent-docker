#!/usr/bin/env python3
"""
Voice Command Server for Claude Flow
Provides WebSocket-based voice control using OpenAI Whisper
"""

import asyncio
import json
import logging
import os
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import websockets
import whisper
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import soundfile as sf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Claude Flow Voice Commander")

# Load Whisper model (using base model for balance of speed/accuracy)
logger.info("Loading Whisper model...")
model = whisper.load_model("base")
logger.info("Whisper model loaded successfully")

# Store active connections and job states
connections: Dict[str, WebSocket] = {}
active_jobs: Dict[str, Dict[str, Any]] = {}

class ClaudeFlowController:
    """Controller for Claude Flow operations"""
    
    def __init__(self):
        self.command_map = {
            # Job control commands
            "start": self.start_job,
            "stop": self.stop_job,
            "pause": self.pause_job,
            "resume": self.resume_job,
            "status": self.get_status,
            
            # Swarm commands
            "spawn": self.spawn_agents,
            "orchestrate": self.orchestrate_task,
            
            # MCP commands
            "test blender": self.test_blender_mcp,
            "test revit": self.test_revit_mcp,
            "test unreal": self.test_unreal_mcp,
            
            # Workflow commands
            "create workflow": self.create_workflow,
            "run workflow": self.run_workflow,
        }
    
    async def process_command(self, text: str) -> Dict[str, Any]:
        """Process voice command text and execute appropriate action"""
        text_lower = text.lower().strip()
        logger.info(f"Processing command: {text}")
        
        # Find matching command
        for cmd_key, cmd_func in self.command_map.items():
            if cmd_key in text_lower:
                try:
                    result = await cmd_func(text_lower)
                    return {
                        "success": True,
                        "command": cmd_key,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"Error executing command {cmd_key}: {e}")
                    return {
                        "success": False,
                        "command": cmd_key,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
        
        # No matching command found
        return {
            "success": False,
            "error": f"Unknown command: {text}",
            "suggestions": list(self.command_map.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def start_job(self, text: str) -> Dict[str, Any]:
        """Start a new Claude Flow job"""
        # Extract job type from command
        job_type = "default"
        if "blender" in text:
            job_type = "blender"
        elif "revit" in text:
            job_type = "revit"
        elif "unreal" in text:
            job_type = "unreal"
        
        # Execute Claude Flow command
        cmd = ["npx", "claude-flow@alpha", "start", "--type", job_type]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        active_jobs[job_id] = {
            "id": job_id,
            "type": job_type,
            "status": "running",
            "started": datetime.now().isoformat(),
            "output": result.stdout
        }
        
        return {
            "job_id": job_id,
            "message": f"Started {job_type} job",
            "output": result.stdout
        }
    
    async def stop_job(self, text: str) -> Dict[str, Any]:
        """Stop a running job"""
        # Get the most recent job if no ID specified
        if active_jobs:
            job_id = list(active_jobs.keys())[-1]
            job = active_jobs[job_id]
            job["status"] = "stopped"
            
            # Execute stop command
            cmd = ["npx", "claude-flow@alpha", "stop", "--job-id", job_id]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                "job_id": job_id,
                "message": f"Stopped job {job_id}",
                "output": result.stdout
            }
        
        return {"message": "No active jobs to stop"}
    
    async def pause_job(self, text: str) -> Dict[str, Any]:
        """Pause a running job"""
        if active_jobs:
            job_id = list(active_jobs.keys())[-1]
            active_jobs[job_id]["status"] = "paused"
            
            cmd = ["npx", "claude-flow@alpha", "pause", "--job-id", job_id]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                "job_id": job_id,
                "message": f"Paused job {job_id}",
                "output": result.stdout
            }
        
        return {"message": "No active jobs to pause"}
    
    async def resume_job(self, text: str) -> Dict[str, Any]:
        """Resume a paused job"""
        # Find paused jobs
        paused_jobs = [j for j in active_jobs.values() if j["status"] == "paused"]
        if paused_jobs:
            job = paused_jobs[-1]
            job["status"] = "running"
            
            cmd = ["npx", "claude-flow@alpha", "resume", "--job-id", job["id"]]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                "job_id": job["id"],
                "message": f"Resumed job {job['id']}",
                "output": result.stdout
            }
        
        return {"message": "No paused jobs to resume"}
    
    async def get_status(self, text: str) -> Dict[str, Any]:
        """Get status of all jobs"""
        cmd = ["npx", "claude-flow@alpha", "status", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            status_data = json.loads(result.stdout)
        except:
            status_data = {"raw": result.stdout}
        
        return {
            "active_jobs": len(active_jobs),
            "jobs": list(active_jobs.values()),
            "claude_flow_status": status_data
        }
    
    async def spawn_agents(self, text: str) -> Dict[str, Any]:
        """Spawn Claude Flow agents"""
        # Extract agent count
        count = 3  # default
        for word in text.split():
            if word.isdigit():
                count = int(word)
                break
        
        cmd = ["npx", "claude-flow@alpha", "agent", "spawn", "--count", str(count)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "message": f"Spawning {count} agents",
            "output": result.stdout
        }
    
    async def orchestrate_task(self, text: str) -> Dict[str, Any]:
        """Orchestrate a task with Claude Flow"""
        # Extract task description (everything after "orchestrate")
        task_desc = text.split("orchestrate", 1)[-1].strip()
        
        cmd = ["npx", "claude-flow@alpha", "task", "orchestrate", "--description", task_desc]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "task": task_desc,
            "message": "Task orchestrated",
            "output": result.stdout
        }
    
    async def test_blender_mcp(self, text: str) -> Dict[str, Any]:
        """Test Blender MCP connection"""
        result = subprocess.run(["nc", "-zv", "localhost", "9876"], 
                              capture_output=True, text=True)
        
        return {
            "service": "Blender MCP",
            "port": 9876,
            "status": "connected" if result.returncode == 0 else "disconnected",
            "output": result.stderr  # nc outputs to stderr
        }
    
    async def test_revit_mcp(self, text: str) -> Dict[str, Any]:
        """Test Revit MCP connection"""
        result = subprocess.run(["nc", "-zv", "localhost", "8080"], 
                              capture_output=True, text=True)
        
        return {
            "service": "Revit MCP",
            "port": 8080,
            "status": "connected" if result.returncode == 0 else "disconnected",
            "output": result.stderr
        }
    
    async def test_unreal_mcp(self, text: str) -> Dict[str, Any]:
        """Test Unreal MCP connection"""
        result = subprocess.run(["nc", "-zv", "localhost", "55557"], 
                              capture_output=True, text=True)
        
        return {
            "service": "Unreal MCP",
            "port": 55557,
            "status": "connected" if result.returncode == 0 else "disconnected",
            "output": result.stderr
        }
    
    async def create_workflow(self, text: str) -> Dict[str, Any]:
        """Create a new workflow"""
        # Extract workflow name
        name = text.split("workflow", 1)[-1].strip()
        if not name:
            name = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cmd = ["npx", "claude-flow@alpha", "workflow", "create", "--name", name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "workflow_name": name,
            "message": f"Created workflow: {name}",
            "output": result.stdout
        }
    
    async def run_workflow(self, text: str) -> Dict[str, Any]:
        """Run a workflow"""
        # Extract workflow name or use latest
        name = text.split("workflow", 1)[-1].strip()
        
        cmd = ["npx", "claude-flow@alpha", "workflow", "run"]
        if name:
            cmd.extend(["--name", name])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "workflow": name or "latest",
            "message": "Workflow started",
            "output": result.stdout
        }

# Initialize controller
controller = ClaudeFlowController()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice commands"""
    await websocket.accept()
    client_id = f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    connections[client_id] = websocket
    
    try:
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "message": "Voice command server ready"
        })
        
        while True:
            # Receive audio data
            data = await websocket.receive_json()
            
            if data["type"] == "audio":
                # Process audio with Whisper
                audio_data = np.array(data["audio"], dtype=np.float32)
                
                # Save to temporary file (Whisper requires file input)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    sf.write(tmp_file.name, audio_data, data.get("sampleRate", 16000))
                    
                    # Transcribe with Whisper
                    result = model.transcribe(tmp_file.name)
                    text = result["text"]
                    
                    # Clean up temp file
                    os.unlink(tmp_file.name)
                
                # Send transcription back
                await websocket.send_json({
                    "type": "transcription",
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Process command
                command_result = await controller.process_command(text)
                
                # Send command result
                await websocket.send_json({
                    "type": "command_result",
                    **command_result
                })
            
            elif data["type"] == "command":
                # Direct text command (for testing)
                command_result = await controller.process_command(data["text"])
                await websocket.send_json({
                    "type": "command_result",
                    **command_result
                })
            
            elif data["type"] == "ping":
                # Keepalive
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if client_id in connections:
            del connections[client_id]

# Serve static files
app.mount("/static", StaticFiles(directory="/app/voice-ui"), name="static")

@app.get("/")
async def get_index():
    """Serve the main web interface"""
    return HTMLResponse(content=open("/app/voice-ui/index.html").read())

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    Path("/app/voice-ui").mkdir(parents=True, exist_ok=True)
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )