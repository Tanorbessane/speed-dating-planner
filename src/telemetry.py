"""Module de telemetry et observabilité pour tracking performance.

Ce module fournit des decorators et utilitaires pour monitorer les performances
des opérations critiques de l'application.

Usage:
    from src.telemetry import track_performance

    @track_performance("generate_planning")
    def generate_optimized_planning(config, seed=42):
        ...

Functions:
    track_performance: Decorator pour tracker latency et status d'opérations
    log_metric: Logger une métrique custom
    log_error: Logger une erreur avec contexte
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

# Type variable pour préserver types dans decorator
F = TypeVar('F', bound=Callable[..., Any])


def track_performance(operation_name: str, log_args: bool = False) -> Callable[[F], F]:
    """Decorator pour tracker performance d'une opération critique.

    Mesure le temps d'exécution, log le statut (success/error), et capture
    les erreurs pour observabilité production.

    Args:
        operation_name: Nom descriptif de l'opération (ex: "generate_planning")
        log_args: Si True, log les arguments de la fonction (défaut: False, pour éviter logs volumin...

)

    Returns:
        Decorator qui wrap la fonction avec tracking

    Example:
        >>> @track_performance("compute_metrics")
        >>> def compute_metrics(planning, config):
        >>>     # Logic here
        >>>     return metrics

        >>> # Logs automatiques:
        >>> # INFO: Performance: compute_metrics completed in 0.42s
        >>> # Extra: {"operation": "compute_metrics", "duration_seconds": 0.42, "status": "success"}

    Note:
        Le decorator préserve la signature et les annotations de type
        de la fonction originale.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            # Context pour logging structuré
            context: Dict[str, Any] = {
                "operation": operation_name,
                "function": func.__name__,
            }

            # Log arguments si demandé (attention: peut être verbeux)
            if log_args:
                context["args_count"] = len(args)
                context["kwargs_keys"] = list(kwargs.keys())

            try:
                # Exécuter fonction originale
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Log succès
                context["duration_seconds"] = round(elapsed, 3)
                context["status"] = "success"

                logger.info(
                    f"Performance: {operation_name} completed in {elapsed:.3f}s",
                    extra=context
                )

                return result

            except Exception as e:
                elapsed = time.time() - start_time

                # Log erreur
                context["duration_seconds"] = round(elapsed, 3)
                context["status"] = "error"
                context["error_type"] = type(e).__name__
                context["error_message"] = str(e)

                logger.error(
                    f"Performance: {operation_name} failed after {elapsed:.3f}s - {type(e).__name__}: {e}",
                    extra=context,
                    exc_info=False  # Pas de stack trace ici (déjà loggé ailleurs)
                )

                # Re-raise l'exception (ne pas masquer)
                raise

        return cast(F, wrapper)

    return decorator


def log_metric(metric_name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None) -> None:
    """Log une métrique custom pour monitoring.

    Args:
        metric_name: Nom de la métrique (ex: "planning_generations_total")
        value: Valeur numérique de la métrique
        unit: Unité optionnelle (ex: "seconds", "count", "participants")
        tags: Tags additionnels pour filtrage (ex: {"tier": "pro", "N_range": "100-300"})

    Example:
        >>> log_metric("planning_generations_total", 1, unit="count", tags={"tier": "pro"})
        >>> log_metric("equity_gap_achieved", 0.5, unit="gap", tags={"N": "100"})

    Note:
        En production, ces métriques peuvent être envoyées vers:
        - Prometheus (via prometheus_client)
        - CloudWatch (AWS)
        - Datadog
        - Grafana Cloud
    """
    context = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "tags": tags or {},
        "timestamp": time.time(),
    }

    logger.info(
        f"Metric: {metric_name}={value}{unit}",
        extra=context
    )


