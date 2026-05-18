"""Map a file path to its hierarchy layer (H1..H5 or ENV).

Preservado desde FarMedic. Universal — la jerarquía H1..H5 es del Code Vault,
no del stack. Solo cambian los patterns dentro del hierarchy_mapping según
el archetype elegido.
"""
from __future__ import annotations
import fnmatch


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _match_any(path: str, patterns: list[str]) -> bool:
    norm = _normalize(path)
    for pat in patterns:
        pat_norm = _normalize(pat)
        if fnmatch.fnmatch(norm, pat_norm):
            return True
        # Soporte simple de ** (recursivo).
        if "**" in pat_norm:
            simple = pat_norm.replace("**/", "").replace("/**", "")
            if simple in norm:
                return True
    return False


def detect_layer(path: str, hierarchy_mapping: dict) -> str:
    """Return layer key (e.g. 'H4_contracts') or 'UNCLASSIFIED'."""
    for layer, patterns in hierarchy_mapping.items():
        if _match_any(path, patterns):
            return layer
    return "UNCLASSIFIED"


def is_excluded(path: str, exclude_patterns: list[str]) -> bool:
    return _match_any(path, exclude_patterns)
