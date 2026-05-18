"""Read vault notes and parse their frontmatter — read-mostly, append-only writes.

Preservado desde FarMedic. Bug fix incidental: la heurística
`path.parent.name != "FarMedic"` en `read_note` se reemplazó por
`vault_root` explícito (parámetro opcional), eliminando el acoplamiento al
nombre del proyecto FarMedic.
"""
from __future__ import annotations
from pathlib import Path
import re

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body). Frontmatter is parsed as simple key: value."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, body


def list_notes(vault_path: Path) -> list[Path]:
    """Lista todas las notas del vault, excluyendo templates (`_template*.md`)."""
    return [
        p for p in vault_path.rglob("*.md")
        if "/_template" not in p.as_posix()
    ]


def read_note(path: Path, vault_root: Path | None = None) -> dict:
    """Lee una nota y la devuelve como dict.

    `vault_root` se usa para calcular el path relativo a la raíz del vault.
    Si no se provee, se intenta inferir desde el árbol del archivo.
    """
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if vault_root is not None:
        try:
            relative = path.relative_to(vault_root).as_posix()
        except ValueError:
            relative = path.as_posix()
    else:
        # Fallback determinista: usar el path absoluto. No adivinar.
        relative = path.as_posix()
    return {
        "path": str(path),
        "relative": relative,
        "frontmatter": fm,
        "body": body,
        "raw": text,
    }


def is_protected(note: dict, protected_status: list[str]) -> bool:
    return note["frontmatter"].get("status", "").lower() in [s.lower() for s in protected_status]


def find_notes_by_code_path(vault_path: Path, code_path_substring: str) -> list[Path]:
    """Return vault notes whose `code_path:` references the given substring."""
    results = []
    for p in list_notes(vault_path):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        fm, _ = parse_frontmatter(text)
        cp = fm.get("code_path", "")
        if cp and code_path_substring in cp:
            results.append(p)
    return results
