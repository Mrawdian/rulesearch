"""
CANARI DE CORRECTION (invariant 3 de CLAUDE.md).

Remplir la grille ne suffit pas : la deduction doit retrouver EXACTEMENT la
solution d'origine. Une technique fausse remplit ET se trompe, et rien dans
les journaux ne le signalerait.

C'est ce canari qui aurait attrape le bug T1 (hidden single applique a des
regions qui n'exigent pas la presence de chaque valeur).

Sortie non nulle = au moins une divergence = le moteur ment.
"""
import random, sys
from rulesearch import *
from dsl2 import *
from deduction import apply_T0, apply_T1, apply_T2, t1_regions

random.seed(23)
n = 4


def solve_and_grid(rs, puzzle):
    g = list(puzzle)
    while True:
        p0, c0 = apply_T0(rs, g)
        if c0:
            return None
        if p0:
            continue
        p1, c1 = apply_T1(rs, g)
        if c1:
            return None
        if p1:
            continue
        p2, c2 = apply_T2(rs, g)
        if c2:
            return None
        if p2:
            continue
        break
    return g if all(x != UNASSIGNED for x in g) else None


rng = random.Random(5)
cages = random_cages(n, rng)

tests = [
    ("sudoku4", RuleSystem(n, 4, [AllDiff(R) for R in rows(n) + cols(n) + blocks(n)], "s")),
    ("connect", RuleSystem(n, 2, [Connected(n, 1), NoSquare(n, 1),
                                  Count(list(range(16)), 1, 7, 9)], "c")),
    ("count+neqadj", RuleSystem(n, 3, [Count(R, 1, 1, 2) for R in rows(n)]
                                + [NeqAdj(R) for R in cols(n)], "x")),
    ("cages+sum", RuleSystem(n, 4, [AllDiff(R) for R in rows(n) + cols(n)]
                             + [SumRange(C, len(C), len(C) * 2, 4) for C in cages], "g")),
    ("pairdiff", RuleSystem(n, 4, [AllDiff(R) for R in rows(n) + cols(n)]
                            + [PairDiff(adj_pairs(n), 1, n)], "p")),
]

total_div = 0
for name, rs in tests:
    solved = div = tot = 0
    for _ in range(12):
        sol = random_solution(rs)
        if sol is None:
            continue
        tot += 1
        puz = minimal_clues(rs, sol)
        g = solve_and_grid(rs, puz)
        if g is not None:
            solved += 1
            if g != sol:
                div += 1
    total_div += div
    print("%-14s instances=%2d resolues=%2d DIVERGENCES=%d (T1 sur %d regions)"
          % (name, tot, solved, div, len(t1_regions(rs))))

if total_div:
    print("\nECHEC : la deduction ne retrouve pas la solution d'origine.")
    sys.exit(1)
print("\nOK : aucune divergence.")
