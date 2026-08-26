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
from propagate import (domaines, domaines_contiennent, propager,
                       propager_alldiff, propager_count,
                       propager_count_interdiction,
                       propager_count_forcage, propager_sum,
                       propager_sum_plafond, propager_sum_plancher,
                       PROPAGATEURS)

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


# ==========================================================================
# Count -- DEUX SENS dans le meme commit, parce que le test negatif les
# distingue SEPAREMENT. Chacun a son bug injecte, chacun est vu mordre.
# ==========================================================================
#
# Cas construits a la main : le generateur ne produit `Count` qu'avec des
# bornes tirees au hasard, il ne garantit ni `lo == hi`, ni `lo == 0`.

# D : lo == hi. Comptage exact -- les deux sens s'appliquent et coincident
#     avec toute confusion lo/hi. Un propagateur correct ICI ne prouve rien.
casD = RuleSystem(2, 2, [Count([0, 1, 2, 3], 1, 2, 2)], "D lo=hi")

# E : lo < hi. Intervalle lache : c'est la que confondre lo et hi devient FAUX.
casE = RuleSystem(2, 2, [Count([0, 1, 2, 3], 1, 1, 3)], "E lo<hi")

# F : lo == 0. LE PIEGE, analogue de |R| < d pour AllDiff : la contrainte
#     autorise ZERO occurrence, donc aucun raisonnement « une cellule doit
#     valoir val » n'y est valide.
casF = RuleSystem(2, 2, [Count([0, 1, 2, 3], 1, 0, 2)], "F lo=0")

print()
print("-- Count : surete sur les trois formes de bornes --")
for nom, rs in (("D lo == hi", casD), ("E lo < hi", casE), ("F lo == 0", casF)):
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1


# ---- LES DEUX SENS DOIVENT SE DECLENCHER -------------------------------
# Un propagateur correct et JAMAIS INVOQUE est le motif du projet : deux
# techniques de deduction ont deja ete ecrites, verifiees, et retirees pour
# cette raison. On le constate ici avant d'y revenir dans six mois.

def _declenchements(rs):
    rnd2 = random.Random(31)
    sols = toutes_solutions(rs) or []
    ci = cf = 0
    for sol in sols[:60]:
        for k in (0, 1, 2, 3):
            dom = domaines(rs, indices(sol, k, rnd2))
            for _ in range(20):
                prog = False
                arret = False
                for cn in rs.constraints:
                    if getattr(cn, "kind", None) != "COUNT":
                        continue
                    pi, c = propager_count_interdiction(cn, dom)
                    if pi:
                        ci += 1
                        prog = True
                    if c:
                        arret = True
                        break
                    pf, c = propager_count_forcage(cn, dom)
                    if pf:
                        cf += 1
                        prog = True
                    if c:
                        arret = True
                        break
                if arret or not prog:
                    break
    return ci, cf

print()
print("-- Count : chaque sens doit etre INVOQUE au moins une fois --")
tot_i = tot_f = 0
for nom, rs in (("D lo == hi", casD), ("E lo < hi", casE), ("F lo == 0", casF)):
    ci, cf = _declenchements(rs)
    tot_i += ci
    tot_f += cf
    print("  %-22s interdiction=%-4d forcage=%-4d" % (nom, ci, cf))
if not tot_i:
    print("  ECHEC : le sens INTERDICTION n'est jamais invoque -- il est inerte.")
    echecs += 1
if not tot_f:
    print("  ECHEC : le sens FORCAGE n'est jamais invoque -- il est inerte.")
    echecs += 1
if tot_i and tot_f:
    print("  OK : les deux sens sont operants.")


# ---- TEST NEGATIF, UN PAR SENS -----------------------------------------
# La condition posee pour mettre les deux sens dans le meme commit : le canari
# doit les rejeter SEPAREMENT. Le bug injecte est le meme dans les deux cas --
# confondre `lo` et `hi` -- ce qui est l'erreur naturelle sur une contrainte a
# deux bornes, et il est faux exactement quand `lo < hi`.

