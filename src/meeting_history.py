"""Calcul de l'historique des rencontres entre participants.

Ce module fournit des primitives pour calculer quelles paires de participants
se sont rencontrées durant un planning (utilisé pour le calcul de métriques).

Functions:
    compute_meeting_history: Calcule ensemble des paires rencontrées
"""

import logging
from typing import Set, Tuple

from src.models import Planning

logger = logging.getLogger(__name__)


def compute_meeting_history(planning: Planning) -> Set[Tuple[int, int]]:
    """Calcule l'ensemble des paires de participants s'étant rencontrés.

    Pour chaque session, pour chaque table, génère toutes les paires possibles
    de participants assis ensemble. Les paires sont normalisées (min, max)
    pour éviter les doublons (1,2) vs (2,1).

    Args:
        planning: Planning complet à analyser

    Returns:
        Set de tuples (p1, p2) avec p1 < p2, représentant toutes les paires
        ayant été à la même table au moins une fois

    Example:
        >>> config = PlanningConfig(N=6, X=2, x=3, S=2)
        >>> sessions = [
        ...     Session(0, [{0, 1, 2}, {3, 4, 5}]),
        ...     Session(1, [{0, 3, 4}, {1, 2, 5}])
        ... ]
        >>> planning = Planning(sessions, config)
        >>> history = compute_meeting_history(planning)
        >>> (0, 1) in history  # 0 et 1 étaient ensemble session 0
        True
        >>> (0, 5) in history  # 0 et 5 jamais ensemble
        False

    Complexity:
        Time: O(S × X × x²)
            - S sessions
            - X tables par session
            - x² paires par table (combinaisons)
        Space: O(total_pairs) où total_pairs ≤ N×(N-1)/2
    """
    met_pairs: Set[Tuple[int, int]] = set()

    for session in planning.sessions:
        for table in session.tables:
            # Générer toutes paires de participants à cette table
            participants = list(table)

            for i in range(len(participants)):
                for j in range(i + 1, len(participants)):
                    p1, p2 = participants[i], participants[j]
                    # Normalisation: toujours (min, max) pour éviter doublons
                    pair = (min(p1, p2), max(p1, p2))
                    met_pairs.add(pair)

    logger.debug(f"Historique calculé : {len(met_pairs)} paires rencontrées")

    return met_pairs
