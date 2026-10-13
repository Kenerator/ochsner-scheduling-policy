"""Private, bounded credential capture; never persist or print helper output."""
from collections.abc import Mapping
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import threading
import time


class LaunchError(Exception):
    """A deliberately safe user-facing category, without raw failure details."""


SAFE_ENVIRONMENT = frozenset(("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TZ",
                             "TMPDIR", "SYSTEMROOT", "VIRTUAL_ENV", "XDG_CONFIG_HOME"))
PUBLIC_SETTINGS = frozenset(("PYTHONPATH", "OPENAI_MODEL", "BOB_ENABLE_OPENAI", "BOB_OPENAI_MODEL",
    "BOB_TRANSPORT_URL", "BOB_BASE_DIR", "BOB_MODEL_BUDGET_PATH", "API_BASE", "SCHEDULING_MODE",
    "SCHEDULING_MODEL", "SCHEDULING_API_BASE", "SCHEDULING_API_URL"))


def child_environment(environ: Mapping[str, str], *, settings: Mapping[str, str], key: str | None = None) -> dict[str, str]:
    """Construct rather than subtract from the parent environment."""
    if not isinstance(settings, Mapping) or any(
        name not in PUBLIC_SETTINGS or not isinstance(value, str) or any(c in value for c in "\x00\r\n")
        for name, value in settings.items()
    ):
        raise LaunchError("Unsupported application environment setting.")
    child = {name: environ[name] for name in SAFE_ENVIRONMENT if name in environ}
    child.update(settings)
    if key is not None:
        child["OPENAI_API_KEY"] = _scalar(key)
    return child


def _stop(child: subprocess.Popen) -> None:
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=1)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=1)


def bounded_helper(argv: list[str], *, env: dict, timeout: float, max_bytes: int) -> subprocess.CompletedProcess:
    """Read both pipes with a size bound and a deadline; own only this Popen."""
    if timeout <= 0 or max_bytes <= 0:
        raise LaunchError("Invalid credential helper limits.")
    child = None
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout
    previous_handler = None
    installed_handler = False
    acquiring = False
    termination_pending = False
    def cancel(_signal, _frame):
        nonlocal termination_pending
        if acquiring:
            termination_pending = True
            return
        raise KeyboardInterrupt()
    try:
        if threading.current_thread() is threading.main_thread():
            previous_handler = signal.signal(signal.SIGTERM, cancel)
            installed_handler = True
        # Defer the parent's exception until this exact child is registered.
        # Do not block OS signals: an exec'd helper would inherit that mask.
        acquiring = True
        try:
            child = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, close_fds=True)
        finally:
            acquiring = False
        if termination_pending:
            raise KeyboardInterrupt()
        for name in buffers:
            pipe = getattr(child, name)
            selector.register(pipe, selectors.EVENT_READ, name)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise LaunchError("Credential helper timed out.")
            for registered, _ in selector.select(min(remaining, 0.1)):
                chunk = os.read(registered.fd, min(8192, max_bytes + 1))
                if not chunk:
                    selector.unregister(registered.fileobj)
                    registered.fileobj.close()
                    continue
                buffer = buffers[registered.data]
                buffer.extend(chunk)
                if len(buffer) > max_bytes:
                    raise LaunchError("Credential helper output exceeded its private limit.")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LaunchError("Credential helper timed out.")
        child.wait(timeout=remaining)
        return subprocess.CompletedProcess(argv, child.returncode,
            buffers["stdout"].decode("utf-8"), buffers["stderr"].decode("utf-8"))
    except BaseException as original:
        if child is not None:
            try:
                _stop(child)
            except Exception:
                original.add_note("Owned credential helper cleanup could not be verified.")
        if isinstance(original, (KeyboardInterrupt, SystemExit, LaunchError)):
            raise
        raise LaunchError("Credential helper unavailable; check the trusted executable.") from None
    finally:
        try:
            selector.close()
            if child is not None:
                for name in buffers:
                    pipe = getattr(child, name, None)
                    if pipe is not None:
                        pipe.close()
        finally:
            if installed_handler:
                signal.signal(signal.SIGTERM, previous_handler)


def helper_executable(credential: dict, environ: Mapping[str, str] | None = None) -> str:
    environ = os.environ if environ is None else environ
    configured = environ.get(credential.get("helper_path_env", "POC_SECRET_HELPER"))
    command = configured or credential.get("helper_command", "bw-get-secret")
    if not isinstance(command, str) or not command or any(c.isspace() for c in command):
        raise LaunchError("Configure one trusted credential helper executable.")
    resolved = command if os.path.isabs(command) else shutil.which(command, path=environ.get("PATH", ""))
    path = Path(resolved) if resolved else None
    if path is None or path.is_symlink() or not path.is_file() or not os.access(path, os.X_OK):
        raise LaunchError("Trusted credential helper is missing or not executable; configure POC_SECRET_HELPER.")
    return str(path)


def _scalar(raw: str) -> str:
    if not isinstance(raw, str):
        raise LaunchError("Credential field must contain one scalar API key.")
    # Helpers conventionally print one newline; do not strip arbitrary whitespace
    # or accept an entire notes document as a credential.
    value = raw[:-2] if raw.endswith("\r\n") else raw[:-1] if raw.endswith("\n") else raw
    if (not value or len(value) > 4096 or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)
        or any(c in value for c in "{}[]<>\"'=:;")):
        raise LaunchError("Credential field must contain one scalar API key.")
    return value


def resolve_key(credential: dict, *, run=bounded_helper) -> str:
    """Resolve exactly the named item, without inherited-key or item fallback."""
    if credential.get("item") != "[Env] (Ochsner PoC) OPENAI_API_KEY" or credential.get("field") not in ("auto", "password", "notes"):
        raise LaunchError("Unsupported Ochsner credential configuration.")
    helper = helper_executable(credential)
    fields = ("password", "notes") if credential["field"] == "auto" else (credential["field"],)
    values = []
    for field in fields:
        try:
            result = run([helper, credential["item"], field], timeout=15, max_bytes=8192,
                         env=child_environment(os.environ, settings={}))
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            raise LaunchError("Credential unavailable; check the named item and trusted helper.") from None
        if result.returncode != 0:
            raise LaunchError("Credential unavailable; check the named item and trusted helper.")
        if result.stdout in ("", "\n", "\r\n") and credential["field"] == "auto":
            continue
        values.append(_scalar(result.stdout))
    if len(values) != 1:
        raise LaunchError("Credential item must have exactly one scalar password or notes field.")
    return values[0]
