# tests/ — suite mínima del engine

Cobertura: módulos cuyo correcto funcionamiento es contractual para todas las
skills downstream. Stdlib `unittest` only, zero deps externas.

Correr:

```
python -m unittest discover -s tests -t .
```

Cubre:

- `hierarchy.detect_layer` / `_match_any` — glob `**` con boundary correctos.
- `vault.parse_frontmatter` — quotes balanceadas, listas YAML ignoradas en dict.
- `vault.update_frontmatter_text` — preservación de listas YAML, idempotencia.
- `apply.apply_changes` — locked guard, idempotencia, las 4 actions.
- `schema.validate_report` — rechaza JSON malformados.

Si tocás módulos del engine, **agregá un test** que cubra el cambio antes de
shippearlo. Eso es lo que distingue a este sistema de un script de un solo uso.
