# 9. Plan de Migration Post-MVP

## 9.1 Epic 4 : Edge Cases & Dynamic Management

**Prérequis :** Epic 1-3 MVP validés en production

**Changements Architecture :**

1. **Détection Configurations Impossibles (FR12)**
   - Nouvelle fonction `detect_impossibility(config) -> bool`
   - Calcul borne inférieure répétitions
   - Retourner info utilisateur (pas juste warning)

2. **Gestion Retardataires/Abandons (FR14-FR15)**
   - Nouveau module `src/dynamic.py`
   - `handle_late_arrival(planning, participant_id, from_session) -> Planning`
   - `handle_dropout(planning, participant_id, from_session) -> Planning`
   - Recalcul partiel sessions futures uniquement
   - **Impact architecture :** Planning devient partiellement mutable (sessions futures)

**Migration :**
```python
# Avant (MVP)
planning, metrics = generate_optimized_planning(config)

# Après (Epic 4)
planning, metrics = generate_optimized_planning(config)
# ... durant événement ...
planning = handle_late_arrival(planning, participant_id=105, from_session=3)
planning = handle_dropout(planning, participant_id=42, from_session=5)
```

**Tests additionnels :**
- `test_dynamic.py` : Insertion/suppression sans dégrader équité
- `test_impossibility.py` : Détection correcte configs impossibles

---

## 9.2 Epic 5 : Visualization & Analysis Tools

**Prérequis :** Epic 4 optionnel, Epic 1-3 obligatoire

**Nouvelles Dépendances :**
```toml
[tool.poetry.dependencies]
matplotlib = { version = "^3.7", optional = true }
pandas = { version = "^2.0", optional = true }
openpyxl = { version = "^3.1", optional = true }  # Export Excel

[tool.poetry.extras]
viz = ["matplotlib", "pandas"]
export-all = ["openpyxl"]
```

**Nouveaux Modules :**

1. **src/visualization.py**
   - `plot_meeting_heatmap(planning, config, filepath)`
   - `plot_equity_distribution(metrics, filepath)`
   - Génération PNG/SVG

2. **src/exporters_extended.py**
   - `export_to_excel(planning, config, filepath)`
   - Feuilles multiples (sessions, métriques, stats)

3. **examples/notebook.ipynb**
   - Jupyter notebook interactif
   - Visualisations inline
   - Comparaison plannings

**Pas d'impact architecture core :** Modules additionnels optionnels, pas de changement pipeline.

---

## 9.3 Checklist Migration

Avant chaque Epic post-MVP :

- [ ] Validation Epic précédent (tests passent, couverture ≥85%)
- [ ] Revue architecture (nouveaux modules nécessaires ?)
- [ ] Mise à jour `docs/architecture.md` (nouvelles sections)
- [ ] Tests de régression (NFR1-3 toujours respectés)
- [ ] Documentation utilisateur mise à jour (README, user-guide)
- [ ] Benchmarks mis à jour (nouvelles instances test)

---
