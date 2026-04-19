# C++ gRPC benchmark

Same streaming RPC as the Python tool: `ServerStream` using repo-root `proto/benchmark.proto`.

## Run with Docker (recommended if you have no local C++ toolchain)

From the **repository root**:

```bash
docker build -f cpp/Dockerfile -t grpc-benchmark:cpp .
docker run --rm -p 50051:50051 grpc-benchmark:cpp
```

In another terminal:

```bash
docker run --rm --network host grpc-benchmark:cpp grpc_benchmark_client --target 127.0.0.1:50051
```

On **Docker Desktop (Windows/macOS)**, use a user-defined network instead of `host`:

```bash
docker network create grpcbench
docker run -d --name cpp-server --network grpcbench -p 50051:50051 grpc-benchmark:cpp
docker run --rm --network grpcbench grpc-benchmark:cpp grpc_benchmark_client --target cpp-server:50051
docker stop cpp-server && docker rm cpp-server && docker network rm grpcbench
```

**Compose** (from the **repository root**; root `docker-compose.yml` — use the `cpp` profile):

```bash
docker compose --profile cpp up --build
```

**C++ server in the background**, then run the client on demand:

```bash
docker compose --profile cpp up -d cpp-server --build
docker compose --profile cpp run --rm cpp-client grpc_benchmark_client --target cpp-server:50051
```

The server is published on host **localhost:50051** (same as the Python stack; run only one profile at a time).

## Build locally (optional)

Requires CMake 3.20+, gRPC C++, and Protobuf (e.g. via [vcpkg](https://github.com/microsoft/vcpkg)). From `cpp/`: `cmake -B build -S .` then `cmake --build build` (after installing dependencies). If you only use Docker, you can skip this.

Binaries:

- `grpc_benchmark_server` — `--listen HOST:PORT` (default `[::]:50051`)
- `grpc_benchmark_client` — `--target`, `--response-size`, `--max-size-bytes`, `--sequence`, `--timeout` (same defaults as Python: 4 MiB chunk, 5 GiB cap)

Throughput logging matches the Python client (decimal Gbps).
