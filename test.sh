#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "Testing Qwen3-235B Docker Setup"
echo "================================"

# Check if service is running
if ! curl -s http://localhost:8080/health > /dev/null; then
    print_error "Service is not running or not accessible on localhost:8080"
    print_info "Start the service with: ./start.sh"
    exit 1
fi

# Test health endpoint
print_status "Testing health endpoint..."
health_response=$(curl -s http://localhost:8080/health)
echo "Health response: $health_response"

# Test models endpoint
print_status "Testing models endpoint..."
models_response=$(curl -s http://localhost:8080/v1/models)
echo "Models response: $models_response"

# Test chat completion
print_status "Testing chat completion..."
chat_response=$(curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-235b",
    "messages": [{"role": "user", "content": "Hello! Please respond with exactly 5 words."}],
    "max_tokens": 20,
    "temperature": 0.1
  }')

echo "Chat response: $chat_response"

# Check GPU usage
if command -v nvidia-smi &> /dev/null; then
    print_status "Current GPU usage:"
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
fi

# Show recent container logs
print_status "Recent container logs:"
docker-compose logs --tail=10

print_status "Test completed successfully!"
print_status "API is ready for use on http://localhost:8080"