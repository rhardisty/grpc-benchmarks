# Build from repository root so proto/ and python/ match setup.py layout.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /workspace
COPY proto /workspace/proto
COPY python /workspace/python

WORKDIR /workspace/python
RUN pip install --upgrade pip setuptools wheel \
    && pip install .

EXPOSE 50051

# Overridden by docker-compose (python-server vs python-client; use --profile python).
CMD ["python", "-m", "python_grpc_benchmark.server", "--listen", "0.0.0.0:50051"]
