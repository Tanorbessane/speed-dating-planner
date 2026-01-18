# 4. Modèles de Données

## 4.1 Dataclasses Complètes

Les modèles de données complets sont définis dans la section 3.1. Voici un récapitulatif des choix de design :

**Choix 1 : `Table = Set[int]` (type alias)**
- **Avantages :** Garantit unicité participants, vérification O(1) appartenance
- **Alternative rejetée :** `List[int]` (permet duplications, moins sémantique)

**Choix 2 : `PlanningConfig` frozen (immutable)**
- **Avantages :** Thread-safe, hashable, prévient modifications accidentelles
- **Alternative rejetée :** Mutable (risques side-effects)

**Choix 3 : `Planning` contient sa `config`**
- **Avantages :** Self-documenting, facilite export avec métadonnées
- **Alternative rejetée :** Passer config séparément (duplication paramètres)

**Choix 4 : `PlanningMetrics` avec @property equity_gap**
- **Avantages :** Métrique dérivée toujours cohérente, API propre
- **Alternative rejetée :** Stocker equity_gap (risque désynchronisation)

## 4.2 Invariants Garantis

Les structures de données garantissent les invariants suivants :

```python
# Invariant 1 : Tous participants assignés exactement 1 fois par session
for session in planning.sessions:
    all_participants = set()
    for table in session.tables:
        all_participants.update(table)
    assert len(all_participants) == planning.config.N
    assert all_participants == set(range(planning.config.N))

# Invariant 2 : Capacité tables respectée
for session in planning.sessions:
    for table in session.tables:
        assert len(table) <= planning.config.x

# Invariant 3 : Écart taille tables ≤1 (FR7)
for session in planning.sessions:
    sizes = [len(table) for table in session.tables]
    assert max(sizes) - min(sizes) <= 1

# Invariant 4 : Équité ±1 (FR6) après pipeline complet
assert metrics.equity_gap <= 1
```

---
