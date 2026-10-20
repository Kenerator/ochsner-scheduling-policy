"""No-shell application launcher. Help and doctor never retrieve a key."""
import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys

import credentials
from credentials import LaunchError


@dataclass(frozen=True)
class LaunchRequest:
    mode: str
    interface: str
    model: str | None
    api_port: int | None
    ui_port: int | None
    transport_port: int | None


MODELS = {"bob": "BOB_OPENAI_MODEL", "enhanced": "OPENAI_MODEL", "lab": "OPENAI_MODEL",
          "policy": "OPENAI_MODEL", "mvp": "SCHEDULING_MODEL"}
INTERFACES = {"bob": ("browser", "cli"), "enhanced": ("cli", "browser"), "lab": ("browser", "cli"),
              "policy": ("cli",), "mvp": ("cli", "browser")}


def _keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise LaunchError("Application launch configuration has unsupported or missing fields.")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LaunchError("Application launch configuration contains duplicate fields.")
        result[key] = value
    return result


def _model(value):
    if not isinstance(value, str) or not value or len(value) > 200 or any(c.isspace() or ord(c) < 32 for c in value):
        raise LaunchError("Configure one nonempty model name without whitespace.")
    return value


def load_config(path: Path) -> dict:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
            raise LaunchError("Application launch configuration must be a bounded regular file.")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
    except LaunchError:
        raise
    except (OSError, UnicodeError, ValueError):
        raise LaunchError("Cannot read application launch configuration.") from None
    _keys(value, ("schema_version", "project_id", "adapter", "default_interface", "credential", "model"))
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise LaunchError("Unsupported application launch schema version.")
    adapter = value["adapter"]
    if not isinstance(adapter, str) or adapter not in MODELS:
        raise LaunchError("Unsupported application adapter.")
    if not isinstance(value["project_id"], str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", value["project_id"]) or len(value["project_id"]) > 80:
        raise LaunchError("Application project ID must be a bounded technical slug.")
    if value["default_interface"] not in INTERFACES[adapter]:
        raise LaunchError("Unsupported application interface.")
    credential = value["credential"]
    _keys(credential, ("item", "field", "helper_path_env", "helper_command"))
    credentials.validate_selection(credential)
    if (credential["helper_path_env"] != "POC_SECRET_HELPER"
        or credential["helper_command"] != "bw-get-secret"):
        raise LaunchError("Unsupported credential helper configuration.")
    model = value["model"]
    _keys(model, ("default", "environment"))
    if model["environment"] != MODELS[adapter]:
        raise LaunchError("Unsupported model environment setting.")
    if model["default"] is not None:
        _model(model["default"])
    return value


class SafeParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, allow_abbrev=False, **kwargs)

    def error(self, message):
        # argparse's normal error can quote raw argv. Emit a fixed safe category.
        raise LaunchError("Invalid launcher arguments; use --help for supported options.")


def resolve_request(config: dict, argv: list[str], environ) -> LaunchRequest:
    parser = SafeParser(add_help=False)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--interface", choices=("browser", "cli"))
    parser.add_argument("--model")
    for name in ("api-port", "ui-port", "transport-port"):
        parser.add_argument("--" + name, type=int)
    options = parser.parse_args(argv)
    adapter = config["adapter"]
    interface = options.interface or config["default_interface"]
    if interface not in INTERFACES[adapter]:
        raise LaunchError("This adapter does not support the selected interface.")
    if options.offline and adapter not in ("bob", "lab", "policy"):
        raise LaunchError("Interactive offline mode is unsupported; use the documented deterministic demos.")
    ports = (options.api_port, options.ui_port, options.transport_port)
    if any(port is not None and not 1024 <= port <= 65535 for port in ports):
        raise LaunchError("Use a loopback service port between 1024 and 65535.")
    selected = options.model if options.model is not None else environ.get(config["model"]["environment"], config["model"]["default"])
    model = None if options.offline else _model(selected)
    return LaunchRequest("offline" if options.offline else "model", interface, model, *ports)


def main(argv: list[str] | None = None) -> int:
    parser = SafeParser(description="Launch a configured Ochsner PoC in real model mode; --offline is explicit where supported.")
    parser.add_argument("--config", type=Path, default=Path("poc-launch.json"))
    parser.add_argument("--doctor", action="store_true", help="Check readiness without credentials, startup or model calls")
    parser.add_argument("--offline", action="store_true", help="Explicit no-model mode where supported")
    parser.add_argument("--interface", choices=("browser", "cli"))
    parser.add_argument("--model")
    for name in ("api-port", "ui-port", "transport-port"):
        parser.add_argument("--" + name, type=int)
    try:
        try:
            options = parser.parse_args(argv)
        except SystemExit as exit_status:
            return int(exit_status.code)
        config = load_config(options.config)
        request_argv = []
        if options.offline:
            request_argv.append("--offline")
        for name in ("interface", "model", "api_port", "ui_port", "transport_port"):
            value = getattr(options, name)
            if value is not None:
                request_argv.extend(("--" + name.replace("_", "-"), str(value)))
        request = resolve_request(config, request_argv, os.environ)
        from adapters import preflight, process_specs
        root = options.config.resolve().parent
        preflight(root, config, request)
        if options.doctor:
            if request.mode == "model":
                credentials.helper_executable(config["credential"])
            print("Application configuration, dependencies, ports and accounting are ready; no credentials retrieved or model request made.")
            return 0
        key = credentials.resolve_key(config["credential"]) if request.mode == "model" else None
        from processes import run_owned
        return run_owned(process_specs(root, config, request, key=key))
    except LaunchError as error:
        print(str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt as error:
        # Notes may contain private upstream diagnostics. Emit only our fixed
        # category, conservatively retaining uncertainty rather than raw notes.
        if getattr(error, "__notes__", ()):
            print("Application launch cancelled; owned cleanup could not be verified.", file=sys.stderr)
        else:
            print("Application launch cancelled; owned children were stopped.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
