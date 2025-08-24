# Intel AI Assistant Windows Deployment Script
# PowerShell script for automated deployment with Intel hardware detection

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("cpu", "gpu", "npu", "full")]
    [string]$Profile,
    
    [Parameter(Mandatory=$false)]
    [switch]$Monitoring,
    
    [Parameter(Mandatory=$false)]
    [switch]$HighAvailability,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DeploymentDir = $ScriptDir

# Initialize variables
$IntelCPU = $false
$IntelGPU = $false
$IntelNPU = $false
$DeploymentProfile = ""

# Logging functions
function Write-InfoLog {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-SuccessLog {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-WarningLog {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorLog {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Show help information
function Show-Help {
    Write-Host "Intel AI Assistant Windows Deployment Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -Profile PROFILE     Force deployment profile (cpu|gpu|npu|full)" -ForegroundColor Gray
    Write-Host "  -Monitoring          Enable monitoring (Prometheus + Grafana)" -ForegroundColor Gray
    Write-Host "  -HighAvailability    Enable high availability setup" -ForegroundColor Gray
    Write-Host "  -SkipBuild           Skip Docker image building" -ForegroundColor Gray
    Write-Host "  -Help                Show this help message" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\deploy.ps1                                    # Auto-detect hardware and deploy" -ForegroundColor Gray
    Write-Host "  .\deploy.ps1 -Profile full -Monitoring         # Force full profile with monitoring" -ForegroundColor Gray
    Write-Host "  .\deploy.ps1 -HighAvailability                 # Deploy with high availability" -ForegroundColor Gray
    exit 0
}

# Check if command exists
function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Detect Intel hardware using Windows tools
function Get-IntelHardware {
    Write-InfoLog "Detecting Intel hardware..."
    
    # Detect Intel CPU
    try {
        $cpuInfo = Get-WmiObject -Class Win32_Processor | Where-Object { $_.Manufacturer -like "*Intel*" }
        if ($cpuInfo) {
            $script:IntelCPU = $true
            $cpuModel = $cpuInfo.Name
            Write-SuccessLog "Intel CPU detected: $cpuModel"
        }
    }
    catch {
        Write-WarningLog "Could not detect CPU information"
    }
    
    # Detect Intel GPU
    try {
        $gpuInfo = Get-WmiObject -Class Win32_VideoController | Where-Object { 
            $_.Name -like "*Intel*" -and ($_.Name -like "*Arc*" -or $_.Name -like "*Xe*" -or $_.Name -like "*Graphics*")
        }
        if ($gpuInfo) {
            $script:IntelGPU = $true
            $gpuModel = $gpuInfo.Name
            Write-SuccessLog "Intel GPU detected: $gpuModel"
        }
    }
    catch {
        Write-WarningLog "Could not detect GPU information"
    }
    
    # Detect Intel NPU (simplified detection)
    try {
        $npuInfo = Get-WmiObject -Class Win32_PnPEntity | Where-Object { 
            $_.Name -like "*NPU*" -or $_.Name -like "*Neural*" -or $_.DeviceID -like "*VEN_8086*NPU*"
        }
        if ($npuInfo) {
            $script:IntelNPU = $true
            Write-SuccessLog "Intel NPU detected"
        }
    }
    catch {
        Write-WarningLog "Could not detect NPU information"
    }
    
    # Determine deployment profile
    if ($script:IntelCPU -and $script:IntelGPU -and $script:IntelNPU) {
        $script:DeploymentProfile = "full"
        Write-SuccessLog "Full Intel hardware stack detected"
    }
    elseif ($script:IntelCPU -and $script:IntelGPU) {
        $script:DeploymentProfile = "gpu"
        Write-SuccessLog "Intel CPU + GPU configuration detected"
    }
    elseif ($script:IntelCPU -and $script:IntelNPU) {
        $script:DeploymentProfile = "npu"
        Write-SuccessLog "Intel CPU + NPU configuration detected"
    }
    elseif ($script:IntelCPU) {
        $script:DeploymentProfile = "cpu"
        Write-SuccessLog "Intel CPU-only configuration detected"
    }
    else {
        $script:DeploymentProfile = "cpu"
        Write-WarningLog "No Intel hardware detected, using CPU-only profile"
    }
}

# Check system requirements
function Test-SystemRequirements {
    Write-InfoLog "Checking system requirements..."
    
    $requirementsMet = $true
    
    # Check Docker
    if (-not (Test-CommandExists "docker")) {
        Write-ErrorLog "Docker is not installed"
        $requirementsMet = $false
    }
    else {
        $dockerVersion = (docker --version) -replace '.*?(\d+\.\d+\.\d+).*', '$1'
        Write-SuccessLog "Docker $dockerVersion is installed"
    }
    
    # Check Docker Compose
    if (-not (Test-CommandExists "docker-compose") -and -not (docker compose version 2>$null)) {
        Write-ErrorLog "Docker Compose is not available"
        $requirementsMet = $false
    }
    else {
        Write-SuccessLog "Docker Compose is available"
    }
    
    # Check available disk space (minimum 10GB)
    try {
        $drive = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "C:" }
        $availableSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
        
        if ($availableSpaceGB -lt 10) {
            Write-ErrorLog "Insufficient disk space. Required: 10GB, Available: ${availableSpaceGB}GB"
            $requirementsMet = $false
        }
        else {
            Write-SuccessLog "Sufficient disk space available: ${availableSpaceGB}GB"
        }
    }
    catch {
        Write-WarningLog "Could not check disk space"
    }
    
    # Check available RAM (minimum 8GB)
    try {
        $totalRAM = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory
        $totalRAMGB = [math]::Round($totalRAM / 1GB, 2)
        
        if ($totalRAMGB -lt 8) {
            Write-WarningLog "Low RAM detected. Required: 8GB, Available: ${totalRAMGB}GB"
        }
        else {
            Write-SuccessLog "Sufficient RAM available: ${totalRAMGB}GB"
        }
    }
    catch {
        Write-WarningLog "Could not check RAM information"
    }
    
    if (-not $requirementsMet) {
        Write-ErrorLog "System requirements not met. Please install missing dependencies."
        exit 1
    }
}

# Setup deployment environment
function Initialize-Environment {
    Write-InfoLog "Setting up deployment environment..."
    
    Set-Location $ProjectRoot
    
    # Create necessary directories
    $directories = @("models", "cache", "data", "logs")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    # Create production environment file
    $envContent = @"
# Intel AI Assistant Production Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Intel Hardware Configuration
INTEL_CPU=$IntelCPU
INTEL_GPU=$IntelGPU
INTEL_NPU=$IntelNPU
DEPLOYMENT_PROFILE=$DeploymentProfile

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
"@
    
    $envContent | Out-File -FilePath ".env.production" -Encoding UTF8
    
    Write-SuccessLog "Environment configuration created"
}

# Build Docker images
function Build-DockerImages {
    Write-InfoLog "Building Docker images for deployment profile: $DeploymentProfile"
    
    Set-Location $ProjectRoot
    
    try {
        switch ($DeploymentProfile) {
            "full" {
                docker-compose -f deployment/docker-compose.yml build intel-ai-full
            }
            "gpu" {
                docker-compose -f deployment/docker-compose.yml build intel-ai-gpu
            }
            "npu" {
                docker-compose -f deployment/docker-compose.yml build intel-ai-npu
            }
            "cpu" {
                docker-compose -f deployment/docker-compose.yml build intel-ai-cpu
            }
        }
        
        Write-SuccessLog "Docker image built successfully"
    }
    catch {
        Write-ErrorLog "Failed to build Docker image: $_"
        exit 1
    }
}

# Deploy services
function Start-Services {
    Write-InfoLog "Deploying Intel AI Assistant services..."
    
    Set-Location $ProjectRoot
    
    # Configure compose profiles
    $composeProfiles = @("production", $DeploymentProfile)
    
    if ($Monitoring) {
        $composeProfiles += "monitoring"
    }
    
    if ($HighAvailability) {
        $composeProfiles += "ha"
    }
    
    $env:COMPOSE_PROFILES = $composeProfiles -join ","
    
    try {
        docker-compose -f deployment/docker-compose.yml up -d
        Write-SuccessLog "Services deployed successfully"
    }
    catch {
        Write-ErrorLog "Failed to deploy services: $_"
        exit 1
    }
}

# Wait for services to be ready
function Wait-ForServices {
    Write-InfoLog "Waiting for services to be ready..."
    
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-SuccessLog "Services are ready!"
                return
            }
        }
        catch {
            # Service not ready yet
        }
        
        Write-InfoLog "Attempt $attempt/$maxAttempts - waiting for services..."
        Start-Sleep -Seconds 10
        $attempt++
    }
    
    Write-ErrorLog "Services failed to start within the expected time"
    exit 1
}

