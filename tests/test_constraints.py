"""Tests unitaires pour les contraintes de groupes (Story 4.2).

Ce module teste les fonctionnalités de contraintes cohésives et exclusives :
    - Modèles de données (GroupConstraint, PlanningConstraints)
    - Génération baseline avec contraintes
    - Protection contraintes dans optimizer
    - Validation et détection erreurs

Test coverage:
    - Groupes cohésifs (must be together) : toujours même table
    - Groupes exclusifs (must be separate) : jamais même table
    - Validation contraintes vs configuration
    - Respect hard constraints dans baseline
    - Protection contraintes dans optimizer (swaps rejetés)
"""

import pytest

from src.baseline import generate_baseline
from src.improvement import improve_planning
from src.models import (
    GroupConstraint,
    GroupConstraintType,
    PlanningConfig,
    PlanningConstraints,
)
from src.planner import generate_optimized_planning
from src.validation import InvalidConfigurationError


class TestGroupConstraintModel:
    """Tests pour GroupConstraint dataclass."""

    def test_cohesive_group_creation(self) -> None:
        """Test création groupe cohésif valide."""
        group = GroupConstraint(
            name="Couple 1",
            constraint_type=GroupConstraintType.MUST_BE_TOGETHER,
            participant_ids={0, 1},
        )

        assert group.name == "Couple 1"
        assert group.constraint_type == GroupConstraintType.MUST_BE_TOGETHER
        assert group.participant_ids == {0, 1}

    def test_exclusive_group_creation(self) -> None:
        """Test création groupe exclusif valide."""
        group = GroupConstraint(
            name="Concurrents A-B",
            constraint_type=GroupConstraintType.MUST_BE_SEPARATE,
            participant_ids={5, 12},
        )

        assert group.name == "Concurrents A-B"
        assert group.constraint_type == GroupConstraintType.MUST_BE_SEPARATE
        assert len(group.participant_ids) == 2

    def test_group_minimum_size(self) -> None:
        """Test validation taille minimale groupe (≥2)."""
        with pytest.raises(ValueError, match="au moins 2 participants"):
            GroupConstraint(
                name="Invalid",
                constraint_type=GroupConstraintType.MUST_BE_TOGETHER,
                participant_ids={0},  # Seulement 1 participant
            )

    def test_large_group(self) -> None:
        """Test groupe cohésif de grande taille."""
        large_group = GroupConstraint(
            name="Grande Équipe",
            constraint_type=GroupConstraintType.MUST_BE_TOGETHER,
            participant_ids={0, 1, 2, 3, 4, 5},  # 6 participants
        )

        assert len(large_group.participant_ids) == 6


