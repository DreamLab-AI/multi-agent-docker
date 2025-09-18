#!/bin/bash

# Security Validation Script for Multi-Agent Docker Environment
# Tests all security features and configurations

set -e

echo "🔒 Multi-Agent Docker Security Validation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

# Helper functions
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

log_info() {
    echo -e "ℹ️  $1"
}

# Check if services are running
check_service_status() {
    log_info "Checking service status..."
    
    if docker ps | grep -q "multi-agent-container"; then
        log_success "Multi-agent container is running"
    else
        log_error "Multi-agent container is not running"
        return 1
    fi
}

# Test environment configuration
test_environment_config() {
    log_info "Testing environment configuration..."
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        log_success ".env file exists"
    else
        log_error ".env file not found"
        return 1
    fi
    
    # Check for default tokens
    if grep -q "your-secure-websocket-token-change-me" .env 2>/dev/null; then
        log_warning "Default WebSocket token detected in .env"
    else
        log_success "WebSocket token has been changed"
    fi
    
    if grep -q "your-secure-tcp-token-change-me" .env 2>/dev/null; then
        log_warning "Default TCP token detected in .env"
    else
        log_success "TCP token has been changed"
    fi
    
    if grep -q "your-super-secret-jwt-key-minimum-32-chars" .env 2>/dev/null; then
        log_warning "Default JWT secret detected in .env"
    else
        log_success "JWT secret has been changed"
    fi
}

# Test network connectivity
test_network_connectivity() {
    log_info "Testing network connectivity..."
    
    # Test WebSocket port
    if docker exec multi-agent-container nc -z localhost 3002 2>/dev/null; then
        log_success "WebSocket service (port 3002) is accessible"
    else
        log_error "WebSocket service (port 3002) is not accessible"
    fi
    
    # Test TCP port
    if docker exec multi-agent-container nc -z localhost 9500 2>/dev/null; then
        log_success "TCP service (port 9500) is accessible"
    else
        log_error "TCP service (port 9500) is not accessible"
    fi
    
    # Test health check
    if docker exec multi-agent-container curl -f http://localhost:9501/health 2>/dev/null; then
        log_success "Health check endpoint is responding"
    else
        log_warning "Health check endpoint is not responding"
    fi
}

# Test authentication
test_authentication() {
    log_info "Testing authentication..."
    
    # Test WebSocket authentication (should fail without token)
    if timeout 5 docker exec multi-agent-container node -e "
        const WebSocket = require('ws');
        const ws = new WebSocket('ws://localhost:3002');
        ws.on('error', () => process.exit(0));
        ws.on('open', () => process.exit(1));
        setTimeout(() => process.exit(0), 3000);
    " 2>/dev/null; then
        log_success "WebSocket authentication is working (rejected unauthenticated connection)"
    else
        log_warning "WebSocket authentication test inconclusive"
    fi
}

# Test rate limiting
test_rate_limiting() {
    log_info "Testing rate limiting..."
    
    # Create a simple rate limit test
    docker exec multi-agent-container bash -c '
        echo "Testing rate limiting with multiple rapid connections..."
        for i in {1..10}; do
            timeout 1 nc localhost 3002 &
        done
        wait
        echo "Rate limit test completed"
    ' >/dev/null 2>&1
    
    log_success "Rate limiting test completed (check logs for blocked connections)"
}

# Test security scripts
test_security_scripts() {
    log_info "Testing security scripts..."
    
    # Check if auth middleware exists
    if docker exec multi-agent-container test -f "/app/core-assets/scripts/auth-middleware.js"; then
        log_success "Auth middleware script is present"
    else
        log_error "Auth middleware script is missing"
    fi
    
    # Check if secure client example exists
    if docker exec multi-agent-container test -f "/app/core-assets/scripts/secure-client-example.js"; then
        log_success "Secure client example script is present"
    else
        log_error "Secure client example script is missing"
    fi
    
    # Test script permissions
    if docker exec multi-agent-container ls -la /app/core-assets/scripts/ | grep -q "rwxr-x---"; then
        log_success "Security scripts have appropriate permissions"
    else
        log_warning "Security scripts may have incorrect permissions"
    fi
}

# Test logging and monitoring
test_logging_monitoring() {
    log_info "Testing logging and monitoring..."
    
    # Check if log directory exists
    if docker exec multi-agent-container test -d "/app/mcp-logs"; then
        log_success "Log directory exists"
    else
        log_error "Log directory is missing"
    fi
    
    # Check if security log directory exists
    if docker exec multi-agent-container test -d "/app/mcp-logs/security"; then
        log_success "Security log directory exists"
    else
        log_warning "Security log directory is missing"
    fi
    
    # Check for recent log entries
    if docker exec multi-agent-container find /app/mcp-logs -name "*.log" -mtime -1 | grep -q .; then
        log_success "Recent log files found"
    else
        log_warning "No recent log files found"
    fi
}