# Validate deployment
function Test-Deployment {
    Write-InfoLog "Validating deployment..."
    
    # Check service status
    $serviceStatus = docker-compose -f deployment/docker-compose.yml ps
    if (-not ($serviceStatus -match "Up")) {
        Write-ErrorLog "Some services are not running"
        return $false
    }
    
    # Check API health
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing
        if ($healthResponse.StatusCode -ne 200) {
            Write-ErrorLog "API health check failed"
            return $false
        }
    }
    catch {
        Write-ErrorLog "API health check failed: $_"
        return $false
    }
    
    # Check hardware information
    try {
        $hardwareResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/hardware" -UseBasicParsing
        if ($hardwareResponse.StatusCode -eq 200) {
            Write-SuccessLog "Hardware information retrieved successfully"
        }
    }
    catch {
        Write-WarningLog "Could not retrieve hardware information"
    }
    
    # Check Intel profile
    try {
        $configResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/configuration" -UseBasicParsing
        if ($configResponse.StatusCode -eq 200) {
            $configData = $configResponse.Content | ConvertFrom-Json
            if ($configData.current_profile) {
                Write-SuccessLog "Intel profile configured: $($configData.current_profile)"
            }
        }
    }
    catch {
        Write-WarningLog "Could not retrieve Intel profile information"
    }
    
    Write-SuccessLog "Deployment validation completed"
    return $true
}

