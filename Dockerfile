################################################################################
# Enhanced 3D Application MCP Docker Environment
# Supports: Blender, Unreal Engine, Revit MCP servers with proper networking
#
# Key Features:
# - All MCP servers properly integrated and auto-started
# - Network configured for host<->container communication
# - VNC/noVNC for remote GUI access
# - GPU support with CUDA 12.9
# - Comprehensive logging and monitoring
################################################################################
FROM nvidia/cuda:12.9.0-cudnn-devel-ubuntu24.04 AS base

################################################################################
# Stage 1 – OS deps, Python 3.12 & 3.13 venvs, Rust, Node, ML stack, WasmEdge, Blender
################################################################################
ARG DEBIAN_FRONTEND=noninteractive

# 1. Set Environment Variables
ARG BLENDER_DOWNLOAD_URL
ENV BLENDER_VERSION="4.5"
ENV BLENDER_PATH="/usr/local/blender"
ENV APP_HOME="/app"
ENV PATH="/root/.cargo/bin:/opt/venv312/bin:/root/.local/bin:${PATH}"
ENV RUSTFLAGS="-C target-cpu=skylake-avx512 -C target-feature=+avx2,+avx512f,+avx512bw,+avx512dq"
ENV WASMEDGE_PLUGIN_PATH="/usr/local/lib/wasmedge"
ENV PYTHONPATH="${APP_HOME}:/workspace"

# VNC and Display settings for remote GUI access
ENV DISPLAY=:99
ENV VNC_PORT=5900
ENV NO_VNC_PORT=6080
ENV VNC_COL_DEPTH=24
ENV VNC_RESOLUTION=1920x1080

# MCP Server configuration
ENV MCP_LOG_LEVEL=debug
ENV BLENDER_MCP_HOST=0.0.0.0
ENV BLENDER_MCP_PORT=9876
ENV REVIT_MCP_PORT=8080
ENV UNREAL_MCP_PORT=55557

WORKDIR $APP_HOME

