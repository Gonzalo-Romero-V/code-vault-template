# Changelog

Todas las notas de cambio relevantes de `code-vault-template`.

El formato sigue [Keep a Changelog](https://keepachangelog.com/) y este proyecto
se versiona con [SemVer](https://semver.org/).

---

## [1.0.0] — Inicial

### Added
- Bootstrapper Python (`bootstrap/init_vault.py`) que instala el sistema completo
  en un proyecto desde cero: vault Obsidian, engine determinista, git hook,
  skills de Claude Code, config y `AGENTS.md` adaptado al stack.
- Plugin system de extractores (`scripts/lib/extractors/`) con interfaz universal
  `ExtractorBase` y registry dinámico.
- Extractores preinstalados:
  - `nextjs-laravel` — el extractor probado en FarMedic, sin cambios funcionales.
  - `python-generic` — heurísticas para Python (FastAPI / Django / Flask).
  - `graphify` — adaptador para [Graphify](https://graphify.net/) que reemplaza
    el parsing AST por la lectura de `graphify-out/graph.json`.
  - `generic` — fallback con detección de stack + scaffolding: si encuentra una
    pila sin archetype (Angular, Java, Go, Rust, etc.), genera propuestas en
    `_proposed_*` para que el humano las promueva al catálogo.
- Stacks archetype en `bootstrap/stacks/`: `nextjs-laravel`, `nextjs-only`,
  `python-fastapi`, `generic`.
- Templates tipados de notas (`bootstrap/vault-skeleton/`) con frontmatter
  tipificado por capa (intent H1, domain H2, decisions H3).
- Skills `/snapshot`, `/sync`, `/ingest`, `/check` adaptados a stack-agnóstico
  y con awareness opcional de Graphify.
- `AGENTS.md` y `vault_sync.config.json` con placeholders documentados.

### Preservado intacto desde FarMedic
- `scripts/vault_sync.py` — engine determinista, 6 subcomandos, 0 dependencias.
- `scripts/lib/schema.py` — schema de validación `change_report.json`.
- `scripts/lib/git_ops.py` — wrapper de `git diff` cross-commit.
- `scripts/lib/hierarchy.py` — `detect_layer` y `is_excluded`.
- `scripts/lib/vault.py` — frontmatter parser y locked guard.
- `scripts/lib/consistency.py` — chequeos `env_references` y `vault_code_paths`.
- Hook `post-commit` non-blocking que loguea a `.vault-sync/post-commit.log`.
