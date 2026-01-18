# Standards de Code - Speed Dating Planner

## Vue d'Ensemble

Ce document définit les standards de qualité et de style pour le projet Speed Dating Planner. Tous les contributeurs doivent respecter ces règles pour maintenir la cohérence et la qualité du code.

---

## Python Version

**Version minimum:** Python 3.10+

**Raison:** Utilisation des fonctionnalités modernes (match/case, union types avec `|`, etc.)

---

## Dépendances

### Runtime (Production)

**Standard Library UNIQUEMENT** - Aucune dépendance externe

**Modules autorisés:**
- `dataclasses` - Structures de données
- `typing` - Type hints
- `random` - Génération aléatoire (seed-based)
- `csv` - Export CSV
- `json` - Export JSON
- `argparse` - CLI interface
- `logging` - Logging structuré
- `pathlib` - Manipulation fichiers
- `sys` - Exit codes

### Développement

- `pytest` - Framework de tests
- `pytest-cov` - Couverture de code
- `black` - Formatage automatique
- `ruff` - Linting rapide
- `mypy` - Type checking strict
- `pre-commit` - Hooks git

---

## Formatage - Black

**Configuration:**
```toml
line-length = 100
target-version = ['py310']
```

**Exécution:**
```bash
black src/ tests/
black --check src/ tests/  # Vérification sans modification
```

**Règles:**
- Longueur ligne max: 100 caractères
- Indentation: 4 espaces (pas de tabs)
- Quotes: doubles (`"`) pour strings, simples (`'`) autorisées
- Trailing commas: oui pour multi-lignes

---

## Linting - Ruff

**Configuration:**
```toml
line-length = 100
target-version = "py310"
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

**Exécution:**
```bash
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix
```

**Règles activées:**
- `E/W`: pycodestyle (PEP 8)
- `F`: pyflakes (erreurs logiques)
- `I`: isort (imports triés)
- `B`: flake8-bugbear (bugs communs)
- `C4`: flake8-comprehensions (optimisations)
- `UP`: pyupgrade (modernisation Python)

---

## Type Checking - MyPy

**Mode:** `--strict`

**Exécution:**
```bash
mypy src/ --strict
mypy tests/ --strict
```

**Règles strictes:**
- `disallow_untyped_defs`: Toutes fonctions typées
- `disallow_incomplete_defs`: Pas de types partiels
- `no_implicit_optional`: Optional explicite uniquement
- `warn_return_any`: Warn sur retours `Any`
- `warn_unused_ignores`: Warn sur `# type: ignore` inutiles

**Type hints obligatoires:**
```python
# ✅ Bon
def compute_metric(planning: Planning, config: PlanningConfig) -> int:
    return 42

# ❌ Mauvais
def compute_metric(planning, config):
    return 42
```

---

## Tests - Pytest

**Structure:**
```
tests/
├── test_models.py
├── test_validation.py
├── test_baseline.py
├── test_metrics.py
└── ...
```

**Convention nommage:**
- Fichiers: `test_*.py`
- Classes: `TestClassName`
- Fonctions: `test_function_name`

**Markers:**
```python
@pytest.mark.slow  # Tests lents (>1s)
@pytest.mark.integration  # Tests d'intégration
```

**Exécution:**
```bash
pytest                     # Tous tests
pytest -m "not slow"       # Exclure tests lents
pytest -v --cov=src        # Avec couverture
pytest --cov-fail-under=85 # Fail si coverage <85%
```

---

## Couverture de Code

**Cibles:**
- **Epic 1-2 (core algo):** ≥90%
- **Epic 3 (CLI/export):** ≥85%
- **Projet global:** ≥85%

**Exclusions:**
```python
if __name__ == "__main__":  # pragma: no cover
    main()
```

**Vérification:**
```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=85
pytest --cov=src --cov-report=html  # Rapport HTML
```

---

## Docstrings - Google Style

**Format standard:**
```python
def function_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """Résumé court (impératif, français).

    Description détaillée optionnelle sur plusieurs lignes.
    Explique le comportement, les algorithmes, les cas particuliers.

    Args:
        arg1: Description de arg1
        arg2: Description de arg2

    Returns:
        Description de la valeur retournée

    Raises:
        ValueError: Si arg1 est invalide
        TypeError: Si arg2 n'est pas du bon type

    Example:
        >>> function_name(value1, value2)
        42

    Complexity:
        Time: O(N)
        Space: O(1)
    """
    pass
```

**Règles:**
- Résumé en français, impératif, <80 caractères
- Args/Returns/Raises obligatoires si applicable
- Example pour fonctions publiques complexes
- Complexity pour algorithmes (optionnel mais recommandé)

---

## Structure Code

### Imports

**Ordre (géré par ruff/isort):**
1. Standard library
2. Third-party (dev uniquement)
3. Local modules

**Exemple:**
```python
# Standard library
import csv
import json
import logging
from dataclasses import dataclass
from typing import Set, List, Tuple

# Local
from src.models import Planning, PlanningConfig
from src.validation import validate_config
```

### Dataclasses

**Préférer frozen pour immutabilité:**
```python
@dataclass(frozen=True)
class PlanningConfig:
    N: int
    X: int
    x: int
    S: int
```

### Exceptions

**Exceptions custom avec messages français:**
```python
class InvalidConfigurationError(ValueError):
    """Configuration invalide détectée."""
    pass

raise InvalidConfigurationError(
    f"Capacité insuffisante : {X} tables × {x} places = {total} < {N} participants"
)
```

