"""Validation de configuration pour le système de planification.

Ce module fournit la validation métier des configurations de planning,
avec messages d'erreur en français (NFR10).

Classes:
    InvalidConfigurationError: Exception pour configurations invalides

Functions:
    validate_config: Valide une configuration selon les contraintes métier
"""

import logging

from src.models import PlanningConfig

logger = logging.getLogger(__name__)


class InvalidConfigurationError(ValueError):
    """Exception levée lors de la détection d'une configuration invalide.

    Cette exception est utilisée pour signaler des violations des contraintes
    métier (capacité insuffisante, paramètres hors limites, etc.).

    Example:
        >>> try:
        ...     validate_config(PlanningConfig(N=50, X=5, x=8, S=3))
        ... except InvalidConfigurationError as e:
        ...     print(e)
        Capacité insuffisante : ...
    """

    pass


def validate_config(config: PlanningConfig) -> None:
    """Valide une configuration de planning selon les contraintes métier.

    Contraintes validées:
        - N ≥ 2 (au moins 2 participants)
        - X ≥ 1 (au moins 1 table)
        - x ≥ 2 (au moins 2 places par table pour permettre rencontres)
        - S ≥ 1 (au moins 1 session)
        - X × x ≥ N (capacité totale suffisante)

    Args:
        config: Configuration à valider

    Raises:
        InvalidConfigurationError: Si une contrainte est violée (message en français)

    Example:
        >>> config = PlanningConfig(N=30, X=5, x=6, S=6)
        >>> validate_config(config)  # OK, pas d'exception
        >>> validate_config(PlanningConfig(N=1, X=5, x=6, S=6))
        Traceback (most recent call last):
        ...
        InvalidConfigurationError: Nombre de participants insuffisant : N = 1 (minimum : 2)

    Complexity:
        Time: O(1)
        Space: O(1)
    """
    # Validation N (participants)
    if config.N < 2:
        raise InvalidConfigurationError(
            f"Nombre de participants insuffisant : N = {config.N} (minimum : 2)"
        )

    # Validation X (tables)
    if config.X < 1:
        raise InvalidConfigurationError(
            f"Nombre de tables insuffisant : X = {config.X} (minimum : 1)"
        )

    # Validation x (capacité par table)
    if config.x < 2:
        raise InvalidConfigurationError(
            f"Capacité par table insuffisante : x = {config.x} (minimum : 2). "
            f"Une table doit accueillir au moins 2 participants pour permettre des rencontres."
        )

    # Validation S (sessions)
    if config.S < 1:
        raise InvalidConfigurationError(
            f"Nombre de sessions insuffisant : S = {config.S} (minimum : 1)"
        )

    # Validation capacité totale (X × x ≥ N)
    total_capacity = config.X * config.x
    if total_capacity < config.N:
        raise InvalidConfigurationError(
            f"Capacité insuffisante : {config.X} tables × {config.x} places = "
            f"{total_capacity} < {config.N} participants. "
            f"Il manque {config.N - total_capacity} place(s)."
        )

    logger.debug(
        f"Configuration validée : N={config.N}, X={config.X}, x={config.x}, S={config.S}"
    )
