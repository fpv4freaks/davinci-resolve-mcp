#!/usr/bin/env python3
"""Build the AiBS offline RAPID registry from the canonical RAPID methodology.

The generated file is a cache with provenance, not an independent taxonomy. Its
task slugs, phases, streams, groups, owners, and sequencing come from the RAPID
repository at one recorded commit.

Examples:
    python scripts/sync_rapid_registry.py
    python scripts/sync_rapid_registry.py --check
    python scripts/sync_rapid_registry.py --source C:\\src\\RAPID

Normal synchronization refreshes from ``main``. ``--check`` instead rebuilds
from the exact commit recorded in the existing cache unless ``--ref`` is
provided explicitly, so CI verifies reproducibility without following a
floating branch.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Run: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)


DEFAULT_REPOSITORY = "mcaps-microsoft/RAPID"
DEFAULT_REF = "main"
REGISTRY_SCHEMA_VERSION = 1
TASK_GROUP_ORDER = ["context", "outcomes", "eval", "refinement"]


def _run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def _repo_url(repository: str) -> str:
    if "://" in repository or repository.endswith(".git"):
        return repository
    return f"https://github.com/{repository}.git"


def _clone(repository: str, ref: str) -> Path:
    checkout = Path(tempfile.mkdtemp(prefix="aibs_rapid_registry_"))
    try:
        _run(["git", "init", "--quiet", str(checkout)])
        _run(["git", "remote", "add", "origin", _repo_url(repository)], cwd=checkout)
        _run(["git", "sparse-checkout", "init", "--cone"], cwd=checkout)
        _run(["git", "sparse-checkout", "set", "methodology"], cwd=checkout)
        _run(["git", "fetch", "--depth", "1", "origin", ref], cwd=checkout)
        _run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], cwd=checkout)
        return checkout
    except Exception:
        shutil.rmtree(checkout, ignore_errors=True)
        raise


def _git_value(repo: Path, *args: str) -> str:
    return _run(["git", *args], cwd=repo)


def _frontmatter(text: str, path: Path) -> dict[str, Any]:
    match = re.match(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not match:
        return {}
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML frontmatter must be a mapping")
    return data


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _owner(text: str) -> str:
    match = re.search(r"^\*\*Owner role:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _purpose(text: str) -> str:
    section = _section(text, "Purpose")
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", section) if part.strip()]
    if not paragraphs:
        return ""
    return re.sub(r"\s+", " ", paragraphs[0])


def _clean_cell(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "; ", value, flags=re.IGNORECASE)
    value = re.sub(r"[`*_]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _section_items(text: str, heading: str) -> list[str]:
    section = _section(text, heading)
    items: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [_clean_cell(cell) for cell in stripped.strip("|").split("|")]
            first = cells[0] if cells else ""
            if (
                first
                and first.lower() not in {"name", "input", "output", "outcome", "artefact"}
                and not re.fullmatch(r"[-: ]+", first)
            ):
                items.append(first)
        elif stripped.startswith("- "):
            first = re.split(r"\s+[—-]\s+", stripped[2:], maxsplit=1)[0]
            first = _clean_cell(first)
            if first:
                items.append(first)
    return list(dict.fromkeys(items))


def _execution_skills(text: str) -> list[str]:
    section = _section(text, "Execution")
    return sorted(set(re.findall(r"`(rapid-[a-z0-9-]+)`", section)))


def _phase_folders(methodology: Path) -> list[Path]:
    return sorted(
        path
        for path in methodology.iterdir()
        if path.is_dir() and re.match(r"^\d\d-", path.name)
    )


def _stream_catalog(phase_folders: list[Path]) -> list[dict[str, Any]]:
    streams: dict[str, dict[str, Any]] = {}
    for phase in phase_folders:
        for folder in phase.iterdir():
            match = re.match(r"^(\d\d)-(.+)$", folder.name)
            if not folder.is_dir() or not match:
                continue
            name = match.group(2).replace("-", " ")
            code = _slugify(name)
            candidate = {
                "code": code,
                "name": name.title().replace(" And ", " and "),
                "order": int(match.group(1)),
            }
            streams.setdefault(code, candidate)
    return sorted(streams.values(), key=lambda item: (item["order"], item["code"]))


def _parse_tasks(methodology: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seen_slugs: dict[str, str] = {}
    for phase_folder in _phase_folders(methodology):
        phase_code = phase_folder.name.lower()
        for path in sorted(phase_folder.rglob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            metadata = _frontmatter(text, path)
            task_name = str(metadata.get("task") or "").strip()
            if not task_name:
                continue
            slug = path.stem
            relative_path = path.relative_to(methodology.parent).as_posix()
            if slug in seen_slugs:
                raise ValueError(
                    f"Duplicate RAPID task slug '{slug}': {seen_slugs[slug]} and {relative_path}"
                )
            seen_slugs[slug] = relative_path
            phase_name = str(metadata.get("phase") or "").strip()
            stream_name = str(metadata.get("stream") or "").strip().strip("—-").strip()
            group = str(metadata.get("task_group") or "").strip()
            if not phase_name or not group:
                raise ValueError(f"{relative_path}: task frontmatter requires phase and task_group")
            archetypes = metadata.get("archetypes") or []
            if isinstance(archetypes, str):
                archetypes = [archetypes]
            task = {
                "slug": slug,
                "name": task_name,
                "path": relative_path,
                "phase": {"code": phase_code, "name": phase_name},
                "stream": (
                    {"code": _slugify(stream_name), "name": stream_name}
                    if stream_name
                    else None
                ),
                "group": group,
                "output_type": str(metadata.get("output_type") or "").strip(),
                "owner": _owner(text),
                "purpose": _purpose(text),
                "archetypes": [str(value) for value in archetypes],
                "inputs": _section_items(text, "Input"),
                "outputs": _section_items(text, "Output"),
                "execution_skills": _execution_skills(text),
                "predecessor": None,
            }
            tasks.append(task)
    return sorted(tasks, key=lambda item: item["path"])


def _index_rows(index_text: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    phase = ""
    stream = ""
    for line in index_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if (
            len(cells) != 4
            or cells[0] == "Phase"
            or (cells[0] and set(cells[0]) <= {"-", ":"})
        ):
            continue
        if cells[0]:
            phase = cells[0]
        if cells[1]:
            stream = cells[1]
        task_link = re.search(r"\[([^\]]+)\]\(([^)]+\.md)\)", cells[2])
        if not task_link:
            continue
        rows.append((phase, stream, Path(task_link.group(2)).stem, _clean_cell(cells[3])))
    return rows


def _apply_predecessors(methodology: Path, tasks: list[dict[str, Any]]) -> None:
    index_path = methodology / "references" / "tasks-index.md"
    rows = _index_rows(index_path.read_text(encoding="utf-8"))
    indexed_slugs = {row[2] for row in rows}
    task_slugs = {task["slug"] for task in tasks}
    if indexed_slugs != task_slugs:
        missing = sorted(task_slugs - indexed_slugs)
        unknown = sorted(indexed_slugs - task_slugs)
        raise ValueError(
            "RAPID task index disagrees with task files. "
            f"Missing from index: {missing or 'none'}; unknown in index: {unknown or 'none'}"
        )

    by_lane_and_name: dict[tuple[str, str, str], str] = {}
    for task in tasks:
        stream_name = task["stream"]["name"] if task["stream"] else "—"
        by_lane_and_name[(task["phase"]["name"], stream_name, task["name"])] = task["slug"]
    by_slug = {task["slug"]: task for task in tasks}
    for phase, stream, slug, predecessor_name in rows:
        if not predecessor_name or predecessor_name == "—":
            continue
        key = (phase, stream or "—", predecessor_name)
        predecessor_slug = by_lane_and_name.get(key)
        if not predecessor_slug:
            raise ValueError(
                f"tasks-index.md: cannot resolve predecessor '{predecessor_name}' "
                f"for {phase} / {stream or '—'} / {slug}"
            )
        by_slug[slug]["predecessor"] = predecessor_slug


def build_registry(repo_root: Path, repository: str, ref: str) -> dict[str, Any]:
    methodology = repo_root / "methodology"
    if not methodology.is_dir():
        raise ValueError(f"RAPID methodology folder not found: {methodology}")
    tasks = _parse_tasks(methodology)
    _apply_predecessors(methodology, tasks)
    phase_folders = _phase_folders(methodology)
    phase_names = {
        task["phase"]["code"]: task["phase"]["name"]
        for task in tasks
        if task.get("phase")
    }
    phases = [
        {
            "code": folder.name.lower(),
            "name": phase_names.get(
                folder.name.lower(),
                folder.name.split("-", 1)[1].replace("-", " ").title(),
            ),
            "order": int(folder.name.split("-", 1)[0]),
        }
        for folder in phase_folders
    ]
    groups = sorted(
        {task["group"] for task in tasks},
        key=lambda value: (
            TASK_GROUP_ORDER.index(value) if value in TASK_GROUP_ORDER else len(TASK_GROUP_ORDER),
            value,
        ),
    )
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "source": {
            "repository": repository,
            "ref": ref,
            "commit": _git_value(repo_root, "rev-parse", "HEAD"),
            "commit_date": _git_value(repo_root, "show", "-s", "--format=%cI", "HEAD"),
            "methodology_path": "methodology",
        },
        "phases": phases,
        "streams": _stream_catalog(phase_folders),
        "task_groups": groups,
        "task_count": len(tasks),
        "tasks": tasks,
    }


def _serialized(registry: dict[str, Any]) -> str:
    return json.dumps(registry, indent=2, ensure_ascii=False) + "\n"


def _resolve_refs(output: Path, requested_ref: str | None, check: bool) -> tuple[str, str]:
    """Return ``(checkout_ref, recorded_ref)`` for refresh or reproducible check."""
    if requested_ref:
        return requested_ref, requested_ref
    if not check:
        return DEFAULT_REF, DEFAULT_REF
    try:
        cached = json.loads(output.read_text(encoding="utf-8"))
        source = cached["source"]
        commit = source["commit"]
        recorded_ref = source.get("ref") or commit
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(
            f"Cannot resolve pinned RAPID commit from {output}: {exc}"
        ) from exc
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError(f"Invalid pinned RAPID commit in {output}: {commit!r}")
    if not isinstance(recorded_ref, str) or not recorded_ref:
        raise ValueError(f"Invalid RAPID source ref in {output}: {recorded_ref!r}")
    return commit, recorded_ref


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_output = script_dir.parent / "references" / "rapid-registry.generated.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument(
        "--ref",
        help="RAPID branch, tag, or commit (default: main for refresh; cached commit for --check)",
    )
    parser.add_argument("--source", type=Path, help="Existing RAPID repository checkout")
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--check", action="store_true", help="Fail if the cached registry is stale")
    args = parser.parse_args()

    temporary_checkout: Path | None = None
    try:
        checkout_ref, recorded_ref = _resolve_refs(args.output, args.ref, args.check)
        repo_root = args.source.resolve() if args.source else _clone(args.repo, checkout_ref)
        if not args.source:
            temporary_checkout = repo_root
        registry = build_registry(repo_root, args.repo, recorded_ref)
        content = _serialized(registry)
        if args.check:
            if not args.output.is_file() or args.output.read_text(encoding="utf-8") != content:
                print(
                    f"ERROR: {args.output} is stale for RAPID {registry['source']['commit']}",
                    file=sys.stderr,
                )
                return 1
            print(
                f"OK: RAPID registry is current ({registry['task_count']} tasks, "
                f"commit {registry['source']['commit'][:7]})."
            )
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8", newline="\n")
        print(
            f"Wrote {args.output}: {registry['task_count']} tasks from "
            f"{args.repo}@{registry['source']['commit'][:7]}"
        )
        return 0
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary_checkout:
            shutil.rmtree(temporary_checkout, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())