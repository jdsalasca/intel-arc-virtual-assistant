# Intel AI Assistant - Deployment Guide

## Overview

This directory contains all the necessary files for deploying the Intel AI Assistant with full Intel hardware optimization support. The deployment system supports automatic hardware detection and provides optimized configurations for different Intel hardware combinations.

## Deployment Options

### Hardware Profiles

- **Full Intel Stack** (`full`): Core Ultra 7 + Arc GPU + NPU
- **Intel GPU** (`gpu`): Intel CPU + Arc GPU (A770, A750, or Iris Xe)
- **Intel NPU** (`npu`): Intel CPU + AI Boost NPU
- **CPU Only** (`cpu`): Intel CPU without dedicated GPU/NPU

### Deployment Methods

1. **Docker Compose** (Recommended)
2. **Standalone Docker**
3. **Native Python Installation**

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 8GB+ RAM (16GB+ recommended for GPU profiles)
- 10GB+ available disk space
- Intel hardware (CPU required, GPU/NPU optional)

### Automatic Deployment

#### Linux/macOS
```bash
cd deployment
chmod +x deploy.sh
./deploy.sh
```

#### Windows
```powershell
cd deployment
.\deploy.ps1
```

The deployment script will:
1. Detect your Intel hardware
2. Select the optimal deployment profile
3. Build the appropriate Docker image
4. Deploy the services
5. Validate the deployment

### Manual Deployment

#### 1. Choose Your Profile

Check your hardware and select the appropriate profile:

```bash
# Auto-detect hardware
docker-compose -f docker-compose.yml --profile production --profile full up -d

# Or specify manually
docker-compose -f docker-compose.yml --profile production --profile cpu up -d
```

#### 2. Available Profiles

- `dev`: Development environment with hot reload
- `cpu`: CPU-only production
- `gpu`: Intel GPU-enabled production
- `npu`: Intel NPU-enabled production  
- `full`: Full Intel hardware support
- `monitoring`: Prometheus + Grafana monitoring
- `ha`: High availability with load balancer

## Configuration Files

### Docker Configuration

- **`Dockerfile`**: Multi-stage build with Intel optimizations
  - Base image with Intel Extension for PyTorch
  - OpenVINO and Intel MKL integration
  - GPU and NPU driver support
  - Security hardening

- **`docker-compose.yml`**: Complete service orchestration
  - Multiple hardware profiles
  - Load balancing with Nginx
  - Monitoring with Prometheus/Grafana
  - Database persistence with PostgreSQL
  - Caching with Redis

### Infrastructure Configuration

- **`nginx.conf`**: Load balancer and reverse proxy
  - Rate limiting
  - SSL termination
  - Health checks
  - Static file serving

- **`prometheus.yml`**: Monitoring configuration
  - Intel hardware metrics
  - Application performance metrics
  - Custom Intel AI metrics

- **`init-db.sql`**: Database schema
  - Conversation storage
  - User management
  - Performance analytics
  - Intel profile configurations

## Environment Configuration

### Production Environment Variables

```bash
# Intel Hardware Configuration
INTEL_CPU=true
INTEL_GPU=true
INTEL_NPU=true
DEPLOYMENT_PROFILE=full

# OpenVINO Configuration
OPENVINO_DEVICE=AUTO
MODEL_CACHE_DIR=/app/models
OPENVINO_CACHE_DIR=/app/cache

# Intel Optimizations
MKL_NUM_THREADS=0
OMP_NUM_THREADS=0
INTEL_MKL_ENABLE_INSTRUCTIONS=AVX2
INTEL_GPU_BACKEND=ocl

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### Hardware-Specific Variables

#### Intel GPU
```bash
INTEL_ARC_GPU_AVAILABLE=true
OPENVINO_DEVICE=GPU
RENDER_GROUP_ID=109
```

#### Intel NPU
```bash
INTEL_NPU_AVAILABLE=true
NPU_COMPILER_TYPE=DRIVER
NPU_EXECUTION_MODE=SYNC
```

## Deployment Scripts

### Linux/macOS: `deploy.sh`

Features:
- Automatic Intel hardware detection
- System requirements validation
- Docker image building
- Service deployment
- Health validation
- Deployment information display

Usage:
```bash
./deploy.sh [OPTIONS]

Options:
  --profile PROFILE    Force deployment profile (cpu|gpu|npu|full)
  --monitoring         Enable monitoring (Prometheus + Grafana)
  --ha                 Enable high availability
  --skip-build         Skip Docker image building
  --help               Show help message
```

Examples:
```bash
# Auto-detect and deploy
./deploy.sh

# Force full profile with monitoring
./deploy.sh --profile full --monitoring

# Deploy with high availability
./deploy.sh --ha
```

### Windows: `deploy.ps1`

PowerShell deployment script with the same features as the Linux version.

Usage:
```powershell
.\deploy.ps1 [OPTIONS]

Parameters:
  -Profile            Deployment profile
  -Monitoring         Enable monitoring
  -HighAvailability   Enable HA setup
  -SkipBuild          Skip image building
  -Help               Show help
