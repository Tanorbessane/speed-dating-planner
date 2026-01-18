"""Tests unitaires pour module pdf_exporter (Story 5.4).

Ce module teste l'export PDF des plannings.

Note: Tests basiques pour vérifier absence de crash.
      Tests visuels manuels requis pour validation complète.
"""

import pytest
from io import BytesIO
from src.models import PlanningConfig
from src.baseline import generate_baseline
from src.metrics import compute_metrics


class TestExportToPDF:
    """Tests pour export_to_pdf() (Story 5.4)."""

    def test_pdf_generation_basic(self):
        """Test génération PDF basique sans crash."""
        from src.pdf_exporter import export_to_pdf

        config = PlanningConfig(N=10, X=2, x=5, S=3)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        pdf_bytes = export_to_pdf(planning, config, metrics, participants_df=None)

        # Vérifier PDF généré
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, BytesIO)

        # Vérifier contenu commence par header PDF
        pdf_content = pdf_bytes.getvalue()
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF')  # Header PDF standard

    def test_pdf_generation_small_planning(self):
        """Test PDF avec petit planning (N=6)."""
        from src.pdf_exporter import export_to_pdf

        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        pdf_bytes = export_to_pdf(planning, config, metrics)

        assert pdf_bytes is not None
        assert len(pdf_bytes.getvalue()) > 1000  # PDF doit avoir contenu substantiel

    def test_pdf_generation_medium_planning(self):
        """Test PDF avec planning moyen (N=30)."""
        from src.pdf_exporter import export_to_pdf

        config = PlanningConfig(N=30, X=5, x=6, S=6)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        pdf_bytes = export_to_pdf(planning, config, metrics)

        assert pdf_bytes is not None
        assert pdf_bytes.getvalue().startswith(b'%PDF')

    def test_pdf_with_participants_names(self):
        """Test PDF avec noms participants."""
        import pandas as pd
        from src.pdf_exporter import export_to_pdf

        config = PlanningConfig(N=6, X=2, x=3, S=2)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        # Mock participants DataFrame
        participants_df = pd.DataFrame({
            "id": list(range(6)),
            "nom": ["A", "B", "C", "D", "E", "F"],
            "prenom": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
            "is_vip": [False] * 6
        })

        pdf_bytes = export_to_pdf(planning, config, metrics, participants_df)

        assert pdf_bytes is not None
        assert pdf_bytes.getvalue().startswith(b'%PDF')

    @pytest.mark.skipif(True, reason="Test manuel - trop long pour CI")
    def test_pdf_large_planning(self):
        """Test PDF avec grand planning (N=100) - Skip en CI."""
        from src.pdf_exporter import export_to_pdf

        config = PlanningConfig(N=100, X=20, x=5, S=10)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        pdf_bytes = export_to_pdf(planning, config, metrics)

        assert pdf_bytes is not None

    def test_pdf_format_table_participants_list(self):
        """Test helper _format_table_participants_list."""
        from src.pdf_exporter import _format_table_participants_list

        table = {0, 1, 2}

        # Sans participants
        result = _format_table_participants_list(table, participants_df=None)
        assert "Participant" in result or "P0" in result

        # Avec participants
        import pandas as pd
        participants_df = pd.DataFrame({
            "id": [0, 1, 2],
            "nom": ["A", "B", "C"],
            "prenom": ["Alice", "Bob", "Charlie"],
            "is_vip": [False, False, False]
        })

        result = _format_table_participants_list(table, participants_df)
        assert "Alice" in result or "Bob" in result or "Charlie" in result


class TestIntegration:
    """Tests d'intégration export PDF (Story 5.4)."""

    def test_full_workflow_pdf_export(self):
        """Workflow complet : génération → métriques → PDF."""
        from src.pdf_exporter import export_to_pdf

        config = PlanningConfig(N=12, X=3, x=4, S=4)
        planning = generate_baseline(config, seed=42)
        metrics = compute_metrics(planning, config)

        # Générer PDF
        pdf_bytes = export_to_pdf(planning, config, metrics)

        # Vérifications
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, BytesIO)

        pdf_content = pdf_bytes.getvalue()
        assert len(pdf_content) > 5000  # PDF substantiel
        assert pdf_content.startswith(b'%PDF')
        assert pdf_content.endswith(b'%%EOF\n')  # PDF bien formé
