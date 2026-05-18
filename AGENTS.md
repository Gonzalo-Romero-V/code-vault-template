# __PROJECT_NAME__ — Guía para agentes de IA

> Esta guía es **canónica** y la lee cualquier CLI de IA que abra el repo
> (Claude Code, Codex CLI, Cursor, etc.). `CLAUDE.md` la importa con `@AGENTS.md`.
>
> Stack activo: **`__STACK__`** (extractor configurado en `vault_sync.config.json`).

---

## ⚠️ Pre-flight obligatorio (antes de tocar código)

El proyecto tiene un **vault Obsidian** como fuente de verdad semántica.
El código (H4–H5) refleja al vault (H1–H3), nunca al revés.
**Saltar este protocolo produce código que contradice contratos documentados.**

Toda sesión nueva, antes de la primera respuesta no-trivial, debe:

1. **Leer este archivo completo** — ya estás acá, sigamos.
2. **Leer el `INDEX.md` del vault** (`__VAULT_ABSOLUTE_PATH__/INDEX.md`). Nota: el vault NO está dentro del repo; vive en una carpeta separada (path absoluto, no relativo).
3. **Identificar la tarea** y consultar la tabla de abajo para saber qué notas leer.
4. **Leer SOLO esas notas** — no leer el vault completo, no inventar.
5. **Recién entonces** explorar código del repo.

Si la tarea es trivial y no toca dominio (cambiar un copy, fix de import,
ajustar un README), los pasos 3–5 son opcionales — usá criterio.

---

## Qué notas leer según la tarea

> **Esta tabla es la mitad del valor del sistema.** Las filas de abajo son
> ejemplos genéricos — al instanciar el proyecto, reemplazalas con los
> flujos reales de TU dominio. Ver la sección "Adaptación al proyecto" al final.

| Tarea | Notas obligatorias |
|-------|---------------------|
| Nueva entidad de dominio | `domain/<entidad>.md` + `decisions/architecture.md` |
| Nueva ruta / endpoint | `decisions/api-contracts.md` (si existe) + `domain/<entidad>.md` |
| Cambio de modelo / schema | `domain/<entidad>.md` + `domain/data-model.md` (si existe) |
| Refactor de autenticación | `decisions/architecture.md` + `intent/vision.md` |
| Cambio de stack / librería estructural | `decisions/stack.md` + impacto en H4 completo |
| Feature cross-entidad | todas las `domain/*.md` involucradas |

Si una nota referenciada no existe → **preguntar al humano**, no inventar.

---

## Regla de oro: contradicción → reportar, no resolver

Si el código actual contradice una nota del vault con `status: stable` o `locked`:

1. Parar.
2. Reportar al humano qué nota dice qué y qué código contradice.
3. Esperar decisión.

Resolver unilateralmente es **prohibido** (`SYSTEM.md`, regla 3).

---

## Estados de las notas

| Status | Edición |
|--------|---------|
| `draft` | Modificable libremente vía `/sync` |
| `stable` | Solo `code_path` y `append_section` vía `/sync` |
| `locked` | Inmutable — solo edición humana directa |
| `deprecated` | Histórico — nadie la actualiza |

Operaciones prohibidas siempre:

- Borrar archivos del vault.
- Sobrescribir cuerpo completo de una nota.
- Modificar notas `locked`.

---

## Flujo de trabajo cotidiano

```
1. Recibís tarea
2. Pre-flight (arriba) → leer vault relevante
3. Implementás código
4. Pedís al humano permiso para commit + proponés mensaje
5. git commit
   └─ post-commit hook genera .vault-sync/{change_report,facts}.json automáticamente
6. /sync skill → propone cambios al vault basados en el reporte
7. Humano revisa propuesta → aprueba o ajusta
8. apply ejecuta → vault queda alineado al código
```

**Después de cada commit no-trivial, sugerí al humano correr `/sync`** para
que el grafo refleje el estado actual. Si no se hace, el vault drifta y la
próxima sesión de IA tendrá contexto desactualizado.

Si el commit fue solo refactor de implementación (H5), `/sync` puede
proponer 0 cambios — eso es correcto.

---

## Reglas inviolables (resumen)

1. **Antes de tocar dominio**: leer las notas correspondientes del vault.
2. **Antes de cualquier commit / push**: pedir confirmación explícita al humano.
3. **Nunca** modificar notas con `status: locked`.
4. **Nunca** borrar notas (usar `deprecate` si hace falta).
5. **Nunca** commitear secrets (`.env`, credenciales, claves API).
6. **Solo proponer** cambios al vault; la aplicación la hace `apply` tras aprobación.
7. **Preferir scripts deterministas** (`scripts/vault_sync.py`) sobre razonamiento
   LLM cuando la operación es estructural (extracción de modelos, migraciones,
   rutas, imports).

---

