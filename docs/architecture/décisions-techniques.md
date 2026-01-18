# 6. Décisions Techniques

## 6.1 Structures de Données

### Décision 1 : HashMap pour Historique Rencontres

**Choix retenu :** `Set[Tuple[int, int]]` (HashMap implicite Python)

**Alternatives considérées :**
- Matrice N×N booléenne : O(N²) mémoire toujours, lookup O(1)
- Bitset compacté : mémoire efficace mais complexité implémentation
- Graphe NetworkX : flexible mais dépendance externe

**Justification :**
- Mémoire proportionnelle aux paires réellement rencontrées : O(min(N², S×X×x²))
- Pour configurations typiques (N=300, S=15, x=5) : ~22k paires << 90k (matrice)
- Lookup O(1) grâce hashset Python
- Stdlib uniquement (pas de dépendance)
- Simple à tester et débugger

**Impact NFR4 :** Empreinte mémoire garantie <O(N²) dans le pire cas.

---

### Décision 2 : Représentation Planning

**Choix retenu :** `Planning = List[Session]` où `Session = List[Set[int]]`

**Alternatives considérées :**
- Dict[session_id, Dict[table_id, Set[int]]] : plus verbeux
- Matrice 3D `[S][X][x]` : tailles variables problématiques

**Justification :**
- Sémantique claire : liste ordonnée de sessions
- Tables de tailles variables gérées naturellement (Sets de tailles différentes)
- Itération simple : `for session in planning.sessions`
- Compatible export direct CSV/JSON

---

## 6.2 Algorithmes

### Décision 3 : Round-Robin avec Stride pour Baseline

**Choix retenu :** Rotation systématique avec stride coprime

**Alternatives considérées :**
- Permutations aléatoires : non déterministe
- Constructions algébriques (Latin squares) : limitées à paramètres spécifiques

**Justification :**
- Déterministe (NFR11)
- Complexité O(N×S) garantie
- Mélange efficace via stride (évite blocs statiques)
- Générique (fonctionne pour tous N, X, x, S)

**Implémentation détaillée :**
```python
stride = (session_id * 17 + 1) % N  # 17 coprime avec la plupart des N
participants = [participants[(i * stride) % N] for i in range(N)]
```

---

### Décision 4 : Amélioration Gloutonne avec Plateau Local

**Choix retenu :** Swaps locaux itératifs avec arrêt si aucune amélioration

**Alternatives considérées :**
- Recuit simulé : complexité code élevée, paramètres à tuner
- Recherche tabou : mémoire additionnelle
- Algorithme génétique : non déterministe, temps variable

**Justification :**
- Déterministe (seed fixe)
- Complexité contrôlable (max_iterations)
- Plateau local = efficacité (évite itérations inutiles)
- Simple à tester et débugger

**Trade-off accepté :** Optimum local (pas global), mais suffisant pour qualité pratique.

---

## 6.3 Patterns et Architecture

### Décision 5 : Pipeline Séquentiel (pas Reactive)

**Choix retenu :** Phases exécutées séquentiellement (baseline → improve → equity)

**Alternatives considérées :**
- Pipeline réactif (RxPy) : over-engineering pour MVP
- Parallélisation phases : dépendances entre phases interdisent

**Justification :**
- Simplicité : code linéaire facile à suivre
- Testabilité : chaque phase testable isolément
- Performance suffisante (NFR1-3 respectés sans parallélisation)

---

### Décision 6 : Logging (stdlib) vs Metrics (non)

**Choix retenu :** Module `logging` standard, pas de télémétrie

**Justification :**
- Outil standalone offline (pas de métriques distantes)
- Logging INFO pour progression, DEBUG pour troubleshooting
- Messages français (NFR10)

**Configuration :**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
```

---

## 6.4 Gestion Edge Cases

### Décision 7 : Tables Partielles (Remainder Distribution)

**Problème :** Si N=37, X=6, x=7 → 6×7=42 > 37, comment répartir ?

**Choix retenu :** Répartir remainder sur premières tables
```python
base_size = N // X  # 37 // 6 = 6
remainder = N % X   # 37 % 6 = 1
# Tables: [7, 6, 6, 6, 6, 6] → écart ≤1 ✓
```

**Alternative rejetée :** Répartition aléatoire (non déterministe)

**Garantie FR7 :** `max(sizes) - min(sizes) ≤ 1`

---

### Décision 8 : Configuration Impossible (Best Effort)

**Problème :** Si S×(x-1) < N-1, zéro répétition mathématiquement impossible

**Choix retenu :**
1. Détecter condition dans `generate_optimized_planning`
2. Logger WARNING explicite en français
3. Continuer génération (minimiser répétitions + garantir équité)

**Justification :**
- Transparence utilisateur (warning clair)
- Toujours retourner résultat utilisable (meilleur planning possible)
- Équité ±1 respectée même avec répétitions

---
