"""Explicit adapters for existing applications, not arbitrary shell recipes."""
import importlib
import importlib.util
import os
from pathlib import Path
import socket
import sys
import uuid

from credentials import LaunchError, child_environment
from launch import INTERFACES, LaunchRequest
from processes import ProcessSpec, require_listener_probe


API_PORTS = {"enhanced": 4011, "lab": 4013, "policy": 4012, "mvp": 4010}
UI_PORTS = {"bob": 28450, "enhanced": 28452, "lab": 28454, "mvp": 28456}
VENDOR = {"enhanced": "vendor/reference/mock-api/server.py", "lab": "vendor/reference-api/mock-api/server.py",
          "policy": "reference/mock-api/server.py", "mvp": "vendor/scheduling-reference/mock-api/server.py"}
PACKAGES = {"bob": "ochsner_bob", "enhanced": "guarded_scheduling", "lab": "appointment_assistant",
            "policy": "scheduling_assistant", "mvp": "scheduling_assistant"}
APPS = {"bob": "apps/scheduling_app.py", "enhanced": "apps/scheduling.py", "lab": "apps/lab.py",
        "mvp": "apps/scheduling_app.py"}


def check_ports(ports: list[int]) -> None:
    if (len(set(ports)) != len(ports) or any(type(p) is not int or not 1024 <= p <= 65535 for p in ports)):
        raise LaunchError("Use distinct loopback service ports between 1024 and 65535.")
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", port))
        except OSError:
            raise LaunchError("A requested loopback port is occupied; choose a different port. No existing process was stopped.") from None


def _regular(root: Path, relative: str) -> Path:
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
        current = path
        while current != root:
            if current.is_symlink():
                raise ValueError()
            current = current.parent
        if not path.is_file():
            raise ValueError()
    except (OSError, ValueError):
        raise LaunchError("A required application file is missing or unsafe; check the project installation.") from None
    return path


def _ports(config: dict, request: LaunchRequest):
    adapter = config["adapter"]
    if request.interface not in INTERFACES[adapter] or request.mode not in ("model", "offline"):
        raise LaunchError("Unsupported application request.")
    if request.mode == "offline" and adapter not in ("bob", "lab", "policy"):
        raise LaunchError("This application has no interactive offline mode.")
    if request.interface == "cli" and request.ui_port is not None:
        raise LaunchError("A UI port applies only to browser mode.")
    if adapter == "bob" and request.interface == "browser" and request.api_port is not None:
        raise LaunchError("BOB browser owns its ephemeral synthetic API; do not supply --api-port.")
    if request.interface == "cli" and request.transport_port is not None:
        raise LaunchError("A transport port applies only to BOB browser mode.")
    if adapter != "bob" and request.transport_port is not None:
        raise LaunchError("A transport port applies only to BOB.")
    api = (None if adapter == "bob" and request.interface == "browser" else
           request.api_port if request.api_port is not None else
           4010 if adapter == "bob" else API_PORTS[adapter])
    ui = (request.ui_port if request.ui_port is not None else UI_PORTS[adapter]) if request.interface == "browser" else None
    transport = (request.transport_port if request.transport_port is not None else 28451) if adapter == "bob" and request.interface == "browser" else None
    ports = [p for p in (api, ui, transport) if p is not None]
    if len(set(ports)) != len(ports) or any(type(p) is not int or not 1024 <= p <= 65535 for p in ports):
        raise LaunchError("Use distinct bounded loopback service ports.")
    return api, ui, transport


