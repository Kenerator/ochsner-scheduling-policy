"""Deliberate, isolated native asset installation; never a machine-wide update."""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from .bootstrap import SPEC_KIT, digest
from .stage_guidance import strict_json

ROOT_METADATA = (".specify/integration.json", ".specify/init-options.json", ".specify/.gitignore")


def native_argv(python: str, args: list[str]) -> list[str]:
    # v1.1.0 exports a console entry function, not a specify_cli.__main__ module.
    return [str(python), "-c", "from specify_cli import main; main()", *args]


def fingerprint(root: Path) -> str:
    value = hashlib.sha256()
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
            value.update(path.relative_to(root).as_posix().encode() + b"\0")
            value.update(digest(path.read_bytes()).encode() + b"\n")
    return value.hexdigest()


def manifest(root: Path) -> dict:
    record = strict_json((root / "reference/bootstrap/spec-kit.json").read_text())
    if any(record.get(key) != value for key, value in SPEC_KIT.items()):
        raise ValueError("Spec-Kit source/version pin differs from this bootstrap")
    return record


def verify_assets(root: Path) -> dict:
    root = Path(root).resolve()
    record = manifest(root)
    for relative, expected in record["files"].items():
        path = root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or not path.resolve().is_relative_to(root):
            raise ValueError("Managed asset path must stay inside the project")
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError(f"Managed asset changed or missing: {relative}; review before upgrading")
        if relative in record.get("executable_files", []) and not path.stat().st_mode & 0o100:
            raise ValueError(f"Managed script lost executable permission: {relative}")
    return record


def verify_runtime(root: Path) -> dict:
    record = manifest(root)
    try:
        version = importlib.metadata.version("specify-cli")
        spec = importlib.util.find_spec("specify_cli")
    except (importlib.metadata.PackageNotFoundError, ImportError) as error:
        raise ValueError("Install the reviewed isolated bootstrap tool profile first") from error
    if version != SPEC_KIT["version"] or spec is None or not spec.origin:
        raise ValueError("Wrong Spec-Kit runtime version")
    if fingerprint(Path(spec.origin).parent) != record.get("package_sha256"):
        raise ValueError("Spec-Kit runtime bytes differ from the reviewed source build")
    return record


def install_assets(root: Path) -> dict:
    """First installation/reuse only. Changed assets need a separately reviewed update."""
    root = Path(root).resolve()
    record = verify_runtime(root)
    if record.get("files"):
        verify_assets(root)
        if all(name in record["files"] for name in ROOT_METADATA):
            return record
    env = dict(os.environ, SPECKIT_PYTHON_EXECUTABLE=sys.executable)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    with tempfile.TemporaryDirectory(prefix="poc-speckit-assets-") as temporary:
        staging = Path(temporary).resolve()
        for args in (["init", "--here", "--integration", "codex", "--script", "py", "--non-interactive", "--ignore-agent-tools"],
                     ["integration", "install", "claude", "--script", "py"]):
            result = subprocess.run(native_argv(sys.executable, args), cwd=staging,
                                    env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise ValueError("Native asset initialization failed: " + (result.stderr or result.stdout)[-3000:])
        prefixes = (".agents/skills", ".claude/skills", ".specify/scripts", ".specify/templates", ".specify/integrations")
        prepared, executable = {}, list(record.get("executable_files", []))
        for prefix in prefixes:
            for source in sorted((staging / prefix).rglob("*")):
                if source.is_file() and not source.is_symlink():
                    relative = source.relative_to(staging).as_posix()
                    if relative in record.get("files", {}):
                        continue  # Already verified; preserve the original managed bytes.
                    target = root / relative
                    if target.exists() or target.is_symlink():
                        raise ValueError(f"Refusing to overwrite existing asset: {relative}")
                    prepared[relative] = source.read_bytes()
                    if source.stat().st_mode & 0o100:
                        executable.append(relative)
        for relative in ROOT_METADATA:
            if relative in record.get("files", {}):
                continue
            target = root / relative
            source = staging / relative
            if target.exists() or target.is_symlink():
                # Migration may adopt identical native metadata, never replace a customization.
                if target.is_symlink() or not target.is_file() or target.read_bytes() != source.read_bytes():
                    raise ValueError(f"Refusing to overwrite existing asset: {relative}")
            prepared[relative] = source.read_bytes()
        for integration in (".agents/skills", ".claude/skills"):
            for stage in ("specify", "clarify", "plan", "tasks", "analyze", "implement", "converge"):
                relative = f"{integration}/speckit-{stage}/SKILL.md"
                if relative not in prepared and relative not in record.get("files", {}):
                    raise ValueError("Native initialization did not produce required skills")
        for relative, data in prepared.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with target.open("xb") as stream:
                    stream.write(data)
            if relative in executable:
                target.chmod(0o755)
        record = {**record, "files": {**record.get("files", {}), **{path: digest(data) for path, data in prepared.items()}},
                  "executable_files": sorted(executable)}
        destination = root / "reference/bootstrap/spec-kit.json"
        temporary_record = destination.with_suffix(".new")
        with temporary_record.open("x") as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary_record, destination)
    return verify_assets(root)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        installed = install_assets(args.root)
        print(f"Verified {len(installed['files'])} assets from Spec-Kit {installed['version']}")
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
