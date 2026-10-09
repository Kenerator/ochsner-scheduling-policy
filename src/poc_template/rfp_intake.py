"""Bounded local RFP snapshot; never execute, interpret or publish client files."""
import hashlib
import json
import os
from pathlib import Path
import stat

INDEX = "docs/product/RFP/README.md"
MANIFEST = "docs/product/RFP/manifest.json"
SOURCE = "docs/product/RFP/source"
LIMIT = 16 * 1024 * 1024
ATTACHMENTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
               ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".ico",
               ".zip", ".gz", ".tar", ".7z", ".mp3", ".mp4", ".wav",
               ".bin", ".so", ".dylib", ".exe", ".pyc"}


def snapshot_rfp(source: Path, used_bytes: int = 0) -> dict:
    """Preserve relative paths/bytes, index every file and refuse unsafe omissions."""
    source = Path(source)
    if source.is_symlink() or not source.is_dir():
        raise ValueError("RFP must be an existing, non-symlink directory")
    files, directories, entries = {}, [SOURCE], []
    total, count = used_bytes, 0
    # Do not silently skip inaccessible subtrees (os.walk's default).
    def walk_error(error):
        raise ValueError("RFP directory cannot be fully read") from error
    for folder, children, names in os.walk(source, followlinks=False, onerror=walk_error):
        children.sort()
        for name in sorted(children + names):
            count += 1
            if count > 1024:
                raise ValueError("RFP exceeds 1024 entries; preprocess explicitly")
            path = Path(folder) / name
            relative = SOURCE + "/" + path.relative_to(source).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError("RFP contains a symlink; provide regular local sources")
            if stat.S_ISDIR(mode):
                directories.append(relative)
                continue
            if not stat.S_ISREG(mode):
                raise ValueError("RFP children must be regular files or directories")
            with path.open("rb") as stream:
                data = stream.read(LIMIT - total + 1)
            total += len(data)
            if total > LIMIT:
                raise ValueError("Total intake/RFP exceeds 16 MiB; preprocess explicitly")
            kind, reason = "text", ""
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                kind, reason = "attachment", "Not UTF-8 text; review or convert explicitly"
            if path.suffix.lower() in ATTACHMENTS or b"\x00" in data:
                kind, reason = "attachment", "Attachment; review or convert explicitly"
            files[relative] = data
            entry = {"path": relative, "sha256": hashlib.sha256(data).hexdigest(),
                     "bytes": len(data), "kind": kind}
            if reason:
                entry["note"] = reason
            entries.append(entry)
    entries.sort(key=lambda item: item["path"])
    files[MANIFEST] = (json.dumps({"schema_version": 1, "files": entries}, indent=2) + "\n").encode()
    return {"files": files, "directories": sorted(directories), "entries": entries,
            "summary": {"index": INDEX, "manifest": MANIFEST, "files": len(entries),
                        "text_files": sum(item["kind"] == "text" for item in entries),
                        "attachments": sum(item["kind"] == "attachment" for item in entries),
                        "bytes": total - used_bytes}}
