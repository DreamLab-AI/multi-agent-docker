const WebSocket = require('ws');

const port = process.env.MCP_WS_RELAY_PORT || 3002;
const wss = new WebSocket.Server({ port });

console.log(`MCP WebSocket relay starting on port ${port}`);

wss.on('connection', ws => {
  console.log('Client connected');
  ws.on('message', message => {
    console.log(`Received message => ${message}`);
  });
  ws.send('ho!');
});