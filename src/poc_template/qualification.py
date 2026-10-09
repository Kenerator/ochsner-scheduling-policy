"""Qualify trusted developer argv against one disposable committed local export.

Declared commands are executable developer configuration, not safe untrusted intake.
This evidence supplies neither remote access nor product/clinical acceptance.
"""
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile
import time

from .project_git import git_environment
from .speckit_adapter import run_process

DEFAULT_PROFILE = Path("docs/internal/qualification.json")
EXPORT_LIMIT = 128 * 1024 * 1024


def _git(root, *args):
    result = run_process(["git", *args], root, timeout=30, env=git_environment(),
                         structured_stdout=True)
    if result["returncode"] or result["timed_out"]:
        raise ValueError("Local Git source/profile operation failed: " + result["stderr"][-1000:])
    return result["stdout"].strip()


def _timeout(value):
    if type(value) is not int or not 1 <= value <= 3600:
        raise ValueError("Qualification timeout must be an integer from 1 to 3600 seconds")
    return value


def _argv(value):
    if (not isinstance(value, list) or not 1 <= len(value) <= 100 or
            any(not isinstance(token, str) or not token or len(token) > 8192 or "\0" in token
                for token in value)):
        raise ValueError("Qualification commands require bounded nonempty argv strings")
    if any(re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", token.replace("{python}", "").replace("{project}", ""))
           for token in value):
        raise ValueError("Only {python} and {project} command substitutions are supported")
    return value


def _profile(text):
    try:
        value = json.loads(text)
    except (ValueError, TypeError) as error:
        raise ValueError("Qualification profile must be committed JSON") from error
    if (not isinstance(value, dict) or
            set(value) - {"schema_version", "install", "checks", "timeout"} or
            type(value.get("schema_version")) is not int or value["schema_version"] != 1):
        raise ValueError("Qualification profile requires schema_version 1 and declared fields")
    timeout = _timeout(value.get("timeout", 900))
    steps = [dict(name="install", argv=_argv(value.get("install")), timeout=timeout)]
    checks = value.get("checks")
    if not isinstance(checks, list) or not 1 <= len(checks) <= 32:
        raise ValueError("Qualification profile requires 1–32 checks")
    names = {"install", "venv"}
    for check in checks:
        if not isinstance(check, dict) or set(check) - {"name", "argv", "timeout"}:
            raise ValueError("Invalid qualification check fields")
        name = check.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", name) or name in names:
            raise ValueError("Qualification check names must be unique bounded names")
        names.add(name)
        steps.append(dict(name=name, argv=_argv(check.get("argv")),
                          timeout=_timeout(check.get("timeout", timeout))))
    return steps


def _private(path):
    parts = [part.lower() for part in path.parts]
    directories = {".git", ".venv", "venv", "env", ".env", ".ssh", ".aws", ".gnupg",
                   ".poc-template", "node_modules", "__pycache__"}
    return (any(part in directories or part.startswith(".venv") for part in parts) or
            ".specify/workflows/runs" in "/".join(parts) or
            "/".join(parts) == ".specify/workflows/poc-bootstrap.lock" or
            any(part.startswith(".env.") for part in parts) or
            any(part in {"id_rsa", "id_ed25519", "credentials", "credentials.json"} or
                part.endswith((".key", ".p12", ".pfx", ".pem")) for part in parts))


def _extract(archive, project):
    if archive.stat().st_size > EXPORT_LIMIT:
        raise ValueError("Committed export exceeds the 128 MiB qualification limit")
    with tarfile.open(archive, "r:") as source:
        total = count = 0
        for member in source:
            path = PurePosixPath(member.name)
            count += 1
            total += member.size
            if (count > 20000 or total > EXPORT_LIMIT or member.size < 0 or path.is_absolute() or
                    ".." in path.parts or not path.parts or _private(path) or
                    not (member.isfile() or member.isdir())):
                raise ValueError("Unsafe, private, linked or oversized committed export member")
            target = project.joinpath(*path.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as incoming, target.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)


def _step(step, root, env):
    start = time.monotonic()
    try:
        result = run_process(step["argv"], root, timeout=step["timeout"], env=env)
    except OSError as error:
        result = dict(returncode=None, timed_out=False, stdout="", stderr=str(error))
    return {**step, "elapsed_seconds": round(time.monotonic() - start, 6),
            "exit_code": result["returncode"], "timed_out": result["timed_out"],
            "stdout": result["stdout"], "stderr": result["stderr"]}


def qualify_project(root: Path, profile: Path | None = None, *, execute=False) -> dict:
    """Preview by default; execution creates and removes only its owned scratch tree."""
    root = Path(root).resolve()
    if not root.is_dir() or Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("Qualification root must be the exact local Git project root")
    commit = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    requested = Path(profile) if profile is not None else DEFAULT_PROFILE
    # Use lexical repository-relative paths; read their bytes exclusively from HEAD.
    if requested.is_absolute():
        try:
            requested = requested.relative_to(root)
        except ValueError as error:
            raise ValueError("Qualification profile must be inside the exact project root") from error
    if ".." in requested.parts or not requested.parts:
        raise ValueError("Qualification profile must be project-relative")
    relative = requested.as_posix()
    steps = _profile(_git(root, "show", f"{commit}:{relative}"))
    report = dict(status="preview", source_root=str(root), source_commit=commit, profile=relative,
                  source_kind="clean committed local export", excludes_uncommitted=True,
                  limitations=["Local export, not a GitHub access check",
                               "Declared deterministic checks, not clinical or semantic acceptance"], steps=steps)
    if not execute:
        return report
    # export-ignore may omit private tracked state; inspect the tree itself first.
    for entry in _git(root, "ls-tree", "-r", "-z", "--full-tree", commit).split("\0"):
        if entry:
            metadata, path = entry.split("\t", 1)
            if metadata.split()[0] not in {"100644", "100755"} or _private(PurePosixPath(path)):
                raise ValueError("Committed source tracks private material, links or submodules")
    with tempfile.TemporaryDirectory(prefix="poc-qualification-") as scratch:
        scratch = Path(scratch)
        project, environment = scratch / "project", scratch / "venv"
        project.mkdir()
        archive = scratch / "source.tar"
        _git(root, "archive", "--format=tar", f"--output={archive}", commit)
        _extract(archive, project)
        env = git_environment()
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "VIRTUAL_ENV",
                    "PIP_TARGET", "PIP_PREFIX", "PIP_ROOT"):
            env.pop(key, None)
        env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PIP_USER="0",
                   PIP_CONFIG_FILE=os.devnull, PIP_CACHE_DIR=str(scratch / "pip-cache"))
        creation = dict(name="venv", argv=[sys.executable, "-m", "venv", str(environment)], timeout=900)
        completed = [_step(creation, scratch, env)]
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env["PATH"] = str(python.parent) + os.pathsep + env.get("PATH", os.defpath)
        env["VIRTUAL_ENV"] = str(environment)
        for step in steps:
            if completed[-1]["exit_code"] != 0 or completed[-1]["timed_out"]:
                break
            argv = [token.replace("{python}", str(python)).replace("{project}", str(project))
                    for token in step["argv"]]
            completed.append(_step({**step, "argv": argv}, project, env))
        report["steps"] = completed
        report["status"] = "passed" if all(
            step["exit_code"] == 0 and not step["timed_out"] for step in completed) else "failed"
    return report
