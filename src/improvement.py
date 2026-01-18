"""Amélioration de planning par recherche locale greedy.

Ce module implémente l'algorithme d'optimisation locale (Phase 2 du pipeline)
qui réduit les répétitions en appliquant des swaps bénéfiques de manière itérative.

Functions:
    improve_planning: Optimise un planning par recherche locale greedy
    _swap_violates_constraints: Vérifie si swap viole contraintes hard
"""

import copy
import logging
from typing import List, Set, Tuple, Optional

from src.meeting_history import compute_meeting_history
from src.metrics import compute_metrics
from src.models import Planning, PlanningConfig, Session, PlanningConstraints
from src.swap_evaluation import evaluate_swap

logger = logging.getLogger(__name__)


def improve_planning(
    planning: Planning,
    config: PlanningConfig,
    max_iterations: int = 100,
    constraints: Optional[PlanningConstraints] = None,
) -> Planning:
    """Améliore un planning par recherche locale greedy (Phase 2).

    Algorithme:
        1. Calculer historique rencontres initial
        2. Pour chaque itération (jusqu'à max_iterations):
           a. Pour chaque session:
              - Pour chaque paire de tables:
                - Pour chaque paire de participants (un de chaque table):
                  - Évaluer swap avec evaluate_swap()
                  - Si amélioration (delta < 0), appliquer swap immédiatement
           b. Recalculer historique après modifications
           c. Détection plateau: si aucune amélioration, incrémenter compteur
           d. Si plateau détecté (N itérations sans amélioration), arrêter
        3. Retourner planning optimisé

    Stratégie greedy:
        - Applique le premier swap bénéfique trouvé (greedy, pas optimal global)
        - Recalcule historique après chaque itération complète
        - Arrêt anticipé si plateau détecté (évite itérations inutiles)

    Args:
        planning: Planning initial à améliorer
        config: Configuration associée
        max_iterations: Nombre maximum d'itérations (défaut: 100)
        constraints: Contraintes de groupes (hard constraints), optionnel

    Returns:
        Planning amélioré (nouvelle instance, planning original NON modifié)

    Note Protection Contraintes:
        Si contraintes fournies, chaque swap est vérifié AVANT application.
        Swaps violant contraintes cohésives ou exclusives sont REJETÉS.

    Example:
        >>> baseline = generate_baseline(config, seed=42)
        >>> improved = improve_planning(baseline, config, max_iterations=50)
        >>> # improved contient moins de répétitions que baseline

    Complexity:
        Time: O(iter × S × X² × x²)
            - iter: iterations effectuées (≤ max_iterations)
            - S: sessions
            - X²: paires de tables
            - x²: paires de participants
        Space: O(N × S) pour copie planning

    Note:
        La fonction crée une COPIE du planning en entrée et retourne
        une nouvelle instance modifiée.
    """
    # Copie profonde du planning (ne pas modifier l'original)
    optimized = copy.deepcopy(planning)

    # Calculer equity_gap initial (pour vérifier qu'on ne l'empire pas)
    initial_metrics = compute_metrics(planning, config)
    initial_equity_gap = initial_metrics.equity_gap

    # Détection plateau
    plateau_counter = 0
    plateau_threshold = 5  # Arrêter après 5 itérations sans amélioration

    logger.info(
        f"Démarrage amélioration locale : max {max_iterations} itérations, "
        f"plateau threshold {plateau_threshold}"
    )

    for iteration in range(max_iterations):
        # Recalculer historique rencontres pour cette itération
        met_pairs = compute_meeting_history(optimized)

        # Compteur améliorations pour cette itération
        improvements_found = 0

        # Parcourir toutes les sessions
        for session_id, session in enumerate(optimized.sessions):
            improvements_found += _improve_session(
                optimized, session_id, session, met_pairs, constraints
            )

        # Log progression
        if improvements_found > 0:
            logger.debug(
                f"Itération {iteration + 1}: {improvements_found} swaps bénéfiques appliqués"
            )
            plateau_counter = 0  # Reset compteur plateau
        else:
            plateau_counter += 1
            logger.debug(
                f"Itération {iteration + 1}: aucune amélioration (plateau {plateau_counter}/{plateau_threshold})"
            )

        # Détection plateau: arrêt anticipé
        if plateau_counter >= plateau_threshold:
            logger.info(
                f"Plateau détecté après {iteration + 1} itérations, arrêt anticipé"
            )
            break

    logger.info(
        f"Amélioration terminée après {min(iteration + 1, max_iterations)} itérations"
    )

    # Vérifier qu'on n'a pas empiré l'equity_gap
    final_metrics = compute_metrics(optimized, config)
    final_equity_gap = final_metrics.equity_gap

    if final_equity_gap > initial_equity_gap:
        logger.warning(
            f"Amélioration locale a empiré equity_gap ({initial_equity_gap} → {final_equity_gap}), "
            f"retour au planning baseline"
        )
        return planning  # Retourner planning original (baseline)

    return optimized


