"""Module d'analyse avancée des plannings (Story 5.2+).

Ce module fournit des fonctions pour analyser en profondeur les plannings générés,
notamment la matrice des rencontres et les statistiques associées.

Functions:
    compute_meetings_matrix: Calcule matrice N×N des rencontres entre participants
    compute_matrix_statistics: Calcule statistiques sur matrice rencontres
    compute_quality_score: Calcule score qualité global du planning (0-100)
"""

import logging
from typing import Dict
import numpy as np

from src.models import Planning, PlanningMetrics

logger = logging.getLogger(__name__)


def compute_meetings_matrix(planning: Planning, N: int) -> np.ndarray:
    """Calcule matrice N×N des rencontres entre participants.

    Construit une matrice carrée où matrix[i][j] représente le nombre de fois
    que le participant i a rencontré le participant j dans le planning.

    Propriétés de la matrice :
    - Carrée N×N (N = nombre de participants)
    - Symétrique : matrix[i][j] = matrix[j][i]
    - Diagonale = 0 : un participant ne se rencontre pas lui-même
    - Valeurs ≥ 0 : nombre de rencontres

    Args:
        planning: Planning à analyser
        N: Nombre total de participants

    Returns:
        Matrice numpy N×N (dtype=int) des rencontres

    Example:
        >>> config = PlanningConfig(N=6, X=2, x=3, S=2)
        >>> planning = generate_baseline(config, seed=42)
        >>> matrix = compute_meetings_matrix(planning, config.N)
        >>> matrix.shape
        (6, 6)
        >>> matrix[0][5]  # Nombre rencontres entre participant 0 et 5
        2
        >>> matrix[5][0]  # Symétrique
        2
        >>> matrix[0][0]  # Diagonale = 0
        0

    Complexity:
        Time: O(S × X × x²) où S=sessions, X=tables, x=places par table
              En pratique ≈ O(N × S) car x est constant
        Space: O(N²) pour la matrice

    Note:
        Utilise numpy pour performance sur grandes matrices (N > 100).
    """
    # Initialiser matrice N×N à zéro
    matrix = np.zeros((N, N), dtype=int)

    # Pour chaque session et chaque table
    for session in planning.sessions:
        for table in session.tables:
            participants = list(table)

            # Pour chaque paire dans la table (combinaisons)
            for i in range(len(participants)):
                for j in range(i + 1, len(participants)):
                    p1, p2 = participants[i], participants[j]

                    # Incrémenter compteur pour cette paire (symétrique)
                    matrix[p1][p2] += 1
                    matrix[p2][p1] += 1

    logger.debug(f"Matrice {N}×{N} calculée : {np.count_nonzero(matrix)} cellules non-nulles")

    return matrix


def compute_matrix_statistics(matrix: np.ndarray) -> Dict[str, float]:
    """Calcule statistiques descriptives sur matrice rencontres.

    Analyse la matrice pour extraire métriques clés :
    - Combien de paires se sont rencontrées au moins une fois
    - Taux de couverture (% des paires possibles rencontrées)
    - Nombre de répétitions (paires rencontrées ≥2 fois)
    - Maximum de rencontres entre une paire

    Args:
        matrix: Matrice N×N rencontres (numpy array)

    Returns:
        Dict avec statistiques :
        - total_pairs_met (int): Nombre paires rencontrées ≥1 fois
        - total_possible_pairs (int): N×(N-1)/2 (total paires possibles)
        - coverage_rate (float): Pourcentage paires rencontrées (0-100)
        - repeat_pairs (int): Nombre paires rencontrées ≥2 fois
        - max_meetings (int): Maximum rencontres entre une paire

    Example:
        >>> matrix = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]])
        >>> stats = compute_matrix_statistics(matrix)
        >>> stats['total_possible_pairs']
        3  # 3×2/2 = 3 paires possibles
        >>> stats['total_pairs_met']
        3  # Toutes les paires se sont rencontrées
        >>> stats['coverage_rate']
        100.0  # 100% de couverture
        >>> stats['repeat_pairs']
        1  # Une paire rencontrée 2 fois : (0, 2)
        >>> stats['max_meetings']
        2

    Complexity:
        Time: O(N²) pour parcourir triangle supérieur de la matrice
        Space: O(1) pour compteurs

    Note:
        On ne compte que le triangle supérieur car matrice symétrique.
    """
    N = matrix.shape[0]

    # Total paires possibles : N×(N-1)/2 (combinaisons)
    total_possible_pairs = N * (N - 1) // 2

    # Parcourir triangle supérieur uniquement (matrice symétrique)
    pairs_met = 0
    repeat_pairs = 0
    max_meetings = 0

    for i in range(N):
        for j in range(i + 1, N):
            meetings = matrix[i][j]

            # Compter paires rencontrées au moins une fois
            if meetings >= 1:
                pairs_met += 1

            # Compter répétitions (≥2 rencontres)
            if meetings >= 2:
                repeat_pairs += 1

            # Tracker maximum
            if meetings > max_meetings:
                max_meetings = meetings

    # Taux de couverture (pourcentage)
    coverage_rate = (
        100.0 * pairs_met / total_possible_pairs if total_possible_pairs > 0 else 0.0
    )

    stats = {
        "total_pairs_met": pairs_met,
        "total_possible_pairs": total_possible_pairs,
        "coverage_rate": coverage_rate,
        "repeat_pairs": repeat_pairs,
        "max_meetings": max_meetings,
    }

    logger.debug(
        f"Statistiques matrice : {pairs_met}/{total_possible_pairs} paires "
        f"({coverage_rate:.1f}% couverture), {repeat_pairs} répétitions, max={max_meetings}"
    )

    return stats


