# Multi-stage build for optimized production image
FROM python:3.12-slim AS builder

# Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libhdf5-dev \
    libnetcdf-dev \
    libopenblas-dev \
    libgdal-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip first (cached layer)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install requirements in order of build time (cache optimization)
COPY requirements.txt .

# Install core scientific stack first (these are big but stable)
RUN pip install --no-cache-dir \
    numpy>=1.24.0 \
    pandas>=2.0.0

# Install geospatial dependencies (pre-built wheels when available)
RUN pip install --no-cache-dir \
    rasterio>=1.3.8 \
    pyproj>=3.6.0 \
    shapely>=2.0.0

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    EDR_DATA_PATH="/app/data" \
    EDR_HOST="0.0.0.0" \
    EDR_PORT="8000" \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# Set timezone to prevent interactive prompts
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    libhdf5-310 \
    libnetcdf22 \
    libopenblas0 \
    libgdal36 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app user for security
RUN groupadd -r edr && useradd -r -g edr edr

# Create application directory
WORKDIR /app

# Copy application code
COPY --chown=edr:edr edr_publisher/ ./edr_publisher/
COPY --chown=edr:edr scripts/ ./scripts/
COPY --chown=edr:edr *.py ./

# Create data directory with proper permissions
RUN mkdir -p /app/data && chown -R edr:edr /app

# Switch to non-root user
USER edr

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${EDR_PORT}/ || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "edr_publisher.main:app", "--host", "0.0.0.0", "--port", "8000"]