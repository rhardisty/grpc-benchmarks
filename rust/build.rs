use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let proto_dir = manifest_dir.join("../proto");
    let proto_file = proto_dir.join("benchmark.proto");
    tonic_build::configure()
        .compile_protos(&[proto_file.as_path()], &[proto_dir.as_path()])?;
    Ok(())
}
