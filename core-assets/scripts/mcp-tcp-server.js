#!/usr/bin/env node

/**
 * MCP TCP/Unix Socket Server Wrapper
 * Adds TCP and Unix socket capabilities to claude-flow MCP
 * without modifying the npm package
 */

const { spawn } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');

// Configuration from environment
const TCP_PORT = process.env.MCP_TCP_PORT || 9500;
const UNIX_SOCKET = process.env.MCP_UNIX_SOCKET || '/var/run/mcp/claude-flow.sock';
const ENABLE_TCP = process.env.MCP_ENABLE_TCP !== 'false';
const ENABLE_UNIX = process.env.MCP_ENABLE_UNIX === 'true';
const LOG_LEVEL = process.env.MCP_LOG_LEVEL || 'info';

class MCPServerWrapper {
  constructor() {
    this.connections = new Map();
    this.stats = {
      totalConnections: 0,
      activeConnections: 0,
      messagesProcessed: 0,
      startTime: Date.now()
    };
  }

  log(level, message, ...args) {
    const levels = { debug: 0, info: 1, warn: 2, error: 3 };
    if (levels[level] >= levels[LOG_LEVEL]) {
      console.log(`[MCP-${level.toUpperCase()}] ${new Date().toISOString()} ${message}`, ...args);
    }
  }

  startTCPServer() {
    const server = net.createServer((socket) => {
      const clientAddr = `${socket.remoteAddress}:${socket.remotePort}`;
      this.log('info', `TCP client connected from ${clientAddr}`);
      this.stats.totalConnections++;
      this.stats.activeConnections++;
      
      // Spawn dedicated MCP instance for this connection
      const mcp = spawn('npx', ['claude-flow@alpha', 'mcp', 'start', '--stdio', '--file', '/workspace/.mcp.json'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: '/workspace',
        env: { ...process.env, CLAUDE_FLOW_DIRECT_MODE: 'true' }
      });
      
      // Store connection
      this.connections.set(clientAddr, { 
        socket, 
        mcp, 
        startTime: Date.now(),
        messagesIn: 0,
        messagesOut: 0
      });
      
      // Set up bidirectional pipe with line buffering for JSON-RPC
      let inBuffer = '';
      let outBuffer = '';
      
      // Socket -> MCP stdin
      socket.on('data', (data) => {
        inBuffer += data.toString();
        const lines = inBuffer.split('\n');
        inBuffer = lines.pop() || '';
        
        lines.forEach(line => {
          if (line.trim()) {
            this.connections.get(clientAddr).messagesIn++;
            this.stats.messagesProcessed++;
            this.log('debug', `TCP -> MCP [${clientAddr}]: ${line.substring(0, 100)}...`);
            mcp.stdin.write(line + '\n');
          }
        });
      });
      
      // MCP stdout -> Socket
      mcp.stdout.on('data', (data) => {
        outBuffer += data.toString();
        const lines = outBuffer.split('\n');
        outBuffer = lines.pop() || '';
        
        lines.forEach(line => {
          if (line.trim()) {
            this.connections.get(clientAddr).messagesOut++;
            this.log('debug', `MCP -> TCP [${clientAddr}]: ${line.substring(0, 100)}...`);
            socket.write(line + '\n');
          }
        });
      });
      
      // Error handling
      mcp.stderr.on('data', (data) => {
        this.log('error', `MCP stderr [${clientAddr}]:`, data.toString());
      });
      
      // Socket error handling
      socket.on('error', (err) => {
        this.log('error', `Socket error [${clientAddr}]:`, err.message);
        this.cleanupConnection(clientAddr);
      });
      
      // Cleanup on disconnect
      socket.on('close', () => {
        this.log('info', `TCP client ${clientAddr} disconnected`);
        this.cleanupConnection(clientAddr);
      });
      
      mcp.on('exit', (code, signal) => {
        this.log('info', `MCP process for ${clientAddr} exited (code: ${code}, signal: ${signal})`);
        socket.end();
        this.cleanupConnection(clientAddr);
      });
    });
    
    server.on('error', (err) => {
      this.log('error', 'TCP server error:', err);
      if (err.code === 'EADDRINUSE') {
        this.log('error', `Port ${TCP_PORT} is already in use`);
        process.exit(1);
      }
    });
    
    server.listen(TCP_PORT, '0.0.0.0', () => {
      this.log('info', `TCP server listening on port ${TCP_PORT}`);
    });
    
    return server;
  }

