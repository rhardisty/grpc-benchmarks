"""Async gRPC server for the streaming benchmark service."""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import AsyncIterator

import grpc

from . import benchmark_pb2, benchmark_pb2_grpc

_LOGGER = logging.getLogger(__name__)


class StreamingBenchmarkServicerImpl(benchmark_pb2_grpc.StreamingBenchmarkServicer):
    """Streams responses whose body size is set by the client request."""

    async def ServerStream(
        self,
        request: benchmark_pb2.EchoRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[benchmark_pb2.EchoResponse]:
        max_size = int(request.max_size_bytes)
        if max_size <= 0:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "max_size_bytes must be positive",
            )
        chunk_target = int(request.response_chunk_size_bytes)
        if chunk_target <= 0:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "response_chunk_size_bytes must be positive",
            )
        total = 0
        n = 0
        while total < max_size:
            remaining = max_size - total
            this_len = min(chunk_target, remaining)
            body = b"\0" * this_len
            yield benchmark_pb2.EchoResponse(
                chunk=body,
                sequence=request.sequence + n,
            )
            total += this_len
            n += 1


async def _serve(listen_addr: str) -> None:
    server = grpc.aio.server(
        options=(
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ),
    )
    benchmark_pb2_grpc.add_StreamingBenchmarkServicer_to_server(
        StreamingBenchmarkServicerImpl(),
        server,
    )
    server.add_insecure_port(listen_addr)
    _LOGGER.info("listening on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run the benchmark gRPC server (grpc.aio).")
    parser.add_argument(
        "--listen",
        default="[::]:50051",
        help="Address to bind (host:port), e.g. 0.0.0.0:50051 or [::]:50051",
    )
    args = parser.parse_args()
    asyncio.run(_serve(args.listen))


if __name__ == "__main__":
    main()
