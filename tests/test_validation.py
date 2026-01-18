"""Tests unitaires pour la validation de configuration (src.validation).

Ce module teste la fonction validate_config et l'exception InvalidConfigurationError.

Test coverage:
    - Configurations valides (pas d'exception)
    - Configurations invalides (exceptions avec messages français)
    - Validation de chaque contrainte métier
"""

import pytest

from src.models import PlanningConfig
from src.validation import InvalidConfigurationError, validate_config


class TestValidateConfig:
    """Tests pour validate_config()."""

    def test_valid_config_small(self) -> None:
        """Test configuration valide (petit événement)."""
        config = PlanningConfig(N=6, X=2, x=3, S=2)
        validate_config(config)  # Ne doit pas lever d'exception

    def test_valid_config_medium(self) -> None:
        """Test configuration valide (événement moyen)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        validate_config(config)  # Ne doit pas lever d'exception

    def test_valid_config_large(self) -> None:
        """Test configuration valide (grand événement)."""
        config = PlanningConfig(N=100, X=20, x=5, S=10)
        validate_config(config)  # Ne doit pas lever d'exception

    def test_valid_config_exact_capacity(self) -> None:
        """Test configuration avec capacité exacte (X × x == N)."""
        config = PlanningConfig(N=30, X=5, x=6, S=6)
        assert config.total_capacity == config.N
        validate_config(config)  # OK

    def test_valid_config_excess_capacity(self) -> None:
        """Test configuration avec capacité excédentaire (X × x > N)."""
        config = PlanningConfig(N=25, X=5, x=6, S=6)
        assert config.total_capacity > config.N
        validate_config(config)  # OK, capacity excess allowed

    def test_invalid_n_too_small(self) -> None:
        """Test N < 2 (insuffisant)."""
        config = PlanningConfig(N=1, X=5, x=6, S=6)

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "participants insuffisant" in str(exc_info.value).lower()
        assert "N = 1" in str(exc_info.value)
        assert "minimum : 2" in str(exc_info.value)

    def test_invalid_n_zero(self) -> None:
        """Test N = 0."""
        config = PlanningConfig(N=0, X=5, x=6, S=6)

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "participants" in str(exc_info.value).lower()

    def test_invalid_x_too_small(self) -> None:
        """Test X < 1 (insuffisant)."""
        config = PlanningConfig(N=30, X=0, x=6, S=6)

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "tables insuffisant" in str(exc_info.value).lower()
        assert "X = 0" in str(exc_info.value)
        assert "minimum : 1" in str(exc_info.value)

    def test_invalid_capacity_too_small(self) -> None:
        """Test x < 2 (insuffisant pour rencontres)."""
        config = PlanningConfig(N=30, X=5, x=1, S=6)

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "capacité par table insuffisante" in str(exc_info.value).lower()
        assert "x = 1" in str(exc_info.value)
        assert "minimum : 2" in str(exc_info.value)

    def test_invalid_capacity_zero(self) -> None:
        """Test x = 0."""
        config = PlanningConfig(N=30, X=5, x=0, S=6)

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "capacité" in str(exc_info.value).lower()

    def test_invalid_s_too_small(self) -> None:
        """Test S < 1 (insuffisant)."""
        config = PlanningConfig(N=30, X=5, x=6, S=0)

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "sessions insuffisant" in str(exc_info.value).lower()
        assert "S = 0" in str(exc_info.value)
        assert "minimum : 1" in str(exc_info.value)

    def test_invalid_total_capacity_insufficient(self) -> None:
        """Test X × x < N (capacité totale insuffisante)."""
        config = PlanningConfig(N=50, X=5, x=8, S=3)
        # 5 × 8 = 40 < 50

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        error_message = str(exc_info.value)
        assert "capacité insuffisante" in error_message.lower()
        assert "5 tables × 8 places = 40 < 50 participants" in error_message
        assert "manque 10 place(s)" in error_message.lower()

    def test_invalid_total_capacity_off_by_one(self) -> None:
        """Test X × x = N - 1 (manque 1 place)."""
        config = PlanningConfig(N=31, X=5, x=6, S=6)
        # 5 × 6 = 30 < 31

        with pytest.raises(InvalidConfigurationError) as exc_info:
            validate_config(config)

        assert "manque 1 place(s)" in str(exc_info.value).lower()

    def test_error_messages_french(self) -> None:
        """Test que tous les messages d'erreur sont en français (NFR10)."""
        test_cases = [
            (PlanningConfig(N=1, X=5, x=6, S=6), "participants"),
            (PlanningConfig(N=30, X=0, x=6, S=6), "tables"),
            (PlanningConfig(N=30, X=5, x=1, S=6), "capacité"),
            (PlanningConfig(N=30, X=5, x=6, S=0), "sessions"),
            (PlanningConfig(N=50, X=5, x=8, S=3), "capacité insuffisante"),
        ]

        for config, expected_keyword in test_cases:
            with pytest.raises(InvalidConfigurationError) as exc_info:
                validate_config(config)

            error_message = str(exc_info.value)
            # Vérifier absence de mots anglais communs
            assert "insufficient" not in error_message.lower()
            assert "error" not in error_message.lower()
            assert "invalid" not in error_message.lower()
            # Vérifier présence du mot clé français
            assert expected_keyword in error_message.lower()


class TestInvalidConfigurationError:
    """Tests pour l'exception InvalidConfigurationError."""

    def test_is_value_error(self) -> None:
        """Test que InvalidConfigurationError hérite de ValueError."""
        assert issubclass(InvalidConfigurationError, ValueError)

    def test_can_be_raised(self) -> None:
        """Test levée de l'exception."""
        with pytest.raises(InvalidConfigurationError):
            raise InvalidConfigurationError("Test message")

    def test_message_preserved(self) -> None:
        """Test que le message d'erreur est préservé."""
        message = "Configuration invalide : capacité insuffisante"

        with pytest.raises(InvalidConfigurationError) as exc_info:
            raise InvalidConfigurationError(message)

        assert str(exc_info.value) == message