def _interdiction_zele(cn, dom):
    """BUG : declenche sur `lo` au lieu de `hi`."""
    sur, poss = [], []
    for i in cn.region:
        if cn.val in dom[i]:
            poss.append(i)
            if len(dom[i]) == 1:
                sur.append(i)
    if len(sur) != cn.lo:
        return False, False
    prog = False
    certains = set(sur)
    for i in poss:
        if i in certains:
            continue
        dom[i].discard(cn.val)
        prog = True
        if not dom[i]:
            return prog, True
    return prog, False


def _forcage_zele(cn, dom):
    """BUG : declenche sur `hi` au lieu de `lo`."""
    poss = [i for i in cn.region if cn.val in dom[i]]
    if len(poss) != cn.hi:
        return False, False
    prog = False
    for i in poss:
        if dom[i] != {cn.val}:
            dom[i].clear()
            dom[i].add(cn.val)
            prog = True
    return prog, False


def _fabrique(sens_i, sens_f):
    """Propagateur complet ou UN seul sens est remplace par sa version fausse.
    L'autre reste correct : une violation est donc imputable au sens injecte."""
    def _p(rs, dom):
        for _ in range(50):
            prog = False
            for cn in rs.constraints:
                if getattr(cn, "kind", None) != "COUNT":
                    continue
                pi, c = sens_i(cn, dom)
                if c:
                    return True, True
                pf, c = sens_f(cn, dom)
                if c:
                    return True, True
                prog = prog or pi or pf
            if not prog:
                break
        return True, False
    return _p

print()
print("-- test negatif Count : chaque sens rejete SEPAREMENT --")
for etiquette, faux in (
        ("INTERDICTION zelee", _fabrique(_interdiction_zele, propager_count_forcage)),
        ("FORCAGE zele", _fabrique(propager_count_interdiction, _forcage_zele))):
    detecte = False
    for nom, rs in (("D lo == hi", casD), ("E lo < hi", casE), ("F lo == 0", casF)):
        v = cas_surete("%s / %s" % (etiquette[:12], nom), rs, prop=faux)
        if v:
            detecte = True
    if detecte:
        print("  OK : %s est rejetee." % etiquette)
    else:
        print("  ECHEC : %s passe le canari. Le sens n'est pas couvert." % etiquette)
        echecs += 1


# ==========================================================================
# SumRange -- meme famille de bornes que Count, donc meme gabarit a deux sens.
# ==========================================================================

# G : lo == hi. Somme exacte -- les deux sens mordent au maximum.
casG = RuleSystem(2, 3, [SumRange([0, 1, 2, 3], 4, 4, 3)], "G lo=hi")
# H : lo < hi. Intervalle lache.
casH = RuleSystem(2, 3, [SumRange([0, 1, 2, 3], 3, 5, 3)], "H lo<hi")
# I : bornes VACUOUS -- [0, |R|*(d-1)] est toujours satisfait. LE PIEGE :
#     aucun retrait n'y est jamais justifie. Analogue de lo == 0 pour Count.
casI = RuleSystem(2, 3, [SumRange([0, 1, 2, 3], 0, 8, 3)], "I vacuous")

print()
print("-- SumRange : surete sur les trois formes de bornes --")
for nom, rs in (("G lo == hi", casG), ("H lo < hi", casH), ("I vacuous", casI)):
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- SumRange : chaque sens doit etre INVOQUE au moins une fois --")


def _declenchements_sum(rs):
    rnd2 = random.Random(37)
    sols = toutes_solutions(rs) or []
    cp = cq = 0
    for sol in sols[:60]:
        for k in (0, 1, 2, 3):
            dom = domaines(rs, indices(sol, k, rnd2))
            for _ in range(20):
                prog = arret = False
                for cn in rs.constraints:
                    if getattr(cn, "kind", None) != "SUM":
                        continue
                    pa, c = propager_sum_plafond(cn, dom)
                    if pa:
                        cp += 1
                        prog = True
                    if c:
                        arret = True
                        break
                    pb, c = propager_sum_plancher(cn, dom)
                    if pb:
                        cq += 1
                        prog = True
                    if c:
                        arret = True
                        break
                if arret or not prog:
                    break
    return cp, cq


