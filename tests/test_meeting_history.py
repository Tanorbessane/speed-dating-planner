"""Tests unitaires pour l'historique des rencontres (src.meeting_history).

Ce module teste le calcul de l'historique des paires de participants
s'étant rencontrées.

Test coverage:
    - Calcul correct des paires
    - Normalisation (p1, p2) avec p1 < p2
    - Complexité O(S × X × x²)
"""

import pytest

from src.meeting_history import compute_meeting_history
from src.models import Planning, PlanningConfig, Session


class TestComputeMeetingHistory:
    """Tests pour compute_meeting_history()."""

    def test_simple_planning_two_sessions(self) -> None:
        """Test calcul historique planning simple (2 sessions)."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # Session 0, table 0: (0,1), (0,2), (1,2)
        assert (0, 1) in history
        assert (0, 2) in history
        assert (1, 2) in history

        # Session 0, table 1: (3,4), (3,5), (4,5)
        assert (3, 4) in history
        assert (3, 5) in history
        assert (4, 5) in history

        # Session 1, table 0: (0,3), (0,4), (3,4)
        assert (0, 3) in history
        assert (0, 4) in history
        # (3,4) already in history from session 0

        # Session 1, table 1: (1,2), (1,5), (2,5)
        # (1,2) already in history from session 0
        assert (1, 5) in history
        assert (2, 5) in history

    def test_pair_normalization(self) -> None:
        """Test que les paires sont normalisées (min, max)."""
        config = PlanningConfig(N=4, X=1, x=4, S=1)
        sessions = [Session(0, [{0, 1, 2, 3}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # Vérifier normalisation: toujours p1 < p2
        for p1, p2 in history:
            assert p1 < p2

        # Vérifier présence paires
        assert (0, 1) in history
        assert (0, 2) in history
        assert (0, 3) in history
        assert (1, 2) in history
        assert (1, 3) in history
        assert (2, 3) in history

        # Pas de doublons inversés
        assert (1, 0) not in history
        assert (2, 0) not in history

    def test_no_duplicates_across_sessions(self) -> None:
        """Test que répétitions de paires ne créent pas doublons."""
        config = PlanningConfig(N=4, X=2, x=2, S=2)
        sessions = [
            Session(0, [{0, 1}, {2, 3}]),
            Session(1, [{0, 1}, {2, 3}]),  # Même composition
        ]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # Même si (0,1) apparaît 2 fois, set ne contient qu'une occurrence
        assert (0, 1) in history
        assert (2, 3) in history
        assert len(history) == 2

    def test_empty_planning(self) -> None:
        """Test planning vide (0 sessions)."""
        config = PlanningConfig(N=6, X=2, x=3, S=0)
        planning = Planning(sessions=[], config=config)

        history = compute_meeting_history(planning)

        assert len(history) == 0
        assert history == set()

    def test_single_session_single_table(self) -> None:
        """Test cas minimal: 1 session, 1 table."""
        config = PlanningConfig(N=3, X=1, x=3, S=1)
        sessions = [Session(0, [{0, 1, 2}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # 3 participants → 3 paires
        assert len(history) == 3
        assert (0, 1) in history
        assert (0, 2) in history
        assert (1, 2) in history

    def test_single_participant_pair(self) -> None:
        """Test table avec 2 participants (taille minimale)."""
        config = PlanningConfig(N=2, X=1, x=2, S=1)
        sessions = [Session(0, [{0, 1}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        assert len(history) == 1
        assert (0, 1) in history

    def test_multiple_tables_per_session(self) -> None:
        """Test sessions avec plusieurs tables."""
        config = PlanningConfig(N=9, X=3, x=3, S=1)
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}, {6, 7, 8}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # 3 tables × 3 paires par table = 9 paires
        assert len(history) == 9

        # Vérifier qu'aucune paire cross-table n'existe
        assert (0, 3) not in history
        assert (1, 4) not in history
        assert (2, 8) not in history

        # Vérifier paires intra-table
        assert (0, 1) in history
        assert (3, 4) in history
        assert (6, 7) in history

    def test_variable_table_sizes(self) -> None:
        """Test tables de tailles variables (FR7: gestion remainder)."""
        config = PlanningConfig(N=7, X=3, x=3, S=1)
        # 7 participants, 3 tables → tailles [3, 2, 2]
        sessions = [Session(0, [{0, 1, 2}, {3, 4}, {5, 6}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # Table 0 (3 participants): 3 paires
        # Table 1 (2 participants): 1 paire
        # Table 2 (2 participants): 1 paire
        # Total: 5 paires
        assert len(history) == 5

        assert (0, 1) in history
        assert (0, 2) in history
        assert (1, 2) in history
        assert (3, 4) in history
        assert (5, 6) in history

    def test_large_table(self) -> None:
        """Test table avec beaucoup de participants."""
        config = PlanningConfig(N=10, X=1, x=10, S=1)
        sessions = [Session(0, [set(range(10))])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # 10 participants → 10×9/2 = 45 paires
        expected_pairs = 10 * 9 // 2
        assert len(history) == expected_pairs

    def test_no_cross_session_pairs(self) -> None:
        """Test que seules paires intra-table sont comptées."""
        config = PlanningConfig(N=4, X=2, x=2, S=2)
        sessions = [
            Session(0, [{0, 1}, {2, 3}]),
            Session(1, [{0, 2}, {1, 3}]),
        ]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        # Session 0: (0,1), (2,3)
        # Session 1: (0,2), (1,3)
        # Total: 4 paires uniques
        assert len(history) == 4
        assert (0, 1) in history
        assert (2, 3) in history
        assert (0, 2) in history
        assert (1, 3) in history

        # Pas de paires qui n'ont jamais été ensemble
        assert (0, 3) not in history
        assert (1, 2) not in history

    def test_return_type_is_set(self) -> None:
        """Test que le retour est bien un Set."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        assert isinstance(history, set)

    def test_tuple_elements_are_ints(self) -> None:
        """Test que les éléments des tuples sont des entiers."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        history = compute_meeting_history(planning)

        for p1, p2 in history:
            assert isinstance(p1, int)
            assert isinstance(p2, int)
