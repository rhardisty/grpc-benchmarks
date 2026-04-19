# Build from repository root: docker build -f cpp/Dockerfile .
# Single stage: compile and run against the same APT gRPC/Protobuf packages (avoids runtime
# package name mismatches like libgrpc++1.43 vs libgrpc++1 across mirrors/updates).

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        pkg-config \
        ca-certificates \
        libgrpc++-dev \
        libprotobuf-dev \
        protobuf-compiler \
        protobuf-compiler-grpc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY proto /workspace/proto
COPY cpp /workspace/cpp

# gRPC 1.30 (Ubuntu 22.04): SetMaxSendMessageSize returns void — fluent chaining must not be used.
# If this fails, your build context has an old client_main.cpp; save/sync sources, then:
#   docker compose build --no-cache cpp-server
RUN if grep -Fq "ChannelArguments().SetMaxSendMessageSize" /workspace/cpp/src/client_main.cpp; then \
      echo "ERROR: cpp/src/client_main.cpp still uses chained SetMax* (breaks gRPC 1.30). Update that file from the repo." >&2; \
      exit 1; \
    fi

RUN cmake -B /workspace/cpp/build -S /workspace/cpp \
        -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /workspace/cpp/build --parallel "$(nproc)" \
    && install -m755 /workspace/cpp/build/grpc_benchmark_server /usr/local/bin/ \
    && install -m755 /workspace/cpp/build/grpc_benchmark_client /usr/local/bin/

EXPOSE 50051

CMD ["grpc_benchmark_server", "--listen", "0.0.0.0:50051"]
