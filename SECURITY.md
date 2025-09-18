# Security Guide for Multi-Agent Docker Environment

## Overview

This document outlines the security features integrated into the multi-agent Docker environment, including authentication, rate limiting, connection management, and secure communication protocols.

## Security Features Implemented

### 1. Authentication & Authorization

#### WebSocket Authentication
- **Token-based authentication** for WebSocket connections
- **Bearer token validation** in Authorization header
- **Configurable authentication** via `WS_AUTH_ENABLED` environment variable

#### TCP Authentication
- **Custom authentication protocol** for TCP connections
- **Secure token exchange** during connection establishment
- **Session-based authentication** with timeout management

#### JWT Support
- **JWT token generation** and validation
- **Configurable JWT secrets** for token signing
- **Secure token refresh** mechanisms

### 2. Rate Limiting & DDoS Protection

#### Connection Rate Limiting
- **Per-client rate limiting** with configurable windows
- **Burst request handling** with separate limits
- **Automatic IP blocking** for abuse prevention
- **Sliding window algorithm** for accurate rate limiting

#### Connection Limits
- **Maximum concurrent connections** for WebSocket and TCP
- **Per-IP connection limits** to prevent resource exhaustion
- **Connection timeout management** with automatic cleanup

### 3. Input Validation & Sanitization

#### Message Validation
- **JSON-RPC protocol validation** for all messages
- **Message size limits** to prevent memory exhaustion
- **Buffer overflow protection** with configurable limits
- **Content sanitization** to prevent injection attacks

#### Security Filters
- **Script injection prevention** with HTML/JavaScript filtering
- **Prototype pollution protection** for object validation
- **Path traversal prevention** for file operations
- **SQL injection protection** for database queries

### 4. Network Security

#### CORS Protection
- **Configurable CORS policies** with origin validation
- **Secure headers** for cross-origin requests
- **Method and header restrictions** for API endpoints
- **Preflight request handling** for complex requests

#### SSL/TLS Support
- **Configurable SSL encryption** for production deployments
- **Certificate management** with custom CA support
- **Protocol version enforcement** for secure connections
- **Cipher suite configuration** for optimal security

### 5. Monitoring & Auditing

#### Security Logging
- **Comprehensive audit trails** for all security events
- **Real-time threat detection** with automated blocking
- **Performance monitoring** with metrics collection
- **Health check endpoints** for service status

#### Circuit Breaker Pattern
- **Automatic failure detection** with configurable thresholds
- **Service degradation protection** with fallback mechanisms
- **Recovery monitoring** with automatic circuit reset
- **Cascade failure prevention** for dependent services

## Configuration

### Environment Variables

All security features are configured through environment variables defined in `.env`:

```bash
# Authentication
WS_AUTH_ENABLED=true
WS_AUTH_TOKEN=your-secure-websocket-token
TCP_AUTH_TOKEN=your-secure-tcp-token
JWT_SECRET=your-jwt-secret-minimum-32-chars

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Connection Limits
WS_MAX_CONNECTIONS=100
TCP_MAX_CONNECTIONS=50
WS_CONNECTION_TIMEOUT=300000

# Security Headers
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=https://yourdomain.com
SSL_ENABLED=false
```

### Default Security Settings

The system includes secure defaults for development and production:

| Feature | Development | Production |
|---------|------------|------------|
| Authentication | Enabled | Enabled |
| Rate Limiting | Permissive | Strict |
| SSL/TLS | Disabled | Enabled |
| Debug Logging | Enabled | Disabled |
| CORS | Permissive | Restrictive |

## Deployment Security

### Pre-deployment Checklist

- [ ] **Change all default tokens and secrets**
- [ ] **Enable SSL/TLS for production**
- [ ] **Configure restrictive CORS policies**
- [ ] **Set appropriate rate limits**
- [ ] **Enable security audit logging**
- [ ] **Configure firewall rules**
- [ ] **Set up monitoring and alerting**

