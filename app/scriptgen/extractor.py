"""Extract project facts from a local folder: README, tech stack, file tree, routes."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    "node_modules", ".git", ".venv", "venv", "dist", "build", "target",
    "__pycache__", ".next", ".idea", ".vscode", "vendor", "bin", "obj",
}

STACK_FILES = {
    "go.mod": "Go",
    "cargo.toml": "Rust",
    "pubspec.yaml": "Flutter",
    "composer.json": "PHP",
    "pom.xml": "Java",
    "build.gradle": "Java",
}

ROUTE_PATTERNS = [
    re.compile(r"""\.(?:GET|POST|PUT|DELETE|PATCH)\(\s*["'`](/[^"'`]*)["'`]"""),   # gin/echo/chi
    re.compile(r"""@(?:app|router|bp|api)\.(?:get|post|put|delete|patch)\(\s*["'](/[^"']*)["']"""),  # flask
    re.compile(r"""\b(?:app|router)\.(?:get|post|put|delete|patch)\(\s*["'`](/[^"'`]*)["'`]"""),    # express/koa
    re.compile(r"""(?:path|to)=\{?["'`](/[^"'`]*)["'`]"""),                       # react-router
]


def _read_text(path: Path, limit: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _parse_readme(text: str) -> dict[str, Any]:
    """Naive markdown section parser: title, tagline, sections by heading."""
    lines = text.splitlines()
    title = ""
    tagline = ""
    sections: dict[str, list[str]] = {}
    current = ""
    for line in lines:
        h1 = re.match(r"^#\s+(.+)", line)
        h2 = re.match(r"^##+\s+(.+)", line)
        if h1 and not title:
            title = h1.group(1).strip()
            continue
        if h2:
            current = h2.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        stripped = line.strip()
        # Tagline = first meaningful line between the H1 and the first section.
        if title and not current and not tagline and stripped and not stripped.startswith(("#", "!", "[", "```")):
            tagline = stripped
        if current:
            sections.setdefault(current, []).append(line)
    features: list[str] = []
    for key, body in sections.items():
        if "feature" in key or "what it does" in key:
            for line in body:
                bullet = re.match(r"^\s*[-*+]\s+(.+)", line)
                if bullet:
                    clean = re.sub(r"\*\*|`", "", bullet.group(1)).strip()
                    if clean:
                        features.append(clean)
    problem_lines: list[str] = []
    for key, body in sections.items():
        if "problem" in key or "about" in key or "challenge" in key or "background" in key:
            for line in body:
                bullet = re.match(r"^\s*[-*+]\s+(.+)", line)
                if bullet:
                    clean = re.sub(r"\*\*|`", "", bullet.group(1)).strip()
                    if clean:
                        problem_lines.append(clean)
                elif line.strip() and not problem_lines:
                    clean = re.sub(r"\*\*|`", "", line).strip()
                    if clean:
                        problem_lines.append(clean)
    return {
        "title": title,
        "tagline": tagline,
        "features": features[:6],
        "problem": problem_lines[:3],
    }


def _detect_stack(root: Path, tree_files: list[Path]) -> list[str]:
    stack: list[str] = []
    names = {f.name.lower(): f for f in tree_files if f.is_file()}
    for fname, label in STACK_FILES.items():
        if fname in names:
            stack.append(label)
    pkg = names.get("package.json")
    if pkg:
        stack.append("Node.js")
        try:
            deps = json.loads(pkg.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            deps = {}
        for section in ("dependencies", "devDependencies"):
            for dep in (deps.get(section) or {}):
                low = dep.lower()
                if low.startswith("react") and "React" not in stack:
                    stack.append("React")
                elif low.startswith("vue") and "Vue" not in stack:
                    stack.append("Vue")
                elif low.startswith("next") and "Next.js" not in stack:
                    stack.append("Next.js")
                elif low == "svelte" and "Svelte" not in stack:
                    stack.append("Svelte")
                elif low == "express" and "Express" not in stack:
                    stack.append("Express")
                elif low == "tailwindcss" and "Tailwind CSS" not in stack:
                    stack.append("Tailwind CSS")
                elif low == "playwright" and "Playwright" not in stack:
                    stack.append("Playwright")
    for fname in ("requirements.txt", "pyproject.toml", "Pipfile"):
        if fname in names:
            stack.append("Python")
            text = _read_text(names[fname]).lower()
            for lib, label in (("fastapi", "FastAPI"), ("flask", "Flask"), ("django", "Django")):
                if lib in text and label not in stack:
                    stack.append(label)
            break
    if (root / "Dockerfile").exists():
        stack.append("Docker")
    return stack


def _walk_tree(root: Path, max_entries: int = 200) -> list[Path]:
    entries: list[Path] = []
    for dirpath, dirnames, filenames in root.walk():
        rel = Path(dirpath).relative_to(root)
        depth = 0 if rel == Path(".") else len(rel.parts)
        if depth >= 2:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        entries.append(Path(dirpath))
        entries.extend(Path(dirpath) / f for f in filenames if f not in SKIP_DIRS)
        if len(entries) >= max_entries:
            break
    return entries


def _detect_routes(tree_files: list[Path]) -> list[str]:
    routes: list[str] = []
    code_exts = {".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".kt", ".rb"}
    for path in tree_files:
        if path.suffix.lower() not in code_exts or path.name.lower() in {
            "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        }:
            continue
        text = _read_text(path, limit=120000)
        for pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(text):
                route = match.group(1)
                if route not in routes and not route.startswith("/api/0"):
                    routes.append(route)
        if len(routes) >= 12:
            break
    return routes[:12]


def extract_project(project_folder: str) -> dict[str, Any]:
    root = Path(project_folder)
    if not root.is_dir():
        raise ValueError(f"Folder project tidak ditemukan: {project_folder}")
    tree_files = _walk_tree(root)
    readme = next(
        (f for f in tree_files if f.is_file() and f.name.lower() in {"readme.md", "readme"}),
        None,
    )
    readme_info = _parse_readme(_read_text(readme)) if readme else {}
    return {
        "name": readme_info.get("title") or root.name,
        "tagline": readme_info.get("tagline", ""),
        "features": readme_info.get("features", []),
        "problem": readme_info.get("problem", []),
        "stack": _detect_stack(root, tree_files),
        "routes": _detect_routes(tree_files),
        "tree": [
            str(p.relative_to(root)) for p in tree_files[:60] if p != root
        ],
    }
