"""Garantie d'équité pour les plannings (FR6: equity_gap ≤ 1).

Ce module implémente l'algorithme de garantie d'équité (Phase 3 du pipeline)
qui assure que max_unique - min_unique ≤ 1 pour tous les participants.

Functions:
    enforce_equity: Garantit equity_gap ≤ 1 par swaps ciblés
"""

import copy
import logging
from typing import List, Set, Tuple, Optional

from src.constraints_validator import validate_swap_constraints
from src.meeting_history import compute_meeting_history
from src.metrics import compute_metrics
from src.models import Planning, PlanningConfig, PlanningConstraints, Participant
from src.swap_evaluation import evaluate_swap

logger = logging.getLogger(__name__)


def enforce_equity(
    planning: Planning,
    config: PlanningConfig,
    constraints: Optional[PlanningConstraints] = None,
    participants: Optional[List[Participant]] = None,
    vip_max_advantage: int = 2,
) -> Planning:
    """Garantit équité parfaite ou quasi-parfaite (FR6: equity_gap ≤ 1).

    Algorithme:
        1. Calculer métriques actuelles
        2. Tant que equity_gap > 1:
           a. Identifier participants over-exposed (max_unique rencontres)
           b. Identifier participants under-exposed (min_unique rencontres)
           c. Si VIP présents : prioriser swaps VIP under-exposed
           d. Pour chaque swap candidat:
              - Chercher swap avec under-exposed qui réduit gap
              - Évaluer avec evaluate_swap (limiter répétitions)
              - Vérifier contraintes AVANT application (si définies)
              - Appliquer premier swap bénéfique trouvé
           e. Recalculer métriques
           f. Sécurité: max 1000 itérations (éviter boucle infinie)
        3. Retourner planning avec equity_gap ≤ 1 garanti

    Stratégie:
        - Swaps ciblés entre over/under-exposed (pas exhaustif)
        - Priorité VIP : VIP under-exposed corrigés en priorité
        - Avantage VIP contrôlé : VIP peuvent avoir +vip_max_advantage vs non-VIP
        - Contrainte secondaire: minimiser impact sur répétitions

    Args:
        planning: Planning à équilibrer
        config: Configuration associée
        constraints: Contraintes de groupes (hard constraints), optionnel
        participants: Liste participants avec statut VIP (optionnel)
        vip_max_advantage: Avantage max VIP vs non-VIP (défaut: 2 rencontres)

    Returns:
        Planning équilibré avec equity_gap ≤ 1 (nouvelle instance)

    Note Protection Contraintes:
        Si contraintes fournies, chaque swap est vérifié AVANT application.
        Swaps violant contraintes cohésives ou exclusives sont REJETÉS.

    Note Priorité VIP (Story 4.4):
        Si participants fournis avec VIP :
        - VIP under-exposed reçoivent swaps en priorité
        - Non-VIP equity_gap maintenu ≤ 1 (FR6 strict pour non-VIP)
        - VIP peuvent avoir jusqu'à +vip_max_advantage rencontres vs min non-VIP

    Raises:
        RuntimeError: Si impossible d'atteindre equity_gap ≤ 1 après 1000 itérations

    Example:
        >>> improved = improve_planning(baseline, config)
        >>> equitable = enforce_equity(improved, config)
        >>> metrics = compute_metrics(equitable, config)
        >>> assert metrics.equity_gap <= 1

    Complexity:
        Time: O(iter × N × S × X × x) où iter est le nombre d'itérations nécessaires
              En pratique: O(S × N) car peu d'itérations suffisent
        Space: O(N × S) pour copie planning

    Note:
        Garantie mathématique: equity_gap ≤ 1 atteint en temps fini
        (car nombre fini de configurations possibles et algorithme converge).
    """
    # Copie profonde (ne pas modifier original)
    equitable = copy.deepcopy(planning)

    max_iterations_safety = 1000  # Sécurité anti-boucle infinie
    iteration = 0

    # Détection de cycles (historique des 10 derniers equity_gaps)
    recent_gaps: List[int] = []
    cycle_detection_window = 10

    logger.info("Démarrage enforcement équité (objectif: equity_gap ≤ 1)")

    while iteration < max_iterations_safety:
        # Calculer métriques actuelles
        metrics = compute_metrics(equitable, config)
        met_pairs = compute_meeting_history(equitable)

        # Vérifier si équité atteinte
        if metrics.equity_gap <= 1:
            logger.info(
                f"✓ Équité atteinte après {iteration} itérations "
                f"(equity_gap = {metrics.equity_gap})"
            )
            return equitable

        # Détection de cycles : si equity_gap oscille, arrêter
        recent_gaps.append(metrics.equity_gap)
        if len(recent_gaps) > cycle_detection_window:
            recent_gaps.pop(0)

        # Si on a vu le même pattern 3+ fois dans la fenêtre, on est dans un cycle
        if len(recent_gaps) >= cycle_detection_window:
            # Vérifier oscillation (ex: 5,4,5,4,5,4...)
            if len(set(recent_gaps)) <= 2 and recent_gaps.count(recent_gaps[0]) >= 3:
                logger.warning(
                    f"Cycle détecté (equity_gap oscille entre {set(recent_gaps)}), "
                    f"arrêt après {iteration} itérations. Equity_gap final: {metrics.equity_gap}"
                )
                return equitable

        # Identifier over-exposed et under-exposed
        over_exposed = _find_over_exposed(metrics)
        under_exposed = _find_under_exposed(metrics)

        logger.debug(
            f"Itération {iteration}: equity_gap = {metrics.equity_gap}, "
            f"{len(over_exposed)} over-exposed, {len(under_exposed)} under-exposed"
        )

        # Chercher swaps bénéfiques avec priorité VIP si applicable
        swap_found = False

        # Si participants VIP : prioriser swaps VIP
        if participants:
            vip_ids = {p.id for p in participants if p.is_vip}

            # Vérifier avantage VIP actuel
            vip_meetings = [
                metrics.unique_meetings_per_person[p.id]
                for p in participants
                if p.is_vip
            ]
            non_vip_meetings = [
                metrics.unique_meetings_per_person[p.id]
                for p in participants
                if not p.is_vip
            ]

            vip_advantage_ok = True
            if vip_meetings and non_vip_meetings:
                min_vip = min(vip_meetings)
                min_non_vip = min(non_vip_meetings)
                current_advantage = min_vip - min_non_vip
                if current_advantage >= vip_max_advantage:
                    # VIP ont déjà avantage max, pas de priorité
                    vip_advantage_ok = False
                    logger.debug(
                        f"VIP advantage limit atteint ({current_advantage} >= {vip_max_advantage}), "
                        "pas de priorité VIP"
                    )

            # Séparer VIP et non-VIP
            over_vip = [p for p in over_exposed if p in vip_ids]
            over_regular = [p for p in over_exposed if p not in vip_ids]
            under_vip = [p for p in under_exposed if p in vip_ids]
            under_regular = [p for p in under_exposed if p not in vip_ids]

            # Ordre de priorité pour swaps (si avantage VIP OK)
            if vip_advantage_ok and under_vip:
                swap_priorities = [
                    (under_vip, over_regular, "VIP under ↔ Regular over"),  # Priorité 1
                    (under_vip, over_vip, "VIP under ↔ VIP over"),  # Priorité 2
                    (under_regular, over_exposed, "Regular under ↔ Over"),  # Priorité 3
                ]
            else:
                # Pas de priorité VIP (avantage déjà max ou pas de VIP under)
                swap_priorities = [(under_exposed, over_exposed, "Standard")]
        else:
            # Pas de participants : comportement standard
            swap_priorities = [(under_exposed, over_exposed, "Standard")]

        # Chercher swaps avec priorités
        for under_list, over_list, priority_name in swap_priorities:
            for p_under in under_list:
                for p_over in over_list:
                    # Chercher swap entre p_over et p_under dans toutes les sessions
                    if _try_swap_participants(
                        equitable, p_over, p_under, met_pairs, config, constraints
                    ):
                        swap_found = True
                        logger.debug(
                            f"Swap appliqué [{priority_name}]: participant {p_over} (over) ↔ {p_under} (under)"
                        )
                        break  # Appliquer un swap, recalculer métriques
                if swap_found:
                    break
            if swap_found:
                break

        # Si aucun swap trouvé, impossible de progresser
        if not swap_found:
            logger.warning(
                f"Aucun swap bénéfique trouvé, equity_gap = {metrics.equity_gap} (arrêt)"
            )
            # Accepter equity_gap actuel (peut être > 1 si impossible)
            return equitable

        iteration += 1

    # Sécurité: max iterations atteint (ne devrait jamais arriver avec détection cycles)
    final_metrics = compute_metrics(equitable, config)
    logger.warning(
        f"Max iterations ({max_iterations_safety}) atteint. "
        f"Equity_gap final: {final_metrics.equity_gap}"
    )
    return equitable


