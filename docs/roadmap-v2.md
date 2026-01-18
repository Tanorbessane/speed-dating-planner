# Roadmap V2 - Production Interface & Features Événements

**Statut** : DRAFT - En attente validation choix technologiques
**Date** : 2026-01-12
**Auteur** : James (Dev Agent)

---

## 🎯 Objectifs V2

1. **Interface utilisateur** : Web locale ou desktop pour remplacer CLI
2. **Import participants** : CSV/Excel avec mapping colonnes
3. **Contraintes événements** : Groupes, interdictions, VIP
4. **Gestion dynamique** : Retardataires, abandons (FR14-FR15)
5. **Dashboards** : Visualisation métriques et analyses (Epic 5)
6. **Distribution** : Packaging pour utilisateurs finaux

---

## 📋 Architecture Proposée

### Option A : Streamlit (RECOMMANDÉ)

**Stack** :
- Frontend : Streamlit (widgets interactifs)
- Backend : Code existant src/ (aucun changement)
- Export : PDF/Excel en plus de CSV/JSON
- Déploiement : Executable standalone (PyInstaller)

**Structure** :
```
speedDating/
├── src/              # Code métier (INCHANGÉ)
├── app/              # Interface Streamlit
│   ├── pages/
│   │   ├── 1_📊_Dashboard.py
│   │   ├── 2_⚙️_Configuration.py
│   │   ├── 3_👥_Participants.py
│   │   ├── 4_🎯_Contraintes.py
│   │   └── 5_📈_Résultats.py
│   ├── components/   # Composants réutilisables
│   └── main.py       # Point d'entrée
├── tests/
└── dist/             # Executables packagés
```

**Avantages** :
- Développement rapide (2-3 semaines pour Epic 4-5)
- Hot-reload pour itérations rapides
- Widgets natifs (file uploader, dataframes, charts)
- Session state pour gestion contexte

**Inconvénients** :
- Dépendance runtime (streamlit, pandas, plotly)
- Moins de contrôle layout vs HTML custom

### Option B : Flask + Vanilla JS

**Stack** :
- Backend : Flask (routes API REST)
- Frontend : HTML5 + Vanilla JS (ou Alpine.js)
- Templating : Jinja2
- Charts : Chart.js ou D3.js

**Avantages** :
- Contrôle total UI/UX
- Peut devenir API pour intégrations futures
- Léger et standard

**Inconvénients** :
- Plus de code à écrire (templates, JS, CSS)
- Développement plus long (4-6 semaines)

### Option C : CLI Améliorée (Textual)

**Stack** :
- TUI : Textual (Rich sous le capot)
- Interface : Menus, formulaires, tableaux
- Reste 100% terminal

**Avantages** :
- Cohérent avec CLI actuelle
- Pas de dépendances web
- Scriptable/automatable

**Inconvénients** :
- UX limitée vs web
- Pas de visualisations riches (charts)

---

## 🚀 Epic 4 : Gestion Événements Réels

**Epic Goal** : Permettre la gestion complète d'un événement réel avec import participants, contraintes, et ajustements dynamiques.

### Story 4.1 : Import Participants (CSV/Excel)

**User Story** :
En tant qu'organisateur,
Je veux importer une liste de participants depuis CSV/Excel,
Afin de ne pas saisir manuellement 50-300 noms.

**Acceptance Criteria** :
1. L'interface permet d'uploader CSV ou Excel (.xlsx)
2. L'utilisateur peut mapper les colonnes :
   - `participant_id` (optionnel, auto-généré si absent)
   - `nom` (requis)
   - `prenom` (optionnel)
   - `email` (optionnel)
   - `groupe` (optionnel, pour contraintes)
   - `tags` (optionnel, ex: "VIP", "Speaker")
3. Preview des 10 premières lignes avant import
4. Validation : détection doublons, colonnes manquantes
5. Import stocké en mémoire (session state) ou fichier JSON
6. Export template CSV vierge téléchargeable

**Tech** :
- Streamlit : `st.file_uploader`, `st.dataframe`, `st.download_button`
- Pandas : `pd.read_csv()`, `pd.read_excel()`
- Validation : dataclass `Participant(id, nom, prenom, email, groupe, tags)`

**Files** :
- `app/pages/3_👥_Participants.py` : Interface import
- `src/participants.py` : Logic import/validation
- `tests/test_participants.py` : Tests validation

---

