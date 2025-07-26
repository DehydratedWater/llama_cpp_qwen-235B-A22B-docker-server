#!/bin/bash

set -eu

# Set default environment variables if not provided
set_default_env_vars() {
  # Host and port
  if [ -z ${LLAMA_ARG_HOST+x} ]; then
    export LLAMA_ARG_HOST="0.0.0.0"
  fi
  if [ -z ${LLAMA_ARG_PORT+x} ]; then
    export LLAMA_ARG_PORT="8080"
  fi
  
  # Model path (required)
  if [ -z ${LLAMA_ARG_MODEL+x} ]; then
    echo "Error: LLAMA_ARG_MODEL environment variable is required"
    exit 1
  fi
  
  # Context size for 80k context
  if [ -z ${LLAMA_ARG_CTX_SIZE+x} ]; then
    export LLAMA_ARG_CTX_SIZE="81920"
  fi
  
  # Batch settings optimized for large context
  if [ -z ${LLAMA_ARG_BATCH_SIZE+x} ]; then
    export LLAMA_ARG_BATCH_SIZE="2048"
  fi
  if [ -z ${LLAMA_ARG_UBATCH_SIZE+x} ]; then
    export LLAMA_ARG_UBATCH_SIZE="512"
  fi
  
  # GPU settings
  if [ -z ${LLAMA_ARG_N_GPU_LAYERS+x} ]; then
    export LLAMA_ARG_N_GPU_LAYERS="-1"  # Offload all layers
  fi
  
  # Flash attention
  if [ -z ${LLAMA_ARG_FLASH_ATTN+x} ]; then
    export LLAMA_ARG_FLASH_ATTN="true"
  fi
  
  # Memory settings
  if [ -z ${LLAMA_ARG_NO_MMAP+x} ]; then
    export LLAMA_ARG_NO_MMAP="true"
  fi
  if [ -z ${LLAMA_ARG_MLOCK+x} ]; then
    export LLAMA_ARG_MLOCK="true"
  fi
  
  # Threading
  if [ -z ${LLAMA_ARG_THREADS+x} ]; then
    export LLAMA_ARG_THREADS="16"
  fi
  if [ -z ${LLAMA_ARG_THREADS_BATCH+x} ]; then
    export LLAMA_ARG_THREADS_BATCH="16"
  fi
  
  # API settings for multiple concurrent requests
  if [ -z ${LLAMA_ARG_PARALLEL+x} ]; then
    export LLAMA_ARG_PARALLEL="4"
  fi
  if [ -z ${LLAMA_ARG_CONT_BATCHING+x} ]; then
    export LLAMA_ARG_CONT_BATCHING="true"
  fi
  
  # Generation settings
  if [ -z ${LLAMA_ARG_N_PREDICT+x} ]; then
    export LLAMA_ARG_N_PREDICT="-1"  # Unlimited
  fi
}

# Function to build llama-server arguments from environment variables
build_args() {
  local args=()
  
  # Add arguments based on environment variables
  for var in $(env | grep '^LLAMA_ARG_' | cut -d= -f1); do
    local arg_name=$(echo "$var" | sed 's/^LLAMA_ARG_//' | tr '[:upper:]' '[:lower:]' | tr '_' '-')
    local arg_value=$(eval echo \$$var)
    
    if [ "$arg_value" = "true" ]; then
      args+=("--$arg_name")
    elif [ "$arg_value" = "false" ]; then
      # Skip false boolean values
      continue
    else
      args+=("--$arg_name" "$arg_value")
    fi
  done
  
  echo "${args[@]}"
}

# Validate GPU setup
validate_gpu_setup() {
  if command -v nvidia-smi &> /dev/null; then
    echo "GPU Information:"
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader,nounits
    echo
  else
    echo "Warning: nvidia-smi not found. GPU may not be available."
  fi
}

# Check if model file exists
check_model_file() {
  if [ ! -f "$LLAMA_ARG_MODEL" ]; then
    echo "Error: Model file not found at $LLAMA_ARG_MODEL"
    echo "Available model files in /home/llama/models:"
    find /home/llama/models -name "*.gguf" -type f 2>/dev/null || echo "No .gguf files found"
    exit 1
  fi
  echo "Using model: $LLAMA_ARG_MODEL"
}

# Main execution
echo "Starting Qwen3-235B Multi-GPU Server..."
echo "========================================"

set_default_env_vars
validate_gpu_setup
check_model_file

# Build arguments array
server_args=$(build_args)

echo "Server configuration:"
echo "Host: $LLAMA_ARG_HOST"
echo "Port: $LLAMA_ARG_PORT"
echo "Context Size: $LLAMA_ARG_CTX_SIZE"
echo "Flash Attention: $LLAMA_ARG_FLASH_ATTN"
echo "GPU Layers: $LLAMA_ARG_N_GPU_LAYERS"
if [ -n "${LLAMA_ARG_TENSOR_SPLIT+x}" ]; then
  echo "Tensor Split: $LLAMA_ARG_TENSOR_SPLIT"
fi
echo "========================================"

# Start the server
set -x
exec llama-server $server_args