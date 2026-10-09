"""Plain native-stage inputs; no plugins, shell interpolation or extra model."""
import json
from pathlib import Path
import re

STAGES = ("specify", "clarify", "plan", "tasks", "analyze", "implement")


def strict_json(data: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"Non-finite JSON value: {value}")

    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON: {error.msg}") from error


def normalize_guidance(config: dict | None) -> dict:
    config = config if config is not None else {"schema_version": 1}
    if not isinstance(config, dict) or set(config) - {"schema_version", "profile", "common", "stages"}:
        raise ValueError("Guidance accepts only schema_version, profile, common and stages")
    if type(config.get("schema_version")) is not int or config["schema_version"] != 1:
        raise ValueError("Guidance schema_version must be 1")
    profile = config.get("profile", "upstream-only")
    stages = config.get("stages", {})
    if profile not in {"poc-default", "upstream-only"} or not isinstance(stages, dict) or set(stages) - set(STAGES):
        raise ValueError("Choose a known guidance profile and stage")

    def fragments(value):
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("Guidance fragments must be lists of nonempty text")
        return list(value)

    common = fragments(config.get("common", []))
    selected = {stage: fragments(items) for stage, items in stages.items()}
    for stage in STAGES:
        if len("\n".join(common + selected.get(stage, [])).encode()) > 16384:
            raise ValueError("Custom guidance exceeds 16 KiB per stage; shorten it explicitly")
    return {"schema_version": 1, "profile": profile, "common": common, "stages": selected}


def extract_guidance(document: str) -> tuple[str, dict | None]:
    pattern = re.compile(r"^```poc-stage-guidance\s*\n(.*?)^```[ \t]*$", re.M | re.S)
    blocks = list(pattern.finditer(document))
    if len(blocks) > 1 or document.count("```poc-stage-guidance") != len(blocks):
        raise ValueError("Use one complete explicitly labeled guidance block")
    if not blocks:
        return document, None
    block = blocks[0]
    return document[:block.start()] + document[block.end():], normalize_guidance(strict_json(block[1]))


def effective_guidance(config: dict, stage: str, pack: dict | None = None) -> str:
    if stage not in STAGES:
        raise ValueError("Unknown stage")
    config = normalize_guidance(config)
    if pack is None:
        pack = strict_json(Path("reference/bootstrap/guidance/default.json").read_text())
    defaults = [pack.get("common", ""), pack.get("stages", {}).get(stage, "")] if config["profile"] == "poc-default" else []
    return "\n".join(item for item in defaults + config["common"] + config["stages"].get(stage, []) if item)
