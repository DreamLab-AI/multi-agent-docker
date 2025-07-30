#!/bin/bash
set -e  # Exit on any error

echo "--- Setting up environment ---"
export DISPLAY=:1
export MCP_HOST=${MCP_HOST:-0.0.0.0}
echo "DISPLAY=$DISPLAY"
echo "MCP_HOST=$MCP_HOST"

echo "--- Starting virtual framebuffer ---"
Xvfb :1 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 3

echo "--- Checking if Xvfb started ---"
if ps -p $XVFB_PID > /dev/null; then
    echo "Xvfb started successfully (PID: $XVFB_PID)"
else
    echo "ERROR: Xvfb failed to start"
    exit 1
fi

echo "--- Starting XFCE desktop ---"
startxfce4 &
sleep 3

echo "--- Starting Blender ---"
/home/blender/blender-4.5/blender --python /home/blender/autostart.py &
sleep 3

echo "--- Starting QGIS ---"
qgis &
sleep 3

echo "--- Starting PBR Generator MCP Server ---"
python3 /opt/tessellating-pbr-generator/pbr_mcp_server.py &
sleep 3

echo "--- Starting x11vnc ---"
x11vnc -display :1 -nopw -forever -xkb -listen 0.0.0.0 -rfbport 5901 -verbose &
VNC_PID=$!
sleep 5

echo "--- Checking if x11vnc started ---"
if ps -p $VNC_PID > /dev/null; then
    echo "x11vnc started successfully (PID: $VNC_PID)"
else
    echo "ERROR: x11vnc failed to start"
    exit 1
fi

echo "--- Checking all processes ---"
ps aux | grep -E "(Xvfb|startxfce4|blender|qgis|x11vnc)" | grep -v grep

echo "--- Checking network listeners ---"
netstat -tuln

echo "--- Startup complete, container is running ---"
sleep infinity