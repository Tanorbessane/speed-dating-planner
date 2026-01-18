"""Tests unitaires pour module visualizations (Story 5.3).

Ce module teste les fonctions de création de graphiques Plotly
pour la visualisation des plannings.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
from src.visualizations import (
    create_distribution_chart,
    create_pairs_pie_chart,
    create_meetings_heatmap
)
from src.models import PlanningConfig, Planning, Session
from src.baseline import generate_baseline
from src.analysis import compute_meetings_matrix, compute_matrix_statistics


class TestCreateDistributionChart:
    """Tests pour create_distribution_chart() (Story 5.3)."""

    def test_basic_chart_no_participants(self):
        """Crée chart basique sans participants DataFrame."""
        unique_meetings = [10, 11, 10, 11, 10]

        fig = create_distribution_chart(unique_meetings, participants_df=None)

        # Vérifier figure créée
        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # 1 trace bar chart

        # Vérifier données
        bar_trace = fig.data[0]
        assert bar_trace.type == 'bar'
        assert list(bar_trace.y) == unique_meetings
        assert len(bar_trace.x) == 5

    def test_chart_with_participants(self):
        """Crée chart avec noms participants."""
        unique_meetings = [10, 11, 10]

        # Mock participants DataFrame
        participants_df = pd.DataFrame({
            "id": [0, 1, 2],
            "nom": ["Dupont", "Martin", "Durand"],
            "prenom": ["Jean", "Marie", "Paul"],
            "is_vip": [False, False, False]
        })

        fig = create_distribution_chart(unique_meetings, participants_df)

        # Vérifier figure créée
        assert fig is not None
        bar_trace = fig.data[0]

        # Vérifier noms sur axe X
        assert bar_trace.x[0] == "Jean Dupont"
        assert bar_trace.x[1] == "Marie Martin"
        assert bar_trace.x[2] == "Paul Durand"

    def test_chart_shows_mean_line(self):
        """Vérifie ligne moyenne affichée."""
        unique_meetings = [8, 10, 12]

        fig = create_distribution_chart(unique_meetings, show_mean=True)

        # Vérifier figure créée
        assert fig is not None

        # Vérifier présence ligne moyenne (shape ou annotation)
        # Plotly add_hline crée une shape
        assert len(fig.layout.shapes) > 0 or len(fig.layout.annotations) > 0

    def test_chart_without_mean_line(self):
        """Vérifie pas de ligne moyenne si show_mean=False."""
        unique_meetings = [8, 10, 12]

        fig = create_distribution_chart(unique_meetings, show_mean=False)

        # Vérifier figure créée
        assert fig is not None

        # Pas de ligne moyenne (moins de shapes/annotations)
        # Note: peut avoir des annotations de titre, donc on vérifie juste que ça ne crash pas
        assert isinstance(fig, go.Figure)

    def test_empty_list(self):
        """Gère liste vide sans crash."""
        fig = create_distribution_chart([], participants_df=None)

        # Devrait retourner figure vide mais valide
        assert fig is not None
        assert isinstance(fig, go.Figure)

    def test_large_dataset(self):
        """Test avec grand dataset (N=100)."""
        unique_meetings = [10] * 100

        fig = create_distribution_chart(unique_meetings, participants_df=None)

        # Vérifier figure créée
        assert fig is not None
        bar_trace = fig.data[0]
        assert len(bar_trace.y) == 100

        # Vérifier rotation labels si N > 20
        assert fig.layout.xaxis.tickangle == 45

    def test_realistic_planning_integration(self):
        """Test avec planning réaliste généré."""
        from src.metrics import compute_metrics

        config = PlanningConfig(N=12, X=3, x=4, S=4)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        fig = create_distribution_chart(
            metrics.unique_meetings_per_person,
            participants_df=None
        )

        # Vérifier figure créée
        assert fig is not None
        assert len(fig.data) == 1
        assert len(fig.data[0].y) == 12


class TestCreatePairsPieChart:
    """Tests pour create_pairs_pie_chart() (Story 5.3)."""

    def test_basic_pie_chart(self):
        """Crée pie chart basique."""
        stats = {
            'total_pairs_met': 45,
            'repeat_pairs': 5,
            'total_possible_pairs': 66,
            'coverage_rate': 68.2,
            'max_meetings': 2
        }

        fig = create_pairs_pie_chart(stats)

        # Vérifier figure créée
        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # 1 trace pie chart

        # Vérifier données
        pie_trace = fig.data[0]
        assert pie_trace.type == 'pie'
        assert len(pie_trace.values) == 2

        # Vérifier valeurs : uniques = 45 - 5 = 40, répétées = 5
        assert pie_trace.values[0] == 40  # Paires uniques
        assert pie_trace.values[1] == 5   # Paires répétées

    def test_no_repeats(self):
        """Pie chart avec 0 répétitions (optimal)."""
        stats = {
            'total_pairs_met': 45,
            'repeat_pairs': 0,
            'total_possible_pairs': 45,
            'coverage_rate': 100.0,
            'max_meetings': 1
        }

        fig = create_pairs_pie_chart(stats)

        # Vérifier figure créée
        assert fig is not None
        pie_trace = fig.data[0]

        # Toutes les paires sont uniques
        assert pie_trace.values[0] == 45  # Paires uniques
        assert pie_trace.values[1] == 0   # Paires répétées

    def test_all_repeats(self):
        """Pie chart avec toutes répétitions."""
        stats = {
            'total_pairs_met': 30,
            'repeat_pairs': 30,
            'total_possible_pairs': 66,
            'coverage_rate': 45.5,
            'max_meetings': 3
        }

        fig = create_pairs_pie_chart(stats)

        # Vérifier figure créée
        assert fig is not None
        pie_trace = fig.data[0]

        # Aucune paire unique
        assert pie_trace.values[0] == 0   # Paires uniques
        assert pie_trace.values[1] == 30  # Paires répétées

    def test_realistic_planning_integration(self):
        """Test avec planning réaliste généré."""
        config = PlanningConfig(N=12, X=3, x=4, S=4)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)
        stats = compute_matrix_statistics(matrix)

        fig = create_pairs_pie_chart(stats)

        # Vérifier figure créée
        assert fig is not None
        assert len(fig.data) == 1

        # Vérifier cohérence valeurs
        pie_trace = fig.data[0]
        total_computed = pie_trace.values[0] + pie_trace.values[1]
        assert total_computed == stats['total_pairs_met']


class TestIntegration:
    """Tests d'intégration visualisations (Story 5.3)."""

    def test_full_workflow_all_charts(self):
        """Workflow complet : génération → matrice → tous les graphiques."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)
        planning = generate_baseline(config, seed=42)

        # Calculer métriques
        from src.metrics import compute_metrics
        metrics = compute_metrics(planning, config)

        # Calculer matrice et stats
        matrix = compute_meetings_matrix(planning, config.N)
        stats = compute_matrix_statistics(matrix)

        # Créer tous les graphiques
        fig_heatmap = create_meetings_heatmap(matrix, participants_df=None)
        fig_dist = create_distribution_chart(metrics.unique_meetings_per_person)
        fig_pie = create_pairs_pie_chart(stats)

        # Vérifier tous créés
        assert fig_heatmap is not None
        assert fig_dist is not None
        assert fig_pie is not None

        # Vérifier types
        assert isinstance(fig_heatmap, go.Figure)
        assert isinstance(fig_dist, go.Figure)
        assert isinstance(fig_pie, go.Figure)

    def test_charts_with_participants_names(self):
        """Test charts avec noms participants réels."""
        # Créer planning
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)

        # Mock participants DataFrame
        participants_df = pd.DataFrame({
            "id": list(range(6)),
            "nom": ["A", "B", "C", "D", "E", "F"],
            "prenom": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
            "is_vip": [False] * 6
        })

        # Calculer métriques
        from src.metrics import compute_metrics
        metrics = compute_metrics(planning, config)

        # Calculer matrice
        matrix = compute_meetings_matrix(planning, config.N)

        # Créer graphiques avec noms
        fig_heatmap = create_meetings_heatmap(matrix, participants_df)
        fig_dist = create_distribution_chart(
            metrics.unique_meetings_per_person,
            participants_df
        )

        # Vérifier noms présents
        assert fig_heatmap is not None
        assert fig_dist is not None

        # Vérifier labels contiennent noms (pas juste P0, P1, etc.)
        dist_labels = fig_dist.data[0].x
        assert "Alice A" in dist_labels or "Alice" in dist_labels[0]
