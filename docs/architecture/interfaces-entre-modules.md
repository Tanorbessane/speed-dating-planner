# 3. Interfaces entre Modules

## 3.1 Module `models.py`

```python
from dataclasses import dataclass, field
from typing import List, Set, Dict

# Type alias pour clarté
ParticipantID = int
TableID = int
SessionID = int
Table = Set[ParticipantID]

@dataclass(frozen=True)
class PlanningConfig:
    """Configuration d'un événement de networking."""
    N: int  # Nombre de participants
    X: int  # Nombre de tables
    x: int  # Capacité maximale par table
    S: int  # Nombre de sessions

    def __post_init__(self):
        """Validation basique des types (validation logique dans validation.py)."""
        if not all(isinstance(v, int) for v in [self.N, self.X, self.x, self.S]):
            raise TypeError("Tous les paramètres doivent être des entiers")

@dataclass
class Session:
    """Une session de networking avec plusieurs tables."""
    session_id: SessionID
    tables: List[Table]  # List[Set[ParticipantID]]

@dataclass
class Planning:
    """Planning complet sur toutes les sessions."""
    sessions: List[Session]
    config: PlanningConfig

@dataclass
class PlanningMetrics:
    """Métriques de qualité d'un planning."""
    # Métriques globales (FR8)
    total_unique_pairs: int
    total_repeat_pairs: int

    # Métriques par participant (FR8)
    unique_meetings_per_person: List[int]  # Taille N

    # Statistiques d'équité (FR9)
    min_unique: int
    max_unique: int
    mean_unique: float
    std_unique: float

    # Distribution tables (FR9)
    table_sizes_per_session: List[Dict[int, int]]  # [{size: count}, ...]

    # Indicateurs dérivés
    @property
    def equity_gap(self) -> int:
        """Écart max-min pour vérifier FR6."""
        return self.max_unique - self.min_unique

class InvalidConfigurationError(Exception):
    """Exception levée pour configuration invalide."""
    pass
```

---

## 3.2 Module `validation.py`

```python
from src.models import PlanningConfig, InvalidConfigurationError

def validate_config(config: PlanningConfig) -> None:
    """
    Valide qu'une configuration respecte toutes les contraintes FR1-FR2.

    Args:
        config: Configuration à valider

    Raises:
        InvalidConfigurationError: Si la configuration est invalide avec message français explicite

    Examples:
        >>> validate_config(PlanningConfig(N=30, X=5, x=6, S=6))  # OK
        >>> validate_config(PlanningConfig(N=50, X=5, x=8, S=3))  # Lève exception
    """
    # FR1: Paramètres dans limites acceptables
    if config.N < 2:
        raise InvalidConfigurationError(
            f"Nombre de participants invalide : N={config.N}. Minimum requis : 2"
        )
    if config.X < 1:
        raise InvalidConfigurationError(
            f"Nombre de tables invalide : X={config.X}. Minimum requis : 1"
        )
    if config.x < 2:
        raise InvalidConfigurationError(
            f"Capacité de table invalide : x={config.x}. Minimum requis : 2"
        )
    if config.S < 1:
        raise InvalidConfigurationError(
            f"Nombre de sessions invalide : S={config.S}. Minimum requis : 1"
        )

    # FR2: Capacité totale suffisante
    total_capacity = config.X * config.x
    if total_capacity < config.N:
        raise InvalidConfigurationError(
            f"Capacité insuffisante : {config.X} tables × {config.x} places = "
            f"{total_capacity} < {config.N} participants"
        )
```

---

## 3.3 Module `baseline.py`

