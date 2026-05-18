# code-vault-template

> Plantilla Git-cloneable que estandariza el workflow **Code Vault**: un vault
> Obsidian como fuente de verdad semántica, un engine determinista que mantiene
> el grafo sincronizado con el código, y 4 skills de Claude Code que operan
> sobre ese contrato. Cero LLM en el engine, plugin system de extractores,
> bootstrap one-shot.

---

## Qué es

**Code Vault** es un sistema que mantiene dos fuentes de verdad sincronizadas:

- **El código** (H4–H5: contratos e implementación) — la verdad técnica.
- **El vault Obsidian** (H1–H3: intent, dominio, decisiones) — la verdad semántica.

Las capas superiores **causan** las inferiores. Cuando el código cambia, un
git hook dispara el engine, que produce un `change_report.json` determinista
y un `facts.json` semántico. Las skills de Claude Code leen esos artefactos
y proponen cambios al vault — el humano aprueba, el engine aplica.

Este repo es la **abstracción del sistema** que nació en FarMedic, despojada
del dominio farmacéutico, lista para instanciar en cualquier proyecto nuevo.

---

## Cuándo usarlo / cuándo no

**Usalo si**:

- Trabajás con agentes de IA (Claude Code, Codex, Cursor) y querés que tengan
  contexto consistente entre sesiones sin re-explicarles el proyecto.
- Tu proyecto tiene reglas de negocio que no caben en el código (invariantes,
  estados, RBAC, decisiones arquitectónicas con trade-offs).
- Te molesta que la IA invente enums, duplique endpoints o ignore decisiones
  documentadas porque no las leyó antes de codear.

**No lo uses si**:

- El proyecto es un script de una sola sesión, un prototipo descartable, o
  un POC de menos de un día.
- El dominio es trivial y todo cabe en el README.
- No tenés tolerancia a mantener notas Markdown como segundo cerebro
  (el sistema asume que vas a abrir el vault y editarlo a mano cuando aplique).

---

## Inicio rápido

```bash
git clone https://github.com/Gonzalo-Romero-V/code-vault-template.git mi-proyecto
cd mi-proyecto
rm -rf .git && git init   # opcional pero recomendado — empezás desde un repo limpio
python bootstrap/init_vault.py \
  --stack nextjs-laravel \
  --project-name "MiProyecto" \
  --vault-path "$HOME/vaults/mi-proyecto"
```

Esto deja listo: vault inicializado, scripts del engine instalados, git hook
activo, `AGENTS.md` generado, `vault_sync.config.json` con paths reales.

Después: `git add . && git commit -m "chore: init code-vault"` y el hook
genera el primer reporte automáticamente.

> **Sobre el `rm -rf .git && git init`**: el clone trae los commits del
> template. Sin reiniciar la historia, el primer commit de tu proyecto solo
> reportará los archivos que el bootstrap *modificó* (típicamente 2: `AGENTS.md`
> y `vault_sync.config.json`), porque el resto ya existía en commits del
> template. Reiniciar la historia produce un primer reporte completo y honesto.

---

## Opciones del bootstrapper

```
python bootstrap/init_vault.py [opciones]
```

| Flag | Obligatorio | Descripción |
|---|---|---|
| `--stack <id>` | sí | Archetype a usar. Opciones builtin: `nextjs-laravel`, `nextjs-only`, `python-fastapi`, `generic` |
| `--project-name <name>` | sí | Nombre humano. Sustituye `__PROJECT_NAME__` en config y AGENTS.md |
| `--vault-path <path>` | sí | Ruta **absoluta** al vault Obsidian. NO debe existir (el bootstrapper rechaza sobreescribir) |
| `--with-graphify` | no | Setea `extractor: "graphify"` en el config (override del archetype) |
| `--dry-run` | no | Imprime las operaciones planeadas sin escribir nada. Idempotente |

Validaciones previas (todas acumulativas, exit 2):