tot_p = tot_q = 0
for nom, rs in (("G lo == hi", casG), ("H lo < hi", casH), ("I vacuous", casI)):
    cp, cq = _declenchements_sum(rs)
    tot_p += cp
    tot_q += cq
    print("  %-22s plafond=%-4d plancher=%-4d" % (nom, cp, cq))
if not tot_p:
    print("  ECHEC : le sens PLAFOND est inerte.")
    echecs += 1
if not tot_q:
    print("  ECHEC : le sens PLANCHER est inerte.")
    echecs += 1
if tot_p and tot_q:
    print("  OK : les deux sens sont operants.")


# ---- test negatif, un par sens -----------------------------------------
# Bug injecte : intervertir min et max dans le calcul du reste. C'est l'erreur
# classique de la coherence aux bornes, et elle est fausse des que les domaines
# ne sont pas tous des singletons.

def _sum_plafond_zele(cn, dom):
    """BUG : borne le reste par son MAXIMUM au lieu de son minimum."""
    if any(not dom[i] for i in cn.region):
        return False, True
    mx = [max(dom[i]) for i in cn.region]
    total_max = sum(mx)
    prog = False
    for k, i in enumerate(cn.region):
        plafond = cn.hi - (total_max - mx[k])
        trop = [v for v in dom[i] if v > plafond]
        if trop:
            for v in trop:
                dom[i].discard(v)
            prog = True
            if not dom[i]:
                return prog, True
    return prog, False


def _sum_plancher_zele(cn, dom):
    """BUG : borne le reste par son MINIMUM au lieu de son maximum."""
    if any(not dom[i] for i in cn.region):
        return False, True
    mn = [min(dom[i]) for i in cn.region]
    total_min = sum(mn)
    prog = False
    for k, i in enumerate(cn.region):
        plancher = cn.lo - (total_min - mn[k])
        trop = [v for v in dom[i] if v < plancher]
        if trop:
            for v in trop:
                dom[i].discard(v)
            prog = True
            if not dom[i]:
                return prog, True
    return prog, False


def _fabrique_sum(sens_p, sens_q):
    def _p(rs, dom):
        for _ in range(50):
            prog = False
            for cn in rs.constraints:
                if getattr(cn, "kind", None) != "SUM":
                    continue
                pa, c = sens_p(cn, dom)
                if c:
                    return True, True
                pb, c = sens_q(cn, dom)
                if c:
                    return True, True
                prog = prog or pa or pb
            if not prog:
                break
        return True, False
    return _p


print()
print("-- test negatif SumRange : chaque sens rejete SEPAREMENT --")
for etiquette, faux in (
        ("PLAFOND zele", _fabrique_sum(_sum_plafond_zele, propager_sum_plancher)),
        ("PLANCHER zele", _fabrique_sum(propager_sum_plafond, _sum_plancher_zele))):
    detecte = False
    for nom, rs in (("G lo == hi", casG), ("H lo < hi", casH), ("I vacuous", casI)):
        v = cas_surete("%s / %s" % (etiquette[:9], nom), rs, prop=faux)
        if v:
            detecte = True
    if detecte:
        print("  OK : %s est rejete." % etiquette)
    else:
        print("  ECHEC : %s passe le canari." % etiquette)
        echecs += 1


