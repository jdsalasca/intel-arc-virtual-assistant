#!/bin/bash
# Intel AI Assistant Deployment Script
# Automated deployment with Intel hardware detection and optimization

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOYMENT_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect Intel hardware
detect_intel_hardware() {
    log_info "Detecting Intel hardware..."
    
    # Initialize hardware flags
    INTEL_CPU=false
    INTEL_GPU=false
    INTEL_NPU=false
    
    # Detect Intel CPU
    if lscpu | grep -q "Intel"; then
        INTEL_CPU=true
        CPU_MODEL=$(lscpu | grep "Model name" | sed 's/Model name://g' | xargs)
        log_success "Intel CPU detected: $CPU_MODEL"
    fi
    
    # Detect Intel GPU (Arc)
    if lspci | grep -i "intel.*arc\|intel.*xe"; then
        INTEL_GPU=true
        GPU_MODEL=$(lspci | grep -i "intel.*arc\|intel.*xe" | head -1)
        log_success "Intel GPU detected: $GPU_MODEL"
    elif lspci | grep -i "intel.*graphics"; then
        INTEL_GPU=true
        GPU_MODEL=$(lspci | grep -i "intel.*graphics" | head -1)
        log_success "Intel integrated graphics detected: $GPU_MODEL"
    fi
    
    # Detect Intel NPU (simplified check)
    if lspci | grep -i "neural\|npu" || dmesg | grep -i "intel.*npu"; then
        INTEL_NPU=true
        log_success "Intel NPU detected"
    fi
    
    # Determine deployment profile
    if $INTEL_CPU && $INTEL_GPU && $INTEL_NPU; then
        DEPLOYMENT_PROFILE="full"
        log_success "Full Intel hardware stack detected"
    elif $INTEL_CPU && $INTEL_GPU; then
        DEPLOYMENT_PROFILE="gpu"
        log_success "Intel CPU + GPU configuration detected"
    elif $INTEL_CPU && $INTEL_NPU; then
        DEPLOYMENT_PROFILE="npu"
        log_success "Intel CPU + NPU configuration detected"
    elif $INTEL_CPU; then
        DEPLOYMENT_PROFILE="cpu"
        log_success "Intel CPU-only configuration detected"
    else
        DEPLOYMENT_PROFILE="cpu"
        log_warning "No Intel hardware detected, using CPU-only profile"
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    local requirements_met=true
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker is not installed"
        requirements_met=false
    else
        DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+')
        log_success "Docker $DOCKER_VERSION is installed"
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not installed"
        requirements_met=false
    else
        log_success "Docker Compose is available"
    fi
    
    # Check available disk space (minimum 10GB)
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=$((10 * 1024 * 1024)) # 10GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space. Required: 10GB, Available: $((AVAILABLE_SPACE / 1024 / 1024))GB"
        requirements_met=false
    else
        log_success "Sufficient disk space available: $((AVAILABLE_SPACE / 1024 / 1024))GB"
    fi
    
    # Check available RAM (minimum 8GB)
    AVAILABLE_RAM=$(free -m | awk 'NR==2{print $2}')
    REQUIRED_RAM=8192 # 8GB in MB
    
    if [ "$AVAILABLE_RAM" -lt "$REQUIRED_RAM" ]; then
        log_warning "Low RAM detected. Required: 8GB, Available: $((AVAILABLE_RAM / 1024))GB"
    else
        log_success "Sufficient RAM available: $((AVAILABLE_RAM / 1024))GB"
    fi
    
    if ! $requirements_met; then
        log_error "System requirements not met. Please install missing dependencies."
        exit 1
    fi
}

# Setup environment
setup_environment() {
    log_info "Setting up deployment environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create necessary directories
    mkdir -p models cache data logs
    
    # Set permissions
    chmod 755 models cache data logs
    
    # Create .env file for production
    cat > .env.production << EOF
# Intel AI Assistant Production Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Intel Hardware Configuration
INTEL_CPU=$INTEL_CPU
INTEL_GPU=$INTEL_GPU
INTEL_NPU=$INTEL_NPU
DEPLOYMENT_PROFILE=$DEPLOYMENT_PROFILE

# Model Configuration
MODEL_CACHE_DIR=/app/models
OPENVINO_CACHE_DIR=/app/cache

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Performance Configuration
MKL_NUM_THREADS=0
OMP_NUM_THREADS=0
INTEL_MKL_ENABLE_INSTRUCTIONS=AVX2

# Security (generate in production)
API_KEY_REQUIRED=false
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60

# Data Storage
CONVERSATIONS_DIR=/app/data/conversations
AUTO_SAVE_INTERVAL=30

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9000
EOF
    
    log_success "Environment configuration created"
}

