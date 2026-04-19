# Build from repository root: docker build -f rust/Dockerfile .
# Multi-stage: compile with official Rust image + protoc; run on slim Debian.

# Clap 4.6+ and recent transitive crates need a current stable toolchain (not 1.83).
FROM rust:1.85-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY proto /workspace/proto
COPY rust /workspace/rust

WORKDIR /workspace/rust
RUN cargo build --release

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /workspace/rust/target/release/grpc_benchmark_server /usr/local/bin/
COPY --from=builder /workspace/rust/target/release/grpc_benchmark_client /usr/local/bin/

EXPOSE 50051

CMD ["/usr/local/bin/grpc_benchmark_server", "--listen", "0.0.0.0:50051"]
