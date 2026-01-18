# Système d'Optimisation de Tables Rotatives - Product Requirements Document (PRD)

---

## Goals and Background Context

### Goals

- Créer un système d'optimisation de planification pour événements de networking/speed dating permettant de maximiser les rencontres uniques entre participants
- Garantir une équité stricte dans l'expérience (chaque participant rencontre un nombre similaire de personnes ±1)
- Assurer une performance scalable pour 300-1000 participants avec génération de planning en moins de 10 secondes
- Fournir une gestion robuste des cas réels (retardataires, abandons, tables de tailles variables)
- Produire des exports exploitables (CSV/JSON) pour intégration avec systèmes événementiels existants

### Background Context

Le problème de l'optimisation des rencontres lors d'événements de networking est un défi combinatoire complexe connu sous le nom de Social Golfer Problem généralisé. Les organisateurs d'événements ont besoin d'un outil capable de répartir automatiquement N participants sur X tables (capacité maximale x personnes) durant S sessions, tout en maximisant la diversité des rencontres et en minimisant les répétitions de paires.

Les solutions existantes soit ne garantissent pas l'équité entre participants, soit ne sont pas scalables, soit ne gèrent pas les contraintes pratiques des événements réels (tables non-pleines, participants en retard). Ce projet vise à créer une solution pragmatique basée sur une architecture hybride à 3 couches : génération rapide d'un planning de base (round-robin), amélioration heuristique pour réduire les répétitions, et post-traitement pour garantir l'équité individuelle.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-10 | 1.0 | Version initiale du PRD basée sur session de brainstorming | John (PM) |

---

## Requirements

### Functional Requirements

#### 🎯 Core MVP Requirements

**FR1:** Le système doit accepter en entrée les paramètres N (nombre de participants ≥2), X (nombre de tables ≥1), x (capacité maximale par table ≥2), et S (nombre de sessions ≥1).

**FR2:** Le système doit valider que X × x ≥ N (capacité totale suffisante pour tous les participants), sinon retourner une erreur explicite.

**FR3:** Le système doit générer un planning complet assignant chaque participant à exactement une table par session, pour toutes les S sessions.

**FR4:** Le système doit maximiser le nombre total de paires uniques de participants se rencontrant à travers toutes les sessions.

