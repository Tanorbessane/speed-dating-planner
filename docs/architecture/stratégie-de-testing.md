# 5. Stratégie de Testing

## 5.1 Pyramide de Tests

```
                    ▲
                   ╱ ╲
                  ╱ E2E╲          10% - Tests End-to-End
                 ╱───────╲         (subprocess CLI, fichiers réels)
                ╱  INTEGR ╲       20% - Tests Intégration
               ╱  ATION    ╲      (pipeline complet, multi-modules)
              ╱─────────────╲
             ╱   UNIT TESTS  ╲   70% - Tests Unitaires
            ╱─────────────────╲  (fonctions isolées, logique pure)
           ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
```

## 5.2 Tests Unitaires (70%)

**Modules à tester :**

1. **test_models.py**
   - Validation dataclasses (création valide/invalide)
   - Propriétés dérivées (`equity_gap`)
   - Immutabilité `PlanningConfig`

2. **test_validation.py**
   - Tous les cas FR1-FR2 (N, X, x, S dans limites)
   - Capacité insuffisante (X×x < N)
   - Messages d'erreur français exacts
   - Couverture cible : 100%

3. **test_baseline.py**
   - Planning valide généré (tous participants assignés)
   - Tables partielles (N=37, X=6, x=7)
   - Déterminisme (seed → même résultat)
   - Performance : N=100 en <1s
   - Couverture cible : 95%

4. **test_metrics.py**
   - `compute_meeting_history` : paires normalisées
   - `compute_metrics` : calcul correct sur plannings connus
   - Cas limites (N=2, S=1)
   - Couverture cible : 90%

5. **test_optimizer.py**
   - `evaluate_swap` : détection amélioration/dégradation
   - `improve_planning` : réduction répétitions mesurable
   - `enforce_equity` : garantie écart ≤1
   - Plateau local détecté
   - Couverture cible : 85%

6. **test_exporters.py**
   - CSV : colonnes correctes, encodage UTF-8-BOM
   - JSON : structure conforme FR11
   - Parsing inverse (lire fichier généré)
   - Gestion chemins avec espaces
   - Couverture cible : 95%

7. **test_cli.py**
   - Parsing arguments valides/invalides
   - Valeurs par défaut
   - Messages d'aide en français
   - Couverture cible : 90%

**Fixtures communes :**
```python
@pytest.fixture
def config_simple():
    """Config standard N=30."""
    return PlanningConfig(N=30, X=5, x=6, S=6)

@pytest.fixture
def config_medium():
    """Config moyenne N=100."""
    return PlanningConfig(N=100, X=20, x=5, S=10)

@pytest.fixture
def config_large():
    """Config grande N=300."""
    return PlanningConfig(N=300, X=60, x=5, S=15)
```

## 5.3 Tests d'Intégration (20%)

**1. test_integration_baseline.py**
- Pipeline Phase 1 complet : Config → Baseline → Métriques
- Exemples A (N=30) et B (N=100)
- Validation : aucun participant oublié, tables équilibrées

**2. test_integration_optimized.py**
- Pipeline 3 phases complet : Baseline → Amélioration → Équité
- Vérification amélioration mesurable (baseline vs optimisé)
- Configuration impossible : warning loggé, équité garantie
- Grande instance (N=300, <5s)

**3. test_cli_e2e.py**
- Subprocess calls réels via `speed-dating-planner`
- Génération CSV/JSON avec fichiers réels
- Configuration invalide → exit code 1
- Mode verbose → logs DEBUG visibles

## 5.4 Tests de Performance (Benchmarks)

**test_performance.py** (marqués `@pytest.mark.slow`) :

```python
@pytest.mark.slow
def test_performance_nfr1_n100():
    """NFR1: N≤100 en <2s."""
    config = PlanningConfig(N=100, X=20, x=5, S=10)
    start = time.time()
    planning, metrics = generate_optimized_planning(config)
    elapsed = time.time() - start
    assert elapsed < 2.0, f"Temps: {elapsed:.2f}s (limite 2s)"

@pytest.mark.slow
def test_performance_nfr2_n300():
    """NFR2: N≤300 en <5s."""
    config = PlanningConfig(N=300, X=60, x=5, S=15)
    start = time.time()
    planning, metrics = generate_optimized_planning(config)
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Temps: {elapsed:.2f}s (limite 5s)"

@pytest.mark.slow
def test_performance_nfr3_n1000():
    """NFR3: N≤1000 en <30s."""
    config = PlanningConfig(N=1000, X=200, x=5, S=25)
    start = time.time()
    planning, metrics = generate_optimized_planning(config)
    elapsed = time.time() - start
    assert elapsed < 30.0, f"Temps: {elapsed:.2f}s (limite 30s)"
```

**Script `scripts/run_benchmarks.py` :**
- Exécute tous benchmarks
- Génère rapport JSON (`benchmarks/results.json`)
- Détection régression (>10% ralentissement vs précédent)

## 5.5 Stratégie d'Exécution

**Tests rapides (CI sur chaque PR) :**
```bash
pytest -v --cov=src --cov-report=html -m "not slow"
```
- Exécute unitaires + intégration (hors performance)
- Temps total : <10s
- Couverture minimale : 85%

**Tests complets (CI sur merge main) :**
```bash
pytest -v --cov=src --cov-report=html
python scripts/run_benchmarks.py
```
- Tous tests + benchmarks
- Temps total : <2min
- Vérification NFR1-3

---