### Story 4.2 : Contraintes - Groupes Imposés

**User Story** :
En tant qu'organisateur,
Je veux forcer certains participants à être toujours ensemble (ex: partenaires de danse),
Afin qu'ils ne soient jamais séparés.

**Acceptance Criteria** :
1. Interface pour définir groupes :
   - Nom du groupe
   - Liste des participant IDs
   - Type : "Toujours ensemble" ou "Jamais ensemble"
2. Validation : un participant ne peut être dans 2 groupes incompatibles
3. Algorithme baseline adapté :
   - Groupe "ensemble" traité comme 1 méta-participant
   - Assignation aux mêmes tables toujours
4. Export JSON inclut contraintes respectées

**Tech** :
- Nouveau : `src/constraints.py` avec classes :
  - `MustBeTogetherConstraint(participants: List[int])`
  - `MustBeSeparatedConstraint(participants: List[int])`
- Modifier `src/baseline.py` pour respecter contraintes

**Files** :
- `src/constraints.py` : Définition contraintes
- `src/baseline.py` : Adaptation round-robin avec contraintes
- `app/pages/4_🎯_Contraintes.py` : Interface gestion
- `tests/test_constraints.py` : Tests validation

---

### Story 4.3 : Contraintes - Interdictions

**User Story** :
En tant qu'organisateur,
Je veux interdire que certains participants se rencontrent (ex: ex-conjoints),
Afin d'éviter des situations inconfortables.

**Acceptance Criteria** :
1. Interface pour ajouter paires interdites :
   - Sélection participant 1 + participant 2
   - Raison optionnelle (texte libre)
2. Validation lors de la génération :
   - Algorithme refuse si contrainte violable mathématiquement
   - Sinon garantit jamais à la même table
3. Rapport post-génération : toutes contraintes respectées

**Tech** :
- Extension `src/constraints.py` :
  - `ForbiddenPairConstraint(p1: int, p2: int, reason: str)`
- Modifier `src/swap_evaluation.py` pour rejeter swaps violant contraintes

**Files** :
- Extension `src/constraints.py`
- Modification `src/baseline.py` + `src/swap_evaluation.py`
- Tests `tests/test_constraints.py`

---

### Story 4.4 : Priorités VIP

**User Story** :
En tant qu'organisateur,
Je veux que certains VIP rencontrent le maximum de personnes différentes,
Afin d'optimiser leur expérience.

**Acceptance Criteria** :
1. Interface pour taguer participants "VIP" ou "Priority"
2. Algorithme d'équité adapté :
   - VIP reçoivent priorité pour tables pleines
   - Equity_gap calculé séparément pour VIP vs non-VIP
3. Métriques séparées dans résultats :
   - VIP : min/max/avg rencontres uniques
   - Non-VIP : min/max/avg rencontres uniques

**Tech** :
- Modifier `PlanningMetrics` pour ajouter `vip_metrics: Optional[VIPMetrics]`
- Adapter `src/equity.py` pour prioriser VIP

**Files** :
- `src/models.py` : Ajout champ `is_vip: bool` dans Participant
- `src/equity.py` : Adaptation algorithme
- Tests

---

### Story 4.5 : Retardataires (FR14)

**User Story** :
En tant qu'organisateur,
Je veux ajouter un participant arrivé en retard à partir de session 3,
Sans régénérer tout le planning.

**Acceptance Criteria** :
1. Interface "Ajouter retardataire" :
   - Nom du participant
   - Session de départ (ex: session 3/6)
2. Algorithme recalcule UNIQUEMENT sessions futures (3→6)
3. Sessions passées (1-2) : retardataire marqué "absent"
4. Export CSV inclut absences (ligne vide ou `table_id=-1`)

**Tech** :
- Nouveau : `src/dynamic_planning.py`
  - `add_latecomer(planning, participant_id, start_session, config)`
  - Réutilise `generate_baseline` sur sous-ensemble sessions
- Modification `src/exporters.py` pour gérer absences

**Files** :
- `src/dynamic_planning.py` : Logic ajout/retrait
- `app/pages/2_⚙️_Configuration.py` : Interface ajout retardataire
- Tests

---

### Story 4.6 : Abandons (FR15)

**User Story** :
En tant qu'organisateur,
Je veux gérer un participant qui quitte l'événement après session 4,
Afin de redistribuer sa place.

**Acceptance Criteria** :
1. Interface "Retirer participant" :
   - Sélection participant + session de départ
