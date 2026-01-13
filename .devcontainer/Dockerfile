# Use Python 3.13 slim as base image
FROM python:3.13-slim

# Set locale environment variables to C.UTF-8 (always available in Debian)
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22.x via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install @openai/codex globally
RUN npm install -g @openai/codex

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

# Set the default user
USER $USERNAME

# Set bash as the default shell
SHELL ["/bin/bash", "-c"]
ENV PATH="/home/vscode/.local/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Upgrade pip and install basic tools
RUN pip install --user --upgrade pip setuptools wheel