  startUnixServer() {
    // Ensure directory exists
    const socketDir = path.dirname(UNIX_SOCKET);
    if (!fs.existsSync(socketDir)) {
      fs.mkdirSync(socketDir, { recursive: true });
      this.log('info', `Created socket directory: ${socketDir}`);
    }
    
    // Remove old socket if exists
    if (fs.existsSync(UNIX_SOCKET)) {
      fs.unlinkSync(UNIX_SOCKET);
      this.log('debug', 'Removed existing socket file');
    }
    
    const server = net.createServer((socket) => {
      const connId = `unix-${Date.now()}`;
      this.log('info', `Unix socket client connected (${connId})`);
      this.stats.totalConnections++;
      this.stats.activeConnections++;
      
      // Same logic as TCP but for Unix socket
      const mcp = spawn('npx', ['claude-flow@alpha', 'mcp', 'start', '--stdio', '--file', '/workspace/.mcp.json'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: '/workspace'
      });
      
      this.connections.set(connId, { socket, mcp, startTime: Date.now() });
      
      // Bidirectional pipe
      socket.pipe(mcp.stdin);
      mcp.stdout.pipe(socket);
      
      mcp.stderr.on('data', (data) => {
        this.log('error', `MCP stderr [${connId}]:`, data.toString());
      });
      
      socket.on('close', () => {
        this.log('info', `Unix socket client ${connId} disconnected`);
        this.cleanupConnection(connId);
      });
      
      mcp.on('exit', () => {
        socket.end();
        this.cleanupConnection(connId);
      });
    });
    
    server.listen(UNIX_SOCKET, () => {
      // Make socket accessible to other containers
      fs.chmodSync(UNIX_SOCKET, '666');
      this.log('info', `Unix socket server listening at ${UNIX_SOCKET}`);
    });
    
    return server;
  }

  cleanupConnection(connId) {
    const conn = this.connections.get(connId);
    if (conn) {
      if (conn.mcp && !conn.mcp.killed) {
        conn.mcp.kill();
      }
      this.connections.delete(connId);
      this.stats.activeConnections--;
      
      const duration = Date.now() - conn.startTime;
      this.log('debug', `Connection ${connId} lasted ${duration}ms, processed ${conn.messagesIn}/${conn.messagesOut} messages`);
    }
  }

  setupHealthCheck() {
    // Simple HTTP health check endpoint
    const http = require('http');
    const healthServer = http.createServer((req, res) => {
      if (req.url === '/health') {
        const uptime = Date.now() - this.stats.startTime;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'healthy',
          uptime: uptime,
          stats: this.stats,
          tcp: ENABLE_TCP ? `listening on ${TCP_PORT}` : 'disabled',
          unix: ENABLE_UNIX ? `listening on ${UNIX_SOCKET}` : 'disabled'
        }));
      } else {
        res.writeHead(404);
        res.end();
      }
    });
    
    const healthPort = parseInt(process.env.MCP_HEALTH_PORT || '9501');
    healthServer.listen(healthPort, '127.0.0.1', () => {
      this.log('info', `Health check endpoint at http://127.0.0.1:${healthPort}/health`);
    });
  }

  start() {
    this.log('info', 'Starting MCP Server Wrapper...');
    this.log('info', `Configuration: TCP=${ENABLE_TCP}, Unix=${ENABLE_UNIX}`);
    
    const servers = [];
    
    if (ENABLE_TCP) {
      servers.push(this.startTCPServer());
    }
    
    if (ENABLE_UNIX) {
      servers.push(this.startUnixServer());
    }
    
    if (servers.length === 0) {
      this.log('error', 'No servers enabled! Set MCP_ENABLE_TCP=true or MCP_ENABLE_UNIX=true');
      process.exit(1);
    }
    
    // Setup health check
    this.setupHealthCheck();
    
    // Graceful shutdown
    const shutdown = () => {
      this.log('info', 'Shutting down servers...');
      this.connections.forEach((conn, id) => {
        this.log('debug', `Terminating connection ${id}`);
        if (conn.mcp) conn.mcp.kill();
        if (conn.socket) conn.socket.end();
      });
      
      setTimeout(() => {
        this.log('info', 'Shutdown complete');
        process.exit(0);
      }, 1000);
    };
    
    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
    
    // Status reporting
    setInterval(() => {
      this.log('debug', `Status: ${this.stats.activeConnections} active connections, ${this.stats.messagesProcessed} total messages`);
    }, 30000);
  }
}

// Auto-start if run directly
if (require.main === module) {
  const wrapper = new MCPServerWrapper();
  wrapper.start();
}

module.exports = MCPServerWrapper;