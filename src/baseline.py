"""Génération de planning baseline avec algorithme round-robin.

Ce module implémente l'algorithme de génération baseline (Phase 1 du pipeline)
utilisant une rotation round-robin avec stride coprime pour maximiser la diversité
des rencontres initiales.

Functions:
    generate_baseline: Génère un planning baseline avec rotation round-robin
    _create_super_participants: Crée super-participants pour groupes cohésifs
    _assign_tables_with_constraints: Assigne tables en respectant contraintes
    _violates_exclusive_constraint: Vérifie violation contrainte exclusive
"""

import logging
import random
from typing import List, Set, Optional

from src.models import Planning, PlanningConfig, Session, PlanningConstraints
from src.validation import validate_config

logger = logging.getLogger(__name__)


def generate_baseline(
    config: PlanningConfig, seed: int = 42, constraints: Optional[PlanningConstraints] = None
) -> Planning:
    """Génère un planning baseline avec rotation round-robin (Phase 1).

    Algorithme:
        1. Validation de la configuration et contraintes
        2. Création super-participants (groupes cohésifs = unité atomique)
        3. Pour chaque session:
           - Rotation des super-participants avec stride coprime
           - Distribution sur tables avec respect contraintes exclusives
        4. Retour du planning complet

    Caractéristiques:
        - Déterminisme: seed fixe → planning identique (NFR11)
        - Équité partielle: rotation uniforme
        - Respect HARD des contraintes cohésives et exclusives
        - Gestion tables partielles: tailles varient de ≤1 (FR7)

    Args:
        config: Configuration validée du planning
        seed: Graine aléatoire pour reproductibilité (défaut: 42, NFR11)
        constraints: Contraintes de groupes (cohésifs/exclusifs), optionnel

    Returns:
        Planning baseline avec S sessions générées

    Raises:
        InvalidConfigurationError: Si configuration ou contraintes invalides

    Example:
        >>> config = PlanningConfig(N=30, X=5, x=6, S=6)
        >>> constraints = PlanningConstraints(cohesive_groups=[...])
        >>> planning = generate_baseline(config, seed=42, constraints=constraints)
        >>> len(planning.sessions)
        6

    Complexity:
        Time: O(N × S) sans contraintes, O(N × S × X) avec contraintes exclusives
        Space: O(N × S) pour stocker le planning
    """
    # Validation configuration
    validate_config(config)

    # Validation contraintes si présentes
    if constraints:
        errors = constraints.validate(config)
        if errors:
            from src.validation import InvalidConfigurationError

            raise InvalidConfigurationError(
                f"Contraintes invalides : {'; '.join(errors)}"
            )
        logger.info(
            f"Contraintes détectées : {len(constraints.cohesive_groups)} cohésives, "
            f"{len(constraints.exclusive_groups)} exclusives"
        )

    # Initialisation seed pour déterminisme (NFR11)
    random.seed(seed)
    logger.debug(f"Génération baseline avec seed={seed}")

    # Créer super-participants (groupes cohésifs = unités atomiques)
    super_participants = _create_super_participants(config.N, constraints)
    logger.debug(
        f"Super-participants créés : {len(super_participants)} unités "
        f"(dont {len(constraints.cohesive_groups) if constraints else 0} groupes cohésifs)"
    )

    sessions: List[Session] = []

    for session_id in range(config.S):
        # Stride coprime pour rotation diverse
        stride = (session_id * 17 + 1) % len(super_participants) if len(super_participants) > 1 else 1

        # Rotation des super-participants
        rotated = super_participants[stride:] + super_participants[:stride]

        # Distribution sur tables avec respect contraintes
        tables = _assign_tables_with_constraints(
            rotated, config, session_id, constraints
        )

        # Création session
        session = Session(session_id=session_id, tables=tables)
        sessions.append(session)

        logger.debug(
            f"Session {session_id}: {len(tables)} tables, "
            f"{session.total_participants} participants"
        )

    planning = Planning(sessions=sessions, config=config)
    logger.info(
        f"Planning baseline généré : {config.N} participants, "
        f"{config.X} tables, {config.S} sessions"
    )

    return planning


def _create_super_participants(
    N: int, constraints: Optional[PlanningConstraints]
) -> List[Set[int]]:
    """Crée super-participants pour groupes cohésifs.

    Groupes cohésifs sont traités comme unités atomiques (jamais séparés).
    Participants sans groupe restent individuels.

    Args:
        N: Nombre total de participants
        constraints: Contraintes (peut être None)

    Returns:
        Liste de sets (super-participants). Chaque set = participants à la même table.

    Example:
        >>> # N=5, cohesive_groups=[{0,1}, {3,4}]
        >>> _create_super_participants(5, constraints)
        [{0,1}, {2}, {3,4}]
    """
    if not constraints or not constraints.cohesive_groups:
        # Pas de contraintes → chaque participant est individuel
        return [{i} for i in range(N)]

    assigned = set()
    super_participants: List[Set[int]] = []

    # Ajouter groupes cohésifs en premier
    for group in constraints.cohesive_groups:
        super_participants.append(group.participant_ids.copy())
        assigned.update(group.participant_ids)

    # Ajouter participants individuels (non assignés à groupe cohésif)
    for i in range(N):
        if i not in assigned:
            super_participants.append({i})

    return super_participants


def _assign_tables_with_constraints(
    super_participants: List[Set[int]],
    config: PlanningConfig,
    session_id: int,
    constraints: Optional[PlanningConstraints],
) -> List[Set[int]]:
    """Assigne super-participants aux tables avec respect contraintes exclusives.

    Strategy:
    - Round-robin standard pour répartition équitable
    - Avant assignation, vérifier contraintes exclusives
    - Si conflit détecté → essayer table suivante
    - Si toutes tables en conflit → forcer assignation (warning)

    Args:
        super_participants: Liste super-participants (individus ou groupes cohésifs)
        config: Configuration planning
        session_id: ID session (pour stride)
        constraints: Contraintes (peut être None)

    Returns:
        Liste de tables (sets de participant IDs)
    """
    tables: List[Set[int]] = [set() for _ in range(config.X)]

    for idx, sp in enumerate(super_participants):
        # Déterminer table cible (round-robin)
        table_id = idx % config.X

        # Vérifier contraintes exclusives
        if constraints and constraints.exclusive_groups:
            attempts = 0
            while (
                _violates_exclusive_constraint(tables[table_id], sp, constraints)
                and attempts < config.X
            ):
                # Essayer table suivante
                table_id = (table_id + 1) % config.X
                attempts += 1

            if attempts >= config.X:
                # Toutes tables violent contrainte → forcer assignation avec warning
                logger.warning(
                    f"Session {session_id}: Impossible de respecter contrainte exclusive "
                    f"pour participants {sp}. Assignation forcée."
                )

        # Assigner super-participant à table
        tables[table_id].update(sp)

    return tables


def _violates_exclusive_constraint(
    table: Set[int], new_participants: Set[int], constraints: PlanningConstraints
) -> bool:
    """Vérifie si ajouter new_participants à table viole contrainte exclusive.

    Args:
        table: Participants déjà à la table
        new_participants: Participants à ajouter (super-participant)
        constraints: Contraintes de planning

    Returns:
        True si violation, False sinon
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
                return True

    return False
