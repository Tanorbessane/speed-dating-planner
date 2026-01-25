#!/bin/bash
# Script de lancement rapide pour tests Stripe
# Usage: ./scripts/quick_test.sh

set -e

echo "========================================="
echo "🚀 Lancement Speed Dating Planner - TEST"
echo "========================================="
echo ""

# Vérifier config Stripe d'abord
echo "🔍 Vérification configuration Stripe..."
./scripts/verify_stripe_config.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Lancement Streamlit..."
    echo ""
    echo "📝 Carte de test recommandée:"
    echo "   Numéro: 4242 4242 4242 4242"
    echo "   MM/YY:  12/34"
    echo "   CVC:    123"
    echo ""
    echo "📚 Guide complet: docs/STRIPE_TESTING_GUIDE.md"
    echo "✅ Checklist: TEST_STRIPE_CHECKLIST.md"
    echo ""
    echo "========================================="
    echo ""

    # Lancer Streamlit
    ./venv/bin/streamlit run app/main.py
else
    echo ""
    echo "❌ Veuillez d'abord configurer Stripe correctement"
    exit 1
fi