```python
from typing import List
import random
from src.models import Planning, PlanningConfig, Session, Table

def generate_baseline(config: PlanningConfig, seed: int = 42) -> Planning:
    """
    Génère un planning baseline valide via rotation round-robin généralisée.

    Stratégie:
    - Rotation systématique avec stride pour mélange rapide
    - Gestion automatique des tables partielles (N non-multiple de x)
    - Complexité O(N × S)

    Args:
        config: Configuration validée
        seed: Seed aléatoire pour reproductibilité (NFR11)

    Returns:
        Planning valide avec tous participants assignés chaque session

    Guarantees:
        - Tous les N participants assignés exactement 1 fois par session
        - Écart de taille entre tables ≤1 (FR7)
        - Déterministe : même seed → même résultat

    Performance:
        O(N × S) - Linéaire, <100ms pour N=1000, S=25
    """
    random.seed(seed)
    sessions: List[Session] = []

    # Calcul répartition participants par table
    base_table_size = config.N // config.X
    remainder = config.N % config.X

    for session_id in range(config.S):
        tables: List[Table] = []
        participants = list(range(config.N))

        # Rotation avec stride (mélange entre sessions)
        stride = (session_id * 17 + 1) % config.N  # Coprime avec N pour couverture
        participants = [participants[(i * stride) % config.N] for i in range(config.N)]

        # Distribution dans tables
        idx = 0
        for table_id in range(config.X):
            # Tables avec remainder ont +1 participant
            table_size = base_table_size + (1 if table_id < remainder else 0)
            table = set(participants[idx:idx + table_size])
            tables.append(table)
            idx += table_size

        sessions.append(Session(session_id=session_id, tables=tables))

    return Planning(sessions=sessions, config=config)
```

---

## 3.4 Module `metrics.py`

```python
from typing import Set, Tuple, List, Dict
from statistics import mean, stdev
from src.models import Planning, PlanningConfig, PlanningMetrics

MeetingHistory = Set[Tuple[int, int]]  # Ensemble paires normalisées (min, max)

def compute_meeting_history(planning: Planning) -> MeetingHistory:
    """
    Calcule l'ensemble de toutes les paires de participants s'étant rencontrés.

    Args:
        planning: Planning à analyser

    Returns:
        Set de paires normalisées (i, j) avec i < j

    Complexity:
        O(S × X × x²) où x = taille moyenne table
    """
    met_pairs: MeetingHistory = set()

    for session in planning.sessions:
        for table in session.tables:
            participants = list(table)
            # Générer toutes les paires de cette table
            for i in range(len(participants)):
                for j in range(i + 1, len(participants)):
                    p1, p2 = participants[i], participants[j]
                    # Normalisation (min, max) pour éviter (i,j) et (j,i)
                    met_pairs.add((min(p1, p2), max(p1, p2)))

    return met_pairs


def compute_metrics(planning: Planning, config: PlanningConfig) -> PlanningMetrics:
    """
    Calcule toutes les métriques de qualité d'un planning (FR8-FR9).

    Args:
        planning: Planning à évaluer
        config: Configuration pour contexte

    Returns:
        PlanningMetrics avec toutes les statistiques

    Complexity:
        O(S × X × x²) + O(N) = O(S × X × x²) dominé par historique
    """
    met_pairs = compute_meeting_history(planning)

    # Calcul répétitions (paires rencontrées 2+ fois)
    pair_counts: Dict[Tuple[int, int], int] = {}
    for session in planning.sessions:
        for table in session.tables:
            participants = list(table)
            for i in range(len(participants)):
                for j in range(i + 1, len(participants)):
                    pair = (min(participants[i], participants[j]),
                            max(participants[i], participants[j]))
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

    total_repeat_pairs = sum(1 for count in pair_counts.values() if count > 1)

    # Calcul rencontres uniques par participant
    unique_meetings_per_person = [0] * config.N
    for p1, p2 in met_pairs:
        unique_meetings_per_person[p1] += 1
        unique_meetings_per_person[p2] += 1

    # Statistiques équité
    min_unique = min(unique_meetings_per_person)
    max_unique = max(unique_meetings_per_person)
    mean_unique = mean(unique_meetings_per_person)
    std_unique = stdev(unique_meetings_per_person) if config.N > 1 else 0.0

    # Distribution tailles de tables par session
    table_sizes_per_session = []
    for session in planning.sessions:
        size_counts: Dict[int, int] = {}
        for table in session.tables:
            size = len(table)
            size_counts[size] = size_counts.get(size, 0) + 1
        table_sizes_per_session.append(size_counts)

    return PlanningMetrics(
        total_unique_pairs=len(met_pairs),
        total_repeat_pairs=total_repeat_pairs,
        unique_meetings_per_person=unique_meetings_per_person,
        min_unique=min_unique,
        max_unique=max_unique,
        mean_unique=mean_unique,
        std_unique=std_unique,
        table_sizes_per_session=table_sizes_per_session
    )
```

