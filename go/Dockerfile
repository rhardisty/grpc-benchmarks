# Build from repository root: docker build -f go/Dockerfile .
# Generates protobuf Go stubs in the image, then static-ish binaries on Debian.

FROM golang:1.23-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/go/bin:${PATH}"
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.2 \
    && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1

WORKDIR /workspace

COPY proto/benchmark.proto /workspace/proto/benchmark.proto
COPY go /workspace/go

WORKDIR /workspace/go
RUN mkdir -p gen/benchmarkpb \
    && protoc -I /workspace/proto \
        --go_out=gen/benchmarkpb --go_opt=paths=source_relative \
        --go-grpc_out=gen/benchmarkpb --go-grpc_opt=paths=source_relative \
        /workspace/proto/benchmark.proto

RUN go mod tidy

RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/grpc_benchmark_server ./cmd/grpc_benchmark_server \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/grpc_benchmark_client ./cmd/grpc_benchmark_client

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/grpc_benchmark_server /usr/local/bin/
COPY --from=builder /out/grpc_benchmark_client /usr/local/bin/

EXPOSE 50051

CMD ["/usr/local/bin/grpc_benchmark_server", "--listen", "0.0.0.0:50051"]
