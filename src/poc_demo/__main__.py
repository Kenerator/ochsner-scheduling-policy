"""Diagnostics/demo interface; a scenario is not live action authorization."""
import argparse
import json
from . import run_scenario


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="poc-demo")
    parser.add_argument("--scenario", choices=["success", "cancel", "failure", "handoff"], default="success")
    args = parser.parse_args(argv)
    print(json.dumps(run_scenario(args.scenario), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
