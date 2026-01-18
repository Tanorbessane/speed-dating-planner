"""Évaluation de l'impact d'un swap entre deux participants.

Ce module fournit la primitive pure pour évaluer l'impact d'un swap
sur le nombre de répétitions, sans modifier le planning (fonction pure).

Functions:
    evaluate_swap: Évalue delta répétitions d'un swap potentiel
"""

import logging
from typing import Set, Tuple

from src.models import Planning

logger = logging.getLogger(__name__)


def evaluate_swap(
    planning: Planning,
    session_id: int,
    table1_id: int,
    p1: int,
    table2_id: int,
    p2: int,
    met_pairs: Set[Tuple[int, int]],
) -> int:
    """Évalue l'impact d'un swap sur le nombre de répétitions (fonction pure).

    Calcule la différence de répétitions entre l'état actuel et l'état après swap,
    SANS modifier le planning (fonction pure).

    Algorithme:
        1. Récupérer tables concernées de la session
        2. Calculer répétitions AVANT swap (état actuel)
        3. Simuler swap (créer nouvelles tables temporaires)
        4. Calculer répétitions APRÈS swap (état simulé)
        5. Retourner delta = après - avant

    Args:
        planning: Planning à évaluer (NON MODIFIÉ)
        session_id: Index de la session concernée
        table1_id: Index de la première table
        p1: Participant à la table 1 à swapper
        table2_id: Index de la deuxième table
        p2: Participant à la table 2 à swapper
        met_pairs: Historique complet des rencontres (pour compter répétitions)

    Returns:
        Delta répétitions (int):
            - Négatif: swap améliore (réduit répétitions) ✅
            - Zéro: swap neutre
            - Positif: swap dégrade (augmente répétitions) ❌

    Example:
        >>> met_pairs = {(0,1), (0,2), (1,2), ...}
        >>> delta = evaluate_swap(planning, 0, 0, 5, 1, 12, met_pairs)
        >>> if delta < 0:
        ...     print("Swap bénéfique !")

    Complexity:
        Time: O(x) où x = taille table (parcours participants des 2 tables)
        Space: O(x) pour stockage tables temporaires

    Note:
        Cette fonction est PURE - elle ne modifie PAS le planning en entrée.
        Elle retourne uniquement une évaluation numérique.
    """
    # Récupérer session et tables concernées
    session = planning.sessions[session_id]
    table1 = session.tables[table1_id]
    table2 = session.tables[table2_id]

    # Validation: participants doivent être dans leurs tables respectives
    if p1 not in table1:
        raise ValueError(f"Participant {p1} absent de table {table1_id}")
    if p2 not in table2:
        raise ValueError(f"Participant {p2} absent de table {table2_id}")

    # Calcul répétitions AVANT swap (état actuel)
    repeats_before = _count_table_repeats(table1, met_pairs) + _count_table_repeats(
        table2, met_pairs
    )

    # Simulation swap (création tables temporaires - PURE)
    new_table1 = (table1 - {p1}) | {p2}  # Retirer p1, ajouter p2
    new_table2 = (table2 - {p2}) | {p1}  # Retirer p2, ajouter p1

    # Calcul répétitions APRÈS swap (état simulé)
    repeats_after = _count_table_repeats(
        new_table1, met_pairs
    ) + _count_table_repeats(new_table2, met_pairs)

    # Delta: négatif = amélioration
    delta = repeats_after - repeats_before

    return delta


def _count_table_repeats(table: Set[int], met_pairs: Set[Tuple[int, int]]) -> int:
    """Compte le nombre de répétitions dans une table (fonction auxiliaire pure).

    Une paire est considérée comme répétition si elle apparaît dans met_pairs
    (c'est-à-dire qu'elle s'est déjà rencontrée auparavant).

    Args:
        table: Ensemble des participants à la table
        met_pairs: Historique complet des rencontres

    Returns:
        Nombre de répétitions dans cette table

    Complexity:
        Time: O(x²) où x = taille table (génération paires)
        Space: O(1)

    Note:
        Fonction auxiliaire privée, pure (pas d'effets de bord).
    """
    repeats = 0
    participants = list(table)

    for i in range(len(participants)):
        for j in range(i + 1, len(participants)):
            p1, p2 = participants[i], participants[j]
            pair = (min(p1, p2), max(p1, p2))

            # Si cette paire s'est déjà rencontrée, c'est une répétition
            if pair in met_pairs:
                repeats += 1

    return repeats
