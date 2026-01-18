# 8. Performance et Scalabilité

## 8.1 Analyse de Complexité

### Phase 1 : Génération Baseline
- **Temps :** O(N × S)
- **Mémoire :** O(N × S × X) pour stocker planning
- **Performance mesurée :** N=1000, S=25 en ~50ms

### Phase 2 : Amélioration Locale
- **Temps pire cas :** O(iter × S × X² × x²)
- **Temps pratique :** O(iter × S × X × x) grâce plateau local (iter << 100)
- **Mémoire :** O(N²) pour historique (pire cas), pratiquement O(S × X × x²)
- **Performance mesurée :** N=300, S=15 amélioration en ~2s

### Phase 3 : Enforcement Équité
- **Temps :** O(S × N) pour swaps ciblés
- **Mémoire :** O(N) pour tracking rencontres par participant
- **Performance mesurée :** N=1000 enforcement en <500ms

### Export CSV/JSON
- **Temps :** O(N × S)
- **Mémoire :** O(N × S) buffer écriture
- **Performance mesurée :** N=1000, S=25 export en <100ms

## 8.2 Optimisations Implémentées

**Optimisation 1 : Arrêt Plateau Local**
- Évite itérations inutiles (gain 30-50% temps Phase 2)

**Optimisation 2 : Paires Normalisées**
- `(min(i,j), max(i,j))` évite duplications (gain 50% mémoire historique)

**Optimisation 3 : Sets Python Natifs**
- Lookup O(1) pour appartenance table/paires

**Optimisation 4 : Stride Coprime**
- Rotation efficace sans calculs coûteux

## 8.3 Limites et Scalabilité

**Limites MVP :**
- N > 1000 : non testé, peut dépasser 30s (NFR3)
- S > 50 : temps Phase 2 augmente linéairement
- x > 20 : complexité swaps (x²) devient significative

**Plan de Scalabilité Post-MVP :**

1. **Parallélisation Phase 2** (Epic 5)
   - Swaps sur sessions indépendantes en parallèle
   - Gain estimé : 2-4x sur machines multi-core

2. **Historique Incrémental** (Epic 5)
   - Tracking incrémental swaps (éviter recalcul complet)
   - Gain mémoire + 20% temps Phase 2

3. **Mode Exact CSP pour Petits N** (Epic 5)
   - OR-Tools CP-SAT pour N≤50 (garantie optimum)
   - Bascule automatique selon taille

---
