# Image Analysis MCP Server Dockerfile
# Builds a production-ready image with all dependencies pre-installed

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies required for image processing libraries
# - build-essential: C/C++ compilers needed for building packages
# - libraw-dev: Required for rawpy (RAW image processing)
# - libgl1: Required for opencv-python (OpenCV)
# - libglib2.0-0: Required for opencv-python
# - libsm6, libxext6, libxrender-dev: Additional OpenCV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libraw-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    chmod +x $POETRY_HOME/bin/poetry

# Set working directory
WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies using Poetry
# This will download and install all packages specified in pyproject.toml
RUN poetry install --no-root --only main

# Copy the rest of the application
COPY src/ ./src/
COPY tests/ ./tests/

# Install the application itself
RUN poetry install --only-root

# Create a non-root user for security
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose any ports if needed (MCP uses stdio, so not strictly necessary)
# EXPOSE 8080

# Health check (optional - checks if Python can import the module)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import image_analysis_mcp; print('OK')" || exit 1

# Set the entry point to run the MCP server
ENTRYPOINT ["python", "-m", "image_analysis_mcp.server"]

# Default command (can be overridden)
CMD []
