"""One locally locked, atomically replaced catalog retains every identity revision.

This lock protects one filesystem copy, not independent Git working copies.
Validate after merging; never auto-remove a lock or replay an ambiguous write.
"""
import copy
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
import uuid

from .persona_compose import IDENTITY_KEYS, json_equal, positive_int, read_json, safe_id, strings, trait_map, validate_basis


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Name must be text")
    normalized = unicodedata.normalize("NFKC", name).casefold()
    normalized = re.sub(r"[\W_]+", "-", normalized).strip("-")
    if not normalized:
        raise ValueError("Name must contain letters or numbers")
    return normalized


def validate_composition(value: dict) -> None:
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] not in (1, 2):
        raise ValueError("Invalid composition schema")
    fields = {"schema_version", "actor_type", "components", "traits", "requirements", "references", "scenarios", "basis", "component_basis"}
    if value["schema_version"] == 2:
        fields |= {"overrides", "unknowns"}
    if not fields <= set(value) or set(value) - fields - {"description"}:
        raise ValueError("Invalid composition fields")
    if value.get("actor_type") not in ("human", "agent", "unknown"):
        raise ValueError("Invalid actor type")
    trait_map(value.get("traits"))
    if value.get("basis") not in ("hypothesis", "validated"):
        raise ValueError("Invalid research basis")
    for field in ("requirements", "references"):
        strings(value.get(field), field)
    for reference in value["references"]:
        safe_id(reference)
    components, seen = value.get("components"), set()
    if not isinstance(components, list):
        raise ValueError("Components must be pinned")
    for ref in components:
        if not isinstance(ref, dict) or set(ref) != {"id", "version"}:
            raise ValueError("Invalid pinned component")
        identifier = safe_id(ref["id"])
        positive_int(ref["version"])
        if identifier in seen:
            raise ValueError("Duplicate pinned component")
        seen.add(identifier)
    basis = value["component_basis"]
    if not isinstance(basis, dict) or set(basis) != seen:
        raise ValueError("Basis records must exactly match pinned components")
    for label in basis.values():
        validate_basis(label)
    if value["schema_version"] == 1:
        # Old revisions omitted override provenance; keep them intact, not relabeled.
        if value["basis"] != "hypothesis":
            raise ValueError("Legacy validated composition lacks override provenance")
    else:
        overrides = trait_map(value["overrides"])
        unknowns = strings(value["unknowns"], "Unknown keys")
        trait_map({key: None for key in unknowns})
        if any(key not in value["traits"] or not json_equal(item, value["traits"][key]) for key, item in overrides.items()):
            raise ValueError("Override provenance does not match resolved traits")
        if any(key not in value["traits"] for key in unknowns):
            raise ValueError("Unknown keys must remain represented in traits")
        for key in unknowns:
            if value["traits"][key] is not None:
                raise ValueError(f"Trait {key} has a known value and cannot also be unknown")
        expected = "validated" if basis and not overrides and not unknowns and all(item["status"] == "validated" for item in basis.values()) else "hypothesis"
        if value["basis"] != expected:
            raise ValueError("Research basis disagrees with components/additions")
    scenarios = value.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("Scenarios must be a list")
    seen = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict) or set(scenario) != {"id", "given", "when", "then"}:
            raise ValueError("Invalid scenario")
        identifier = safe_id(scenario["id"])
        strings([scenario[key] for key in ("given", "when", "then")], "Scenario text")
        if identifier in seen:
            raise ValueError("Duplicate scenario")
        seen.add(identifier)
    if "description" in value and not isinstance(value["description"], str):
        raise ValueError("Description must be text")
    json.dumps(value, allow_nan=False)


