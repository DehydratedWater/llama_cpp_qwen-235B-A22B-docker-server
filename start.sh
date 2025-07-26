#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project directory."
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning ".env file not found. Creating from .env.example"
        cp .env.example .env
        print_info "Please edit .env file to match your configuration, then run this script again."
        exit 1
    else
        print_error "Neither .env nor .env.example found."
        exit 1
    fi
fi

# Check prerequisites
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check NVIDIA Docker GPU support  
print_info "Testing GPU access through Docker..."
if ! nvidia-smi &> /dev/null; then
    print_error "NVIDIA drivers not working properly"
    exit 1
fi

print_info "Starting Qwen3-235B Docker service..."

# Build and start
docker compose up --build

print_info "Service started! Waiting for it to be ready..."

# Wait for service
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_info "Service is ready!"
        echo
        print_info "API endpoints:"
        echo "  Health: http://localhost:8080/health"
        echo "  Chat: http://localhost:8080/v1/chat/completions"
        echo "  Models: http://localhost:8080/v1/models"
        echo
        print_info "To stop the service: ./stop.sh"
        print_info "To view logs: docker-compose logs -f"
        break
    fi
    
    if [ $attempt -eq $((max_attempts - 1)) ]; then
        print_error "Service failed to start within timeout"
        print_info "Check logs with: docker-compose logs"
        exit 1
    fi
    
    sleep 5
    ((attempt++))
    echo -n "."
done