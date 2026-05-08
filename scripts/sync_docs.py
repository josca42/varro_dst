from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = SKILL_ROOT.parent / "agent_data"
DEST = SKILL_ROOT / "docs"
COPIED_DIRS = ("subjects", "fact", "dim", "geo")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", default=str(DEFAULT_SOURCE))
    parser.add_argument("--dest", default=str(DEST))
    return parser.parse_args()


def copy_tree(source, dest):
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def copy_docs(source, dest):
    dest.mkdir(parents=True, exist_ok=True)
    for name in COPIED_DIRS:
        copy_tree(source / name, dest / name)


def subject_hierarchy(dest):
    subjects = dest / "subjects"
    lines = []
    for root in sorted(p for p in subjects.iterdir() if p.is_dir()):
        mids = sorted(p for p in root.iterdir() if p.is_dir())
        if not mids:
            continue
        lines.append(f"{root.name}:")
        lines.extend(f"  {mid.name}" for mid in mids)
        lines.append("")
    (dest / "subject_hierarchy.md").write_text("\n".join(lines).rstrip() + "\n")


def first_match(pattern, text):
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def fact_entry(path, dest):
    text = path.read_text()
    rel = path.relative_to(SKILL_ROOT).as_posix()
    subject = path.relative_to(dest / "fact").parent.as_posix()
    columns = []
    columns_match = re.search(r"^columns:\n((?:- .+\n)+)", text, re.MULTILINE)
    if columns_match:
        for line in columns_match.group(1).splitlines():
            columns.append(line[2:].split(":", 1)[0].strip())

    return {
        "kind": "fact",
        "id": path.stem,
        "path": rel,
        "subject": subject,
        "description": first_match(r"^description: (.+)$", text),
        "measure": first_match(r"^measure: (.+)$", text),
        "columns": columns,
    }


def dim_entry(path):
    text = path.read_text()
    rel = path.relative_to(SKILL_ROOT).as_posix()
    return {
        "kind": "dim",
        "id": path.stem,
        "path": rel,
        "title": first_match(r"^# (.+)$", text),
    }


def subject_entry(path, dest):
    text = path.read_text()
    rel = path.relative_to(SKILL_ROOT).as_posix()
    table_ids = re.findall(r"^id: ([a-z0-9_]+)$", text, re.MULTILINE)
    return {
        "kind": "subject",
        "id": path.stem,
        "path": rel,
        "subject": path.relative_to(dest / "subjects").with_suffix("").as_posix(),
        "tables": table_ids,
    }


def table_index(dest):
    entries = []
    entries.extend(
        subject_entry(path, dest)
        for path in sorted((dest / "subjects").rglob("*.md"))
    )
    entries.extend(fact_entry(path, dest) for path in sorted((dest / "fact").rglob("*.md")))
    entries.extend(dim_entry(path) for path in sorted((dest / "dim").glob("*.md")))

    lines = [json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in entries]
    (dest / "table_index.jsonl").write_text("\n".join(lines) + "\n")


def geo_index(dest):
    lines = ["# Geo Files", ""]
    for path in sorted((dest / "geo").glob("*.parquet")):
        lines.append(f"- `{path.name}`")
    (dest / "geo_index.md").write_text("\n".join(lines) + "\n")


def main():
    args = parse_args()
    source = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    copy_docs(source, dest)
    subject_hierarchy(dest)
    table_index(dest)
    geo_index(dest)
    print(f"Synced {source} -> {dest}")


if __name__ == "__main__":
    main()
