################################################################################
# Optimized 3D Application MCP Docker Environment
# Multi-stage build for faster rebuilds and better caching
################################################################################

# Base stage with system dependencies
FROM nvidia/cuda:12.9.0-cudnn-devel-ubuntu24.04 AS base-system

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.cargo/bin:/opt/venv312/bin:/root/.local/bin:${PATH}"

# Install system dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg software-properties-common wget \
    build-essential git pkg-config libssl-dev \
    xvfb x11vnc fluxbox novnc websockify supervisor \
    netcat-openbsd net-tools iputils-ping dnsutils \
    python3.12 python3.12-venv python3.12-dev \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Python virtual environment
RUN python3.12 -m venv /opt/venv312 && \
    /opt/venv312/bin/pip install --upgrade pip wheel setuptools

################################################################################
# Blender stage
FROM base-system AS blender-stage

ARG BLENDER_DOWNLOAD_URL
ENV BLENDER_VERSION="4.5"
ENV BLENDER_PATH="/usr/local/blender"

RUN BLENDER_URL=${BLENDER_DOWNLOAD_URL:-"https://mirror.clarkson.edu/blender/release/Blender4.5/blender-4.5.0-linux-x64.tar.xz"} && \
    wget "${BLENDER_URL}" -O blender.tar.xz && \
    tar -xf blender.tar.xz && \
    mv blender-${BLENDER_VERSION}.0-linux-x64 ${BLENDER_PATH} && \
    rm blender.tar.xz && \
    mkdir -p ${BLENDER_PATH}/${BLENDER_VERSION}/scripts/addons/blender_mcp_server

################################################################################
# MCP dependencies stage
FROM base-system AS mcp-deps

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .
RUN /opt/venv312/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv312/bin/pip install --no-cache-dir blender-mcp fastmcp mcp

# Clone MCP repositories
RUN git clone https://github.com/revit-mcp/revit-mcp.git /app/revit-mcp && \
    cd /app/revit-mcp && npm install && npm run build && \
    git clone https://github.com/ahujasid/blender-mcp.git /app/blender-mcp-source && \
    cd /app/blender-mcp-source && /opt/venv312/bin/pip install -e . && \
    git clone https://github.com/chongdashu/unreal-mcp.git /app/unreal-mcp-source

################################################################################
# Runtime stage
FROM base-system AS runtime

# Copy from previous stages
COPY --from=blender-stage /usr/local/blender /usr/local/blender
COPY --from=mcp-deps /opt/venv312 /opt/venv312
COPY --from=mcp-deps /app /app

# Environment variables
ENV BLENDER_VERSION="4.5"
ENV BLENDER_PATH="/usr/local/blender"
ENV APP_HOME="/app"
ENV DISPLAY=:99
ENV VNC_PORT=5900
ENV NO_VNC_PORT=6080
ENV VNC_COL_DEPTH=24
ENV VNC_RESOLUTION=1920x1080
ENV MCP_LOG_LEVEL=debug
ENV PYTHONPATH="${APP_HOME}:/workspace"

WORKDIR $APP_HOME

# Install additional runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libxi6 libxxf86vm1 libxfixes3 libxrender1 \
    libgl1 libglu1-mesa libglib2.0-0 libsm6 libxext6 \
    libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 libdbus-1-3 \
    jq uuid-runtime \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/mcp-configs /app/mcp-logs /app/mcp-scripts

# Copy application files
COPY addon.py ${BLENDER_PATH}/${BLENDER_VERSION}/scripts/addons/blender_mcp_server/__init__.py
COPY keep_alive.py $APP_HOME/
COPY entrypoint.sh /
COPY supervisord.conf /etc/supervisor/conf.d/
COPY mcp-scripts/ /app/mcp-scripts/

RUN chmod +x /entrypoint.sh /app/mcp-scripts/*.sh

# Create non-root user
ARG UID=1000
ARG GID=1000

RUN groupadd -g ${GID} dev && \
    useradd -m -s /bin/bash -u ${UID} -g ${GID} dev && \
    usermod -aG sudo dev && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/dev && \
    mkdir -p /workspace /home/dev/.vnc && \
    chown -R dev:dev /workspace /app /home/dev && \
    x11vnc -storepasswd ${VNC_PASSWORD:-mcpserver} /home/dev/.vnc/passwd

USER dev
WORKDIR /workspace

# Copy documentation
COPY --chown=dev:dev README.md CLAUDE-README.md MCP_VISUALIZATION_API.md ./

# Configure git
RUN git config --global user.email "mcp@3d-docker.local" && \
    git config --global user.name "MCP 3D Agent" && \
    mkdir -p /home/dev/.claude && \
    echo '{"mcpServers": {}}' > /home/dev/.claude/settings.json

# Expose ports
EXPOSE 9876 8080 55557 3000 3001 5900 6080 8000 8888

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD ["/app/mcp-scripts/health-check.sh"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["--interactive"]