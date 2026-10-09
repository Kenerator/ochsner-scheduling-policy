"""Resolve selected, pinned components; never infer traits from names or roles."""
import copy
import json
from pathlib import Path
import re


IDENTITY_KEYS = {"namespace", "id", "name", "aliases", "family_id", "parent",
                 "differences", "revision", "status", "allocation_status"}


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return value


def positive_int(value: int) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("Version/revision must be a positive integer")
    return value


def strings(value: list, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} must be a list of nonempty strings")
    return value


def read_json(path: Path) -> dict:
    """Reject ambiguous duplicate keys and nonstandard NaN/Infinity literals."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_number(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    result = json.loads(Path(path).read_text(encoding="utf-8"),
                        object_pairs_hook=pairs, parse_constant=invalid_number)
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return result


def trait_map(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Traits/overrides must be a flat JSON map")
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip() or key in IDENTITY_KEYS:
            raise ValueError(f"Invalid trait key: {key!r}")
        if item is not None and type(item) not in (str, int, float, bool):
            raise ValueError(f"Trait must be a scalar: {key}")
    json.dumps(value, allow_nan=False)
    return value


def json_equal(left, right) -> bool:
    """Compare actual JSON values, not Python's True == 1 coercion."""
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def validate_basis(label: dict) -> None:
    if not isinstance(label, dict) or set(label) != {"status", "evidence"} or label["status"] not in ("hypothesis", "validated"):
        raise ValueError("Basis requires a status/evidence record")
    strings(label["evidence"], "Evidence")
    if label["status"] == "validated" and not label["evidence"]:
        raise ValueError("Validated attributes require an actual evidence record")


def compose(components: list[dict], *, actor_type: str,
            overrides: dict | None = None, unknowns: list[str] | None = None) -> dict:
    if actor_type not in ("human", "agent", "unknown"):
        raise ValueError("Actor type must be human, agent or unknown")
    if not isinstance(components, list):
        raise ValueError("Components must be a list")
    overrides = trait_map(overrides if overrides is not None else {})
    unknowns = strings(unknowns if unknowns is not None else [], "Unknown keys")
    trait_map({key: None for key in unknowns})
    traits, scenarios, pinned, seen = {}, {}, [], set()
    requirements, references, basis = set(), set(), {}
    for component in components:
        if not isinstance(component, dict) or set(component) - {"id", "version", "traits", "requirements", "scenarios", "references", "basis"}:
            raise ValueError("Unexpected component metadata; identity belongs to the catalog")
        identifier = safe_id(component.get("id"))
        version = positive_int(component.get("version"))
        if identifier in seen:
            raise ValueError(f"Duplicate component: {identifier}")
        seen.add(identifier)
        pinned.append({"id": identifier, "version": version})
        # A reference supports a recommendation, not proof that a persona was researched.
        label = component.get("basis", "hypothesis")
        if label == "hypothesis":
            label = {"status": "hypothesis", "evidence": []}
        validate_basis(label)
        basis[identifier] = label
        for key, value in trait_map(component.get("traits")).items():
            if key in traits and not json_equal(traits[key], value) and key not in overrides:
                raise ValueError(f"Conflicting trait {key} in component {identifier}")
            traits[key] = value
        requirements.update(strings(component.get("requirements", []), "Requirements"))
        for source in strings(component.get("references", []), "References"):
            references.add(safe_id(source))
        entries = component.get("scenarios", [])
        if not isinstance(entries, list):
            raise ValueError("Scenarios must be a list")
        for scenario in entries:
            if not isinstance(scenario, dict) or set(scenario) != {"id", "given", "when", "then"}:
                raise ValueError("Scenario requires id, given, when and then")
            identifier = safe_id(scenario["id"])
            strings([scenario[key] for key in ("given", "when", "then")], "Scenario text")
            if identifier in scenarios and scenarios[identifier] != scenario:
                raise ValueError(f"Conflicting scenario: {identifier}")
            scenarios[identifier] = scenario
    traits.update(overrides)
    for key in unknowns:
        if traits.get(key) is not None:
            raise ValueError(f"Trait {key} has a known value and cannot also be unknown")
        traits.setdefault(key, None)
    return copy.deepcopy({"schema_version": 2, "actor_type": actor_type,
                          "components": sorted(pinned, key=lambda item: item["id"]),
                          "traits": dict(sorted(traits.items())),
                          "requirements": sorted(requirements),
                          "scenarios": [scenarios[key] for key in sorted(scenarios)],
                          "references": sorted(references),
                          "overrides": dict(sorted(overrides.items())), "unknowns": sorted(set(unknowns)),
                          "basis": "validated" if basis and not overrides and not unknowns and all(item["status"] == "validated" for item in basis.values()) else "hypothesis",
                          "component_basis": dict(sorted(basis.items()))})


def load_recipe(recipe_path: Path, components_root: Path) -> dict:
    recipe = read_json(recipe_path)
    refs = recipe.get("components")
    if not isinstance(refs, list):
        raise ValueError("Recipe components must be a list")
    root = Path(components_root).resolve()
    components = []
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"id", "version"}:
            raise ValueError("Recipe component requires exact id/version")
        identifier = safe_id(ref["id"])
        version = positive_int(ref["version"])
        path = root / f"{identifier}.json"
        if not path.resolve().is_relative_to(root):
            raise ValueError("Component path escapes the component root")
        component = read_json(path)
        if component.get("id") != identifier or component.get("version") != version:
            raise ValueError(f"Pinned component version mismatch: {identifier}@{version}")
        components.append(component)
    for field in ("description", "constraint"):
        if field in recipe:
            strings([recipe[field]], field)
    overrides = dict(trait_map(recipe.get("overrides", {})))
    if "constraint" in recipe:
        if "context.constraint" in overrides and not json_equal(overrides["context.constraint"], recipe["constraint"]):
            raise ValueError("Conflicting recipe constraint and override")
        overrides["context.constraint"] = recipe["constraint"]
    result = compose(components, actor_type=recipe.get("actor_type"),
                     overrides=overrides, unknowns=recipe.get("unknowns"))
    if "description" in recipe:
        result["description"] = recipe["description"]
    return result
