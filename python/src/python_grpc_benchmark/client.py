"""Async gRPC client for the streaming benchmark service."""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

import grpc.aio

from . import benchmark_pb2, benchmark_pb2_grpc

_LOGGER = logging.getLogger(__name__)

_DEFAULT_RESPONSE_CHUNK_BYTES = 4 * 1024 * 1024
_DEFAULT_MAX_SIZE_BYTES = 5*1024**3

_CHANNEL_OPTIONS = (
    ("grpc.max_send_message_length", -1),
    ("grpc.max_receive_message_length", -1),
)


@dataclass(frozen=True)
class ClientArgs:
    target: str
    response_chunk_size_bytes: int
    max_size_bytes: int
    sequence: int
    rpc_timeout: float | None


@dataclass(frozen=True)
class StreamThroughput:
    """Chunk payload totals and wall time for one ``ServerStream`` RPC."""

    total_chunk_bytes: int
    elapsed_seconds: float

    @property
    def gbps(self) -> float:
        """Application payload rate: gigabits per second (decimal, 1e9 bits/s)."""
        if self.elapsed_seconds <= 0:
            return 0.0
        return (self.total_chunk_bytes * 8) / self.elapsed_seconds / 1e9


async def iter_server_stream(args: ClientArgs) -> AsyncIterator[benchmark_pb2.EchoResponse]:
    """Stream ``EchoResponse`` messages from ``ServerStream`` until the server ends."""
    async with grpc.aio.insecure_channel(args.target, options=_CHANNEL_OPTIONS) as channel:
        stub = benchmark_pb2_grpc.StreamingBenchmarkStub(channel)
        req = benchmark_pb2.EchoRequest(
            response_chunk_size_bytes=args.response_chunk_size_bytes,
            sequence=args.sequence,
            max_size_bytes=args.max_size_bytes,
        )
        call = stub.ServerStream(req, timeout=args.rpc_timeout)
        async for resp in call:
            yield resp


async def server_stream(args: ClientArgs) -> StreamThroughput:
    """Call ``ServerStream`` and return chunk throughput over wall time."""
    t0 = time.perf_counter()
    total_chunk_bytes = 0
    async for resp in iter_server_stream(args):
        total_chunk_bytes += len(resp.chunk)
    elapsed = time.perf_counter() - t0
    return StreamThroughput(total_chunk_bytes=total_chunk_bytes, elapsed_seconds=elapsed)


async def _run_client(args: ClientArgs) -> None:
    stats = await server_stream(args)
    _LOGGER.info(
        "%.3f Gbps (%d chunk bytes in %.6f s)",
        stats.gbps,
        stats.total_chunk_bytes,
        stats.elapsed_seconds,
    )


def _positive_int(value: str) -> int:
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return n


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run the benchmark gRPC client (grpc.aio).")
    parser.add_argument(
        "--target",
        default="localhost:50051",
        help="Server address (host:port)",
    )
    parser.add_argument(
        "--response-size",
        type=_positive_int,
        default=_DEFAULT_RESPONSE_CHUNK_BYTES,
        metavar="N",
        dest="response_chunk_size_bytes",
        help="Byte size of each EchoResponse.chunk (EchoRequest.response_chunk_size_bytes); must be positive",
    )
    parser.add_argument(
        "--max-size-bytes",
        type=_positive_int,
        default=_DEFAULT_MAX_SIZE_BYTES,
        metavar="N",
        dest="max_size_bytes",
        help="Total max chunk payload bytes for the stream (EchoRequest.max_size_bytes); must be positive",
    )
    parser.add_argument(
        "--sequence",
        type=int,
        default=0,
        help="EchoRequest.sequence starting value",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SEC",
        dest="rpc_timeout",
        help="Optional per-RPC timeout in seconds",
    )
    ns = parser.parse_args()
    client_args = ClientArgs(
        target=ns.target,
        response_chunk_size_bytes=ns.response_chunk_size_bytes,
        max_size_bytes=ns.max_size_bytes,
        sequence=ns.sequence,
        rpc_timeout=ns.rpc_timeout,
    )
    asyncio.run(_run_client(client_args))


if __name__ == "__main__":
    main()
