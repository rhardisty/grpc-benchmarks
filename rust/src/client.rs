use std::time::Instant;

use clap::Parser;
use tonic::transport::Endpoint;

use grpc_benchmark_rust::pb::streaming_benchmark_client::StreamingBenchmarkClient;
use grpc_benchmark_rust::pb::EchoRequest;

const DEFAULT_RESPONSE_CHUNK_BYTES: i64 = 4 * 1024 * 1024;
const DEFAULT_MAX_SIZE_BYTES: i64 = 5 * 1024 * 1024 * 1024;

/// Match Python/C++ unlimited gRPC message size (`-1`); tonic uses `usize` (see `server.rs`).
const UNLIMITED_GRPC_BYTES: usize = usize::MAX;

#[derive(Parser, Debug)]
#[command(version, about = "gRPC streaming benchmark client (tonic)")]
struct Args {
    #[arg(long, default_value = "localhost:50051")]
    target: String,
    #[arg(long = "response-size", default_value_t = DEFAULT_RESPONSE_CHUNK_BYTES)]
    response_chunk_size_bytes: i64,
    #[arg(long = "max-size-bytes", default_value_t = DEFAULT_MAX_SIZE_BYTES)]
    max_size_bytes: i64,
    #[arg(long, default_value_t = 0)]
    sequence: i64,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    if args.response_chunk_size_bytes <= 0 {
        eprintln!("--response-size must be positive");
        std::process::exit(1);
    }
    if args.max_size_bytes <= 0 {
        eprintln!("--max-size-bytes must be positive");
        std::process::exit(1);
    }

    let uri = format!("http://{}", args.target);
    let channel = Endpoint::from_shared(uri)?.connect().await?;
    let mut client = StreamingBenchmarkClient::new(channel)
        .max_decoding_message_size(UNLIMITED_GRPC_BYTES)
        .max_encoding_message_size(UNLIMITED_GRPC_BYTES);

    let request = EchoRequest {
        response_chunk_size_bytes: args.response_chunk_size_bytes,
        sequence: args.sequence,
        max_size_bytes: args.max_size_bytes,
    };

    let mut stream = client.server_stream(request).await?.into_inner();
    let t0 = Instant::now();
    let mut total_chunk_bytes: i64 = 0;
    while let Some(msg) = stream.message().await? {
        total_chunk_bytes += msg.chunk.len() as i64;
    }
    let elapsed = t0.elapsed().as_secs_f64();

    let gbps = (total_chunk_bytes as f64 * 8.0) / elapsed / 1e9;
    println!(
        "INFO {:.3} Gbps ({} chunk bytes in {:.6} s)",
        gbps, total_chunk_bytes, elapsed
    );

    Ok(())
}