def compute_quality_score(metrics: PlanningMetrics, stats: Dict[str, float]) -> Dict[str, any]:
    """Calcule score qualité global du planning (0-100).

    Évalue la qualité d'un planning selon 3 critères pondérés :
    - Équité (40%) : Écart min-max rencontres par participant
    - Couverture (30%) : Pourcentage de paires ayant été rencontrées
    - Répétitions (30%) : Pourcentage de paires rencontrées plusieurs fois

    Scoring par critère :
    - **Équité (40 pts)** :
      - gap ≤ 1 : 40 pts (optimal FR6)
      - gap = 2 : 25 pts
      - gap = 3 : 10 pts
      - gap > 3 : 0 pts

    - **Couverture (30 pts)** :
      - Proportionnel à coverage_rate (0-100%)
      - 100% couverture = 30 pts
      - 50% couverture = 15 pts

    - **Répétitions (30 pts)** :
      - 0% répétitions : 30 pts (optimal FR5)
      - < 5% : 25 pts
      - < 10% : 15 pts
      - ≥ 10% : décroît linéairement

    Grades :
    - Excellent (🟢) : ≥ 90 points
    - Bon (🟡) : 70-89 points
    - À améliorer (🔴) : < 70 points

    Args:
        metrics: PlanningMetrics avec equity_gap, total_repeat_pairs, etc.
        stats: Statistiques matrice (coverage_rate, repeat_pairs, total_possible_pairs)

    Returns:
        Dict avec :
        - score (int): Score total 0-100
        - grade (str): "Excellent" / "Bon" / "À améliorer"
        - color (str): "green" / "yellow" / "red"
        - emoji (str): "🟢" / "🟡" / "🔴"

    Example:
        >>> from src.analysis import compute_quality_score
        >>> from src.models import PlanningMetrics
        >>> metrics = PlanningMetrics(
        ...     total_unique_pairs=45,
        ...     total_repeat_pairs=0,
        ...     unique_meetings_per_person=[10]*10,
        ...     min_unique=10,
        ...     max_unique=10,
        ...     mean_unique=10.0
        ... )
        >>> stats = {
        ...     'coverage_rate': 100.0,
        ...     'repeat_pairs': 0,
        ...     'total_possible_pairs': 45
        ... }
        >>> quality = compute_quality_score(metrics, stats)
        >>> quality['score']
        100
        >>> quality['grade']
        'Excellent'
        >>> quality['emoji']
        '🟢'

    Complexity:
        Time: O(1) - calcul simple arithmétique
        Space: O(1)

    Note:
        Le score favorise fortement l'équité (40%) car c'est l'exigence
        fonctionnelle FR6 la plus importante pour l'expérience utilisateur.
    """
    # ===== ÉQUITÉ (40 points) =====
    if metrics.equity_gap <= 1:
        equity_score = 40
    elif metrics.equity_gap == 2:
        equity_score = 25
    elif metrics.equity_gap == 3:
        equity_score = 10
    else:
        equity_score = 0

    # ===== COUVERTURE (30 points) =====
    coverage_score = 30 * (stats['coverage_rate'] / 100)

    # ===== RÉPÉTITIONS (30 points) =====
    repeat_pct = (
        100 * stats['repeat_pairs'] / stats['total_possible_pairs']
        if stats['total_possible_pairs'] > 0
        else 0
    )

    if repeat_pct == 0:
        repeat_score = 30
    elif repeat_pct < 5:
        repeat_score = 25
    elif repeat_pct < 10:
        repeat_score = 15
    else:
        # Décroissance linéaire après 10%
        repeat_score = max(0, 30 - repeat_pct)

    # ===== SCORE TOTAL =====
    total_score = round(equity_score + coverage_score + repeat_score)

    # ===== GRADE ET COULEUR =====
    if total_score >= 90:
        grade = "Excellent"
        color = "green"
        emoji = "🟢"
    elif total_score >= 70:
        grade = "Bon"
        color = "yellow"
        emoji = "🟡"
    else:
        grade = "À améliorer"
        color = "red"
        emoji = "🔴"

    logger.info(
        f"Score qualité : {total_score}/100 ({grade}) - "
        f"Équité: {equity_score:.0f}pts, Couverture: {coverage_score:.1f}pts, Répétitions: {repeat_score:.1f}pts"
    )

    return {
        "score": total_score,
        "grade": grade,
        "color": color,
        "emoji": emoji
    }
