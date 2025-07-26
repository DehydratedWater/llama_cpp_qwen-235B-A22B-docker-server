# Qwen3-235B Multi-GPU Docker Server

A standalone Docker setup for running the Qwen3-235B-A22B-Instruct model with multi-GPU support, flash attention, and 80k context length.

## Features

- ✅ **Multi-GPU Support** with custom tensor splitting
- ✅ **Flash Attention** for improved performance
- ✅ **80k Context Length** (81,920 tokens)
- ✅ **Optimized for A4000 + Multi-GPU** setups
- ✅ **OpenAI-Compatible API**
- ✅ **Continuous Batching** for concurrent requests
- ✅ **Health Monitoring** and automatic restarts

## Quick Start

1. **Clone/Extract this project:**
   ```bash
   cd /path/to/qwen3-235b-docker
   ```

2. **Configure your setup:**
   ```bash
   cp .env.example .env
   # Edit .env file to match your model path and GPU configuration
   ```

3. **Start the server:**
   ```bash
   ./start.sh
   ```

4. **Test the setup:**
   ```bash
   ./test.sh
   ```

5. **Stop the server:**
   ```bash
   ./stop.sh
   ```

## Configuration

### Model Path

Edit the `.env` file and set your model path:

```bash
MODEL_PATH=/your/path/to/Qwen3-235B-A22B-Instruct-2507-GGUF/Q2_K_L/Qwen3-235B-A22B-Instruct-2507-Q2_K_L-00001-of-00002.gguf
```

### GPU Configuration

Adjust the tensor split based on your GPU setup:

```bash
# Example for 3x24GB + 1x16GB A4000 (at 0.7 capacity)
TENSOR_SPLIT=24,24,24,16.8

# Example for 2x24GB GPUs
TENSOR_SPLIT=24,24

# Example for 4x24GB GPUs
TENSOR_SPLIT=24,24,24,24
```

### Performance Tuning

Key settings in `.env`:

- `CONTEXT_SIZE`: Context window size (default: 81920 for 80k)
- `THREADS`: CPU threads for processing (default: 16)
- `PARALLEL_REQUESTS`: Concurrent request slots (default: 4)
- `FLASH_ATTENTION`: Enable flash attention (default: true)

## API Usage

The server provides OpenAI-compatible endpoints:

### Chat Completions

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-235b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Text Completions

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-235b",
    "prompt": "The future of AI is",
    "max_tokens": 100
  }'
```

### Available Endpoints

- `GET /health` - Health check
- `GET /v1/models` - List models
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions

## Docker Commands

### Manual Docker Operations

```bash
# Build the image
docker-compose build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Resource Monitoring

```bash
# Monitor GPU usage
nvidia-smi -l 1

# Monitor container resources
docker stats

# Check container logs
docker-compose logs --tail=50
```

## Requirements

- **Docker** (19.03+) with GPU support
- **NVIDIA GPUs** with CUDA support
- **Sufficient GPU memory** for the model (recommend 64GB+ total)
- **Model files** accessible on the host system

## Troubleshooting

### Common Issues

1. **Out of Memory:**
   - Reduce `CONTEXT_SIZE` in `.env`
   - Adjust `TENSOR_SPLIT` for your GPUs
   - Ensure total GPU memory > model size

2. **Model Not Found:**
   - Check `MODEL_PATH` in `.env`
   - Verify file permissions
   - Ensure model files are accessible to Docker

3. **GPU Not Detected:**
   - Ensure NVIDIA drivers are installed
   - Verify Docker has GPU support: `docker run --rm --gpus all nvidia/cuda:12.9.1-base nvidia-smi`
   - For older Docker versions, install nvidia-docker2: `sudo apt install nvidia-docker2`

4. **Service Won't Start:**
   - Check logs: `docker-compose logs`
   - Verify .env configuration
   - Ensure port 8080 is available

### Performance Tips

- Use `--no-mmap` (enabled by default) for better performance
- Adjust `THREADS` based on your CPU cores
- Monitor GPU memory usage and adjust tensor split
- Use SSD storage for model files

## File Structure

```
qwen3-235b-docker/
├── Dockerfile              # Multi-stage build with CUDA support
├── docker-compose.yml      # Service configuration
├── docker-entrypoint.sh    # Smart startup script
├── .env.example            # Configuration template
├── start.sh               # Easy start script
├── stop.sh                # Easy stop script
├── test.sh                # Test the setup
└── README.md              # This file
```

## License

This project uses llama.cpp which is licensed under the MIT License.