def validate_data(data: dict) -> None:
    if set(data) != {"schema_version", "namespace", "generation", "personas"} or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Invalid catalog schema")
    safe_id(data["namespace"])
    if type(data["generation"]) is not int or data["generation"] < 0 or not isinstance(data["personas"], dict):
        raise ValueError("Invalid catalog generation/personas")
    reservations = set()
    immutable = ("name", "aliases", "family_id", "parent", "differences", "allocation_status")
    for identifier, record in data["personas"].items():
        safe_id(identifier)
        if not isinstance(record, dict) or set(record) != {*immutable, "status", "revisions"}:
            raise ValueError("Invalid persona record")
        strings(record["aliases"], "Aliases")
        safe_id(record["family_id"])
        strings(record["differences"], "Differences")
        if record["status"] not in ("active", "retired") or record["allocation_status"] not in ("provisional", "authoritative"):
            raise ValueError("Invalid identity status")
        for name in [record["name"], *record["aliases"]]:
            normalized = normalize_name(name)
            if normalized in reservations:
                raise ValueError(f"Name/alias reserved: {name}")
            reservations.add(normalized)
        revisions = record["revisions"]
        if not isinstance(revisions, dict) or not revisions:
            raise ValueError("Missing retained revisions")
        if set(revisions) != {str(n) for n in range(1, len(revisions) + 1)}:
            raise ValueError("Revisions must start at 1 and remain contiguous")
        original = revisions["1"]
        for revision, snapshot in revisions.items():
            if not isinstance(snapshot, dict):
                raise ValueError("Invalid snapshot")
            positive_int(snapshot.get("revision"))
            if snapshot["revision"] != int(revision) or snapshot.get("id") != identifier or snapshot.get("namespace") != data["namespace"]:
                raise ValueError("Snapshot identity/revision drift")
            if snapshot.get("status") not in ("active", "retired"):
                raise ValueError("Invalid snapshot-time status")
            if any(snapshot.get(field) != record[field] for field in immutable):
                raise ValueError("Immutable identity metadata drift")
            behavior = {key: value for key, value in snapshot.items() if key not in IDENTITY_KEYS}
            validate_composition(behavior)
            # Same-identity revisions may edit prose, never behavioral fixtures.
            if not json_equal({key: value for key, value in behavior.items() if key != "description"}, {
                key: value for key, value in original.items() if key not in IDENTITY_KEYS and key != "description"
            }):
                raise ValueError("Behavior changed within an identity; derive a variant")
        parent = record["parent"]
        if parent is not None:
            if not isinstance(parent, dict) or set(parent) != {"id", "revision"}:
                raise ValueError("Parent requires pinned id/revision")
            safe_id(parent["id"])
            positive_int(parent["revision"])
            target = data["personas"].get(parent["id"])
            if not isinstance(target, dict) or str(parent["revision"]) not in target.get("revisions", {}):
                raise ValueError("Missing parent revision")
            if target.get("family_id") != record["family_id"] or not record["differences"]:
                raise ValueError("A variant needs its parent's family and explicit differences")
            pinned_parent = target["revisions"][str(parent["revision"])]
            behavior_fields = ("actor_type", "traits", "requirements", "scenarios")
            if json_equal({key: original[key] for key in behavior_fields},
                          {key: pinned_parent[key] for key in behavior_fields}):
                raise ValueError("Unchanged variant behavior; reuse the pinned parent instead")
    for identifier in data["personas"]:
        ancestry = set()
        current = identifier
        while current is not None:
            if current in ancestry:
                raise ValueError("Cyclic persona lineage")
            ancestry.add(current)
            parent = data["personas"][current]["parent"]
            current = parent["id"] if parent else None


