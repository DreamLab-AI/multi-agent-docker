#!/usr/bin/env node

const WebSocket = require('ws');
const { spawn } = require('child_process');

const PORT = process.env.MCP_BRIDGE_PORT || 3002;
const HOST = '0.0.0.0'; // Listen on all network interfaces

const wss = new WebSocket.Server({ host: HOST, port: PORT });

console.log(`[MCP Bridge] WebSocket-to-Stdio bridge listening on ws://${HOST}:${PORT}`);

wss.on('connection', (ws, req) => {
    const clientIp = req.socket.remoteAddress;
    console.log(`[MCP Bridge] New client connected from ${clientIp}`);

    // For each new WebSocket connection, spawn a dedicated claude-flow MCP process.
    // This provides perfect session isolation.
    const mcpProcess = spawn('npx', ['claude-flow@alpha', 'mcp', 'start', '--stdio'], {
        cwd: '/workspace', // Run in the context of the user's workspace
        stdio: ['pipe', 'pipe', 'pipe'] // stdin, stdout, stderr
    });

    console.log(`[MCP Bridge] Spawned claude-flow MCP process with PID: ${mcpProcess.pid}`);

    // Pipe data from the claude-flow process's stdout to the WebSocket client
    mcpProcess.stdout.on('data', (data) => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(data.toString());
        }
    });

    // Log any errors from the claude-flow process
    mcpProcess.stderr.on('data', (data) => {
        console.error(`[MCP Process Stderr - PID ${mcpProcess.pid}] ${data.toString()}`);
    });

    // Pipe messages from the WebSocket client to the claude-flow process's stdin
    ws.on('message', (message) => {
        try {
            // claude-flow expects newline-delimited JSON
            mcpProcess.stdin.write(message.toString() + '\n');
        } catch (error) {
            console.error('[MCP Bridge] Error writing to MCP process stdin:', error);
        }
    });

    // Handle connection termination
    ws.on('close', (code, reason) => {
        console.log(`[MCP Bridge] Client from ${clientIp} disconnected. Code: ${code}. Terminating MCP process.`);
        mcpProcess.kill('SIGTERM');
    });

    ws.on('error', (error) => {
        console.error(`[MCP Bridge] WebSocket error from ${clientIp}:`, error);
        mcpProcess.kill('SIGTERM');
    });

    mcpProcess.on('exit', (code, signal) => {
        console.log(`[MCP Bridge] MCP process PID ${mcpProcess.pid} exited with code ${code}, signal ${signal}`);
        if (ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });
});

console.log('[MCP Bridge] Ready to accept external connections.');