def process_specs(root: Path, config: dict, request: LaunchRequest, *, key: str | None = None) -> list[ProcessSpec]:
    root = root.resolve()
    adapter = config["adapter"]
    api, ui, transport = _ports(config, request)
    if request.mode == "model" and (not request.model or key is None):
        raise LaunchError("Real model mode requires an explicit model and the named credential.")
    public = {"PYTHONPATH": str(root / "src")}
    settings = dict(public)
    if request.mode == "model":
        settings[config["model"]["environment"]] = request.model
    model_key = key if request.mode == "model" else None
    specs = []
    if adapter == "bob":
        # This new effect namespace never changes BOB's canonical budget path.
        namespace = root / ".bob-local" / ("launch-" + uuid.uuid4().hex)
        if request.mode == "model":
            settings["BOB_ENABLE_OPENAI"] = "1"
        if request.interface == "cli":
            # CLI has no nested mock owner: supervise the unchanged server
            # directly, and bind the application to this launch's exact port.
            specs.append(ProcessSpec("mock", (sys.executable, str(root / "vendor/reference/mock-api/server.py"),
                                     "--port", str(api)), child_environment(os.environ, settings=public), api))
            argv = (sys.executable, "-m", "ochsner_bob", "--api-url", f"http://127.0.0.1:{api}",
                    "--journal", str(namespace / "effects.json"))
            if request.mode == "model":
                argv += ("--openai",)
            specs.append(ProcessSpec("model", argv, child_environment(os.environ, settings=settings, key=model_key)))
            return specs
        argv = (sys.executable, str(root / "scripts/serve_browser.py"), "--port", str(transport),
                "--ui-port", str(ui), "--namespace", str(namespace))
        if request.mode == "model":
            argv += ("--openai",)
        specs.append(ProcessSpec("model", argv, child_environment(os.environ, settings=settings, key=model_key), transport))
        viewer = public | {"BOB_TRANSPORT_URL": f"http://127.0.0.1:{transport}"}
        specs.append(ProcessSpec("viewer", _marimo(root, APPS[adapter], ui),
                                 child_environment(os.environ, settings=viewer), ui))
        return specs
    # Directly own the unchanged vendor server rather than a wrapper's nested
    # child: terminating a wrapper on SIGTERM cannot strand its subprocess.
    specs.append(ProcessSpec("mock", (sys.executable, str(root / VENDOR[adapter]), "--port", str(api)),
                             child_environment(os.environ, settings=public), api))
    url = f"http://127.0.0.1:{api}"
    if adapter == "lab":
        mode = "openai" if request.mode == "model" else "rehearsal"
        settings.update(SCHEDULING_MODE=mode, API_BASE=url)
        argv = (sys.executable, "-m", "appointment_assistant", "--mode", mode, "--api-base", url)
        if request.mode == "model":
            argv += ("--model", request.model)
    elif adapter == "enhanced":
        settings["SCHEDULING_API_URL"] = url
        argv = (sys.executable, "-m", "guarded_scheduling", "--api-url", url)
    elif adapter == "policy":
        mode = "live" if request.mode == "model" else "offline"
        argv = (sys.executable, "-m", "scheduling_assistant", "--intent-mode", mode, "--api-base", url)
        if request.mode == "model":
            argv += ("--model", request.model)
    else:
        settings["SCHEDULING_API_URL"] = url
        argv = (sys.executable, "-m", "scheduling_assistant", "--model", request.model, "--api-base-url", url)
    if request.interface == "browser":
        argv = _marimo(root, APPS[adapter], ui)
    specs.append(ProcessSpec("model", argv, child_environment(os.environ, settings=settings, key=model_key), ui))
    return specs


def _marimo(root, app, port):
    return (sys.executable, "-m", "marimo", "run", str(root / app), "--headless", "--host", "127.0.0.1", "--port", str(port))


def check_bob_budget(root: Path, model: str) -> None:
    """Check existing accounting storage/model support, not a runtime spend grant."""
    _regular(root, "src/ochsner_bob/model_budget.py")
    source = str(root / "src")
    sys.path.insert(0, source)
    try:
        budget = importlib.import_module("ochsner_bob.model_budget")
        if Path(budget.__file__).resolve() != (root / "src/ochsner_bob/model_budget.py").resolve():
            raise ValueError()
        readiness = getattr(budget, "preflight_budget", None)
        if not callable(readiness):
            raise ValueError()
        readiness(root / ".bob-local/model-budget.json", model=model)
    except Exception:
        raise LaunchError("BOB model accounting is unavailable or incompatible; no new ledger was created.") from None
    finally:
        sys.path.remove(source)


def preflight(root: Path, config: dict, request: LaunchRequest) -> None:
    if sys.version_info < (3, 11):
        raise LaunchError("Use a project Python 3.11 or newer.")
    root = root.resolve()
    adapter = config["adapter"]
    api, ui, transport = _ports(config, request)
    if any(port is not None for port in (api, ui, transport)):
        require_listener_probe()
    _regular(root, f"src/{PACKAGES[adapter]}/__main__.py")
    if adapter == "bob":
        _regular(root, "vendor/reference/mock-api/server.py")
        if request.interface == "browser":
            _regular(root, "scripts/mock_lifecycle.py")
            _regular(root, "scripts/serve_browser.py")
        if request.mode == "model":
            check_bob_budget(root, request.model)
    else:
        _regular(root, VENDOR[adapter])
    if request.interface == "browser":
        _regular(root, APPS[adapter])
        for dependency in (("marimo", "anywidget", "traitlets") if adapter == "bob" else ("marimo",)):
            if importlib.util.find_spec(dependency) is None:
                raise LaunchError("A browser dependency is missing; install the declared project environment.")
    check_ports([p for p in (api, ui, transport) if p is not None])
