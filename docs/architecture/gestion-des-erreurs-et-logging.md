# 7. Gestion des Erreurs et Logging

## 7.1 Hiérarchie des Exceptions

```python
Exception
└── InvalidConfigurationError  (src/models.py)
    ├── "Nombre de participants invalide : N={N}. Minimum requis : 2"
    ├── "Nombre de tables invalide : X={X}. Minimum requis : 1"
    ├── "Capacité de table invalide : x={x}. Minimum requis : 2"
    ├── "Nombre de sessions invalide : S={S}. Minimum requis : 1"
    └── "Capacité insuffisante : {X} tables × {x} places = {total} < {N} participants"
```

**Principe :** Messages d'erreur explicites en français (NFR10), incluant valeurs problématiques.

## 7.2 Stratégie de Logging

### Niveaux de Logs

**DEBUG :** Détails internes (activé via `--verbose`)
```python
logger.debug(f"Swap évalué : p{p1} ↔ p{p2}, delta={delta}")
```

**INFO :** Progression pipeline et résultats clés
```python
logger.info("Phase 1 : Baseline générée ✓")
logger.info(f"Itération {iteration}: {swaps} swaps appliqués")
```

**WARNING :** Situations anormales non-bloquantes
```python
logger.warning("Configuration mathématiquement impossible pour zéro répétition")
logger.warning(f"Fichier existant écrasé : {filepath}")
```

**ERROR :** Erreurs bloquantes (rare, CLI gère via exceptions)
```python
logger.error(f"Impossible d'écrire {filepath}: {e}")
```

### Configuration Logging

**CLI par défaut (INFO) :**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
```

**Mode verbose (DEBUG) :**
```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 7.3 Gestion Erreurs par Module

| Module | Exceptions Levées | Gestion |
|--------|------------------|---------|
| `validation.py` | `InvalidConfigurationError` | Propagée à CLI |
| `baseline.py` | Aucune (config validée en amont) | - |
| `optimizer.py` | Aucune (logique pure) | - |
| `exporters.py` | `IOError` (échec écriture) | Propagée à CLI |
| `cli.py` | Aucune (catch all) | Exit codes 1-3 |

**Principe :** Validation au plus tôt (validation.py), propagation exceptions, gestion centralisée (CLI).

---
