#!/usr/bin/env python3
"""Exemple d'utilisation basique de l'API Speed Dating Planner.

Cet exemple montre comment:
    1. Créer une configuration
    2. Générer un planning baseline
    3. Calculer les métriques de qualité

Usage:
    python examples/basic_usage.py
"""

import logging

from src.baseline import generate_baseline
from src.metrics import compute_metrics
from src.models import PlanningConfig
from src.validation import validate_config

# Configuration logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Exemple basique de génération de planning."""
    # 1. Créer configuration
    logger.info("=== Configuration ===")
    config = PlanningConfig(
        N=30,  # 30 participants
        X=5,  # 5 tables
        x=6,  # 6 places par table
        S=6,  # 6 sessions
    )
    logger.info(f"Configuration : {config.N} participants, {config.X} tables")

    # 2. Valider configuration
    logger.info("\n=== Validation ===")
    validate_config(config)
    logger.info("✓ Configuration valide")

    # 3. Générer planning baseline
    logger.info("\n=== Génération Planning Baseline ===")
    planning = generate_baseline(config, seed=42)
    logger.info(f"✓ Planning généré : {len(planning.sessions)} sessions")

    # 4. Afficher aperçu première session
    session0 = planning.sessions[0]
    logger.info(f"\nSession 0 : {len(session0.tables)} tables")
    for table_id, table in enumerate(session0.tables):
        participants = sorted(list(table))
        logger.info(f"  Table {table_id}: {participants}")

    # 5. Calculer métriques
    logger.info("\n=== Métriques de Qualité ===")
    metrics = compute_metrics(planning, config)

    logger.info(f"Paires uniques créées    : {metrics.total_unique_pairs}")
    logger.info(f"Répétitions              : {metrics.total_repeat_pairs}")
    logger.info(
        f"Rencontres par personne  : min={metrics.min_unique}, "
        f"max={metrics.max_unique}, moyenne={metrics.mean_unique:.1f}"
    )
    logger.info(f"Équité (écart max-min)   : {metrics.equity_gap}")

    if metrics.equity_gap <= 1:
        logger.info("✓ Équité respectée (écart ≤ 1)")
    else:
        logger.warning(f"⚠ Équité à améliorer (écart = {metrics.equity_gap})")

    logger.info("\n=== Terminé ===")


if __name__ == "__main__":
    main()
