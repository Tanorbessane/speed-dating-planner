"""Tests unitaires pour l'évaluation de swaps (src.swap_evaluation).

Test coverage:
    - Fonction pure (pas d'effets de bord)
    - Delta correct (négatif = amélioration, positif = dégradation)
    - Validation erreurs (participants absents)
    - Edge cases
    - Complexité O(x)
"""

import pytest

from src.models import Planning, PlanningConfig, Session
from src.swap_evaluation import evaluate_swap


class TestEvaluateSwap:
    """Tests pour evaluate_swap()."""

    def test_swap_reduces_repeats_beneficial(self) -> None:
        """Test swap bénéfique (réduit répétitions, delta négatif)."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)

        # Historique: (0,1) et (2,3) se sont déjà rencontrés
        met_pairs = {(0, 1), (2, 3)}

        # Session actuelle: table 0 = {0,1,2}, table 1 = {3,4,5}
        # Répétitions AVANT: (0,1) à table 0 → 1 répétition
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # Swap: échanger 1 (table 0) avec 4 (table 1)
        # APRÈS: table 0 = {0,2,4}, table 1 = {1,3,5}
        # Répétitions APRÈS: aucune (0,2), (0,4), (2,4), (1,3), (1,5), (3,5) toutes nouvelles
        # Delta = 0 - 1 = -1 (amélioration !)

        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=1, table2_id=1, p2=4, met_pairs=met_pairs
        )

        assert delta < 0, "Swap devrait être bénéfique (delta négatif)"

    def test_swap_increases_repeats_harmful(self) -> None:
        """Test swap néfaste (augmente répétitions, delta positif)."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)

        # Historique: (0,3) et (1,4) se sont déjà rencontrés
        met_pairs = {(0, 3), (1, 4)}

        # Session actuelle: table 0 = {0,1,2}, table 1 = {3,4,5}
        # Répétitions AVANT: 0 (aucune paire actuelle dans met_pairs)
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # Swap: échanger 1 (table 0) avec 4 (table 1)
        # APRÈS: table 0 = {0,2,4}, table 1 = {1,3,5}
        # Répétitions APRÈS: (1,3) et (0,4)... attendez non
        # APRÈS: table 0 = {0,2,4} → (0,4) pas dans met_pairs
        # APRÈS: table 1 = {1,3,5} → (1,3) pas dans met_pairs
        # Hmm, mauvais exemple

        # Meilleur exemple:
        # Historique: (0,4) et (1,3) déjà rencontrés
        met_pairs2 = {(0, 4), (1, 3)}

        # Swap: échanger 2 (table 0) avec 3 (table 1)
        # AVANT: table 0 = {0,1,2}, table 1 = {3,4,5} → 0 répétitions
        # APRÈS: table 0 = {0,1,3}, table 1 = {2,4,5}
        # table 0 contient (1,3) → répétition !
        # Delta = 1 - 0 = +1 (dégradation)

        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=2, table2_id=1, p2=3, met_pairs=met_pairs2
        )

        assert delta > 0, "Swap devrait être néfaste (delta positif)"

    def test_swap_neutral(self) -> None:
        """Test swap neutre (delta = 0)."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)

        # Historique: aucune rencontre
        met_pairs: set[tuple[int, int]] = set()

        # Session actuelle: table 0 = {0,1,2}, table 1 = {3,4,5}
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # Swap: échanger n'importe qui
        # AVANT: 0 répétitions (aucune paire dans historique)
        # APRÈS: 0 répétitions (toujours aucune paire dans historique)
        # Delta = 0

        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=1, table2_id=1, p2=4, met_pairs=met_pairs
        )

        assert delta == 0, "Swap devrait être neutre (delta = 0)"

    def test_function_is_pure(self) -> None:
        """Test que evaluate_swap ne modifie PAS le planning (fonction pure)."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)
        met_pairs = {(0, 1)}

        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # Sauvegarder état initial
        original_table0 = set(planning.sessions[0].tables[0])
        original_table1 = set(planning.sessions[0].tables[1])

        # Appeler evaluate_swap
        evaluate_swap(
            planning, session_id=0, table1_id=0, p1=1, table2_id=1, p2=4, met_pairs=met_pairs
        )

        # Vérifier que planning n'a PAS été modifié
        assert planning.sessions[0].tables[0] == original_table0
        assert planning.sessions[0].tables[1] == original_table1

    def test_invalid_participant_p1_not_in_table(self) -> None:
        """Test erreur si p1 absent de table1."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)
        met_pairs: set[tuple[int, int]] = set()

        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # p1 = 99 n'est pas dans table 0
        with pytest.raises(ValueError, match="Participant 99 absent"):
            evaluate_swap(
                planning, session_id=0, table1_id=0, p1=99, table2_id=1, p2=4, met_pairs=met_pairs
            )

    def test_invalid_participant_p2_not_in_table(self) -> None:
        """Test erreur si p2 absent de table2."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)
        met_pairs: set[tuple[int, int]] = set()

        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # p2 = 99 n'est pas dans table 1
        with pytest.raises(ValueError, match="Participant 99 absent"):
            evaluate_swap(
                planning, session_id=0, table1_id=0, p1=1, table2_id=1, p2=99, met_pairs=met_pairs
            )

    def test_swap_with_multiple_repeats(self) -> None:
        """Test évaluation avec plusieurs répétitions."""
        config = PlanningConfig(N=6, X=2, x=3, S=1)

        # Historique riche: plusieurs paires déjà rencontrées
        met_pairs = {(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)}

        # Session actuelle: TOUTES les paires sont des répétitions
        sessions = [Session(0, [{0, 1, 2}, {3, 4, 5}])]
        planning = Planning(sessions, config)

        # Répétitions AVANT:
        # Table 0: (0,1), (0,2), (1,2) → 3 répétitions
        # Table 1: (3,4), (3,5), (4,5) → 3 répétitions
        # Total AVANT: 6 répétitions

        # Swap: échanger 2 avec 5
        # APRÈS: table 0 = {0,1,5}, table 1 = {2,3,4}
        # Table 0: (0,1) répétition, (0,5) nouvelle, (1,5) nouvelle → 1 répétition
        # Table 1: (2,3) nouvelle, (2,4) nouvelle, (3,4) répétition → 1 répétition
        # Total APRÈS: 2 répétitions
        # Delta = 2 - 6 = -4 (amélioration significative!)

        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=2, table2_id=1, p2=5, met_pairs=met_pairs
        )

        assert delta < 0, "Swap devrait réduire répétitions"
        assert delta == -4, f"Delta attendu -4, obtenu {delta}"

    def test_swap_between_small_tables(self) -> None:
        """Test swap entre tables de taille 2 (cas minimal)."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        met_pairs = {(0, 1)}

        # Tables minimales: 2 participants chacune
        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        # AVANT: table 0 a (0,1) → 1 répétition
        # APRÈS: swap 1 avec 2 → table 0 = {0,2}, table 1 = {1,3}
        # Table 0: (0,2) nouvelle → 0 répétitions
        # Table 1: (1,3) nouvelle → 0 répétitions
        # Delta = 0 - 1 = -1

        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=1, table2_id=1, p2=2, met_pairs=met_pairs
        )

        assert delta == -1

    def test_swap_in_multi_session_planning(self) -> None:
        """Test évaluation dans planning multi-sessions."""
        config = PlanningConfig(N=6, X=2, x=3, S=3)

        met_pairs = {(0, 1), (2, 3)}

        sessions = [
            Session(0, [{0, 1, 2}, {3, 4, 5}]),
            Session(1, [{0, 3, 4}, {1, 2, 5}]),
            Session(2, [{0, 2, 5}, {1, 3, 4}]),
        ]
        planning = Planning(sessions, config)

        # Évaluer swap dans session 1
        # Session 1 actuelle: table 0 = {0,3,4}, table 1 = {1,2,5}
        # Répétitions AVANT: (1,2) dans met_pairs → 1 répétition
        # Swap: 4 (table 0) avec 2 (table 1)
        # APRÈS: table 0 = {0,2,3}, table 1 = {1,4,5}
        # Table 0: (2,3) dans met_pairs → 1 répétition
        # Table 1: aucune paire dans met_pairs → 0 répétitions
        # Delta = 1 - 1 = 0 (neutre)

        delta = evaluate_swap(
            planning, session_id=1, table1_id=0, p1=4, table2_id=1, p2=2, met_pairs=met_pairs
        )

        assert delta == 0

    def test_return_type_is_int(self) -> None:
        """Test que evaluate_swap retourne bien un int."""
        config = PlanningConfig(N=4, X=2, x=2, S=1)
        met_pairs: set[tuple[int, int]] = set()

        sessions = [Session(0, [{0, 1}, {2, 3}])]
        planning = Planning(sessions, config)

        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=1, table2_id=1, p2=2, met_pairs=met_pairs
        )

        assert isinstance(delta, int)

    def test_complexity_linear_in_table_size(self) -> None:
        """Test que complexité est O(x) (linéaire en taille table).

        Note: Test conceptuel, vérifie que grandes tables fonctionnent.
        """
        config = PlanningConfig(N=20, X=2, x=10, S=1)
        met_pairs: set[tuple[int, int]] = set()

        # Tables de 10 participants chacune
        sessions = [Session(0, [set(range(10)), set(range(10, 20))])]
        planning = Planning(sessions, config)

        # Doit s'exécuter rapidement même avec tables de taille 10
        delta = evaluate_swap(
            planning, session_id=0, table1_id=0, p1=5, table2_id=1, p2=15, met_pairs=met_pairs
        )

        assert isinstance(delta, int)
