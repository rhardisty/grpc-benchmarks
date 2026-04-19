package main

import (
	"flag"
	"fmt"
	"log"
	"math"
	"net"
	"os"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	pb "grpc-benchmark/go/gen/benchmarkpb"
)

func init() {
	if len(os.Args) > 1 {
		fixed := make([]string, 0, len(os.Args))
		fixed = append(fixed, os.Args[0])
		for _, a := range os.Args[1:] {
			if strings.HasPrefix(a, "--") && !strings.HasPrefix(a, "---") {
				fixed = append(fixed, "-"+strings.TrimPrefix(a, "--"))
			} else {
				fixed = append(fixed, a)
			}
		}
		os.Args = fixed
	}
}

// Match Python/C++ unlimited gRPC message size (-1); Go uses MaxInt32-sized caps by default.
const unlimitedGRPC = math.MaxInt32

type benchmarkServer struct {
	pb.UnimplementedStreamingBenchmarkServer
}

func (s *benchmarkServer) ServerStream(req *pb.EchoRequest, stream pb.StreamingBenchmark_ServerStreamServer) error {
	if req.GetMaxSizeBytes() <= 0 {
		return status.Error(codes.InvalidArgument, "max_size_bytes must be positive")
	}
	if req.GetResponseChunkSizeBytes() <= 0 {
		return status.Error(codes.InvalidArgument, "response_chunk_size_bytes must be positive")
	}
	var total int64
	var n int64
	for total < req.GetMaxSizeBytes() {
		remaining := req.GetMaxSizeBytes() - total
		thisLen := req.GetResponseChunkSizeBytes()
		if remaining < thisLen {
			thisLen = remaining
		}
		chunk := make([]byte, thisLen)
		if err := stream.Send(&pb.EchoResponse{
			Chunk:    chunk,
			Sequence: req.GetSequence() + n,
		}); err != nil {
			return err
		}
		total += thisLen
		n++
	}
	return nil
}

func main() {
	listen := flag.String("listen", "[::]:50051", "address to bind (host:port)")
	flag.Parse()

	lis, err := net.Listen("tcp", *listen)
	if err != nil {
		log.Fatalf("listen: %v", err)
	}

	s := grpc.NewServer(
		grpc.MaxRecvMsgSize(unlimitedGRPC),
		grpc.MaxSendMsgSize(unlimitedGRPC),
	)
	pb.RegisterStreamingBenchmarkServer(s, &benchmarkServer{})

	fmt.Printf("listening on %s\n", *listen)
	if err := s.Serve(lis); err != nil {
		log.Fatalf("serve: %v", err)
	}
}
