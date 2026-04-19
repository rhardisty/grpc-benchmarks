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
| local host | local host | Python   |            13.067 | 4194304 | 5368709120 | 3.286764 |
| local host | local host | C++      |            28.291 | 4194304 | 5368709120 | 1.518142 |
| local host | local host | Rust     |            16.686 | 4194304 | 5368709120 | 2.574034 |
| local host | local host | Go       |            19.382 | 4194304 | 5368709120 | 2.21590 |

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

**C++** (`cpp-server`, `cpp-client`; client exits after the stream reaches `max_size_bytes`; Compose stops when the client exits):

```bash
docker compose --profile cpp up --build
```

**C++ server in the background**, then run the client on demand:

```bash
docker compose --profile cpp up -d cpp-server --build
docker compose --profile cpp run --rm cpp-client grpc_benchmark_client --target cpp-server:50051
```

**Rust** (`rust-server`, `rust-client`; client exits after the stream reaches `max_size_bytes`; Compose stops when the client exits):

```bash
docker compose --profile rust up --build
```

**Rust server in the background**, then run the client on demand:

```bash
docker compose --profile rust up -d rust-server --build
docker compose --profile rust run --rm rust-client /usr/local/bin/grpc_benchmark_client --target rust-server:50051
```

**Go** (`go-server`, `go-client`; client exits after the stream reaches `max_size_bytes`; Compose stops when the client exits):

```bash
docker compose --profile go up --build
```

**Go server in the background**, then run the client on demand:

```bash
docker compose --profile go up -d go-server --build
docker compose --profile go run --rm go-client /usr/local/bin/grpc_benchmark_client --target go-server:50051
```

**Cross-language client (e.g. Python → C++ server)** — gRPC is fine: any client here can talk to any server that implements `proto/benchmark.proto`. The friction is **Compose**, not the wire protocol: `python-client` has **`depends_on: python-server`**, so `docker compose … run python-client` tries to start **python-server** as well. That container also maps host **50051**, which fails if **cpp-server** (or another stack) already owns that port (`Bind for 0.0.0.0:50051 failed: port is already allocated`).

Keep **one** server running, then run the client **without** starting its bundled server:

```bash
docker compose --profile cpp up -d cpp-server --build
docker compose --profile python run --rm --no-deps python-client python -m python_grpc_benchmark.client --target cpp-server:50051
```

Use `--no-deps` whenever the client’s default `depends_on` server would conflict with the server you actually want (`rust-server`, `go-server`, etc.). Inside Compose, use the **service name** and port **50051** (e.g. `cpp-server:50051`), not `python-server`, unless that is the server you started.

**Stop and remove containers:**

```bash
docker compose down
```

With the **`python`** profile, the server listens on host port **50051** (`50051:50051`). Override client flags by passing arguments after `docker compose --profile python run --rm python-client` as in the example above. The **`cpp`**, **`rust`**, and **`go`** profiles use the same host port mapping; never enable more than one profile at once.

For C++ without Compose, see **`cpp/README.md`** (`docker build` / `docker run`). For Rust without Compose, see **`rust/README.md`**. For Go without Compose, see **`go/README.md`**.