# ==========================================================================
# CROISEMENTS DE PROPAGATEURS -- construits a la main, contre le generateur.
# ==========================================================================
#
# Les cas limites sont a la main, mais leurs CROISEMENTS venaient jusqu'ici du
# generateur, qui n'assemble que les paires que les familles du DSL produisent
# naturellement. Avec dix propagateurs il y aura 45 paires ; le generateur
# n'en couvrira qu'une fraction. C'est exactement la faiblesse de couverture
# payee avec T1.
#
# Donc : pour chaque paire de propagateurs branches, un systeme portant les
# DEUX contraintes dans leur configuration limite respective, sur des regions
# QUI SE CHEVAUCHENT.
#
# LE CHEVAUCHEMENT EST LE POINT. Deux propagateurs sur des regions disjointes
# ne peuvent pas interagir : c'est le partage de cellules qui cree le risque
# qu'un retrait de l'un rende l'autre trop zele. Le systeme X3 ci-dessous est
# le TEMOIN disjoint, et il doit rester muet la ou X2 crie.
#
# Le cout est quadratique en nombre de propagateurs. C'est assume : c'est la
# seule couverture qui ne depende pas du generateur.

# X1 : la paire limite nommee -- AllDiff |R| < d croise Count lo == 0,
#      partageant la cellule 1.
croiX1 = RuleSystem(2, 3, [AllDiff([0, 1]),
                           Count([1, 2], 1, 0, 1)], "X1 |R|<d x lo=0")

# X2 : meme AllDiff limite, Count avec lo == 1. C'est ici que le forcage peut
#      se declencher, donc ici que le bug d'interaction peut mordre.
croiX2 = RuleSystem(2, 3, [AllDiff([0, 1]),
                           Count([1, 2], 1, 1, 2)], "X2 |R|<d x lo=1")

# X3 : TEMOIN. Identique a X2, regions DISJOINTES. Doit rester muet.
croiX3 = RuleSystem(2, 3, [AllDiff([0, 1]),
                           Count([2, 3], 1, 1, 2)], "X3 disjoint")

CROISEMENTS = (("X1 |R|<d x lo=0 (chevauche)", croiX1),
               ("X2 |R|<d x lo=1 (chevauche)", croiX2),
               ("X3 meme paire, DISJOINT", croiX3))


def croisement_surete(nom, rs, prop=None, verbeux=True):
    """Surete par enumeration EXHAUSTIVE : toutes les solutions croisees avec
    tous les sous-ensembles d'indices possibles. Les grilles de croisement sont
    minuscules exprès pour que ce soit calculable en entier -- un echantillon
    aleatoire raterait precisement la configuration rare qui declenche
    l'interaction."""
    fonction = prop or propager
    sols = toutes_solutions(rs)
    if sols is None:
        print("  %-30s INDETERMINE : au-dela du plafond" % nom)
        return None
    N = rs.n * rs.n
    viol = essais = 0
    for sol in sols:
        for taille in range(N + 1):
            for pris in itertools.combinations(range(N), taille):
                essais += 1
                g = [sol[i] if i in pris else UNASSIGNED for i in range(N)]
                dom = domaines(rs, g)
                _, contra = fonction(rs, dom)
                if contra or not domaines_contiennent(dom, sol):
                    viol += 1
    if verbeux:
        print("  %-30s solutions=%-4d essais=%-5d VIOLATIONS=%d"
              % (nom, len(sols), essais, viol))
    return viol


print()
print("-- croisements AllDiff x Count : surete --")
for nom, rs in CROISEMENTS:
    v = croisement_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1


# ---- TEST NEGATIF D'INTERACTION ----------------------------------------
#
# Il doit s'agir d'un bug D'INTERACTION, pas de la reinjection d'un bug simple.
#
# CE QUI NE MARCHE PAS, ET POURQUOI -- resultat negatif, consigne ici parce
# qu'il vaut mieux qu'une case vide. Le candidat naturel etait le CACHE PERIME
# (un propagateur lit l'etat d'une cellule et ne le relit pas apres qu'un autre
# l'ait reduite). Il est **structurellement inerte** ici : les domaines ne font
# que RETRECIR, et les deux declencheurs de Count sont des egalites sur des
# quantites monotones (`|sur|` croit, `|poss| decroit`). Une lecture perimee
# donne donc toujours un `sur` plus PETIT et un `poss` plus GRAND que la
# realite -- c'est-a-dire un propagateur plus FAIBLE, jamais plus zele. Un
# cache perime produirait ici une deduction manquee, pas une solution fausse.
#
# CE QUI MARCHE : le bug d'interaction reel a cette frontiere est l'hypothese
# implicite qu'un domaine est PLEIN OU SINGLETON -- vrai dans le monde du
# forward-checking d'ou l'on vient, faux des qu'un autre propagateur a rogne
# PARTIELLEMENT une cellule partagee. C'est le piege conceptuel propre a
# l'introduction des domaines, et il exige le chevauchement.