2. Algorithme recalcule sessions futures avec N-1 participants
3. Sessions passées : participant conservé dans historique
4. Métriques recalculées sans le participant retiré

**Tech** :
- Extension `src/dynamic_planning.py` :
  - `remove_participant(planning, participant_id, from_session, config)`

**Files** :
- Extension `src/dynamic_planning.py`
- Interface
- Tests

---

### Story 4.7 : Configuration Priorités (FR16)

**User Story** :
En tant qu'organisateur avancé,
Je veux ajuster les priorités d'optimisation (rencontres uniques vs équité),
Pour adapter l'algo à mon contexte spécifique.

**Acceptance Criteria** :
1. Fichier `config.yaml` optionnel :
   ```yaml
   optimization:
     weights:
       unique_meetings: 0.7  # 70%
       equity: 0.3           # 30%
     max_iterations: 50
     plateau_threshold: 5
   ```
2. Interface "Réglages avancés" pour éditer sans YAML
3. Algorithme `improve_planning` utilise poids pour scorer swaps

**Tech** :
- Dépendance : `pyyaml` (si choix YAML)
- Modifier `src/swap_evaluation.py` pour weighted scoring
- Streamlit : `st.number_input` pour sliders poids

**Files** :
- `src/config.py` : Chargement config
- Modification algorithmes
- Tests

---

## 📊 Epic 5 : Dashboards & Visualisation

**Epic Goal** : Fournir dashboards interactifs pour analyser la qualité du planning et valider visuellement les résultats.

### Story 5.1 : Dashboard Général

**User Story** :
En tant qu'organisateur,
Je veux voir un dashboard récapitulatif après génération,
Pour valider rapidement la qualité du planning.

**Acceptance Criteria** :
1. Page dashboard avec 4 sections :
   - **KPIs** : Total participants, sessions, paires uniques, répétitions
   - **Équité** : Histogramme distribution rencontres uniques par participant
   - **Qualité** : Gauge equity_gap (vert si ≤1, orange si >1)
   - **Timeline** : Durée génération, performance NFR1-3
2. Boutons actions :
   - Régénérer avec autre seed
   - Exporter (CSV/JSON/PDF)
   - Partager lien (si web)

**Tech** :
- Streamlit : `st.metric`, `st.bar_chart`, `st.plotly_chart`
- Plotly : Graphs interactifs

**Files** :
- `app/pages/1_📊_Dashboard.py`
- `app/components/kpi_cards.py`
- `app/components/charts.py`

---

### Story 5.2 : Matrice de Rencontres (Heatmap)

**User Story** :
En tant qu'organisateur,
Je veux visualiser quels participants se sont rencontrés,
Pour détecter visuellement les problèmes (clusters, isolation).

**Acceptance Criteria** :
1. Heatmap N×N participants :
   - Axe X/Y : participant IDs
   - Couleur : nombre de rencontres (0=blanc, 1=vert, 2+=rouge)
2. Hover : noms participants + sessions communes
3. Filtre : afficher seulement répétitions (≥2)

**Tech** :
- Plotly Heatmap : `go.Heatmap`
- Calcul matrice à partir `meeting_history`

**Files** :
- `app/pages/5_📈_Résultats.py` : Onglet "Heatmap"
- `src/visualizations.py` : Génération heatmap data

---

### Story 5.3 : Export PDF avec Logos

**User Story** :
En tant qu'organisateur,
Je veux exporter un PDF avec logo de mon événement et tables imprimables,
Pour distribuer aux participants.

**Acceptance Criteria** :
1. Upload logo (.png/.jpg)
2. Template PDF :
   - En-tête : Logo + nom événement
   - Par session : tables avec noms participants (pas IDs)
   - Footer : "Généré par Speed Dating Planner v2.0"
3. Format A4, imprimable

**Tech** :
- Dépendance : `reportlab` ou `weasyprint`
- Jinja2 : Template HTML → PDF

**Files** :
- `src/export_pdf.py` : Génération PDF
- `templates/planning_template.html` : Template
- Tests

---

### Story 5.4 : Graphe Social (NetworkX)

**User Story** :
En tant qu'organisateur,
Je veux voir un graphe des rencontres (participants = nodes, rencontres = edges),
Pour analyser la structure sociale de l'événement.

