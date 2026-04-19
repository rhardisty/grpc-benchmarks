package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"os"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "grpc-benchmark/go/gen/benchmarkpb"
)

func init() {
	// Go's flag package expects single-dash flags; align with Python/C++/Rust CLI (`--target`, etc.).
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

const (
	defaultResponseChunkBytes = int64(4 * 1024 * 1024)
	defaultMaxSizeBytes       = int64(5 * 1024 * 1024 * 1024)
	unlimitedGRPC             = math.MaxInt32
)

func main() {
	target := flag.String("target", "localhost:50051", "server host:port")
	responseSize := flag.Int64("response-size", defaultResponseChunkBytes, "bytes per EchoResponse.chunk")
	maxSize := flag.Int64("max-size-bytes", defaultMaxSizeBytes, "total streamed chunk bytes")
	sequence := flag.Int64("sequence", 0, "base sequence number")
	flag.Parse()

	if *responseSize <= 0 {
		log.Fatal("--response-size must be positive")
	}
	if *maxSize <= 0 {
		log.Fatal("--max-size-bytes must be positive")
	}

	opts := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(unlimitedGRPC),
			grpc.MaxCallSendMsgSize(unlimitedGRPC),
		),
	}

	conn, err := grpc.NewClient(*target, opts...)
	if err != nil {
		log.Fatalf("dial: %v", err)
	}
	defer conn.Close()

	client := pb.NewStreamingBenchmarkClient(conn)
	ctx := context.Background()

	stream, err := client.ServerStream(ctx, &pb.EchoRequest{
		ResponseChunkSizeBytes: *responseSize,
		Sequence:               *sequence,
		MaxSizeBytes:           *maxSize,
	})
	if err != nil {
		log.Fatalf("ServerStream: %v", err)
	}

	t0 := time.Now()
	var total int64
	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalf("recv: %v", err)
		}
		total += int64(len(msg.GetChunk()))
	}
	elapsed := time.Since(t0).Seconds()
	gbps := float64(total) * 8.0 / elapsed / 1e9
	fmt.Printf("INFO %.3f Gbps (%d chunk bytes in %.6f s)\n", gbps, total, elapsed)
}
