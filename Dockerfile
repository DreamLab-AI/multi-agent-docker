# Stage 0 – CUDA + cuDNN (official NVIDIA image)
FROM nvidia/cuda:12.9.1-devel-ubuntu24.04 AS base

################################################################################
# Stage 1 – OS deps, Python 3.12 & 3.13 venvs, Rust, Node, ML stack, WasmEdge, Blender
################################################################################
ARG DEBIAN_FRONTEND=noninteractive

# 1. Set Environment Variables
# Internal Blender has been removed. This environment now connects to an external Blender instance.
# ARG BLENDER_DOWNLOAD_URL
# ENV BLENDER_VERSION="4.5"
# ENV BLENDER_PATH="/usr/local/blender"

# Set the application workspace directory
ENV APP_HOME="/app"
WORKDIR $APP_HOME

# 2. Install Dependencies
# Add any dependencies needed to run Blender and its Python environment.
# wget and other utilities are for downloading and extracting Blender.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
    ca-certificates curl gnupg software-properties-common
# Add Docker's official GPG key
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg
# Set up the repository
RUN echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
# Add Deadsnakes PPA for newer Python versions
RUN add-apt-repository -y ppa:deadsnakes/ppa && \
    add-apt-repository -y ppa:kicad/kicad-9.0-releases
# Add NodeSource repository for up-to-date NodeJS (v22+)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
# Install all packages including network utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
      wget libxi6 libxxf86vm1 libxfixes3 libxrender1 \
      build-essential clang git pkg-config libssl-dev \
      lsb-release shellcheck hyperfine openssh-client tmux sudo \
      docker-ce docker-ce-cli containerd.io unzip 7zip texlive-full latexmk chktex \
      iputils-ping netcat-openbsd net-tools dnsutils traceroute tcpdump nmap \
      iproute2 iptables curl wget telnet mtr-tiny \
      sqlite3 libsqlite3-dev \
      libgl1 libglu1-mesa libglib2.0-0 libsm6 libxext6 \
      libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 libdbus-1-3 \
      supervisor \
      python3.12 python3.12-venv python3.12-dev \
      nodejs \
      jq \
      libvulkan1 vulkan-tools ocl-icd-libopencl1 && \
    rm -rf /var/lib/apt/lists/* && \
    wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 && \
    chmod +x /usr/local/bin/hadolint

# 3. Create a non-root user
RUN useradd -m -s /bin/bash dev && \
    echo "dev:dev" | chpasswd && \
    adduser dev sudo

# 4. Set up Python environments
# Create a virtual environment for Python 3.12
RUN python3.12 -m venv /opt/venv312
# Create a virtual environment for Python 3.13
# RUN python3.13 -m venv /opt/venv313

# Set the PATH to include the venv's bin directory
ENV PATH="/opt/venv312/bin:$PATH"

# 5. Install Graphics and 3D Libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
    imagemagick \
    inkscape \
    ffmpeg \
    colmap \
    libpng-dev libjpeg-dev libtiff-dev libopenexr-dev && \
    rm -rf /var/lib/apt/lists/*

# 6. Install EDA (Electronic Design Automation) Tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends --allow-unauthenticated \
    kicad \
    ngspice \
    libngspice0 && \
    rm -rf /var/lib/apt/lists/*

# 7. Set up Deno
# Install Deno
RUN curl -fsSL https://deno.land/x/install/install.sh | sh
# Add Deno to the PATH for all users
ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:$PATH"

# 8. Copy Application Files
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY setup-workspace.sh /app/setup-workspace.sh
RUN chmod +x /app/setup-workspace.sh

# 9. Install Node.js packages
# Install global Node.js packages
RUN npm install -g \
    gltf-pipeline \
    claude-flow@alpha \
    ruv-swarm@latest \
    @google/gemini-cli@latest \
    @openai/codex@latest && \
    # Install claude-code separately to avoid potential npm conflicts
    npm install -g @anthropic-ai/claude-code@latest && \
    npm install -g sqlite3 --unsafe-perm

# ---------- Install Python ML & AI libraries into the 3.12 venv ----------
# Copy requirements file and install dependencies to leverage Docker layer caching.
# Note: PyTorch is installed separately to ensure the correct CUDA-enabled version is used.
COPY requirements.txt .
RUN /opt/venv312/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r requirements.txt

# Install pre-release packages like 'modular' separately. This ensures that they are
# installed on its own to avoid influencing the resolution of stable packages.
RUN /opt/venv312/bin/pip install --no-cache-dir --retries 10 --timeout 60 --pre modular

# Install PyTorch with CUDA support
RUN /opt/venv312/bin/pip install --no-cache-dir --retries 10 --timeout 60 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# ---------- Rust tool-chain (AVX‑512) ----------
ENV PATH="/root/.cargo/bin:${PATH}"
# Update certificates and install Rust with retry logic
RUN apt-get update && apt-get install -y ca-certificates && \
    for i in 1 2 3; do curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && break || sleep 5; done

# ---------- WasmEdge (with OpenVINO backend) ----------
RUN curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install.sh | \
    bash -s -- -p /usr/local --plugins wasi_nn-openvino && \
    ldconfig

# 10. Switch to the dev user
USER dev
WORKDIR /workspace

# Copy core assets and set permissions
USER root
COPY --chown=dev:dev core-assets/ /app/core-assets/
# Install Node.js dependencies for all scripts
USER root
RUN cd /app/core-assets/scripts && npm install && chown -R dev:dev /app/core-assets/scripts/node_modules
USER dev

# Copy documentation and configuration files
USER root
COPY README.md .
COPY AGENT-BRIEFING.md .

# Configure git for the dev user
RUN git config --global user.email "agent@multi-agent-docker.com" && \
    git config --global user.name "Development Agent"

# 11. Final Setup
# Copy supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command to start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# Healthcheck to verify claude-flow is installed
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["sh", "-c", "command -v claude-flow >/dev/null"] || exit 1