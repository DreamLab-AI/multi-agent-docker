#!/bin/bash
# Health check script for MCP services

# This script can be used as a Docker health check or run manually
# Exit codes: 0 = healthy, 1 = unhealthy

BLENDER_HOST="${BLENDER_HOST:-blender_desktop}"
BLENDER_PORT="${BLENDER_PORT:-9876}"
QGIS_HOST="${QGIS_HOST:-blender_desktop}"
QGIS_PORT="${QGIS_PORT:-9877}"
PBR_HOST="${PBR_HOST:-blender_desktop}"
PBR_PORT="${PBR_PORT:-9878}"

# Check if services are specified via arguments
SERVICE="${1:-all}"

check_blender() {
    if timeout 2 bash -c "</dev/tcp/$BLENDER_HOST/$BLENDER_PORT" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

check_qgis() {
    if timeout 2 bash -c "</dev/tcp/$QGIS_HOST/$QGIS_PORT" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

check_pbr() {
    if timeout 2 bash -c "</dev/tcp/$PBR_HOST/$PBR_PORT" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

case "$SERVICE" in
    blender)
        check_blender
        exit $?
        ;;
    qgis)
        check_qgis
        exit $?
        ;;
    pbr)
        check_pbr
        exit $?
        ;;
    all|*)
        blender_status=0
        qgis_status=0
        pbr_status=0
        
        check_blender || blender_status=1
        check_qgis || qgis_status=1
        check_pbr || pbr_status=1
        
        # Return unhealthy if any service fails
        if [ $blender_status -ne 0 ] || [ $qgis_status -ne 0 ] || [ $pbr_status -ne 0 ]; then
            exit 1
        else
            exit 0
        fi
        ;;
esac