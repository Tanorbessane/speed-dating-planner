"""Validation des contraintes hard (cohésives/exclusives).

Ce module centralise la logique de validation des contraintes pour garantir cohérence
entre toutes les phases du pipeline (improvement & equity).

Functions:
    validate_swap_constraints: Vérifie si swap viole contraintes
    validate_table_assignment: Vérifie si assignation table viole contraintes
"""

import logging
from typing import Set

from src.models import PlanningConstraints, Session

logger = logging.getLogger(__name__)


def validate_swap_constraints(
    session: Session,
    table1_id: int,
    p1: int,
    table2_id: int,
    p2: int,
    constraints: PlanningConstraints,
) -> bool:
    """Vérifie si swap p1 ↔ p2 viole contraintes hard.

    Vérifie :
    1. Groupes cohésifs : membres doivent rester ensemble
    2. Groupes exclusifs : membres ne doivent jamais être ensemble

    Args:
        session: Session actuelle
        table1_id: Index table 1
        p1: Participant à swapper (de table 1)
        table2_id: Index table 2
        p2: Participant à swapper (de table 2)
        constraints: Contraintes de groupes

    Returns:
        True si swap INTERDIT (viole contrainte), False si OK

    Example:
        >>> # Dans improvement.py ou equity.py
        >>> if validate_swap_constraints(session, table1_id, p1, table2_id, p2, constraints):
        >>>     continue  # Skip ce swap, viole contrainte

    Note:
        Cette fonction est CRITIQUE pour garantir respect des contraintes hard.
        Elle doit être appelée AVANT chaque swap dans optimizer et equity enforcement.

    Complexity:
        Time: O(C) où C = nombre de contraintes (cohésives + exclusives)
        Space: O(1)
    """
    # Simuler état APRÈS swap
    table1_after = (session.tables[table1_id] - {p1}) | {p2}
    table2_after = (session.tables[table2_id] - {p2}) | {p1}

    # Vérifier groupes cohésifs (membres doivent rester ensemble)
    for group in constraints.cohesive_groups:
        # Si p1 fait partie d'un groupe cohésif
        if p1 in group.participant_ids:
            # Vérifier que TOUS les membres (y compris p1) seraient à table2 après swap
            # Si pas tous à table2 → violation
            if not group.participant_ids.issubset(table2_after):
                logger.debug(
                    f"Swap {p1}↔{p2} rejected: would separate cohesive group '{group.name}'"
                )
                return True  # p1 serait séparé du groupe → INTERDIT

        # Si p2 fait partie d'un groupe cohésif
        if p2 in group.participant_ids:
            # Vérifier que TOUS les membres (y compris p2) seraient à table1 après swap
            # Si pas tous à table1 → violation
            if not group.participant_ids.issubset(table1_after):
                logger.debug(
                    f"Swap {p1}↔{p2} rejected: would separate cohesive group '{group.name}'"
                )
                return True  # p2 serait séparé du groupe → INTERDIT

    # Vérifier groupes exclusifs (membres ne doivent jamais être ensemble)
    for group in constraints.exclusive_groups:
        # Vérifier table1 après swap : 2+ membres du même groupe exclusif ?
        members_in_table1 = table1_after & group.participant_ids
        if len(members_in_table1) >= 2:
            # 2+ membres du groupe exclusif seraient ensemble → INTERDIT
            logger.debug(
                f"Swap {p1}↔{p2} rejected: would put exclusive group '{group.name}' together at table {table1_id}"
            )
            return True

        # Vérifier table2 après swap : 2+ membres du même groupe exclusif ?
        members_in_table2 = table2_after & group.participant_ids
        if len(members_in_table2) >= 2:
            # 2+ membres du groupe exclusif seraient ensemble → INTERDIT
            logger.debug(
                f"Swap {p1}↔{p2} rejected: would put exclusive group '{group.name}' together at table {table2_id}"
            )
            return True

    # Aucune violation détectée → swap autorisé
    return False