```

Examples:
```powershell
# Auto-detect and deploy
.\deploy.ps1

# Force GPU profile with monitoring
.\deploy.ps1 -Profile gpu -Monitoring

# Deploy with high availability
.\deploy.ps1 -HighAvailability
```

## Service Management

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.yml --profile production --profile full up -d

# Start with monitoring
docker-compose -f docker-compose.yml --profile production --profile full --profile monitoring up -d
```

### Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.yml down

# Stop and remove volumes
docker-compose -f docker-compose.yml down -v
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.yml logs -f

# Specific service
docker-compose -f docker-compose.yml logs -f intel-ai-full
```

### Health Checks

```bash
# Main API
curl http://localhost:8000/healthz

# Hardware information
curl http://localhost:8000/api/v1/health/hardware

# Configuration status
curl http://localhost:8000/api/v1/health/configuration
```

## Monitoring and Observability

### Prometheus Metrics

Access Prometheus at `http://localhost:9090`

Available metrics:
- Intel hardware utilization (GPU, NPU)
- Model performance (tokens/sec, latency)
- System resources (CPU, memory)
- Application metrics (requests, errors)

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin)

Pre-configured dashboards:
- Intel AI Assistant Overview
- Hardware Performance
- Model Performance Analytics
- System Health

### Log Aggregation

Logs are centralized and accessible via:
```bash
# Application logs
docker-compose logs -f intel-ai-full

# Nginx access logs
docker-compose logs -f nginx

# Database logs
docker-compose logs -f postgres
```

## Scaling and High Availability

### Horizontal Scaling

Add more application instances:

```yaml
# docker-compose.override.yml
services:
  intel-ai-full-2:
    extends:
      service: intel-ai-full
    container_name: intel-ai-full-2
    
  intel-ai-full-3:
    extends:
      service: intel-ai-full
    container_name: intel-ai-full-3
```

Update Nginx upstream configuration:
```nginx
upstream intel_ai_backend {
    least_conn;
    server intel-ai-full:8000;
    server intel-ai-full-2:8000;
    server intel-ai-full-3:8000;
}
```

### Database High Availability

Enable PostgreSQL replication:
```yaml
postgres-primary:
  image: postgres:15-alpine
  environment:
    - POSTGRES_REPLICATION_MODE=master
    
postgres-replica:
  image: postgres:15-alpine
  environment:
    - POSTGRES_REPLICATION_MODE=slave
    - POSTGRES_MASTER_SERVICE=postgres-primary
```

### Load Balancing

Nginx provides:
- Round-robin load balancing
- Health check-based routing
- Failover support
- Rate limiting

## Security Considerations

### Network Security

- Container-to-container communication via internal networks
- Expose only necessary ports (80, 443, 8000)
- Rate limiting on API endpoints
- Security headers in Nginx

### Data Security

- Environment variable encryption
- Database connection encryption
- API key management
- User authentication and authorization

### Container Security

- Non-root user execution
- Read-only file systems where possible
- Resource limits
- Security scanning

## Troubleshooting

### Common Issues

#### GPU Not Detected
```bash
# Check GPU devices
ls -la /dev/dri/
# Ensure render group access
groups $USER
```

#### NPU Not Available
```bash
# Check NPU devices
ls -la /dev/accel/
# Verify NPU drivers
lspci | grep -i neural
```

#### Service Health Check Failing
```bash
# Check service logs
docker-compose logs intel-ai-full

# Verify configuration
curl -v http://localhost:8000/healthz

# Check Intel profile
curl http://localhost:8000/api/v1/health/configuration
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor Intel hardware
intel_gpu_top  # If available
```

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in docker-compose
environment:
  - LOG_LEVEL=DEBUG
  - DEBUG=true
```

### Getting Support

1. Check logs: `docker-compose logs -f`
2. Verify configuration: `/api/v1/health/configuration`
3. Test hardware: `/api/v1/health/hardware`
4. Review deployment validation results

## Performance Optimization

### Intel Hardware Optimization

The deployment automatically configures:
- Intel MKL optimizations
- OpenVINO device selection
- GPU memory management
- NPU model placement

### Model Optimization

- Automatic model quantization (INT4/INT8)
- Device-specific model selection
- Batch size optimization
- Context length management

### System Optimization

- Container resource limits
- Nginx caching
- Database connection pooling
- Redis session management

## Maintenance

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d
```

### Backups

```bash
# Database backup
docker-compose exec postgres pg_dump -U ai_user intel_ai_assistant > backup.sql

# Model cache backup
docker-compose exec intel-ai-full tar -czf models_backup.tar.gz /app/models
```

### Monitoring

Regular checks:
- Service health endpoints
- Resource utilization
- Log file sizes
- Database performance

## License

This deployment configuration is part of the Intel AI Assistant project and follows the same licensing terms.

## Contributing

For deployment improvements and configurations:
1. Test changes in development environment
2. Validate with multiple Intel hardware configurations
3. Update documentation
4. Submit pull request with deployment validation results