"""Module de visualisations avancées (Story 5.2+).

Ce module fournit des fonctions pour créer des graphiques et visualisations
interactives avec Plotly pour l'analyse des plannings.

Functions:
    create_meetings_heatmap: Crée heatmap interactive matrice rencontres
    create_distribution_chart: Crée bar chart distribution rencontres par participant
    create_pairs_pie_chart: Crée pie chart répartition paires uniques vs répétitions
"""

import logging
from typing import Optional, Dict
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.display_utils import get_participant_display_name

logger = logging.getLogger(__name__)


def create_meetings_heatmap(
    matrix: np.ndarray,
    participants_df: Optional[pd.DataFrame] = None,
    title: str = "Matrice des Rencontres entre Participants",
    max_label_length: int = 20,
) -> go.Figure:
    """Crée heatmap interactive Plotly pour matrice rencontres.

    Génère une visualisation carte de chaleur (heatmap) N×N interactive où :
    - Chaque cellule (i, j) montre le nombre de rencontres entre i et j
    - Échelle de couleur : blanc (0) → jaune (1) → orange (2) → rouge foncé (3+)
    - Hover tooltips avec noms participants et nombre rencontres
    - Axes avec noms participants (si disponibles) ou IDs

    Args:
        matrix: Matrice N×N rencontres (numpy array)
        participants_df: DataFrame participants pour noms sur axes (optionnel)
        title: Titre du graphique
        max_label_length: Longueur max labels (tronqué si > N)

    Returns:
        Figure Plotly interactive prête à afficher avec st.plotly_chart()

    Example:
        >>> matrix = compute_meetings_matrix(planning, config.N)
        >>> fig = create_meetings_heatmap(matrix, participants_df)
        >>> st.plotly_chart(fig, use_container_width=True)

    Complexity:
        Time: O(N²) pour construire hover text
        Space: O(N²) pour stockage hover text

    Note Colormap:
        - 0 rencontres : blanc (paire jamais rencontrée)
        - 1 rencontre : jaune (optimal FR5)
        - 2 rencontres : orange (répétition)
        - 3+ rencontres : rouge foncé (répétitions multiples)

    Note Performance:
        - Fluide jusqu'à N=100
        - Acceptable jusqu'à N=200
        - Au-delà : warning recommandé
    """
    N = matrix.shape[0]

    logger.debug(f"Création heatmap pour matrice {N}×{N}")

    # ===== CONSTRUIRE LABELS AXES =====
    labels = []
    for i in range(N):
        if participants_df is not None and not participants_df.empty:
            name = get_participant_display_name(i, participants_df)
            # Tronquer si trop long
            if len(name) > max_label_length:
                name = name[:max_label_length - 3] + "..."
            labels.append(name)
        else:
            # Fallback : IDs
            labels.append(f"P{i}")

    # ===== CONSTRUIRE HOVER TEXT =====
    hover_text = []
    for i in range(N):
        row_hover = []
        for j in range(N):
            if i == j:
                # Diagonale : soi-même
                text = f"{labels[i]}<br><i>(soi-même)</i>"
            else:
                meetings = matrix[i][j]
                # Format : "Jean Dupont ↔ Marie Martin : 2 rencontres"
                text = f"{labels[i]} ↔ {labels[j]}<br><b>{meetings} rencontre(s)</b>"
            row_hover.append(text)
        hover_text.append(row_hover)

    # ===== CRÉER HEATMAP PLOTLY =====
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',  # Custom hover, pas de trace name
        colorscale=[
            [0.0, 'white'],       # 0 rencontres
            [0.25, '#FFFF99'],    # 1 rencontre (jaune clair)
            [0.5, '#FFB347'],     # 2 rencontres (orange)
            [0.75, '#FF6347'],    # 3 rencontres (tomate)
            [1.0, '#8B0000']      # 4+ rencontres (rouge foncé)
        ],
        colorbar=dict(
            title="Rencontres",
            tickmode='linear',
            tick0=0,
            dtick=1,
            len=0.7
        ),
        showscale=True,
        zmin=0,  # Force min à 0 pour blanc = jamais rencontré
    ))

    # ===== LAYOUT =====
    # Taille dynamique selon N
    size = min(max(600, N * 15), 1200)  # Entre 600px et 1200px

    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Participants",
        yaxis_title="Participants",
        width=size,
        height=size,
        xaxis=dict(
            side='bottom',
            tickangle=45 if N > 20 else 0,  # Rotation si beaucoup de participants
            tickfont=dict(size=max(8, 14 - N // 10))  # Police plus petite si N grand
        ),
        yaxis=dict(
            autorange='reversed',  # Y de haut en bas (0 en haut)
            tickfont=dict(size=max(8, 14 - N // 10))
        ),
        margin=dict(l=100, r=100, t=100, b=100)
    )

    logger.info(f"Heatmap {N}×{N} créée avec succès")

    return fig


def create_distribution_chart(
    unique_meetings_per_person: list,
    participants_df: Optional[pd.DataFrame] = None,
    title: str = "Distribution des Rencontres par Participant",
    show_mean: bool = True
) -> go.Figure:
    """Crée bar chart distribution rencontres uniques par participant.

    Génère un bar chart interactif montrant le nombre de rencontres uniques
    pour chaque participant, avec :
    - Gradient couleur (vert = proche moyenne, rouge = extrêmes)
    - Ligne moyenne horizontale en pointillés
    - Noms participants sur axe X (si disponibles)
    - Hover tooltips avec détails

    Args:
        unique_meetings_per_person: Liste nombre rencontres par participant
        participants_df: DataFrame participants pour noms (optionnel)
        title: Titre du graphique
        show_mean: Afficher ligne moyenne (défaut: True)

    Returns:
        Figure Plotly interactive

    Example:
        >>> from src.metrics import compute_metrics
        >>> metrics = compute_metrics(planning, config, participants)
        >>> fig = create_distribution_chart(
        ...     metrics.unique_meetings_per_person,
        ...     participants_df
        ... )
        >>> st.plotly_chart(fig, use_container_width=True)

    Complexity:
        Time: O(N) pour construire labels et graphique
        Space: O(N)

    Design:
        - Gradient couleur : Rouge-Jaune-Vert (RdYlGn)
        - Ligne pointillée bleue pour moyenne
        - Valeurs affichées au-dessus des barres
        - Hover : "Participant X : Y rencontres"
    """
    N = len(unique_meetings_per_person)

    if N == 0:
        # Cas edge : liste vide
        logger.warning("Liste vide pour create_distribution_chart")
        return go.Figure()

    mean_value = sum(unique_meetings_per_person) / N

    logger.debug(f"Création distribution chart pour {N} participants (moyenne: {mean_value:.1f})")

    # ===== CONSTRUIRE LABELS AXE X =====
    x_labels = []
    for i in range(N):
        if participants_df is not None and not participants_df.empty:
            name = get_participant_display_name(i, participants_df)
            x_labels.append(name)
        else:
            # Fallback : IDs
            x_labels.append(f"P{i}")

    # ===== CRÉER BAR CHART =====
    fig = go.Figure(data=go.Bar(
        x=x_labels,
        y=unique_meetings_per_person,
        marker=dict(
            color=unique_meetings_per_person,
            colorscale='RdYlGn',  # Rouge-Jaune-Vert
            reversescale=False,  # Vert = valeurs hautes
            colorbar=dict(title="Rencontres")
        ),
        text=unique_meetings_per_person,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Rencontres: %{y}<extra></extra>'
    ))

    # ===== AJOUTER LIGNE MOYENNE =====
    if show_mean:
        fig.add_hline(
            y=mean_value,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Moyenne: {mean_value:.1f}",
            annotation_position="right"
        )

    # ===== LAYOUT =====
    fig.update_layout(
        title=title,
        xaxis_title="Participants",
        yaxis_title="Rencontres Uniques",
        showlegend=False,
        height=500,
        xaxis=dict(
            tickangle=45 if N > 20 else 0  # Rotation si beaucoup de participants
        ),
        yaxis=dict(
            rangemode='tozero'  # Commence à 0
        )
    )

    logger.info(f"Distribution chart créé pour {N} participants")

    return fig


def create_pairs_pie_chart(
    stats: Dict[str, any],
    title: str = "Répartition Paires Uniques vs Répétitions"
) -> go.Figure:
    """Crée pie chart répartition paires uniques vs répétées.

    Génère un camembert interactif montrant la répartition entre :
    - Paires uniques (rencontrées 1 seule fois)
    - Paires répétées (rencontrées 2+ fois)

    Couleurs :
    - Vert : Paires uniques (optimal FR5)
    - Orange : Paires répétées

    Args:
        stats: Statistiques matrice (total_pairs_met, repeat_pairs, etc.)
        title: Titre du graphique

    Returns:
        Figure Plotly interactive

    Example:
        >>> matrix = compute_meetings_matrix(planning, config.N)
        >>> stats = compute_matrix_statistics(matrix)
        >>> fig = create_pairs_pie_chart(stats)
        >>> st.plotly_chart(fig, use_container_width=True)

    Complexity:
        Time: O(1)
        Space: O(1)

    Design:
        - Vert (#2ecc71) : Paires uniques
        - Orange (#e67e22) : Paires répétées
        - Pourcentages affichés sur segments
        - Total dans sous-titre
    """
    # Calculer paires uniques (1 rencontre) vs répétées (2+ rencontres)
    total_pairs_met = stats['total_pairs_met']
    repeat_pairs = stats['repeat_pairs']
    unique_only_pairs = total_pairs_met - repeat_pairs

    logger.debug(
        f"Création pie chart : {unique_only_pairs} uniques, {repeat_pairs} répétées "
        f"(total: {total_pairs_met})"
    )

    # ===== DONNÉES PIE CHART =====
    labels = ['Paires Uniques (1 fois)', 'Paires Répétées (2+ fois)']
    values = [unique_only_pairs, repeat_pairs]
    colors = ['#2ecc71', '#e67e22']  # Vert, Orange

    # ===== CRÉER PIE CHART =====
    fig = go.Figure(data=go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>%{value} paires (%{percent})<extra></extra>'
    ))

    # ===== LAYOUT =====
    fig.update_layout(
        title=f"{title}<br><sub>Total paires rencontrées: {total_pairs_met}</sub>",
        showlegend=True,
        height=400
    )

    logger.info(f"Pie chart créé : {unique_only_pairs} uniques / {repeat_pairs} répétées")

    return fig
