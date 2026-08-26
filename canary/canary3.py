"""
CANARI DE CORRECTION (invariant 3 de CLAUDE.md).

Remplir la grille ne suffit pas : la deduction doit retrouver EXACTEMENT la
solution d'origine. Une technique fausse remplit ET se trompe, et rien dans
les journaux ne le signalerait.

C'est ce canari qui aurait attrape le bug T1 (hidden single applique a des
regions qui n'exigent pas la presence de chaque valeur).

Couvre T0, T1 et T2. Toute nouvelle technique doit etre ajoutee ICI avant
d'etre activee : une technique fausse remplit la grille et rend une solution
FAUSSE, ce qu'aucun autre canari ne verrait.

--------------------------------------------------------------------------
PARTIE 2 : LES PROPAGATEURS DE DOMAINES (projet A).

POURQUOI ICI ET PAS DANS UN canary9 SEPARE. Ce que ce canari verifie -- la
deduction retrouve EXACTEMENT la solution d'origine -- est une propriete du
SYSTEME DE DEDUCTION ENTIER, pas de chaque technique prise isolement. Un
propagateur AllDiff correct et un propagateur Count correct peuvent, ENSEMBLE,
retirer un candidat de trop : l'erreur nait de l'interaction. Un canari par
propagateur ne verrait jamais ca.

Donc ce fichier grossit a chaque propagateur, et chaque ajout tourne avec TOUS
les precedents actifs. Le cout monte, c'est voulu : c'est exactement la
combinatoire qu'on veut couvrir.

DEUX CONSEQUENCES :
  - l'ordre d'ajout des propagateurs n'est pas seulement une progression de
    difficulte, c'est un ORDRE DE VALIDATION INCREMENTALE. Un canary3 rouge au
    sixieme propagateur peut accuser le sixieme comme n'importe quel couple
    anterieur ;
  - si ce canari devient trop lent pour tourner a chaque run, on le sortira de
    `run_canaries` vers un pre-commit. On ne reduira JAMAIS sa couverture pour
    gagner du temps.

Sortie non nulle = au moins une divergence = le moteur ment.
"""
import itertools
import random
import sys

from rulesearch import *
from dsl2 import *
from deduction import apply_T0, apply_T1, apply_T2, t1_regions
from propagate import domaines, domaines_contiennent, propager, propager_alldiff

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

echecs = 0

print("== PARTIE 1 : hierarchie de deduction T0/T1/T2 ==")
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
    print("ECHEC : la deduction ne retrouve pas la solution d'origine.")
    echecs += 1
else:
    print("OK : aucune divergence.")


# ==========================================================================
# PARTIE 2 : PROPAGATEURS DE DOMAINES
# ==========================================================================
#
# Invariant 8 : LES CAS LIMITES SONT CONSTRUITS A LA MAIN. Le generateur ne
# produit `AllDiff` que sur des regions de taille n avec d >= n : il ne
# fabriquera JAMAIS spontanement |R| < d ni |R| > d, qui sont precisement les
# deux configurations dangereuses.
#
# La verite de reference n'est pas `feasible()` seule mais l'ENUMERATION
# EXHAUSTIVE des solutions. Sur les grilles minuscules construites ici, elle
# est calculable en entier.

def toutes_solutions(rs, plafond=200000):
    """Enumeration exhaustive par backtracking sur `feasible()`. Rend la liste
    complete des solutions, ou None si le plafond est atteint (auquel cas le
    cas de test est trop gros et doit etre reduit, pas contourne)."""
    N = rs.n * rs.n
    g = [UNASSIGNED] * N
    out = []

    def rec(i):
        if len(out) > plafond:
            return False
        if i == N:
            out.append(list(g))
            return True
        for v in range(rs.d):
            g[i] = v
            if rs.feasible(g, changed=i):
                if not rec(i + 1):
                    g[i] = UNASSIGNED
                    return False
            g[i] = UNASSIGNED
        return True

    return out if rec(0) else None


def indices(sol, k, rnd):
    """Grille partielle : k cellules d'une solution reelle, le reste inconnu."""
    N = len(sol)
    pris = rnd.sample(range(N), k)
    return [sol[i] if i in set(pris) else UNASSIGNED for i in range(N)]


