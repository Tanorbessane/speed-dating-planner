"""Speed Dating Planner - Système d'optimisation de plannings pour événements de networking.

Ce package fournit des algorithmes optimisés pour générer des plannings équitables
d'événements de type speed dating ou networking, garantissant une distribution
équilibrée des rencontres entre participants.

Modules:
    models: Structures de données (Planning, PlanningConfig, Session, PlanningMetrics)
    validation: Validation de configuration
    baseline: Algorithme de génération baseline (round-robin)
    metrics: Calcul de métriques de qualité
    improvement: Optimisation par recherche locale
    equity: Garantie d'équité (FR6)
    planner: Pipeline complet
    exporters: Export CSV/JSON
    cli: Interface ligne de commande

Usage:
    >>> from src.planner import generate_optimized_planning
    >>> from src.models import PlanningConfig
    >>> config = PlanningConfig(N=30, X=5, x=6, S=6)
    >>> planning, metrics = generate_optimized_planning(config, seed=42)
"""

__version__ = "0.1.0"
