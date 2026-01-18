# Brainstorming Session Results

**Session Date:** 2026-01-10
**Facilitator:** Business Analyst Mary
**Participant:** Tanor Bessane

---

## Executive Summary

**Topic:** Optimisation de Rencontres - Algorithme de Tables Rotatives pour Speed Dating / Networking

**Session Goals:**
Concevoir une solution algorithmique complète pour répartir N participants sur X tables (capacité max x) durant S sessions, maximisant les rencontres uniques tout en minimisant les répétitions. L'objectif est de couvrir les approches algorithmiques, structures de données, stratégies d'implémentation, gestion des cas limites et contraintes de performance.

**Techniques Used:**
- First Principles Thinking (déconstruction du problème)
- Analogical Thinking (SGP, Round-Robin, Graph Theory)
- Question Storming (identification zones d'incertitude)
- Morphological Analysis (exploration combinaisons architecturales)

**Total Ideas Generated:** 25+ approches et variantes explorées

### Key Themes Identified:
- Architecture hybride pragmatique (baseline rapide + amélioration locale)
- Équité individuelle prioritaire sur optimisation globale
- Gestion robuste des edge cases (retardataires, abandons, tables déséquilibrées)
- Performance scalable jusqu'à N=1000 participants
- Métriques multi-objectif pour évaluation holistique

---

## Technique Sessions

### First Principles Thinking - 15 min

**Description:** Déconstruction du problème en éléments fondamentaux pour établir une compréhension solide des contraintes et objectifs.

**Ideas Generated:**

1. **Métrique d'optimisation** : Maximiser paires uniques U(i) par participant et globalement U_total, minimiser répétitions R_total via score composite `Score = #paires_uniques - λ × #répétitions`

2. **Contraintes dures** : N participants fixes, X tables fixes, capacité max x, 1 table/session/participant, S sessions prédéfinies

3. **Contraintes souples** : Zéro répétition (idéal mais pas toujours faisable), équilibrage tables (écart ≤1), équité (répétitions réparties équitablement)

4. **Trade-offs acceptables** : Accepter répétitions minimales quand impossible, privilégier équité individuelle vs score global selon contexte

5. **Modélisation mathématique** : Problème = design de rounds créant des cliques de taille ≤x, avec suite de partitions couvrant maximum de paires uniques

6. **Bornes théoriques** :
   - Max rencontrable par participant : N-1
   - Nouvelles rencontres/session : k-1 (où k=taille table)
   - Sessions min pour zéro répétition : S_min = ceil((N-1)/(x-1))
   - Condition d'impossibilité : S × (x-1) < N-1

**Insights Discovered:**
- Le problème est structurellement un Social Golfer Problem généralisé
- La résolvabilité dépend non seulement des bornes comptables mais aussi de contraintes combinatoires (NP-complet)
- Deux niveaux d'impossibilité : borne d'opportunité individuelle ET borne structurelle (pigeonhole sur paires globales)

**Notable Connections:**
- Lien direct avec théorie des designs combinatoires (BIBD, Steiner systems)
- Analogie forte avec problèmes de scheduling et graph matching

---

### Analogical Thinking - 20 min

**Description:** Exploration de problèmes analogues classiques pour identifier techniques algorithmiques adaptables.

**Ideas Generated:**

1. **Approche SGP (Social Golfer Problem)** :
   - Formulation CSP/SAT/ILP avec variables assign[p,s]=table_id
   - Contraintes : capacité tables, unicité assignment, non-répétition paires
   - Backtracking + propagation avec heuristiques (participant le plus contraint d'abord)
   - Constructions algébriques pour paramètres "beaux" (grilles, corps finis)

2. **Approche Round-Robin généralisée** :
   - Rotation systématique par permutations contrôlées
   - Méthode "blocs + décalages" avec strides coprimes
   - Interleaving/tressage pour mélange rapide
   - Complexité O(N×S), baseline excellente

3. **Approche basée graphe** :
   - Modélisation : sommets=participants, arêtes=rencontres (pondérées par fréquence)
   - Objectif : construire cliques de taille x minimisant poids intra-clique
   - Heuristique gloutonne : ajouter participants minimisant rencontres déjà faites
   - Efficace pour minimisation répétitions même quand parfait impossible

4. **Stratégie hybride en 3 couches** :
   - Baseline rapide (round-robin) → planning immédiat
   - Amélioration heuristique (graphe/local search) → réduction répétitions
   - Mode preuve optionnel (CP-SAT) → validation petites instances

**Insights Discovered:**
- Aucune approche unique ne domine tous les critères (qualité/vitesse/garantie)
- L'hybridation permet de combiner avantages : rapidité baseline + qualité amélioration locale
- Les constructions algébriques existent mais limitées à configurations spécifiques

**Notable Connections:**
- Round-robin = cas particulier de Latin squares
- Graph matching = problème de partitionnement en cliques avec contraintes historiques
- Backtracking SGP = même structure que Sudoku solver mais espace plus grand

---

### Question Storming - 15 min

**Description:** Génération de questions critiques pour identifier zones d'incertitude et angles morts avant convergence.

**Ideas Generated:**

**Catégorie Implémentation Pratique :**
1. Quelle structure permet vérification O(1) si deux participants se sont rencontrés, mémoire-efficiente pour N≤1000 ?
2. Comment représenter historique : matrice booléenne, bitsets, hash de paires, ou graphe pondéré ?
3. Jusqu'à quelle taille N/S la stratégie hybride reste interactive (quelques secondes) sans parallélisation ?
4. Comment découpler génération baseline et amélioration locale sans casser lisibilité code ?

**Catégorie Validation & Tests :**
5. Quelle métrique unique robuste pour comparer deux plannings (global vs équité individuelle) ?
6. Comment générer automatiquement instances "dures" (proches impossibilité) pour stress-test ?
7. Comment détecter plateau local (amélioration supplémentaire inutile) ?
8. Valider niveau global (paires totales) ou niveau individuel (max/min rencontres par participant) ?

**Catégorie Edge Cases & Robustesse :**
9. Que faire si N n'est pas multiple de x (tables partielles) sans trop de répétitions ?
10. Retardataire/abandon : recalculer sessions futures uniquement ou ajuster localement session courante ?
11. Comment garantir équité quand certains participants ont raté sessions ?
12. Peut-on insérer dynamiquement participant sans dégrader fortement score global ?

**Catégorie Optimisation & Trade-offs :**
13. Privilégier équité individuelle stricte ou optimisation globale (score total maximal) ?
14. À partir de quels seuils (N, S, x) abandonner recherche exacte pour heuristique pure ?
15. Comment pondérer objectifs : répétitions minimales, équilibre tables, stabilité planning ?
16. Jusqu'où accepter répétitions si réduction drastique temps calcul ou complexité code ?

**Insights Discovered:**
- Les vraies difficultés ne sont pas dans l'algorithme pur mais dans les décisions de design (trade-offs, robustesse, UX)
- La question de l'équité individuelle vs optimisation globale est centrale pour l'expérience utilisateur
- La gestion dynamique (retardataires/abandons) nécessite une architecture découplée

**Notable Connections:**
- Question 13 (équité vs global) rejoint des problèmes éthiques d'allocation de ressources
- Questions performance (3, 14) déterminent la viabilité pratique en production

---

### Morphological Analysis - 25 min

**Description:** Décomposition de la solution en 5 dimensions architecturales critiques et exploration des combinaisons viables.

**Ideas Generated:**

**Dimension 1 - Stratégie Algorithmique Principale :**
- Option A : Exact (CSP/SAT) uniquement → qualité max, risque timeout
- Option B : Heuristique pure (round-robin + greedy) → rapide, qualité non garantie
- **Option C : Hybride (baseline → amélioration locale) → équilibre pragmatique** ✅ CHOISI
- Option D : Adaptative (exact si petit N, sinon heuristique) → complexité code

**Dimension 2 - Structure de Données Historique :**
- Option A : Matrice N×N booléenne → O(1) lookup, O(N²) mémoire
- **Option B : Dict/HashMap de paires → O(1) lookup, mémoire proportionnelle** ✅ CHOISI
- Option C : Bitset compacté → très mémoire-efficace
- Option D : Graphe pondéré (NetworkX) → flexible pour heuristiques graphe

**Dimension 3 - Métrique de Qualité :**
- Option A : Score = #paires_uniques - λ×#répétitions (global)
- Option B : Score = min(rencontres_uniques/participant) (équité max-min)
- Option C : Score = (moyenne, écart-type) rencontres uniques (équilibre)
- **Option D : Multi-objectif Pareto (global/équité/équilibrage)** ✅ CHOISI

**Dimension 4 - Gestion Edge Cases :**
- Option A : Pas de gestion dynamique (planning figé)
- Option B : Insertion greedy locale (sans recalcul global)
- **Option C : Recalcul partiel (sessions futures uniquement)** ✅ CHOISI
- Option D : Recalcul complet avec contraintes stabilité

**Dimension 5 - Stratégie Trade-offs :**
- Option A : Minimiser répétitions coûte que coûte (tables déséquilibrées OK)
- Option B : Équilibrage tables prioritaire (répétitions tolérées si équitables)
- **Option C : Équité individuelle stricte (chaque participant score ±1)** ✅ CHOISI
- Option D : Optimisation globale (score total prime sur équité)

**Insights Discovered:**
- Les 5 dimensions sont orthogonales : choix indépendants mais doivent être cohérents
- Le choix D5 (équité stricte) influence fortement l'algorithme d'amélioration (phase 3)
- La combinaison choisie (C-B-D-C-C) définit une architecture "humain-centric" vs "score-centric"

**Notable Connections:**
- D1×D4 : L'approche hybride facilite le recalcul partiel (modularité)
- D3×D5 : Métrique multi-objectif permet de mesurer l'équité choisie en D5
- D2 influence directement la complexité de D1 (structure HashMap parfaite pour swaps locaux)

---

## Idea Categorization

### Immediate Opportunities
*Ideas ready to implement now*

1. **Baseline Round-Robin Généralisé**
   - Description: Algorithme de rotation systématique avec stride pour générer planning initial en O(N×S)
   - Why immediate: Indépendant des autres composants, facile à tester, valeur immédiate
   - Resources needed: Structures de base (Planning, Session, Table), fonction de permutation

2. **Structures de Données Fondamentales**
   - Description: Définir `Planning`, `Session`, `Table`, `Metrics`, `Config` et `met_pairs: Set[Tuple[int,int]]`
   - Why immediate: Prérequis à toute implémentation, design stabilisé
   - Resources needed: Python 3.10+ (dataclasses, type hints)

3. **Fonction de Calcul Métriques**
   - Description: `compute_metrics()` retournant paires uniques, répétitions, stats équité, équilibrage tables
   - Why immediate: Nécessaire pour tests et validation, logique claire
   - Resources needed: Accès à planning et historique rencontres

4. **Export CSV/JSON**
   - Description: Formatter planning en sortie exploitable (session_id, table_id, participants)
   - Why immediate: Indépendant de l'algo, valeur utilisateur directe
   - Resources needed: Librairies standard (csv, json)

### Future Innovations
*Ideas requiring development/research*

1. **Amélioration Locale par Swaps Gloutons**
   - Description: Phase 2 de l'architecture hybride, itérations de swaps pour minimiser répétitions
   - Development needed: Heuristique `evaluate_swap()`, gestion plateau local, tests performance
   - Timeline estimate: Sprint 3 (après baseline fonctionnelle)

2. **Enforcement de l'Équité Stricte (±1)**
   - Description: Post-traitement garantissant écart max 1 rencontre unique entre tous participants
   - Development needed: Algorithme de swaps ciblés équité, métriques validation
   - Timeline estimate: Sprint 4 (après amélioration locale)

3. **Gestion Dynamique Retardataires/Abandons**
   - Description: Recalcul partiel sessions futures lors d'événement dynamique
   - Development needed: Historique figé vs modifiable, insertion greedy, tests robustesse
   - Timeline estimate: Sprint 4 (après architecture stable)

4. **Mode Exact CP-SAT (Optionnel)**
   - Description: Solver CSP via OR-Tools CP-SAT pour instances petites/moyennes (N≤50)
   - Development needed: Formulation contraintes, intégration OR-Tools, benchmarks vs heuristique
   - Timeline estimate: Post-MVP (amélioration qualité pour petits cas)

5. **Constructions Algébriques (Cas Spéciaux)**
   - Description: Détection paramètres "beaux" (N, X, x avec structure algébrique) et génération directe
   - Development needed: Recherche théorique, implémentation cas particuliers (Latin squares, etc.)
   - Timeline estimate: Recherche long terme (amélioration élégance)

### Moonshots
*Ambitious, transformative concepts*

1. **Optimisation Multi-Objectif Pareto Automatique**
   - Description: Génération de plusieurs plannings sur front Pareto (global/équité/équilibrage) avec choix utilisateur
   - Transformative potential: Permet à l'organisateur de choisir selon priorités événement (business strict, networking fun, etc.)
   - Challenges to overcome: Génération multiples solutions augmente temps calcul, interface choix utilisateur

2. **Apprentissage des Préférences Sociales**
   - Description: Intégrer retours participants (feedback post-rencontre) pour optimiser rencontres futures sessions
   - Transformative potential: Maximise non pas rencontres uniques mais rencontres *pertinentes* (matching intelligent)
   - Challenges to overcome: Collecte données temps réel, biais systématiques, confidentialité

3. **Architecture Distribuée Temps Réel**
   - Description: Recalcul planning en temps réel durant événement avec contraintes hardware (tablettes aux tables)
   - Transformative potential: Adaptabilité totale aux aléas (retards, affinités émergentes, durées variables)
   - Challenges to overcome: Latence réseau, synchronisation, UX fluidité transitions

4. **Génération Planning Multi-Événements Chaînés**
   - Description: Optimiser séquence d'événements (J1, J2, J3) pour maximiser diversité inter-événements (fidélisation participants)
   - Transformative potential: Créer écosystème networking long terme plutôt qu'événement ponctuel
   - Challenges to overcome: Gestion base participants évolutive, prédiction présences futures

### Insights & Learnings
*Key realizations from the session*

- **Le problème est NP-complet dans le cas général** : Accepter l'impossibilité de perfection absolue libère le design vers pragmatisme (heuristiques robustes > recherche exhaustive coûteuse)

- **L'équité individuelle prime sur l'optimisation globale pour l'expérience humaine** : Un participant ayant 10 répétitions alors que la moyenne est 2 dégrade plus l'événement qu'un score global inférieur de 5%

- **La modularité architecture (3 couches) permet robustesse et évolutivité** : Baseline indépendante → amélioration pluggable → validation découplée facilite tests, maintenance et extensions futures

- **Les edge cases (retardataires, tables partielles) ne sont pas des détails mais des features critiques** : Un algo parfait en théorie mais cassant à la première absence est inutile en production

- **La métrique unique est un piège** : Réduire qualité planning à un score masque trade-offs importants ; multi-objectif force transparence décisions

- **Les analogies (SGP, Round-Robin, Graphes) ne sont pas juste théoriques** : Chacune apporte une brique concrète (CSP pour preuve, RR pour baseline, graphe pour amélioration)

- **Performance scalable (N≤1000 en <10s) est une contrainte de design forte** : Élimine approches exponentielles, favorise heuristiques linéaires/quadratiques, force découplage génération/amélioration

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Architecture Hybride 3 Couches (Baseline → Amélioration → Équité)

- **Rationale:**
  - C'est la colonne vertébrale de toute la solution
  - Combine rapidité (baseline), qualité (amélioration), et expérience (équité)
  - Modulaire : chaque couche testable indépendamment
  - Scalable : performance contrôlée à chaque étape

- **Next steps:**
  1. Implémenter structures de données fondamentales (`Planning`, `Metrics`, `Config`)
  2. Coder baseline round-robin avec tests sur exemples A (N=30) et B (N=100)
  3. Implémenter `compute_metrics()` avec métriques multi-objectif
  4. Développer phase amélioration locale (`improve_planning()` avec swaps gloutons)
  5. Ajouter `enforce_equity()` pour garantie ±1
  6. Intégrer pipeline complet avec tests end-to-end

- **Resources needed:**
  - Python 3.10+ (dataclasses, type hints)
  - Librairies standard (collections.defaultdict, typing)
  - Framework tests (pytest)
  - Environnement calcul (Jupyter notebook pour prototypage)

- **Timeline:**
  - Sprint 1-3 (fondations + baseline + amélioration) : ~10-12h
  - Sprint 4 (équité + robustesse) : ~3-4h
  - **Total : 14-16h de développement**

---

#### #2 Priority: Gestion Robuste Edge Cases (Tables Partielles, Recalcul Partiel)

- **Rationale:**
  - Différenciateur clé entre POC académique et outil production
  - Cas N non-multiple de x apparaît fréquemment en pratique
  - Retardataires/abandons sont la norme en événementiel réel
  - Complexité modérée mais valeur utilisateur élevée

- **Next steps:**
  1. Implémenter gestion tables partielles dans baseline (répartition remainder)
  2. Développer `handle_late_arrival()` avec recalcul partiel (sessions futures)
  3. Tester équité sur cas déséquilibrés (vérifier pas de biais contre petites tables)
  4. Documenter stratégies recommandées pour organisateurs (quand recalculer vs insertion greedy)

- **Resources needed:**
  - Accès à architecture hybride (dépendance Priority #1)
  - Générateur instances edge cases (N=37, 103, etc.)
  - Tests de régression (non-régression qualité sur cas standards)

- **Timeline:**
  - Intégré dans Sprint 4 après architecture stable
  - **Estimation : 3-4h développement + tests**

---

#### #3 Priority: Export Exploitable & Interface Simple

- **Rationale:**
  - Sans sortie utilisable, l'algorithme reste théorique
  - CSV/JSON standards permettent intégration outils tiers (badges, apps événement)
  - CLI ou notebook simple facilite adoption (pas besoin UI complexe MVP)
  - Feedback utilisateur rapide pour itérations futures

- **Next steps:**
  1. Définir format export standardisé (colonnes : session_id, table_id, participant_id, participant_name optionnel)
  2. Implémenter exporters CSV et JSON
  3. Créer CLI avec arguments (N, X, x, S, output_file, config_file optionnel)
  4. Notebook Jupyter exemple avec visualisation simple (matplotlib heatmap rencontres)
  5. Documentation utilisateur (README avec exemples usage)

- **Resources needed:**
  - Librairies standard (csv, json, argparse)
  - Matplotlib pour visualisation (optionnel)
  - Exemples templates config (YAML ou JSON)

- **Timeline:**
  - Sprint 5 (après architecture + robustesse validées)
  - **Estimation : 2-3h développement + documentation**

---

## Reflection & Follow-up

### What Worked Well

- **First Principles Thinking dès le départ** : Établir bornes théoriques et conditions d'impossibilité a évité fausses pistes (chercher algo parfait quand mathématiquement impossible)

- **Analogical Thinking structuré** : Comparer à SGP/Round-Robin/Graphes a généré 3 approches orthogonales complémentaires plutôt qu'une seule voie

- **Question Storming avant convergence** : Identifier questions critiques (trade-offs, edge cases) AVANT de figer architecture a forcé considération robustesse tôt

- **Morphological Analysis pour convergence** : Décomposer en 5 dimensions avec options explicites a rendu décisions claires et justifiables (vs intuition floue)

- **Équilibre théorie/pratique** : Alterner entre modélisation mathématique et considérations implémentation (structures données, performance) a gardé solution réaliste

### Areas for Further Exploration

- **Benchmarking approches alternatives** : Implémenter version CSP exact (OR-Tools CP-SAT) pour comparer qualité/temps sur instances N≤50 et valider qualité heuristique

- **Constructions algébriques spécifiques** : Rechercher si paramètres courants (N=100, x=5) admettent structures connues (Steiner, BIBD) pour solutions élégantes

- **Optimisation équité via programmation linéaire** : Explorer si phase 3 (enforce_equity) peut se formuler comme LP pour garanties théoriques vs heuristique

- **Apprentissage heuristiques optimales** : Tester si hyperparamètres (stride rotation, ordre swaps, poids métriques) peuvent s'apprendre par recherche grille ou meta-heuristique

- **Visualisation interactive plannings** : Créer outil web simple (Flask + D3.js) pour explorer plannings générés, simuler changements, comparer métriques

### Recommended Follow-up Techniques

- **Prototypage rapide** : Implémenter baseline+métriques en 2-3h pour valider hypothèses performance et découvrir contraintes imprévues

- **Test-Driven Development** : Écrire tests cas limites AVANT implémentation amélioration locale pour forcer robustesse

- **Benchmarking systématique** : Créer suite 20-30 instances (tiny/small/medium/large, easy/hard) et tracker métriques à chaque commit

- **Code review avec focus trade-offs** : Valider que code implémente bien priorités choisies (équité > global, robustesse > perfection)

### Questions That Emerged

- **Quelle est la "vraie" complexité temporelle de l'amélioration locale dans le pire cas ?** (théoriquement O(S×X²×x²×iter) mais plateaux rapides en pratique ?)

- **Existe-t-il une borne inférieure prouvable sur le nombre de répétitions pour configurations données ?** (au-delà de la borne pigeonhole simple)

- **Comment les utilisateurs réels prioriseraient trade-offs ?** (enquête organisateurs événements : équité vs vitesse calcul vs équilibrage tables)

- **L'architecture hybride est-elle over-engineered pour petits N (<50) ?** (baseline seule suffit-elle ? amélioration apporte combien de % gain ?)

- **Peut-on paralléliser l'amélioration locale sans complexifier code ?** (swaps indépendants sur sessions différentes, race conditions ?)

### Next Session Planning

- **Suggested topics:**
  - Session implémentation : Live coding baseline + métriques avec TDD
  - Session analyse complexité : Preuve formelle bornes inférieures répétitions
  - Session UX : Design interface organisateur (config événement, visualisation plannings, ajustements temps réel)
  - Session validation terrain : Test avec organisateurs événements réels, feedback contraintes oubliées

- **Recommended timeframe:**
  - Implémentation MVP (Priority #1-3) : 2-3 jours de développement concentré
  - Première validation terrain : 1-2 semaines après MVP (feedback organisateurs)
  - Itération améliorations : cycle 1 semaine développement → 1 semaine tests utilisateurs

- **Preparation needed:**
  - Setup environnement Python (venv, pytest, jupyter)
  - Préparer exemples instances tests (A, B, edge cases)
  - Identifier 2-3 organisateurs événements pour beta-testing
  - Documenter hypothèses validables (équité ±1 suffisante ? temps <10s acceptable ?)

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*
