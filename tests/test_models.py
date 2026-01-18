"""Tests unitaires pour les structures de données (src.models).

Ce module teste les dataclasses PlanningConfig, Session, Planning et PlanningMetrics.

Test coverage:
    - Création et validation des structures
    - Properties calculées
    - Validation des types et valeurs
    - Immutabilité (frozen dataclass)
"""

import pytest

from src.models import Planning, PlanningConfig, PlanningMetrics, Session


class TestPlanningConfig:
    """Tests pour la dataclass PlanningConfig."""

    def test_creation_valid(self) -> None:
        """Test création configuration valide."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        assert config.N == 30
        assert config.X == 5
        assert config.x == 6
        assert config.S == 6

    def test_total_capacity(self) -> None:
        """Test calcul capacité totale (X × x)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        assert config.total_capacity == 30

        config2 = PlanningConfig(N=100, X=20, x=5, S=10)
        assert config2.total_capacity == 100

    def test_frozen_immutability(self) -> None:
        """Test immutabilité (frozen=True)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            config.N = 50  # type: ignore

    def test_invalid_types(self) -> None:
        """Test validation types invalides."""
        with pytest.raises(TypeError):
            PlanningConfig(N="30", X=5, x=6, S=6)  # type: ignore

        with pytest.raises(TypeError):
            PlanningConfig(N=30, X=5.5, x=6, S=6)  # type: ignore

    def test_negative_values(self) -> None:
        """Test validation valeurs négatives."""
        with pytest.raises(TypeError):
            PlanningConfig(N=-30, X=5, x=6, S=6)

        with pytest.raises(TypeError):
            PlanningConfig(N=30, X=-5, x=6, S=6)

    def test_zero_values(self) -> None:
        """Test valeurs à zéro (validation métier dans validation.py)."""
        # N=0 devrait être rejeté par validation.py, mais models.py accepte
        config = PlanningConfig(N=0, X=0, x=0, S=0)
        assert config.N == 0
        assert config.total_capacity == 0


class TestSession:
    """Tests pour la dataclass Session."""

    def test_creation_valid(self) -> None:
        """Test création session valide."""
        session = Session(session_id=0, tables=[{0, 1, 2}, {3, 4, 5}])

        assert session.session_id == 0
        assert len(session.tables) == 2
        assert {0, 1, 2} in session.tables
        assert {3, 4, 5} in session.tables

    def test_total_participants(self) -> None:
        """Test calcul nombre total participants."""
        session = Session(0, [{0, 1, 2}, {3, 4}])
        assert session.total_participants == 5

        session_empty = Session(0, [])
        assert session_empty.total_participants == 0

    def test_creation_default_tables(self) -> None:
        """Test création session avec tables par défaut (liste vide)."""
        session = Session(session_id=5)
        assert session.session_id == 5
        assert session.tables == []
        assert session.total_participants == 0

    def test_invalid_session_id(self) -> None:
        """Test validation session_id invalide."""
        with pytest.raises(TypeError):
            Session(session_id=-1, tables=[])

        with pytest.raises(TypeError):
            Session(session_id="0", tables=[])  # type: ignore

    def test_invalid_tables_type(self) -> None:
        """Test validation type tables invalide."""
        with pytest.raises(TypeError):
            Session(session_id=0, tables={0, 1, 2})  # type: ignore


class TestPlanning:
    """Tests pour la dataclass Planning."""

    def test_creation_valid(self) -> None:
        """Test création planning valide."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        assert len(planning.sessions) == 2
        assert planning.config.N == 6
        assert planning.sessions[0].session_id == 0
        assert planning.sessions[1].session_id == 1

    def test_invalid_sessions_type(self) -> None:
        """Test validation type sessions invalide."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)

        with pytest.raises(TypeError):
            Planning(sessions="invalid", config=config)  # type: ignore

    def test_invalid_config_type(self) -> None:
        """Test validation type config invalide."""
        sessions = [Session(0, [{0, 1, 2}])]

        with pytest.raises(TypeError):
            Planning(sessions=sessions, config="invalid")  # type: ignore


class TestPlanningMetrics:
    """Tests pour la dataclass PlanningMetrics."""

    def test_creation_valid(self) -> None:
        """Test création métriques valides."""
        metrics = PlanningMetrics(
            total_unique_pairs=145,
            total_repeat_pairs=7,
            unique_meetings_per_person=[10, 11, 10, 11, 10, 10],
            min_unique=10,
            max_unique=11,
            mean_unique=10.33,
        )

        assert metrics.total_unique_pairs == 145
        assert metrics.total_repeat_pairs == 7
        assert metrics.min_unique == 10
        assert metrics.max_unique == 11
        assert metrics.mean_unique == pytest.approx(10.33, rel=0.01)

    def test_equity_gap_property(self) -> None:
        """Test calcul equity_gap (max - min)."""
        metrics = PlanningMetrics(
            total_unique_pairs=100,
            total_repeat_pairs=5,
            unique_meetings_per_person=[10, 11, 10],
            min_unique=10,
            max_unique=11,
            mean_unique=10.33,
        )
        assert metrics.equity_gap == 1

        metrics_perfect = PlanningMetrics(
            total_unique_pairs=100,
            total_repeat_pairs=0,
            unique_meetings_per_person=[10, 10, 10],
            min_unique=10,
            max_unique=10,
            mean_unique=10.0,
        )
        assert metrics_perfect.equity_gap == 0

    def test_invalid_total_unique_pairs(self) -> None:
        """Test validation total_unique_pairs négatif."""
        with pytest.raises(ValueError, match="total_unique_pairs"):
            PlanningMetrics(
                total_unique_pairs=-1,
                total_repeat_pairs=0,
                unique_meetings_per_person=[10],
                min_unique=10,
                max_unique=10,
                mean_unique=10.0,
            )

    def test_invalid_total_repeat_pairs(self) -> None:
        """Test validation total_repeat_pairs négatif."""
        with pytest.raises(ValueError, match="total_repeat_pairs"):
            PlanningMetrics(
                total_unique_pairs=100,
                total_repeat_pairs=-5,
                unique_meetings_per_person=[10],
                min_unique=10,
                max_unique=10,
                mean_unique=10.0,
            )

    def test_invalid_min_unique(self) -> None:
        """Test validation min_unique négatif."""
        with pytest.raises(ValueError, match="min_unique"):
            PlanningMetrics(
                total_unique_pairs=100,
                total_repeat_pairs=0,
                unique_meetings_per_person=[10],
                min_unique=-1,
                max_unique=10,
                mean_unique=10.0,
            )

    def test_invalid_max_min_relationship(self) -> None:
        """Test validation max_unique < min_unique."""
        with pytest.raises(ValueError, match="max_unique.*min_unique"):
            PlanningMetrics(
                total_unique_pairs=100,
                total_repeat_pairs=0,
                unique_meetings_per_person=[10],
                min_unique=15,
                max_unique=10,  # max < min
                mean_unique=10.0,
            )

    def test_zero_metrics(self) -> None:
        """Test métriques avec valeurs à zéro."""
        metrics = PlanningMetrics(
            total_unique_pairs=0,
            total_repeat_pairs=0,
            unique_meetings_per_person=[0, 0, 0],
            min_unique=0,
            max_unique=0,
            mean_unique=0.0,
        )
        assert metrics.equity_gap == 0
        assert metrics.total_unique_pairs == 0