def _improve_session(
    planning: Planning,
    session_id: int,
    session: Session,
    met_pairs: Set[Tuple[int, int]],
    constraints: Optional[PlanningConstraints] = None,
) -> int:
    """Améliore une session en appliquant swaps bénéfiques (fonction auxiliaire).

    Parcourt toutes les paires de tables et toutes les paires de participants,
    évalue chaque swap, et applique le premier swap bénéfique trouvé.

    Args:
        planning: Planning complet (MODIFIÉ en place)
        session_id: Index de la session à améliorer
        session: Session à améliorer
        met_pairs: Historique rencontres actuel
        constraints: Contraintes de groupes (hard constraints), optionnel

    Returns:
        Nombre de swaps bénéfiques appliqués dans cette session

    Note:
        Cette fonction MODIFIE le planning en place pour efficacité.
        Swaps violant contraintes sont REJETÉS automatiquement.
    """
    swaps_applied = 0
    skipped_swaps = 0  # Compteur swaps rejetés par contraintes

    # Single-pass greedy: parcourir toutes les paires une fois
    # Si un participant a déjà été swappé, evaluate_swap lèvera ValueError qu'on ignore
    for table1_id in range(len(session.tables)):
        for table2_id in range(table1_id + 1, len(session.tables)):
            # Snapshot des participants au début (car tables modifiées en place)
            table1_participants = list(session.tables[table1_id])
            table2_participants = list(session.tables[table2_id])

            # Parcourir toutes les paires de participants
            for p1 in table1_participants:
                for p2 in table2_participants:
                    try:
                        # NOUVEAU: Vérifier contraintes AVANT d'évaluer swap
                        if constraints and _swap_violates_constraints(
                            session, table1_id, p1, table2_id, p2, constraints
                        ):
                            # Swap violerait contrainte hard → REJETER
                            skipped_swaps += 1
                            continue

                        # Évaluer swap (peut lever ValueError si participant déjà swappé)
                        delta = evaluate_swap(
                            planning,
                            session_id,
                            table1_id,
                            p1,
                            table2_id,
                            p2,
                            met_pairs,
                        )

                        # Si amélioration, appliquer swap immédiatement (greedy)
                        if delta < 0:
                            _apply_swap(session, table1_id, p1, table2_id, p2)
                            swaps_applied += 1

                            logger.debug(
                                f"Session {session_id}: swap {p1} (table {table1_id}) "
                                f"↔ {p2} (table {table2_id}), delta={delta}"
                            )
                    except ValueError:
                        # Participant déjà swappé dans cette session, skip
                        pass

    if skipped_swaps > 0:
        logger.debug(
            f"Session {session_id}: {skipped_swaps} swaps rejetés (violation contraintes)"
        )

    return swaps_applied


def _apply_swap(
    session: Session, table1_id: int, p1: int, table2_id: int, p2: int
) -> None:
    """Applique un swap entre deux participants (modifie session en place).

    Args:
        session: Session à modifier (MODIFIÉE en place)
        table1_id: Index table 1
        p1: Participant à retirer de table 1
        table2_id: Index table 2
        p2: Participant à retirer de table 2

    Note:
        Fonction auxiliaire privée, modifie la session en place pour efficacité.
    """
    table1 = session.tables[table1_id]
    table2 = session.tables[table2_id]

    # Swap atomique
    table1.remove(p1)
    table1.add(p2)

    table2.remove(p2)
    table2.add(p1)


def _swap_violates_constraints(
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
        True si swap interdit (viole contrainte), False si OK

    Note:
        Cette fonction est CRITIQUE pour garantir respect des contraintes hard.
        Elle doit être appelée AVANT chaque swap dans l'optimizer.
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
                return True  # p1 serait séparé du groupe → INTERDIT

        # Si p2 fait partie d'un groupe cohésif
        if p2 in group.participant_ids:
            # Vérifier que TOUS les membres (y compris p2) seraient à table1 après swap
            # Si pas tous à table1 → violation
            if not group.participant_ids.issubset(table1_after):
                return True  # p2 serait séparé du groupe → INTERDIT

    # Vérifier groupes exclusifs (membres ne doivent jamais être ensemble)
    for group in constraints.exclusive_groups:
        # Simuler état APRÈS swap pour vérifier
        table1_after = (session.tables[table1_id] - {p1}) | {p2}
        table2_after = (session.tables[table2_id] - {p2}) | {p1}

        # Vérifier table1 après swap : 2+ membres du même groupe exclusif ?
        members_in_table1 = table1_after & group.participant_ids
        if len(members_in_table1) >= 2:
            # 2+ membres du groupe exclusif seraient ensemble → INTERDIT
            return True

        # Vérifier table2 après swap : 2+ membres du même groupe exclusif ?
        members_in_table2 = table2_after & group.participant_ids
        if len(members_in_table2) >= 2:
            # 2+ membres du groupe exclusif seraient ensemble → INTERDIT
            return True

    # Aucune violation détectée → swap autorisé
    return False
