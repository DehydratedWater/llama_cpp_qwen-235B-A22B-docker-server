FROM nvidia/cuda:12.3.2-devel-ubuntu22.04 AS env-build

WORKDIR /srv

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    pciutils \
    build-essential \
    cmake \
    curl \
    libcurl4-openssl-dev \
    git \
    libgomp1 \
    python3 \
    python3-pip \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone and compile llama.cpp with your specific configuration
RUN git clone https://github.com/ggml-org/llama.cpp \
  && cmake llama.cpp -B llama.cpp/build \
    -DBUILD_SHARED_LIBS=OFF \
    -DGGML_CUDA=ON \
    -DLLAMA_CURL=ON \
  && cmake --build llama.cpp/build --config Release -j --clean-first --target llama-cli llama-server llama-gguf-split \
  && cp llama.cpp/build/bin/llama-* llama.cpp

FROM ubuntu:22.04 AS env-deploy

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy CUDA and OpenMP libraries
ENV LD_LIBRARY_PATH=/usr/local/lib
COPY --from=0 /usr/lib/x86_64-linux-gnu/libgomp.so.1 ${LD_LIBRARY_PATH}/libgomp.so.1
COPY --from=0 /usr/local/cuda/lib64/libcublas.so.12 ${LD_LIBRARY_PATH}/libcublas.so.12
COPY --from=0 /usr/local/cuda/lib64/libcublasLt.so.12 ${LD_LIBRARY_PATH}/libcublasLt.so.12
COPY --from=0 /usr/local/cuda/lib64/libcudart.so.12 ${LD_LIBRARY_PATH}/libcudart.so.12
COPY --from=0 /usr/local/cuda/lib64/libcurand.so.10 ${LD_LIBRARY_PATH}/libcurand.so.10

# Copy llama.cpp binaries
COPY --from=0 /srv/llama.cpp/llama-cli /usr/local/bin/llama-cli
COPY --from=0 /srv/llama.cpp/llama-server /usr/local/bin/llama-server
COPY --from=0 /srv/llama.cpp/llama-gguf-split /usr/local/bin/llama-gguf-split

# Create llama user and set home directory
RUN useradd --system --create-home llama

# Create models directory
RUN mkdir -p /home/llama/models && chown llama:llama /home/llama/models

USER llama
WORKDIR /home/llama

EXPOSE 8080

# Copy and set entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]