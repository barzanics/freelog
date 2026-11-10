# Developer guide
- Layers: `core` (no deps) -> `services` (no Qt) -> `ui` (no SQL). Integrations are optional plugins and never imported at startup.
- Time: store aware UTC ISO text; show with `persian.to_tehran`. Day boundaries = Tehran midnight.
- Serialization lives only in `models._Row.to_row/from_row`. Never put Python lists in SQL.
- Transactions nest; only the outermost commits. Use `db.transaction()` around multi-step writes.
- Add a table: append a migration string to `database.MIGRATIONS`, register the model in `_TABLES`.
- Tests: `python -m unittest discover -s worktracker/tests -t .` ; benchmark: `python -m worktracker.tools.bench`.
