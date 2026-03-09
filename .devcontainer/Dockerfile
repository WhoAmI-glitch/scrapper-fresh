FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    jq \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    shellcheck \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm via corepack
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up workspace directory
WORKDIR /workspace

# Copy dependency manifests for caching
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./

# Default shell
SHELL ["/bin/bash", "-c"]
