"""Tests end-to-end pour CLI (src.cli).

Test coverage:
    - Parse arguments (requis + optionnels)
    - Exit codes (0, 1, 2, 3)
    - Export formats (CSV, JSON)
    - Gestion erreurs (config invalide, I/O)
    - Mode verbeux
    - Déterminisme (même seed → même output)
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCLIArguments:
    """Tests parsing arguments CLI."""

    def test_required_args_present(self) -> None:
        """Test arguments requis présents."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert Path(filepath).exists()
        Path(filepath).unlink()

    def test_missing_required_arg_fails(self) -> None:
        """Test argument requis manquant échoue."""
        # Manque -s (sessions)
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "-n", "6", "-t", "2", "-c", "3"],
            capture_output=True,
            text=True,
        )

        # argparse renvoie exit code 2 pour erreur args
        assert result.returncode == 2

    def test_help_message_works(self) -> None:
        """Test --help affiche aide."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "speed-dating-planner" in result.stdout
        assert "participants" in result.stdout

    def test_optional_seed_accepted(self) -> None:
        """Test argument optionnel --seed accepté."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "4",
                "-t",
                "2",
                "-c",
                "2",
                "-s",
                "1",
                "-o",
                filepath,
                "--seed",
                "123",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        Path(filepath).unlink()

    def test_verbose_flag_works(self) -> None:
        """Test flag -v active mode verbeux."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "4",
                "-t",
                "2",
                "-c",
                "2",
                "-s",
                "1",
                "-o",
                filepath,
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Mode verbeux affiche plus de logs
        assert "DEBUG" in result.stderr or "Configuration" in result.stderr
        Path(filepath).unlink()


class TestCLIExitCodes:
    """Tests exit codes selon spécification."""

    def test_exit_0_on_success(self) -> None:
        """Test exit code 0 pour succès."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        Path(filepath).unlink()

    def test_exit_1_on_invalid_config(self) -> None:
        """Test exit code 1 pour config invalide."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        # N=1 invalide (minimum 2)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "1",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Configuration invalide" in result.stderr or "invalide" in result.stderr

    def test_exit_2_on_io_error(self) -> None:
        """Test exit code 2 pour erreur I/O."""
        # Chemin invalide (répertoire inexistant)
        invalid_path = "/nonexistent_dir_12345/planning.csv"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                invalid_path,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "I/O" in result.stderr or "Erreur" in result.stderr


class TestCLIExportFormats:
    """Tests formats export (CSV, JSON)."""

    def test_csv_export_default(self) -> None:
        """Test export CSV par défaut."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert Path(filepath).exists()

        # Vérifier contenu CSV
        content = Path(filepath).read_text(encoding="utf-8-sig")
        assert "session_id" in content
        assert "table_id" in content
        assert "participant_id" in content

        Path(filepath).unlink()

    def test_csv_export_explicit(self) -> None:
        """Test export CSV explicite avec -f csv."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "4",
                "-t",
                "2",
                "-c",
                "2",
                "-s",
                "1",
                "-o",
                filepath,
                "-f",
                "csv",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert Path(filepath).exists()
        Path(filepath).unlink()

    def test_json_export(self) -> None:
        """Test export JSON avec -f json."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath,
                "-f",
                "json",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert Path(filepath).exists()

        # Vérifier contenu JSON
        import json

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert "sessions" in data
        assert "metadata" in data  # include_metadata=True par défaut
        assert data["metadata"]["config"]["N"] == 6

        Path(filepath).unlink()

    def test_invalid_format_rejected(self) -> None:
        """Test format invalide rejeté par argparse."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                "out.txt",
                "-f",
                "xml",
            ],
            capture_output=True,
            text=True,
        )

        # argparse exit code 2 pour choix invalide
        assert result.returncode == 2
        assert "invalid choice" in result.stderr or "invalide" in result.stderr


class TestCLIDeterminism:
    """Tests déterminisme (stabilité outputs)."""

    def test_same_seed_same_output_csv(self) -> None:
        """Test même seed produit même CSV."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="_1.csv"
        ) as f1:
            filepath1 = f1.name
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="_2.csv"
        ) as f2:
            filepath2 = f2.name

        # Génération 1
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath1,
                "--seed",
                "42",
            ],
            check=True,
        )

        # Génération 2 (même seed)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath2,
                "--seed",
                "42",
            ],
            check=True,
        )

        # Comparer contenus
        content1 = Path(filepath1).read_text()
        content2 = Path(filepath2).read_text()

        assert content1 == content2

        Path(filepath1).unlink()
        Path(filepath2).unlink()

    def test_different_seed_different_output(self) -> None:
        """Test seeds différents produisent outputs différents."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="_a.csv"
        ) as f1:
            filepath1 = f1.name
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="_b.csv"
        ) as f2:
            filepath2 = f2.name

        # Génération avec seed=42
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath1,
                "--seed",
                "42",
            ],
            check=True,
        )

        # Génération avec seed=123
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath2,
                "--seed",
                "123",
            ],
            check=True,
        )

        # Contenus doivent différer
        content1 = Path(filepath1).read_text()
        content2 = Path(filepath2).read_text()

        assert content1 != content2

        Path(filepath1).unlink()
        Path(filepath2).unlink()


class TestCLIIntegration:
    """Tests intégration end-to-end."""

    def test_full_workflow_csv(self) -> None:
        """Test workflow complet : génération → export CSV → validation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        # Générer planning
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "9",
                "-t",
                "3",
                "-c",
                "3",
                "-s",
                "3",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Vérifier fichier créé
        assert Path(filepath).exists()

        # Lire et valider CSV
        import csv

        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # 9 participants × 3 sessions = 27 lignes
        assert len(rows) == 27

        # Vérifier colonnes FR10
        assert all("session_id" in row for row in rows)
        assert all("table_id" in row for row in rows)
        assert all("participant_id" in row for row in rows)

        Path(filepath).unlink()

    def test_full_workflow_json(self) -> None:
        """Test workflow complet : génération → export JSON → validation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        # Générer planning
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "6",
                "-t",
                "2",
                "-c",
                "3",
                "-s",
                "2",
                "-o",
                filepath,
                "-f",
                "json",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Vérifier fichier créé
        assert Path(filepath).exists()

        # Lire et valider JSON
        import json

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # Structure FR11
        assert "sessions" in data
        assert len(data["sessions"]) == 2

        # Metadata présente
        assert "metadata" in data
        assert data["metadata"]["config"]["N"] == 6
        assert data["metadata"]["total_sessions"] == 2

        Path(filepath).unlink()

    def test_success_message_french(self) -> None:
        """Test messages succès en français (NFR10)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "4",
                "-t",
                "2",
                "-c",
                "2",
                "-s",
                "1",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Vérifier messages français
        assert "Configuration" in result.stderr or "succès" in result.stderr

        Path(filepath).unlink()

    def test_overwrite_existing_file(self) -> None:
        """Test écrasement fichier existant."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        # Créer fichier initial
        Path(filepath).write_text("old content")

        # Générer planning (doit écraser)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli",
                "-n",
                "4",
                "-t",
                "2",
                "-c",
                "2",
                "-s",
                "1",
                "-o",
                filepath,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Vérifier nouveau contenu
        content = Path(filepath).read_text()
        assert "session_id" in content
        assert "old content" not in content

        Path(filepath).unlink()
