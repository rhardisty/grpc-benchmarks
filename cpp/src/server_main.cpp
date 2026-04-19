#include <grpcpp/grpcpp.h>

#include <algorithm>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>

#include "benchmark.grpc.pb.h"

namespace {

constexpr int kDefaultMaxMsg = -1;

class StreamingBenchmarkService final : public benchmark::StreamingBenchmark::Service {
 public:
  grpc::Status ServerStream(grpc::ServerContext* context,
                            const benchmark::EchoRequest* request,
                            grpc::ServerWriter<benchmark::EchoResponse>* writer) override {
    (void)context;
    const int64_t max_size = request->max_size_bytes();
    if (max_size <= 0) {
      return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT, "max_size_bytes must be positive");
    }
    const int64_t chunk_target = request->response_chunk_size_bytes();
    if (chunk_target <= 0) {
      return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT,
                          "response_chunk_size_bytes must be positive");
    }
    int64_t total = 0;
    int64_t n = 0;
    while (total < max_size) {
      const int64_t remaining = max_size - total;
      const int64_t this_len = std::min(chunk_target, remaining);
      benchmark::EchoResponse resp;
      resp.set_chunk(std::string(static_cast<size_t>(this_len), '\0'));
      resp.set_sequence(request->sequence() + n);
      if (!writer->Write(resp)) {
        return grpc::Status::CANCELLED;
      }
      total += this_len;
      ++n;
    }
    return grpc::Status::OK;
  }
};

void PrintUsage(std::string_view argv0) {
  std::cerr << "Usage: " << argv0 << " [--listen HOST:PORT]\n";
  std::cerr << "  --listen   Bind address (default [::]:50051)\n";
}

}  // namespace

int main(int argc, char** argv) {
  std::string listen_addr = "[::]:50051";
  for (int i = 1; i < argc; ++i) {
    const std::string_view arg(argv[i]);
    if (arg == "--listen" && i + 1 < argc) {
      listen_addr = argv[++i];
    } else if (arg == "-h" || arg == "--help") {
      PrintUsage(argv[0]);
      return 0;
    } else {
      std::cerr << "Unknown argument: " << arg << "\n";
      PrintUsage(argv[0]);
      return 1;
    }
  }

  StreamingBenchmarkService service;
  grpc::ServerBuilder builder;
  builder.AddListeningPort(listen_addr, grpc::InsecureServerCredentials());
  builder.SetMaxSendMessageSize(kDefaultMaxMsg);
  builder.SetMaxReceiveMessageSize(kDefaultMaxMsg);
  builder.RegisterService(&service);
  std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
  if (!server) {
    std::cerr << "Failed to start server on " << listen_addr << "\n";
    return 1;
  }
  std::cout << "listening on " << listen_addr << "\n";
  server->Wait();
  return 0;
}
