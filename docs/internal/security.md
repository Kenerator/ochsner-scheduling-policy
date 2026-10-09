# Basic credential hygiene

Reviewed: **2026-10-07**. No added dependency, global Git setting or online scan.

Fresh Git-enabled scaffolds install a local pre-commit guard. It checks the **whole staged index**, including intake/docs and existing tracked files—not just changed lines or the working copy. Partial staging and Git's temporary commit index are respected. Recognizable tokens, private-key headers, likely literal credential assignments and force-added credential files block the commit. Findings report **path, line and rule only**, never suspected values.

```sh
# Run with a verified Python 3.11+ interpreter:
PYTHONPATH=src python3 -m poc_template secrets scan --project .
# For a generated project or clone with the bundled scanner (hooks aren't cloned):
PYTHONPATH=src python3 -m poc_template secrets install --project .
```

Exit **0** means no unresolved match in the checked index; **1** means findings; **2** means incomplete/error. The hook prefers `POC_PYTHON`, then `.venv/bin/python`, then a compatible Python on PATH. For a tool interpreter outside PATH, use `POC_PYTHON=/absolute/path/to/python git commit ...`; do not replace system Python. Installation is idempotent for this exact guard. An existing hook, symlinked hook directory or `core.hooksPath` is preserved; bootstrap warns and continues, while explicit install reports the conflict. Integrate the scan into your existing hook or run it explicitly—do not overwrite another safeguard.

`.gitignore` keeps common environments, credential files, keys and private-local folders out of ordinary staging; it does **not** protect already-tracked or force-added files.[^ignore] `.gitattributes` normalizes text and scripts to predictable line endings. Keep confidential intake/notes outside Git or in the ignored `docs/product/intake/private/` and `docs/internal/private/` folders. These are manual private-local locations, not automatic routing of `--input`: normal intake is copied into tracked-capable product documents. Do not pass private data to bootstrap expecting it to be anonymized. Private GitHub visibility is not protection against later publication of its history.

## False positives

Prefer environment references or obvious placeholders in examples. For a **reviewed nonsecret fixture**, add a narrow entry to `.poc-secret-allowlist.json` and stage it alongside that exact file:

```json
{"allow": [{"path": "tests/fixture.txt", "rule": "github-token", "sha256": "REPLACE_WITH_64_CHARACTER_SHA256_OF_EXACT_STAGED_BLOB", "reason": "Synthetic nonworking scanner fixture"}]}
```

Compute the digest without printing the content, using the staged blob, not its working copy:

```sh
git show :tests/fixture.txt | python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'
```

Exact path + rule + blob digest + explanation are required; any byte change invalidates the exception. Unstaged exceptions have no effect. No wildcard directory exclusions or automatic waiver creation. Never allow a real credential; remove it from staging and revoke/rotate it if already exposed.

## Limits and optional stronger tooling

This is a small pattern guard, **not** a secret-free/history/PHI/confidentiality certification. It can miss arbitrary opaque passwords, computed/encoded values and unsupported formats. It scans bounded binary bytes for recognizable text too, but does not decode archives/images; symlink targets and submodule contents are not followed and their counts are reported. Blobs over 16 MiB or unresolved merges produce an explicit incomplete result. Hooks can be bypassed; review staged changes and public-sharing rights independently. Existing Git history and external logs need separate attention when sharing.

For a larger project, optionally qualify [Gitleaks](https://github.com/gitleaks/gitleaks) for local history/CI scanning with redacted reports. Pin a reviewed version and keep CI scopes/permissions appropriate; it is not installed or required here. Review current maintenance/tool alternatives when adopting. GitHub push protection is an additional repository setting, not an assumed safeguard on every private repo.[^push]

[^ignore]: [Git: gitignore](https://git-scm.com/docs/gitignore). Reviewed 2026-10-07; ignore rules do not affect already-tracked files.
[^push]: [GitHub: push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection). Reviewed 2026-10-07; repository coverage/configuration must be verified.
