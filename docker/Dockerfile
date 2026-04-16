FROM ubuntu:24.04

ARG AGENT=gemini

# Install base tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    python-is-python3 \
    python3-pip \
    python3-venv \
    unzip \
    wget \
&& rm -rf /var/lib/apt/lists/*

# Install C++ development tools (Gemini only).
RUN if [ "$AGENT" = "gemini" ]; then \
    apt-get update && apt-get install -y --no-install-recommends \
        cmake \
        g++ \
        gdb \
        gpg \
        lcov \
        llvm \
        ninja-build \
        software-properties-common \
        ssh \
    && rm -rf /var/lib/apt/lists/*; \
    fi

# Create non-root user.
RUN useradd -m -s /bin/bash vscode \
    && mkdir -p /workspace \
    && chown vscode:vscode /workspace

# Install Node.js (required for both Gemini CLI and Claude Code).
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Switch to non-root user.
USER vscode
WORKDIR /workspace

# Configure npm for user-local global installs.
ENV NPM_CONFIG_PREFIX=/home/vscode/.npm-global
ENV PATH="/home/vscode/.npm-global/bin:/home/vscode/.local/bin:/usr/local/bin:${PATH}"
RUN mkdir -p /home/vscode/.npm-global

# Install the AI agent CLI.
RUN if [ "$AGENT" = "gemini" ]; then \
        npm install -g @google/gemini-cli; \
    else \
        npm install -g @anthropic-ai/claude-code; \
    fi

# Set up uv and Python environment.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV UV_PROJECT_ENVIRONMENT="/home/vscode/.venv"

# Pre-configure Gemini CLI (Gemini only).
RUN if [ "$AGENT" = "gemini" ]; then \
        mkdir -p /home/vscode/.gemini \
        && echo '{"/workspace": "TRUST_FOLDER"}' > /home/vscode/.gemini/trustedFolders.json \
        && echo '{"selectedAuthType": "oauth-personal"}' > /home/vscode/.gemini/settings.json; \
    fi

# For Claude: ~/.claude is mounted from the host at runtime to persist auth state between sessions.
