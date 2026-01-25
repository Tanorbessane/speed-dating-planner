# ✅ Checklist de Test Stripe - Speed Dating Planner

**Date:** 2026-01-24
**Objectif:** Valider l'intégration Stripe complète avant production

---

## 📋 Phase 1 : Préparation (5 minutes)

### ✅ 1.1 - Compte Stripe TEST

- [ ] Aller sur https://dashboard.stripe.com/register
- [ ] Créer un compte gratuit (ou se connecter)
- [ ] **ACTIVER LE MODE TEST** (toggle en haut à gauche du dashboard)
- [ ] Vérifier que vous voyez "Viewing test data" dans le dashboard

### ✅ 1.2 - Récupérer les Clés TEST

- [ ] Aller dans **Developers > API keys**
- [ ] Copier **Publishable key** (commence par `pk_test_...`)
- [ ] Copier **Secret key** (cliquer "Reveal test key", commence par `sk_test_...`)

### ✅ 1.3 - Configurer l'Application

- [ ] Ouvrir le fichier `.streamlit/secrets.toml`
- [ ] Remplacer `YOUR_SECRET_KEY_HERE` par votre clé secrète TEST
- [ ] Remplacer `YOUR_PUBLISHABLE_KEY_HERE` par votre clé publique TEST
- [ ] **Vérifier** que les clés commencent bien par `sk_test_` et `pk_test_`
- [ ] Sauvegarder le fichier

**Exemple de configuration valide :**
```toml
[stripe]
secret_key = "sk_test_51ABC...XYZ"
publishable_key = "pk_test_51ABC...XYZ"
```

---

## 🚀 Phase 2 : Lancement Application (2 minutes)

### ✅ 2.1 - Démarrer Streamlit

```bash
# Dans le terminal, depuis le répertoire speedDating/
./venv/bin/streamlit run app/main.py
```

**Résultat attendu :**
- [ ] Terminal affiche : `You can now view your Streamlit app in your browser.`
- [ ] URL locale : `http://localhost:8501`
- [ ] Navigateur s'ouvre automatiquement

### ✅ 2.2 - Vérifier Logs Stripe

Dans le terminal, chercher :
```
INFO: Stripe initialisé en mode TEST
```

- [ ] ✅ Si "mode TEST" → Configuration correcte !
- [ ] ❌ Si "mode LIVE" → STOP ! Vérifier les clés (doivent commencer par `sk_test_`)
- [ ] ❌ Si erreur "Configuration Stripe manquante" → Vérifier `.streamlit/secrets.toml`

---

## 🧪 Phase 3 : Tests Fonctionnels (10 minutes)

### ✅ Test 1 : Paiement Pro Réussi ✅

**Objectif :** Tester le flow complet d'upgrade vers Pro

**Steps :**
1. [ ] Dans l'app, aller sur **💳 Pricing**
2. [ ] Cliquer **"⬆️ Upgrade vers Pro - 29€/mois"**
3. [ ] Remplir le formulaire Stripe avec la **carte de test** :
   ```
   Numéro carte:  4242 4242 4242 4242
   MM/YY:        12/34
   CVC:          123
   Code postal:  12345
   Email:        test@example.com
   ```
4. [ ] Cliquer **"Subscribe"**

**Résultat attendu :**
- [ ] ✅ Redirection vers page de confirmation
- [ ] ✅ Message "Paiement Réussi !" avec 🎉 balloons
- [ ] ✅ Email de confirmation affiché

**Vérification Stripe Dashboard :**
- [ ] Aller sur https://dashboard.stripe.com/test/payments
- [ ] ✅ Voir un paiement de **29,00 € EUR** avec statut **Succeeded**
- [ ] ✅ Customer email : `test@example.com` (ou votre email)

---

### ✅ Test 2 : Paiement Business Réussi ✅

**Steps :**
1. [ ] Page **💳 Pricing**
2. [ ] Cliquer **"💎 Upgrade vers Business - 99€/mois"**
3. [ ] Utiliser la même carte test : `4242 4242 4242 4242`
4. [ ] Cliquer Subscribe

**Résultat attendu :**
- [ ] ✅ Confirmation paiement **99,00 € EUR**
- [ ] ✅ Statut **Succeeded** dans Stripe Dashboard

---

### ✅ Test 3 : Paiement Refusé (Carte Déclinée) ❌

**Objectif :** Vérifier que l'error handling fonctionne

**Steps :**
1. [ ] Page **💳 Pricing**
2. [ ] Cliquer **"⬆️ Upgrade vers Pro"**
3. [ ] Utiliser la **carte qui échoue** :
   ```
   Numéro carte:  4000 0000 0000 0002
   MM/YY:        12/34
   CVC:          123
   ```
4. [ ] Cliquer Subscribe

**Résultat attendu :**
- [ ] ❌ Message d'erreur Stripe : **"Your card was declined"**
- [ ] ✅ Utilisateur reste sur page Pricing
- [ ] ✅ **Aucun paiement** créé dans Stripe Dashboard

