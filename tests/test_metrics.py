"""Tests unitaires pour le calcul de métriques (src.metrics).

Test coverage:
    - Calcul correct toutes métriques
    - Integration avec meeting_history
    - Edge cases (plannings vides, répétitions)
"""

import pytest

from src.metrics import compute_metrics
from src.models import Planning, PlanningConfig, Session


class TestComputeMetrics:
    """Tests pour compute_metrics()."""

    def test_simple_planning_no_repeats(self) -> None:
        """Test métriques planning sans répétitions."""
        config = PlanningConfig(N=4, X=2, x=2, S=2)
        sessions = [
            Session(0, [{0, 1}, {2, 3}]),
            Session(1, [{0, 2}, {1, 3}]),
        ]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # 4 paires uniques: (0,1), (2,3), (0,2), (1,3)
        assert metrics.total_unique_pairs == 4
        assert metrics.total_repeat_pairs == 0

        # Chaque participant rencontre 2 autres (équitable)
        assert metrics.min_unique == 2
        assert metrics.max_unique == 2
        assert metrics.equity_gap == 0
        assert metrics.mean_unique == 2.0

    def test_planning_with_repeats(self) -> None:
        """Test métriques planning avec répétitions."""
        config = PlanningConfig(N=4, X=2, x=2, S=2)
        sessions = [
            Session(0, [{0, 1}, {2, 3}]),
            Session(1, [{0, 1}, {2, 3}]),  # Même composition → répétitions
        ]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # 2 paires uniques: (0,1), (2,3)
        assert metrics.total_unique_pairs == 2
        # Les 2 paires se répètent
        assert metrics.total_repeat_pairs == 2

        # Chaque participant rencontre 1 autre unique
        assert metrics.min_unique == 1
        assert metrics.max_unique == 1
        assert metrics.equity_gap == 0

    def test_inequitable_planning(self) -> None:
        """Test métriques planning inéquitable (equity_gap > 1)."""
        config = PlanningConfig(N=5, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4}]),
            Session(1, [{0, 1, 2}, {3, 4}]),
        ]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # Participant 0, 1, 2: rencontrent 2 autres chacun
        # Participant 3, 4: rencontrent 1 autre chacun
        assert metrics.min_unique == 1  # Participants 3,4
        assert metrics.max_unique == 2  # Participants 0,1,2
        assert metrics.equity_gap == 1

    def test_empty_planning(self) -> None:
        """Test métriques planning vide."""
        config = PlanningConfig(N=6, X=2, x=3, S=0)
        planning = Planning(sessions=[], config=config)

        metrics = compute_metrics(planning, config)

        assert metrics.total_unique_pairs == 0
        assert metrics.total_repeat_pairs == 0
        assert metrics.min_unique == 0
        assert metrics.max_unique == 0
        assert metrics.equity_gap == 0
        assert metrics.mean_unique == 0.0

    def test_single_session(self) -> None:
        """Test métriques avec 1 seule session."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # 2 tables × 3 paires par table = 6 paires
        assert metrics.total_unique_pairs == 6
        assert metrics.total_repeat_pairs == 0  # Pas de répétition possible

        # Chaque participant rencontre 2 autres
        assert all(count == 2 for count in metrics.unique_meetings_per_person)
        assert metrics.equity_gap == 0

    def test_large_table_many_pairs(self) -> None:
        """Test table avec beaucoup de participants."""
        config = PlanningConfig(N=10, X=1, x=10, S=1)
        sessions = [Session(0, [set(range(10))])]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # 10 participants → 10×9/2 = 45 paires
        expected_pairs = 10 * 9 // 2
        assert metrics.total_unique_pairs == expected_pairs
        assert metrics.total_repeat_pairs == 0

        # Chaque participant rencontre 9 autres
        assert all(count == 9 for count in metrics.unique_meetings_per_person)
        assert metrics.min_unique == 9
        assert metrics.max_unique == 9
        assert metrics.equity_gap == 0

    def test_unique_meetings_per_person_length(self) -> None:
        """Test que liste rencontres a taille N."""
        config = PlanningConfig(N=30, X=5, x=6, S=3)
        sessions = [
            Session(0, [{i, i + 1, i + 2, i + 3, i + 4, i + 5} for i in range(0, 30, 6)])
        ] * 3
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        assert len(metrics.unique_meetings_per_person) == 30

    def test_mean_unique_calculation(self) -> None:
        """Test calcul moyenne rencontres uniques."""
        config = PlanningConfig(N=4, X=2, x=2, S=2)
        sessions = [
            Session(0, [{0, 1}, {2, 3}]),
            Session(1, [{0, 2}, {1, 3}]),
        ]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # Chaque participant: 2 rencontres
        # Moyenne: (2+2+2+2)/4 = 2.0
        assert metrics.mean_unique == pytest.approx(2.0)

    def test_repeat_pairs_count(self) -> None:
        """Test comptage précis répétitions."""
        config = PlanningConfig(N=3, X=1, x=3, S=3)
        sessions = [
            Session(0, [{0, 1, 2}]),
            Session(1, [{0, 1, 2}]),
            Session(2, [{0, 1, 2}]),
        ]
        planning = Planning(sessions, config)

        metrics = compute_metrics(planning, config)

        # 3 paires uniques: (0,1), (0,2), (1,2)
        assert metrics.total_unique_pairs == 3
        # Toutes les paires se répètent (3 fois chacune)
        assert metrics.total_repeat_pairs == 3