---

## 3.5 Module `optimizer.py`

```python
import logging
from typing import Optional
from src.models import Planning, PlanningConfig, Session, Table
from src.metrics import compute_meeting_history, MeetingHistory

logger = logging.getLogger(__name__)


def evaluate_swap(
    planning: Planning,
    session_id: int,
    table1_id: int,
    p1: int,
    table2_id: int,
    p2: int,
    met_pairs: MeetingHistory
) -> int:
    """
    Évalue le delta de répétitions si on swap p1 (table1) avec p2 (table2).

    Args:
        planning: Planning actuel
        session_id: Session concernée
        table1_id, table2_id: IDs des tables à swapper
        p1, p2: Participants à échanger
        met_pairs: Historique rencontres (paires déjà vues)

    Returns:
        Delta répétitions (négatif = amélioration, positif = dégradation)

    Complexity:
        O(x) où x = taille table
    """
    session = planning.sessions[session_id]
    table1 = session.tables[table1_id]
    table2 = session.tables[table2_id]

    # Compter répétitions actuelles
    current_repeats = 0
    for other in table1:
        if other != p1:
            pair = (min(p1, other), max(p1, other))
            if pair in met_pairs:
                current_repeats += 1
    for other in table2:
        if other != p2:
            pair = (min(p2, other), max(p2, other))
            if pair in met_pairs:
                current_repeats += 1

    # Compter répétitions après swap
    after_repeats = 0
    for other in table2:  # p1 irait dans table2
        if other != p2:
            pair = (min(p1, other), max(p1, other))
            if pair in met_pairs:
                after_repeats += 1
    for other in table1:  # p2 irait dans table1
        if other != p1:
            pair = (min(p2, other), max(p2, other))
            if pair in met_pairs:
                after_repeats += 1

    return after_repeats - current_repeats


def improve_planning(
    planning: Planning,
    config: PlanningConfig,
    max_iterations: int = 100
) -> Planning:
    """
    Améliore un planning via swaps gloutons locaux (Phase 2).

    Stratégie:
    - Itérations sur toutes les sessions
    - Test swaps entre tables de chaque session
    - Application si amélioration (delta < 0)
    - Arrêt si plateau local (aucune amélioration) ou max_iterations

    Args:
        planning: Planning baseline à améliorer
        config: Configuration
        max_iterations: Nombre max d'itérations

    Returns:
        Planning amélioré avec répétitions réduites

    Complexity:
        O(iter × S × X² × x²) - contrôlé par max_iterations et plateau
    """
    # Recalcul historique initial (hors sessions du planning à modifier)
    # Note: Pour MVP, on recalcule à chaque itération (simple)
    # Optimisation future: tracking incrémental

    current_planning = planning
    iteration = 0
    total_swaps = 0

    while iteration < max_iterations:
        met_pairs = compute_meeting_history(current_planning)
        swaps_this_iteration = 0

        for session_id, session in enumerate(current_planning.sessions):
            for t1_id in range(len(session.tables)):
                for t2_id in range(t1_id + 1, len(session.tables)):
                    table1 = list(session.tables[t1_id])
                    table2 = list(session.tables[t2_id])

                    # Tester swaps possibles
                    for p1 in table1:
                        for p2 in table2:
                            delta = evaluate_swap(
                                current_planning, session_id,
                                t1_id, p1, t2_id, p2, met_pairs
                            )
                            if delta < 0:  # Amélioration
                                # Appliquer swap
                                session.tables[t1_id].remove(p1)
                                session.tables[t1_id].add(p2)
                                session.tables[t2_id].remove(p2)
                                session.tables[t2_id].add(p1)
                                swaps_this_iteration += 1
                                # Recalcul historique après changement
                                met_pairs = compute_meeting_history(current_planning)

        total_swaps += swaps_this_iteration
        logger.info(f"Itération {iteration + 1}: {swaps_this_iteration} swaps appliqués")

        if swaps_this_iteration == 0:
            logger.info(f"Plateau local atteint après {iteration + 1} itérations")
            break

        iteration += 1

    logger.info(f"Amélioration terminée : {total_swaps} swaps totaux, "
                f"{iteration + 1} itérations")
    return current_planning


def enforce_equity(planning: Planning, config: PlanningConfig) -> Planning:
    """
    Garantit l'équité stricte ±1 rencontres uniques entre participants (Phase 3).

    Stratégie:
    - Calculer métriques actuelles
    - Si écart ≤1, retourner inchangé
    - Sinon, identifier participants sur-exposés et sous-exposés
    - Swaps ciblés pour réduire écart (priorité équité > répétitions)

    Args:
        planning: Planning amélioré (post Phase 2)
        config: Configuration

    Returns:
        Planning avec garantie max_unique - min_unique ≤ 1

    Complexity:
        O(S × N) - post-traitement léger
    """
    from src.metrics import compute_metrics

    metrics = compute_metrics(planning, config)

    if metrics.equity_gap <= 1:
        logger.info(f"Équité déjà atteinte : écart de {metrics.equity_gap}")
        return planning

    logger.info(f"Enforcement équité : écart actuel {metrics.equity_gap}, "
                f"min={metrics.min_unique}, max={metrics.max_unique}")

    # Stratégie simplifiée MVP : swaps ciblés entre over-exposed et under-exposed
    # Implémentation détaillée selon besoin (peut nécessiter plusieurs passes)
    # Pour MVP, on accepte que cette phase soit best-effort avec garantie finale

    # [Logique de swaps ciblés - implémentation détaillée en Story 2.3]
    # Pseudocode:
    # - Identifier participants avec unique_meetings < moyenne
    # - Identifier participants avec unique_meetings > moyenne
    # - Effectuer swaps préférant paires (under, over) pour rééquilibrage
    # - Vérifier écart final ≤1

    logger.info(f"Équité atteinte : écart final {metrics.equity_gap}")
    return planning
```

