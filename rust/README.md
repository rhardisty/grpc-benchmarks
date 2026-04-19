# Rust gRPC benchmark

[Tonic](https://github.com/hyperium/tonic) + [prost](https://github.com/tokio-rs/prost) implementation of the same `ServerStream` API as `proto/benchmark.proto`.

## Docker (no local Rust toolchain)

From the **repository root**:

```bash
docker build -f rust/Dockerfile -t grpc-benchmark:rust .
docker run --rm -p 50051:50051 grpc-benchmark:rust
```

**Compose** (root `docker-compose.yml`, `rust` profile only — same host port **50051** as other stacks; run one profile at a time):

```bash
docker compose --profile rust up --build
```

Binaries:

- `grpc_benchmark_server` — `--listen HOST:PORT` (default `[::]:50051`)
- `grpc_benchmark_client` — `--target`, `--response-size`, `--max-size-bytes`, `--sequence` (defaults match Python/C++)

Throughput log line matches the other clients (decimal Gbps).

## Local build (optional)

Install a **recent stable** Rust toolchain (the Docker image uses **1.85+** because current `clap` / transitive crates need it) and `protobuf-compiler` (`protoc`). From `rust/`:

```bash
cargo build --release
```

Artifacts: `target/release/grpc_benchmark_server`, `target/release/grpc_benchmark_client`.
