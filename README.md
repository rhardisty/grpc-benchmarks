# gRPC benchmark

Shared [Protocol Buffers](https://protobuf.dev/) definitions live in `proto/`. Language-specific servers, clients, and tooling live in subfolders (for example `python/`).

## Layout

- `proto/` — `.proto` sources shared by all language implementations
- `python/` — Python package, install instructions, and `uv` lockfile
- `cpp/` — C++ server and client; build with CMake locally or use **`cpp/Dockerfile`** (no host compiler required)
- `rust/` — Rust server and client (Tonic); build with **`rust/Dockerfile`** (no host Rust toolchain required)
- `go/` — Go server and client (`google.golang.org/grpc`); build with **`go/Dockerfile`** (no host Go toolchain required)

See `python/README.md` for the Python gRPC streaming benchmark, `cpp/README.md` for the C++ image, `rust/README.md` for the Rust image, and `go/README.md` for the Go image. **Compose:** root `docker-compose.yml` requires **`--profile python`**, **`--profile cpp`**, **`--profile rust`**, or **`--profile go`** (enable only one at a time); there is no default stack.

## Benchmark results

Python, C++, Rust, and Go clients log the same way: **application chunk payload** rate (sum of `EchoResponse.chunk` lengths), **decimal Gbps** (10⁹ bit/s), over **wall-clock** time for the streaming RPC (`INFO … Gbps (… chunk bytes in … s)`). Add new rows for other runs.

| Client | Server | Language | Throughput (Gbps) | Chunk size (bytes) | Total size (bytes) | Duration (s) |
|--------|--------|----------|------------------:|-------------------:|-------------------:|-------------:|
| local host | local host | Python |            13.067 | 4194304 | 5368709120 | 3.286764 |

## Docker Compose

From the repository root (where `docker-compose.yml` and `Dockerfile` live), with [Docker Compose](https://docs.docker.com/compose/) available:

**Profiles are required** — `docker compose up` with no profile starts no application services. **Use one profile at a time** — do not combine `python`, `cpp`, `rust`, and `go` profiles; each stack publishes the server on host **50051**, so run one stack, then `docker compose down` before starting another.

**Python** (`python-server`, `python-client`; client exits after `max_size_bytes`; Compose stops when the client exits):

```bash
docker compose --profile python up --build
```

**Python server in the background**, then run the client on demand:

```bash
docker compose --profile python up -d python-server --build
docker compose --profile python run --rm python-client python -m python_grpc_benchmark.client --target python-server:50051 --max-size-bytes 5368709120
```

**Stop and remove containers:**

```bash
docker compose down
```


