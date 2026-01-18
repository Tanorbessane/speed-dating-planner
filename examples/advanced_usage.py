#!/usr/bin/env python3
"""Exemple d'utilisation avancée - Comparaison baseline vs optimisé.

Cet exemple montre comment:
    1. Générer un planning baseline
    2. Générer un planning optimisé complet
    3. Comparer les métriques (répétitions, équité)

Usage:
    python examples/advanced_usage.py
"""

import logging

from src.baseline import generate_baseline
from src.metrics import compute_metrics
from src.models import PlanningConfig
from src.planner import generate_optimized_planning

# Configuration logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Comparaison baseline vs optimisé."""
    # Configuration
    logger.info("=== Configuration ===")
    config = PlanningConfig(
        N=30,  # 30 participants
        X=5,  # 5 tables
        x=6,  # 6 places par table
        S=6,  # 6 sessions
    )
    logger.info(f"Configuration : {config.N} participants, {config.S} sessions\n")

    # 1. Génération BASELINE (Phase 1 uniquement)
    logger.info("=== BASELINE (Round-robin rapide) ===")
    baseline = generate_baseline(config, seed=42)
    metrics_baseline = compute_metrics(baseline, config)

    logger.info(f"Paires uniques créées    : {metrics_baseline.total_unique_pairs}")
    logger.info(f"Répétitions              : {metrics_baseline.total_repeat_pairs}")
    logger.info(
        f"Rencontres par personne  : min={metrics_baseline.min_unique}, "
        f"max={metrics_baseline.max_unique}, "
        f"moyenne={metrics_baseline.mean_unique:.1f}"
    )
    logger.info(f"Équité (écart max-min)   : {metrics_baseline.equity_gap}")

    if metrics_baseline.equity_gap <= 1:
        logger.info("✓ Équité satisfaisante (baseline)")
    else:
        logger.warning(f"⚠ Équité à améliorer (gap = {metrics_baseline.equity_gap})")

    # 2. Génération OPTIMISÉE (Pipeline complet 3 phases)
    logger.info("\n=== OPTIMISÉ (Pipeline complet) ===")
    optimized, metrics_optimized = generate_optimized_planning(config, seed=42)

    # 3. Comparaison
    logger.info("\n=== COMPARAISON BASELINE vs OPTIMISÉ ===")

    # Répétitions
    reduction_repeats = (
        metrics_baseline.total_repeat_pairs - metrics_optimized.total_repeat_pairs
    )
    reduction_pct = (
        100 * reduction_repeats / max(metrics_baseline.total_repeat_pairs, 1)
    )

    logger.info(
        f"Répétitions : {metrics_baseline.total_repeat_pairs} → "
        f"{metrics_optimized.total_repeat_pairs} "
        f"(réduction {reduction_pct:.1f}%)"
    )

    # Équité
    equity_improvement = metrics_baseline.equity_gap - metrics_optimized.equity_gap

    logger.info(
        f"Équité (gap) : {metrics_baseline.equity_gap} → "
        f"{metrics_optimized.equity_gap} "
        f"(amélioration {equity_improvement})"
    )

    # Garantie FR6
    if metrics_optimized.equity_gap <= 1:
        logger.info("✓ FR6 garanti : equity_gap ≤ 1")
    else:
        logger.error(f"❌ FR6 violé : equity_gap = {metrics_optimized.equity_gap}")

    # Résumé
    logger.info("\n=== RÉSUMÉ ===")
    if (
        reduction_repeats >= 0
        and metrics_optimized.equity_gap <= 1
        and equity_improvement >= 0
    ):
        logger.info("✅ Optimisation réussie :")
        logger.info(f"   • Répétitions réduites de {reduction_pct:.1f}%")
        logger.info(f"   • Équité garantie (gap = {metrics_optimized.equity_gap})")
    else:
        logger.warning("⚠ Optimisation n'a pas amélioré tous les aspects")

    logger.info("\n=== Terminé ===")


if __name__ == "__main__":
    main()