---

## Logging

**Configuration:**
```python
import logging

logger = logging.getLogger(__name__)
```

**Niveaux:**
- `DEBUG`: Détails internes (verbose mode)
- `INFO`: Étapes importantes (succès, métriques)
- `WARNING`: Situations inhabituelles (écrasement fichier)
- `ERROR`: Erreurs récupérables
- `CRITICAL`: Erreurs fatales

**Exemple:**
```python
logger.info(f"Planning généré avec succès : {metrics.total_unique_pairs} paires")
logger.warning(f"Fichier existant écrasé : {filepath}")
logger.error(f"Export échoué : {e}")
```

**Messages en français (NFR10):**
```python
# ✅ Bon
logger.info("Configuration validée avec succès")

# ❌ Mauvais
logger.info("Configuration validated successfully")
```

---

## Git Workflow

### Pre-commit Hooks

**Installation:**
```bash
poetry install
pre-commit install
```

**Hooks actifs:**
1. Trailing whitespace removal
2. End-of-file fixer
3. YAML/TOML check
4. Black formatting
5. Ruff linting + auto-fix
6. MyPy type checking

**Bypass (déconseillé):**
```bash
git commit --no-verify  # Éviter sauf urgence
```

### Commit Messages

**Format:**
```
[Story X.Y] Titre court (impératif, <50 chars)

Description détaillée optionnelle :
- Point 1
- Point 2

Refs: #issue-number
```

**Exemple:**
```
[Story 1.4] Implémenter algorithme baseline round-robin

- Génération rotation avec stride coprime
- Gestion tables partielles (FR7)
- Tests déterminisme seed (NFR11)

Refs: #4
```

---

## Performance

### Benchmarks

**Marquage:**
```python
@pytest.mark.slow
def test_performance_n100():
    """NFR1: N=100 doit s'exécuter en <2s."""
    start = time.time()
    # Test...
    duration = time.time() - start
    assert duration < 2.0
```

**Exécution séparée:**
```bash
pytest -m slow  # Uniquement benchmarks
```

### Complexité

**Documenter dans docstrings:**
```python
def compute_meeting_history(planning: Planning) -> Set[Tuple[int, int]]:
    """Calcule l'historique des rencontres.

    Complexity:
        Time: O(S × X × x²)
        Space: O(N²) worst-case
    """
```

---

## Security & Best Practices

### Path Handling

**Utiliser pathlib:**
```python
from pathlib import Path

output_path = Path(filepath)
if output_path.exists():
    logger.warning(f"Fichier écrasé : {filepath}")
```

### Input Validation

**Toujours valider entrées utilisateur:**
```python
def export_to_csv(planning: Planning, config: PlanningConfig, filepath: str) -> None:
    if not filepath:
        raise ValueError("Le chemin de fichier ne peut pas être vide")
    # ...
```

### Randomness

**Seed explicite pour reproductibilité (NFR11):**
```python
import random

def generate_baseline(config: PlanningConfig, seed: int = 42) -> Planning:
    random.seed(seed)  # Déterminisme
    # ...
```

---

## CLI Standards

### Pas de logique métier

**CLI = orchestration uniquement:**
```python
# ✅ Bon
def main() -> int:
    args = parse_args()
    config = PlanningConfig(args.participants, args.tables, args.capacity, args.sessions)
    planning, metrics = generate_optimized_planning(config, seed=args.seed)
    export_to_csv(planning, config, args.output)
    return 0

# ❌ Mauvais (logique métier dans CLI)
def main() -> int:
    # Calculs complexes directement dans main()...
```

### Exit Codes

**Standards:**
- `0`: Succès
- `1`: Configuration invalide (erreur utilisateur)
- `2`: Erreur I/O (export, permissions)
- `3`: Erreur inattendue (bug)

### Messages Français (NFR10)

**Tous messages utilisateur en français:**
```python
parser.add_argument('-n', '--participants', type=int, required=True,
                   help="Nombre total de participants (N ≥ 2)")
```

---

## Outputs Déterministes

### CSV/JSON

**Ordre stable pour reproductibilité:**
```python
# Trier participants dans chaque table
for participant_id in sorted(table):
    writer.writerow([session_id, table_id, participant_id])

# JSON avec tri activé
json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
```

---

## Checklist Code Review

Avant chaque PR, vérifier:

- [ ] `pytest` - Tous tests passent
- [ ] `pytest --cov=src --cov-fail-under=85` - Couverture ≥85%
- [ ] `black --check src/ tests/` - Formatage OK
- [ ] `ruff check src/ tests/` - Linting OK
- [ ] `mypy src/ --strict` - Type checking OK
- [ ] Docstrings Google style présentes
- [ ] Messages en français (NFR10)
- [ ] QA gate YAML validé
- [ ] Pas de dépendances runtime ajoutées
- [ ] Outputs déterministes (si applicable)
- [ ] Tests performance marqués `@pytest.mark.slow`

---

## Références

- **PEP 8:** https://peps.python.org/pep-0008/
- **Black:** https://black.readthedocs.io/
- **Ruff:** https://beta.ruff.rs/docs/
- **MyPy:** https://mypy.readthedocs.io/
- **Pytest:** https://docs.pytest.org/
- **Google Style Docstrings:** https://google.github.io/styleguide/pyguide.html

---

**Version:** 1.0
**Dernière mise à jour:** 2026-01-11
**Auteur:** Speed Dating Team
