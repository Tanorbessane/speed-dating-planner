"""Module d'export PDF des plannings (Story 5.4).

Génère un rapport PDF complet avec :
- Page de garde avec configuration et score qualité
- KPIs et métriques principales
- Graphiques (heatmap, distribution, pie chart)
- Planning détaillé (toutes sessions/tables)

Dependencies:
    - reportlab : Génération PDF
    - kaleido : Export graphiques Plotly → PNG
    - Pillow : Manipulation images

Functions:
    export_to_pdf: Génère rapport PDF complet du planning
"""

import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
from typing import Optional
import pandas as pd
import tempfile
import os

from src.models import Planning, PlanningConfig, PlanningMetrics
from src.analysis import compute_meetings_matrix, compute_matrix_statistics, compute_quality_score
from src.visualizations import create_meetings_heatmap, create_distribution_chart, create_pairs_pie_chart
from src.display_utils import get_participant_display_name

logger = logging.getLogger(__name__)


def export_to_pdf(
    planning: Planning,
    config: PlanningConfig,
    metrics: PlanningMetrics,
    participants_df: Optional[pd.DataFrame] = None,
    output_path: Optional[str] = None
) -> BytesIO:
    """Génère rapport PDF complet du planning.

    Crée un document PDF professionnel contenant :
    1. Page de garde avec configuration et score qualité
    2. Section KPIs avec métriques principales
    3. Graphiques visuels (heatmap, distribution, pie chart)
    4. Planning détaillé avec toutes les sessions/tables
    5. Footer avec "Généré par Speed Dating Planner" et numéros de page

    Args:
        planning: Planning à exporter
        config: Configuration du planning
        metrics: Métriques calculées
        participants_df: DataFrame participants (optionnel, pour afficher noms)
        output_path: Chemin fichier PDF (si None, retourne BytesIO)

    Returns:
        BytesIO contenant le PDF si output_path=None, sinon None

    Example:
        >>> pdf_bytes = export_to_pdf(planning, config, metrics, participants_df)
        >>> st.download_button(
        ...     label="Télécharger PDF",
        ...     data=pdf_bytes.getvalue(),
        ...     file_name="planning_report.pdf",
        ...     mime="application/pdf"
        ... )

    Raises:
        Exception: Si erreur génération PDF ou export graphiques

    Note:
        - Pour N > 50, la heatmap n'est pas incluse (trop grande)
        - Graphiques exportés en PNG haute résolution (scale=2)
        - Format A4, marges 0.5 inch
    """
    logger.info(f"Début génération PDF pour planning N={config.N}, S={config.S}")

    # Calculer matrice et stats
    matrix = compute_meetings_matrix(planning, config.N)
    stats = compute_matrix_statistics(matrix)
    quality = compute_quality_score(metrics, stats)

    # Créer BytesIO si pas de output_path
    buffer = BytesIO() if output_path is None else None
    output = buffer if buffer else output_path

    # Créer document PDF
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=inch/2,
        leftMargin=inch/2,
        topMargin=inch,
        bottomMargin=inch/2
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    # Conteneur éléments PDF
    story = []

    # ===== PAGE DE GARDE =====
    logger.debug("Génération page de garde")
    _add_cover_page(story, config, quality, styles, title_style)

    # ===== SECTION KPIS =====
    logger.debug("Génération KPIs")
    _add_kpis_section(story, config, metrics, stats, styles)

    # ===== SECTION GRAPHIQUES =====
    logger.debug("Génération graphiques")
    _add_charts_section(story, config, matrix, metrics, stats, participants_df, styles)

    # ===== PLANNING DÉTAILLÉ =====
    logger.debug("Génération planning détaillé")
    _add_planning_section(story, planning, participants_df, styles)

    # Build PDF avec footer
    logger.debug("Construction document PDF")
    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)

    logger.info(f"PDF généré avec succès ({len(planning.sessions)} sessions)")

    # Retourner buffer si pas de output_path
    if buffer:
        buffer.seek(0)
        return buffer

    return None


def _add_cover_page(story, config, quality, styles, title_style):
    """Ajoute page de garde au PDF."""
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Rapport Planning Speed Dating", title_style))
    story.append(Spacer(1, 0.5*inch))

    # Date génération
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(
        f"<para align=center>Généré le {date_str}</para>",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Configuration
    config_data = [
        ["Configuration Planning", ""],
        ["Participants", str(config.N)],
        ["Tables", str(config.X)],
        ["Capacité/table", str(config.x)],
        ["Sessions", str(config.S)],
    ]

    config_table = Table(config_data, colWidths=[3*inch, 2*inch])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(config_table)
    story.append(Spacer(1, 0.5*inch))

    # Score qualité
    quality_text = f"Score Qualité : {quality['grade']} ({quality['score']}/100)"
    story.append(Paragraph(
        f"<para align=center fontSize=16><b>{quality_text}</b></para>",
        styles['Normal']
    ))

    story.append(PageBreak())


def _add_kpis_section(story, config, metrics, stats, styles):
    """Ajoute section KPIs au PDF."""
    story.append(Paragraph("KPIs Principaux", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))

    repeat_pct = (
        100 * stats['repeat_pairs'] / stats['total_possible_pairs']
        if stats['total_possible_pairs'] > 0
        else 0
    )

    kpis_data = [
        ["Métrique", "Valeur"],
        ["Participants", str(config.N)],
        ["Couverture", f"{stats['coverage_rate']:.1f}%"],
        ["Équité (Gap)", str(metrics.equity_gap)],
        ["Répétitions", f"{stats['repeat_pairs']} ({repeat_pct:.1f}%)"],
        ["Max Rencontres", str(stats['max_meetings'])],
        ["Sessions", str(config.S)],
    ]

    kpis_table = Table(kpis_data, colWidths=[3*inch, 2*inch])
    kpis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
    ]))
    story.append(kpis_table)

    story.append(PageBreak())


