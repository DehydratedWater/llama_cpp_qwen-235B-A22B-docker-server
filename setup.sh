#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

echo "Qwen3-235B Docker Setup"
echo "======================="
echo

print_header "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
else
    echo "✅ Docker found: $(docker --version)"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "   Please install Docker Compose first"
    exit 1
else
    echo "✅ Docker Compose found: $(docker-compose --version)"
fi

# Check NVIDIA Docker
if docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA Docker is working"
else
    echo "❌ NVIDIA Docker is not working"
    echo "   Please install nvidia-docker2 and restart Docker daemon"
    exit 1
fi

echo

print_header "Setting up configuration..."

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Created .env from .env.example"
    else
        print_warning ".env.example not found"
        exit 1
    fi
else
    print_info ".env already exists"
fi

echo

print_header "GPU Information:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader,nounits | while read line; do
        echo "  GPU $line"
    done
else
    print_warning "nvidia-smi not found"
fi

echo

print_header "Next steps:"
echo "1. Edit .env file to configure your model path and GPU settings:"
echo "   nano .env"
echo
echo "2. Update the MODEL_PATH to point to your Qwen3-235B model:"
echo "   MODEL_PATH=/your/path/to/Qwen3-235B-A22B-Instruct-2507-Q2_K_L-00001-of-00002.gguf"
echo
echo "3. Adjust TENSOR_SPLIT based on your GPU memory:"
echo "   Example: TENSOR_SPLIT=24,24,24,16.8  # for 3x24GB + 1x16GB A4000"
echo
echo "4. Start the server:"
echo "   ./start.sh"
echo
echo "5. Test the setup:"
echo "   ./test.sh"
echo

print_info "Setup completed! Edit .env and run ./start.sh to begin."