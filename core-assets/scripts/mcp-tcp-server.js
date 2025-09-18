#!/usr/bin/env node

// Persistent MCP TCP Server - Fixes agent tracking
// Maintains single MCP instance across all connections

const { spawn } = require('child_process');
const net = require('net');
const readline = require('readline');

const TCP_PORT = process.env.MCP_TCP_PORT || 9500;
const LOG_LEVEL = process.env.MCP_LOG_LEVEL || 'info';

class PersistentMCPServer {
  constructor() {
    this.mcpProcess = null;
    this.mcpInterface = null;
    this.clients = new Map();
    this.initialized = false;
    this.initPromise = null;
  }

  log(level, message, ...args) {
    const levels = { debug: 0, info: 1, warn: 2, error: 3 };
    if (levels[level] >= levels[LOG_LEVEL]) {
      console.log(`[PMCP-${level.toUpperCase()}] ${new Date().toISOString()} ${message}`, ...args);
    }
  }

  async startMCPProcess() {
    if (this.mcpProcess) return;

    this.log('info', 'Starting persistent MCP process...');
    this.mcpProcess = spawn('/usr/bin/claude-flow', ['mcp', 'start', '--stdio'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: '/workspace',
      env: {
          CLAUDE_FLOW_GLOBAL: '/usr/bin/claude-flow', ...process.env, CLAUDE_FLOW_DIRECT_MODE: 'true' }
    });

    this.mcpInterface = readline.createInterface({
      input: this.mcpProcess.stdout,
      crlfDelay: Infinity
    });

    this.mcpInterface.on('line', (line) => this.handleMCPOutput(line));
    this.mcpProcess.stderr.on('data', (data) => this.log('debug', `MCP: ${data}`));
    this.mcpProcess.on('close', (code) => {
      this.log('error', `MCP exited: ${code}`);
      this.mcpProcess = null;
      this.initialized = false;
      setTimeout(() => this.startMCPProcess(), 5000);
    });

    await this.initializeMCP();
  }

  async initializeMCP() {
    if (this.initialized) return;
    const initRequest = {
      jsonrpc: "2.0",
      id: "init-" + Date.now(),
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: { listChanged: true }},
        clientInfo: { name: "tcp-wrapper", version: "1.0.0" }
      }
    };
    return new Promise((resolve) => {
      this.initPromise = { resolve, id: initRequest.id };
      this.mcpProcess.stdin.write(JSON.stringify(initRequest) + '\n');
    });
  }

  handleMCPOutput(line) {
    if (!line.startsWith('{')) return;
    try {
      const msg = JSON.parse(line);
      if (this.initPromise && msg.id === this.initPromise.id) {
        this.initialized = true;
        this.log('info', 'MCP initialized');
        this.initPromise.resolve();
        this.initPromise = null;
        return;
      }
      if (!msg.id) {
        this.broadcastToClients(line);
        return;
      }
      const clientId = this.findClientByRequestId(msg.id);
      if (clientId) {
        const client = this.clients.get(clientId);
        if (client && client.socket) {
          client.socket.write(line + '\n');
        }
      }
    } catch (err) {
      this.log('error', `Parse error: ${err.message}`);
    }
  }

  findClientByRequestId(requestId) {
    for (const [clientId, client] of this.clients) {
      if (client.pendingRequests && client.pendingRequests.has(requestId)) {
        client.pendingRequests.delete(requestId);
        return clientId;
      }
    }
    return null;
  }

  broadcastToClients(message) {
    for (const [clientId, client] of this.clients) {
      if (client.socket && !client.socket.destroyed) {
        client.socket.write(message + '\n');
      }
    }
  }

  async handleClient(socket) {
    const clientId = `${socket.remoteAddress}:${socket.remotePort}-${Date.now()}`;
    this.log('info', `Client connected: ${clientId}`);

    if (!this.initialized) {
      let waitCount = 0;
      while (!this.initialized && waitCount < 20) {
        await new Promise(resolve => setTimeout(resolve, 100));
        waitCount++;
      }
      if (!this.initialized) {
        socket.write('{"error":"MCP not ready"}\n');
        socket.end();
        return;
      }
    }

    this.clients.set(clientId, {
      socket,
      pendingRequests: new Set(),
      buffer: ''
    });

    socket.on('data', (data) => {
      const client = this.clients.get(clientId);
      if (!client) return;
      client.buffer += data.toString();
      const lines = client.buffer.split('\n');
      client.buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.trim()) this.handleClientRequest(clientId, line);
      }
    });

    socket.on('close', () => {
      this.log('info', `Client disconnected: ${clientId}`);
      this.clients.delete(clientId);
    });

    socket.on('error', (err) => {
      this.log('error', `Client error: ${err.message}`);
      this.clients.delete(clientId);
    });
  }

  handleClientRequest(clientId, requestStr) {
    try {
      const request = JSON.parse(requestStr);
      const client = this.clients.get(clientId);
      if (!client) return;

      if (request.method === 'initialize') {
        client.socket.write(JSON.stringify({
          jsonrpc: "2.0",
          id: request.id,
          result: {
            protocolVersion: "2024-11-05",
            serverInfo: { name: "claude-flow", version: "2.0.0-alpha.101" }
          }
        }) + '\n');
        return;
      }

      if (request.id) {
        client.pendingRequests.add(request.id);
      }
      this.mcpProcess.stdin.write(requestStr + '\n');
      this.log('debug', `Forwarded: ${request.id}`);
    } catch (err) {
      this.log('error', `Invalid request: ${err.message}`);
    }
  }

  async start() {
    await this.startMCPProcess();
    const server = net.createServer((socket) => this.handleClient(socket));
    server.listen(TCP_PORT, '0.0.0.0', () => {
      this.log('info', `Persistent MCP TCP server on port ${TCP_PORT}`);
    });
    server.on('error', (err) => {
      this.log('error', `Server error: ${err.message}`);
      if (err.code === 'EADDRINUSE') process.exit(1);
    });
  }
}

const server = new PersistentMCPServer();
server.start().catch(err => {
  console.error('Failed to start:', err);
  process.exit(1);
});

process.on('SIGINT', () => {
  if (server.mcpProcess) server.mcpProcess.kill();
  process.exit(0);
});
