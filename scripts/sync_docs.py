from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PLUGIN_ROOT.parent / "agent_data"
DEST = PLUGIN_ROOT / "docs"
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
    (subjects / "index.md").write_text("\n".join(lines).rstrip() + "\n")


def geo_index(dest):
    lines = ["# Geo Files", ""]
    for path in sorted((dest / "geo").glob("*.parquet")):
        lines.append(f"- `{path.name}`")
    (dest / "geo" / "index.md").write_text("\n".join(lines) + "\n")


def main():
    args = parse_args()
    source = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    copy_docs(source, dest)
    subject_hierarchy(dest)
    geo_index(dest)
    print(f"Synced {source} -> {dest}")


if __name__ == "__main__":
    main()