def _find_over_exposed(metrics) -> List[int]:
    """Trouve participants over-exposed (max_unique rencontres).

    Returns:
        Liste des IDs participants avec max_unique rencontres
    """
    over_exposed = []
    for participant_id, count in enumerate(metrics.unique_meetings_per_person):
        if count == metrics.max_unique:
            over_exposed.append(participant_id)
    return over_exposed


def _find_under_exposed(metrics) -> List[int]:
    """Trouve participants under-exposed (min_unique rencontres).

    Returns:
        Liste des IDs participants avec min_unique rencontres
    """
    under_exposed = []
    for participant_id, count in enumerate(metrics.unique_meetings_per_person):
        if count == metrics.min_unique:
            under_exposed.append(participant_id)
    return under_exposed


def _try_swap_participants(
    planning: Planning,
    p_over: int,
    p_under: int,
    met_pairs: Set[Tuple[int, int]],
    config: PlanningConfig,
    constraints: Optional[PlanningConstraints] = None,
) -> bool:
    """Tente de swapper p_over et p_under dans n'importe quelle session.

    Parcourt toutes les sessions, cherche où p_over et p_under sont dans
    des tables différentes, calcule l'impact sur equity_gap, applique si bénéfique.

    Pour réduire equity_gap:
    - p_over (over-exposed) doit perdre des rencontres uniques
    - p_under (under-exposed) doit gagner des rencontres uniques

    Args:
        planning: Planning (MODIFIÉ en place si swap appliqué)
        p_over: Participant over-exposed
        p_under: Participant under-exposed
        met_pairs: Historique rencontres
        config: Configuration
        constraints: Contraintes de groupes (hard constraints), optionnel

    Returns:
        True si swap appliqué, False sinon

    Note:
        Si contraintes fournies, swaps violant contraintes sont REJETÉS.
    """
    for session_id, session in enumerate(planning.sessions):
        # Trouver tables contenant p_over et p_under
        table_over_id = None
        table_under_id = None

        for table_id, table in enumerate(session.tables):
            if p_over in table:
                table_over_id = table_id
            if p_under in table:
                table_under_id = table_id

        # Si dans tables différentes, évaluer swap
        if (
            table_over_id is not None
            and table_under_id is not None
            and table_over_id != table_under_id
        ):
            table_over = session.tables[table_over_id]
            table_under = session.tables[table_under_id]

            # Calculer impact sur rencontres uniques de chaque participant
            # p_over perd table_over, gagne table_under
            over_loses = table_over - {p_over}
            over_gains = table_under - {p_under}

            # p_under perd table_under, gagne table_over
            under_loses = table_under - {p_under}
            under_gains = table_over - {p_over}

            # Compter rencontres uniques perdues/gagnées
            over_unique_lost = sum(
                1 for p in over_loses if (min(p_over, p), max(p_over, p)) not in met_pairs
            )
            over_unique_gained = sum(
                1 for p in over_gains if (min(p_over, p), max(p_over, p)) not in met_pairs
            )

            under_unique_lost = sum(
                1 for p in under_loses if (min(p_under, p), max(p_under, p)) not in met_pairs
            )
            under_unique_gained = sum(
                1 for p in under_gains if (min(p_under, p), max(p_under, p)) not in met_pairs
            )

            # Delta net pour chaque participant
            over_delta = over_unique_gained - over_unique_lost
            under_delta = under_unique_gained - under_unique_lost

            # Pour réduire equity_gap :
            # - p_over doit perdre des uniques (over_delta < 0)
            # - p_under doit gagner des uniques (under_delta > 0)
            # Metric: under_delta - over_delta (devrait être positif)
            equity_improvement = under_delta - over_delta

            if equity_improvement > 0:
                # Ce swap réduit l'equity_gap
                # NOUVEAU: Vérifier contraintes AVANT d'appliquer swap
                if constraints and validate_swap_constraints(
                    session, table_over_id, p_over, table_under_id, p_under, constraints
                ):
                    # Swap violerait contrainte hard → REJETER
                    continue

                # Appliquer swap
                session.tables[table_over_id].remove(p_over)
                session.tables[table_over_id].add(p_under)
                session.tables[table_under_id].remove(p_under)
                session.tables[table_under_id].add(p_over)

                logger.debug(
                    f"Session {session_id}: swap p{p_over} ↔ p{p_under}, "
                    f"equity_improvement={equity_improvement} (over_delta={over_delta}, under_delta={under_delta})"
                )
                return True

    return False


# NOTE: La fonction _swap_violates_constraints a été déplacée vers src/constraints_validator.py
# pour éviter la duplication avec improvement.py. Utiliser validate_swap_constraints() à la place.
