FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git curl wget python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# serving vLLM for OpenAI API.
RUN pip install --upgrade pip
RUN pip install 'vllm[server]' gdown google-colab

WORKDIR /vLLM

EXPOSE 8000