---

### ✅ Test 4 : Annulation Paiement ❌

**Objectif :** Tester le flow d'annulation

**Steps :**
1. [ ] Page **💳 Pricing**
2. [ ] Cliquer **"⬆️ Upgrade vers Pro"**
3. [ ] Sur la page Stripe, cliquer **← Back** (bouton retour)

**Résultat attendu :**
- [ ] ✅ Redirection vers page Pricing
- [ ] ✅ Utilisateur revient sur l'app
- [ ] ✅ **Aucun paiement** créé dans Stripe Dashboard

---

### ✅ Test 5 : 3D Secure Authentication 🔒

**Objectif :** Tester l'authentification forte

**Steps :**
1. [ ] Page **💳 Pricing**
2. [ ] Cliquer **"⬆️ Upgrade vers Pro"**
3. [ ] Utiliser la **carte 3D Secure** :
   ```
   Numéro carte:  4000 0025 0000 3155
   MM/YY:        12/34
   CVC:          123
   ```
4. [ ] Cliquer Subscribe

**Résultat attendu :**
- [ ] ✅ Popup **3D Secure** apparaît
- [ ] ✅ Cliquer **"Complete"** dans la popup
- [ ] ✅ Paiement **accepté**
- [ ] ✅ Redirection vers confirmation

---

## 📊 Phase 4 : Vérification Dashboard Stripe (5 minutes)

### ✅ 4.1 - Vérifier les Paiements

- [ ] Aller sur https://dashboard.stripe.com/test/payments
- [ ] ✅ Voir **3 paiements réussis** (Pro + Business + 3D Secure)
- [ ] ✅ **0 paiement** pour carte déclinée (normal)
- [ ] ✅ Tous les statuts = **Succeeded**

### ✅ 4.2 - Vérifier les Customers

- [ ] Aller sur https://dashboard.stripe.com/test/customers
- [ ] ✅ Voir les clients créés avec leurs emails
- [ ] ✅ Cliquer sur un client → voir détails

### ✅ 4.3 - Vérifier les Abonnements

- [ ] Aller sur https://dashboard.stripe.com/test/subscriptions
- [ ] ✅ Voir les abonnements **Active**
- [ ] ✅ Plans : **Pro (29€/mois)** et **Business (99€/mois)**

---

## 🔍 Phase 5 : Tests Edge Cases (Optionnel - 5 minutes)

### ✅ Test 6 : Fonds Insuffisants

**Carte :**
```
4000 0000 0000 9995
```

**Résultat attendu :**
- [ ] ❌ Message : "Your card has insufficient funds"

---

### ✅ Test 7 : Carte Expirée

**Carte :**
```
4000 0000 0000 0069
```

**Résultat attendu :**
- [ ] ❌ Message : "Your card has expired"

---

## ✅ Résumé Final - Checklist Complète

| Test | Statut | Notes |
|------|--------|-------|
| Configuration Stripe TEST | ⬜ |  |
| Logs "mode TEST" au démarrage | ⬜ |  |
| Paiement Pro réussi (4242...) | ⬜ |  |
| Paiement Business réussi | ⬜ |  |
| Paiement refusé (0002) | ⬜ |  |
| Annulation paiement | ⬜ |  |
| 3D Secure (3155) | ⬜ |  |
| Paiements visibles Dashboard | ⬜ |  |
| Clients créés Dashboard | ⬜ |  |
| Abonnements actifs Dashboard | ⬜ |  |

---

## 🎉 Tests Passés avec Succès ?

**Si tous les tests ✅ :**
→ L'intégration Stripe est **VALIDÉE** ! Vous êtes prêt pour la production.

**Si des tests ❌ :**
→ Notez les erreurs et revenez vers moi avec les détails (logs, screenshots, messages d'erreur).

---

## 🚨 Troubleshooting Rapide

### Problème : "Configuration Stripe manquante"

**Solution :**
1. Vérifier que `.streamlit/secrets.toml` existe
2. Vérifier que les clés sont renseignées (pas de "YOUR_...HERE")
3. Relancer Streamlit

---

### Problème : "Invalid API Key"

**Solution :**
1. Vérifier que la clé commence par `sk_test_` (pas `sk_live_`)
2. Re-copier la clé depuis Stripe Dashboard (sans espaces)
3. S'assurer d'être en mode TEST dans Stripe Dashboard

---

### Problème : Redirect après paiement ne fonctionne pas

**Solution :**
- En **LOCAL** : URLs sont `http://localhost:8501/`
- En **PRODUCTION** : Modifier dans `app/pages/7_💳_Pricing.py` lignes 104 et 105

---

## 📚 Ressources

- **Guide complet** : `docs/STRIPE_TESTING_GUIDE.md`
- **Cartes de test** : https://stripe.com/docs/testing
- **Dashboard TEST** : https://dashboard.stripe.com/test
- **Support Stripe** : https://support.stripe.com

---

**🎯 Bon test ! Revenez avec vos résultats.**