## Skills disponibles

| Skill | Cuándo usar |
|-------|-------------|
| `/snapshot` | Solo en arranque de proyecto, refactor masivo, o sospecha de drift severo. Caro en tokens. |
| `/sync` | Después de cada commit aprobado. El flujo natural de mantenimiento del grafo. |
| `/ingest <ruta>` | Después de dropear un PDF / .txt / imagen en `vault/raw/`. |
| `/check` | Cuando dudes de la coherencia entre código y vault. Solo reporta, no resuelve. |

> **Si tu CLI no soporta slash commands** (Codex CLI, Cursor, Cline, Continue,
> etc.), las mismas 4 operaciones están documentadas de forma agnóstica en
> [`prompts/SKILLS.md`](prompts/SKILLS.md). Cuando el usuario te pida
> "sincronizar", "auditar", "ingerir" o "tomar snapshot", leé ese archivo
> antes de operar. El engine determinista (`scripts/vault_sync.py`) es el
> mismo en todos los casos.

Más detalle en `USAGE.md` (cara dev) y `vault/SYSTEM.md` (cara agente).

---

## Contexto rápido del proyecto

### Vault y código

- **Vault**: `__VAULT_ABSOLUTE_PATH__`
- **Sistema vault-sync**: `vault/SYSTEM.md` (locked, leer una vez por sesión)
- **Manual de uso humano**: `USAGE.md`
- **Engine determinista**: `scripts/vault_sync.py` (stdlib only, 0 deps externas)
- **Estado en vivo**: `.vault-sync/facts.json` — snapshot semántico, actualizado
  por el post-commit hook. **No leer el código si la respuesta ya está acá.**
- **Extractor activo**: `__STACK__`. Los campos que produce en `facts.json`
  varían según el extractor; ver `scripts/lib/extractors/<extractor>.py` para
  el contrato exacto.

### Stack

Documentado en `vault/decisions/stack.md`. Si tocás dependencias, librerías
estructurales o decisiones de stack, esa nota es lectura **obligatoria**.

### Convenciones

Documentadas en `vault/decisions/architecture.md`: capas, naming, manejo de
errores, autenticación, separación de responsabilidades. Cualquier feature
que toque más de un archivo debería respetar esas convenciones.

### Commits

- Mensajes en inglés (o como decidas en `decisions/git.md` si existe).
- Prefijos: `feat: fix: refactor: docs: style: chore: test:`.
- Cortos y honestos sobre el "qué/por qué", no sobre el "cómo".

---

## Adaptación al proyecto

Este `AGENTS.md` se generó al bootstrappear con `--stack __STACK__` el `__DATE__`.
**Antes de empezar a operar el sistema en serio**, hacé esto una vez:

1. **Completar la tabla "Qué notas leer según la tarea"** con filas
   específicas del dominio del proyecto. Las filas de ejemplo son
   genéricas — reemplazalas con los flujos reales que tu equipo ejecuta a
   diario (ej. "agregar producto al catálogo", "procesar pago", "exportar
   reporte mensual").
2. **Crear las notas fundacionales**, en este orden:
   - `vault/intent/vision.md` (H1 — define el porqué, **obligatoria antes
     del primer feature**).
   - `vault/decisions/stack.md` (H3 — define las tecnologías y por qué).
   - `vault/decisions/architecture.md` (H3 — define las capas y convenciones).
3. **Editar `vault/INDEX.md`** para reflejar la realidad: agregar wikilinks
   a las notas que vayas creando, completar la tabla "tarea → notas
   obligatorias" con los flujos reales del proyecto.

Esta tabla **es la mitad del valor del sistema**. Sin ella, los agentes no
saben qué leer antes de tocar código en cada área del repo. Invertir 15
minutos al inicio del proyecto rinde durante toda su vida.

---

## Por qué este protocolo existe (anti-patrón histórico)

Sin pre-flight, una IA típicamente:

1. **Inventa enums**: ej. asume `Pedido.estado = "preparando|listo"` cuando
   el canónico es `pendiente|en_camino|entregado|cancelado` (especificado
   en `domain/pedido.md`).
2. **Duplica endpoints** o contradice una matriz de permisos documentada
   en `decisions/rbac.md`.
3. **Deja el vault desactualizado**, drifteando capa H4 vs H2 hasta que
   nadie sabe cuál tiene razón.

El vault existe precisamente para que la próxima sesión de IA pueda
recuperar contexto en **pocos tokens** (notas concisas, hipervínculos
`[[entidad]]`, índice). Cada vez que se salta `/sync`, se rompe ese contrato.

Tres frases que resumen el sistema:

> El código (H4–H5) refleja al vault (H1–H3), nunca al revés.
> El vault es la fuente de verdad semántica; el código es la fuente de verdad técnica.
> Contradicción se reporta, no se resuelve unilateralmente.
