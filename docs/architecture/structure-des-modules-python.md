# 2. Structure des Modules Python

## 2.1 Arborescence du Projet

```
speed-dating-planner/
├── src/
│   ├── __init__.py                    # Package principal
│   ├── models.py                      # Modèles de données (dataclasses)
│   ├── validation.py                  # Validation des configurations
│   ├── baseline.py                    # Phase 1 : Génération baseline
│   ├── optimizer.py                   # Phase 2 & 3 : Amélioration + Équité
│   ├── metrics.py                     # Calcul métriques et historique
│   ├── planner.py                     # Orchestrateur pipeline complet
│   ├── exporters.py                   # Export CSV/JSON
│   └── cli.py                         # Interface ligne de commande
├── tests/
│   ├── __init__.py
│   ├── test_models.py                 # Tests structures de données
│   ├── test_validation.py             # Tests validation
│   ├── test_baseline.py               # Tests génération baseline
│   ├── test_optimizer.py              # Tests amélioration/équité
│   ├── test_metrics.py                # Tests calcul métriques
│   ├── test_exporters.py              # Tests export
│   ├── test_cli.py                    # Tests parseur CLI
│   ├── test_integration_baseline.py   # Tests intégration phase 1
│   ├── test_integration_optimized.py  # Tests intégration pipeline complet
│   ├── test_cli_e2e.py                # Tests end-to-end subprocess
│   └── test_performance.py            # Benchmarks performance (NFR1-3)
├── examples/
│   ├── basic_usage.py                 # Exemple utilisation Python
│   ├── advanced_usage.py              # Exemple avec métriques détaillées
│   └── cli_usage.sh                   # Exemples commandes shell
├── docs/
│   ├── architecture.md                # Ce document
│   ├── prd.md                         # Product Requirements Document
│   ├── brainstorming-session-results.md
│   └── user-guide.md                  # Guide utilisateur détaillé
├── benchmarks/
│   └── results.json                   # Résultats benchmarks historiques
├── scripts/
│   └── run_benchmarks.py              # Script exécution benchmarks
├── pyproject.toml                     # Configuration Poetry
├── .pre-commit-config.yaml            # Hooks pre-commit
├── .gitignore
└── README.md
```

## 2.2 Responsabilités des Modules

### **models.py** - Modèles de Données
**Responsabilité :** Définir toutes les structures de données typées du domaine.

**Contenu :**
- `PlanningConfig` : Paramètres d'entrée (N, X, x, S) avec validation
- `Planning` : Représentation du planning complet
- `Session` : Liste de tables pour une session
- `Table` : Ensemble de participants (type alias `Set[int]`)
- `PlanningMetrics` : Toutes les métriques de qualité
- `InvalidConfigurationError` : Exception personnalisée

**Dépendances :** Aucune (module feuille)

---

### **validation.py** - Validation des Configurations
**Responsabilité :** Valider les contraintes FR1-FR2, lever exceptions explicites.

**Contenu :**
- `validate_config(config: PlanningConfig) -> None`
- Validation : N≥2, X≥1, x≥2, S≥1, X×x≥N
- Messages d'erreur en français (NFR10)

**Dépendances :** `models.py`

---

### **baseline.py** - Phase 1 : Génération Baseline
**Responsabilité :** Générer rapidement un planning valide initial (round-robin généralisé).

**Contenu :**
- `generate_baseline(config: PlanningConfig, seed: int = 42) -> Planning`
- Algorithme rotation systématique avec stride
- Gestion tables partielles (N non-multiple de x)
- Complexité O(N × S)

**Dépendances :** `models.py`

---

### **metrics.py** - Métriques et Historique
**Responsabilité :** Calculer historique rencontres et métriques de qualité.

**Contenu :**
- `compute_meeting_history(planning: Planning) -> Set[Tuple[int, int]]`
- `compute_metrics(planning: Planning, config: PlanningConfig) -> PlanningMetrics`
- Calcul paires uniques, répétitions, stats équité, distribution tables
- Complexité O(S × X × x²) pour historique, O(N) pour métriques

