"""Tests unitaires pour module analysis (Story 5.2).

Ce module teste les fonctions d'analyse des plannings,
notamment la matrice des rencontres et ses statistiques.
"""

import pytest
import numpy as np
from src.analysis import compute_meetings_matrix, compute_matrix_statistics
from src.models import PlanningConfig, Planning, Session, PlanningMetrics
from src.baseline import generate_baseline


class TestComputeMeetingsMatrix:
    """Tests pour compute_meetings_matrix()."""

    def test_matrix_shape(self):
        """Matrice a shape N×N."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)

        assert matrix.shape == (6, 6)
        assert matrix.dtype == np.int64 or matrix.dtype == np.int32

    def test_diagonal_zero(self):
        """Diagonale = 0 (personne ne se rencontre soi-même)."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)

        # Tous les éléments diagonaux doivent être 0
        for i in range(6):
            assert matrix[i][i] == 0

    def test_symmetric(self):
        """Matrice est symétrique."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)

        # Pour toute paire (i, j), matrix[i][j] = matrix[j][i]
        for i in range(10):
            for j in range(10):
                assert matrix[i][j] == matrix[j][i]

    def test_values_non_negative(self):
        """Toutes les valeurs ≥ 0."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)

        assert np.all(matrix >= 0)

    def test_simple_planning(self):
        """Test avec planning simple et prévisible."""
        # Planning manuel : 2 participants, 1 table, 1 session
        # Participant 0 et 1 se rencontrent 1 fois
        config = PlanningConfig(N=2, X=1, x=2, S=1)
        planning = Planning(
            sessions=[
                Session(session_id=0, tables=[{0, 1}])
            ],
            config=config
        )

        matrix = compute_meetings_matrix(planning, config.N)

        # Participant 0 et 1 se sont rencontrés 1 fois
        assert matrix[0][1] == 1
        assert matrix[1][0] == 1

        # Diagonale = 0
        assert matrix[0][0] == 0
        assert matrix[1][1] == 0

    def test_multiple_meetings(self):
        """Test avec répétitions (même paire plusieurs fois)."""
        # Planning avec 3 participants, même paire se rencontre 2 fois
        config = PlanningConfig(N=3, X=2, x=2, S=2)
        planning = Planning(
            sessions=[
                Session(session_id=0, tables=[{0, 1}, {2}]),  # 0-1 se rencontrent
                Session(session_id=1, tables=[{0, 1}, {2}])   # 0-1 se rencontrent encore
            ],
            config=config
        )

        matrix = compute_meetings_matrix(planning, config.N)

        # 0 et 1 se sont rencontrés 2 fois
        assert matrix[0][1] == 2
        assert matrix[1][0] == 2

        # 2 n'a rencontré personne (table seul)
        assert matrix[2][0] == 0
        assert matrix[2][1] == 0

    def test_larger_planning(self):
        """Test avec planning plus grand."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)

        # Propriétés basiques
        assert matrix.shape == (30, 30)
        assert np.all(np.diag(matrix) == 0)  # Diagonale = 0
        assert np.all(matrix >= 0)  # Valeurs ≥ 0

        # Matrice symétrique
        assert np.array_equal(matrix, matrix.T)


class TestComputeMatrixStatistics:
    """Tests pour compute_matrix_statistics()."""

    def test_all_met_once(self):
        """Toutes les paires se sont rencontrées exactement 1 fois."""
        # Matrice 3×3 : toutes paires rencontrées 1 fois
        matrix = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])

        stats = compute_matrix_statistics(matrix)

        # Total paires : 3×2/2 = 3
        assert stats['total_possible_pairs'] == 3

        # Toutes rencontrées
        assert stats['total_pairs_met'] == 3

        # 100% couverture
        assert stats['coverage_rate'] == 100.0

        # Pas de répétitions
        assert stats['repeat_pairs'] == 0

        # Max = 1
        assert stats['max_meetings'] == 1

    def test_with_repeats(self):
        """Certaines paires avec répétitions."""
        # Matrice 4×4
        matrix = np.array([
            [0, 1, 2, 0],
            [1, 0, 1, 1],
            [2, 1, 0, 0],
            [0, 1, 0, 0]
        ])

        stats = compute_matrix_statistics(matrix)

        # Total paires : 4×3/2 = 6
        assert stats['total_possible_pairs'] == 6

        # Paires rencontrées : (0,1), (0,2), (1,2), (1,3) = 4
        assert stats['total_pairs_met'] == 4

        # Couverture : 4/6 = 66.67%
        assert abs(stats['coverage_rate'] - 66.67) < 0.1

        # Répétitions (≥2) : (0,2) = 1
        assert stats['repeat_pairs'] == 1

        # Max : 2
        assert stats['max_meetings'] == 2

    def test_no_meetings(self):
        """Matrice vide (personne ne s'est rencontré)."""
        # Matrice 5×5 remplie de zéros
        matrix = np.zeros((5, 5), dtype=int)

        stats = compute_matrix_statistics(matrix)

        # Total paires : 5×4/2 = 10
        assert stats['total_possible_pairs'] == 10

        # Aucune rencontrée
        assert stats['total_pairs_met'] == 0

        # 0% couverture
        assert stats['coverage_rate'] == 0.0

        # Pas de répétitions
        assert stats['repeat_pairs'] == 0

        # Max = 0
        assert stats['max_meetings'] == 0

    def test_fully_connected_with_repeats(self):
        """Matrice complète avec répétitions partout."""
        # Matrice 3×3 : toutes paires rencontrées 3 fois
        matrix = np.array([
            [0, 3, 3],
            [3, 0, 3],
            [3, 3, 0]
        ])

        stats = compute_matrix_statistics(matrix)

        # Total paires : 3×2/2 = 3
        assert stats['total_possible_pairs'] == 3

        # Toutes rencontrées
        assert stats['total_pairs_met'] == 3

        # 100% couverture
        assert stats['coverage_rate'] == 100.0

        # Toutes ont des répétitions
        assert stats['repeat_pairs'] == 3

        # Max = 3
        assert stats['max_meetings'] == 3

    def test_realistic_planning(self):
        """Test avec planning réaliste généré."""
        config = PlanningConfig(N=12, X=3, x=4, S=4)
        planning = generate_baseline(config, seed=42)

        matrix = compute_meetings_matrix(planning, config.N)
        stats = compute_matrix_statistics(matrix)

        # Total paires : 12×11/2 = 66
        assert stats['total_possible_pairs'] == 66

        # Au moins quelques paires rencontrées
        assert stats['total_pairs_met'] > 0

        # Couverture entre 0 et 100%
        assert 0 <= stats['coverage_rate'] <= 100

        # Statistiques cohérentes
        assert stats['repeat_pairs'] <= stats['total_pairs_met']
        assert stats['max_meetings'] >= 0


class TestIntegration:
    """Tests d'intégration Story 5.2."""

    def test_full_workflow(self):
        """Workflow complet : génération → matrice → stats → heatmap."""
        config = PlanningConfig(N=10, X=2, x=5, S=3)
        planning = generate_baseline(config, seed=42)

        # Calculer matrice
        matrix = compute_meetings_matrix(planning, config.N)

        # Vérifications basiques
        assert matrix.shape == (10, 10)
        assert np.all(np.diag(matrix) == 0)
        assert np.array_equal(matrix, matrix.T)

        # Calculer statistiques
        stats = compute_matrix_statistics(matrix)

        # Vérifications cohérence
        assert stats['total_pairs_met'] <= stats['total_possible_pairs']
        assert stats['repeat_pairs'] <= stats['total_pairs_met']
        assert 0 <= stats['coverage_rate'] <= 100

        # Note: La création de la heatmap sera testée en manuel dans Streamlit
        # car elle nécessite un environnement graphique

    def test_matrix_matches_metrics(self):
        """Matrice doit être cohérente avec métriques."""
        from src.metrics import compute_metrics

        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)

        # Calculer métriques classiques
        metrics = compute_metrics(planning, config)

        # Calculer matrice
        matrix = compute_meetings_matrix(planning, config.N)
        stats = compute_matrix_statistics(matrix)

        # Les paires rencontrées dans matrice doivent correspondre aux métriques
        # Note: total_unique_pairs compte toutes les paires ayant ≥1 rencontre
        assert stats['total_pairs_met'] == metrics.total_unique_pairs

        # Les répétitions doivent correspondre
        assert stats['repeat_pairs'] == metrics.total_repeat_pairs