# Show deployment information
function Show-DeploymentInfo {
    Write-InfoLog "Deployment Information"
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host "Deployment Profile: $DeploymentProfile" -ForegroundColor White
    Write-Host "Intel CPU: $IntelCPU" -ForegroundColor White
    Write-Host "Intel GPU: $IntelGPU" -ForegroundColor White
    Write-Host "Intel NPU: $IntelNPU" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Services:" -ForegroundColor White
    docker-compose -f deployment/docker-compose.yml ps
    Write-Host ""
    
    Write-Host "Access URLs:" -ForegroundColor White
    Write-Host "  Main API: http://localhost:8000" -ForegroundColor Gray
    Write-Host "  Health Check: http://localhost:8000/healthz" -ForegroundColor Gray
    Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "  Hardware Info: http://localhost:8000/api/v1/health/hardware" -ForegroundColor Gray
    Write-Host ""
    
    if ($Monitoring) {
        Write-Host "Monitoring:" -ForegroundColor White
        Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor Gray
        Write-Host "  Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "Management:" -ForegroundColor White
    Write-Host "  View logs: docker-compose -f deployment/docker-compose.yml logs -f" -ForegroundColor Gray
    Write-Host "  Stop services: docker-compose -f deployment/docker-compose.yml down" -ForegroundColor Gray
    Write-Host ""
}

# Main execution function
function Start-Deployment {
    Write-InfoLog "Starting Intel AI Assistant deployment..."
    
    # Show help if requested
    if ($Help) {
        Show-Help
    }
    
    # Use specified profile or auto-detect
    if ($Profile) {
        $script:DeploymentProfile = $Profile
        Write-InfoLog "Using specified deployment profile: $Profile"
    }
    else {
        Get-IntelHardware
    }
    
    # Execute deployment steps
    Test-SystemRequirements
    Initialize-Environment
    
    if (-not $SkipBuild) {
        Build-DockerImages
    }
    
    Start-Services
    Wait-ForServices
    
    if (Test-Deployment) {
        Show-DeploymentInfo
        Write-SuccessLog "Intel AI Assistant deployment completed successfully!"
    }
    else {
        Write-ErrorLog "Deployment validation failed"
        exit 1
    }
}

# Entry point
try {
    Start-Deployment
}
catch {
    Write-ErrorLog "Deployment failed: $_"
    exit 1
}