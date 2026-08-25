"""
CANARI DE DECOUVERTE.
Avant de chercher quoi que ce soit, verifier que le moteur reconnait
un systeme de regles CONNU comme bien pose.

Sudoku 4x4 = ALLDIFF sur lignes + colonnes + blocs, d=4.
Attendu : instances a solution unique, deductibles, densite d'indices
nettement inferieure a 1.

Contre-canari : un systeme SANS contrainte doit donner une densite
d'indices de 1.0 (il faut tout donner pour que la solution soit unique)
et une profondeur de deduction nulle.
"""
import random, time
from rulesearch import *

random.seed(7)

n, d = 4, 4
cons = []
for R in rows(n) + cols(n) + blocks(n):
    cons.append(AllDiff(R))
sudoku4 = RuleSystem(n, d, cons, "ALLDIFF@rows+cols+blocks (sudoku4)")

t = time.time()
st = evaluate(sudoku4, n_instances=10)
print("== CANARI POSITIF : sudoku 4x4 ==")
print("  instances generees   :", st["instances"])
print("  deductibles sans devinette :", st["deducible"], "/", st["instances"])
if st["clue_frac"]:
    print("  densite d'indices moy      : %.2f" % (sum(st["clue_frac"]) / len(st["clue_frac"])))
if st["depths"]:
    print("  profondeur moyenne         : %.1f" % (sum(st["depths"]) / len(st["depths"])))
print("  temps %.1fs" % (time.time() - t))

# contre-canari : aucune contrainte
empty = RuleSystem(n, d, [Count(list(range(n * n)), 0, 0, n * n)], "AUCUNE CONTRAINTE")
st2 = evaluate(empty, n_instances=5)
print()
print("== CONTRE-CANARI : systeme sans contrainte reelle ==")
print("  densite d'indices moy      : %.2f" % (sum(st2["clue_frac"]) / len(st2["clue_frac"])))
print("  profondeur moyenne         :", st2["depths"])
print("  (attendu : densite 1.00, aucune deduction)")