def _add_charts_section(story, config, matrix, metrics, stats, participants_df, styles):
    """Ajoute section graphiques au PDF."""
    story.append(Paragraph("Graphiques Visualisation", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))

    # Heatmap (seulement si N <= 50, sinon trop grande)
    if config.N <= 50:
        try:
            fig_heatmap = create_meetings_heatmap(matrix, participants_df)
            heatmap_img = _plotly_fig_to_image(fig_heatmap, width=700, height=700)
            if heatmap_img:
                story.append(Paragraph("Matrice des Rencontres", styles['Heading2']))
                story.append(heatmap_img)
                story.append(PageBreak())
        except Exception as e:
            logger.warning(f"Erreur export heatmap : {e}")

    # Distribution chart
    try:
        fig_dist = create_distribution_chart(metrics.unique_meetings_per_person, participants_df)
        dist_img = _plotly_fig_to_image(fig_dist, width=700, height=450)
        if dist_img:
            story.append(Paragraph("Distribution Rencontres par Participant", styles['Heading2']))
            story.append(dist_img)
            story.append(Spacer(1, 0.3*inch))
    except Exception as e:
        logger.warning(f"Erreur export distribution chart : {e}")

    # Pie chart
    try:
        fig_pie = create_pairs_pie_chart(stats)
        pie_img = _plotly_fig_to_image(fig_pie, width=600, height=400)
        if pie_img:
            story.append(Paragraph("Répartition Paires Uniques vs Répétitions", styles['Heading2']))
            story.append(pie_img)
    except Exception as e:
        logger.warning(f"Erreur export pie chart : {e}")

    story.append(PageBreak())


def _add_planning_section(story, planning, participants_df, styles):
    """Ajoute planning détaillé au PDF."""
    story.append(Paragraph("Planning Détaillé", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))

    for session in planning.sessions:
        story.append(Paragraph(f"Session {session.session_id + 1}", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))

        for table_idx, table in enumerate(session.tables):
            participants_str = _format_table_participants_list(table, participants_df)
            story.append(Paragraph(
                f"<b>Table {table_idx + 1}</b> : {participants_str}",
                styles['Normal']
            ))

        story.append(Spacer(1, 0.2*inch))


def _plotly_fig_to_image(fig, width=600, height=400):
    """Convertit figure Plotly en Image ReportLab.

    Utilise kaleido pour exporter Plotly → PNG haute résolution.

    Args:
        fig: Figure Plotly
        width: Largeur en pixels
        height: Hauteur en pixels

    Returns:
        Image ReportLab ou None si erreur

    Raises:
        Exception: Si kaleido pas installé ou erreur export

    Note:
        Le fichier temporaire est créé avec delete=False et sera
        nettoyé automatiquement par le système après utilisation.
    """
    try:
        import plotly.io as pio

        # Exporter en PNG via kaleido (scale=2 pour haute résolution)
        img_bytes = pio.to_image(fig, format='png', width=width, height=height, scale=2)

        # Sauvegarder temporairement (delete=False car ReportLab lit le fichier plus tard)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        # Créer Image ReportLab (ReportLab va lire le fichier pendant doc.build())
        img = Image(tmp_path, width=5*inch, height=3*inch)

        # Note: Ne PAS supprimer le fichier ici, ReportLab en a besoin plus tard
        # Le système d'exploitation nettoiera les fichiers temp automatiquement

        return img

    except ImportError as e:
        logger.error(f"Kaleido non installé : {e}")
        logger.info("Installez avec : pip install kaleido")
        return None
    except Exception as e:
        logger.error(f"Erreur export graphique : {e}")
        return None


def _format_table_participants_list(table: set, participants_df: Optional[pd.DataFrame]) -> str:
    """Formate liste participants d'une table pour PDF.

    Args:
        table: Set d'IDs participants
        participants_df: DataFrame participants (optionnel)

    Returns:
        String formatée : "Jean Dupont, Marie Martin, ..." ou "P0, P1, ..."
    """
    sorted_ids = sorted(table)

    names = []
    for p_id in sorted_ids:
        name = get_participant_display_name(p_id, participants_df)
        names.append(name)

    return ", ".join(names)


def _add_footer(canvas, doc):
    """Ajoute footer sur chaque page du PDF.

    Args:
        canvas: Canvas ReportLab
        doc: Document ReportLab
    """
    canvas.saveState()
    canvas.setFont('Helvetica', 9)

    # Footer gauche : texte
    canvas.drawString(inch/2, 0.5*inch, "Généré par Speed Dating Planner")

    # Footer droit : numéro page
    canvas.drawRightString(A4[0] - inch/2, 0.5*inch, f"Page {doc.page}")

    canvas.restoreState()
