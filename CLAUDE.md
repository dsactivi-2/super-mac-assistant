# Projekt-Regeln: super-mac-assistant

## Testing (PFLICHT)

### Bei jedem Code:

- Test-IDs in UI-Elementen
- Tests SOFORT mitschreiben
- Vor Commit: `pytest` ausführen

### Ordnerstruktur

```
tests/
├── test_*.py
└── conftest.py (falls nötig)
```

### Tests ausführen

```bash
pytest
pytest --cov=. --cov-report=term
```

## Projekt-Info

- Sprache: Python
- Typ: macOS Assistant App
