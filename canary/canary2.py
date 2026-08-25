"""
CANARI v2 : la hierarchie de deduction doit SEPARER des systemes qu'on sait
differents. Si tout retombe au meme niveau, la metrique est encore vide.

Reference 1 : sudoku 4x4 -> doit se resoudre bas (T0/T1)
Reference 2 : sudoku 4x4 avec MOINS d'indices que le minimum deductible
              -> doit exiger T2 ou echouer
Reference 3 : systeme a connectivite -> doit resister au bas niveau
"""
import random, time
from rulesearch import *
from dsl2 import *
from deduction import solve_graded

random.seed(11)
n, d = 4, 4

sud = RuleSystem(n, d, [AllDiff(R) for R in rows(n) + cols(n) + blocks(n)],
                 "sudoku4")

# systeme a connectivite : binaire, cellules de valeur 1 connexes, pas de carre 2x2
conn = RuleSystem(n, 2,
                  [Connected(n, 1), NoSquare(n, 1),
                   Count(list(range(n * n)), 1, 7, 9)],
                  "CONNECTED(1)+NOSQUARE(1)+COUNT")

for rs in (sud, conn):
    print("==", rs.label)
    levels = []
    fracs = []
    for _ in range(8):
        sol = random_solution(rs)
        if sol is None:
            print("   pas de solution")
            break
        puz = minimal_clues(rs, sol)
        given = sum(1 for x in puz if x != UNASSIGNED)
        r = solve_graded(rs, puz)
        levels.append(r["max_level"] if r["solved"] else -1)
        fracs.append(given / (n * n))
    if levels:
        print("   niveaux max necessaires :", levels)
        print("   densite indices moy     : %.2f" % (sum(fracs) / len(fracs)))
        print("   resolus sans devinette  : %d/%d" % (sum(1 for x in levels if x >= 0), len(levels)))
    print()