**FR5:** Le système doit minimiser le nombre total de répétitions de paires (deux participants assignés à la même table plus d'une fois).

**FR6:** Le système doit garantir une équité individuelle : l'écart entre le nombre de rencontres uniques du participant ayant rencontré le plus de monde et celui en ayant rencontré le moins ne doit pas excéder 1 personne.

**FR7:** Le système doit gérer les tables de tailles variables lorsque N n'est pas un multiple exact de x, en répartissant les participants de sorte que la différence de taille entre la plus grande et la plus petite table ne dépasse jamais 1 personne par session.

**FR8:** Le système doit calculer et retourner les métriques de qualité suivantes pour chaque planning généré :
- Nombre total de paires uniques créées
- Nombre total de répétitions de paires
- Pour chaque participant : nombre de personnes uniques rencontrées

**FR9:** Le système doit calculer et retourner les statistiques d'équité suivantes :
- Minimum, maximum, moyenne et écart-type des rencontres uniques par participant
- Distribution des tailles de tables par session

**FR10:** Le système doit exporter le planning au format CSV avec les colonnes exactes : `session_id` (entier), `table_id` (entier), `participant_id` (entier).

**FR11:** Le système doit exporter le planning au format JSON avec la structure : `{"sessions": [{"session_id": int, "tables": [{"table_id": int, "participants": [int]}]}]}`

#### 🔮 Enhanced Features (Post-MVP or Optional)

**FR12:** Le système doit détecter les configurations mathématiquement impossibles pour zéro répétition (quand S × (x-1) < N-1) et en informer l'utilisateur.

**FR13:** Pour les configurations impossibles, le système doit générer le planning minimisant les répétitions tout en garantissant une répartition équitable des répétitions (aucun participant ne doit subir significativement plus de répétitions que les autres).

**FR14:** Le système doit permettre l'ajout dynamique d'un participant retardataire à partir d'une session donnée, avec recalcul des sessions futures uniquement.

**FR15:** Le système doit permettre la gestion d'un abandon de participant à partir d'une session donnée, avec recalcul des sessions futures uniquement.

**FR16:** Le système doit permettre la configuration des priorités d'optimisation (poids relatifs : rencontres uniques, équité, équilibrage des tables) via un fichier de configuration optionnel.

### Non-Functional Requirements

**NFR1:** Le système doit générer un planning pour N≤100 participants en moins de 2 secondes (cible de performance confortable).

**NFR2:** Le système doit générer un planning pour N≤300 participants en moins de 5 secondes (cible de performance standard).

**NFR3:** Le système doit générer un planning pour N≤1000 participants en moins de 30 secondes (cible de performance maximale acceptable).

**NFR4:** Le système doit utiliser une empreinte mémoire ne dépassant pas O(N²) dans le pire cas pour le stockage de l'historique des rencontres.

**NFR5:** Le système doit être implémenté en Python 3.10 ou supérieur avec type hints complets pour toutes les fonctions publiques.

**NFR6:** Le code doit atteindre une couverture de tests unitaires et d'intégration d'au moins 85% avec pytest.

**NFR7:** Le système doit fournir une interface en ligne de commande (CLI) acceptant les paramètres : `--participants N`, `--tables X`, `--capacity x`, `--sessions S`, `--output fichier`, `--format {csv|json}`, `--config fichier` (optionnel).

**NFR8:** Le système doit logger les étapes principales de génération (baseline, amélioration, équité) avec niveaux INFO, WARNING, ERROR appropriés.

**NFR9:** Le système doit avoir une architecture modulaire permettant de tester indépendamment : la génération de baseline, l'amélioration locale, et l'enforcement d'équité.

**NFR10:** Le système doit valider toutes les entrées et retourner des messages d'erreur explicites en français pour :
- Paramètres hors limites (N≤0, X≤0, x≤1, S≤0)
- Capacité insuffisante (X × x < N)
- Formats de fichiers invalides

**NFR11:** Le système doit générer des plannings reproductibles : à entrées identiques et seed aléatoire fixe, le système doit produire le même planning.

**NFR12:** La documentation utilisateur doit inclure des exemples concrets pour au moins 3 configurations typiques : petit événement (N=30), moyen événement (N=100), grand événement (N=300).

---

## User Interface Design Goals

### Overall UX Vision

L'expérience utilisateur privilégie la simplicité et l'efficacité pour les organisateurs d'événements techniques. L'interface principale est une CLI permettant une intégration facile dans des workflows automatisés ou des scripts. Des visualisations optionnelles (notebook Jupyter, exports graphiques) permettent de valider la qualité des plannings générés et de communiquer les résultats aux parties prenantes.

### Key Interaction Paradigms

- **CLI-first** : Toutes les fonctionnalités accessibles via ligne de commande avec arguments explicites
- **Configuration as Code** : Paramètres complexes via fichiers YAML/JSON pour reproductibilité
- **Progressive disclosure** : Affichage minimal par défaut (métriques clés), mode verbose optionnel pour debugging
- **Export-oriented** : Outputs standardisés (CSV/JSON) pour intégration avec outils tiers (apps événement, badges, etc.)

### Core Screens and Views

1. **CLI Interface** : Interface principale pour génération de planning
2. **Console Output** : Affichage des métriques de qualité et statistiques d'équité en temps réel
3. **Notebook Jupyter (Optionnel)** : Environnement interactif pour exploration et visualisation
4. **Visualisation Heatmap (Optionnel)** : Matrice de rencontres pour validation visuelle de la qualité

### Accessibility

Aucune exigence d'accessibilité formelle pour le MVP (outil CLI). La sortie console doit être lisible dans des terminaux standards avec support UTF-8 pour caractères français.

### Branding

Aucun branding spécifique requis pour le MVP. L'outil est utilitaire et technique.

### Target Device and Platforms

**Plateformes principales :**
- Terminal/Console (Linux, macOS, Windows avec WSL)
- Jupyter Notebook (environnement Python standard)

**Pas de support prévu pour :**
- Applications mobiles
- Interfaces web (sauf exploration future)

---

## Technical Assumptions

### Repository Structure: **Monorepo**

**Décision :** Monorepo unique contenant code source, tests, documentation et exemples.

**Rationale :** Projet autonome sans dépendances inter-services. Simplicité de gestion et facilité de contribution.

---

### Service Architecture

**Architecture :** Application Python standalone monolithique (outil CLI).

**Contraintes architecturales obligatoires :**

1. **Architecture modulaire en pipeline** : Le système doit suivre une architecture en pipeline avec au minimum 3 phases distinctes et testables indépendamment :
   - Phase de génération d'un planning initial valide
   - Phase d'optimisation/amélioration de la qualité
   - Phase de validation/enforcement des contraintes d'équité

2. **Séparation des préoccupations** : Chaque phase doit être dans un module séparé avec interfaces claires (pas de dépendances circulaires).

3. **Inversion de dépendances** : Les modules de bas niveau (génération) ne doivent pas dépendre des modules de haut niveau (CLI, export).

**Liberté de l'Architect :** La structure exacte des modules, les noms de fichiers, et les patterns d'implémentation (Strategy, Factory, etc.) sont à la discrétion de l'Architect.

**Pas d'architecture distribuée, pas de services externes, pas de base de données** - tout en mémoire.

---

### Testing Requirements

**Stratégie :** Full Testing Pyramid (unitaires + intégration + performance)

**Contraintes quantitatives :**
- Couverture de tests ≥85% (NFR6)
- Temps d'exécution suite de tests <30s (pour CI rapide)
- Tests de performance obligatoires pour valider NFR1-NFR3

**Framework :** pytest (standard Python, riche écosystème de plugins)

**Fixtures obligatoires :** Configurations de référence pour N=30, N=100, N=300 avec résultats attendus pour tests de régression.

**Tests de propriétés (optionnel mais recommandé) :** Utilisation de hypothesis pour générer des cas de test aléatoires et vérifier les invariants (équité ±1, validité du planning, etc.).

---

### Core Technical Stack

**Langage :** Python 3.10 minimum

**Rationale :**
- 3.10+ pour match/case, meilleurs messages d'erreur, union types améliorés
- Largement adopté (pas trop récent), bon support dans CI/CD
- Pas 3.11+ car peut limiter adoption (certains environnements encore sur 3.10)

**Compatibilité OS :**
- Linux (prioritaire)
- macOS (support natif)
- Windows via WSL2 minimum (natif si faisable sans effort)

**Dépendances externes MVP :** AUCUNE en dehors de la stdlib Python

**Rationale :**
- Maximise portabilité et facilité d'installation
- Réduit surface d'attaque (vulnérabilités)
- Simplifie maintenance

**Dépendances dev/test :**
- `pytest` : Tests
- `pytest-cov` : Couverture
- `black` : Formatage automatique
- `ruff` : Linting rapide (remplace flake8, isort, etc.)
- `mypy` : Type checking statique

**Dépendances optionnelles post-MVP :**
- `ortools` : Mode exact CSP/SAT (FR12-FR13 améliorés) - **Epic futur distinct**
- `matplotlib` : Visualisations (notebook Jupyter) - **Epic futur distinct**
- `pyyaml` : Parsing config avancée (FR16) - **Seulement si FR16 implémenté**

---

### Development Environment & Tooling

**Gestionnaire de dépendances :** Poetry (recommandé) ou pip + requirements.txt

**Rationale Poetry :**
- Gestion moderne (lock files, résolution dépendances)
- Build et publish PyPI simplifiés
- Standard de facto pour projets Python modernes

**Alternative acceptable :** pip + requirements.txt si contraintes d'environnement (simplicité extrême privilégiée)

**Code Quality Enforcement :**
- `black` (formatage) : ligne 88 caractères, style standard
- `ruff` (linting) : configuration stricte, pas de warnings tolérés
- `mypy` (type checking) : mode strict, tous les types vérifiés
- Pre-commit hooks obligatoires en dev

**Git Workflow :**
- Branches feature, PRs obligatoires
- Commits conventionnels (feat, fix, docs, test, refactor)
- Pas de commits directs sur `main`

---

### CI/CD & Automation

**Plateforme CI/CD :** GitHub Actions (si hébergé sur GitHub) ou équivalent

**Pipeline obligatoire :**
1. **Tests** : Exécution suite complète sur Python 3.10, 3.11, 3.12
2. **Linting** : black --check, ruff, mypy
3. **Coverage** : Vérification seuil 85%, génération rapport
4. **Performance** : Benchmarks sur instances de référence, détection régression

**Déclencheurs :**
- Sur chaque PR (tous les checks)
- Sur merge main (tous les checks + optionnel: publish test PyPI)

**Artifacts :**
- Rapport de couverture (HTML)
- Résultats benchmarks (JSON)

---

### Packaging & Distribution

**Format :** Package Python standard (wheel + source distribution)

**Distribution MVP :**
- Installation via `pip install -e .` (mode développement)
- Pas de publication PyPI pour MVP (distribution interne ou Git clone)

**Distribution future :**
- Publication PyPI quand stable (v1.0+)
- Versioning sémantique strict (MAJOR.MINOR.PATCH)

**Point d'entrée CLI :**
- Script entry point défini dans `pyproject.toml` ou `setup.py`
- Commande globale : `speed-dating-planner` ou `sdp` (à définir)

---

### Configuration & Extensibility

**Configuration utilisateur :**
- Arguments CLI prioritaires (NFR7)
- Fichier de config optionnel (format YAML ou JSON, à décider par Architect)
- Variables d'environnement pour debugging (ex: `SDP_LOG_LEVEL=DEBUG`)

**Principes de configuration :**
- Convention over configuration (defaults sensibles)
- Validation stricte des configs (erreurs explicites si invalide)
- Pas de config globale système (tout local au projet/exécution)

**Extensibilité future :**
- Architecture doit permettre ajout de nouveaux algorithmes de génération (plugins potentiels)
- Interface abstraite pour exporters (faciliter ajout Excel, PDF, etc.)

---

### Logging & Observability

**Framework :** Module `logging` standard Python

**Contraintes :**
- Messages en français (NFR10)
- Niveaux : DEBUG, INFO, WARNING, ERROR
- Sortie : console par défaut, fichier optionnel via config
- Format : Lisible humain (pas JSON pour MVP)

**Pas de télémétrie, pas de metrics externes** - outil standalone offline.

---

### Security & Code Quality

**Scan de vulnérabilités :**
- Dependabot ou équivalent activé (si GitHub)
- `safety check` dans CI pour dépendances

**Code quality gates :**
- Complexity cyclomatique <10 par fonction (ruff config)
- Pas de code dupliqué >10 lignes (détection manuelle en code review)

**Pas de secrets** dans le code (pas applicable pour cet outil, mais principe respecté).

---

### Additional Assumptions

**Reproductibilité :**
- Seed aléatoire configurable pour reproductibilité (NFR11)
- Résultats déterministes à seed et entrées identiques

**Performance baseline :**
- Benchmarks exécutés sur machine standard (4 cores, 8GB RAM)
- Pas d'optimisations GPU/CUDA nécessaires

**Internationalisation :**
- MVP en français uniquement (messages, docs)
- Architecture doit permettre i18n future (mais pas implémenté MVP)

**Données de test :**
- Générateurs de données synthétiques pour tests
- Pas de données réelles d'événements (RGPD, vie privée)

---

## Epic List

### Epic 1: Foundation & Core Algorithm (MVP)
Établir l'infrastructure du projet et implémenter l'algorithme de génération de planning de base avec métriques de qualité.

### Epic 2: Optimization & Equity Enforcement (MVP)
Ajouter les phases d'amélioration locale et d'enforcement d'équité pour garantir la qualité des plannings selon les contraintes FR4-FR6.

### Epic 3: CLI & Export Capabilities (MVP)
Créer l'interface ligne de commande complète et les fonctionnalités d'export CSV/JSON pour rendre l'outil utilisable en production.

### Epic 4: Edge Cases & Dynamic Management (Post-MVP)
Gérer les cas limites (tables partielles, configurations impossibles) et permettre la gestion dynamique des participants (retardataires, abandons).

### Epic 5: Visualization & Analysis Tools (Future)
Ajouter des outils de visualisation (notebook Jupyter, heatmaps) et d'analyse avancée pour faciliter l'exploration et la validation des plannings.

---

## Epic 1: Foundation & Core Algorithm

**Epic Goal:**

Établir les fondations du projet (configuration, structure, tests) et implémenter l'algorithme de génération de planning de base (phase 1 du pipeline). À la fin de cet epic, le système doit être capable de générer un planning valide pour N participants sur X tables durant S sessions, avec calcul des métriques de qualité, même si l'optimisation n'est pas encore appliquée. Cet epic pose les bases pour tous les développements futurs en créant une architecture propre, testable et documentée.

### Story 1.1: Setup Initial du Projet

As a développeur,
I want un projet Python correctement structuré avec toutes les configurations de base,
so that je peux commencer à développer le système dans un environnement propre et reproductible.

**Acceptance Criteria:**

1. Le repository Git est initialisé avec structure de dossiers standard (`src/`, `tests/`, `docs/`, `examples/`)
2. Le fichier `pyproject.toml` (Poetry) ou `setup.py` est configuré avec métadonnées du projet (nom, version 0.1.0, auteur, description, Python >=3.10)
3. Le fichier `.gitignore` exclut les fichiers Python standards (`__pycache__`, `.pytest_cache`, `*.pyc`, `.venv`, etc.)
4. Les dépendances dev sont installées et fonctionnelles : `pytest`, `pytest-cov`, `black`, `ruff`, `mypy`
5. Un fichier `README.md` de base existe avec titre du projet et description d'une phrase
6. La commande `pytest` s'exécute sans erreur (même sans tests encore)
7. La commande `black .` et `ruff check .` s'exécutent sans erreur sur le code existant
8. Un fichier `.pre-commit-config.yaml` est configuré avec hooks pour black, ruff, mypy

### Story 1.2: Définir les Structures de Données Fondamentales

As a développeur,
I want des dataclasses Python typées représentant les entités du domaine,
so that je peux manipuler les plannings, sessions, et configurations de manière type-safe et testable.

**Acceptance Criteria:**

1. Un module `src/models.py` contient une dataclass `Planning` représentant une liste de sessions
2. Une dataclass `Session` représente une liste de tables pour une session donnée
3. Une dataclass `Table` (ou type alias `Set[int]`) représente un ensemble de participant IDs
4. Une dataclass `PlanningConfig` contient les paramètres d'entrée : N, X, x, S avec validation dans `__post_init__`
5. Une dataclass `PlanningMetrics` contient toutes les métriques de qualité définies dans FR8-FR9
6. Tous les types sont documentés avec docstrings Google style
7. Les tests unitaires dans `tests/test_models.py` valident :
   - La création valide d'un `PlanningConfig` avec paramètres corrects
   - Le rejet avec exception pour paramètres invalides (N≤0, X×x<N, etc.) selon FR2
   - L'immutabilité ou mutabilité contrôlée des structures
8. `mypy src/models.py` passe sans erreur avec mode strict

### Story 1.3: Implémenter la Validation des Paramètres d'Entrée

As a organisateur d'événement,
I want que le système valide mes paramètres d'entrée et me donne des messages d'erreur clairs en français,
so that je sais immédiatement si ma configuration est viable avant de lancer la génération.

**Acceptance Criteria:**

1. Un module `src/validation.py` contient une fonction `validate_config(config: PlanningConfig) -> None` qui lance des exceptions typées
2. La validation vérifie toutes les contraintes FR1-FR2 :
   - N ≥ 2, X ≥ 1, x ≥ 2, S ≥ 1
   - X × x ≥ N (capacité suffisante)
3. Les exceptions personnalisées (`InvalidConfigurationError`) ont des messages en français explicites conformes à NFR10
4. Exemples de messages : "Nombre de participants invalide : N=0. Minimum requis : 2", "Capacité insuffisante : 5 tables × 4 places = 20 < 25 participants"
5. Les tests dans `tests/test_validation.py` couvrent tous les cas d'erreur avec vérification des messages français
6. Les tests vérifient qu'une configuration valide ne lève pas d'exception
7. La couverture de tests du module `validation.py` est ≥95%

### Story 1.4: Implémenter l'Algorithme de Génération Baseline (Round-Robin)

As a développeur,
I want un algorithme de génération rapide produisant un planning valide initial,
so that le système peut toujours fournir un résultat même sans optimisation avancée.

**Acceptance Criteria:**

1. Un module `src/baseline.py` contient une fonction `generate_baseline(config: PlanningConfig, seed: int = 42) -> Planning`
2. L'algorithme implémente une stratégie de rotation systématique (round-robin généralisé avec stride)
3. Pour chaque session, tous les N participants sont assignés à exactement une table
4. La fonction garantit que chaque table respecte la contrainte de capacité x
5. La gestion des tables partielles est correcte : si N n'est pas multiple de x, les participants sont répartis avec écart de taille ≤1 entre tables (FR7)
6. L'algorithme est déterministe : à seed identique, génère le même planning (NFR11)
7. Les tests dans `tests/test_baseline.py` vérifient :
   - Planning valide pour config simple (N=30, X=5, x=6, S=6)
   - Planning valide pour tables partielles (N=37, X=6, x=7)
   - Déterminisme (2 appels avec même seed = même résultat)
   - Performance : génération pour N=100 en <1s
8. Aucun participant n'est oublié ou dupliqué dans une session

### Story 1.5: Implémenter le Calcul de l'Historique des Rencontres

As a développeur,
I want une fonction calculant quels participants se sont déjà rencontrés,
so that je peux mesurer les répétitions et préparer les phases d'optimisation futures.

**Acceptance Criteria:**

1. Un module `src/metrics.py` contient une fonction `compute_meeting_history(planning: Planning) -> Set[Tuple[int, int]]`
2. La fonction retourne l'ensemble de toutes les paires de participants qui se sont rencontrés au moins une fois
3. Les paires sont normalisées : `(min(i,j), max(i,j))` pour éviter duplications `(i,j)` et `(j,i)`
4. La complexité est O(S × X × x²) dans le pire cas
5. Les tests dans `tests/test_metrics.py` vérifient :
   - Planning sans répétitions : `len(met_pairs)` = nombre de paires attendu
   - Planning avec répétitions connues : paires détectées correctement
   - Normalisation des paires : `(0,1)` présent, pas `(1,0)`
6. La fonction gère correctement les tables de tailles variables

### Story 1.6: Implémenter le Calcul des Métriques de Qualité

As a organisateur d'événement,
I want des métriques précises sur la qualité de mon planning,
so that je peux évaluer si le planning généré répond à mes besoins d'équité et de diversité.

**Acceptance Criteria:**

1. Une fonction `compute_metrics(planning: Planning, config: PlanningConfig) -> PlanningMetrics` dans `src/metrics.py` calcule toutes les métriques FR8-FR9
2. Les métriques calculées incluent :
   - `total_unique_pairs`: nombre total de paires uniques rencontrées
   - `total_repeat_pairs`: nombre de paires rencontrées plus d'une fois
   - `unique_meetings_per_person`: liste de taille N avec rencontres uniques par participant
   - `min_unique`, `max_unique`, `mean_unique`, `std_unique`: statistiques d'équité
   - `table_sizes_per_session`: distribution des tailles de tables par session
3. La fonction calcule correctement l'écart max-min pour vérifier FR6 (équité ±1)
4. Les tests vérifient le calcul sur des plannings construits manuellement avec résultats attendus connus
5. Les tests vérifient que pour un planning "parfait" (zéro répétition), `total_repeat_pairs == 0`
6. La performance est acceptable : calcul en <100ms pour N=300, S=20
7. La couverture de tests du module `metrics.py` est ≥90%

### Story 1.7: Tests d'Intégration Pipeline Baseline Complet

As a développeur,
I want des tests d'intégration validant le pipeline complet de génération baseline + métriques,
so that je garantis que toutes les pièces fonctionnent ensemble correctement.

**Acceptance Criteria:**

1. Un fichier `tests/test_integration_baseline.py` contient des tests end-to-end
2. Test "Exemple A" (N=30, X=5, x=6, S=6) :
   - Validation config passe
   - Génération baseline produit planning valide
   - Métriques calculées sans erreur
   - Vérification : tous les participants présents chaque session, tables équilibrées
3. Test "Exemple B" (N=100, X=20, x=5, S=10) :
   - Pipeline complet réussit
   - Performance : <2s total (NFR1)
4. Test "Tables partielles" (N=37, X=6, x=7) :
   - Planning généré avec gestion correcte du remainder
   - Écart de taille ≤1 vérifié dans métriques
5. Test "Configuration invalide" :
   - X × x < N → exception levée avec message français
6. Tous les tests d'intégration passent et la suite s'exécute en <5s

### Story 1.8: Documentation et Exemples de Base

As a développeur futur,
I want une documentation claire du code et des exemples d'utilisation,
so that je comprends rapidement comment fonctionne le système et comment l'étendre.

**Acceptance Criteria:**

1. Toutes les fonctions publiques ont des docstrings Google style avec :
   - Description brève
   - Args avec types
   - Returns avec type
   - Raises (exceptions possibles)
   - Exemple d'utilisation si pertinent
2. Le `README.md` est mis à jour avec :
   - Description du projet (2-3 paragraphes)
   - Installation (`pip install -e .`)
   - Exemple d'utilisation Python basique (5-10 lignes de code)
   - Structure du projet (arborescence)
3. Un fichier `examples/basic_usage.py` démontre :
   - Création d'un `PlanningConfig`
   - Génération baseline
   - Calcul et affichage des métriques
4. Le code de l'exemple s'exécute sans erreur
5. Un fichier `docs/architecture.md` décrit l'architecture 3 phases (même si seule phase 1 implémentée)

---

## Epic 2: Optimization & Equity Enforcement

**Epic Goal:**

Implémenter les phases 2 et 3 du pipeline hybride pour transformer les plannings baseline en plannings de haute qualité respectant les contraintes d'optimisation (FR4-FR5) et d'équité stricte (FR6). À la fin de cet epic, le système doit produire des plannings minimisant les répétitions tout en garantissant que chaque participant rencontre un nombre similaire de personnes uniques (écart ≤1). Cet epic apporte la valeur différenciatrice du système par rapport aux approches naïves.

### Story 2.1: Implémenter l'Évaluation de Qualité d'un Swap

As a développeur,
I want une fonction évaluant si échanger deux participants entre tables améliore la qualité du planning,
so that je peux construire l'heuristique d'amélioration locale sur cette primitive.

**Acceptance Criteria:**

1. Un module `src/optimizer.py` contient une fonction `evaluate_swap(planning, session_id, table1_id, p1, table2_id, p2, met_pairs) -> int`
2. La fonction calcule le delta de répétitions avant/après swap (négatif = amélioration)
3. Le calcul compare combien de paires répétées existent avec p1 dans table1 et p2 dans table2 vs après swap
4. La fonction ne modifie PAS le planning (évaluation pure)
5. Les tests dans `tests/test_optimizer.py` vérifient :
   - Swap bénéfique détecté correctement (delta < 0)
   - Swap neutre détecté (delta == 0)
   - Swap néfaste détecté (delta > 0)
   - Performance : évaluation en <1ms pour tables de taille 10
6. La fonction gère correctement les cas où p1 ou p2 n'ont aucune rencontre préalable

### Story 2.2: Implémenter l'Amélioration Locale par Swaps Gloutons

As a organisateur d'événement,
I want que le système améliore automatiquement la qualité du planning baseline,
so that je reçois un planning avec le minimum de répétitions possible.

**Acceptance Criteria:**

1. Une fonction `improve_planning(planning: Planning, config: PlanningConfig, max_iterations: int = 100) -> Planning` dans `src/optimizer.py`
2. L'algorithme itère sur toutes les sessions et teste des swaps entre tables
3. À chaque itération, si un swap améliore le score (réduit répétitions), il est appliqué
4. L'algorithme s'arrête quand aucune amélioration n'est trouvée (plateau local) ou max_iterations atteint
5. Un système de logging (niveau INFO) indique : "Itération X: Y swaps appliqués, Z répétitions éliminées"
6. Les tests vérifient :
   - Planning avec répétitions connues → amélioration mesurable après `improve_planning`
   - Détection du plateau local (stop avant max_iterations si plus d'améliorations)
   - Déterminisme (seed fixe → même résultat)
   - Performance : amélioration pour N=100, S=10 en <3s
7. Le planning retourné est toujours valide (tous participants assignés, contraintes respectées)

### Story 2.3: Implémenter l'Enforcement de l'Équité Stricte

As a organisateur d'événement,
I want que tous les participants aient une expérience équitable avec un écart de rencontres uniques ≤1,
so that personne ne se sente désavantagé lors de l'événement.

**Acceptance Criteria:**

1. Une fonction `enforce_equity(planning: Planning, config: PlanningConfig) -> Planning` dans `src/optimizer.py`
2. La fonction calcule les rencontres uniques par participant via `compute_metrics`
3. Si `max_unique - min_unique <= 1`, le planning est retourné inchangé
4. Sinon, la fonction identifie participants sur-exposés (> moyenne) et sous-exposés (< moyenne)
5. Des swaps ciblés sont effectués pour réduire l'écart tout en minimisant l'impact sur les répétitions
6. La fonction garantit que le planning final respecte FR6 (équité ±1)
7. Les tests vérifient :
   - Planning déjà équitable → inchangé
   - Planning déséquilibré (écart 3) → ramené à écart ≤1
   - Métriques finales confirment `max_unique - min_unique <= 1`
   - Performance : enforcement pour N=300 en <2s
8. Un message de logging INFO indique : "Équité atteinte : écart de X rencontres entre min et max"

### Story 2.4: Implémenter le Pipeline Complet d'Optimisation

As a développeur,
I want une fonction orchestrant les 3 phases du pipeline hybride,
so that je peux générer des plannings optimisés en un seul appel de fonction.

**Acceptance Criteria:**

1. Un module `src/planner.py` contient une fonction `generate_optimized_planning(config: PlanningConfig, seed: int = 42) -> Tuple[Planning, PlanningMetrics]`
2. La fonction exécute séquentiellement :
   - Phase 1 : `generate_baseline(config, seed)`
   - Phase 2 : `improve_planning(baseline, config)`
   - Phase 3 : `enforce_equity(improved, config)`
   - Calcul final : `compute_metrics(final_planning, config)`
3. Chaque phase logue son exécution (niveau INFO) : "Phase 1: Baseline générée", "Phase 2: X répétitions éliminées", "Phase 3: Équité garantie"
4. La fonction retourne le planning final ET ses métriques
5. Les tests vérifient :
   - Pipeline complet pour config standard (N=30) réussit
   - Métriques finales confirment FR6 (équité ±1)
   - Planning final est valide (aucun participant oublié)
6. La fonction gère les configurations impossibles (S × (x-1) < N-1) en loguant un WARNING mais produit quand même le meilleur planning possible

### Story 2.5: Tests de Performance et Benchmarks

As a développeur,
I want des benchmarks systématiques validant les contraintes de performance NFR1-NFR3,
so that je garantis que le système reste utilisable en production pour toutes les tailles d'événements.

**Acceptance Criteria:**

1. Un fichier `tests/test_performance.py` contient des benchmarks pour les 3 niveaux de performance
2. Benchmark NFR1 (N=100, X=20, x=5, S=10) :
   - Pipeline complet s'exécute en <2s
   - Résultat enregistré dans fichier JSON (`benchmarks/results.json`)
3. Benchmark NFR2 (N=300, X=60, x=5, S=15) :
   - Pipeline complet s'exécute en <5s
4. Benchmark NFR3 (N=1000, X=200, x=5, S=25) :
   - Pipeline complet s'exécute en <30s
5. Les benchmarks mesurent aussi l'empreinte mémoire (vérification NFR4 : <O(N²))
6. Un script `scripts/run_benchmarks.py` exécute tous les benchmarks et génère un rapport formaté
7. Les tests de performance sont marqués `@pytest.mark.slow` et exclus des tests rapides par défaut
8. Le CI exécute les benchmarks sur chaque merge à `main` et détecte les régressions (>10% ralentissement)

### Story 2.6: Tests d'Intégration Pipeline Complet Optimisé

As a développeur,
I want des tests d'intégration validant que le pipeline complet (3 phases) produit des plannings de haute qualité,
so that je garantis la valeur livrée aux utilisateurs finaux.

**Acceptance Criteria:**

1. Un fichier `tests/test_integration_optimized.py` contient des tests end-to-end du pipeline complet
2. Test "Exemple A optimisé" (N=30, X=5, x=6, S=6) :
   - Pipeline 3 phases exécuté
   - Métriques finales : équité ±1 vérifiée, répétitions minimales (<5% du total)
   - Comparaison avant/après : amélioration locale réduit répétitions d'au moins 50% vs baseline
3. Test "Configuration impossible" (N=32, S=3, X=4, x=8) :
   - Détection mathématique : S × (x-1) = 21 < N-1 = 31
   - WARNING loggé indiquant impossibilité
   - Planning généré quand même avec répétitions équitablement réparties
   - Équité ±1 toujours respectée
4. Test "Grande instance" (N=300) :
   - Pipeline complet réussit
   - Performance <5s (NFR2)
   - Équité ±1 garantie
5. Tous les tests d'intégration passent avec couverture ≥85%

### Story 2.7: Documentation de l'Optimisation

As a utilisateur technique,
I want une documentation expliquant comment fonctionne l'optimisation et comment interpréter les métriques,
so that je comprends la valeur ajoutée du système et comment configurer les paramètres avancés.

**Acceptance Criteria:**

1. Le fichier `docs/architecture.md` est complété avec :
   - Description détaillée des 3 phases du pipeline
   - Explication de l'heuristique de swaps gloutons
   - Critères d'arrêt (plateau local, max_iterations)
   - Trade-offs équité vs répétitions minimales
2. Le `README.md` inclut une section "Comment ça marche ?" avec :
   - Schéma textuel du pipeline 3 phases
   - Exemple de métriques avant/après optimisation
3. Un fichier `examples/advanced_usage.py` démontre :
   - Utilisation de `generate_optimized_planning`
   - Affichage des métriques détaillées
   - Comparaison baseline vs optimisé
4. Le code de l'exemple s'exécute sans erreur et produit une sortie lisible
5. Les docstrings des fonctions d'optimisation expliquent la complexité algorithmique et les garanties

---

## Epic 3: CLI & Export Capabilities

**Epic Goal:**

Créer l'interface utilisateur complète (CLI) et les fonctionnalités d'export permettant aux organisateurs d'événements d'utiliser le système en production. À la fin de cet epic, l'outil est livrable : un utilisateur peut installer le package, exécuter une commande avec ses paramètres, obtenir un planning optimisé, et l'exporter aux formats CSV/JSON pour intégration avec ses systèmes événementiels. Cet epic finalise le MVP en transformant une bibliothèque algorithmique en produit utilisable.

### Story 3.1: Implémenter l'Exporteur CSV

As a organisateur d'événement,
I want exporter mon planning au format CSV,
so that je peux l'importer dans Excel, Google Sheets ou mon système de gestion d'événements.

**Acceptance Criteria:**

1. Un module `src/exporters.py` contient une fonction `export_to_csv(planning: Planning, config: PlanningConfig, filepath: str) -> None`
2. Le fichier CSV généré contient exactement les colonnes : `session_id`, `table_id`, `participant_id` (FR10)
3. Les IDs sont des entiers (0-indexed pour participants, 0-indexed pour sessions, 0-indexed pour tables)
4. Le fichier est encodé en UTF-8 avec BOM pour compatibilité Excel
5. Les tests dans `tests/test_exporters.py` vérifient :
   - Export réussit sans erreur pour planning valide
   - Fichier CSV produit contient bon nombre de lignes (N × S)
   - Lecture du CSV avec `csv.DictReader` fonctionne
   - Valeurs correctes pour un planning connu
6. La fonction gère correctement les chemins avec espaces et caractères spéciaux
7. Si le fichier existe déjà, il est écrasé (avec warning loggé)

### Story 3.2: Implémenter l'Exporteur JSON

As a organisateur d'événement,
I want exporter mon planning au format JSON structuré,
so that je peux l'utiliser dans des applications web ou API sans parsing complexe.

**Acceptance Criteria:**

1. Une fonction `export_to_json(planning: Planning, config: PlanningConfig, filepath: str) -> None` dans `src/exporters.py`
2. Le fichier JSON suit la structure exacte spécifiée dans FR11 : `{"sessions": [{"session_id": int, "tables": [{"table_id": int, "participants": [int]}]}]}`
3. Le JSON est indenté (2 espaces) pour lisibilité humaine
4. Le fichier est encodé en UTF-8
5. Les tests vérifient :
   - Export réussit sans erreur
   - JSON produit est valide (parsing avec `json.load` réussit)
   - Structure conforme à FR11
   - Valeurs correctes pour un planning connu
6. Un champ optionnel `metadata` peut être ajouté avec : `{"config": {"N": ..., "X": ..., "x": ..., "S": ...}, "metrics": {...}}`
7. Si filepath non fourni, la fonction retourne le JSON sous forme de string

### Story 3.3: Implémenter le Parseur d'Arguments CLI

As a utilisateur,
I want une interface en ligne de commande intuitive avec des arguments clairs,
so that je peux facilement générer des plannings sans écrire de code Python.

**Acceptance Criteria:**

1. Un module `src/cli.py` contient une fonction `parse_args()` utilisant `argparse`
2. Les arguments obligatoires (NFR7) sont supportés :
   - `--participants N` ou `-n N`
   - `--tables X` ou `-t X`
   - `--capacity x` ou `-c x`
   - `--sessions S` ou `-s S`
3. Les arguments optionnels sont supportés :
   - `--output fichier` ou `-o fichier` (défaut : `planning.csv`)
   - `--format {csv|json}` ou `-f {csv|json}` (défaut : `csv`)
   - `--seed SEED` (défaut : `42`)
   - `--verbose` ou `-v` (active logging DEBUG)
   - `--config fichier` (fichier YAML/JSON de configuration, non implémenté dans MVP mais préparé)
4. L'aide (`--help`) affiche une description claire en français de chaque argument
5. Les tests dans `tests/test_cli.py` vérifient :
   - Parsing réussit avec arguments minimaux
   - Parsing réussit avec tous les arguments
   - Parsing échoue avec message clair si argument obligatoire manquant
   - Valeurs par défaut correctes
6. Les descriptions d'aide sont en français (NFR10)

### Story 3.4: Implémenter la Fonction Main de la CLI

As a utilisateur,
I want exécuter une seule commande pour générer et exporter un planning complet,
so that je peux utiliser l'outil sans connaissance Python approfondie.

**Acceptance Criteria:**

1. Une fonction `main()` dans `src/cli.py` orchestre le flux CLI complet
2. Le flux exécuté est :
   - Parsing des arguments
   - Configuration du logging (INFO par défaut, DEBUG si `--verbose`)
   - Création de `PlanningConfig` depuis les arguments
   - Appel de `generate_optimized_planning(config, seed)`
   - Affichage console des métriques clés (paires uniques, répétitions, équité)
   - Export vers fichier selon `--format` et `--output`
   - Message de succès : "Planning généré avec succès : X paires uniques, Y répétitions, équité ±Z. Exporté vers {fichier}"
3. Gestion d'erreurs robuste avec messages en français (NFR10) :
   - Configuration invalide → affichage du message d'erreur de validation et exit code 1
   - Erreur I/O (export impossible) → message clair et exit code 2
   - Erreur inattendue → stack trace si `--verbose`, sinon message générique et exit code 3
4. Les tests vérifient :
   - Exécution réussie end-to-end avec arguments valides
   - Exit code 0 sur succès
   - Exit code != 0 sur erreur
   - Fichier de sortie créé et valide
5. La fonction retourne l'exit code (pour testabilité)

### Story 3.5: Créer le Point d'Entrée Exécutable

As a utilisateur,
I want installer le package et exécuter une commande globale dans mon terminal,
so that je n'ai pas besoin d'appeler Python directement avec des chemins de modules.

**Acceptance Criteria:**

1. Le `pyproject.toml` (ou `setup.py`) définit un entry point console : `speed-dating-planner = src.cli:main`
2. Après installation (`pip install -e .`), la commande `speed-dating-planner` est disponible globalement
3. L'exécution de `speed-dating-planner --help` affiche l'aide complète
4. L'exécution de `speed-dating-planner -n 30 -t 5 -c 6 -s 6 -o test.csv` génère un planning et l'exporte
5. Les tests dans `tests/test_cli_integration.py` vérifient :
   - Commande exécutable trouvée après installation
   - Exécution via subprocess réussit
   - Fichier de sortie créé avec contenu valide
6. Un alias court `sdp` peut être ajouté (optionnel)

### Story 3.6: Affichage Console des Métriques

As a utilisateur,
I want voir les résultats de génération directement dans le terminal,
so that je peux évaluer la qualité du planning avant de consulter le fichier exporté.

**Acceptance Criteria:**

1. La fonction `main()` affiche un résumé formaté des métriques après génération
2. Le format d'affichage console inclut : participants, sessions, tables, paires uniques créées, répétitions, statistiques d'équité (min, max, moyenne, écart)
3. Les émojis sont optionnels (activés seulement si terminal supporte UTF-8)
4. En mode `--verbose`, affichage additionnel : temps d'exécution par phase, nombre d'itérations d'amélioration
5. Les tests vérifient :
   - Sortie console contient les métriques clés
   - Format lisible (pas de dump JSON brut)
6. Si configuration impossible détectée, un warning clair est affiché avant les métriques

### Story 3.7: Tests d'Intégration CLI End-to-End

As a développeur,
I want des tests complets validant le flux CLI de bout en bout,
so that je garantis que l'outil est utilisable en production par des non-développeurs.

**Acceptance Criteria:**

1. Un fichier `tests/test_cli_e2e.py` contient des tests end-to-end via subprocess
2. Test "Génération CSV simple" :
   - Exécution : `speed-dating-planner -n 30 -t 5 -c 6 -s 6 -o output.csv`
   - Exit code 0
   - Fichier `output.csv` créé avec 180 lignes (30×6)
   - Contenu CSV valide et conforme FR10
3. Test "Génération JSON avec seed" :
   - Exécution : `speed-dating-planner -n 100 -t 20 -c 5 -s 10 --format json --seed 42 -o output.json`
   - Exit code 0
   - JSON valide et conforme FR11
   - Reproductibilité : 2 exécutions avec même seed → même JSON
4. Test "Configuration invalide" :
   - Exécution : `speed-dating-planner -n 50 -t 5 -c 8 -s 3` (capacité insuffisante)
   - Exit code 1
   - Message d'erreur en français affiché
5. Test "Mode verbose" :
   - Exécution avec `--verbose`
   - Logs DEBUG visibles dans sortie
6. Tous les tests e2e passent et nettoient les fichiers générés (cleanup dans teardown)

### Story 3.8: Documentation Utilisateur Complète

As a organisateur d'événement,
I want une documentation claire m'expliquant comment installer et utiliser l'outil,
so that je peux générer mes plannings sans assistance technique.

**Acceptance Criteria:**

1. Le `README.md` contient une section "Installation" avec :
   - Prérequis (Python 3.10+)
   - Commandes d'installation (`pip install -e .` pour dev, ou `pip install speed-dating-planner` si publié)
   - Vérification de l'installation (`speed-dating-planner --help`)
2. Une section "Utilisation" avec :
   - Exemple basique avec paramètres minimaux
   - Exemple avancé avec tous les arguments
   - Explication de chaque paramètre
   - Interprétation des métriques affichées
3. Une section "Exemples Concrets" (NFR12) :
   - Petit événement (N=30)
   - Moyen événement (N=100)
   - Grand événement (N=300)
   - Pour chacun : commande complète + résultats attendus
4. Une section "Troubleshooting" avec :
   - Configuration invalide → que faire
   - Performance lente → attentes réalistes
   - Répétitions inévitables → explication mathématique
5. Le fichier `examples/cli_usage.sh` contient des exemples shell exécutables
6. Un fichier `docs/user-guide.md` approfondit l'utilisation avec captures d'écran simulées (texte)

---

## Checklist Results Report

### PM Checklist Validation - Executive Summary

**PRD Completeness:** 92%
**MVP Scope Appropriateness:** Just Right ✓
**Readiness for Architecture Phase:** **READY** ✓

### Category Statuses

| Category                         | Status | Critical Issues                                      |
| -------------------------------- | ------ | ---------------------------------------------------- |
| 1. Problem Definition & Context  | PASS   | Aucun (personas implicites mais clairs)              |
| 2. MVP Scope Definition          | PASS   | Aucun (séparation MVP/post-MVP exemplaire)           |
| 3. User Experience Requirements  | PASS   | Aucun (CLI-first approprié)                          |
| 4. Functional Requirements       | PASS   | Aucun (FR1-FR16 testables, priorités claires)       |
| 5. Non-Functional Requirements   | PASS   | Aucun (NFR1-NFR12 complets)                          |
| 6. Epic & Story Structure        | PASS   | Aucun (Epic 1-3 MVP détaillés)                       |
| 7. Technical Guidance            | PASS   | Aucun (Technical Assumptions exceptionnelles)        |
| 8. Cross-Functional Requirements | PASS   | Aucun (approprié pour outil CLI standalone)         |
| 9. Clarity & Communication       | PASS   | Aucun (document structuré, en français)              |

### Critical Deficiencies

**BLOCKERS:** Aucun

**Areas for Improvement (Non-Blocking):**
- Success metrics business quantifiés (adoption, satisfaction)
- User personas formalisés
- Competitive analysis

### Recommendations

✅ **PRD est READY FOR ARCHITECT**

**Next Steps:**
1. Passer ce PRD à l'Architect agent pour création de `docs/architecture.md`
2. L'Architect définira structure modules, patterns, interfaces pipeline, stratégies testing
3. Validation architecture → Scrum Master pour création stories détaillées
4. Dev agent pour implémentation Epic par Epic

### Final Decision

**READY FOR ARCHITECT** - Le PRD est exceptionnellement complet (92/100), bien structuré, et prêt pour la phase de design architectural.

---

## Epic 4: Edge Cases & Dynamic Management (Post-MVP)

**Epic Goal:** Gérer les cas limites et permettre la gestion dynamique des participants (retardataires, abandons) avec recalcul partiel du planning.

**Stories (High-Level):**
- Détection et signalement des configurations mathématiquement impossibles (FR12)
- Génération du meilleur planning possible pour configurations impossibles (FR13)
- Gestion de l'ajout dynamique de participants retardataires (FR14)
- Gestion des abandons de participants (FR15)
- Tests robustesse sur cas limites variés

---

## Epic 5: Visualization & Analysis Tools (Future)

**Epic Goal:** Ajouter des outils de visualisation et d'analyse avancée pour faciliter l'exploration et la validation des plannings.

**Stories (High-Level):**
- Création de notebook Jupyter interactif avec exemples
- Génération de heatmap des rencontres (matplotlib)
- Visualisation des métriques d'équité par session
- Outils de comparaison entre différents plannings
- Export vers formats additionnels (Excel, PDF)

---

## Next Steps

### UX Expert Prompt

**Note:** Ce projet est principalement un outil CLI algorithmique sans interface graphique complexe. L'UX Expert peut être **optionnel** pour ce MVP.

Si consultation UX souhaitée, utiliser ce prompt :

```
Analyser le PRD du système d'optimisation de tables rotatives (docs/prd.md) et valider que l'expérience CLI proposée est optimale pour les organisateurs d'événements.

Focus areas:
- Est-ce que l'interface CLI (arguments, flags) est intuitive ?
- Le format d'affichage des métriques console est-il clair et actionnable ?
- Les messages d'erreur en français sont-ils suffisamment explicites ?
- Y a-t-il des opportunités pour améliorer l'UX sans ajouter de complexité ?

Livrable: Recommandations UX pour améliorer la clarté et l'utilisabilité de la CLI (optionnel).
```

### Architect Prompt

```
Créer le document d'architecture technique complet pour le système d'optimisation de tables rotatives basé sur le PRD (docs/prd.md) et la session de brainstorming (docs/brainstorming-session-results.md).

Contexte:
- Outil CLI Python 3.10+ pour génération de plannings de networking/speed dating
- Architecture hybride 3 phases obligatoire : Baseline → Amélioration → Équité
- MVP = Epic 1-3 (Foundation + Optimization + CLI & Export)
- Contraintes: stdlib Python uniquement pour MVP, performance N≤1000 en <30s, équité ±1 garantie

Livrables requis dans docs/architecture.md:
1. Vue d'ensemble de l'architecture (schéma ASCII des 3 phases + flux de données)
2. Structure détaillée des modules Python avec responsabilités
3. Définition des interfaces entre modules (signatures fonctions clés)
4. Modèles de données (dataclasses exactes : Planning, Metrics, Config)
5. Stratégie de testing (unitaires, intégration, performance)
6. Décisions techniques justifiées (structures de données, patterns, algorithmes)
7. Gestion des erreurs et logging
8. Considérations de performance et scalabilité
9. Plan de migration/extension pour Epic 4-5 post-MVP

Contraintes importantes:
- Respecter les Technical Assumptions du PRD (Poetry, black/ruff/mypy, pytest, GitHub Actions)
- Architecture modulaire testable indépendamment (NFR9)
- HashMap pour historique rencontres (pas matrice N×N)
- Reproductibilité via seed (NFR11)
- Messages d'erreur en français (NFR10)

Créer une architecture propre, pragmatique et implémentable qui guide le développement des Epic 1-3 MVP.
```

---

**🎉 PRD COMPLET ET VALIDÉ - READY FOR NEXT PHASE**

Ce PRD a été créé par l'agent Product Manager (John) basé sur la session de brainstorming du 2026-01-10 avec l'agent Business Analyst (Mary).

**Document Version:** 1.0
**Status:** ✅ Ready for Architecture Phase
**Next Agent:** Architect

---
