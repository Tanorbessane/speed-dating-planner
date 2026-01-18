"""Tests unitaires pour les exporteurs (src.exporters).

Test coverage:
    - Export CSV (FR10)
    - Export JSON (FR11)
    - Encodage UTF-8 BOM
    - Gestion chemins spéciaux
    - Écrasement fichiers
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from src.exporters import export_to_csv, export_to_json
from src.models import Planning, PlanningConfig, Session


class TestExportToCSV:
    """Tests pour export_to_csv()."""

    def test_export_success(self) -> None:
        """Test export CSV réussit sans erreur."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        # Export
        export_to_csv(planning, config, filepath)

        # Vérifier fichier créé
        assert Path(filepath).exists()

        # Cleanup
        Path(filepath).unlink()

    def test_correct_number_of_lines(self) -> None:
        """Test nombre de lignes correct (header + N×S data rows)."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Compter lignes
        with open(filepath, encoding="utf-8-sig") as f:
            lines = f.readlines()

        # Header + 6 participants × 2 sessions = 1 + 12
        assert len(lines) == 13

        # Cleanup
        Path(filepath).unlink()

    def test_csv_readable_with_dictreader(self) -> None:
        """Test lecture CSV avec csv.DictReader fonctionne."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Lire avec DictReader
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Vérifier colonnes FR10
        assert len(rows) == 12
        assert all("session_id" in row for row in rows)
        assert all("table_id" in row for row in rows)
        assert all("participant_id" in row for row in rows)

        # Cleanup
        Path(filepath).unlink()

    def test_correct_values(self) -> None:
        """Test valeurs correctes pour planning connu."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        # Session 0: table 0 = {0,1}, table 1 = {2,3}
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Lire données
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Vérifier valeurs attendues
        # Session 0, table 0: participants 0 et 1
        # Session 0, table 1: participants 2 et 3
        expected_data = [
            {"session_id": "0", "table_id": "0", "participant_id": "0"},
            {"session_id": "0", "table_id": "0", "participant_id": "1"},
            {"session_id": "0", "table_id": "1", "participant_id": "2"},
            {"session_id": "0", "table_id": "1", "participant_id": "3"},
        ]

        assert len(rows) == 4
        for i, expected in enumerate(expected_data):
            assert rows[i] == expected

        # Cleanup
        Path(filepath).unlink()

    def test_utf8_bom_present(self) -> None:
        """Test encodage UTF-8 avec BOM (compatibilité Excel)."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Lire en mode binaire pour vérifier BOM
        with open(filepath, "rb") as f:
            first_bytes = f.read(3)

        # UTF-8 BOM = 0xEF 0xBB 0xBF
        assert first_bytes == b"\xef\xbb\xbf"

        # Cleanup
        Path(filepath).unlink()

    def test_path_with_spaces(self) -> None:
        """Test gestion chemin avec espaces."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        # Créer fichier temporaire avec espaces dans le nom
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=" test planning.csv"
        ) as f:
            filepath = f.name

        # Export doit réussir
        export_to_csv(planning, config, filepath)

        assert Path(filepath).exists()

        # Cleanup
        Path(filepath).unlink()

    def test_path_with_accents(self) -> None:
        """Test gestion chemin avec caractères accentués."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        # Créer fichier temporaire avec accents
        import tempfile
        import os

        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, "planníng_été.csv")

        # Export doit réussir
        export_to_csv(planning, config, filepath)

        assert Path(filepath).exists()

        # Cleanup
        Path(filepath).unlink()

    def test_overwrite_existing_file(self, caplog) -> None:
        """Test écrasement fichier existant avec warning loggé."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        # Créer fichier initial
        Path(filepath).write_text("old content")

        # Export (doit écraser)
        with caplog.at_level("WARNING"):
            export_to_csv(planning, config, filepath)

        # Vérifier warning loggé
        assert "écrasé" in caplog.text.lower()

        # Vérifier nouveau contenu
        with open(filepath, encoding="utf-8-sig") as f:
            content = f.read()
        assert "session_id" in content
        assert "old content" not in content

        # Cleanup
        Path(filepath).unlink()

    def test_sorted_participants_determinism(self) -> None:
        """Test participants triés pour déterminisme."""
        config = PlanningConfig(N=4, X=1, x=4, S=1)
        # Table avec ordre non trié
        sessions = [Session(0, [{3, 1, 2, 0}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Lire données
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Vérifier ordre trié (0, 1, 2, 3)
        participant_ids = [int(row["participant_id"]) for row in rows]
        assert participant_ids == [0, 1, 2, 3]

        # Cleanup
        Path(filepath).unlink()

    def test_multiple_sessions(self) -> None:
        """Test export multi-sessions."""
        config = PlanningConfig(N=6, X=2, x=3, S=3)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
            Session(2, [{0, 2, 5}, {1, 3, 4}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Lire données
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Vérifier sessions présentes
        session_ids = set(int(row["session_id"]) for row in rows)
        assert session_ids == {0, 1, 2}

        # Vérifier nombre total lignes (6 participants × 3 sessions)
        assert len(rows) == 18

        # Cleanup
        Path(filepath).unlink()

    def test_partial_tables(self) -> None:
        """Test export avec tables partielles (FR7)."""
        config = PlanningConfig(N=7, X=3, x=3, S=1)
        # 7 participants, 3 tables → tailles [3, 2, 2]
        sessions = [Session(0, [{0, 1, 2}, {3, 4}, {5, 6}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as f:
            filepath = f.name

        export_to_csv(planning, config, filepath)

        # Lire données
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Vérifier tous participants exportés
        participant_ids = set(int(row["participant_id"]) for row in rows)
        assert participant_ids == {0, 1, 2, 3, 4, 5, 6}

        # Cleanup
        Path(filepath).unlink()


class TestExportToJSON:
    """Tests pour export_to_json()."""

    def test_export_success(self) -> None:
        """Test export JSON réussit sans erreur."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        export_to_json(planning, config, filepath)
        assert Path(filepath).exists()
        Path(filepath).unlink()

    def test_json_valid_and_parsable(self) -> None:
        """Test JSON produit est valide et parsable."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        export_to_json(planning, config, filepath)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert "sessions" in data
        Path(filepath).unlink()

    def test_structure_fr11_compliant(self) -> None:
        """Test structure JSON conforme FR11."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
        ]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        export_to_json(planning, config, filepath)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        assert len(data["sessions"]) == 2

        session0 = data["sessions"][0]
        assert session0["session_id"] == 0
        assert "tables" in session0

        table0 = session0["tables"][0]
        assert "table_id" in table0
        assert "participants" in table0
        assert isinstance(table0["participants"], list)

        Path(filepath).unlink()

    def test_metadata_included_by_default(self) -> None:
        """Test metadata incluse par défaut."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        export_to_json(planning, config, filepath)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["config"]["N"] == 6
        assert data["metadata"]["total_participants"] == 6

        Path(filepath).unlink()

    def test_metadata_excluded_when_false(self) -> None:
        """Test metadata absente si include_metadata=False."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        export_to_json(planning, config, filepath, include_metadata=False)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" not in data
        Path(filepath).unlink()
