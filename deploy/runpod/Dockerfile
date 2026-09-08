FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /workspace

# Install vLLM
RUN pip install --no-cache-dir vllm fastapi uvicorn

# Copy handler
COPY handler.py /workspace/handler.py

# Expose port
EXPOSE 8000

# Run
CMD ["python", "/workspace/handler.py"]