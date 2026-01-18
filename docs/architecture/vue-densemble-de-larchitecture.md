# 1. Vue d'Ensemble de l'Architecture

## 1.1 Principe Architectural

L'architecture suit un pattern **Pipeline Hybride à 3 Phases** séquentiel et modulaire :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE PIPELINE HYBRIDE                        │
└─────────────────────────────────────────────────────────────────────────┘

   INPUT                                                          OUTPUT
     │                                                               │
     ▼                                                               │
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌────┴────┐
│ Planning │      │   PHASE 1    │      │   PHASE 2    │      │ Planning│
│  Config  │─────▶│   BASELINE   │─────▶│ AMÉLIORATION │─────▶│Optimisé │
│  (N,X,   │      │  GENERATION  │      │    LOCALE    │      │  avec   │
│  x,S)    │      │              │      │              │      │Métriques│
└──────────┘      └──────┬───────┘      └──────┬───────┘      └─────────┘
                         │                     │                    ▲
                         │                     │                    │
                         ▼                     ▼                    │
                  Planning Baseline     Planning Amélioré          │
                  (valide, rapide)      (répétitions ↓)            │
                         │                     │                    │
                         │                     ▼                    │
                         │              ┌──────────────┐            │
                         │              │   PHASE 3    │            │
                         └─────────────▶│   ÉQUITÉ     │────────────┘
                                        │ ENFORCEMENT  │
                                        │              │
                                        └──────────────┘
                                        Planning Final
                                        (équité ±1)


┌─────────────────────────────────────────────────────────────────────────┐
│                       FLUX DE DONNÉES DÉTAILLÉ                          │
└─────────────────────────────────────────────────────────────────────────┘

1. VALIDATION
   PlanningConfig ──▶ [validate_config()] ──▶ Exception ou ✓

2. GÉNÉRATION BASELINE
   Config + Seed ──▶ [generate_baseline()] ──▶ Planning
                                                    │
                                                    ├──▶ List[Session]
                                                    └──▶ Session = List[Set[int]]

3. CALCUL HISTORIQUE
   Planning ──▶ [compute_meeting_history()] ──▶ Set[Tuple[int,int]]
                                                  (paires rencontrées)

4. AMÉLIORATION LOCALE
   Planning + MeetingHistory ──▶ [improve_planning()] ──▶ Planning Amélioré
        │
        ├──▶ [evaluate_swap()] (itérations)
        └──▶ Arrêt plateau local

5. ENFORCEMENT ÉQUITÉ
   Planning Amélioré ──▶ [enforce_equity()] ──▶ Planning Final
        │
        └──▶ Swaps ciblés pour écart ≤1

6. MÉTRIQUES
   Planning Final ──▶ [compute_metrics()] ──▶ PlanningMetrics
                                                  │
                                                  ├──▶ Paires uniques
                                                  ├──▶ Répétitions
                                                  └──▶ Stats équité

7. EXPORT
   Planning + Config ──▶ [export_to_csv()] ──▶ fichier.csv
                     ──▶ [export_to_json()] ──▶ fichier.json
```

## 1.2 Garanties Architecturales

**Garanties de Correction :**
- ✅ Tous les participants assignés exactement 1 fois par session
- ✅ Contraintes de capacité respectées (tables ≤ x personnes)
- ✅ Équité stricte : `max_unique - min_unique ≤ 1`
- ✅ Plannings reproductibles (seed fixe → résultat déterministe)

**Garanties de Performance :**
- ✅ Phase 1 (Baseline) : O(N × S) - linéaire, rapide
- ✅ Phase 2 (Amélioration) : O(iter × S × swaps) - contrôlée par max_iterations
- ✅ Phase 3 (Équité) : O(S × N) - post-traitement léger
- ✅ Total : N≤100 en <2s, N≤300 en <5s, N≤1000 en <30s

**Garanties de Modularité :**
- ✅ Chaque phase testable indépendamment
- ✅ Pas de dépendances circulaires
- ✅ Inversion de dépendances (CLI/export dépendent de core, pas l'inverse)

---