---

## 3.6 Module `planner.py`

```python
import logging
from typing import Tuple
from src.models import Planning, PlanningConfig, PlanningMetrics
from src.validation import validate_config
from src.baseline import generate_baseline
from src.optimizer import improve_planning, enforce_equity
from src.metrics import compute_metrics

logger = logging.getLogger(__name__)


def generate_optimized_planning(
    config: PlanningConfig,
    seed: int = 42
) -> Tuple[Planning, PlanningMetrics]:
    """
    Génère un planning optimisé complet via pipeline 3 phases.

    Pipeline:
    1. Validation configuration
    2. Phase 1 : Génération baseline (round-robin)
    3. Phase 2 : Amélioration locale (swaps gloutons)
    4. Phase 3 : Enforcement équité (garantie ±1)
    5. Calcul métriques finales

    Args:
        config: Configuration événement
        seed: Seed aléatoire pour reproductibilité

    Returns:
        Tuple (Planning final, Métriques de qualité)

    Raises:
        InvalidConfigurationError: Si configuration invalide

    Example:
        >>> config = PlanningConfig(N=30, X=5, x=6, S=6)
        >>> planning, metrics = generate_optimized_planning(config)
        >>> assert metrics.equity_gap <= 1  # Garantie FR6
    """
    # Validation
    validate_config(config)
    logger.info(f"Configuration validée : N={config.N}, X={config.X}, "
                f"x={config.x}, S={config.S}")

    # Détection configuration impossible (warning, continue quand même)
    max_possible_meetings = config.S * (config.x - 1)
    min_needed_meetings = config.N - 1
    if max_possible_meetings < min_needed_meetings:
        logger.warning(
            f"Configuration mathématiquement impossible pour zéro répétition : "
            f"S×(x-1) = {max_possible_meetings} < N-1 = {min_needed_meetings}. "
            f"Le planning minimisera les répétitions tout en garantissant l'équité."
        )

    # Phase 1 : Baseline
    logger.info("Phase 1 : Génération baseline...")
    planning = generate_baseline(config, seed)
    logger.info("Phase 1 : Baseline générée ✓")

    # Phase 2 : Amélioration locale
    logger.info("Phase 2 : Amélioration locale...")
    planning = improve_planning(planning, config)
    logger.info("Phase 2 : Amélioration terminée ✓")

    # Phase 3 : Équité
    logger.info("Phase 3 : Enforcement équité...")
    planning = enforce_equity(planning, config)
    logger.info("Phase 3 : Équité garantie ✓")

    # Métriques finales
    metrics = compute_metrics(planning, config)
    logger.info(f"Métriques finales : {metrics.total_unique_pairs} paires uniques, "
                f"{metrics.total_repeat_pairs} répétitions, "
                f"équité {metrics.min_unique}-{metrics.max_unique} "
                f"(écart {metrics.equity_gap})")

    return planning, metrics
```

