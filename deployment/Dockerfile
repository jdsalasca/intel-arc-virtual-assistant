# Intel AI Assistant - Optimized Docker Configuration
# Multi-stage build for production deployment with Intel hardware support

# Base image with Intel optimizations
FROM intel/intel-extension-for-pytorch:2.2.0-xpu as base

# Set environment variables for Intel optimizations
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Intel OpenVINO and MKL optimizations
ENV OPENVINO_INSTALL_DIR=/opt/intel/openvino
ENV INTEL_OPENVINO_DIR=/opt/intel/openvino
ENV LD_LIBRARY_PATH=$OPENVINO_INSTALL_DIR/runtime/lib/intel64:$LD_LIBRARY_PATH
ENV PYTHONPATH=$OPENVINO_INSTALL_DIR/python:$PYTHONPATH

# Intel MKL optimizations
ENV MKL_NUM_THREADS=0
ENV OMP_NUM_THREADS=0
ENV INTEL_MKL_ENABLE_INSTRUCTIONS=AVX2

# Intel GPU optimizations
ENV INTEL_GPU_BACKEND=ocl
ENV SYCL_DEVICE_FILTER=level_zero

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    cmake \
    pkg-config \
    # Intel tools
    intel-basekit \
    intel-hpckit \
    # Media libraries for audio processing
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    # System utilities
    curl \
    wget \
    git \
    unzip \
    # GPU support
    ocl-icd-opencl-dev \
    intel-opencl-icd \
    # Level Zero support
    level-zero \
    level-zero-dev \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Intel OpenVINO
RUN wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null && \
    echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | tee /etc/apt/sources.list.d/oneAPI.list && \
    apt-get update && \
    apt-get install -y intel-openvino-runtime-ubuntu20-2024.1.0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Development stage
FROM base as development

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    jupyter \
    notebook \
    ipython \
    black \
    flake8 \
    mypy

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p models cache data logs

# Expose ports
EXPOSE 8000 8888

# Development command
CMD ["python", "main.py"]

# Production build stage
FROM base as builder

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM base as production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p models cache data logs && \
    chown -R appuser:appuser models cache data logs

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "main.py"]

# Intel GPU-enabled production stage
FROM production as intel-gpu

USER root

# Install additional Intel GPU drivers and tools
RUN apt-get update && apt-get install -y \
    intel-gpu-tools \
    vainfo \
    intel-media-va-driver-non-free \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Intel GPU specific environment variables
ENV OPENVINO_DEVICE=GPU
ENV INTEL_ARC_GPU_AVAILABLE=true
ENV RENDER_GROUP_ID=109

# Add user to render group for GPU access
RUN usermod -a -G render appuser

USER appuser

# Intel NPU-enabled production stage
FROM production as intel-npu

USER root

# Install Intel NPU drivers and tools
RUN apt-get update && apt-get install -y \
    intel-npu-driver \
    intel-npu-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Intel NPU specific environment variables
ENV INTEL_NPU_AVAILABLE=true
ENV NPU_COMPILER_TYPE=DRIVER
ENV NPU_EXECUTION_MODE=SYNC

USER appuser

# Full Intel hardware support stage
FROM intel-gpu as intel-full

USER root

# Install Intel NPU support
RUN apt-get update && apt-get install -y \
    intel-npu-driver \
    intel-npu-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set comprehensive Intel hardware environment variables
ENV INTEL_NPU_AVAILABLE=true
ENV NPU_COMPILER_TYPE=DRIVER
ENV NPU_EXECUTION_MODE=SYNC
ENV INTEL_FULL_HARDWARE=true

USER appuser

# Override command with Intel profile detection
CMD ["python", "-c", "import os; os.environ.setdefault('AUTO_DETECT_HARDWARE', 'true'); exec(open('main.py').read())"]