# 2. Install All System Dependencies in a Single Layer
# This includes setting up repositories for Docker, Deadsnakes, Node.js, and OpenVINO,
# then installing all packages, and finally cleaning up.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg software-properties-common wget && \
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    # Set up the Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    # Add Deadsnakes PPA for newer Python versions
    add-apt-repository -y ppa:deadsnakes/ppa && \
    # Add NodeSource repository for up-to-date NodeJS (v22+)
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    # Add Intel's GPG key for OpenVINO
    wget -qO- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor --output /etc/apt/trusted.gpg.d/intel.gpg && \
    echo "deb https://apt.repos.intel.com/openvino ubuntu24 main" > /etc/apt/sources.list.d/intel-openvino.list && \
    # Update apt lists again after adding new repos
    apt-get update && \
    # Install all packages
    apt-get install -y --no-install-recommends \
      # Build tools and utilities
      build-essential clang git pkg-config libssl-dev \
      lsb-release shellcheck hyperfine openssh-client tmux sudo \
      unzip 7zip texlive-full latexmk chktex \
      # Docker
      docker-ce docker-ce-cli containerd.io \
      # Blender dependencies
      libxi6 libxxf86vm1 libxfixes3 libxrender1 \
      libgl1 libglu1-mesa libglib2.0-0 libsm6 libxext6 \
      libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 libdbus-1-3 \
      xvfb \
      # VNC and Remote Display for GUI access
      x11vnc xvfb fluxbox novnc websockify supervisor \
      # Network debugging tools for MCP troubleshooting
      netcat-openbsd net-tools iputils-ping dnsutils tcpdump \
      # Additional 3D application dependencies
      libglfw3 libglew2.2 libassimp5 libfreetype6 \
      ffmpeg imagemagick potrace \
      # Python versions
      python3.12 python3.12-venv python3.12-dev \
      python3.13 python3.13-venv python3.13-dev \
      # Node.js
      nodejs \
      # GPU/Wasm dependencies
      libvulkan1 vulkan-tools ocl-icd-libopencl1 \
      # OpenVINO
      openvino-2025.2.0 && \
    # Clean up apt cache
    rm -rf /var/lib/apt/lists/* && \
    # Install hadolint
    wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 && \
    chmod +x /usr/local/bin/hadolint

# 3. Install Blender
RUN BLENDER_URL=${BLENDER_DOWNLOAD_URL:-"https://mirror.clarkson.edu/blender/release/Blender4.5/blender-4.5.0-linux-x64.tar.xz"} && \
    wget "${BLENDER_URL}" -O blender.tar.xz && \
    tar -xf blender.tar.xz && \
    mv blender-${BLENDER_VERSION}.0-linux-x64 ${BLENDER_PATH} && \
    rm blender.tar.xz

# 4. Install Blender Python Dependencies & Create Addon Directory
RUN mkdir -p ${BLENDER_PATH}/${BLENDER_VERSION}/scripts/addons/blender_mcp_server && \
    ${BLENDER_PATH}/${BLENDER_VERSION}/python/bin/python3.11 -m ensurepip && \
    ${BLENDER_PATH}/${BLENDER_VERSION}/python/bin/python3.11 -m pip install --upgrade pip && \
    ${BLENDER_PATH}/${BLENDER_VERSION}/python/bin/python3.11 -m pip install Pillow

# 5. Install Rust Toolchain and Tools
# Using cargo-binstall for faster, pre-compiled binaries
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile default && \
    . "$HOME/.cargo/env" && \
    cargo install cargo-binstall && \
    cargo binstall -y cargo-edit

# 6. Install uv and uvx (fast python package managers)
# uvx is required for running blender-mcp as a tool
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 7. Install WasmEdge
RUN curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install.sh | \
    bash -s -- -p /usr/local --plugins wasi_nn-openvino && ldconfig

# 8. Create Python Virtual Environments
RUN python3.12 -m venv /opt/venv312 && \
    /opt/venv312/bin/pip install --upgrade pip wheel setuptools && \
    python3.13 -m venv /opt/venv313 && \
    /opt/venv313/bin/pip install --upgrade pip wheel setuptools

# 9. Install Global NPM Packages
RUN npm install -g \
    claude-flow@alpha \
    ruv-swarm \
    @anthropic-ai/claude-code \
    @google/gemini-cli \
    @openai/codex \
    vite \
    typescript \
    eslint \
    prettier \
    jest \
    storybook

# 10. Install Python ML & AI libraries + MCP dependencies
# Copy requirements file and install dependencies to leverage Docker layer caching.
COPY requirements.txt .
RUN /opt/venv312/bin/pip install --no-cache-dir -r requirements.txt && \
    # Install Modular MAX runtime separately
    /opt/venv312/bin/pip install --no-cache-dir --pre modular && \
    # Install MCP-specific Python packages
    /opt/venv312/bin/pip install --no-cache-dir blender-mcp fastmcp mcp

# 11. Clone and Setup MCP Server Repositories
# Each MCP server is properly built and configured for immediate use
RUN git clone https://github.com/revit-mcp/revit-mcp.git /app/revit-mcp && \
    cd /app/revit-mcp && npm install && npm run build && cd /app && \
    git clone https://github.com/ahujasid/blender-mcp.git /app/blender-mcp-source && \
    cd /app/blender-mcp-source && /opt/venv312/bin/pip install -e . && cd /app && \
    git clone https://github.com/chongdashu/unreal-mcp.git /app/unreal-mcp-source && \
    cd /app/unreal-mcp-source/Python && \
    [ -f requirements.txt ] && /opt/venv312/bin/pip install -r requirements.txt || true && \
    cd /app

# Create directories for MCP configuration and logs
RUN mkdir -p /app/mcp-configs /app/mcp-logs /app/mcp-scripts

# 12. Copy application files and MCP configurations
COPY addon.py ${BLENDER_PATH}/${BLENDER_VERSION}/scripts/addons/blender_mcp_server/__init__.py
COPY keep_alive.py $APP_HOME/
COPY entrypoint.sh /
COPY supervisord.conf /etc/supervisor/conf.d/
COPY healthcheck.sh /app/mcp-scripts/
RUN chmod +x /entrypoint.sh && \
    [ -f /app/mcp-scripts/healthcheck.sh ] && chmod +x /app/mcp-scripts/healthcheck.sh || true

################################################################################
# Stage 2 – Non‑root user, health‑check, env placeholders
################################################################################
ARG UID=1000
ARG GID=1000

# 13. Create non-root user and set permissions
RUN (id ubuntu &>/dev/null && userdel -r ubuntu) || true && \
    groupadd -g ${GID} dev && \
    useradd -m -s /bin/bash -u ${UID} -g ${GID} dev && \
    usermod -aG docker,sudo dev && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/dev && chmod 0440 /etc/sudoers.d/dev && \
    chown -R dev:dev /usr/lib/node_modules && \
    ln -s /usr/bin/python3.12 /usr/local/bin/python && \
    mkdir -p /workspace /workspace/ext /workspace/logs /workspace/.vnc && \
    chown -R dev:dev /workspace $APP_HOME && \
    # Setup VNC password (default: mcpserver) - can be overridden via env
    mkdir -p /home/dev/.vnc && \
    x11vnc -storepasswd ${VNC_PASSWORD:-mcpserver} /home/dev/.vnc/passwd && \
    chown -R dev:dev /home/dev/.vnc && \
    # Ensure uvx is available in PATH for all users
    ln -s /root/.cargo/bin/uvx /usr/local/bin/uvx 2>/dev/null || true

USER dev
WORKDIR /workspace

# 14. Copy documentation and configure git for the dev user
COPY README.md .
COPY CLAUDE-README.md .
RUN git config --global user.email "mcp@3d-docker.local" && \
    git config --global user.name "MCP 3D Agent" && \
    # Configure Claude Code MCP settings directory
    mkdir -p /home/dev/.claude && \
    echo '{"mcpServers": {}}' > /home/dev/.claude/settings.json && \
    chown -R dev:dev /home/dev/.claude

# 15. Final setup and port exposure
# MCP Server Ports - accessible from host machine
# Blender MCP TCP server
EXPOSE 9876
# Revit MCP server
EXPOSE 8080
# Unreal MCP TCP server
EXPOSE 55557

# UI/Service Ports
# Claude Flow UI
EXPOSE 3000
# Additional services
EXPOSE 3001

# Remote Access Ports
# VNC for remote desktop
EXPOSE 5900
# noVNC for web-based access
EXPOSE 6080

# Development Ports
# Development server
EXPOSE 8000
# Jupyter notebook
EXPOSE 8888

# Health check to ensure MCP servers are responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD ["/bin/bash", "-c", "nc -z localhost 9876 || nc -z localhost 8080 || nc -z localhost 55557 || exit 1"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["--interactive"]
