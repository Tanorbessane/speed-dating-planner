"""Tests unitaires pour display_utils (Story 5.1).

Ce module teste les fonctions helper d'affichage des noms de participants.
"""

import pytest
import pandas as pd
from src.display_utils import get_participant_display_name, format_table_participants


class TestGetParticipantDisplayName:
    """Tests pour get_participant_display_name()."""

    def test_with_prenom(self):
        """Participant avec prénom."""
        df = pd.DataFrame({
            "id": [0],
            "nom": ["Dupont"],
            "prenom": ["Jean"],
            "is_vip": [False]
        })
        assert get_participant_display_name(0, df) == "Jean Dupont"

    def test_without_prenom(self):
        """Participant sans prénom."""
        df = pd.DataFrame({
            "id": [0],
            "nom": ["Dupont"],
            "prenom": [None],
            "is_vip": [False]
        })
        assert get_participant_display_name(0, df) == "Dupont"

    def test_participant_not_found(self):
        """Participant introuvable."""
        df = pd.DataFrame({
            "id": [0],
            "nom": ["Dupont"],
            "prenom": ["Jean"],
            "is_vip": [False]
        })
        assert get_participant_display_name(99, df) == "Participant #99"

    def test_no_dataframe(self):
        """Pas de DataFrame participants."""
        assert get_participant_display_name(5, None) == "Participant #5"

    def test_empty_dataframe(self):
        """DataFrame vide."""
        df = pd.DataFrame(columns=["id", "nom", "prenom", "is_vip"])
        assert get_participant_display_name(0, df) == "Participant #0"

    def test_vip_badge(self):
        """Badge VIP affiché."""
        df = pd.DataFrame({
            "id": [0],
            "nom": ["Dupont"],
            "prenom": ["Jean"],
            "is_vip": [True]
        })
        result = get_participant_display_name(0, df, include_vip_badge=True)
        assert result == "⭐ Jean Dupont"

    def test_vip_badge_not_vip(self):
        """Badge VIP non affiché si pas VIP."""
        df = pd.DataFrame({
            "id": [0],
            "nom": ["Dupont"],
            "prenom": ["Jean"],
            "is_vip": [False]
        })
        result = get_participant_display_name(0, df, include_vip_badge=True)
        assert result == "Jean Dupont"

    def test_multiple_participants(self):
        """DataFrame avec plusieurs participants."""
        df = pd.DataFrame({
            "id": [0, 1, 2],
            "nom": ["Dupont", "Martin", "Bernard"],
            "prenom": ["Jean", "Marie", None],
            "is_vip": [False, True, False]
        })

        assert get_participant_display_name(0, df) == "Jean Dupont"
        assert get_participant_display_name(1, df) == "Marie Martin"
        assert get_participant_display_name(2, df) == "Bernard"
        assert get_participant_display_name(1, df, include_vip_badge=True) == "⭐ Marie Martin"


class TestFormatTableParticipants:
    """Tests pour format_table_participants()."""

    def test_with_participants_df(self):
        """Format avec DataFrame participants."""
        df = pd.DataFrame({
            "id": [0, 1, 2],
            "nom": ["Dupont", "Martin", "Bernard"],
            "prenom": ["Jean", "Marie", "Luc"],
            "is_vip": [False, False, False]
        })
        table = {0, 1, 2}

        result = format_table_participants(table, df)
        assert result == "Jean Dupont, Marie Martin, Luc Bernard"

    def test_without_participants_df(self):
        """Format sans DataFrame (fallback IDs)."""
        table = {5, 3, 7}

        result = format_table_participants(table, None)
        assert result == "3, 5, 7"  # Triés

    def test_empty_dataframe(self):
        """Format avec DataFrame vide (fallback IDs)."""
        df = pd.DataFrame(columns=["id", "nom", "prenom"])
        table = {1, 2, 3}

        result = format_table_participants(table, df)
        assert result == "1, 2, 3"

    def test_with_vip_badge(self):
        """Format avec badges VIP."""
        df = pd.DataFrame({
            "id": [0, 1, 2],
            "nom": ["Dupont", "Martin", "Bernard"],
            "prenom": ["Jean", "Marie", "Luc"],
            "is_vip": [True, False, True]
        })
        table = {0, 1, 2}

        result = format_table_participants(table, df, include_vip_badge=True)
        assert result == "⭐ Jean Dupont, Marie Martin, ⭐ Luc Bernard"

    def test_custom_separator(self):
        """Format avec séparateur custom."""
        df = pd.DataFrame({
            "id": [0, 1],
            "nom": ["Dupont", "Martin"],
            "prenom": ["Jean", "Marie"],
            "is_vip": [False, False]
        })
        table = {0, 1}

        result = format_table_participants(table, df, separator=" | ")
        assert result == "Jean Dupont | Marie Martin"

    def test_sorted_output(self):
        """Output est trié par ID."""
        df = pd.DataFrame({
            "id": [10, 5, 15, 3],
            "nom": ["A", "B", "C", "D"],
            "prenom": ["A", "B", "C", "D"],
            "is_vip": [False, False, False, False]
        })
        table = {15, 3, 10, 5}

        result = format_table_participants(table, df)
        # IDs triés: 3, 5, 10, 15
        assert result == "D D, B B, A A, C C"

    def test_participant_not_in_df(self):
        """Participant dans table mais pas dans DataFrame."""
        df = pd.DataFrame({
            "id": [0, 1],
            "nom": ["Dupont", "Martin"],
            "prenom": ["Jean", "Marie"],
            "is_vip": [False, False]
        })
        table = {0, 1, 99}  # 99 n'existe pas

        result = format_table_participants(table, df)
        assert result == "Jean Dupont, Marie Martin, Participant #99"


class TestIntegration:
    """Tests d'intégration Story 5.1."""

    def test_full_workflow(self):
        """Workflow complet : import CSV → affichage noms."""
        # Simuler participants importés
        participants_df = pd.DataFrame({
            "id": list(range(6)),
            "nom": ["Dupont", "Martin", "Bernard", "Durand", "Petit", "Roux"],
            "prenom": ["Jean", "Marie", "Luc", "Sophie", "Paul", "Emma"],
            "is_vip": [True, False, False, True, False, False]
        })

        # Simuler table planning
        table1 = {0, 1, 2}
        table2 = {3, 4, 5}

        # Vérifier affichage
        display1 = format_table_participants(table1, participants_df, include_vip_badge=True)
        display2 = format_table_participants(table2, participants_df, include_vip_badge=True)

        assert display1 == "⭐ Jean Dupont, Marie Martin, Luc Bernard"
        assert display2 == "⭐ Sophie Durand, Paul Petit, Emma Roux"

    def test_backward_compatibility(self):
        """Backward compatibility sans participants."""
        table = {5, 10, 15}

        # Sans participants_df, affiche IDs
        result = format_table_participants(table, None)
        assert result == "5, 10, 15"

        # get_participant_display_name aussi compatible
        assert get_participant_display_name(10, None) == "Participant #10"
