#!/usr/bin/env node

// WebSocket to MCP Bridge
// Uses global claude-flow installation instead of npx

const WebSocket = require('ws');
const { spawn } = require('child_process');

const PORT = process.env.MCP_BRIDGE_PORT || 3002;
const HOST = '0.0.0.0'; // Listen on all network interfaces

const wss = new WebSocket.Server({ host: HOST, port: PORT });

console.log(`[MCP Bridge] WebSocket-to-Stdio bridge listening on ws://${HOST}:${PORT}`);
console.log(`[MCP Bridge] Using global claude-flow installation at /usr/bin/claude-flow`);

wss.on('connection', (ws, req) => {
    const clientIp = req.socket.remoteAddress;
    console.log(`[MCP Bridge] New client connected from ${clientIp}`);

    // For each new WebSocket connection, spawn a dedicated claude-flow MCP process.
    // This provides perfect session isolation using global installation.
    const mcpProcess = spawn('/usr/bin/claude-flow', ['mcp', 'start', '--stdio', '--file', '/workspace/.mcp.json'], {
        cwd: '/workspace', // Run in the context of the user's workspace
        stdio: ['pipe', 'pipe', 'pipe'], // stdin, stdout, stderr
        env: {
            ...process.env,
            CLAUDE_FLOW_DIRECT_MODE: 'true',
            CLAUDE_FLOW_GLOBAL: 'true',
            CLAUDE_FLOW_DATABASE: '/workspace/.swarm/memory.db'
        }
    });

    console.log(`[MCP Bridge] Spawned claude-flow MCP process with PID: ${mcpProcess.pid}`);

    // Pipe data from the claude-flow process's stdout to the WebSocket client
    mcpProcess.stdout.on('data', (data) => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(data.toString());
        }
    });

    // Pipe data from the WebSocket client to the claude-flow process's stdin
    ws.on('message', (message) => {
        mcpProcess.stdin.write(message + '\n');
    });

    // Handle WebSocket close event
    ws.on('close', () => {
        console.log(`[MCP Bridge] Client disconnected from ${clientIp}`);
        mcpProcess.kill();
    });

    // Handle claude-flow process exit
    mcpProcess.on('close', (code) => {
        console.log(`[MCP Bridge] claude-flow process exited with code ${code}`);
        if (ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });

    // Handle errors from the claude-flow process
    mcpProcess.stderr.on('data', (data) => {
        console.error(`[MCP Bridge] claude-flow stderr: ${data}`);
    });

    // Handle errors from the WebSocket
    ws.on('error', (error) => {
        console.error(`[MCP Bridge] WebSocket error: ${error.message}`);
        mcpProcess.kill();
    });
});

// Health check endpoint
const http = require('http');
const healthPort = parseInt(process.env.MCP_WS_HEALTH_PORT || '3003');

const healthServer = http.createServer((req, res) => {
    if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            connections: wss.clients.size,
            port: PORT,
            uptime: process.uptime()
        }));
    } else {
        res.writeHead(404);
        res.end();
    }
});

healthServer.listen(healthPort, '127.0.0.1', () => {
    console.log(`[MCP Bridge] Health check endpoint at http://127.0.0.1:${healthPort}/health`);
});

// Handle server errors
wss.on('error', (error) => {
    console.error(`[MCP Bridge] Server error: ${error.message}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log(`[MCP Bridge] Shutting down...`);
    wss.close(() => {
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log(`[MCP Bridge] Shutting down...`);
    wss.close(() => {
        process.exit(0);
    });
});