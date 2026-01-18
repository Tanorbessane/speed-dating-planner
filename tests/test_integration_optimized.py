"""Tests d'intégration pour pipeline optimisé (Epic 2).

Test coverage:
    - Pipeline complet end-to-end
    - Régression: optimisé améliore baseline
    - Garantie FR6 (equity_gap ≤ 1)
    - Métriques cohérentes
"""

import pytest

from src.baseline import generate_baseline
from src.metrics import compute_metrics
from src.models import PlanningConfig
from src.planner import generate_optimized_planning
from src.validation import InvalidConfigurationError


class TestIntegrationOptimized:
    """Tests d'intégration du pipeline optimisé complet."""

    def test_end_to_end_optimized_success(self) -> None:
        """Test pipeline optimisé complet end-to-end."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Pipeline complet
        planning, metrics = generate_optimized_planning(config, seed=42)

        # Vérifications structurelles
        assert len(planning.sessions) == 6
        assert all(len(s.tables) == 5 for s in planning.sessions)
        assert all(s.total_participants == 30 for s in planning.sessions)

        # Vérifications métriques
        assert metrics.total_unique_pairs > 0
        assert metrics.equity_gap <= 1  # FR6
        assert len(metrics.unique_meetings_per_person) == 30

    def test_regression_optimized_reduces_repeats(self) -> None:
        """Test régression: optimisé réduit répétitions vs baseline."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Baseline
        baseline = generate_baseline(config, seed=42)
        metrics_baseline = compute_metrics(baseline, config)

        # Optimisé
        planning, metrics_optimized = generate_optimized_planning(config, seed=42)

        # Régression: répétitions RÉDUITES (ou égales)
        assert (
            metrics_optimized.total_repeat_pairs
            <= metrics_baseline.total_repeat_pairs
        ), "Régression: répétitions augmentées vs baseline !"

        # Log amélioration
        reduction = (
            metrics_baseline.total_repeat_pairs
            - metrics_optimized.total_repeat_pairs
        )
        pct = (
            100 * reduction / max(metrics_baseline.total_repeat_pairs, 1)
        )
        print(
            f"Amélioration: {reduction} répétitions réduites ({pct:.1f}%)"
        )

    def test_regression_equity_improved_or_equal(self) -> None:
        """Test régression: équité améliorée ou égale vs baseline."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Baseline
        baseline = generate_baseline(config, seed=42)
        metrics_baseline = compute_metrics(baseline, config)

        # Optimisé
        planning, metrics_optimized = generate_optimized_planning(config, seed=42)

        # Régression: equity_gap RÉDUIT (ou égal)
        assert (
            metrics_optimized.equity_gap <= metrics_baseline.equity_gap
        ), "Régression: équité dégradée vs baseline !"

        # Log amélioration
        print(
            f"Équité : baseline gap={metrics_baseline.equity_gap}, "
            f"optimisé gap={metrics_optimized.equity_gap}"
        )

    def test_invalid_config_rejected(self) -> None:
        """Test configuration invalide rejetée."""
        config = PlanningConfig(N=50, X=5, x=8, S=3)  # Capacité insuffisante

        with pytest.raises(InvalidConfigurationError):
            generate_optimized_planning(config, seed=42)

    def test_example_a_optimized(self) -> None:
        """Test Exemple A optimisé (N=30)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # Vérifications PRD
        assert len(planning.sessions) == 6
        assert metrics.equity_gap <= 1  # FR6
        assert metrics.total_unique_pairs > 0

    def test_example_b_optimized(self) -> None:
        """Test Exemple B optimisé (N=100)."""
        config = PlanningConfig(N=100, X=20, x=5, S=10)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # Vérifications PRD
        assert len(planning.sessions) == 10
        assert metrics.equity_gap <= 1  # FR6
        assert len(metrics.unique_meetings_per_person) == 100

    def test_all_participants_assigned_all_sessions(self) -> None:
        """Test tous participants assignés dans toutes sessions."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        for session in planning.sessions:
            all_assigned = set()
            for table in session.tables:
                all_assigned.update(table)
            assert all_assigned == set(range(30))

    def test_metrics_consistency(self) -> None:
        """Test cohérence métriques finales."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # Cohérence
        assert metrics.min_unique <= metrics.max_unique
        assert metrics.equity_gap == metrics.max_unique - metrics.min_unique
        assert 0 <= metrics.mean_unique <= 30
        assert metrics.total_unique_pairs >= 0
        assert metrics.total_repeat_pairs >= 0

    def test_multiple_sizes_all_pass(self) -> None:
        """Test plusieurs tailles d'événements."""
        test_configs = [
            PlanningConfig(N=12, X=3, x=4, S=3),
            PlanningConfig(N=30, X=5, x=6, S=6),
            PlanningConfig(N=50, X=10, x=5, S=8),
        ]

        for config in test_configs:
            planning, metrics = generate_optimized_planning(config, seed=42)

            # Vérifications communes
            assert len(planning.sessions) == config.S
            assert metrics.equity_gap <= 1  # FR6
            assert len(metrics.unique_meetings_per_person) == config.N
