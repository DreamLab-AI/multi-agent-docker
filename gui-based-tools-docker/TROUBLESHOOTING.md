# MCP Docker Networking Troubleshooting Guide

This guide helps diagnose and fix common issues with MCP (Model Context Protocol) networking between containers.

## Common Issues and Solutions

### 1. Connection Refused Error

**Symptoms:**
```
Error connecting to Blender server at blender_desktop:9876: Error: connect ECONNREFUSED
```

**Diagnosis:**
```bash
# Check if container is running
docker ps | grep blender_desktop

# Test port connectivity
nc -zv blender_desktop 9876
```

**Solutions:**
1. Start the Blender container:
   ```bash
   cd /workspace/blender-docker
   docker-compose up -d
   ```

2. Verify MCP service is running inside container:
   ```bash
   docker exec blender_desktop ps aux | grep -E "(blender|mcp)"
   ```

3. Check container logs for errors:
   ```bash
   docker logs blender_desktop --tail 50
   ```

### 2. Network Unreachable

**Symptoms:**
```
Network is unreachable
Cannot resolve hostname 'blender_desktop'
```

**Diagnosis:**
```bash
# Check container networks
docker inspect $(hostname) | grep -A 10 Networks

# Check if on correct network
docker network inspect docker_ragflow | grep $(hostname)
```

**Solutions:**
1. Connect to the correct network:
   ```bash
   # From host machine
   docker network connect docker_ragflow $(docker ps -q -f name=multi-agent)
   ```

2. Verify network connectivity:
   ```bash
   # Inside container
   ip addr show
   ping -c 1 blender_desktop
   ```

### 3. Environment Variables Not Set

**Symptoms:**
```
Trying to connect to localhost:9876 instead of blender_desktop:9876
```

**Diagnosis:**
```bash
# Check current environment
env | grep -E "(BLENDER|QGIS)_(HOST|PORT)"
```

**Solutions:**
1. Set environment variables:
   ```bash
   source /workspace/blender-docker/setup-mcp-env.sh
   ```

2. Export manually:
   ```bash
   export BLENDER_HOST=blender_desktop
   export BLENDER_PORT=9876
   export QGIS_HOST=blender_desktop
   export QGIS_PORT=9877
   ```

3. Add to shell profile:
   ```bash
   echo "source /workspace/blender-docker/setup-mcp-env.sh" >> ~/.bashrc
   ```

### 4. MCP Bridge Script Failures

**Symptoms:**
```
MCP server 'blender-mcp' failed to start
Error in Blender bridge: <error message>
```

**Diagnosis:**
```bash
# Test bridge script directly
node /workspace/scripts/mcp-blender-client.js

# Check script permissions
ls -la /workspace/scripts/mcp-blender-client.js
```

**Solutions:**
1. Check Node.js is installed:
   ```bash
   node --version
   npm --version
   ```

2. Verify script syntax:
   ```bash
   node -c /workspace/scripts/mcp-blender-client.js
   ```

3. Test manual connection:
   ```bash
   echo '{"type":"ping","params":{}}' | nc blender_desktop 9876
   ```

### 5. Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Diagnosis:**
```bash
# Check what's using the port
lsof -i :9876
netstat -tlnp | grep 9876
```

**Solutions:**
1. Stop conflicting service:
   ```bash
   # Find and stop the process
   sudo kill $(lsof -t -i:9876)
   ```

2. Use different port:
   ```bash
   # Update environment
   export BLENDER_PORT=9878
   
   # Update docker-compose.yml port mapping
   ```

### 6. DNS Resolution Issues

**Symptoms:**
```
getaddrinfo ENOTFOUND blender_desktop
```

**Diagnosis:**
```bash
# Check DNS resolution
nslookup blender_desktop
cat /etc/resolv.conf
```

**Solutions:**
1. Use IP address instead:
   ```bash
   # Find container IP
   docker inspect blender_desktop | grep IPAddress
   
   # Use IP directly
   export BLENDER_HOST=172.18.0.9
   ```

2. Add hosts entry:
   ```bash
   sudo /workspace/blender-docker/configure-hosts.sh
   ```

3. Use Docker's internal DNS:
   ```bash
   # Ensure containers are on same network
   docker network connect docker_ragflow both_containers
   ```

### 7. Timeout Issues

**Symptoms:**
```
Response timeout from Blender
Socket timeout while communicating
```

**Diagnosis:**
```bash
# Check network latency
ping -c 5 blender_desktop

# Monitor MCP traffic
tcpdump -i any -n port 9876
```

**Solutions:**
1. Increase timeout values in bridge scripts
2. Check container resource limits:
   ```bash
   docker stats blender_desktop
   ```
3. Reduce network latency by ensuring containers are on same host

## Diagnostic Commands

### Full System Check
```bash
# Run comprehensive test
/workspace/blender-docker/test-mcp-connectivity.sh
```

### Quick Health Check
```bash
# Check all MCP services
/workspace/blender-docker/health-check-mcp.sh
```

### Network Debugging
```bash
# Show all networks
docker network ls

# Inspect specific network
docker network inspect docker_ragflow

# Show container networks
docker inspect $(hostname) | jq '.[0].NetworkSettings.Networks'
```

### Process Debugging
```bash
# Check running processes in container
docker exec blender_desktop ps aux

# Check listening ports
docker exec blender_desktop netstat -tlnp
```

## Advanced Debugging

### 1. Enable Debug Logging

Add to bridge scripts:
```javascript
// In mcp-blender-client.js
const DEBUG = process.env.DEBUG === 'true';
if (DEBUG) console.error('Debug: Connecting to', BLENDER_HOST, BLENDER_PORT);
```

Run with debug:
```bash
DEBUG=true node /workspace/scripts/mcp-blender-client.js
```

### 2. Packet Capture

```bash
# Capture MCP traffic
sudo tcpdump -i any -w mcp-traffic.pcap port 9876 or port 9877

# Analyze with Wireshark
wireshark mcp-traffic.pcap
```

### 3. Strace Debugging

```bash
# Trace system calls
strace -f -e network node /workspace/scripts/mcp-blender-client.js
```

## Prevention Tips

1. **Always use docker-compose**: Ensures consistent network setup
2. **Set environment variables early**: Source setup script in .bashrc
3. **Use health checks**: Detect issues before they impact usage
4. **Monitor logs**: Set up log aggregation for early warning
5. **Document changes**: Keep track of network modifications

## Getting Help

If issues persist:

1. Collect diagnostic information:
   ```bash
   /workspace/blender-docker/test-mcp-connectivity.sh > diagnostic.log 2>&1
   docker ps >> diagnostic.log
   docker network ls >> diagnostic.log
   env | grep -E "(BLENDER|QGIS)" >> diagnostic.log
   ```

2. Check container logs:
   ```bash
   docker logs blender_desktop --tail 100 > blender.log
   docker logs $(hostname) --tail 100 > agent.log
   ```

3. Review the MCP integration report at `/workspace/mcp-integration-report.md`

4. Consult the main networking documentation at `/workspace/blender-docker/NETWORKING-SETUP.md`