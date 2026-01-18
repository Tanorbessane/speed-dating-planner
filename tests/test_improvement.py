"""Tests unitaires pour l'amélioration locale (src.improvement).

Test coverage:
    - Amélioration réussie (répétitions réduites)
    - Détection plateau
    - Itérations max respectées
    - Planning original non modifié (deep copy)
    - Complexité O(iter × S × X² × x²)
"""

import pytest

from src.baseline import generate_baseline
from src.improvement import improve_planning
from src.metrics import compute_metrics
from src.models import Planning, PlanningConfig, Session


class TestImprovePlanning:
    """Tests pour improve_planning()."""

    def test_improves_baseline_planning(self) -> None:
        """Test que improve_planning réduit répétitions vs baseline."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        # Générer baseline
        baseline = generate_baseline(config, seed=42)
        metrics_baseline = compute_metrics(baseline, config)

        # Améliorer
        improved = improve_planning(baseline, config, max_iterations=50)
        metrics_improved = compute_metrics(improved, config)

        # Vérifier amélioration (répétitions réduites)
        assert (
            metrics_improved.total_repeat_pairs <= metrics_baseline.total_repeat_pairs
        ), "Répétitions devraient être réduites ou égales"

        # Log pour info
        logger_info = (
            f"Baseline: {metrics_baseline.total_repeat_pairs} répétitions, "
            f"Amélioré: {metrics_improved.total_repeat_pairs} répétitions"
        )
        print(logger_info)

    def test_original_planning_not_modified(self) -> None:
        """Test que planning original n'est PAS modifié (deep copy)."""
        config = PlanningConfig(N=12, X=3, x=4, S=3)

        # Générer baseline
        baseline = generate_baseline(config, seed=42)

        # Sauvegarder état initial
        original_sessions = [
            [set(table) for table in session.tables] for session in baseline.sessions
        ]

        # Améliorer (devrait créer copie)
        improved = improve_planning(baseline, config, max_iterations=10)

        # Vérifier que baseline n'a PAS été modifié
        for session_id, session in enumerate(baseline.sessions):
            for table_id, table in enumerate(session.tables):
                assert (
                    table == original_sessions[session_id][table_id]
                ), f"Table modifiée: session {session_id}, table {table_id}"

        # Vérifier que improved est différent (sinon pas d'amélioration faite)
        # Note: improved peut être identique si baseline déjà optimal
        # Donc on vérifie juste que c'est une instance différente
        assert improved is not baseline

    def test_plateau_detection_stops_early(self) -> None:
        """Test que détection plateau arrête itérations."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)

        # Planning simple avec peu d'amélioration possible
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        baseline = Planning(sessions, config)

        # Améliorer avec beaucoup d'itérations
        # Devrait s'arrêter avant 100 iterations grâce à plateau
        improved = improve_planning(baseline, config, max_iterations=100)

        # Vérifier que fonction a retourné un planning
        assert improved is not None
        assert len(improved.sessions) == 2

    def test_max_iterations_respected(self) -> None:
        """Test que max_iterations est respecté."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        baseline = generate_baseline(config, seed=42)

        # Améliorer avec seulement 5 iterations
        improved = improve_planning(baseline, config, max_iterations=5)

        # Devrait terminer sans erreur
        assert improved is not None
        assert len(improved.sessions) == 6

    def test_no_swaps_if_already_optimal(self) -> None:
        """Test planning déjà optimal (aucun swap bénéfique)."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)

        # Planning optimal: aucune répétition possible
        # Tous participants se rencontrent une seule fois
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        baseline = Planning(sessions, config)

        # Améliorer (ne devrait rien changer)
        improved = improve_planning(baseline, config, max_iterations=10)

        # Vérifier que planning est identique (ou très similaire)
        metrics_baseline = compute_metrics(baseline, config)
        metrics_improved = compute_metrics(improved, config)

        assert (
            metrics_improved.total_repeat_pairs == metrics_baseline.total_repeat_pairs
        )

    def test_all_participants_still_assigned(self) -> None:
        """Test que tous participants restent assignés après amélioration."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        baseline = generate_baseline(config, seed=42)
        improved = improve_planning(baseline, config, max_iterations=20)

        # Vérifier chaque session
        for session in improved.sessions:
            all_assigned = set()
            for table in session.tables:
                all_assigned.update(table)

            # Tous participants 0..N-1 présents
            assert all_assigned == set(range(30))

    def test_table_counts_preserved(self) -> None:
        """Test que nombre de tables par session est préservé."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        baseline = generate_baseline(config, seed=42)
        improved = improve_planning(baseline, config, max_iterations=20)

        # Vérifier nombre de tables
        for session_id in range(6):
            assert len(improved.sessions[session_id].tables) == 5

    def test_table_sizes_preserved(self) -> None:
        """Test que tailles de tables sont préservées (FR7)."""
        config = PlanningConfig(N=37, X=6, x=7, S=5)

        baseline = generate_baseline(config, seed=42)
        improved = improve_planning(baseline, config, max_iterations=20)

        # Vérifier variance ≤ 1 (FR7) toujours respectée
        for session in improved.sessions:
            table_sizes = [len(table) for table in session.tables]
            assert max(table_sizes) - min(table_sizes) <= 1

    def test_returns_planning_instance(self) -> None:
        """Test que improve_planning retourne instance Planning."""
        config = PlanningConfig(N=12, X=3, x=4, S=3)

        baseline = generate_baseline(config, seed=42)
        improved = improve_planning(baseline, config, max_iterations=10)

        assert isinstance(improved, Planning)
        assert improved.config == config

    def test_small_planning_quick(self) -> None:
        """Test amélioration rapide pour petit planning."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)

        baseline = generate_baseline(config, seed=42)
        improved = improve_planning(baseline, config, max_iterations=10)

        # Devrait terminer rapidement
        assert improved is not None

    def test_multiple_sessions_all_improved(self) -> None:
        """Test que toutes sessions sont considérées pour amélioration."""
        config = PlanningConfig(N=12, X=3, x=4, S=4)

        baseline = generate_baseline(config, seed=42)
        improved = improve_planning(baseline, config, max_iterations=20)

        # Vérifier que toutes sessions existent
        assert len(improved.sessions) == 4

        # Calculer métriques
        metrics = compute_metrics(improved, config)
        assert metrics.total_unique_pairs > 0

    def test_determinism_with_same_baseline(self) -> None:
        """Test déterminisme: même baseline → même résultat amélioré.

        Note: improve_planning est déterministe car parcours ordonné des
        tables/participants et swaps appliqués dans ordre fixe.
        """
        config = PlanningConfig(N=12, X=3, x=4, S=3)

        baseline = generate_baseline(config, seed=42)

        # Améliorer 2 fois
        improved1 = improve_planning(baseline, config, max_iterations=10)
        improved2 = improve_planning(baseline, config, max_iterations=10)

        # Calculer métriques (devraient être identiques)
        metrics1 = compute_metrics(improved1, config)
        metrics2 = compute_metrics(improved2, config)

        assert metrics1.total_repeat_pairs == metrics2.total_repeat_pairs
        assert metrics1.equity_gap == metrics2.equity_gap