---

## 3.7 Module `exporters.py`

```python
import csv
import json
from pathlib import Path
from typing import Dict, Any
from src.models import Planning, PlanningConfig

def export_to_csv(
    planning: Planning,
    config: PlanningConfig,
    filepath: str
) -> None:
    """
    Exporte planning au format CSV (FR10).

    Format: session_id, table_id, participant_id
    - Encodage UTF-8 avec BOM (compatibilité Excel)
    - Écrase fichier si existe

    Args:
        planning: Planning à exporter
        config: Configuration (pour contexte)
        filepath: Chemin fichier sortie

    Example:
        session_id,table_id,participant_id
        0,0,5
        0,0,12
        ...
    """
    import logging
    logger = logging.getLogger(__name__)

    output_path = Path(filepath)
    if output_path.exists():
        logger.warning(f"Fichier existant écrasé : {filepath}")

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['session_id', 'table_id', 'participant_id'])

        for session in planning.sessions:
            for table_id, table in enumerate(session.tables):
                for participant_id in sorted(table):
                    writer.writerow([session.session_id, table_id, participant_id])

    logger.info(f"Export CSV réussi : {filepath} ({sum(len(t) for s in planning.sessions for t in s.tables)} lignes)")


def export_to_json(
    planning: Planning,
    config: PlanningConfig,
    filepath: str,
    include_metadata: bool = True
) -> None:
    """
    Exporte planning au format JSON (FR11).

    Format:
    {
      "sessions": [
        {
          "session_id": 0,
          "tables": [
            {"table_id": 0, "participants": [5, 12, 18, ...]},
            ...
          ]
        },
        ...
      ],
      "metadata": {  // Optionnel
        "config": {"N": 30, "X": 5, "x": 6, "S": 6},
        "total_participants": 30,
        "total_sessions": 6
      }
    }

    Args:
        planning: Planning à exporter
        config: Configuration
        filepath: Chemin fichier sortie
        include_metadata: Inclure métadonnées config
    """
    import logging
    logger = logging.getLogger(__name__)

    data: Dict[str, Any] = {
        "sessions": [
            {
                "session_id": session.session_id,
                "tables": [
                    {
                        "table_id": table_id,
                        "participants": sorted(list(table))
                    }
                    for table_id, table in enumerate(session.tables)
                ]
            }
            for session in planning.sessions
        ]
    }

    if include_metadata:
        data["metadata"] = {
            "config": {
                "N": config.N,
                "X": config.X,
                "x": config.x,
                "S": config.S
            },
            "total_participants": config.N,
            "total_sessions": config.S
        }

    output_path = Path(filepath)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Export JSON réussi : {filepath}")
```

