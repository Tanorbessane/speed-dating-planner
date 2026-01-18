"""Tests de performance pour Epic 2 (NFR1-NFR3).

Ces tests vérifient les performances du pipeline optimisé complet.

Performance targets:
    - NFR1: N=100 en <2s
    - NFR2: N=300 en <5s
    - NFR3: N=1000 en <30s
"""

import time

import pytest

from src.models import PlanningConfig
from src.planner import generate_optimized_planning


class TestPerformance:
    """Tests de performance (marqués @pytest.mark.slow)."""

    @pytest.mark.slow
    def test_nfr1_n100_under_2s(self) -> None:
        """NFR1: N=100 doit s'exécuter en <2s."""
        config = PlanningConfig(N=100, X=20, x=5, S=10)

        start = time.time()
        planning, metrics = generate_optimized_planning(config, seed=42)
        duration = time.time() - start

        # Vérifications fonctionnelles
        assert len(planning.sessions) == 10
        assert metrics.equity_gap <= 1  # FR6

        # Performance NFR1
        assert duration < 2.0, f"NFR1 violé: {duration:.3f}s > 2s"
        print(f"✓ NFR1: N=100 en {duration:.3f}s")

    @pytest.mark.slow
    def test_nfr2_n300_under_5s(self) -> None:
        """NFR2: N=300 doit s'exécuter en <5s."""
        config = PlanningConfig(N=300, X=60, x=5, S=15)

        start = time.time()
        planning, metrics = generate_optimized_planning(config, seed=42)
        duration = time.time() - start

        # Vérifications fonctionnelles
        assert len(planning.sessions) == 15
        assert metrics.equity_gap <= 1  # FR6

        # Performance NFR2
        assert duration < 5.0, f"NFR2 violé: {duration:.3f}s > 5s"
        print(f"✓ NFR2: N=300 en {duration:.3f}s")

    @pytest.mark.slow
    def test_nfr3_n1000_under_30s(self) -> None:
        """NFR3: N=1000 doit s'exécuter en <30s."""
        config = PlanningConfig(N=1000, X=200, x=5, S=20)

        start = time.time()
        planning, metrics = generate_optimized_planning(config, seed=42)
        duration = time.time() - start

        # Vérifications fonctionnelles
        assert len(planning.sessions) == 20
        assert metrics.equity_gap <= 1  # FR6

        # Performance NFR3
        assert duration < 30.0, f"NFR3 violé: {duration:.3f}s > 30s"
        print(f"✓ NFR3: N=1000 en {duration:.3f}s")

    @pytest.mark.slow
    def test_small_config_very_fast(self) -> None:
        """Test que petites configs sont très rapides (<0.5s)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)

        start = time.time()
        planning, metrics = generate_optimized_planning(config, seed=42)
        duration = time.time() - start

        assert duration < 0.5, f"Trop lent pour N=30: {duration:.3f}s"
        print(f"✓ N=30 en {duration:.3f}s")