# Build Docker images
build_images() {
    log_info "Building Docker images for deployment profile: $DEPLOYMENT_PROFILE"
    
    cd "$PROJECT_ROOT"
    
    # Build the appropriate image based on detected hardware
    case $DEPLOYMENT_PROFILE in
        "full")
            docker-compose -f deployment/docker-compose.yml build intel-ai-full
            ;;
        "gpu")
            docker-compose -f deployment/docker-compose.yml build intel-ai-gpu
            ;;
        "npu")
            docker-compose -f deployment/docker-compose.yml build intel-ai-npu
            ;;
        "cpu")
            docker-compose -f deployment/docker-compose.yml build intel-ai-cpu
            ;;
    esac
    
    log_success "Docker image built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying Intel AI Assistant services..."
    
    cd "$PROJECT_ROOT"
    
    # Use the appropriate profile
    COMPOSE_PROFILES="production,$DEPLOYMENT_PROFILE"
    
    # Add monitoring if requested
    if [ "${ENABLE_MONITORING:-false}" = "true" ]; then
        COMPOSE_PROFILES="$COMPOSE_PROFILES,monitoring"
    fi
    
    # Add high availability if requested
    if [ "${ENABLE_HA:-false}" = "true" ]; then
        COMPOSE_PROFILES="$COMPOSE_PROFILES,ha"
    fi
    
    export COMPOSE_PROFILES
    
    # Deploy services
    docker-compose -f deployment/docker-compose.yml up -d
    
    log_success "Services deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/healthz >/dev/null 2>&1; then
            log_success "Services are ready!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Services failed to start within the expected time"
    return 1
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    # Check service status
    if ! docker-compose -f deployment/docker-compose.yml ps | grep -q "Up"; then
        log_error "Some services are not running"
        return 1
    fi
    
    # Check API health
    if ! curl -f http://localhost:8000/healthz >/dev/null 2>&1; then
        log_error "API health check failed"
        return 1
    fi
    
    # Check hardware configuration
    local hardware_info
    hardware_info=$(curl -s http://localhost:8000/api/v1/health/hardware || echo "{}")
    
    if [ "$hardware_info" != "{}" ]; then
        log_success "Hardware information retrieved successfully"
    else
        log_warning "Could not retrieve hardware information"
    fi
    
    # Check Intel profile
    local config_info
    config_info=$(curl -s http://localhost:8000/api/v1/health/configuration || echo "{}")
    
    if echo "$config_info" | grep -q "current_profile"; then
        local current_profile
        current_profile=$(echo "$config_info" | jq -r '.current_profile // "unknown"')
        log_success "Intel profile configured: $current_profile"
    else
        log_warning "Could not retrieve Intel profile information"
    fi
    
    log_success "Deployment validation completed"
}

# Show deployment information
show_deployment_info() {
    log_info "Deployment Information"
    echo "=========================="
    echo "Deployment Profile: $DEPLOYMENT_PROFILE"
    echo "Intel CPU: $INTEL_CPU"
    echo "Intel GPU: $INTEL_GPU"
    echo "Intel NPU: $INTEL_NPU"
    echo ""
    echo "Services:"
    docker-compose -f deployment/docker-compose.yml ps
    echo ""
    echo "Access URLs:"
    echo "  Main API: http://localhost:8000"
    echo "  Health Check: http://localhost:8000/healthz"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Hardware Info: http://localhost:8000/api/v1/health/hardware"
    echo ""
    
    if [ "${ENABLE_MONITORING:-false}" = "true" ]; then
        echo "Monitoring:"
        echo "  Prometheus: http://localhost:9090"
        echo "  Grafana: http://localhost:3000 (admin/admin)"
        echo ""
    fi
    
    echo "Logs:"
    echo "  View logs: docker-compose -f deployment/docker-compose.yml logs -f"
    echo "  Stop services: docker-compose -f deployment/docker-compose.yml down"
    echo ""
}

# Main deployment function
main() {
    log_info "Starting Intel AI Assistant deployment..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                DEPLOYMENT_PROFILE="$2"
                shift 2
                ;;
            --monitoring)
                ENABLE_MONITORING=true
                shift
                ;;
            --ha)
                ENABLE_HA=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --help)
                echo "Intel AI Assistant Deployment Script"
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --profile PROFILE    Force deployment profile (cpu|gpu|npu|full)"
                echo "  --monitoring         Enable monitoring (Prometheus + Grafana)"
                echo "  --ha                 Enable high availability (Load balancer + Redis + PostgreSQL)"
                echo "  --skip-build         Skip Docker image building"
                echo "  --help               Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                           # Auto-detect hardware and deploy"
                echo "  $0 --profile full --monitoring  # Force full profile with monitoring"
                echo "  $0 --ha                      # Deploy with high availability"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Detect hardware if profile not specified
    if [ -z "${DEPLOYMENT_PROFILE:-}" ]; then
        detect_intel_hardware
    else
        log_info "Using specified deployment profile: $DEPLOYMENT_PROFILE"
    fi
    
    # Run deployment steps
    check_requirements
    setup_environment
    
    if [ "${SKIP_BUILD:-false}" != "true" ]; then
        build_images
    fi
    
    deploy_services
    wait_for_services
    validate_deployment
    show_deployment_info
    
    log_success "Intel AI Assistant deployment completed successfully!"
}

# Run main function with all arguments
main "$@"