### Production Security Hardening

#### 1. Token Management
```bash
# Generate secure tokens
WS_AUTH_TOKEN=$(openssl rand -hex 32)
TCP_AUTH_TOKEN=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 64)
```

#### 2. SSL Certificate Setup
```bash
# Generate self-signed certificates (for testing)
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes

# Or use Let's Encrypt for production
certbot certonly --standalone -d yourdomain.com
```

#### 3. Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 443   # HTTPS
ufw allow 3002  # WebSocket (if external access needed)
ufw allow 9500  # TCP MCP (if external access needed)
ufw enable
```

### Monitoring Setup

#### 1. Log Monitoring
```bash
# Monitor security events
tail -f /app/mcp-logs/security/*.log | grep SECURITY

# Set up log rotation
logrotate -f /etc/logrotate.d/mcp-security
```

#### 2. Health Checks
```bash
# Automated health monitoring
curl -f http://localhost:9501/health
curl -f http://localhost:3002/health
```

#### 3. Performance Monitoring
```bash
# Monitor connection counts
ss -tulnp | grep -E ":(3002|9500)"

# Monitor resource usage
docker stats multi-agent-container
```

## Security Architecture

### Component Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │────│  Auth Middleware │────│  MCP Services   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐              │
         │              │  Rate Limiter   │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌────────▼────────┐              │
         └──────────────│ Circuit Breaker │──────────────┘
                        └─────────────────┘
```

### Security Flow

1. **Connection Establishment**
   - Client attempts connection
   - IP blocking check
   - Authentication validation
   - Rate limit verification
   - Connection establishment

2. **Message Processing**
   - Input validation
   - Size limit checks
   - Content sanitization
   - Rate limit updates
   - Message forwarding

3. **Error Handling**
   - Circuit breaker evaluation
   - Automatic blocking decisions
   - Security event logging
   - Client notification

## Testing Security

### Authentication Testing
```bash
# Test WebSocket authentication
node /app/core-assets/scripts/secure-client-example.js ws

# Test TCP authentication
node /app/core-assets/scripts/secure-client-example.js tcp
```

### Rate Limit Testing
```bash
# Test rate limiting with rapid requests
for i in {1..200}; do
  curl -H "Authorization: Bearer $WS_AUTH_TOKEN" \
       ws://localhost:3002 &
done
```

### Security Audit
```bash
# Check for security events
mcp-security-audit

# Monitor connections
mcp-connections

# Health status
mcp-health
```

## Common Security Issues

### 1. Default Credentials
**Problem**: Using default tokens in production
**Solution**: Always change default tokens before deployment

### 2. Weak JWT Secrets
**Problem**: Short or predictable JWT secrets
**Solution**: Use cryptographically secure random strings (minimum 32 characters)

### 3. Open CORS Policies
**Problem**: Allowing all origins with wildcards
**Solution**: Specify exact allowed origins for production

### 4. Missing SSL/TLS
**Problem**: Unencrypted communication in production
**Solution**: Always enable SSL/TLS for production deployments

### 5. Insufficient Rate Limiting
**Problem**: High rate limits allowing abuse
**Solution**: Set conservative limits and monitor usage patterns

## Best Practices

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Defense in Depth**: Implement multiple security layers
3. **Regular Updates**: Keep dependencies and certificates current
4. **Monitoring**: Implement comprehensive logging and alerting
5. **Testing**: Regular security testing and penetration testing
6. **Documentation**: Maintain up-to-date security documentation

## Support and Reporting

### Security Issues
- Report security vulnerabilities privately
- Include detailed reproduction steps
- Provide affected versions and configurations

### Getting Help
- Check logs for error messages
- Review configuration settings
- Test with secure client examples
- Monitor health check endpoints

### Updates
- Security patches are prioritized
- Follow semantic versioning for updates
- Test thoroughly in staging environment
- Maintain rollback procedures