- El stack debe existir en `bootstrap/stacks/`.
- `--vault-path` debe ser absoluto y no existir.
- El cwd debe ser un repo git (corré `git init` antes).
- Mensajes accionables: cada error dice qué hacer para resolverlo.

---

## Con Graphify

[Graphify](https://graphify.net/) es un knowledge graph local (tree-sitter,
deterministic, sin LLM). Si lo tenés instalado, podés sustituir el extractor
nativo por el adapter de Graphify y obtener:

- **Call graph** — qué función llama a cuál (campo exclusivo, ningún otro extractor lo provee).
- **25 lenguajes soportados** vía tree-sitter (vs los stacks específicos del catálogo).
- **Confianza por edge** (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`).

Activarlo:

```bash
pip install graphifyy
graphify extract . --no-cluster      # Pass 1: AST tree-sitter, sin LLM, sin red
# Bootstrap con --with-graphify, o editar vault_sync.config.json:
#   "extractor": "graphify"
```

El adapter falla loud si `graphify-out/graph.json` no existe; el mensaje de
error incluye el comando exacto a correr.

**Cuándo activarlo**: cuando tu stack no encaja en los archetypes builtin
(ej. Java, Go, Rust mezclados) y querés extracción real en vez del fallback
`generic`. O cuando el `call_graph` te aporta más que el `import_graph` (en
proyectos donde el shape de las llamadas cross-módulo importa más que las
dependencias entre archivos).

---

## Ciclo de trabajo diario

```
1. Codeás un cambio
2. Pedís al humano permiso para commit + proponés mensaje
3. git commit
   └─ post-commit hook regenera .vault-sync/change_report.json + facts.json
4. /sync skill → Claude lee los artefactos, propone cambios al vault
5. Humano aprueba → script aplica (idempotente, append-only, locked-aware)
6. (Opcional) /check si tocaste algo crítico — reporta drift, no resuelve
```

Notas:
- Si el commit es solo refactor H5, `/sync` puede proponer 0 cambios. Es válido.
- `/snapshot` solo en arranques o refactors masivos — es caro en tokens.
- `/ingest <ruta>` cuando agregás un PDF/transcript a `vault/raw/`.

---

## Estructura del template

```
code-vault-template/
├── README.md                            ← este archivo
├── CHANGELOG.md                         ← v1.0.0
│
├── bootstrap/
│   ├── init_vault.py                    ← bootstrapper Python stdlib
│   ├── stacks/
│   │   ├── nextjs-laravel.json          ← archetype probado (FarMedic)
│   │   ├── nextjs-only.json             ← variante Next.js standalone
│   │   ├── python-fastapi.json          ← Python (FastAPI / SQLAlchemy / Alembic)
│   │   └── generic.json                 ← fallback stack-agnóstico
│   └── vault-skeleton/                  ← templates de notas que se copian al vault
│       ├── SYSTEM.md                    ← locked, contrato del sistema
│       ├── INDEX.md                     ← locked, mapa del vault
│       ├── _template.md                 ← template base de nota
│       ├── intent/vision.md.tpl         ← H1 — visión + invariantes
│       ├── domain/entity.md.tpl         ← H2 — entidad de dominio
│       └── decisions/
│           ├── stack.md.tpl             ← H3 — decisiones de stack
│           └── architecture.md.tpl     ← H3 — decisiones arquitectónicas
│
├── scripts/
│   ├── vault_sync.py                    ← engine (6 subcomandos: report/facts/validate/check/apply/status)
│   └── lib/
│       ├── schema.py                    ← contrato change_report.json
│       ├── config.py                    ← loader vault_sync.config.json
│       ├── git_ops.py                   ← wrapper git diff
│       ├── hierarchy.py                 ← detect_layer / is_excluded
│       ├── vault.py                     ← frontmatter parser + locked guard
│       ├── consistency.py               ← env_references + vault_code_paths checks
│       ├── apply.py                     ← idempotent ops sobre el vault
│       ├── report.py                    ← build_report (función pura)
│       ├── status.py                    ← constantes de status
│       └── extractors/
│           ├── base.py                  ← interfaz ExtractorBase
│           ├── nextjs_laravel.py        ← preservado bit-equivalente
│           ├── python_generic.py        ← FastAPI / SQLAlchemy / Alembic / Django / Flask
│           ├── graphify_adapter.py      ← lee graphify-out/graph.json
│           └── generic.py               ← inspector + scaffolder acumulativo
│
├── .claude/commands/                    ← skills (Claude Code: slash commands)
│   ├── snapshot.md
│   ├── sync.md
│   ├── ingest.md
│   └── check.md
│
├── prompts/
│   └── SKILLS.md                        ← skills agnósticas (Codex / Cursor / Cline / Continue)
│
├── hooks/
│   └── post-commit                      ← non-blocking, cross-platform (python/python3/py)
│
├── vault_sync.config.json               ← template con _doc_* paralelos
├── AGENTS.md                            ← protocolo canónico (sustituye __PROJECT_NAME__ etc.)
├── CLAUDE.md                            ← @AGENTS.md
└── USAGE.md                             ← manual del dev del proyecto instanciado
```

---

## Costos en tokens (referencia relativa)

| Skill | Costo típico | Cuándo |
|---|---|---|
| `/snapshot` | **Alto** | Solo en arranque / refactor masivo. Lee facts.json + vault completo |
| `/sync` | **Medio** | Después de cada commit. Lee 2 artefactos + notas hint. Es el flujo natural |
| `/ingest <ruta>` | **Medio–Alto** | Depende del doc (PDF grande puede ser caro) |
| `/check` | **Bajo** | Mayormente determinista (corre `vault_sync.py check`); la interpretación semántica es por-capa |

El sistema está diseñado para que el grueso del trabajo lo haga el engine
determinista (0 LLM, 0 tokens). El LLM entra solo donde hace falta razonar
sobre semántica: proponer cambios al vault, detectar contradicciones,
ingerir documentos. La política "no leer código si está en facts.json" es
la palanca principal de control de tokens.

---

## Cómo contribuir

### Agregar un stack al catálogo

Cuando trabajás con una pila que no tiene archetype (Angular, Java, Go,
Rust, Ruby, etc.) y querés que el sistema la conozca:

1. Bootstrappeá con `--stack generic`. El extractor `generic` detectará la
   pila y dejará 2 scaffolds en disco:
   - `bootstrap/stacks/_proposed_<stack>.json` — hierarchy_mapping inferido
     de convenciones del lenguaje.
   - `scripts/lib/extractors/_proposed_<stack>.py` — clase Extractor con
     TODOs marcados y fallback al baseline genérico.
2. Editá el extractor: parsers específicos del framework (decoradores,
   modelos, schemas, rutas). Mirá `nextjs_laravel.py` como referencia de
   calidad y `python_generic.py` para inspiración multi-archivo.
3. Renombrá quitando el prefijo `_proposed_`:
   `_proposed_<stack>.json` → `<stack>.json`,
   `_proposed_<stack>.py` → `<stack>.py`.
4. Registrá la clase en `scripts/lib/extractors/__init__.py::REGISTRY`.
5. Verificá con `python scripts/vault_sync.py facts` que produce un facts.json coherente.

El catálogo crece **cuando vos usás la pila en serio**, no antes. El sistema
no inventa extractores.

### Actualizar un extractor existente

Cualquier mejora al extractor `python-generic` debería:

- Preservar campos que ya se exponen (downstream skills los esperan).
- Agregar campos nuevos sin romper el schema mínimo de `ExtractorBase`.
- Mantener 0 dependencias externas, 0 LLM, 0 red.

Si el cambio rompe compat hacia atrás, hay que bumpar `schema_version` en
`schema.py` y documentar en `CHANGELOG.md`.
