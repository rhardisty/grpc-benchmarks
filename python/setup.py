"""Run protoc at build time, then build the package."""
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info as EggInfoCommand


def _python_dir() -> Path:
    return Path(__file__).resolve().parent


def _repo_root() -> Path:
    return _python_dir().parent


def _pkg_dir() -> Path:
    return _python_dir() / "src" / "python_grpc_benchmark"


def _proto_include_dir() -> Path | None:
    """Directory for protoc -I: repo-root proto/ when present, else packaged copy (sdist)."""
    repo_proto = _repo_root() / "proto"
    if (repo_proto / "benchmark.proto").is_file():
        return repo_proto
    packaged = _pkg_dir() / "proto"
    if (packaged / "benchmark.proto").is_file():
        return packaged
    return None


def sync_protos_into_package() -> None:
    """Copy repo-root proto/ into the package when building from a full repo checkout."""
    src = _repo_root() / "proto"
    if not src.is_dir():
        return
    dst = _pkg_dir() / "proto"
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.glob("*.proto"):
        shutil.copy2(p, dst / p.name)


def compile_protos() -> None:
    try:
        import grpc_tools.protoc
    except ImportError:
        return
    pkg_dir = _pkg_dir()
    proto_dir = _proto_include_dir()
    if proto_dir is None:
        return
    proto_file = proto_dir / "benchmark.proto"
    if not proto_file.is_file():
        return
    grpc_tools.protoc.main([
        "",
        f"-I{proto_dir}",
        f"--python_out={pkg_dir}",
        f"--grpc_python_out={pkg_dir}",
        str(proto_file),
    ])
    grpc_file = pkg_dir / "benchmark_pb2_grpc.py"
    if grpc_file.exists():
        text = grpc_file.read_text(encoding="utf-8")
        text = text.replace(
            "import benchmark_pb2 as benchmark__pb2",
            "from . import benchmark_pb2 as benchmark__pb2",
        )
        grpc_file.write_text(text, encoding="utf-8")


class EggInfo(EggInfoCommand):
    def run(self):
        sync_protos_into_package()
        super().run()


class BuildPy(build_py):
    def run(self):
        sync_protos_into_package()
        compile_protos()
        super().run()


setup(cmdclass={"egg_info": EggInfo, "build_py": BuildPy})