class Catalog:
    def __init__(self, path: Path, *, namespace: str | None = None):
        self.path = Path(path)
        self.lock = self.path.with_suffix(self.path.suffix + ".lock")
        self.namespace = safe_id(namespace) if namespace is not None else None

    def _read(self) -> dict:
        if self.path.is_symlink():
            raise ValueError("Symlinked catalog is not allowed")
        if self.path.exists():
            data = read_json(self.path)
            if self.namespace is not None and data.get("namespace") != self.namespace:
                raise ValueError("Existing catalog namespace must be preserved")
        else:
            data = {"schema_version": 1, "namespace": self.namespace or str(uuid.uuid4()),
                    "generation": 0, "personas": {}}
        validate_data(data)
        return data

    def _change(self, operation):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink() or self.lock.is_symlink():
            raise ValueError("Symlinked catalog/lock is not allowed")
        try:
            descriptor = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            raise ValueError(f"Catalog writer busy: inspect {self.lock} and the catalog before recovery; do not blindly replay") from None
        owned = os.fstat(descriptor)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(f"pid={os.getpid()}\n")
            data = self._read()  # Must reread while holding the lock.
            result = operation(data)
            data["generation"] += 1
            validate_data(data)
            descriptor, temporary = tempfile.mkstemp(prefix=".catalog-", dir=self.path.parent)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                Path(temporary).unlink(missing_ok=True)
            return copy.deepcopy(result)
        finally:
            # Never remove a replacement lock belonging to someone else.
            try:
                current = self.lock.lstat()
                if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                    self.lock.unlink()
            except FileNotFoundError:
                pass

    def create(self, composition: dict, *, name: str, persona_id: str, family_id: str,
               aliases: list[str] | None = None, parent: tuple[str, int] | None = None,
               differences: list[str] | None = None, authoritative: bool = False) -> dict:
        validate_composition(composition)
        if composition["schema_version"] != 2:
            raise ValueError("New allocations require schema-2 provenance; compose again explicitly")
        if IDENTITY_KEYS & set(composition):
            raise ValueError("Composition cannot set identity metadata")
        safe_id(persona_id)
        safe_id(family_id)
        normalize_name(name)
        if type(authoritative) is not bool:
            raise ValueError("Authoritative allocation must be an explicit boolean")
        aliases = strings(aliases if aliases is not None else [], "Aliases")
        differences = strings(differences if differences is not None else [], "Differences")
        if parent is not None:
            if not isinstance(parent, tuple) or len(parent) != 2:
                raise ValueError("Parent must be (id, revision)")
            safe_id(parent[0])
            positive_int(parent[1])
        def allocate(data):
            if persona_id in data["personas"]:
                raise ValueError("Persona ID already reserved")
            record = {"name": name, "aliases": aliases, "family_id": family_id,
                      "parent": {"id": parent[0], "revision": parent[1]} if parent else None,
                      "differences": differences, "status": "active",
                      "allocation_status": "authoritative" if authoritative else "provisional"}
            snapshot = {**copy.deepcopy(composition), **copy.deepcopy(record),
                        "namespace": data["namespace"], "id": persona_id, "revision": 1}
            data["personas"][persona_id] = {**record, "revisions": {"1": snapshot}}
            return snapshot
        return self._change(allocate)

    def get(self, persona_id: str, revision: int) -> dict:
        safe_id(persona_id)
        positive_int(revision)
        try:
            return copy.deepcopy(self._read()["personas"][persona_id]["revisions"][str(revision)])
        except KeyError:
            raise ValueError(f"Unknown pinned persona: {persona_id}@{revision}") from None

    def revise_description(self, persona_id: str, description: str) -> dict:
        safe_id(persona_id)
        if not isinstance(description, str):
            raise ValueError("Description must be text")
        def revise(data):
            record = data["personas"].get(persona_id)
            if record is None or record["status"] != "active":
                raise ValueError("Unknown or retired persona")
            revision = len(record["revisions"]) + 1
            snapshot = copy.deepcopy(record["revisions"][str(revision - 1)])
            snapshot.update(revision=revision, description=description)
            record["revisions"][str(revision)] = snapshot
            return snapshot
        return self._change(revise)

    def retire(self, persona_id: str) -> None:
        safe_id(persona_id)
        def retire(data):
            if persona_id not in data["personas"]:
                raise ValueError("Unknown persona")
            data["personas"][persona_id]["status"] = "retired"
        self._change(retire)

    def validate(self) -> None:
        self._read()

    def available_name(self, pool: list[str]) -> str:
        strings(pool, "Name pool")
        reserved = {normalize_name(name) for record in self._read()["personas"].values()
                    for name in [record["name"], *record["aliases"]]}
        for name in pool:
            if normalize_name(name) not in reserved:
                return name
        raise ValueError("Name pool exhausted; add an unused name explicitly")

    def list(self) -> list[dict]:
        """Current availability plus explicitly pinned latest revisions for selection."""
        data = self._read()
        return [{"id": identifier, "name": record["name"], "status": record["status"],
                 "revision": len(record["revisions"]), "namespace": data["namespace"]}
                for identifier, record in sorted(data["personas"].items())]