def validate_table_assignment(
    table: Set[int],
    new_participants: Set[int],
    constraints: PlanningConstraints,
) -> bool:
    """Vérifie si ajouter new_participants à table viole contraintes exclusives.

    Utilisé principalement dans baseline.py pour vérifier assignations initiales.

    Args:
        table: Participants déjà à la table
        new_participants: Participants à ajouter (super-participant)
        constraints: Contraintes de groupes

    Returns:
        True si VIOLATION (ne PAS ajouter), False si OK

    Example:
        >>> # Dans baseline.py
        >>> if validate_table_assignment(table, sp, constraints):
        >>>     # Essayer table suivante
        >>>     table_id = (table_id + 1) % config.X

    Complexity:
        Time: O(E) où E = nombre de contraintes exclusives
        Space: O(1)
    """
    for group in constraints.exclusive_groups:
        # Vérifier si table contient déjà un membre du groupe exclusif
        table_has_member = bool(table & group.participant_ids)
        # Vérifier si on ajoute un autre membre du même groupe
        new_has_member = bool(new_participants & group.participant_ids)

        if table_has_member and new_has_member:
            # Vérifier que ce ne sont pas exactement les mêmes participants
            # (OK si on déplace le même participant)
            table_members = table & group.participant_ids
            new_members = new_participants & group.participant_ids
            if table_members != new_members:
                # Différents membres du groupe exclusif → violation
                logger.debug(
                    f"Table assignment rejected: would put exclusive group '{group.name}' together"
                )
                return True

    return False


def count_constraint_violations(
    session: Session,
    constraints: PlanningConstraints
) -> int:
    """Compte le nombre de violations de contraintes dans une session.

    Utile pour validation et debugging.

    Args:
        session: Session à vérifier
        constraints: Contraintes à appliquer

    Returns:
        Nombre de violations détectées (0 = pas de violation)

    Example:
        >>> violations = count_constraint_violations(session, constraints)
        >>> if violations > 0:
        >>>     logger.warning(f"{violations} constraint violations detected!")

    Note:
        Une violation = un groupe (cohésif ou exclusif) dont la contrainte n'est pas respectée.

    Complexity:
        Time: O(C × T) où C = contraintes, T = tables
        Space: O(1)
    """
    violations = 0

    # Vérifier groupes cohésifs (doivent être à la même table)
    for group in constraints.cohesive_groups:
        # Trouver à quelles tables sont les membres du groupe
        tables_with_members = set()
        for table_id, table in enumerate(session.tables):
            if any(p in table for p in group.participant_ids):
                tables_with_members.add(table_id)

        # Si membres répartis sur plusieurs tables → violation
        if len(tables_with_members) > 1:
            violations += 1
            logger.warning(
                f"Cohesive group '{group.name}' split across {len(tables_with_members)} tables"
            )

    # Vérifier groupes exclusifs (ne doivent JAMAIS être ensemble)
    for group in constraints.exclusive_groups:
        for table_id, table in enumerate(session.tables):
            members_in_table = table & group.participant_ids
            # Si 2+ membres du même groupe exclusif à la même table → violation
            if len(members_in_table) >= 2:
                violations += 1
                logger.warning(
                    f"Exclusive group '{group.name}' has {len(members_in_table)} members together at table {table_id}"
                )

    return violations


def validate_planning_constraints(
    planning: "Planning",
    constraints: PlanningConstraints
) -> bool:
    """Valide qu'un planning complet respecte toutes les contraintes.

    Args:
        planning: Planning complet à valider
        constraints: Contraintes à vérifier

    Returns:
        True si toutes contraintes respectées, False sinon

    Example:
        >>> if not validate_planning_constraints(planning, constraints):
        >>>     raise ValueError("Planning viole contraintes!")

    Note:
        Vérifie TOUTES les sessions du planning.

    Complexity:
        Time: O(S × C × T) où S = sessions, C = contraintes, T = tables
        Space: O(1)
    """
    from src.models import Planning

    total_violations = 0

    for session in planning.sessions:
        violations = count_constraint_violations(session, constraints)
        total_violations += violations

    if total_violations > 0:
        logger.error(
            f"Planning validation failed: {total_violations} constraint violations across {len(planning.sessions)} sessions"
        )
        return False

    logger.info(
        f"Planning validation passed: all constraints respected across {len(planning.sessions)} sessions"
    )
    return True
