use std::pin::Pin;

use async_stream::stream;
use clap::Parser;
use futures_core::Stream;
use tonic::transport::Server;
use tonic::{Request, Response, Status};

use grpc_benchmark_rust::pb::streaming_benchmark_server::{StreamingBenchmark, StreamingBenchmarkServer};
use grpc_benchmark_rust::pb::{EchoRequest, EchoResponse};

/// Match Python/C++ `grpc.max_{send,receive}_message_length` of **-1** (unlimited): tonic has no `-1`, so use the
/// largest `usize` (default tonic/hyper cap is 4 MiB, which rejects 4 MiB chunks once protobuf overhead is added).
const UNLIMITED_GRPC_BYTES: usize = usize::MAX;

#[derive(Default)]
struct BenchmarkService;

#[tonic::async_trait]
impl StreamingBenchmark for BenchmarkService {
    type ServerStreamStream =
        Pin<Box<dyn Stream<Item = Result<EchoResponse, Status>> + Send + 'static>>;

    async fn server_stream(
        &self,
        request: Request<EchoRequest>,
    ) -> Result<Response<Self::ServerStreamStream>, Status> {
        let req = request.into_inner();
        let max_size = req.max_size_bytes;
        if max_size <= 0 {
            return Err(Status::invalid_argument("max_size_bytes must be positive"));
        }
        let chunk_target = req.response_chunk_size_bytes;
        if chunk_target <= 0 {
            return Err(Status::invalid_argument(
                "response_chunk_size_bytes must be positive",
            ));
        }
        let base_sequence = req.sequence;

        let out = stream! {
            let mut total: i64 = 0;
            let mut n: i64 = 0;
            while total < max_size {
                let remaining = max_size - total;
                let this_len = std::cmp::min(chunk_target, remaining);
                let chunk = vec![0u8; this_len as usize];
                yield Ok(EchoResponse {
                    chunk,
                    sequence: base_sequence + n,
                });
                total += this_len;
                n += 1;
            }
        };

        Ok(Response::new(Box::pin(out)))
    }
}

#[derive(Parser, Debug)]
#[command(version, about = "gRPC streaming benchmark server (tonic)")]
struct Args {
    /// Address to bind (host:port), e.g. 0.0.0.0:50051 or [::]:50051
    #[arg(long, default_value = "[::]:50051")]
    listen: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let addr = args.listen.parse()?;
    let svc = StreamingBenchmarkServer::new(BenchmarkService::default())
        .max_decoding_message_size(UNLIMITED_GRPC_BYTES)
        .max_encoding_message_size(UNLIMITED_GRPC_BYTES);

    println!("listening on {}", args.listen);
    Server::builder()
        .add_service(svc)
        .serve(addr)
        .await?;

    Ok(())
}
