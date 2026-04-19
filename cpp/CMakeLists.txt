cmake_minimum_required(VERSION 3.20)
project(grpc-benchmark-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Ubuntu/Debian packages: Protobuf is exposed via CMake's FindProtobuf module (no ProtobufConfig.cmake).
# gRPC C++ is wired through pkg-config (grpc++.pc) from libgrpc++-dev.
find_package(Protobuf REQUIRED)
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GRPCPP REQUIRED IMPORTED_TARGET grpc++)

find_program(GRPC_CPP_PLUGIN grpc_cpp_plugin REQUIRED)

set(PROTO_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../proto")
set(PROTO_FILE "${PROTO_DIR}/benchmark.proto")
set(GEN_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")

# protoc does not create --cpp_out / --grpc_out directories; ensure they exist.
file(MAKE_DIRECTORY "${GEN_DIR}")

add_custom_command(
  OUTPUT
    "${GEN_DIR}/benchmark.pb.cc"
    "${GEN_DIR}/benchmark.pb.h"
    "${GEN_DIR}/benchmark.grpc.pb.cc"
    "${GEN_DIR}/benchmark.grpc.pb.h"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${GEN_DIR}"
  COMMAND "${Protobuf_PROTOC_EXECUTABLE}"
  ARGS
    --cpp_out "${GEN_DIR}"
    --grpc_out "${GEN_DIR}"
    -I "${PROTO_DIR}"
    --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN}
    "${PROTO_FILE}"
  DEPENDS "${PROTO_FILE}"
  COMMENT "Generating C++ protobuf and gRPC code from benchmark.proto"
  VERBATIM)

add_library(benchmark_proto STATIC
  "${GEN_DIR}/benchmark.pb.cc"
  "${GEN_DIR}/benchmark.grpc.pb.cc")
target_include_directories(benchmark_proto PUBLIC "${GEN_DIR}")
target_link_libraries(
  benchmark_proto
  PUBLIC
    protobuf::libprotobuf
    PkgConfig::GRPCPP
    Threads::Threads
)

add_executable(grpc_benchmark_server src/server_main.cpp)
target_link_libraries(grpc_benchmark_server PRIVATE benchmark_proto)

add_executable(grpc_benchmark_client src/client_main.cpp)
target_link_libraries(grpc_benchmark_client PRIVATE benchmark_proto)
