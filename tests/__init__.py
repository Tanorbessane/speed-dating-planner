"""Tests unitaires et d'intégration pour Speed Dating Planner.

Organisation:
    test_models.py: Tests structures de données
    test_validation.py: Tests validation configuration
    test_baseline.py: Tests algorithme baseline
    test_metrics.py: Tests calcul métriques
    test_improvement.py: Tests optimisation locale
    test_equity.py: Tests garantie d'équité
    test_planner.py: Tests pipeline complet
    test_exporters.py: Tests export CSV/JSON
    test_cli.py: Tests interface CLI

Markers:
    @pytest.mark.slow: Tests de performance (>1s)
    @pytest.mark.integration: Tests d'intégration end-to-end

Usage:
    pytest                     # Tous tests
    pytest -m "not slow"       # Exclure tests lents
    pytest --cov=src           # Avec couverture
"""
