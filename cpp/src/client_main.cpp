#include <grpcpp/grpcpp.h>

#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>

#include "benchmark.grpc.pb.h"

namespace {

constexpr int64_t kDefaultResponseChunkBytes = static_cast<int64_t>(4) * 1024 * 1024;
constexpr int64_t kDefaultMaxSizeBytes = static_cast<int64_t>(5) * 1024 * 1024 * 1024;
constexpr int kDefaultMaxMsg = -1;

struct ClientArgs {
  std::string target = "localhost:50051";
  int64_t response_chunk_size_bytes = kDefaultResponseChunkBytes;
  int64_t max_size_bytes = kDefaultMaxSizeBytes;
  int64_t sequence = 0;
  double rpc_timeout_sec = -1.0;
};

bool ParsePositiveInt64(std::string_view s, int64_t* out) {
  char* end = nullptr;
  const long long v = std::strtoll(std::string(s).c_str(), &end, 10);
  if (end == s.data() || *end != '\0' || v <= 0 ||
      v > std::numeric_limits<int64_t>::max()) {
    return false;
  }
  *out = static_cast<int64_t>(v);
  return true;
}

bool ParseInt64(std::string_view s, int64_t* out) {
  char* end = nullptr;
  const long long v = std::strtoll(std::string(s).c_str(), &end, 10);
  if (end == s.data() || *end != '\0') {
    return false;
  }
  *out = static_cast<int64_t>(v);
  return true;
}

bool ParseDouble(std::string_view s, double* out) {
  char* end = nullptr;
  *out = std::strtod(std::string(s).c_str(), &end);
  return end != s.data() && *end == '\0';
}

void PrintUsage(std::string_view argv0) {
  std::cerr << "Usage: " << argv0
            << " [--target HOST:PORT] [--response-size N] [--max-size-bytes N] [--sequence N] "
               "[--timeout SEC]\n";
}

struct StreamStats {
  int64_t total_chunk_bytes = 0;
  double elapsed_seconds = 0.0;
};

double GbpsDecimal(const StreamStats& s) {
  if (s.elapsed_seconds <= 0.0) {
    return 0.0;
  }
  return (static_cast<double>(s.total_chunk_bytes) * 8.0) / s.elapsed_seconds / 1e9;
}

StreamStats RunClient(const ClientArgs& args) {
  // gRPC 1.30 (Ubuntu 22.04 packages): SetMaxSendMessageSize returns void — no fluent chaining.
  grpc::ChannelArguments channel_args;
  channel_args.SetMaxSendMessageSize(kDefaultMaxMsg);
  channel_args.SetMaxReceiveMessageSize(kDefaultMaxMsg);
  auto channel = grpc::CreateCustomChannel(args.target, grpc::InsecureChannelCredentials(), channel_args);
  auto stub = benchmark::StreamingBenchmark::NewStub(channel);

  benchmark::EchoRequest request;
  request.set_response_chunk_size_bytes(args.response_chunk_size_bytes);
  request.set_sequence(args.sequence);
  request.set_max_size_bytes(args.max_size_bytes);

  grpc::ClientContext context;
  if (args.rpc_timeout_sec >= 0.0) {
    const auto deadline =
        std::chrono::system_clock::now() +
        std::chrono::duration_cast<std::chrono::system_clock::duration>(
            std::chrono::duration<double>(args.rpc_timeout_sec));
    context.set_deadline(deadline);
  }

  benchmark::EchoResponse response;
  std::unique_ptr<grpc::ClientReader<benchmark::EchoResponse>> reader(
      stub->ServerStream(&context, request));

  StreamStats stats;
  const auto t0 = std::chrono::steady_clock::now();
  while (reader->Read(&response)) {
    stats.total_chunk_bytes += static_cast<int64_t>(response.chunk().size());
  }
  const auto t1 = std::chrono::steady_clock::now();
  stats.elapsed_seconds = std::chrono::duration<double>(t1 - t0).count();

  const grpc::Status status = reader->Finish();
  if (!status.ok()) {
    std::cerr << "RPC failed: " << status.error_message() << " (" << status.error_code() << ")\n";
    std::exit(1);
  }
  return stats;
}

}  // namespace

int main(int argc, char** argv) {
  ClientArgs args;
  for (int i = 1; i < argc; ++i) {
    const std::string_view arg(argv[i]);
    if (arg == "--target" && i + 1 < argc) {
      args.target = argv[++i];
    } else if (arg == "--response-size" && i + 1 < argc) {
      if (!ParsePositiveInt64(argv[++i], &args.response_chunk_size_bytes)) {
        std::cerr << "--response-size must be a positive integer\n";
        return 1;
      }
    } else if (arg == "--max-size-bytes" && i + 1 < argc) {
      if (!ParsePositiveInt64(argv[++i], &args.max_size_bytes)) {
        std::cerr << "--max-size-bytes must be a positive integer\n";
        return 1;
      }
    } else if (arg == "--sequence" && i + 1 < argc) {
      if (!ParseInt64(argv[++i], &args.sequence)) {
        std::cerr << "--sequence must be an integer\n";
        return 1;
      }
    } else if (arg == "--timeout" && i + 1 < argc) {
      if (!ParseDouble(argv[++i], &args.rpc_timeout_sec)) {
        std::cerr << "--timeout must be a number\n";
        return 1;
      }
    } else if (arg == "-h" || arg == "--help") {
      PrintUsage(argv[0]);
      return 0;
    } else {
      std::cerr << "Unknown argument: " << arg << "\n";
      PrintUsage(argv[0]);
      return 1;
    }
  }

  const StreamStats stats = RunClient(args);
  const double gbps = GbpsDecimal(stats);
  std::cout << std::fixed << std::setprecision(3) << "INFO " << gbps << " Gbps (" << stats.total_chunk_bytes
            << " chunk bytes in " << std::setprecision(6) << stats.elapsed_seconds << " s)\n";
  return 0;
}