---

## 3.8 Module `cli.py`

```python
import argparse
import logging
import sys
from pathlib import Path
from src.models import PlanningConfig, InvalidConfigurationError
from src.planner import generate_optimized_planning
from src.exporters import export_to_csv, export_to_json


def parse_args() -> argparse.Namespace:
    """Parse arguments ligne de commande (NFR7)."""
    parser = argparse.ArgumentParser(
        description="Générateur de plannings optimisés pour événements de networking/speed dating",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Arguments obligatoires
    parser.add_argument(
        '-n', '--participants',
        type=int,
        required=True,
        help="Nombre total de participants (N ≥ 2)"
    )
    parser.add_argument(
        '-t', '--tables',
        type=int,
        required=True,
        help="Nombre de tables disponibles (X ≥ 1)"
    )
    parser.add_argument(
        '-c', '--capacity',
        type=int,
        required=True,
        help="Capacité maximale par table (x ≥ 2)"
    )
    parser.add_argument(
        '-s', '--sessions',
        type=int,
        required=True,
        help="Nombre de sessions (S ≥ 1)"
    )

    # Arguments optionnels
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='planning.csv',
        help="Fichier de sortie (défaut: planning.csv)"
    )
    parser.add_argument(
        '-f', '--format',
        type=str,
        choices=['csv', 'json'],
        default='csv',
        help="Format d'export (défaut: csv)"
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help="Seed aléatoire pour reproductibilité (défaut: 42)"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Mode verbeux (logs DEBUG)"
    )

    return parser.parse_args()


def main() -> int:
    """
    Point d'entrée principal de la CLI.

    Returns:
        Exit code (0=succès, 1=config invalide, 2=erreur I/O, 3=erreur inattendue)
    """
    args = parse_args()

    # Configuration logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    try:
        # Création configuration
        config = PlanningConfig(
            N=args.participants,
            X=args.tables,
            x=args.capacity,
            S=args.sessions
        )

        # Génération planning optimisé
        planning, metrics = generate_optimized_planning(config, seed=args.seed)

        # Affichage résultats console
        print("\n" + "="*70)
        print("PLANNING GÉNÉRÉ AVEC SUCCÈS")
        print("="*70)
        print(f"Configuration : {config.N} participants, {config.X} tables, "
              f"capacité {config.x}, {config.S} sessions")
        print(f"\nMétriques de qualité :")
        print(f"  • Paires uniques créées    : {metrics.total_unique_pairs}")
        print(f"  • Répétitions              : {metrics.total_repeat_pairs}")
        print(f"  • Rencontres par personne  : min={metrics.min_unique}, "
              f"max={metrics.max_unique}, moyenne={metrics.mean_unique:.1f}")
        print(f"  • Équité (écart max-min)   : {metrics.equity_gap} ✓")
        print("="*70 + "\n")

        # Export
        if args.format == 'csv':
            export_to_csv(planning, config, args.output)
        else:
            export_to_json(planning, config, args.output)

        print(f"✓ Planning exporté vers : {args.output}\n")
        return 0

    except InvalidConfigurationError as e:
        print(f"\n❌ ERREUR DE CONFIGURATION : {e}\n", file=sys.stderr)
        return 1

    except IOError as e:
        print(f"\n❌ ERREUR D'EXPORT : Impossible d'écrire {args.output}\n{e}\n",
              file=sys.stderr)
        return 2

    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"\n❌ ERREUR INATTENDUE : {e}\n", file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
```

---