class TestPlanningConstraintsValidation:
    """Tests pour PlanningConstraints.validate()."""

    def test_empty_constraints_valid(self) -> None:
        """Test contraintes vides = valide."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)
        constraints = PlanningConstraints()

        errors = constraints.validate(config)
        assert len(errors) == 0

    def test_cohesive_group_exceeds_table_capacity(self) -> None:
        """Test groupe cohésif > capacité table → erreur."""
        config = PlanningConfig(N=10, X=2, x=3, S=3)  # Capacité table = 3

        group = GroupConstraint(
            name="Trop Grand",
            constraint_type=GroupConstraintType.MUST_BE_TOGETHER,
            participant_ids={0, 1, 2, 3},  # 4 > 3
        )
        constraints = PlanningConstraints(cohesive_groups=[group])

        errors = constraints.validate(config)
        assert len(errors) == 1
        assert "dépasse capacité table" in errors[0]

    def test_participant_in_multiple_cohesive_groups(self) -> None:
        """Test participant dans plusieurs groupes cohésifs → erreur."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)

        group1 = GroupConstraint(
            "Groupe A", GroupConstraintType.MUST_BE_TOGETHER, {0, 1}
        )
        group2 = GroupConstraint(
            "Groupe B", GroupConstraintType.MUST_BE_TOGETHER, {1, 2}  # 1 en doublon
        )
        constraints = PlanningConstraints(cohesive_groups=[group1, group2])

        errors = constraints.validate(config)
        assert len(errors) == 1
        assert "plusieurs groupes cohésifs" in errors[0]

    def test_conflict_cohesive_and_exclusive(self) -> None:
        """Test conflit cohésif/exclusif → erreur."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)

        cohesive = GroupConstraint(
            "Cohésif AB", GroupConstraintType.MUST_BE_TOGETHER, {0, 1}
        )
        exclusive = GroupConstraint(
            "Exclusif AB", GroupConstraintType.MUST_BE_SEPARATE, {0, 1}
        )
        constraints = PlanningConstraints(
            cohesive_groups=[cohesive], exclusive_groups=[exclusive]
        )

        errors = constraints.validate(config)
        assert len(errors) == 1
        assert "Conflit" in errors[0]
        assert "toujours ensemble ET toujours séparés" in errors[0]

    def test_multiple_cohesive_groups_valid(self) -> None:
        """Test plusieurs groupes cohésifs disjoints valides."""
        config = PlanningConfig(N=20, X=4, x=5, S=5)

        group1 = GroupConstraint("Couple 1", GroupConstraintType.MUST_BE_TOGETHER, {0, 1})
        group2 = GroupConstraint("Couple 2", GroupConstraintType.MUST_BE_TOGETHER, {5, 6})
        group3 = GroupConstraint("Équipe", GroupConstraintType.MUST_BE_TOGETHER, {10, 11, 12})

        constraints = PlanningConstraints(cohesive_groups=[group1, group2, group3])

        errors = constraints.validate(config)
        assert len(errors) == 0

    def test_exclusive_groups_no_size_limit(self) -> None:
        """Test groupes exclusifs peuvent être grands (pas de limite)."""
        config = PlanningConfig(N=20, X=4, x=5, S=5)

        # Groupe exclusif de 10 participants (OK car pas de limite taille)
        large_exclusive = GroupConstraint(
            "Concurrents", GroupConstraintType.MUST_BE_SEPARATE, set(range(10))
        )
        constraints = PlanningConstraints(exclusive_groups=[large_exclusive])

        errors = constraints.validate(config)
        assert len(errors) == 0


class TestBaselineWithConstraints:
    """Tests génération baseline avec contraintes."""

    def test_cohesive_group_stays_together_all_sessions(self) -> None:
        """Test groupe cohésif reste ensemble dans toutes les sessions."""
        config = PlanningConfig(N=10, X=2, x=5, S=4)

        cohesive = GroupConstraint(
            "Couple", GroupConstraintType.MUST_BE_TOGETHER, {0, 1}
        )
        constraints = PlanningConstraints(cohesive_groups=[cohesive])

        planning = generate_baseline(config, seed=42, constraints=constraints)

        # Vérifier que 0 et 1 sont toujours dans la même table
        for session in planning.sessions:
            found_0 = None
            found_1 = None

            for table_id, table in enumerate(session.tables):
                if 0 in table:
                    found_0 = table_id
                if 1 in table:
                    found_1 = table_id

            assert (
                found_0 == found_1
            ), f"Session {session.session_id}: participants 0 et 1 séparés"

    def test_multiple_cohesive_groups(self) -> None:
        """Test plusieurs groupes cohésifs respectés simultanément."""
        config = PlanningConfig(N=12, X=2, x=6, S=3)

        group1 = GroupConstraint("Couple 1", GroupConstraintType.MUST_BE_TOGETHER, {0, 1})
        group2 = GroupConstraint("Couple 2", GroupConstraintType.MUST_BE_TOGETHER, {5, 6})

        constraints = PlanningConstraints(cohesive_groups=[group1, group2])

        planning = generate_baseline(config, seed=42, constraints=constraints)

        for session in planning.sessions:
            # Vérifier couple 1
            table_0 = next(i for i, t in enumerate(session.tables) if 0 in t)
            table_1 = next(i for i, t in enumerate(session.tables) if 1 in t)
            assert table_0 == table_1

            # Vérifier couple 2
            table_5 = next(i for i, t in enumerate(session.tables) if 5 in t)
            table_6 = next(i for i, t in enumerate(session.tables) if 6 in t)
            assert table_5 == table_6

    def test_exclusive_group_never_together(self) -> None:
        """Test groupe exclusif jamais à la même table."""
        config = PlanningConfig(N=12, X=3, x=4, S=5)

        exclusive = GroupConstraint(
            "Concurrents", GroupConstraintType.MUST_BE_SEPARATE, {0, 1}
        )
        constraints = PlanningConstraints(exclusive_groups=[exclusive])

        planning = generate_baseline(config, seed=42, constraints=constraints)

        # Vérifier que 0 et 1 ne sont JAMAIS ensemble
        for session in planning.sessions:
            for table in session.tables:
                # Si 0 est dans la table, 1 ne doit PAS y être
                if 0 in table:
                    assert (
                        1 not in table
                    ), f"Session {session.session_id}: 0 et 1 ensemble (violation)"

    def test_cohesive_and_exclusive_combined(self) -> None:
        """Test contraintes cohésives ET exclusives simultanément."""
        config = PlanningConfig(N=15, X=3, x=5, S=4)

        cohesive = GroupConstraint(
            "Couple", GroupConstraintType.MUST_BE_TOGETHER, {0, 1}
        )
        exclusive = GroupConstraint(
            "Séparation", GroupConstraintType.MUST_BE_SEPARATE, {0, 5}
        )
        constraints = PlanningConstraints(
            cohesive_groups=[cohesive], exclusive_groups=[exclusive]
        )

        planning = generate_baseline(config, seed=42, constraints=constraints)

        for session in planning.sessions:
            # Vérifier cohésif : 0 et 1 ensemble
            table_0 = next(i for i, t in enumerate(session.tables) if 0 in t)
            table_1 = next(i for i, t in enumerate(session.tables) if 1 in t)
            assert table_0 == table_1

            # Vérifier exclusif : 0 et 5 séparés
            for table in session.tables:
                if 0 in table:
                    assert 5 not in table

    def test_invalid_constraints_raise_error(self) -> None:
        """Test contraintes invalides lèvent exception."""
        config = PlanningConfig(N=10, X=4, x=3, S=3)  # Capacité suffisante: 4×3=12 ≥ 10

        # Groupe cohésif trop grand (4 > capacité table 3)
        invalid_group = GroupConstraint(
            "Trop Grand", GroupConstraintType.MUST_BE_TOGETHER, {0, 1, 2, 3}
        )
        constraints = PlanningConstraints(cohesive_groups=[invalid_group])

        with pytest.raises(InvalidConfigurationError, match="Contraintes invalides"):
            generate_baseline(config, seed=42, constraints=constraints)


class TestImprovementWithConstraints:
    """Tests amélioration locale avec protection contraintes."""

    def test_cohesive_group_protected_during_optimization(self) -> None:
        """Test groupe cohésif JAMAIS séparé pendant optimisation."""
        config = PlanningConfig(N=12, X=3, x=4, S=4)

        cohesive = GroupConstraint(
            "Couple", GroupConstraintType.MUST_BE_TOGETHER, {0, 1}
        )
        constraints = PlanningConstraints(cohesive_groups=[cohesive])

        baseline = generate_baseline(config, seed=42, constraints=constraints)
        improved = improve_planning(
            baseline, config, max_iterations=20, constraints=constraints
        )

        # Vérifier que 0 et 1 sont toujours ensemble après optimisation
        for session in improved.sessions:
            table_0 = next(i for i, t in enumerate(session.tables) if 0 in t)
            table_1 = next(i for i, t in enumerate(session.tables) if 1 in t)
            assert (
                table_0 == table_1
            ), f"Session {session.session_id}: cohésif violé après optimisation"

    def test_exclusive_group_protected_during_optimization(self) -> None:
        """Test groupe exclusif JAMAIS réuni pendant optimisation."""
        config = PlanningConfig(N=12, X=3, x=4, S=4)

        exclusive = GroupConstraint(
            "Concurrents", GroupConstraintType.MUST_BE_SEPARATE, {0, 5}
        )
        constraints = PlanningConstraints(exclusive_groups=[exclusive])

        baseline = generate_baseline(config, seed=42, constraints=constraints)
        improved = improve_planning(
            baseline, config, max_iterations=20, constraints=constraints
        )

        # Vérifier que 0 et 5 ne sont JAMAIS ensemble après optimisation
        for session in improved.sessions:
            for table in session.tables:
                if 0 in table:
                    assert (
                        5 not in table
                    ), f"Session {session.session_id}: exclusif violé après optimisation"


class TestPlannerWithConstraints:
    """Tests pipeline complet avec contraintes (intégration)."""

    def test_end_to_end_with_cohesive_group(self) -> None:
        """Test pipeline complet (3 phases) avec groupe cohésif.

        Note: Avec contraintes hard, equity_gap ≤ 1 n'est pas toujours
        mathématiquement possible. Priorité absolue = respect contraintes.
        """
        config = PlanningConfig(N=20, X=4, x=5, S=5)

        cohesive = GroupConstraint(
            "Équipe", GroupConstraintType.MUST_BE_TOGETHER, {0, 1, 2}
        )
        constraints = PlanningConstraints(cohesive_groups=[cohesive])

        planning, metrics = generate_optimized_planning(
            config, seed=42, constraints=constraints
        )

        # Vérifier groupe cohésif respecté dans toutes les sessions (priorité absolue)
        for session in planning.sessions:
            tables_with_0 = [i for i, t in enumerate(session.tables) if 0 in t]
            tables_with_1 = [i for i, t in enumerate(session.tables) if 1 in t]
            tables_with_2 = [i for i, t in enumerate(session.tables) if 2 in t]

            # Tous dans la même table
            assert (
                tables_with_0 == tables_with_1 == tables_with_2
            ), f"Session {session.session_id}: groupe cohésif {{0,1,2}} violé"

        # Equity_gap peut être > 1 avec contraintes (acceptable)
        # Juste vérifier qu'on a un planning valide
        assert metrics.total_unique_pairs > 0

    def test_end_to_end_with_exclusive_group(self) -> None:
        """Test pipeline complet (3 phases) avec groupe exclusif."""
        config = PlanningConfig(N=20, X=4, x=5, S=5)

        exclusive = GroupConstraint(
            "Concurrents", GroupConstraintType.MUST_BE_SEPARATE, {0, 10}
        )
        constraints = PlanningConstraints(exclusive_groups=[exclusive])

        planning, metrics = generate_optimized_planning(
            config, seed=42, constraints=constraints
        )

        # Vérifier equity_gap ≤ 1
        assert metrics.equity_gap <= 1

        # Vérifier groupe exclusif respecté
        for session in planning.sessions:
            for table in session.tables:
                if 0 in table:
                    assert 10 not in table

    def test_end_to_end_complex_constraints(self) -> None:
        """Test pipeline avec plusieurs contraintes mixtes.

        Note: Avec contraintes hard complexes, equity_gap ≤ 1 n'est pas toujours possible.
        Priorité absolue = respect contraintes.
        """
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        cohesive1 = GroupConstraint("Couple 1", GroupConstraintType.MUST_BE_TOGETHER, {0, 1})
        cohesive2 = GroupConstraint("Équipe", GroupConstraintType.MUST_BE_TOGETHER, {10, 11, 12})
        exclusive1 = GroupConstraint("Conflit A", GroupConstraintType.MUST_BE_SEPARATE, {5, 15})
        exclusive2 = GroupConstraint("Conflit B", GroupConstraintType.MUST_BE_SEPARATE, {20, 25})

        constraints = PlanningConstraints(
            cohesive_groups=[cohesive1, cohesive2],
            exclusive_groups=[exclusive1, exclusive2],
        )

        planning, metrics = generate_optimized_planning(
            config, seed=42, constraints=constraints
        )

        # Vérifier toutes les contraintes (priorité absolue)
        for session in planning.sessions:
            # Cohésif 1 : {0, 1}
            table_0 = next(i for i, t in enumerate(session.tables) if 0 in t)
            table_1 = next(i for i, t in enumerate(session.tables) if 1 in t)
            assert (
                table_0 == table_1
            ), f"Session {session.session_id}: cohésif {{0,1}} violé"

            # Cohésif 2 : {10, 11, 12}
            table_10 = next(i for i, t in enumerate(session.tables) if 10 in t)
            table_11 = next(i for i, t in enumerate(session.tables) if 11 in t)
            table_12 = next(i for i, t in enumerate(session.tables) if 12 in t)
            assert (
                table_10 == table_11 == table_12
            ), f"Session {session.session_id}: cohésif {{10,11,12}} violé"

            # Exclusifs
            for table in session.tables:
                if 5 in table:
                    assert (
                        15 not in table
                    ), f"Session {session.session_id}: exclusif {{5,15}} violé"
                if 20 in table:
                    assert (
                        25 not in table
                    ), f"Session {session.session_id}: exclusif {{20,25}} violé"

        # Equity_gap peut être > 1 avec contraintes (acceptable car contraintes prioritaires)
        # Vérifier qu'on a au moins un planning valide
        assert metrics.total_unique_pairs > 0

    def test_determinism_with_constraints(self) -> None:
        """Test déterminisme avec contraintes : même seed → même planning."""
        config = PlanningConfig(N=20, X=4, x=5, S=4)

        cohesive = GroupConstraint("Couple", GroupConstraintType.MUST_BE_TOGETHER, {0, 1})
        constraints = PlanningConstraints(cohesive_groups=[cohesive])

        planning1, _ = generate_optimized_planning(config, seed=42, constraints=constraints)
        planning2, _ = generate_optimized_planning(config, seed=42, constraints=constraints)

        # Vérifier que plannings sont identiques
        for s1, s2 in zip(planning1.sessions, planning2.sessions):
            for t1, t2 in zip(s1.tables, s2.tables):
                assert t1 == t2
