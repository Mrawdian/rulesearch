"""
CANARI DU GEL DE T0-HISTORIQUE.

`engine/t0_legacy.py` fige le propagateur de reference de la metrique acquise
du projet — la resistance a T0. Ce canari verifie qu'il n'a pas bouge.

POURQUOI CE CANARI N'EST PAS REDONDANT AVEC LE GEL DU FICHIER
--------------------------------------------------------------
Figer `t0_legacy.py` ne suffit pas. Il appelle `rs.feasible(g, changed=i)`,
dont le comportement vit dans les classes de contraintes de `rulesearch.py` et
`dsl2.py` — que le chantier A va toucher. Une modification de `feasible()`
changerait les valeurs produites ici **sans que ce fichier ait bouge d'une
ligne**.

Ce canari ne compare donc pas a du code courant, qui va changer, mais a des
**nombres figes** : `canary/t0_reference.json`, 60 entrees produites le
2026-08-26 avant l'ouverture de A. Chaque entree fige le systeme (recette +
label), le PUZZLE lui-meme, et les deux valeurs attendues.

Le puzzle est stocke tel quel plutot que regenere : `random_solution` et
`minimal_clues` vivent dans `engine/` et peuvent legitimement changer. Les
regenerer rendrait ce canari sensible a des evolutions permises.

CE QU'UNE DIVERGENCE SIGNIFIE
------------------------------
Que la frontiere mesuree par la metrique acquise a bouge. La resistance a T0
mesure la non-localite **relativement a un propagateur** : un propagateur plus
fort mesure moins bien ce qu'il doit mesurer. Une divergence n'est donc pas un
desagrement a contourner en regenerant le corpus — **c'est le signal**.

Pouvoir de detection : les 40 entrees a resistance POSITIVE detectent un
propagateur RENFORCE (moins de cases restantes) ; les 20 a resistance NULLE
detectent un propagateur AFFAIBLI (des cases resteraient). Les deux sens sont
couverts.

Sortie non nulle = T0-historique a bouge.
"""
import json
import os
import random
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "engine"))

from t0_legacy import resistance
import run as RUN

CHEMIN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "t0_reference.json")

if not os.path.exists(CHEMIN):
    print("ECHEC : corpus de reference absent : %s" % CHEMIN)
    print("Il ne doit JAMAIS etre regenere pour faire passer ce canari.")
    sys.exit(1)

with open(CHEMIN, encoding="utf-8") as f:
    ref = json.load(f)

entrees = ref.get("entrees", [])
print("corpus fige du %s : %d entrees" % (ref.get("_date", "?"), len(entrees)))
if not entrees:
    print("ECHEC : corpus vide.")
    sys.exit(1)

divergences = []
introuvables = []
positives = nulles = 0

for e in entrees:
    rng = random.Random(e["seed"])
    rs = None
    for _ in range(e["idx"]):
        rs = RUN.gen_system(e["n"], e["d"], rng, e["familles"])
    if rs is None or rs.label != e["label"]:
        introuvables.append(e["label"])
        continue
    inc, rest = resistance(rs, e["puzzle"])
    if e["attendu_restantes"] > 0:
        positives += 1
    else:
        nulles += 1
    if inc != e["attendu_inconnues"] or rest != e["attendu_restantes"]:
        divergences.append((e["label"], e["attendu_inconnues"],
                            e["attendu_restantes"], inc, rest))

print("  verifiees : %d  (positives %d, nulles %d)"
      % (positives + nulles, positives, nulles))

ok = True

if introuvables:
    print()
    print("ECHEC : %d systeme(s) non reconstructible(s) — `gen_system` a change,"
          % len(introuvables))
    print("        ou les constructeurs de contraintes ont change.")
    for lab in introuvables[:5]:
        print("        %s" % lab[:64])
    ok = False

if divergences:
    print()
    print("ECHEC : %d divergence(s). T0-historique a bouge." % len(divergences))
    print("  %-38s %9s %9s" % ("systeme", "attendu", "obtenu"))
    for lab, ai, ar, oi, orr in divergences[:8]:
        print("  %-38s  %2d/%-4d   %2d/%-4d" % (lab[:38], ar, ai, orr, oi))
    print()
    print("  Un T0 plus fort (moins de cases restantes) mesure MOINS BIEN la")
    print("  non-localite : la frontiere mesuree a bouge. Ne pas regenerer le")
    print("  corpus — corriger ce qui a touche a `feasible()` ou a t0_legacy.")
    ok = False

print()
if not ok:
    sys.exit(1)
print("OK : T0-historique est intact, la metrique acquise garde sa reference.")
