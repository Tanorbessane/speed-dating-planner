"""Interface CLI pour génération de plannings (NFR7).

Ce module fournit l'interface en ligne de commande pour générer et exporter
des plannings de speed dating. Il orchestre les composants du système sans
contenir de logique métier.

Exit codes:
    0: Succès
    1: Configuration invalide (validation échouée)
    2: Erreur I/O (fichier non accessible)
    3: Erreur inattendue

Usage:
    python -m src.cli -n 30 -t 10 -c 3 -s 5 -o planning.csv

Functions:
    parse_args: Parse arguments ligne de commande
    main: Point d'entrée principal (orchestration uniquement)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import NoReturn

from src.exporters import export_to_csv, export_to_json
from src.models import PlanningConfig
from src.planner import generate_optimized_planning
from src.validation import InvalidConfigurationError, validate_config

# Configuration logging
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse arguments CLI avec validation basique.

    Arguments requis:
        -n, --participants: Nombre total de participants (N)
        -t, --tables: Nombre de tables par session (X)
        -c, --capacity: Capacité par table (x)
        -s, --sessions: Nombre de sessions (S)

    Arguments optionnels:
        -o, --output: Chemin fichier sortie (défaut: planning.csv)
        -f, --format: Format export (csv|json, défaut: csv)
        --seed: Graine aléatoire pour reproductibilité (défaut: 42)
        -v, --verbose: Mode verbeux (logging DEBUG)

    Returns:
        Namespace contenant arguments parsés

    Example:
        >>> args = parse_args()
        >>> print(args.participants, args.tables)
        30 10
    """
    parser = argparse.ArgumentParser(
        prog="speed-dating-planner",
        description="Générateur de plannings pour événements de networking/speed dating",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Générer planning 30 participants, 10 tables de 3, 5 sessions
  python -m src.cli -n 30 -t 10 -c 3 -s 5 -o event.csv

  # Export JSON avec métadonnées
  python -m src.cli -n 50 -t 10 -c 5 -s 8 -o event.json -f json

  # Mode verbeux pour debugging
  python -m src.cli -n 20 -t 5 -c 4 -s 3 -o test.csv -v

Exit codes:
  0: Succès
  1: Configuration invalide
  2: Erreur I/O (fichier non accessible)
  3: Erreur inattendue
        """,
    )

    # Arguments requis (configuration)
    required = parser.add_argument_group("arguments requis")
    required.add_argument(
        "-n",
        "--participants",
        type=int,
        required=True,
        metavar="N",
        help="Nombre total de participants (N ≥ 2)",
    )
    required.add_argument(
        "-t",
        "--tables",
        type=int,
        required=True,
        metavar="X",
        help="Nombre de tables par session (X ≥ 1)",
    )
    required.add_argument(
        "-c",
        "--capacity",
        type=int,
        required=True,
        metavar="x",
        help="Capacité par table (x ≥ 2)",
    )
    required.add_argument(
        "-s",
        "--sessions",
        type=int,
        required=True,
        metavar="S",
        help="Nombre de sessions (S ≥ 1)",
    )

    # Arguments optionnels
    optional = parser.add_argument_group("arguments optionnels")
    optional.add_argument(
        "-o",
        "--output",
        type=str,
        default="planning.csv",
        metavar="PATH",
        help="Chemin fichier sortie (défaut: planning.csv)",
    )
    optional.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["csv", "json"],
        default="csv",
        help="Format export: csv ou json (défaut: csv)",
    )
    optional.add_argument(
        "--seed",
        type=int,
        default=42,
        metavar="SEED",
        help="Graine aléatoire pour reproductibilité (défaut: 42)",
    )
    optional.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Mode verbeux (affiche logs détaillés)",
    )

    return parser.parse_args()


def main() -> NoReturn:
    """Point d'entrée principal CLI (orchestration uniquement).

    Workflow:
        1. Parse arguments CLI
        2. Configure logging
        3. Crée configuration et valide
        4. Génère planning optimisé
        5. Exporte vers fichier (CSV ou JSON)
        6. Affiche statistiques résultat
        7. Exit avec code approprié

    Exit codes:
        0: Succès
        1: Configuration invalide (FR1-FR8, NFR1-3)
        2: Erreur I/O (fichier non accessible)
        3: Erreur inattendue (bug logiciel)

    Note:
        Cette fonction contient UNIQUEMENT de l'orchestration.
        Aucune logique métier n'est implémentée ici.
        Toute la logique est déléguée aux modules spécialisés.
    """
    # Parse arguments
    args = parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    try:
        # Étape 1: Créer configuration
        logger.info(
            f"Configuration : N={args.participants}, X={args.tables}, "
            f"x={args.capacity}, S={args.sessions}"
        )
        config = PlanningConfig(
            N=args.participants, X=args.tables, x=args.capacity, S=args.sessions
        )

        # Étape 2: Valider configuration (délégué à src.validation)
        validate_config(config)
        logger.info("✓ Configuration valide")

        # Étape 3: Générer planning optimisé (délégué à src.planner)
        logger.info(f"Génération planning (seed={args.seed})...")
        planning, metrics = generate_optimized_planning(config, seed=args.seed)
        logger.info("✓ Planning généré")

        # Étape 4: Afficher statistiques
        logger.info(
            f"Statistiques : {metrics.total_unique_pairs} paires uniques, "
            f"{metrics.total_repeat_pairs} répétitions"
        )
        logger.info(
            f"Équité : min={metrics.min_unique}, max={metrics.max_unique}, "
            f"gap={metrics.equity_gap} (FR6: ≤1)"
        )

        # Étape 5: Exporter (délégué à src.exporters)
        output_path = Path(args.output)
        logger.info(f"Export vers {output_path} (format={args.format})...")

        if args.format == "csv":
            export_to_csv(planning, config, str(output_path))
        elif args.format == "json":
            export_to_json(planning, config, str(output_path), include_metadata=True)
        else:
            # Impossible (argparse valide choices), mais défensif
            raise ValueError(f"Format inconnu : {args.format}")

        logger.info(f"✓ Export réussi : {output_path}")
        logger.info("🎉 Planning généré avec succès !")

        # Exit succès
        sys.exit(0)

    except InvalidConfigurationError as e:
        # Exit code 1: Configuration invalide
        logger.error(f"Configuration invalide : {e}")
        sys.exit(1)

    except (IOError, OSError, PermissionError) as e:
        # Exit code 2: Erreur I/O
        logger.error(f"Erreur I/O : {e}")
        sys.exit(2)

    except Exception as e:
        # Exit code 3: Erreur inattendue (bug)
        logger.exception(f"Erreur inattendue : {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