**Dépendances :** `models.py`

---

### **optimizer.py** - Phase 2 & 3 : Amélioration et Équité
**Responsabilité :** Optimiser le planning baseline via swaps locaux et garantir équité ±1.

**Contenu :**
- `evaluate_swap(planning, session_id, table1_id, p1, table2_id, p2, met_pairs) -> int`
- `improve_planning(planning: Planning, config: PlanningConfig, max_iterations: int = 100) -> Planning`
- `enforce_equity(planning: Planning, config: PlanningConfig) -> Planning`
- Heuristique gloutonne avec détection plateau local
- Post-traitement swaps ciblés pour écart rencontres ≤1

**Dépendances :** `models.py`, `metrics.py`

---

### **planner.py** - Orchestrateur Pipeline
**Responsabilité :** Orchestrer le pipeline complet 3 phases et retourner résultat final.

**Contenu :**
- `generate_optimized_planning(config: PlanningConfig, seed: int = 42) -> Tuple[Planning, PlanningMetrics]`
- Séquence : Baseline → Amélioration → Équité → Métriques
- Logging des étapes principales (INFO)
- Gestion configurations impossibles (WARNING loggé)

**Dépendances :** `models.py`, `validation.py`, `baseline.py`, `optimizer.py`, `metrics.py`

---

### **exporters.py** - Export Fichiers
**Responsabilité :** Exporter plannings aux formats CSV et JSON selon FR10-FR11.

**Contenu :**
- `export_to_csv(planning: Planning, config: PlanningConfig, filepath: str) -> None`
- `export_to_json(planning: Planning, config: PlanningConfig, filepath: str, include_metadata: bool = True) -> None`
- Format CSV : colonnes `session_id, table_id, participant_id`
- Format JSON : structure `{"sessions": [...]}`
- Encodage UTF-8 (avec BOM pour CSV/Excel)

**Dépendances :** `models.py`

---

### **cli.py** - Interface Ligne de Commande
**Responsabilité :** Parser arguments CLI, exécuter pipeline, afficher résultats.

**Contenu :**
- `parse_args() -> argparse.Namespace`
- `main() -> int` (retourne exit code)
- Arguments : `--participants`, `--tables`, `--capacity`, `--sessions`, `--output`, `--format`, `--seed`, `--verbose`
- Affichage console des métriques clés
- Gestion erreurs robuste avec messages français

**Dépendances :** `models.py`, `planner.py`, `exporters.py`

---

## 2.3 Graphe de Dépendances

```
                        ┌──────────┐
                        │ models.py│ (Base - aucune dépendance)
                        └─────┬────┘
                              │
              ┌───────────────┼───────────────┬───────────────┐
              │               │               │               │
              ▼               ▼               ▼               ▼
        ┌──────────┐   ┌───────────┐   ┌──────────┐   ┌────────────┐
        │validation│   │baseline.py│   │metrics.py│   │exporters.py│
        └─────┬────┘   └─────┬─────┘   └─────┬────┘   └────────────┘
              │              │               │
              │              │               │
              │              ▼               │
              │        ┌──────────┐          │
              │        │optimizer │◀─────────┘
              │        │   .py    │ (dépend metrics)
              │        └─────┬────┘
              │              │
              └──────────────┼───────────┐
                             │           │
                             ▼           │
                        ┌─────────┐      │
                        │planner  │◀─────┘
                        │  .py    │ (dépend tous)
                        └────┬────┘
                             │
                             ▼
                        ┌─────────┐
                        │ cli.py  │ (dépend planner + exporters)
                        └─────────┘
```

**Principe :** Dépendances unidirectionnelles, pas de cycles. Les modules de bas niveau (models, baseline) ne dépendent jamais des modules de haut niveau (cli, planner).

---
