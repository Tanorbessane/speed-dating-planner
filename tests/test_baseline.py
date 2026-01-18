"""Tests unitaires pour l'algorithme baseline (src.baseline).

Ce module teste la génération de planning baseline avec rotation round-robin.

Test coverage:
    - Génération réussie pour configs valides
    - Déterminisme avec seed (NFR11)
    - Gestion tables partielles (FR7)
    - Tests de performance (NFR1: N=100 <1s)
"""

import time

import pytest

from src.baseline import generate_baseline
from src.models import PlanningConfig
from src.validation import InvalidConfigurationError


class TestGenerateBaseline:
    """Tests pour generate_baseline()."""

    def test_generation_success_small(self) -> None:
        """Test génération réussie (petit événement)."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)

        assert len(planning.sessions) == 2
        assert planning.config == config

        # Vérifier session 0
        session0 = planning.sessions[0]
        assert session0.session_id == 0
        assert len(session0.tables) == 2
        assert session0.total_participants == 6

        # Vérifier session 1
        session1 = planning.sessions[1]
        assert session1.session_id == 1
        assert len(session1.tables) == 2
        assert session1.total_participants == 6

    def test_generation_success_medium(self) -> None:
        """Test génération réussie (événement moyen)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        planning = generate_baseline(config, seed=42)

        assert len(planning.sessions) == 6
        assert planning.config.N == 30

        for session in planning.sessions:
            assert session.total_participants == 30
            assert len(session.tables) == 5

    def test_determinism_same_seed(self) -> None:
        """Test déterminisme: même seed → même planning (NFR11)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning1 = generate_baseline(config, seed=42)
        planning2 = generate_baseline(config, seed=42)

        # Vérifier que les plannings sont identiques
        assert len(planning1.sessions) == len(planning2.sessions)

        for s1, s2 in zip(planning1.sessions, planning2.sessions):
            assert s1.session_id == s2.session_id
            assert len(s1.tables) == len(s2.tables)
            for t1, t2 in zip(s1.tables, s2.tables):
                assert t1 == t2  # Sets égaux

    def test_determinism_different_seed(self) -> None:
        """Test seeds différents → plannings différents."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        planning1 = generate_baseline(config, seed=42)
        planning2 = generate_baseline(config, seed=123)

        # Plannings doivent avoir structure identique mais contenu différent
        assert len(planning1.sessions) == len(planning2.sessions)

        # Au moins une table doit être différente
        found_difference = False
        for s1, s2 in zip(planning1.sessions, planning2.sessions):
            for t1, t2 in zip(s1.tables, s2.tables):
                if t1 != t2:
                    found_difference = True
                    break

        assert found_difference, "Plannings avec seeds différents devraient différer"

    def test_partial_tables_handling(self) -> None:
        """Test gestion tables partielles (FR7: variance ≤1)."""
        # Config avec remainder: 37 / 6 = 6 rest 1
        # → 1 table de 7, 5 tables de 6
        config = PlanningConfig(N=37, X=6, x=7, S=3)
        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            table_sizes = [len(table) for table in session.tables]

            # Vérifier variance ≤ 1 (FR7)
            min_size = min(table_sizes)
            max_size = max(table_sizes)
            assert max_size - min_size <= 1, f"Variance > 1: {table_sizes}"

            # Vérifier total participants correct
            assert sum(table_sizes) == 37

    def test_partial_tables_exact_division(self) -> None:
        """Test division exacte (pas de remainder)."""
        config = PlanningConfig(N=30, X=5, x=6, S=3)
        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            table_sizes = [len(table) for table in session.tables]

            # Toutes tables doivent avoir exactement 6 participants
            assert all(size == 6 for size in table_sizes)
            assert sum(table_sizes) == 30

    def test_all_participants_assigned(self) -> None:
        """Test que tous participants sont assignés à chaque session."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            # Union de toutes les tables
            all_assigned = set()
            for table in session.tables:
                all_assigned.update(table)

            # Vérifier que tous participants 0..N-1 sont présents
            assert all_assigned == set(range(30))

    def test_participants_disjoint_within_session(self) -> None:
        """Test que les tables d'une session sont disjointes."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            # Vérifier intersection vide entre toutes paires de tables
            for i, table1 in enumerate(session.tables):
                for j, table2 in enumerate(session.tables):
                    if i != j:
                        assert (
                            table1.isdisjoint(table2)
                        ), f"Tables {i} et {j} se chevauchent"

    def test_invalid_config_raises(self) -> None:
        """Test configuration invalide lève exception."""
        # Capacité insuffisante: 5 × 8 = 40 < 50
        config = PlanningConfig(N=50, X=5, x=8, S=3)

        with pytest.raises(InvalidConfigurationError):
            generate_baseline(config, seed=42)

    def test_minimum_config(self) -> None:
        """Test configuration minimale (N=2, X=1, x=2, S=1)."""
        config = PlanningConfig(N=2, X=1, x=2, S=1)
        planning = generate_baseline(config, seed=42)

        assert len(planning.sessions) == 1
        assert len(planning.sessions[0].tables) == 1
        assert planning.sessions[0].tables[0] == {0, 1}

    def test_single_session(self) -> None:
        """Test génération avec 1 seule session."""
        config = PlanningConfig(N=30, X=5, x=6, S=1)
        planning = generate_baseline(config, seed=42)

        assert len(planning.sessions) == 1
        assert planning.sessions[0].total_participants == 30

    def test_many_sessions(self) -> None:
        """Test génération avec beaucoup de sessions."""
        config = PlanningConfig(N=30, X=5, x=6, S=20)
        planning = generate_baseline(config, seed=42)

        assert len(planning.sessions) == 20
        for session in planning.sessions:
            assert session.total_participants == 30

    @pytest.mark.slow
    def test_performance_n100_under_1s(self) -> None:
        """Test performance: N=100 doit générer en <1s (baseline rapide).

        Note: Ce test est marqué 'slow' et peut être exclu avec -m "not slow"
        """
        config = PlanningConfig(N=100, X=20, x=5, S=10)

        start = time.time()
        planning = generate_baseline(config, seed=42)
        duration = time.time() - start

        assert len(planning.sessions) == 10
        assert duration < 1.0, f"Génération trop lente: {duration:.3f}s"

    @pytest.mark.slow
    def test_performance_n300_fast(self) -> None:
        """Test performance: N=300 doit générer rapidement (<2s).

        Note: Baseline est O(N×S), donc très rapide même pour N=300
        """
        config = PlanningConfig(N=300, X=60, x=5, S=15)

        start = time.time()
        planning = generate_baseline(config, seed=42)
        duration = time.time() - start

        assert len(planning.sessions) == 15
        assert duration < 2.0, f"Génération trop lente: {duration:.3f}s"

    def test_rotation_stride_diversity(self) -> None:
        """Test que la rotation avec stride crée diversité."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)
        planning = generate_baseline(config, seed=42)

        # Vérifier que session 0 et session 1 ont compositions différentes
        session0_tables = [sorted(list(t)) for t in planning.sessions[0].tables]
        session1_tables = [sorted(list(t)) for t in planning.sessions[1].tables]

        # Au moins une table doit différer
        assert session0_tables != session1_tables

    def test_edge_case_n_equals_x_times_x(self) -> None:
        """Test cas limite: N = X × x (capacité exacte)."""
        config = PlanningConfig(N=25, X=5, x=5, S=5)
        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            assert session.total_participants == 25
            assert len(session.tables) == 5
            # Toutes tables pleines
            assert all(len(table) == 5 for table in session.tables)

    def test_edge_case_single_participant_per_table(self) -> None:
        """Test cas limite: x=2 (minimum pour rencontres)."""
        config = PlanningConfig(N=10, X=5, x=2, S=3)
        planning = generate_baseline(config, seed=42)

        for session in planning.sessions:
            assert session.total_participants == 10
            # Toutes tables ont 2 participants
            assert all(len(table) == 2 for table in session.tables)
