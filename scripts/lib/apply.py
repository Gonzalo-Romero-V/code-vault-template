"""Operaciones sobre el vault — create / update_frontmatter / append_section / deprecate.

Extraído de FarMedic vault_sync.py::cmd_apply, refactorizado como función pura
para que el dispatch CLI quede en vault_sync.py y la lógica sea unit-testable.

Reglas preservadas (no cambian de comportamiento):
    - Idempotente: aplicar el mismo changes.json dos veces no duplica.
    - Locked guard: notas con `status` en `protected_status` rechazan toda op.
    - Append-only sobre body: nunca se sobrescribe la body completa.
    - Falla loud por op, no por payload: errores se cuentan y loguean,
      pero el resto del payload se sigue procesando.
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Callable

from .vault import parse_frontmatter, is_protected


def _render(fm: dict, body: str) -> str:
    """Reconstruye una nota como `---\\nkey: value\\n---\\n\\nbody`. Preserva FarMedic exact."""
    fm_text = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n\n"
    return fm_text + body.lstrip("\n")


def apply_changes(payload: dict,
                  vault_path: Path,
                  protected_status: list[str],
                  log: Callable[[str], None]) -> dict:
    """Aplica un changes.json y devuelve contadores.

    Args:
        payload:           dict con `{operations: [...]}`
        vault_path:        Path raíz del vault Obsidian
        protected_status:  lista de status que bloquean modificaciones (típ. ["locked"])
        log:               función `print`-like para mensajes (permite redirigir)

    Returns:
        {"applied": int, "skipped": int, "failed": int, "locked_blocked": int}
    """
    ops = payload.get("operations", [])
    counters = {"applied": 0, "skipped": 0, "failed": 0, "locked_blocked": 0}

    if not ops:
        log("OK: no operations to apply")
        return counters

    for op in ops:
        action = op.get("action")
        note_rel = op.get("note") or op.get("path")
        if not note_rel:
            counters["failed"] += 1
            log(f"FAIL: op missing 'note' or 'path': {op}")
            continue
        note_path = vault_path / note_rel
        note_path.parent.mkdir(parents=True, exist_ok=True)

        # Locked guard — se evalúa contra la nota existente, si la hay.
        if note_path.exists():
            try:
                fm, body = parse_frontmatter(note_path.read_text(encoding="utf-8"))
            except Exception:
                fm, body = {}, ""
            if is_protected({"frontmatter": fm}, protected_status):
                counters["locked_blocked"] += 1
                log(f"BLOCKED (locked): {note_rel}")
                continue
        else:
            fm, body = {}, ""

        try:
            if action == "create":
                if note_path.exists():
                    counters["skipped"] += 1
                    log(f"SKIP (exists): {note_rel}")
                    continue
                note_path.write_text(op["content"], encoding="utf-8")
                counters["applied"] += 1
                log(f"CREATED: {note_rel}")

            elif action == "update_frontmatter":
                set_map = op.get("set", {})
                # Idempotencia: si ya tiene los valores, skip.
                if all(fm.get(k) == str(v) for k, v in set_map.items()):
                    counters["skipped"] += 1
                    log(f"SKIP (idempotent): {note_rel}")
                    continue
                for k, v in set_map.items():
                    fm[k] = str(v)
                note_path.write_text(_render(fm, body), encoding="utf-8")
                counters["applied"] += 1
                log(f"UPDATED frontmatter: {note_rel} {set_map}")

            elif action == "append_section":
                section = op.get("section", "Notes")
                content = op.get("content", "")
                marker = f"## {section}"
                if marker in body and content.strip() in body:
                    counters["skipped"] += 1
                    log(f"SKIP (idempotent): {note_rel} section={section}")
                    continue
                if marker not in body:
                    body = body.rstrip() + f"\n\n{marker}\n{content}\n"
                else:
                    body = body.rstrip() + f"\n\n{content}\n"
                note_path.write_text(_render(fm, body), encoding="utf-8")
                counters["applied"] += 1
                log(f"APPENDED to {section}: {note_rel}")

            elif action == "deprecate":
                if fm.get("status") == "deprecated":
                    counters["skipped"] += 1
                    log(f"SKIP (already deprecated): {note_rel}")
                    continue
                fm["status"] = "deprecated"
                fm["deprecated_at"] = datetime.date.today().isoformat()
                note_path.write_text(_render(fm, body), encoding="utf-8")
                counters["applied"] += 1
                log(f"DEPRECATED: {note_rel}")

            else:
                counters["failed"] += 1
                log(f"FAIL: unknown action: {action}")

        except Exception as e:
            counters["failed"] += 1
            log(f"FAIL: {note_rel}: {e}")

    log(
        f"DONE: applied={counters['applied']} "
        f"skipped={counters['skipped']} "
        f"failed={counters['failed']} "
        f"blocked_locked={counters['locked_blocked']}"
    )
    return counters
