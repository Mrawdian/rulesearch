#!/bin/sh
# LE CONTROLE DE CIRCULARITE, dans l'ordre des controles BLOQUANTS d'abord.
# Chaque etape ecrit son propre journal ; aucune n'est lue avant la precedente.
cd /home/rulesearch/rulesearch || exit 1

echo "=== 1. CANARY3 : zero solution fausse ==="
PYTHONPATH=$PWD/engine python3 -u canary/canary3.py > bench/ctrl_canary3.log 2>&1
echo "canary3 exit=$?"

echo "=== 2. LOCALISATION DU FORCAGE (bloquant) ==="
python3 -u bench/diag_art2.py > bench/ctrl_localisation.log 2>&1
echo "localisation exit=$?"

echo "=== 3. GAIN_PROPAGATION, deux bras ==="
python3 -u bench/gain_propagation.py --systemes 150 --instances 6 \
        --canari-systemes 60 > bench/ctrl_gain.log 2>&1
echo "gain exit=$?"

echo "=== 4. GAIN_STRATES : le sous-groupe ou r se lit ==="
python3 -u bench/gain_strates.py > bench/ctrl_strates.log 2>&1
echo "strates exit=$?"

echo "=== FIN ==="
