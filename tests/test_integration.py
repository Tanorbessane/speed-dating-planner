"""Tests d'intégration end-to-end pour Epic 1 (Baseline + Metrics).

Ce module teste le pipeline complet:
    1. Validation configuration
    2. Génération planning baseline
    3. Calcul métriques

Test coverage:
    - Pipeline complet réussi
    - Configuration invalide rejetée
    - Exemples réels (N=30, N=100)
    - Timing total
"""

import time

import pytest

from src.baseline import generate_baseline
from src.metrics import compute_metrics
from src.models import PlanningConfig
from src.validation import InvalidConfigurationError, validate_config


class TestIntegrationBaselinePipeline:
    """Tests d'intégration du pipeline baseline complet."""

    def test_end_to_end_success_small(self) -> None:
        """Test pipeline complet réussi (petit événement)."""
        # Configuration
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Étape 1: Validation
        validate_config(config)  # Ne doit pas lever exception

        # Étape 2: Génération baseline
        planning = generate_baseline(config, seed=42)

        # Vérifications planning
        assert len(planning.sessions) == 6
        assert planning.config == config

        for session in planning.sessions:
            assert session.total_participants == 30
            assert len(session.tables) == 5

        # Étape 3: Calcul métriques
        metrics = compute_metrics(planning, config)

        # Vérifications métriques
        assert metrics.total_unique_pairs > 0
        assert metrics.min_unique >= 0
        assert metrics.max_unique <= 30
        assert len(metrics.unique_meetings_per_person) == 30

    @pytest.mark.slow
    def test_end_to_end_timing_n100(self) -> None:
        """Test timing total pipeline N=100 (NFR1: <2s).

        Note: Baseline seul doit être <1s, pipeline complet <2s
        """
        config = PlanningConfig(N=100, X=20, x=5, S=10)

        start = time.time()

        # Pipeline complet
        validate_config(config)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        duration = time.time() - start

        # Vérifications
        assert len(planning.sessions) == 10
        assert metrics.total_unique_pairs > 0

        # Timing: pipeline baseline + metrics doit être rapide
        assert duration < 2.0, f"Pipeline trop lent: {duration:.3f}s"

    def test_invalid_config_rejected(self) -> None:
        """Test configuration invalide rejetée en amont."""
        # Capacité insuffisante: 5×8 = 40 < 50
        config = PlanningConfig(N=50, X=5, x=8, S=3)

        # Validation doit échouer
        with pytest.raises(InvalidConfigurationError):
            validate_config(config)

        # Génération baseline doit aussi échouer (validation interne)
        with pytest.raises(InvalidConfigurationError):
            generate_baseline(config, seed=42)

    def test_example_a_n30(self) -> None:
        """Test Exemple A du PRD: N=30, X=5, x=6, S=6."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Pipeline complet
        validate_config(config)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        # Vérifications conformité PRD
        assert len(planning.sessions) == 6
        assert all(len(s.tables) == 5 for s in planning.sessions)
        assert all(s.total_participants == 30 for s in planning.sessions)

        # Métriques attendues (baseline, pas encore optimisé)
        assert metrics.total_unique_pairs > 0
        assert len(metrics.unique_meetings_per_person) == 30

    @pytest.mark.slow
    def test_example_b_n100(self) -> None:
        """Test Exemple B du PRD: N=100, X=20, x=5, S=10."""
        config = PlanningConfig(N=100, X=20, x=5, S=10)

        start = time.time()

        # Pipeline complet
        validate_config(config)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        duration = time.time() - start

        # Vérifications
        assert len(planning.sessions) == 10
        assert all(len(s.tables) == 20 for s in planning.sessions)
        assert all(s.total_participants == 100 for s in planning.sessions)

        # Performance NFR1: N=100 <2s total
        assert duration < 2.0, f"Pipeline trop lent: {duration:.3f}s"

    def test_partial_tables_integration(self) -> None:
        """Test pipeline complet avec tables partielles (FR7)."""
        # 37 participants, 6 tables → 1 table de 7, 5 tables de 6
        config = PlanningConfig(N=37, X=6, x=7, S=5)

        # Pipeline complet
        validate_config(config)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        # Vérifications
        for session in planning.sessions:
            table_sizes = [len(table) for table in session.tables]
            # FR7: variance ≤ 1
            assert max(table_sizes) - min(table_sizes) <= 1
            assert sum(table_sizes) == 37

        assert len(metrics.unique_meetings_per_person) == 37

    def test_determinism_across_pipeline(self) -> None:
        """Test déterminisme complet du pipeline (NFR11)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Run 1
        planning1 = generate_baseline(config, seed=42)
        metrics1 = compute_metrics(planning1, config)

        # Run 2 (même seed)
        planning2 = generate_baseline(config, seed=42)
        metrics2 = compute_metrics(planning2, config)

        # Plannings identiques
        for s1, s2 in zip(planning1.sessions, planning2.sessions):
            assert s1.session_id == s2.session_id
            for t1, t2 in zip(s1.tables, s2.tables):
                assert t1 == t2

        # Métriques identiques
        assert metrics1.total_unique_pairs == metrics2.total_unique_pairs
        assert metrics1.total_repeat_pairs == metrics2.total_repeat_pairs
        assert metrics1.equity_gap == metrics2.equity_gap

    def test_minimum_viable_config(self) -> None:
        """Test configuration minimale viable (N=2, X=1, x=2, S=1)."""
        config = PlanningConfig(N=2, X=1, x=2, S=1)

        # Pipeline complet
        validate_config(config)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        # Vérifications
        assert len(planning.sessions) == 1
        assert len(planning.sessions[0].tables) == 1
        assert planning.sessions[0].tables[0] == {0, 1}

        # Métriques: 1 paire unique, pas de répétitions
        assert metrics.total_unique_pairs == 1
        assert metrics.total_repeat_pairs == 0
        assert metrics.equity_gap == 0  # Parfaitement équitable

    def test_large_event_n300(self) -> None:
        """Test grand événement N=300 (NFR2: <5s total)."""
        config = PlanningConfig(N=300, X=60, x=5, S=15)

        start = time.time()

        # Pipeline complet
        validate_config(config)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        duration = time.time() - start

        # Vérifications
        assert len(planning.sessions) == 15
        assert len(metrics.unique_meetings_per_person) == 300

        # Performance NFR2: N=300 <5s (baseline rapide, donc largement respecté)
        assert duration < 5.0, f"Pipeline trop lent: {duration:.3f}s"

    def test_all_participants_met_in_each_session(self) -> None:
        """Test intégration: tous participants assignés à chaque session."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            # Union toutes tables
            all_assigned = set()
            for table in session.tables:
                all_assigned.update(table)

            # Tous participants 0..N-1 présents
            assert all_assigned == set(range(30))

    def test_metrics_equity_gap_realistic(self) -> None:
        """Test que l'equity_gap du baseline est raisonnable."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        # Baseline n'optimise pas équité, mais ne devrait pas être catastrophique
        # (Epic 2 garantira equity_gap ≤ 1)
        assert metrics.equity_gap >= 0
        assert metrics.min_unique >= 0
        assert metrics.max_unique <= 30