class TestComputeQualityScore:
    """Tests pour compute_quality_score() (Story 5.5)."""

    def test_score_excellent_perfect_planning(self):
        """Score excellent (≥90) si équité parfaite + bonne couverture + pas de répétitions."""
        from src.analysis import compute_quality_score

        # Mock metrics : équité parfaite (gap=0)
        metrics = PlanningMetrics(
            total_unique_pairs=45,
            total_repeat_pairs=0,
            unique_meetings_per_person=[10] * 10,
            min_unique=10,
            max_unique=10,
            mean_unique=10.0
        )

        # Mock stats : 100% couverture, 0 répétitions
        stats = {
            'total_pairs_met': 45,
            'total_possible_pairs': 45,
            'coverage_rate': 100.0,
            'repeat_pairs': 0,
            'max_meetings': 1
        }

        quality = compute_quality_score(metrics, stats)

        # Score devrait être 100 (40 + 30 + 30)
        assert quality['score'] == 100
        assert quality['grade'] == "Excellent"
        assert quality['emoji'] == "🟢"
        assert quality['color'] == "green"

    def test_score_excellent_gap_1(self):
        """Score excellent avec gap=1 (acceptable)."""
        from src.analysis import compute_quality_score

        # Équité gap=1 (acceptable)
        metrics = PlanningMetrics(
            total_unique_pairs=45,
            total_repeat_pairs=0,
            unique_meetings_per_person=[10] * 5 + [11] * 5,
            min_unique=10,
            max_unique=11,
            mean_unique=10.5
        )

        stats = {
            'total_pairs_met': 45,
            'total_possible_pairs': 45,
            'coverage_rate': 100.0,
            'repeat_pairs': 0,
            'max_meetings': 1
        }

        quality = compute_quality_score(metrics, stats)

        # Score = 40 (équité) + 30 (couverture) + 30 (répétitions) = 100
        assert quality['score'] == 100
        assert quality['grade'] == "Excellent"

    def test_score_bon_gap_2(self):
        """Score bon avec gap=2."""
        from src.analysis import compute_quality_score

        # Équité gap=2
        metrics = PlanningMetrics(
            total_unique_pairs=40,
            total_repeat_pairs=2,
            unique_meetings_per_person=[9] * 5 + [11] * 5,
            min_unique=9,
            max_unique=11,
            mean_unique=10.0
        )

        # Couverture moyenne, peu de répétitions
        stats = {
            'total_pairs_met': 40,
            'total_possible_pairs': 45,
            'coverage_rate': 88.9,  # 40/45
            'repeat_pairs': 2,
            'max_meetings': 2
        }

        quality = compute_quality_score(metrics, stats)

        # Score = 25 (gap=2) + 26.7 (88.9% couv) + 25 (2/45 = 4.4% < 5%) ≈ 77
        assert 70 <= quality['score'] < 90
        assert quality['grade'] == "Bon"
        assert quality['emoji'] == "🟡"

    def test_score_a_ameliorer_gap_3(self):
        """Score à améliorer avec gap=3."""
        from src.analysis import compute_quality_score

        # Équité gap=3
        metrics = PlanningMetrics(
            total_unique_pairs=30,
            total_repeat_pairs=10,
            unique_meetings_per_person=[8] * 5 + [11] * 5,
            min_unique=8,
            max_unique=11,
            mean_unique=9.5
        )

        # Couverture faible, beaucoup de répétitions
        stats = {
            'total_pairs_met': 30,
            'total_possible_pairs': 45,
            'coverage_rate': 66.7,  # 30/45
            'repeat_pairs': 10,
            'max_meetings': 3
        }

        quality = compute_quality_score(metrics, stats)

        # Score = 10 (gap=3) + 20 (66.7% couv) + 15 (10/45 = 22% ≥ 10%) ≈ 45
        assert quality['score'] < 70
        assert quality['grade'] == "À améliorer"
        assert quality['emoji'] == "🔴"

    def test_score_a_ameliorer_gap_4(self):
        """Score à améliorer avec gap≥4 (0 points équité)."""
        from src.analysis import compute_quality_score

        # Équité gap=4
        metrics = PlanningMetrics(
            total_unique_pairs=25,
            total_repeat_pairs=15,
            unique_meetings_per_person=[6] * 5 + [10] * 5,
            min_unique=6,
            max_unique=10,
            mean_unique=8.0
        )

        # Couverture moyenne, beaucoup de répétitions
        stats = {
            'total_pairs_met': 25,
            'total_possible_pairs': 45,
            'coverage_rate': 55.6,  # 25/45
            'repeat_pairs': 15,
            'max_meetings': 3
        }

        quality = compute_quality_score(metrics, stats)

        # Score = 0 (gap≥4) + 16.7 (55.6% couv) + 0 (15/45 = 33% ≥ 10%) ≈ 17
        assert quality['score'] < 70
        assert quality['grade'] == "À améliorer"

    def test_score_zero_coverage_zero_pairs(self):
        """Score avec 0 couverture (cas edge)."""
        from src.analysis import compute_quality_score

        # Aucune paire rencontrée
        metrics = PlanningMetrics(
            total_unique_pairs=0,
            total_repeat_pairs=0,
            unique_meetings_per_person=[0] * 10,
            min_unique=0,
            max_unique=0,
            mean_unique=0.0
        )

        stats = {
            'total_pairs_met': 0,
            'total_possible_pairs': 45,
            'coverage_rate': 0.0,
            'repeat_pairs': 0,
            'max_meetings': 0
        }

        quality = compute_quality_score(metrics, stats)

        # Score = 40 (gap=0) + 0 (0% couv) + 30 (0 répétitions) = 70
        assert quality['score'] == 70
        assert quality['grade'] == "Bon"  # Car 70 est limite

    def test_score_repeat_thresholds(self):
        """Tester seuils répétitions (0%, <5%, <10%, ≥10%)."""
        from src.analysis import compute_quality_score

        # Base metrics
        base_metrics = PlanningMetrics(
            total_unique_pairs=45,
            total_repeat_pairs=0,
            unique_meetings_per_person=[10] * 10,
            min_unique=10,
            max_unique=10,
            mean_unique=10.0
        )

        # 0% répétitions → 30 pts
        stats_0 = {
            'total_pairs_met': 45,
            'total_possible_pairs': 45,
            'coverage_rate': 100.0,
            'repeat_pairs': 0,
            'max_meetings': 1
        }
        q0 = compute_quality_score(base_metrics, stats_0)
        assert q0['score'] == 100  # 40 + 30 + 30

        # 4% répétitions (< 5%) → 25 pts
        stats_4 = {
            'total_pairs_met': 45,
            'total_possible_pairs': 45,
            'coverage_rate': 100.0,
            'repeat_pairs': 1,  # 1/45 = 2.2%
            'max_meetings': 2
        }
        q4 = compute_quality_score(base_metrics, stats_4)
        assert q4['score'] == 95  # 40 + 30 + 25

        # 9% répétitions (< 10%) → 15 pts
        stats_9 = {
            'total_pairs_met': 45,
            'total_possible_pairs': 45,
            'coverage_rate': 100.0,
            'repeat_pairs': 4,  # 4/45 = 8.9%
            'max_meetings': 2
        }
        q9 = compute_quality_score(base_metrics, stats_9)
        assert q9['score'] == 85  # 40 + 30 + 15

    def test_realistic_planning_integration(self):
        """Test avec planning réaliste généré."""
        from src.analysis import compute_quality_score

        config = PlanningConfig(N=12, X=3, x=4, S=4)
        planning = generate_baseline(config, seed=42)

        # Calculer métriques et stats
        from src.metrics import compute_metrics
        metrics = compute_metrics(planning, config)

        matrix = compute_meetings_matrix(planning, config.N)
        stats = compute_matrix_statistics(matrix)

        quality = compute_quality_score(metrics, stats)

        # Vérifications générales
        assert 0 <= quality['score'] <= 100
        assert quality['grade'] in ["Excellent", "Bon", "À améliorer"]
        assert quality['emoji'] in ["🟢", "🟡", "🔴"]
        assert quality['color'] in ["green", "yellow", "red"]

        # Cohérence grade/emoji/color
        if quality['grade'] == "Excellent":
            assert quality['score'] >= 90
            assert quality['emoji'] == "🟢"
            assert quality['color'] == "green"
        elif quality['grade'] == "Bon":
            assert 70 <= quality['score'] < 90
            assert quality['emoji'] == "🟡"
            assert quality['color'] == "yellow"
        else:  # À améliorer
            assert quality['score'] < 70
            assert quality['emoji'] == "🔴"
            assert quality['color'] == "red"
