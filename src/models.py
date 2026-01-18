"""Structures de données pour le système de planification de speed dating.

Ce module définit les dataclasses représentant la configuration, les sessions,
les plannings et les métriques de qualité.

Classes:
    PlanningConfig: Configuration immutable du planning
    Session: Une session avec tables de participants
    Planning: Planning complet (liste de sessions)
    PlanningMetrics: Métriques de qualité du planning
    Participant: Représente un participant à l'événement
    GroupConstraintType: Type de contrainte de groupe (Enum)
    GroupConstraint: Contrainte de groupe (cohésif ou exclusif)
    PlanningConstraints: Ensemble de contraintes pour planning
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Optional


@dataclass(frozen=True)
class PlanningConfig:
    """Configuration immutable pour la génération de planning.

    Cette configuration définit les paramètres fondamentaux d'un événement
    de speed dating ou networking.

    Attributes:
        N: Nombre total de participants (N ≥ 2)
        X: Nombre de tables disponibles (X ≥ 1)
        x: Capacité maximale par table (x ≥ 2)
        S: Nombre de sessions (S ≥ 1)

    Invariants:
        - X × x ≥ N (capacité totale suffisante)
        - Tous les paramètres sont positifs

    Example:
        >>> config = PlanningConfig(N=30, X=5, x=6, S=6)
        >>> config.N
        30
        >>> config.total_capacity
        30
    """

    N: int  # Participants
    X: int  # Tables
    x: int  # Capacité par table
    S: int  # Sessions

    @property
    def total_capacity(self) -> int:
        """Capacité totale de places disponibles.

        Returns:
            X × x (nombre total de places)

        Example:
            >>> PlanningConfig(N=30, X=5, x=6, S=6).total_capacity
            30
        """
        return self.X * self.x

    def __post_init__(self) -> None:
        """Validation basique des types (valeurs positives).

        Note:
            La validation complète des contraintes (X×x ≥ N, etc.)
            est effectuée par le module validation.
        """
        if not isinstance(self.N, int) or self.N < 0:
            raise TypeError(f"N doit être un entier positif, reçu: {self.N}")
        if not isinstance(self.X, int) or self.X < 0:
            raise TypeError(f"X doit être un entier positif, reçu: {self.X}")
        if not isinstance(self.x, int) or self.x < 0:
            raise TypeError(f"x doit être un entier positif, reçu: {self.x}")
        if not isinstance(self.S, int) or self.S < 0:
            raise TypeError(f"S doit être un entier positif, reçu: {self.S}")


@dataclass
class Session:
    """Représente une session avec répartition des participants aux tables.

    Une session est un snapshot temporel où chaque participant est assigné
    à exactement une table.

    Attributes:
        session_id: Identifiant unique de la session (0-indexed)
        tables: Liste de sets de participant IDs par table

    Invariants:
        - Chaque participant apparaît dans au plus une table
        - Les tables sont disjointes (intersection vide)
        - Les IDs participants sont des entiers ≥ 0

    Example:
        >>> session = Session(0, [{0, 1, 2}, {3, 4, 5}])
        >>> session.session_id
        0
        >>> len(session.tables)
        2
        >>> session.total_participants
        6
    """

    session_id: int
    tables: List[Set[int]] = field(default_factory=list)

    @property
    def total_participants(self) -> int:
        """Nombre total de participants dans cette session.

        Returns:
            Somme des tailles de toutes les tables

        Example:
            >>> Session(0, [{0, 1, 2}, {3, 4}]).total_participants
            5
        """
        return sum(len(table) for table in self.tables)

    def __post_init__(self) -> None:
        """Validation basique de la structure de session."""
        if not isinstance(self.session_id, int) or self.session_id < 0:
            raise TypeError(f"session_id doit être un entier ≥ 0, reçu: {self.session_id}")
        if not isinstance(self.tables, list):
            raise TypeError(f"tables doit être une liste, reçu: {type(self.tables)}")


@dataclass
class Planning:
    """Planning complet d'un événement (ensemble de sessions).

    Un planning représente la solution complète d'affectation des participants
    aux tables à travers toutes les sessions de l'événement.

    Attributes:
        sessions: Liste ordonnée des sessions
        config: Configuration associée au planning

    Invariants:
        - len(sessions) == config.S
        - Chaque session respecte config.X et config.x
        - session_id correspond à l'index dans la liste

    Example:
        >>> config = PlanningConfig(N=6, X=2, x=3, S=2)
        >>> sessions = [
        ...     Session(0, [{0, 1, 2}, {3, 4, 5}]),
        ...     Session(1, [{0, 3, 4}, {1, 2, 5}])
        ... ]
        >>> planning = Planning(sessions, config)
        >>> len(planning.sessions)
        2
    """

    sessions: List[Session]
    config: PlanningConfig

    def __post_init__(self) -> None:
        """Validation basique de la structure du planning."""
        if not isinstance(self.sessions, list):
            raise TypeError(f"sessions doit être une liste, reçu: {type(self.sessions)}")
        if not isinstance(self.config, PlanningConfig):
            raise TypeError(
                f"config doit être PlanningConfig, reçu: {type(self.config)}"
            )


@dataclass
class VIPMetrics:
    """Métriques séparées pour participants VIP et réguliers.

    Permet de comparer les expériences VIP vs participants réguliers
    dans un même planning.

    Attributes:
        vip_count: Nombre de participants VIP
        vip_min_unique: Minimum rencontres uniques parmi VIP
        vip_max_unique: Maximum rencontres uniques parmi VIP
        vip_mean_unique: Moyenne rencontres uniques VIP
        vip_equity_gap: Écart max-min pour VIP seulement
        non_vip_count: Nombre de participants réguliers
        non_vip_min_unique: Minimum rencontres uniques parmi réguliers
        non_vip_max_unique: Maximum rencontres uniques parmi réguliers
        non_vip_mean_unique: Moyenne rencontres uniques réguliers
        non_vip_equity_gap: Écart max-min pour réguliers seulement

    Example:
        >>> vip_metrics = VIPMetrics(
        ...     vip_count=3,
        ...     vip_min_unique=15,
        ...     vip_max_unique=16,
        ...     vip_mean_unique=15.67,
        ...     vip_equity_gap=1,
        ...     non_vip_count=17,
        ...     non_vip_min_unique=12,
        ...     non_vip_max_unique=14,
        ...     non_vip_mean_unique=13.2,
        ...     non_vip_equity_gap=2
        ... )
        >>> vip_metrics.vip_equity_gap
        1
    """

    vip_count: int
    vip_min_unique: int
    vip_max_unique: int
    vip_mean_unique: float
    vip_equity_gap: int

    non_vip_count: int
    non_vip_min_unique: int
    non_vip_max_unique: int
    non_vip_mean_unique: float
    non_vip_equity_gap: int


@dataclass
class PlanningMetrics:
    """Métriques de qualité d'un planning.

    Calcule et stocke les métriques utilisées pour évaluer la qualité
    d'un planning : nombre de rencontres uniques, répétitions, équité.

    Attributes:
        total_unique_pairs: Nombre de paires ayant été rencontrées au moins une fois
        total_repeat_pairs: Nombre de paires rencontrées plus d'une fois
        unique_meetings_per_person: Liste[int] du nombre de rencontres uniques par participant
        min_unique: Minimum de rencontres uniques parmi tous les participants
        max_unique: Maximum de rencontres uniques parmi tous les participants
        mean_unique: Moyenne de rencontres uniques par participant
        vip_metrics: Métriques séparées VIP vs réguliers (optionnel)

    Example:
        >>> metrics = PlanningMetrics(
        ...     total_unique_pairs=145,
        ...     total_repeat_pairs=7,
        ...     unique_meetings_per_person=[10, 11, 10, 11, 10, 10],
        ...     min_unique=10,
        ...     max_unique=11,
        ...     mean_unique=10.33
        ... )
        >>> metrics.equity_gap
        1
        >>> metrics.total_unique_pairs
        145
    """

    total_unique_pairs: int
    total_repeat_pairs: int
    unique_meetings_per_person: List[int]
    min_unique: int
    max_unique: int
    mean_unique: float
    vip_metrics: Optional["VIPMetrics"] = None

    @property
    def equity_gap(self) -> int:
        """Écart entre le participant le plus exposé et le moins exposé.

        Cette métrique mesure l'équité du planning. L'objectif est de garantir
        equity_gap ≤ 1 (FR6).

        Returns:
            max_unique - min_unique

        Example:
            >>> metrics = PlanningMetrics(
            ...     total_unique_pairs=100,
            ...     total_repeat_pairs=5,
            ...     unique_meetings_per_person=[10, 11, 10],
            ...     min_unique=10,
            ...     max_unique=11,
            ...     mean_unique=10.33
            ... )
            >>> metrics.equity_gap
            1
        """
        return self.max_unique - self.min_unique

    def __post_init__(self) -> None:
        """Validation basique des métriques."""
        if self.total_unique_pairs < 0:
            raise ValueError(
                f"total_unique_pairs doit être ≥ 0, reçu: {self.total_unique_pairs}"
            )
        if self.total_repeat_pairs < 0:
            raise ValueError(
                f"total_repeat_pairs doit être ≥ 0, reçu: {self.total_repeat_pairs}"
            )
        if self.min_unique < 0:
            raise ValueError(f"min_unique doit être ≥ 0, reçu: {self.min_unique}")
        if self.max_unique < self.min_unique:
            raise ValueError(
                f"max_unique ({self.max_unique}) < min_unique ({self.min_unique})"
            )


@dataclass
class Participant:
    """Représente un participant à l'événement.

    Utilisé pour l'import CSV/Excel et la gestion des contraintes (Epic 4).

    Attributes:
        id: Identifiant unique du participant (0-indexed)
        nom: Nom de famille (requis)
        prenom: Prénom (optionnel)
        email: Adresse email (optionnel, validé si présent)
        groupe: Groupe d'appartenance (optionnel, pour contraintes futures)
        tags: Liste de tags (ex: ["VIP", "Speaker"])
        is_vip: Statut VIP pour priorité dans algorithme (défaut: False)

    Example:
        >>> p = Participant(
        ...     id=0,
        ...     nom="Dupont",
        ...     prenom="Jean",
        ...     email="jean.dupont@example.com",
        ...     groupe="Groupe A",
        ...     tags=["VIP"]
        ... )
        >>> p.nom
        'Dupont'
        >>> p.full_name
        'Jean Dupont'
    """

    id: int
    nom: str
    prenom: Optional[str] = None
    email: Optional[str] = None
    groupe: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_vip: bool = False

    @property
    def full_name(self) -> str:
        """Nom complet du participant.

        Returns:
            "Prénom Nom" si prénom existe, sinon "Nom"

        Example:
            >>> Participant(0, "Dupont", "Jean").full_name
            'Jean Dupont'
            >>> Participant(0, "Dupont").full_name
            'Dupont'
        """
        if self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.nom

    def __post_init__(self) -> None:
        """Validation basique des champs."""
        if not isinstance(self.id, int) or self.id < 0:
            raise ValueError(f"id doit être un entier ≥ 0, reçu: {self.id}")
        if not self.nom or not isinstance(self.nom, str):
            raise ValueError(f"nom est requis et doit être une chaîne, reçu: {self.nom}")
        if not isinstance(self.is_vip, bool):
            raise ValueError(f"is_vip doit être un booléen, reçu: {self.is_vip}")
        if self.tags is None:
            # Ensure tags is always a list
            object.__setattr__(self, "tags", [])


class GroupConstraintType(Enum):
    """Type de contrainte de groupe.

    MUST_BE_TOGETHER: Les participants doivent toujours être à la même table (cohésif)
    MUST_BE_SEPARATE: Les participants ne doivent jamais être à la même table (exclusif)
    """

    MUST_BE_TOGETHER = "must_be_together"
    MUST_BE_SEPARATE = "must_be_separate"


@dataclass
class GroupConstraint:
    """Contrainte de groupe pour participants.

    Permet de définir des groupes qui doivent être toujours ensemble (cohésifs)
    ou toujours séparés (exclusifs).

    Attributes:
        name: Nom descriptif du groupe (ex: "Couple 1", "Concurrents A-B")
        constraint_type: Type de contrainte (MUST_BE_TOGETHER ou MUST_BE_SEPARATE)
        participant_ids: Set d'IDs participants concernés par la contrainte

    Invariants:
        - len(participant_ids) >= 2 (au moins 2 participants requis)
        - MUST_BE_TOGETHER : tous à la même table dans chaque session
        - MUST_BE_SEPARATE : jamais à la même table

    Example:
        >>> # Couple qui doit rester ensemble
        >>> couple = GroupConstraint(
        ...     name="Couple 1",
        ...     constraint_type=GroupConstraintType.MUST_BE_TOGETHER,
        ...     participant_ids={0, 1}
        ... )
        >>> # Concurrents à séparer
        >>> concurrents = GroupConstraint(
        ...     name="Concurrents A-B",
        ...     constraint_type=GroupConstraintType.MUST_BE_SEPARATE,
        ...     participant_ids={5, 12}
        ... )
    """

    name: str
    constraint_type: GroupConstraintType
    participant_ids: Set[int]

    def __post_init__(self) -> None:
        """Validation basique de la contrainte."""
        if len(self.participant_ids) < 2:
            raise ValueError(
                f"Groupe '{self.name}' doit contenir au moins 2 participants, "
                f"reçu: {len(self.participant_ids)}"
            )


@dataclass
class PlanningConstraints:
    """Ensemble de contraintes pour un planning.

    Regroupe toutes les contraintes de groupes (cohésifs et exclusifs)
    à appliquer lors de la génération du planning.

    Attributes:
        cohesive_groups: Liste groupes "must be together" (toujours même table)
        exclusive_groups: Liste groupes "must be separate" (jamais même table)

    Example:
        >>> constraints = PlanningConstraints(
        ...     cohesive_groups=[
        ...         GroupConstraint("Couple 1", GroupConstraintType.MUST_BE_TOGETHER, {0,1})
        ...     ],
        ...     exclusive_groups=[
        ...         GroupConstraint("Concurrents", GroupConstraintType.MUST_BE_SEPARATE, {5,12})
        ...     ]
        ... )
    """

    cohesive_groups: List[GroupConstraint] = field(default_factory=list)
    exclusive_groups: List[GroupConstraint] = field(default_factory=list)

    def validate(self, config: "PlanningConfig") -> List[str]:
        """Valide contraintes vs configuration planning.

        Vérifie :
        - Groupes cohésifs ne dépassent pas capacité table
        - Pas de participant dans plusieurs groupes cohésifs
        - Pas de conflit cohésif/exclusif (même participants)

        Args:
            config: Configuration du planning (N, X, x, S)

        Returns:
            Liste messages erreur (vide si tout OK)

        Example:
            >>> config = PlanningConfig(N=10, X=2, x=5, S=3)
            >>> constraints = PlanningConstraints(cohesive_groups=[...])
            >>> errors = constraints.validate(config)
            >>> if errors:
            ...     print("Erreurs:", errors)
        """
        errors = []

        # Valider groupes cohésifs
        cohesive_participant_ids: Set[int] = set()

        for group in self.cohesive_groups:
            # Vérifier taille groupe ≤ capacité table
            if len(group.participant_ids) > config.x:
                errors.append(
                    f"❌ Groupe cohésif '{group.name}' ({len(group.participant_ids)} participants) "
                    f"dépasse capacité table ({config.x})"
                )

            # Vérifier pas de participant dans plusieurs groupes cohésifs
            overlap = cohesive_participant_ids & group.participant_ids
            if overlap:
                errors.append(
                    f"❌ Participants {overlap} apparaissent dans plusieurs groupes cohésifs "
                    f"(un participant ne peut être que dans 1 groupe cohésif)"
                )
            cohesive_participant_ids.update(group.participant_ids)

        # Valider cohérence groupes cohésifs vs groupes exclusifs
        for exclusive_group in self.exclusive_groups:
            for cohesive_group in self.cohesive_groups:
                # Si 2+ membres d'un groupe cohésif sont dans un groupe exclusif → conflit logique
                overlap = exclusive_group.participant_ids & cohesive_group.participant_ids
                if len(overlap) >= 2:
                    errors.append(
                        f"❌ Conflit : {overlap} sont cohésifs ('{cohesive_group.name}') "
                        f"mais aussi exclusifs ('{exclusive_group.name}'). "
                        f"Impossible d'être toujours ensemble ET toujours séparés."
                    )

        return errors
