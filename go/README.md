# Go gRPC benchmark

[`google.golang.org/grpc`](https://pkg.go.dev/google.golang.org/grpc) implementation of `proto/benchmark.proto` (`ServerStream`).

## Docker (no local Go toolchain)

From the **repository root**:

```bash
docker build -f go/Dockerfile -t grpc-benchmark:go .
docker run --rm -p 50051:50051 grpc-benchmark:go
```

**Compose** (root `docker-compose.yml`, `go` profile only — same host port **50051** as other stacks; run one profile at a time):

```bash
docker compose --profile go up --build
```

Binaries:

- `grpc_benchmark_server` — `-listen HOST:PORT` (default `[::]:50051`; `--listen` accepted for parity with other CLIs)
- `grpc_benchmark_client` — `-target`, `-response-size`, `-max-size-bytes`, `-sequence` (defaults match Python/C++/Rust; `--flag` long form works)

Throughput log line matches the other clients (decimal Gbps).

## Local build (optional)

Install Go 1.22+, `protoc`, and the plugins:

```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

From `go/`, generate stubs and build:

```bash
mkdir -p gen/benchmarkpb
protoc -I ../proto \
  --go_out=gen/benchmarkpb --go_opt=paths=source_relative \
  --go-grpc_out=gen/benchmarkpb --go-grpc_opt=paths=source_relative \
  ../proto/benchmark.proto
go mod tidy
go build -o grpc_benchmark_server ./cmd/grpc_benchmark_server
go build -o grpc_benchmark_client ./cmd/grpc_benchmark_client
```
