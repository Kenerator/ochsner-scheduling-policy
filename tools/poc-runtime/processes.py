"""Owned process contracts; environments deliberately excluded from repr."""
from dataclasses import dataclass, field
import os
import shutil
import socket
import signal
import subprocess
import threading
import time

from credentials import LaunchError, SAFE_ENVIRONMENT, PUBLIC_SETTINGS, bounded_helper, child_environment

READINESS_TIMEOUT = 8.0


@dataclass(frozen=True)
class ProcessSpec:
    role: str
    argv: tuple[str, ...]
    environment: dict[str, str] = field(repr=False)
    readiness_port: int | None = None


def output_for_role(role):
    return subprocess.DEVNULL if role == "mock" else None


def errors_for_role(role):
    return subprocess.DEVNULL if role == "mock" else None


def require_listener_probe():
    executable = shutil.which("lsof")
    if executable is None or not os.path.isfile(executable) or not os.access(executable, os.X_OK):
        raise LaunchError("Local listener ownership verification requires lsof on PATH; no service was started.")
    return executable


def owns_listener(child, port, timeout):
    """Mac-first OS evidence, scoped to this exact child and loopback socket."""
    try:
        result = bounded_helper([require_listener_probe(), "-nP", "-a", "-p", str(child.pid),
            "-iTCP:" + str(port), "-sTCP:LISTEN", "-Fpfn"],
            env=child_environment(os.environ, settings={}), timeout=timeout, max_bytes=4096)
    except LaunchError:
        raise LaunchError("Local listener ownership could not be verified; no dependent service was started.") from None
    lines = result.stdout.splitlines()
    names = [line for line in lines[1:] if line.startswith("n")]
    # lsof includes a file-descriptor record even with a restricted field set.
    return (result.returncode == 0 and len(lines) >= 2 and lines[0] == "p" + str(child.pid)
            and bool(names) and all(line == "n127.0.0.1:" + str(port) for line in names)
            and all(line in names or (line.startswith("f") and line[1:].isdigit()) for line in lines[1:]))


def wait_ready(child, port):
    if port is None:
        return
    deadline = time.monotonic() + READINESS_TIMEOUT
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise LaunchError("An owned service exited before readiness; no fallback was started.")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                pass
        except OSError:
            time.sleep(0.025)
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        # A TCP connection alone can reach a bind-race winner we do not own.
        if owns_listener(child, port, min(1.0, remaining)) and child.poll() is None:
            return
        time.sleep(0.025)
    raise LaunchError("An owned service did not become ready within its startup bound.")


def wait_for_selected_application(owned, specs):
    while True:
        for child, spec in zip(owned, specs):
            status = child.poll()
            if status is not None:
                if spec.role == "mock":
                    raise LaunchError("The owned synthetic service stopped; application launch ended safely.")
                return status
        time.sleep(0.05)


def stop_owned(owned):
    failures = []
    for child in reversed(owned):
        try:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2)
            else:
                child.wait(timeout=0)
        except Exception:
            failures.append(child)
    if failures:
        raise LaunchError("Owned child cleanup could not be verified.")


def close_owned_descriptors(owned):
    failed = False
    for child in owned:
        for name in ("stdin", "stdout", "stderr"):
            stream = getattr(child, name, None)
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    failed = True
    if failed:
        raise LaunchError("Owned descriptor cleanup could not be verified.")


def _validate(specs):
    if not specs or any(not isinstance(spec, ProcessSpec) for spec in specs):
        raise LaunchError("Unsafe application process configuration.")
    if not any(spec.role != "mock" for spec in specs):
        raise LaunchError("An application process is required.")
    for spec in specs:
        permitted = SAFE_ENVIRONMENT | PUBLIC_SETTINGS | ({"OPENAI_API_KEY"} if spec.role == "model" else set())
        if (spec.role not in ("mock", "model", "viewer")
            or not isinstance(spec.argv, tuple) or not spec.argv
            or any(not isinstance(arg, str) or "\x00" in arg for arg in spec.argv)
            or not isinstance(spec.environment, dict) or set(spec.environment) - permitted):
            raise LaunchError("Unsafe application process configuration.")


def run_owned(specs: list[ProcessSpec], *, popen=subprocess.Popen) -> int:
    """Register immediately, clean exact children once, preserve cancellation."""
    from adapters import check_ports
    _validate(specs)
    if any(spec.readiness_port is not None for spec in specs):
        require_listener_probe()
    check_ports([spec.readiness_port for spec in specs if spec.readiness_port is not None])
    owned = []
    original = None
    previous_handler = None
    installed_handler = False
    def cancel(_signal, _frame):
        raise KeyboardInterrupt()
    try:
        if threading.current_thread() is threading.main_thread():
            previous_handler = signal.signal(signal.SIGTERM, cancel)
            installed_handler = True
        for spec in specs:
            if spec.readiness_port is not None:
                check_ports([spec.readiness_port])
            child = popen(spec.argv, env=spec.environment, shell=False, close_fds=True,
                          stdin=None if spec.role == "model" and spec.readiness_port is None else subprocess.DEVNULL,
                          stdout=output_for_role(spec.role), stderr=errors_for_role(spec.role))
            owned.append(child)
            wait_ready(child, spec.readiness_port)
        return wait_for_selected_application(owned, specs)
    except BaseException as error:
        original = error if isinstance(error, (LaunchError, KeyboardInterrupt, SystemExit)) else LaunchError(
            "Owned application startup failed; check the project installation and ports.")
        raise original from None
    finally:
        failed = False
        try:
            for operation in (stop_owned, close_owned_descriptors):
                try:
                    operation(owned)
                except Exception:
                    failed = True
        finally:
            if installed_handler:
                signal.signal(signal.SIGTERM, previous_handler)
        if failed:
            if original is not None:
                original.add_note("Owned child or descriptor cleanup could not be verified.")
            else:
                raise LaunchError("Owned child or descriptor cleanup could not be verified.")
