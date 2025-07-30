# Use an NVIDIA CUDA image as the base for GPU access
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Set non-interactive frontend for package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages for a lightweight desktop environment and VNC
RUN apt-get update && apt-get install -y \
    xfce4 \
    xfce4-goodies \
    xvfb \
    x11vnc \
    dbus-x11 \
    terminator \
    wget \
    python3-pip \
    xinit \
    net-tools \
    curl \
    gnupg \
    software-properties-common \
    git \
    xz-utils \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add QGIS repository and install QGIS
RUN mkdir -p /etc/apt/keyrings/
RUN wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/qgis-archive-keyring.gpg] https://qgis.org/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/qgis.list
RUN apt-get update && apt-get install -y qgis qgis-plugin-grass

# Install Blender 4.5.1 from tar archive
COPY blender-4.5.1-linux-x64.tar.xz /tmp/blender-4.5.1-linux-x64.tar.xz
RUN cd /opt && \
    tar -xf /tmp/blender-4.5.1-linux-x64.tar.xz && \
    rm /tmp/blender-4.5.1-linux-x64.tar.xz && \
    ln -s /opt/blender-4.5.1-linux-x64 /opt/blender-4.5

# Create a non-root user for security
RUN useradd -ms /bin/bash blender

# Create directories for Blender as root (use version-agnostic approach)
RUN mkdir -p /home/blender/.config/blender

# Copy Blender addon and startup scripts as root
# We'll create the version-specific directory and install the addon at runtime
COPY addon.py /home/blender/addon.py
COPY autostart.py /home/blender/autostart.py
COPY startup.sh /home/blender/startup.sh
COPY xstartup /home/blender/.vnc/xstartup

# Install QGIS MCP plugin
RUN mkdir -p /home/blender/.local/share/QGIS/QGIS3/profiles/default/python/plugins

RUN set -x && \
    git clone https://github.com/syauqi-uqi/qgis_mcp_modify1.git /tmp/qgis_mcp_modify1 && \
    ls -la /tmp/qgis_mcp_modify1 && \
    cp -r /tmp/qgis_mcp_modify1/qgis_mcp_plugin /home/blender/.local/share/QGIS/QGIS3/profiles/default/python/plugins/ && \
    rm -rf /tmp/qgis_mcp_modify1

# Install PBR Generator
COPY tessellating-pbr-generator /opt/tessellating-pbr-generator

# Set permissions for the blender user's home directory as root
RUN chmod +x /home/blender/startup.sh /home/blender/.vnc/xstartup
RUN chown -R blender:blender /home/blender
RUN chown -R blender:blender /opt/tessellating-pbr-generator

# Switch to the non-root user
USER blender
WORKDIR /home/blender

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install PBR Generator Python dependencies (switch to root for system-wide installation)
USER root
RUN /home/blender/.local/bin/uv pip install --system -r /opt/tessellating-pbr-generator/requirements.txt
USER blender

# Set environment variables for X server, uv, and Blender
ENV DISPLAY=:1
ENV PATH="/opt/blender-4.5/blender:/home/blender/.cargo/bin:${PATH}"

# Expose the VNC port
EXPOSE 5901

# Set the entrypoint to the startup script
ENTRYPOINT ["/home/blender/startup.sh"]