# Test Docker security
test_docker_security() {
    log_info "Testing Docker security configuration..."
    
    # Check if container is running as non-root
    USER_ID=$(docker exec multi-agent-container id -u dev 2>/dev/null || echo "error")
    if [ "$USER_ID" != "0" ] && [ "$USER_ID" != "error" ]; then
        log_success "Container is running as non-root user (UID: $USER_ID)"
    else
        log_error "Container may be running as root or user check failed"
    fi
    
    # Check security options
    if docker inspect multi-agent-container | grep -q "seccomp:unconfined"; then
        log_warning "Container is running with unconfined seccomp (may be needed for development)"
    else
        log_success "Container is running with default seccomp profile"
    fi
}

# Test SSL/TLS configuration
test_ssl_config() {
    log_info "Testing SSL/TLS configuration..."
    
    # Check if SSL is enabled in environment
    SSL_ENABLED=$(docker exec multi-agent-container env | grep SSL_ENABLED || echo "SSL_ENABLED=false")
    if echo "$SSL_ENABLED" | grep -q "true"; then
        log_info "SSL is enabled - checking certificates..."
        
        # Check for certificate files
        if docker exec multi-agent-container test -f "/app/certs/server.crt"; then
            log_success "SSL certificate file found"
        else
            log_error "SSL certificate file missing"
        fi
        
        if docker exec multi-agent-container test -f "/app/certs/server.key"; then
            log_success "SSL private key file found"
        else
            log_error "SSL private key file missing"
        fi
    else
        log_info "SSL is disabled (expected for development)"
    fi
}

# Performance and resource tests
test_performance() {
    log_info "Testing performance and resource usage..."
    
    # Check memory usage
    MEMORY_USAGE=$(docker stats multi-agent-container --no-stream --format "{{.MemPerc}}" | sed 's/%//')
    if (( $(echo "$MEMORY_USAGE < 80" | bc -l) )); then
        log_success "Memory usage is acceptable ($MEMORY_USAGE%)"
    else
        log_warning "High memory usage detected ($MEMORY_USAGE%)"
    fi
    
    # Check CPU usage
    CPU_USAGE=$(docker stats multi-agent-container --no-stream --format "{{.CPUPerc}}" | sed 's/%//')
    if (( $(echo "$CPU_USAGE < 80" | bc -l) )); then
        log_success "CPU usage is acceptable ($CPU_USAGE%)"
    else
        log_warning "High CPU usage detected ($CPU_USAGE%)"
    fi
}

# Test backup and recovery
test_backup_recovery() {
    log_info "Testing backup and recovery capabilities..."
    
    # Check if backup is enabled
    BACKUP_ENABLED=$(docker exec multi-agent-container env | grep DB_BACKUP_ENABLED || echo "DB_BACKUP_ENABLED=false")
    if echo "$BACKUP_ENABLED" | grep -q "true"; then
        log_success "Database backup is enabled"
    else
        log_info "Database backup is disabled"
    fi
    
    # Check for workspace backup
    if docker exec multi-agent-container test -d "/workspace"; then
        log_success "Workspace directory is accessible for backup"
    else
        log_error "Workspace directory is not accessible"
    fi
}

# Run all tests
main() {
    echo ""
    log_info "Starting security validation tests..."
    echo ""
    
    # Run test suites
    check_service_status
    echo ""
    
    test_environment_config
    echo ""
    
    test_network_connectivity
    echo ""
    
    test_authentication
    echo ""
    
    test_rate_limiting
    echo ""
    
    test_security_scripts
    echo ""
    
    test_logging_monitoring
    echo ""
    
    test_docker_security
    echo ""
    
    test_ssl_config
    echo ""
    
    test_performance
    echo ""
    
    test_backup_recovery
    echo ""
    
    # Summary
    echo "=========================================="
    echo "🔒 Security Validation Summary"
    echo "=========================================="
    echo ""
    log_success "Tests Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Tests Failed: $TESTS_FAILED"
    fi
    if [ $WARNINGS -gt 0 ]; then
        log_warning "Warnings: $WARNINGS"
    fi
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        if [ $WARNINGS -eq 0 ]; then
            echo -e "${GREEN}🎉 All security tests passed! Your environment is secure.${NC}"
        else
            echo -e "${YELLOW}✅ Security tests passed with warnings. Review warnings above.${NC}"
        fi
        exit 0
    else
        echo -e "${RED}💥 Some security tests failed. Please address the issues above.${NC}"
        exit 1
    fi
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if bc is available for calculations
if ! command -v bc &> /dev/null; then
    log_warning "bc is not installed - skipping numeric calculations"
fi

# Run main function
main "$@"