def _fabrique_croise_bugue(d):
    def _count_bugue(cn, dom):
        sur = [i for i in cn.region if len(dom[i]) == 1 and cn.val in dom[i]]
        # LE BUG : « une cellule peut valoir val si elle est intacte (domaine
        # plein) ou deja fixee a val ». Sous-estime `poss` des qu'une cellule
        # partagee a ete rognee partiellement par AllDiff.
        poss = [i for i in cn.region
                if dom[i] == {cn.val} or len(dom[i]) == d]
        prog = False
        if len(sur) == cn.hi:
            certains = set(sur)
            for i in cn.region:
                if i not in certains and cn.val in dom[i]:
                    dom[i].discard(cn.val)
                    prog = True
                    if not dom[i]:
                        return prog, True
        if len(poss) == cn.lo:
            for i in poss:
                if dom[i] != {cn.val}:
                    dom[i].clear()
                    dom[i].add(cn.val)
                    prog = True
        return prog, False

    def _p(rs, dom):
        for _ in range(50):
            prog = False
            for cn in rs.constraints:
                k = getattr(cn, "kind", None)
                if k == "ALLDIFF":
                    pa, c = propager_alldiff(cn, dom)
                    if c:
                        return True, True
                    prog = prog or pa
                elif k == "COUNT":
                    pc, c = _count_bugue(cn, dom)
                    if c:
                        return True, True
                    prog = prog or pc
            if not prog:
                break
        return True, False
    return _p


print()
print("-- test negatif d'INTERACTION : hypothese « plein ou singleton » --")
viols = {}
for nom, rs in CROISEMENTS:
    viols[nom] = croisement_surete("bug " + nom, rs,
                                   prop=_fabrique_croise_bugue(rs.d))

nom_chevauche = "X2 |R|<d x lo=1 (chevauche)"
nom_temoin = "X3 meme paire, DISJOINT"
if not viols.get(nom_chevauche):
    print("  ECHEC : le bug d'interaction n'est pas detecte sur le croisement "
          "qui chevauche. Le croisement ne couvre rien.")
    echecs += 1
elif viols.get(nom_temoin):
    print("  ECHEC : le TEMOIN disjoint crie aussi -- ce n'est donc pas une "
          "interaction mais un bug simple, et le croisement ne prouve rien.")
    echecs += 1
else:
    print("  OK : le bug mord sur le croisement qui CHEVAUCHE (%d violations) "
          "et le temoin DISJOINT reste muet (%d)."
          % (viols[nom_chevauche], viols[nom_temoin]))
    print("  Le chevauchement est bien le mecanisme, pas un decor.")


# ---- paires impliquant SumRange (invariant 13 : contre TOUS les precedents)

def _moteur(remplacants):
    """Propagateur complet ou seuls les `kind` listes sont remplaces par une
    version fausse. Les autres gardent leur propagateur de production : une
    violation est donc imputable au remplacant."""
    def _p(rs, dom):
        for _ in range(60):
            prog = False
            for cn in rs.constraints:
                k = getattr(cn, "kind", None)
                f = remplacants.get(k) or PROPAGATEURS.get(k)
                if f is None:
                    continue
                pp, c = f(cn, dom)
                if c:
                    return True, True
                prog = prog or pp
            if not prog:
                break
        return True, False
    return _p


