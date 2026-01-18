"""Calcul des métriques de qualité d'un planning.

Ce module fournit le calcul complet des métriques utilisées pour évaluer
la qualité d'un planning (FR8-FR9).

Functions:
    compute_metrics: Calcule toutes les métriques de qualité
"""

import logging
from collections import Counter
from typing import Dict, List, Optional

from src.meeting_history import compute_meeting_history
from src.models import Planning, PlanningConfig, PlanningMetrics, Participant, VIPMetrics

logger = logging.getLogger(__name__)


def compute_metrics(
    planning: Planning, config: PlanningConfig, participants: Optional[List[Participant]] = None
) -> PlanningMetrics:
    """Calcule toutes les métriques de qualité d'un planning.

    Métriques calculées:
        - total_unique_pairs: Nombre de paires s'étant rencontrées ≥1 fois
        - total_repeat_pairs: Nombre de paires s'étant rencontrées >1 fois
        - unique_meetings_per_person: Liste du nombre de rencontres uniques par participant
        - min_unique: Minimum de rencontres uniques
        - max_unique: Maximum de rencontres uniques
        - mean_unique: Moyenne de rencontres uniques
        - equity_gap (property): max_unique - min_unique (objectif ≤1, FR6)
        - vip_metrics: Métriques séparées VIP vs réguliers (si participants fournis)

    Args:
        planning: Planning à évaluer
        config: Configuration associée
        participants: Liste participants avec statut VIP (optionnel, pour métriques VIP)

    Returns:
        PlanningMetrics avec toutes les métriques calculées

    Example:
        >>> config = PlanningConfig(N=6, X=2, x=3, S=2)
        >>> planning = generate_baseline(config, seed=42)
        >>> metrics = compute_metrics(planning, config)
        >>> metrics.total_unique_pairs
        15
        >>> metrics.equity_gap  # max_unique - min_unique
        0

    Complexity:
        Time: O(S × X × x²) pour meeting_history + O(N) pour comptage
              = O(S × X × x²)
        Space: O(N²) pour historique paires worst-case
    """
    # Étape 1: Calculer historique des rencontres
    meeting_history = compute_meeting_history(planning)

    # Étape 2: Compter rencontres par paire
    pair_counts: Dict[tuple[int, int], int] = Counter()

    for session in planning.sessions:
        for table in session.tables:
            table_members = list(table)
            for i in range(len(table_members)):
                for j in range(i + 1, len(table_members)):
                    p1, p2 = table_members[i], table_members[j]
                    pair = (min(p1, p2), max(p1, p2))
                    pair_counts[pair] += 1

    # Étape 3: Calculer métriques globales
    total_unique_pairs = len(meeting_history)
    total_repeat_pairs = sum(1 for count in pair_counts.values() if count > 1)

    # Étape 4: Calculer rencontres par participant
    unique_meetings_per_person = [0] * config.N

    for (p1, p2) in meeting_history:
        unique_meetings_per_person[p1] += 1
        unique_meetings_per_person[p2] += 1

    # Étape 5: Statistiques distributionnelles
    if unique_meetings_per_person:
        min_unique = min(unique_meetings_per_person)
        max_unique = max(unique_meetings_per_person)
        mean_unique = sum(unique_meetings_per_person) / len(unique_meetings_per_person)
    else:
        min_unique = 0
        max_unique = 0
        mean_unique = 0.0

    # Étape 6: Calculer métriques VIP si participants fournis
    vip_metrics = None
    if participants is not None and len(participants) > 0:
        vip_metrics = _compute_vip_metrics(unique_meetings_per_person, participants)

    # Création métriques
    metrics = PlanningMetrics(
        total_unique_pairs=total_unique_pairs,
        total_repeat_pairs=total_repeat_pairs,
        unique_meetings_per_person=unique_meetings_per_person,
        min_unique=min_unique,
        max_unique=max_unique,
        mean_unique=mean_unique,
        vip_metrics=vip_metrics,
    )

    if vip_metrics:
        logger.debug(
            f"Métriques calculées : {total_unique_pairs} paires uniques, "
            f"{total_repeat_pairs} répétitions, equity_gap={metrics.equity_gap}, "
            f"VIP: {vip_metrics.vip_count} VIP (gap={vip_metrics.vip_equity_gap}), "
            f"{vip_metrics.non_vip_count} réguliers (gap={vip_metrics.non_vip_equity_gap})"
        )
    else:
        logger.debug(
            f"Métriques calculées : {total_unique_pairs} paires uniques, "
            f"{total_repeat_pairs} répétitions, equity_gap={metrics.equity_gap}"
        )

    return metrics


def _compute_vip_metrics(
    unique_meetings_per_person: List[int], participants: List[Participant]
) -> Optional[VIPMetrics]:
    """Calcule métriques séparées pour VIP vs participants réguliers.

    Args:
        unique_meetings_per_person: Liste rencontres uniques par participant
        participants: Liste participants avec statut is_vip

    Returns:
        VIPMetrics si au moins 1 VIP présent, None sinon

    Example:
        >>> participants = [
        ...     Participant(0, "VIP1", is_vip=True),
        ...     Participant(1, "VIP2", is_vip=True),
        ...     Participant(2, "Regular1", is_vip=False),
        ... ]
        >>> meetings = [15, 16, 12]
        >>> vip_metrics = _compute_vip_metrics(meetings, participants)
        >>> vip_metrics.vip_equity_gap
        1
        >>> vip_metrics.non_vip_equity_gap
        0
    """
    # Séparer VIP et non-VIP
    vip_participants = [p for p in participants if p.is_vip]
    non_vip_participants = [p for p in participants if not p.is_vip]

    # Si aucun VIP, pas de métriques VIP
    if not vip_participants:
        return None

    # Métriques VIP
    vip_meetings = [unique_meetings_per_person[p.id] for p in vip_participants]
    vip_min = min(vip_meetings)
    vip_max = max(vip_meetings)
    vip_mean = sum(vip_meetings) / len(vip_meetings)
    vip_equity_gap = vip_max - vip_min

    # Métriques non-VIP
    if non_vip_participants:
        non_vip_meetings = [unique_meetings_per_person[p.id] for p in non_vip_participants]
        non_vip_min = min(non_vip_meetings)
        non_vip_max = max(non_vip_meetings)
        non_vip_mean = sum(non_vip_meetings) / len(non_vip_meetings)
        non_vip_equity_gap = non_vip_max - non_vip_min
    else:
        # Tous sont VIP
        non_vip_min = non_vip_max = 0
        non_vip_mean = 0.0
        non_vip_equity_gap = 0

    return VIPMetrics(
        vip_count=len(vip_participants),
        vip_min_unique=vip_min,
        vip_max_unique=vip_max,
        vip_mean_unique=vip_mean,
        vip_equity_gap=vip_equity_gap,
        non_vip_count=len(non_vip_participants),
        non_vip_min_unique=non_vip_min,
        non_vip_max_unique=non_vip_max,
        non_vip_mean_unique=non_vip_mean,
        non_vip_equity_gap=non_vip_equity_gap,
    )