def cas_surete(nom, rs, prop=None, verbeux=True):
    """LE test qui compte contre le risque asymetrique : sur toute grille
    partielle extraite d'une solution reelle, la propagation ne doit JAMAIS
    retirer une valeur de cette solution.

    `prop` permet d'injecter un propagateur alternatif (utilise par le test
    negatif). Par defaut, le propagateur de production."""
    fonction = prop or propager
    sols = toutes_solutions(rs)
    if sols is None:
        print("  %-22s INDETERMINE : enumeration au-dela du plafond" % nom)
        return None
    if not sols:
        if verbeux:
            print("  %-22s 0 solution (systeme mort) -- surete vide" % nom)
        return 0
    rnd = random.Random(101)
    viol = essais = 0
    for sol in sols[:60]:
        for k in (0, 1, 2, 3, len(sol) // 2):
            essais += 1
            dom = domaines(rs, indices(sol, k, rnd))
            _, contra = fonction(rs, dom)
            if contra or not domaines_contiennent(dom, sol):
                viol += 1
    if verbeux:
        print("  %-22s solutions=%-5d essais=%-4d VIOLATIONS=%d"
              % (nom, len(sols), essais, viol))
    return viol


print()
print("== PARTIE 2 : propagateurs de domaines ==")
print()
print("-- AllDiff : les trois tailles de region, construites a la main --")

# Cas A : |R| == d. Cas nominal (carre latin 3x3). Chaque valeur apparait
# exactement une fois -- un propagateur correct ICI ne prouve rien ailleurs.
casA = RuleSystem(3, 3, [AllDiff(R) for R in rows(3) + cols(3)], "A|R|=d")

# Cas B : |R| > d. INFAISABLE par principe des tiroirs (3 cellules, 2 valeurs,
# toutes distinctes). Le propagateur doit ne jamais rien affirmer de faux ;
# il n'est PAS tenu de detecter l'infaisabilite -- voir la mesure plus bas.
casB = RuleSystem(3, 2, [AllDiff(rows(3)[0])], "B|R|>d")

# Cas C : LE VRAI PIEGE. |R| < d : satisfaisable, mais aucun raisonnement
# « chaque valeur doit apparaitre » n'y est valide. C'est exactement la
# configuration ou T1 s'etait trompe.
casC = RuleSystem(2, 4, [AllDiff([0, 1])], "C|R|<d")

for nom, rs in (("A |R| == d", casA), ("B |R| > d", casB), ("C |R| < d", casC)):
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

# Le propagateur doit aussi rester sur des systemes reels du generateur, en
# interaction avec les autres contraintes (qui n'ont pas encore de
# propagateur, donc sont ignorees -- ce qui est correct, pas complet).
print()
print("-- AllDiff sur les systemes de la partie 1 --")
for name, rs in tests:
    if not any(getattr(c, "kind", None) == "ALLDIFF" for c in rs.constraints):
        continue
    rnd = random.Random(7)
    viol = essais = 0
    for _ in range(15):
        sol = random_solution(rs)
        if sol is None:
            continue
        for k in (2, 5, 9):
            essais += 1
            dom = domaines(rs, indices(sol, k, rnd))
            _, contra = propager(rs, dom)
            if contra or not domaines_contiennent(dom, sol):
                viol += 1
    print("  %-22s essais=%-4d VIOLATIONS=%d" % (name, essais, viol))
    if viol:
        echecs += 1


# ---- MESURE (invariant : constater, ne pas supposer) ---------------------
# Sur |R| > d le systeme est mort. Le retrait simple atteint-il la
# contradiction par saturation ? On MESURE, on ne tranche pas a priori, et on
# n'ajoute AUCUNE regle pour y arriver : `feasible()` detecte deja ce cas et
# reste l'oracle. Un propagateur qui laisse passer une infaisabilite est
# INCOMPLET, pas faux -- c'est la moitie correcte du compromis.
dom = domaines(casB, [UNASSIGNED] * 9)
_, contra = propager(casB, dom)
print()
print("-- mesure : contradiction detectee sur |R| > d (grille vide) ? %s --"
      % ("OUI" if contra else "NON (incomplet, correct)"))
dom = domaines(casB, [0, UNASSIGNED, UNASSIGNED] + [UNASSIGNED] * 6)
_, contra1 = propager(casB, dom)
print("-- mesure : idem avec un indice pose ? %s --"
      % ("OUI" if contra1 else "NON (incomplet, correct)"))


# ---- TEST NEGATIF OBLIGATOIRE (invariant 9) ------------------------------
# Un canari doit avoir ete VU echouer au moins une fois. On injecte ici un
# AllDiff TROP ZELE : celui qui ajoute le hidden single non conditionne --
# « la valeur v ne peut aller que dans cette cellule de la region, donc elle y
# va ». C'est EXACTEMENT le bug T1, reecrit dans le langage des domaines.
# Valide quand |R| == d ; FAUX des que |R| < d, ou rien n'oblige v a apparaitre.

def _alldiff_trop_zele(cn, dom):
    prog, contra = propager_alldiff(cn, dom)
    if contra:
        return prog, True
    vals = set()
    for i in cn.region:
        vals |= dom[i]
    for v in vals:
        ou = [i for i in cn.region if v in dom[i]]
        # LE BUG DELIBERE : aucune verification que la region exige la
        # presence de chaque valeur.
        if len(ou) == 1 and dom[ou[0]] != {v}:
            dom[ou[0]] = {v}
            prog = True
    return prog, False


def _propager_zele(rs, dom):
    while True:
        prog = False
        for cn in rs.constraints:
            if getattr(cn, "kind", None) != "ALLDIFF":
                continue
            p, contra = _alldiff_trop_zele(cn, dom)
            prog = prog or p
            if contra:
                return True, True
        if not prog:
            return True, False


print()
print("-- test negatif : un AllDiff trop zele doit etre REJETE --")
detecte = False
for nom, rs in (("A |R| == d", casA), ("C |R| < d", casC)):
    v = cas_surete("zele " + nom, rs, prop=_propager_zele)
    if v:
        detecte = True
if detecte:
    print("  OK : le canari mord -- la version trop zelee est rejetee.")
else:
    print("  ECHEC : un propagateur FAUX passe le canari. Il ne verifie rien.")
    echecs += 1


print()
if echecs:
    print("ECHEC : %d section(s) en defaut." % echecs)
    sys.exit(1)
print("OK : aucune divergence, aucune violation de surete.")
