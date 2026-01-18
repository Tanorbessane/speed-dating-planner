"""Utilitaires d'affichage pour l'interface utilisateur.

Ce module fournit des helpers pour formatter l'affichage des données
dans l'interface Streamlit et les exports.

Functions:
    get_participant_display_name: Formate nom d'affichage d'un participant
"""

from typing import Optional, List
import pandas as pd


def get_participant_display_name(
    participant_id: int,
    participants_df: Optional[pd.DataFrame] = None,
    include_vip_badge: bool = False,
) -> str:
    """Retourne nom d'affichage formaté pour un participant.

    Format de sortie :
    - Avec prénom : "Prénom Nom" (ex: "Jean Dupont")
    - Sans prénom : "Nom" uniquement (ex: "Dupont")
    - VIP avec badge : "⭐ Prénom Nom"
    - Fallback : "Participant #ID"

    Args:
        participant_id: ID du participant (0-indexed)
        participants_df: DataFrame participants avec colonnes 'id', 'nom', 'prenom', 'is_vip'
        include_vip_badge: Ajouter emoji ⭐ si participant est VIP

    Returns:
        Nom d'affichage formaté ou "Participant #ID" si introuvable

    Example:
        >>> df = pd.DataFrame({
        ...     "id": [0, 1],
        ...     "nom": ["Dupont", "Martin"],
        ...     "prenom": ["Jean", None],
        ...     "is_vip": [True, False]
        ... })
        >>> get_participant_display_name(0, df)
        'Jean Dupont'
        >>> get_participant_display_name(1, df)
        'Martin'
        >>> get_participant_display_name(0, df, include_vip_badge=True)
        '⭐ Jean Dupont'
        >>> get_participant_display_name(99, df)
        'Participant #99'
        >>> get_participant_display_name(5, None)
        'Participant #5'

    Complexity:
        Time: O(n) pour recherche dans DataFrame (O(1) avec index)
        Space: O(1)
    """
    # Fallback si pas de DataFrame
    if participants_df is None or participants_df.empty:
        return f"Participant #{participant_id}"

    # Chercher participant par ID
    participant = participants_df[participants_df["id"] == participant_id]

    if participant.empty:
        return f"Participant #{participant_id}"

    # Extraire données
    row = participant.iloc[0]
    nom = row.get("nom", "")
    prenom = row.get("prenom", "")
    is_vip = row.get("is_vip", False)

    # Format : "Prénom Nom" ou "Nom" si pas de prénom
    if pd.notna(prenom) and prenom:
        display_name = f"{prenom} {nom}"
    else:
        display_name = str(nom)

    # Ajouter badge VIP si demandé
    if include_vip_badge and is_vip:
        display_name = f"⭐ {display_name}"

    return display_name


def format_table_participants(
    table: set,
    participants_df: Optional[pd.DataFrame] = None,
    include_vip_badge: bool = False,
    separator: str = ", ",
) -> str:
    """Formate liste de participants d'une table pour affichage.

    Args:
        table: Set d'IDs participants dans la table
        participants_df: DataFrame participants (optionnel)
        include_vip_badge: Inclure badge ⭐ pour VIP
        separator: Séparateur entre noms (défaut: ", ")

    Returns:
        String formatée des participants

    Example:
        >>> df = pd.DataFrame({
        ...     "id": [0, 1, 2],
        ...     "nom": ["Dupont", "Martin", "Bernard"],
        ...     "prenom": ["Jean", "Marie", "Luc"]
        ... })
        >>> table = {0, 1, 2}
        >>> format_table_participants(table, df)
        'Jean Dupont, Marie Martin, Luc Bernard'
        >>> format_table_participants(table, None)
        '0, 1, 2'

    Complexity:
        Time: O(n × m) où n = taille table, m = taille DataFrame
        Space: O(n) pour liste résultante
    """
    sorted_ids = sorted(table)

    if participants_df is None or participants_df.empty:
        # Fallback : afficher IDs
        return separator.join(str(p_id) for p_id in sorted_ids)

    # Afficher noms
    names = [
        get_participant_display_name(p_id, participants_df, include_vip_badge)
        for p_id in sorted_ids
    ]
    return separator.join(names)