def _sum_bugue_forme(d):
    """BUG D'INTERACTION, meme classe que celui de Count : deduire le CONTENU
    d'un domaine de sa FORME. Ici, « un domaine deja rogne est une cellule
    decidee », donc on le borne par son minimum -- confusion entre CONTRAINTE
    et DETERMINEE. Sous-estime le maximum atteignable du reste, donc releve le
    plancher a tort. Exige qu'un domaine ait ete rogne PARTIELLEMENT."""
    def f(cn, dom):
        if any(not dom[i] for i in cn.region):
            return False, True
        prog, c = propager_sum_plafond(cn, dom)   # ce sens reste correct
        if c:
            return True, True
        if any(not dom[i] for i in cn.region):
            return True, True
        mx = [min(dom[i]) if 1 < len(dom[i]) < d else max(dom[i])
              for i in cn.region]
        total_max = sum(mx)
        for k, i in enumerate(cn.region):
            plancher = cn.lo - (total_max - mx[k])
            trop = [v for v in dom[i] if v < plancher]
            if trop:
                for v in trop:
                    dom[i].discard(v)
                prog = True
                if not dom[i]:
                    return prog, True
        return prog, False
    return f


def _paire(titre, rs_chev, rs_disj, bug):
    """Un croisement complet : surete des deux cotes, puis le bug injecte, qui
    doit mordre sur le CHEVAUCHANT et rester muet sur le TEMOIN disjoint."""
    print()
    print("-- croisement %s --" % titre)
    faute = 0
    for etiq, rs in (("surete chevauche", rs_chev), ("surete disjoint ", rs_disj)):
        v = croisement_surete("  " + etiq, rs)
        if v is None or v > 0:
            faute += 1
    vc = croisement_surete("  bug chevauche  ", rs_chev, prop=bug)
    vd = croisement_surete("  bug disjoint   ", rs_disj, prop=bug)
    if not vc:
        print("  ECHEC : le bug d'interaction ne mord pas sur le chevauchant.")
        faute += 1
    elif vd:
        print("  ECHEC : le TEMOIN disjoint crie aussi (%d) -- bug simple, pas "
              "interaction. Le croisement ne prouve rien." % vd)
        faute += 1
    else:
        print("  OK : mord sur le chevauchant (%d), temoin disjoint muet (%d)."
              % (vc, vd))
    return faute


echecs += _paire(
    "AllDiff |R|<d  x  SumRange",
    RuleSystem(2, 3, [AllDiff([0, 1]), SumRange([1, 2], 2, 4, 3)], "P3c"),
    RuleSystem(2, 3, [AllDiff([0, 1]), SumRange([2, 3], 2, 4, 3)], "P3d"),
    _moteur({"SUM": _sum_bugue_forme(3)}))

# Count doit ici avoir `hi < |R|`. Avec `hi == |R|` le sens INTERDICTION ne
# peut RIEN retirer a l'interieur de sa propre region -- il ne se declenche que
# lorsque toutes les cellules valent deja `val` -- donc Count ne peut pas
# fabriquer le domaine PARTIELLEMENT rogne dont le bug a besoin. Constate en
# faisant echouer ce croisement : c'est la meme lecon que X1. Une paire de
# configurations limites n'est pas automatiquement une paire ou l'interaction
# est observable ; il faut verifier que l'un des deux peut effectivement
# ROGNER une cellule partagee.
echecs += _paire(
    "Count lo=hi=1  x  SumRange",
    RuleSystem(2, 3, [Count([0, 1], 1, 1, 1), SumRange([1, 2], 2, 4, 3)], "P4c"),
    RuleSystem(2, 3, [Count([0, 1], 1, 1, 1), SumRange([2, 3], 2, 4, 3)], "P4d"),
    _moteur({"SUM": _sum_bugue_forme(3)}))


print()
if echecs:
    print("ECHEC : %d section(s) en defaut." % echecs)
    sys.exit(1)
print("OK : aucune divergence, aucune violation de surete.")
