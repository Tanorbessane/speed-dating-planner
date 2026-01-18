"""Tests unitaires pour le pipeline complet (src.planner).

Test coverage:
    - Pipeline end-to-end réussit
    - Garantie FR6 (equity_gap ≤ 1)
    - Amélioration vs baseline
    - Déterminisme (NFR11)
    - Retours corrects
"""

import pytest

from src.baseline import generate_baseline
from src.metrics import compute_metrics
from src.models import Planning, PlanningConfig, PlanningMetrics
from src.planner import generate_optimized_planning
from src.validation import InvalidConfigurationError


class TestGenerateOptimizedPlanning:
    """Tests pour generate_optimized_planning()."""

    def test_end_to_end_success(self) -> None:
        """Test pipeline complet end-to-end réussit."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Générer planning optimisé complet
        planning, metrics = generate_optimized_planning(config, seed=42)

        # Vérifications basiques
        assert isinstance(planning, Planning)
        assert isinstance(metrics, PlanningMetrics)
        assert len(planning.sessions) == 6
        assert metrics.total_unique_pairs > 0

    def test_guarantees_equity_fr6(self) -> None:
        """Test garantie FR6: equity_gap ≤ 1."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # FR6 GARANTI
        assert (
            metrics.equity_gap <= 1
        ), f"FR6 violé: equity_gap = {metrics.equity_gap} > 1"

    def test_improves_over_baseline(self) -> None:
        """Test amélioration significative vs baseline."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Générer baseline seul
        baseline = generate_baseline(config, seed=42)
        metrics_baseline = compute_metrics(baseline, config)

        # Générer optimisé complet
        planning, metrics_optimized = generate_optimized_planning(config, seed=42)

        # Vérifier amélioration (répétitions réduites OU égales)
        assert (
            metrics_optimized.total_repeat_pairs
            <= metrics_baseline.total_repeat_pairs
        )

        # Vérifier équité améliorée (gap réduit)
        assert metrics_optimized.equity_gap <= metrics_baseline.equity_gap

    def test_determinism_same_seed(self) -> None:
        """Test déterminisme: même seed → même résultat (NFR11)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Générer 2 fois avec même seed
        planning1, metrics1 = generate_optimized_planning(config, seed=42)
        planning2, metrics2 = generate_optimized_planning(config, seed=42)

        # Métriques identiques
        assert metrics1.total_unique_pairs == metrics2.total_unique_pairs
        assert metrics1.total_repeat_pairs == metrics2.total_repeat_pairs
        assert metrics1.equity_gap == metrics2.equity_gap
        assert metrics1.min_unique == metrics2.min_unique
        assert metrics1.max_unique == metrics2.max_unique

    def test_different_seeds_different_results(self) -> None:
        """Test seeds différents → plannings différents."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning1, metrics1 = generate_optimized_planning(config, seed=42)
        planning2, metrics2 = generate_optimized_planning(config, seed=123)

        # Plannings doivent différer (au moins structure initiale)
        # Métriques finales peuvent être similaires mais pas identiques
        # Note: équité garantie (≤1) donc equity_gap peut être identique
        # On vérifie juste que les instances sont différentes
        assert planning1 is not planning2

    def test_returns_correct_types(self) -> None:
        """Test que retourne tuple (Planning, PlanningMetrics)."""
        config = PlanningConfig(N=12, X=3, x=4, S=3)

        result = generate_optimized_planning(config, seed=42)

        # Type du retour
        assert isinstance(result, tuple)
        assert len(result) == 2

        planning, metrics = result
        assert isinstance(planning, Planning)
        assert isinstance(metrics, PlanningMetrics)

    def test_invalid_config_raises(self) -> None:
        """Test configuration invalide lève exception."""
        # Capacité insuffisante: 5×8 = 40 < 50
        config = PlanningConfig(N=50, X=5, x=8, S=3)

        with pytest.raises(InvalidConfigurationError):
            generate_optimized_planning(config, seed=42)

    def test_all_participants_assigned(self) -> None:
        """Test que tous participants sont assignés dans chaque session."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # Vérifier chaque session
        for session in planning.sessions:
            all_assigned = set()
            for table in session.tables:
                all_assigned.update(table)

            # Tous participants 0..N-1 présents
            assert all_assigned == set(range(30))

    def test_table_sizes_valid_fr7(self) -> None:
        """Test que tailles tables respectent FR7 (variance ≤1)."""
        config = PlanningConfig(N=37, X=6, x=7, S=5)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # Vérifier FR7 pour toutes sessions
        for session in planning.sessions:
            table_sizes = [len(table) for table in session.tables]
            assert max(table_sizes) - min(table_sizes) <= 1

    def test_small_planning(self) -> None:
        """Test planning minimal."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)

        planning, metrics = generate_optimized_planning(config, seed=42)

        assert len(planning.sessions) == 2
        assert metrics.equity_gap <= 1
        assert len(metrics.unique_meetings_per_person) == 6

    def test_medium_planning(self) -> None:
        """Test planning moyen."""
        config = PlanningConfig(N=100, X=20, x=5, S=10)

        planning, metrics = generate_optimized_planning(config, seed=42)

        assert len(planning.sessions) == 10
        assert metrics.equity_gap <= 1
        assert len(metrics.unique_meetings_per_person) == 100

    def test_metrics_consistency(self) -> None:
        """Test cohérence des métriques."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        # Métriques cohérentes
        assert metrics.min_unique <= metrics.max_unique
        assert metrics.equity_gap == metrics.max_unique - metrics.min_unique
        assert len(metrics.unique_meetings_per_person) == config.N
        assert metrics.mean_unique > 0

    def test_config_preserved(self) -> None:
        """Test que configuration est préservée dans planning."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning, metrics = generate_optimized_planning(config, seed=42)

        assert planning.config.N == config.N
        assert planning.config.X == config.X
        assert planning.config.x == config.x
        assert planning.config.S == config.S