def log_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "ERROR"
) -> None:
    """Log une erreur avec contexte enrichi pour debugging.

    Args:
        error: Exception capturée
        operation: Nom de l'opération qui a échoué
        context: Contexte additionnel (config, user_id, etc.)
        severity: Niveau de sévérité ("WARNING", "ERROR", "CRITICAL")

    Example:
        >>> try:
        >>>     planning = generate_optimized_planning(config)
        >>> except InvalidConfigurationError as e:
        >>>     log_error(e, "generate_planning", context={"N": config.N, "user_id": 123})

    Note:
        En production, ces erreurs peuvent être envoyées vers Sentry pour tracking.
    """
    error_context = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "severity": severity,
        **(context or {})
    }

    log_method = getattr(logger, severity.lower(), logger.error)
    log_method(
        f"Error in {operation}: {type(error).__name__} - {error}",
        extra=error_context,
        exc_info=True  # Include stack trace
    )


# Métriques globales (optionnel, pour tracking in-memory si besoin)
_METRICS_STORE: Dict[str, float] = {}


def record_metric(metric_name: str, value: float) -> None:
    """Enregistre une métrique dans le store in-memory.

    Utile pour tracking cumulatif (ex: nombre total de générations).

    Args:
        metric_name: Nom de la métrique
        value: Valeur à enregistrer (écrase précédente)

    Example:
        >>> record_metric("generations_count", 42)
        >>> record_metric("average_duration_ms", 850.5)
    """
    _METRICS_STORE[metric_name] = value
    logger.debug(f"Metric recorded: {metric_name}={value}")


def get_metric(metric_name: str) -> Optional[float]:
    """Récupère une métrique du store in-memory.

    Args:
        metric_name: Nom de la métrique

    Returns:
        Valeur de la métrique ou None si non trouvée

    Example:
        >>> count = get_metric("generations_count")
        >>> print(f"Générations: {count}")
    """
    return _METRICS_STORE.get(metric_name)


def get_all_metrics() -> Dict[str, float]:
    """Récupère toutes les métriques du store in-memory.

    Returns:
        Dictionnaire {metric_name: value}

    Example:
        >>> metrics = get_all_metrics()
        >>> print(f"Total metrics: {len(metrics)}")
    """
    return _METRICS_STORE.copy()


def reset_metrics() -> None:
    """Reset toutes les métriques in-memory.

    Utile pour tests ou resets périodiques.

    Example:
        >>> reset_metrics()
    """
    global _METRICS_STORE
    _METRICS_STORE = {}
    logger.debug("Metrics store reset")


# ============================================================================
# HELPERS POUR INTÉGRATIONS TIERCES
# ============================================================================

def configure_sentry(dsn: str, environment: str = "production", traces_sample_rate: float = 0.1) -> None:
    """Configure Sentry pour error tracking (optionnel).

    Args:
        dsn: Sentry DSN (depuis dashboard Sentry)
        environment: Environnement ("development", "staging", "production")
        traces_sample_rate: Taux d'échantillonnage pour performance monitoring (0.0-1.0)

    Example:
        >>> # Dans app/main.py ou src/__init__.py
        >>> from src.telemetry import configure_sentry
        >>> import os
        >>> if os.getenv("SENTRY_DSN"):
        >>>     configure_sentry(os.getenv("SENTRY_DSN"), environment="production")

    Note:
        Nécessite `pip install sentry-sdk`
    """
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            # Capture 10% des transactions pour performance monitoring
            profiles_sample_rate=traces_sample_rate,
        )
        logger.info(f"Sentry configured for environment: {environment}")

    except ImportError:
        logger.warning(
            "Sentry SDK not installed. Install with: pip install sentry-sdk"
        )


def configure_json_logging() -> None:
    """Configure logging au format JSON pour parsing par outils (CloudWatch, etc.).

    Example:
        >>> # Dans app/main.py au démarrage
        >>> from src.telemetry import configure_json_logging
        >>> configure_json_logging()

    Note:
        Nécessite `pip install python-json-logger`
    """
    try:
        from pythonjsonlogger import jsonlogger

        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        logHandler.setFormatter(formatter)

        # Appliquer au root logger
        root_logger = logging.getLogger()
        root_logger.handlers = [logHandler]
        root_logger.setLevel(logging.INFO)

        logger.info("JSON logging configured")

    except ImportError:
        logger.warning(
            "python-json-logger not installed. Install with: pip install python-json-logger"
        )
