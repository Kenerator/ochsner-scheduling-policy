"""Render snapshots as inert Markdown; public guidance is not persona validation."""
import copy
from datetime import date
import html
import re
from urllib.parse import quote, urlsplit

from .persona_catalog import validate_composition
from .persona_compose import IDENTITY_KEYS, positive_int, safe_id, strings


DEFERRED_STEP = "Select and validate a constraint-rich persona as soon as practical."


def text(value) -> str:
    if value is None:
        return "Unknown (needs validation)"
    if isinstance(value, bool):
        value = "yes" if value else "no"
    # Collapse control/newline characters so prose cannot inject headings or HTML.
    value = " ".join(str(value).split())
    value = html.escape(value, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#!|>~])", r"\\\1", value)


def resolve_sources(snapshot, sources, *, references_enabled=True, exclude=None, overrides=None):
    if type(references_enabled) is not bool:
        raise ValueError("Reference selection must be boolean")
    excluded = set(strings(exclude if exclude is not None else [], "Excluded references"))
    selected = strings(snapshot.get("references", []), "Snapshot references")
    catalog = copy.deepcopy(sources)
    if not isinstance(catalog, dict) or not isinstance(overrides if overrides is not None else {}, dict):
        raise ValueError("Sources/overrides must be maps")
    for identifier, fields in (overrides or {}).items():
        if not isinstance(fields, dict):
            raise ValueError("Reference override must be a field map")
        catalog[identifier] = {**catalog.get(identifier, {}), **fields}
    if not references_enabled:
        return {}
    result = {}
    for identifier in sorted(set(selected) - excluded):
        safe_id(identifier)
        source = catalog.get(identifier)
        if not isinstance(source, dict):
            raise ValueError(f"Missing research source: {identifier}")
        for field in ("title", "url", "reviewed", "finding", "limitation"):
            strings([source.get(field)], f"Source {identifier}/{field}")
        url = source["url"]
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or any(char.isspace() or ord(char) < 32 for char in url):
            raise ValueError("Research references require credential-free HTTPS URLs")
        date.fromisoformat(source["reviewed"])
        result[identifier] = source
    return result


def definitions(sources) -> str:
    lines = []
    for identifier, source in sorted(sources.items()):
        url = quote(source["url"], safe=":/?&=%#@+,-_.~")
        lines.append(f"[^{identifier}]: [{text(source['title'])}]({url}). Reviewed {text(source['reviewed'])}. {text(source['finding'])}. Limit: {text(source['limitation'])}.")
    return "\n".join(lines)


def card(snapshot, sources) -> str:
    validate_composition({key: value for key, value in snapshot.items() if key not in IDENTITY_KEYS})
    safe_id(snapshot.get("namespace"))
    safe_id(snapshot.get("id"))
    positive_int(snapshot.get("revision"))
    if snapshot.get("actor_type") not in ("human", "agent", "unknown"):
        raise ValueError("Invalid snapshot actor type")
    identity = f"{snapshot['namespace']}:{snapshot['id']}@{snapshot['revision']}"
    lines = [f"## {text(snapshot.get('name'))} — {text(snapshot.get('description', 'Persona'))}", "",
             f"Identity: {identity} · Actor type: {snapshot['actor_type']}", "",
             "Hypothesis — validate relevant needs with users." if snapshot.get("basis") == "hypothesis" else
             "Evidence label: supplied validation record; not independently verified by this utility.", "",
             f"Family: {text(snapshot.get('family_id', 'unassigned'))} · Snapshot-time status: {text(snapshot.get('status', 'unknown'))}"]
    if snapshot.get("parent"):
        parent = snapshot["parent"]
        lines += [f"Parent: {snapshot['namespace']}:{safe_id(parent['id'])}@{positive_int(parent['revision'])}",
                  "Differences: " + "; ".join(text(item) for item in snapshot.get("differences", []))]
    if snapshot.get("component_basis"):
        lines += ["Basis records: " + "; ".join(f"{text(identifier)}: {text(record['status'])}" +
                  (" — " + "; ".join(text(item) for item in record['evidence']) if record['evidence'] else "")
                  for identifier, record in sorted(snapshot["component_basis"].items()))]
    if snapshot["schema_version"] == 1:
        lines += ["Legacy provenance: overrides were not recorded; this saved hypothesis is unchanged."]
    elif snapshot["overrides"]:
        lines += ["Overrides (hypotheses): " + "; ".join(f"{text(key)}: {text(value)}" for key, value in snapshot["overrides"].items())]
    if snapshot.get("unknowns"):
        lines += ["Explicit unknowns: " + "; ".join(text(key) for key in snapshot["unknowns"])]
    lines += ["", "Traits:", ""]
    lines += [f"- {text(key)}: {text(value)}" for key, value in sorted(snapshot.get("traits", {}).items())]
    if snapshot.get("requirements"):
        lines += ["", "Acceptance requirements:", ""]
        lines += [f"- {text(item)}" for item in snapshot["requirements"]]
    if snapshot.get("scenarios"):
        lines += ["", "Scenarios:", ""]
        for scenario in snapshot["scenarios"]:
            lines.append(f"- {text(scenario['id'])}: Given {text(scenario['given'])}; when {text(scenario['when'])}; then {text(scenario['then'])}.")
    if sources:
        lines += ["", "Research-informed design guidance (not persona validation): " + " ".join(f"[^{identifier}]" for identifier in sorted(sources))]
    lines += ["", "Persona descriptions grant no permissions. Test these obligations in the actual application."]
    return "\n".join(lines)


def render_card(snapshot: dict, sources: dict, *, references_enabled: bool = True,
                exclude: list[str] | None = None, overrides: dict | None = None) -> str:
    resolved = resolve_sources(snapshot, sources, references_enabled=references_enabled, exclude=exclude, overrides=overrides)
    return card(snapshot, resolved) + ("\n\n" + definitions(resolved) if resolved else "") + "\n"


def render_selection(snapshots: list[dict], sources: dict, **options) -> tuple[str, list[str]]:
    cards, references = [], {}
    for snapshot in snapshots:
        resolved = resolve_sources(snapshot, sources, **options)
        references.update(resolved)
        cards.append(card(snapshot, resolved))
    steps = []
    # Access constraints are as actionable as the older general-context field.
    if not any(snapshot.get("traits", {}).get("context.constraint") or
               snapshot.get("traits", {}).get("access.constraint") for snapshot in snapshots):
        cards.append("## Persona selection deferred\n\n" + DEFERRED_STEP)
        steps.append(DEFERRED_STEP)
    document = "# Selected personas\n\n" + "\n\n".join(cards)
    if references:
        document += "\n\n" + definitions(references)
    return document + "\n", steps
