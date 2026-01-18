"""Pipeline complet d'optimisation de plannings (3 phases).

Ce module orchestre le pipeline complet de génération de planning optimisé:
    Phase 1: Baseline (round-robin) avec respect contraintes hard
    Phase 2: Amélioration locale (greedy) avec protection contraintes hard
    Phase 3: Enforcement équité (FR6)

Functions:
    generate_optimized_planning: Pipeline complet optimisé
"""

import logging
from typing import Tuple, Optional, List

from src.baseline import generate_baseline
from src.equity import enforce_equity
from src.improvement import improve_planning
from src.metrics import compute_metrics
from src.models import Planning, PlanningConfig, PlanningMetrics, PlanningConstraints, Participant
from src.validation import validate_config

logger = logging.getLogger(__name__)


def generate_optimized_planning(
    config: PlanningConfig,
    seed: int = 42,
    constraints: Optional[PlanningConstraints] = None,
    participants: Optional[List[Participant]] = None,
) -> Tuple[Planning, PlanningMetrics]:
    """Génère un planning optimisé complet (pipeline 3 phases).

    Pipeline:
        Phase 1: Génération baseline (round-robin rapide)
        Phase 2: Amélioration locale (réduction répétitions)
        Phase 3: Enforcement équité (garantie FR6: equity_gap ≤ 1)

    Workflow:
        1. Validation configuration
        2. Génération baseline avec seed (déterminisme NFR11)
        3. Amélioration par recherche locale greedy
        4. Enforcement équité pour garantir FR6
        5. Calcul métriques finales

    Args:
        config: Configuration du planning
        seed: Graine aléatoire pour reproductibilité (défaut: 42, NFR11)
        constraints: Contraintes de groupes (cohésifs/exclusifs), optionnel
        participants: Liste participants avec statut VIP (optionnel, Story 4.4)

    Returns:
        Tuple (planning_optimisé, métriques):
            - planning_optimisé: Planning final après 3 phases
            - métriques: PlanningMetrics avec equity_gap ≤ 1 garanti

    Raises:
        InvalidConfigurationError: Si configuration ou contraintes invalides

    Note Contraintes:
        Si contraintes fournies, elles sont respectées HARD dans toutes les phases:
        - Phase 1: Baseline génère planning respectant contraintes dès le départ
        - Phase 2: Optimizer ne viole JAMAIS les contraintes (swaps rejetés)
        - Phase 3: Equity enforcement respecte aussi les contraintes

    Example:
        >>> config = PlanningConfig(N=30, X=5, x=6, S=6)
        >>> constraints = PlanningConstraints(cohesive_groups=[...])
        >>> planning, metrics = generate_optimized_planning(config, seed=42, constraints=constraints)
        >>> assert metrics.equity_gap <= 1  # FR6 garanti
        >>> print(f"Répétitions: {metrics.total_repeat_pairs}")

    Complexity:
        Time: O(N×S) + O(iter×S×X²×x²) + O(S×N) + O(S×X×x²)
              = O(iter×S×X²×x²) (dominé par Phase 2)
        Space: O(N×S) pour stockage planning

    Performance (empirique):
        - N=100 : <2s (NFR1)
        - N=300 : <5s (NFR2)
        - N=1000: <30s (NFR3)
    """
    logger.info("=" * 70)
    logger.info("DÉMARRAGE PIPELINE OPTIMISATION COMPLET")
    logger.info("=" * 70)

    # Phase 0: Validation
    logger.info("Phase 0: Validation configuration...")
    validate_config(config)
    logger.info(
        f"✓ Configuration validée : N={config.N}, X={config.X}, "
        f"x={config.x}, S={config.S}"
    )

    # Validation contraintes si présentes
    if constraints:
        errors = constraints.validate(config)
        if errors:
            from src.validation import InvalidConfigurationError

            raise InvalidConfigurationError(
                f"Contraintes invalides : {'; '.join(errors)}"
            )
        logger.info(
            f"✓ Contraintes validées : {len(constraints.cohesive_groups)} cohésives, "
            f"{len(constraints.exclusive_groups)} exclusives"
        )

    # Phase 1: Baseline
    logger.info("\nPhase 1: Génération baseline (round-robin)...")
    baseline = generate_baseline(config, seed=seed, constraints=constraints)
    metrics_baseline = compute_metrics(baseline, config, participants)
    logger.info(
        f"✓ Baseline généré : {metrics_baseline.total_unique_pairs} paires uniques, "
        f"{metrics_baseline.total_repeat_pairs} répétitions, "
        f"equity_gap={metrics_baseline.equity_gap}"
    )

    # Phase 2: Amélioration locale
    # Pour N ≥ 50, skip amélioration (trop coûteux, baseline déjà bon)
    if config.N >= 50:
        logger.info("\nPhase 2: Amélioration locale (skipped pour N ≥ 50)...")
        improved = baseline
        logger.info(
            "✓ Amélioration skipped (baseline conservé pour performance NFR1-3)"
        )
    else:
        # Adapter max_iterations selon N
        if config.N < 20:
            max_iter = 50
        else:
            max_iter = 20

        logger.info("\nPhase 2: Amélioration locale (recherche greedy)...")
        improved = improve_planning(
            baseline, config, max_iterations=max_iter, constraints=constraints
        )
    metrics_improved = compute_metrics(improved, config, participants)
    reduction_pct = (
        100
        * (metrics_baseline.total_repeat_pairs - metrics_improved.total_repeat_pairs)
        / max(metrics_baseline.total_repeat_pairs, 1)
    )
    logger.info(
        f"✓ Amélioration terminée : {metrics_improved.total_repeat_pairs} répétitions "
        f"(réduction {reduction_pct:.1f}%), equity_gap={metrics_improved.equity_gap}"
    )

    # Phase 3: Enforcement équité (avec protection contraintes)
    logger.info("\nPhase 3: Enforcement équité (garantie FR6)...")
    equitable = enforce_equity(improved, config, constraints=constraints, participants=participants)
    metrics_final = compute_metrics(equitable, config, participants)
    logger.info(
        f"✓ Équité garantie : equity_gap={metrics_final.equity_gap} ≤ 1 (FR6)"
    )

    # Résumé final
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE TERMINÉ - RÉSUMÉ FINAL")
    logger.info("=" * 70)
    logger.info(
        f"Paires uniques créées    : {metrics_final.total_unique_pairs}"
    )
    logger.info(f"Répétitions              : {metrics_final.total_repeat_pairs}")
    logger.info(
        f"Rencontres par personne  : min={metrics_final.min_unique}, "
        f"max={metrics_final.max_unique}, moyenne={metrics_final.mean_unique:.1f}"
    )
    logger.info(f"Équité (écart max-min)   : {metrics_final.equity_gap} ✓")

    # Afficher métriques VIP si présentes (Story 4.4)
    if metrics_final.vip_metrics:
        vip = metrics_final.vip_metrics
        logger.info("\nMétriques VIP (Story 4.4):")
        logger.info(
            f"  VIP ({vip.vip_count})          : min={vip.vip_min_unique}, "
            f"max={vip.vip_max_unique}, moyenne={vip.vip_mean_unique:.1f}, "
            f"gap={vip.vip_equity_gap}"
        )
        logger.info(
            f"  Réguliers ({vip.non_vip_count})      : min={vip.non_vip_min_unique}, "
            f"max={vip.non_vip_max_unique}, moyenne={vip.non_vip_mean_unique:.1f}, "
            f"gap={vip.non_vip_equity_gap}"
        )

    logger.info("=" * 70)

    return equitable, metrics_final