**Acceptance Criteria** :
1. Graphe interactif :
   - Nodes : participants (taille = nb rencontres)
   - Edges : rencontres (épaisseur = nb fois)
   - Layout : force-directed (spring)
2. Détection clusters/communautés
3. Export PNG haute résolution

**Tech** :
- NetworkX : construction graphe
- Plotly : `go.Scatter` avec layout networkx
- Communautés : `networkx.community.louvain_communities`

**Files** :
- `app/pages/5_📈_Résultats.py` : Onglet "Graphe social"
- `src/graph_analysis.py` : Logic graphe

---

### Story 5.5 : Statistiques Avancées

**User Story** :
En tant qu'organisateur data-driven,
Je veux des statistiques avancées (écart-type, coefficient variation),
Pour comparer plusieurs plannings.

**Acceptance Criteria** :
1. Onglet "Stats avancées" :
   - Distribution rencontres : moyenne, médiane, écart-type, CV
   - Qualité répétitions : Gini coefficient
   - Comparaison seeds : tableau scores multiples seeds
2. Export statistiques en CSV

**Tech** :
- Numpy/Scipy : calculs statistiques
- Streamlit : `st.dataframe` comparatif

**Files** :
- `src/statistics.py` : Calculs avancés
- Interface

---

## 📦 Epic 6 : Distribution & Packaging

**Epic Goal** : Permettre la distribution du logiciel aux utilisateurs finaux sans installation Python.

### Story 6.1 : Executable Standalone (PyInstaller)

**User Story** :
En tant qu'organisateur non-technique,
Je veux télécharger un .exe/.app et lancer directement,
Sans installer Python/pip.

**Acceptance Criteria** :
1. Build scripts :
   - Windows : `speedDating.exe`
   - macOS : `SpeedDatingPlanner.app`
   - Linux : `speedDating` (AppImage)
2. Taille : <100MB
3. Double-clic lance Streamlit sur localhost:8501
4. README instructions simple (3 lignes)

**Tech** :
- PyInstaller : `pyinstaller --onefile --windowed`
- Assets inclus (templates, config)

**Files** :
- `build/build.py` : Script build multi-plateformes
- `build/speedDating.spec` : Config PyInstaller
- `README-USERS.md` : Instructions utilisateurs

---

### Story 6.2 : Auto-Update (optionnel)

**User Story** :
En tant qu'utilisateur,
Je veux être notifié quand une nouvelle version est disponible,
Pour bénéficier des améliorations.

**Acceptance Criteria** :
1. Au lancement : check version GitHub Releases
2. Si nouvelle version : popup avec changelog
3. Bouton "Télécharger" vers release page
4. Option "Ne plus demander pour cette version"

**Tech** :
- Requests : GET `https://api.github.com/repos/user/repo/releases/latest`
- Streamlit : `st.info` pour notification

**Files** :
- `app/update_checker.py`
- Config version dans `pyproject.toml`

---

## 🗓️ Timeline Estimée

**Epic 4 : Gestion Événements** (3-4 semaines)
- Story 4.1 : 3 jours (Import participants)
- Story 4.2-4.3 : 5 jours (Contraintes groupes/interdictions)
- Story 4.4 : 2 jours (VIP)
- Story 4.5-4.6 : 4 jours (Retardataires/abandons)
- Story 4.7 : 2 jours (Config priorités)

**Epic 5 : Dashboards** (2-3 semaines)
- Story 5.1 : 3 jours (Dashboard général)
- Story 5.2 : 2 jours (Heatmap)
- Story 5.3 : 3 jours (Export PDF)
- Story 5.4 : 3 jours (Graphe social)
- Story 5.5 : 2 jours (Stats avancées)

**Epic 6 : Distribution** (1 semaine)
- Story 6.1 : 4 jours (Packaging)
- Story 6.2 : 1 jour (Auto-update)

**Total V2 : 6-8 semaines** (selon parallélisation et tests)

---

## ✅ Décision Requise

**Question immédiate** : Quelle architecture interface préférez-vous ?

1. **Option A : Streamlit** (rapide, Python pur, dashboards natifs) ⭐
2. **Option B : Flask + Vanilla JS** (flexible, API REST)
3. **Option C : CLI TUI (Textual)** (terminal moderne)

**Ma recommandation** : **Option A** pour MVP V2, migration Flask possible plus tard si besoin API REST pour intégrations.

Validez votre choix, et je commence immédiatement avec Story 4.1 ! 🚀
