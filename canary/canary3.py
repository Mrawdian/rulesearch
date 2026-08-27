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
                       propager_neqadj, propager_mono,
                       propager_mono_avant, propager_mono_arriere,
                       propager_pairdiff, propager_pairstep,
                       propager_notriple, propager_nosquare,
                       propager_connected,
                       objet_inference, statut_objet,
                       SURETE_OBJET_INDUIT,
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


def echantillon(sols, combien, graine=20260826):
    """UN PREFIXE D'ENUMERATION LEXICOGRAPHIQUE N'EST PAS UN ECHANTILLON.

    `toutes_solutions` enumere dans l'ordre lexicographique : ses premiers
    elements partagent tous les memes petites valeurs en tete de grille.
    Prendre `sols[:k]` echantillonne donc un COIN de l'espace, pas l'espace.

    Constate le 26/08/2026 : les sept croisements de `NoTriple` rendaient ZERO
    violation sous un bug qui, sur un tirage ALEATOIRE de meme taille, en
    produit des centaines. Le canari avait l'air de couvrir et ne couvrait
    rien -- le motif du projet, applique cette fois a l'echantillonnage.

    Tirage a graine fixe : reproductible, et non aligne sur l'ordre
    d'enumeration.
    """
    if combien is None or combien >= len(sols):
        return sols
    return random.Random(graine).sample(sols, combien)


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
    for sol in echantillon(sols, 60):
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


def _moteur_simple(remplacants):
    """Propagateur complet ou seuls les `kind` listes sont remplaces par une
    version fausse ; les autres gardent leur propagateur de production. Une
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
    for sol in echantillon(sols, 60):
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
    for sol in echantillon(sols, 60):
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
# NeqAdj -- une seule regle, et LE PIEGE est que ce n'est PAS un AllDiff.
# ==========================================================================

# J : region de 2 -- degenere, NeqAdj y coincide avec AllDiff.
casJ = RuleSystem(2, 3, [NeqAdj([0, 1])], "J |R|=2")
# K : region de 3 -- LE PIEGE. Les extremites peuvent etre EGALES. Tout
#     propagateur qui traite la region comme un AllDiff est faux ici.
casK = RuleSystem(2, 3, [NeqAdj([0, 1, 2])], "K |R|=3")
# L : region de 3 avec d = 2 -- l'alternance est forcee, cas le plus tendu.
casL = RuleSystem(2, 2, [NeqAdj([0, 1, 2])], "L |R|=3, d=2")

print()
print("-- NeqAdj : surete --")
for nom, rs in (("J |R| = 2", casJ), ("K |R| = 3", casK), ("L |R|=3, d=2", casL)):
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- NeqAdj : la regle doit etre INVOQUEE --")
_inv = 0
for nom, rs in (("J", casJ), ("K", casK), ("L", casL)):
    rnd3 = random.Random(41)
    for sol in echantillon(toutes_solutions(rs) or [], 40):
        for k in (1, 2):
            dom = domaines(rs, indices(sol, k, rnd3))
            for cn in rs.constraints:
                if getattr(cn, "kind", None) == "NEQADJ":
                    pp, _ = propager_neqadj(cn, dom)
                    if pp:
                        _inv += 1
print("  declenchements = %d" % _inv)
if not _inv:
    print("  ECHEC : NeqAdj est inerte.")
    echecs += 1
else:
    print("  OK : la regle est operante.")


# ---- test negatif : NeqAdj traite comme un AllDiff ----------------------
# C'est le bug T1 sous un troisieme habit : appliquer a toute la region un
# raisonnement qui n'est valide qu'entre voisines immediates.

def _neqadj_zele(cn, dom):
    R = cn.region
    prog = False
    for a in R:
        if len(dom[a]) != 1:
            continue
        v = next(iter(dom[a]))
        for b in R:                      # LE BUG : toute la region, pas les voisines
            if b == a or v not in dom[b]:
                continue
            dom[b].discard(v)
            prog = True
            if not dom[b]:
                return prog, True
    return prog, False


print()
print("-- test negatif NeqAdj : traite comme un AllDiff --")
_det = False
for nom, rs in (("J |R| = 2", casJ), ("K |R| = 3", casK), ("L |R|=3, d=2", casL)):
    v = cas_surete("zele " + nom, rs, prop=_moteur_simple({"NEQADJ": _neqadj_zele}))
    if v:
        _det = True
if _det:
    print("  OK : le canari mord.")
else:
    print("  ECHEC : NeqAdj traite comme un AllDiff passe le canari.")
    echecs += 1


# ==========================================================================
# Mono -- deux sens, et AUCUNE lecture de forme : sur par construction.
# ==========================================================================

# M : |R| = 2 -- une seule paire, pas de propagation de proche en proche.
casM = RuleSystem(2, 3, [Mono([0, 1])], "M |R|=2")
# N : |R| = 3 -- LE POINT : une seule passe ne suffit pas, la contrainte se
#     propage de proche en proche. C'est le point fixe qui fait le travail.
casN = RuleSystem(2, 3, [Mono([0, 1, 2])], "N |R|=3")
# O : |R| = 4, d = 2 -- cas le plus tendu, la suite est presque constante.
casO = RuleSystem(2, 2, [Mono([0, 1, 2, 3])], "O |R|=4, d=2")

print()
print("-- Mono : surete --")
for nom, rs in (("M |R| = 2", casM), ("N |R| = 3", casN), ("O |R|=4, d=2", casO)):
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- Mono : chaque sens doit etre INVOQUE au moins une fois --")


def _declenchements_mono(rs):
    rnd4 = random.Random(43)
    sols = toutes_solutions(rs) or []
    ca = cb = 0
    for sol in echantillon(sols, 60):
        for k in (1, 2):
            dom = domaines(rs, indices(sol, k, rnd4))
            for _ in range(20):
                prog = arret = False
                for cn in rs.constraints:
                    if getattr(cn, "kind", None) != "MONO":
                        continue
                    pa, c = propager_mono_avant(cn, dom)
                    if pa:
                        ca += 1
                        prog = True
                    if c:
                        arret = True
                        break
                    pb, c = propager_mono_arriere(cn, dom)
                    if pb:
                        cb += 1
                        prog = True
                    if c:
                        arret = True
                        break
                if arret or not prog:
                    break
    return ca, cb


tot_a = tot_b = 0
for nom, rs in (("M |R| = 2", casM), ("N |R| = 3", casN), ("O |R|=4, d=2", casO)):
    ca, cb = _declenchements_mono(rs)
    tot_a += ca
    tot_b += cb
    print("  %-22s avant=%-4d arriere=%-4d" % (nom, ca, cb))
if not tot_a:
    print("  ECHEC : le sens AVANT est inerte.")
    echecs += 1
if not tot_b:
    print("  ECHEC : le sens ARRIERE est inerte.")
    echecs += 1
if tot_a and tot_b:
    print("  OK : les deux sens sont operants.")


# ---- test negatif, un par sens -----------------------------------------
# Bug injecte : intervertir min et max, l'erreur classique sur une contrainte
# d'ordre. Chaque variante ne remplace qu'un sens.

def _mono_avant_zele(cn, dom):
    R = cn.region
    prog = False
    for k in range(len(R) - 1):
        a, b = R[k], R[k + 1]
        if not dom[a] or not dom[b]:
            return prog, True
        seuil = max(dom[a])              # LE BUG : max au lieu de min
        trop = [v for v in dom[b] if v < seuil]
        if trop:
            for v in trop:
                dom[b].discard(v)
            prog = True
            if not dom[b]:
                return prog, True
    return prog, False


def _mono_arriere_zele(cn, dom):
    R = cn.region
    prog = False
    for k in range(len(R) - 1, 0, -1):
        a, b = R[k - 1], R[k]
        if not dom[a] or not dom[b]:
            return prog, True
        seuil = min(dom[b])              # LE BUG : min au lieu de max
        trop = [v for v in dom[a] if v > seuil]
        if trop:
            for v in trop:
                dom[a].discard(v)
            prog = True
            if not dom[a]:
                return prog, True
    return prog, False


def _fabrique_mono(sens_a, sens_b):
    def _p(rs, dom):
        for _ in range(50):
            prog = False
            for cn in rs.constraints:
                if getattr(cn, "kind", None) != "MONO":
                    continue
                pa, c = sens_a(cn, dom)
                if c:
                    return True, True
                pb, c = sens_b(cn, dom)
                if c:
                    return True, True
                prog = prog or pa or pb
            if not prog:
                break
        return True, False
    return _p


print()
print("-- test negatif Mono : chaque sens rejete SEPAREMENT --")
for etiquette, faux in (
        ("AVANT zele", _fabrique_mono(_mono_avant_zele, propager_mono_arriere)),
        ("ARRIERE zele", _fabrique_mono(propager_mono_avant, _mono_arriere_zele))):
    detecte = False
    for nom, rs in (("M |R| = 2", casM), ("N |R| = 3", casN), ("O |R|=4,d=2", casO)):
        v = cas_surete("%s / %s" % (etiquette[:8], nom), rs, prop=faux)
        if v:
            detecte = True
    if detecte:
        print("  OK : %s est rejete." % etiquette)
    else:
        print("  ECHEC : %s passe le canari." % etiquette)
        echecs += 1


# ==========================================================================
# PairDiff -- coherence d'arc sur une relation binaire.
# ==========================================================================

# P : k = 1 -- la contrainte la plus faible, equivaut a « differentes ».
casP = RuleSystem(2, 3, [PairDiff([(0, 1)], 1, 2)], "P k=1")
# Q : k = d-1 -- la plus tendue, seuls les extremes se supportent.
casQ = RuleSystem(2, 3, [PairDiff([(0, 1)], 2, 2)], "Q k=d-1")
# R : k = 0 -- VACUOUS. Toute paire est compatible : LE PIEGE, aucun retrait
#     n'y est jamais justifie.
casR = RuleSystem(2, 3, [PairDiff([(0, 1)], 0, 2)], "R k=0")
# S : chaine de deux paires -- la propagation doit passer de proche en proche.
casS = RuleSystem(2, 3, [PairDiff([(0, 1), (1, 2)], 1, 2)], "S chaine")

PD_CAS = (("P k = 1", casP), ("Q k = d-1", casQ),
          ("R k = 0 vacuous", casR), ("S chaine", casS))

print()
print("-- PairDiff : surete --")
for nom, rs in PD_CAS:
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- PairDiff : la regle doit etre INVOQUEE --")
_inv = 0
for nom, rs in PD_CAS:
    rnd5 = random.Random(47)
    for sol in echantillon(toutes_solutions(rs) or [], 40):
        for k in (1, 2):
            dom = domaines(rs, indices(sol, k, rnd5))
            for cn in rs.constraints:
                if getattr(cn, "kind", None) == "PAIRDIFF":
                    pp, _ = propager_pairdiff(cn, dom)
                    if pp:
                        _inv += 1
print("  declenchements = %d" % _inv)
if not _inv:
    print("  ECHEC : PairDiff est inerte.")
    echecs += 1
else:
    print("  OK : la regle est operante.")


# ---- test negatif : la contrainte lue comme DIRIGEE ---------------------
# Bug injecte : oublier la valeur absolue, donc exiger `v - w >= k` au lieu de
# `|v - w| >= k`. C'est l'erreur naturelle sur une contrainte de distance, et
# elle rend la relation asymetrique alors qu'elle ne l'est pas.

def _pairdiff_dirige(cn, dom):
    k = cn.k
    return _arc_local(cn.pairs, lambda v, w: v - w >= k, dom)


def _arc_local(pairs, compatible, dom):
    prog = False
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            if not dom[x] or not dom[y]:
                return prog, True
            sans = [v for v in dom[x]
                    if not any(compatible(v, w) for w in dom[y])]
            if sans:
                for v in sans:
                    dom[x].discard(v)
                prog = True
                if not dom[x]:
                    return prog, True
    return prog, False


print()
print("-- test negatif PairDiff : valeur absolue oubliee --")
_det = False
for nom, rs in PD_CAS:
    v = cas_surete("dirige " + nom, rs,
                   prop=_moteur_simple({"PAIRDIFF": _pairdiff_dirige}))
    if v:
        _det = True
if _det:
    print("  OK : le canari mord.")
else:
    print("  ECHEC : une PairDiff dirigee passe le canari.")
    echecs += 1


# ==========================================================================
# PairRatio (PAIRSTEP) -- meme helper que PairDiff, relation NON monotone.
# ==========================================================================

# T : delta = 1 -- egales ou adjacentes.
casT = RuleSystem(2, 3, [PairRatio([(0, 1)], 1)], "T delta=1")
# U : delta = d-1 -- egales ou extremes. C'EST LE CAS QUI COMPTE : le support
#     d'une valeur interieure n'est ni min ni max du domaine d'en face.
casU = RuleSystem(2, 3, [PairRatio([(0, 1)], 2)], "U delta=d-1")
# V : delta >= d -- inatteignable, la contrainte se reduit a l'egalite.
casV = RuleSystem(2, 3, [PairRatio([(0, 1)], 3)], "V delta>=d")
# W : chaine de deux paires.
casW = RuleSystem(2, 3, [PairRatio([(0, 1), (1, 2)], 1)], "W chaine")

PR_CAS = (("T delta = 1", casT), ("U delta = d-1", casU),
          ("V delta >= d", casV), ("W chaine", casW))

print()
print("-- PairRatio : surete --")
for nom, rs in PR_CAS:
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- PairRatio : la regle doit etre INVOQUEE --")
_inv = 0
for nom, rs in PR_CAS:
    rnd6 = random.Random(53)
    for sol in echantillon(toutes_solutions(rs) or [], 40):
        for k in (1, 2):
            dom = domaines(rs, indices(sol, k, rnd6))
            for cn in rs.constraints:
                if getattr(cn, "kind", None) == "PAIRSTEP":
                    pp, _ = propager_pairstep(cn, dom)
                    if pp:
                        _inv += 1
print("  declenchements = %d" % _inv)
if not _inv:
    print("  ECHEC : PairRatio est inerte.")
    echecs += 1
else:
    print("  OK : la regle est operante.")


# ---- test negatif : LE SUPPORT CHERCHE AUX BORNES -----------------------
# C'est l'erreur que le helper partage invite : recopier de `PairDiff` un test
# aux bornes, EXACT pour lui parce que sa relation est monotone en `w`, et FAUX
# ici parce que le seul support peut etre une valeur INTERIEURE du domaine.

def _pairstep_aux_bornes(cn, dom):
    delta = cn.delta
    prog = False
    for a, b in cn.pairs:
        for x, y in ((a, b), (b, a)):
            if not dom[x] or not dom[y]:
                return prog, True
            bornes = (min(dom[y]), max(dom[y]))          # LE BUG
            sans = [v for v in dom[x]
                    if not any(abs(v - w) in (0, delta) for w in bornes)]
            if sans:
                for v in sans:
                    dom[x].discard(v)
                prog = True
                if not dom[x]:
                    return prog, True
    return prog, False


print()
print("-- test negatif PairRatio : support cherche aux BORNES --")
_det = False
for nom, rs in PR_CAS:
    v = cas_surete("bornes " + nom, rs,
                   prop=_moteur_simple({"PAIRSTEP": _pairstep_aux_bornes}))
    if v:
        _det = True
if _det:
    print("  OK : le canari mord -- ce qui est exact pour PairDiff est faux ici.")
else:
    print("  ECHEC : le test aux bornes passe le canari.")
    echecs += 1


# ==========================================================================
# NoTriple -- LE PIEGE : ce n'est PAS un NeqAdj.
# ==========================================================================
#
# 14BIS, VERIFIE ET NON SUPPOSE : les fenetres sont les triplets CONSECUTIFS
# de la region -- un objet FIXE par la contrainte, qui ne depend pas des
# domaines et ne bouge pas quand ils retrecissent. L'inference porte cellule
# par cellule sur un index fixe. 14 suffit ; 14bis n'est pas engage.

# AA : |R| = 3, une seule fenetre.
casAA = RuleSystem(2, 3, [NoTriple([0, 1, 2])], "AA |R|=3")
# AB : |R| = 4, DEUX fenetres qui se chevauchent -- la propagation doit
#      traverser le chevauchement.
casAB = RuleSystem(2, 3, [NoTriple([0, 1, 2, 3])], "AB |R|=4")
# AC : d = 2 -- le cas le plus tendu : deux valeurs seulement, donc la
#      contrainte mord souvent.
casAC = RuleSystem(2, 2, [NoTriple([0, 1, 2, 3])], "AC d=2")

NT_CAS = (("AA |R| = 3", casAA), ("AB |R| = 4", casAB), ("AC d = 2", casAC))

print()
print("-- NoTriple : surete --")
for nom, rs in NT_CAS:
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- NoTriple : la regle doit etre INVOQUEE --")
_inv = 0
for nom, rs in NT_CAS:
    rnd7 = random.Random(59)
    for sol in echantillon(toutes_solutions(rs) or [], 40):
        for k in (2, 3):
            dom = domaines(rs, indices(sol, k, rnd7))
            for cn in rs.constraints:
                if getattr(cn, "kind", None) == "NOTRIPLE":
                    pp, _ = propager_notriple(cn, dom)
                    if pp:
                        _inv += 1
print("  declenchements = %d" % _inv)
if not _inv:
    print("  ECHEC : NoTriple est inerte.")
    echecs += 1
else:
    print("  OK : la regle est operante.")


# ---- test negatif : NoTriple traite comme un NeqAdj ---------------------
# DEUX valeurs identiques consecutives sont licites. Interdire `v` a la voisine
# d'une cellule valant `v` est le meme piege que NeqAdj traite comme AllDiff,
# d'un cran plus fin : la regle appliquee a la mauvaise granularite.

def _notriple_comme_neqadj(cn, dom):
    R = cn.region
    prog = False
    for k in range(len(R) - 1):
        for a, b in ((R[k], R[k + 1]), (R[k + 1], R[k])):
            if len(dom[a]) != 1:
                continue
            v = next(iter(dom[a]))
            if v not in dom[b]:
                continue
            dom[b].discard(v)              # LE BUG : deux suffiraient
            prog = True
            if not dom[b]:
                return prog, True
    return prog, False


print()
print("-- test negatif NoTriple : traite comme un NeqAdj --")
_det = False
for nom, rs in NT_CAS:
    v = cas_surete("neqadj " + nom, rs,
                   prop=_moteur_simple({"NOTRIPLE": _notriple_comme_neqadj}))
    if v:
        _det = True
if _det:
    print("  OK : le canari mord.")
else:
    print("  ECHEC : NoTriple traite comme un NeqAdj passe le canari.")
    echecs += 1


# ==========================================================================
# NoSquare -- et la VERIFICATION MECANIQUE de 14bis sur les neuf propagateurs.
# ==========================================================================

# BA : n = 2 -- une seule fenetre, la contrainte dans sa forme minimale.
casBA = RuleSystem(2, 2, [NoSquare(2, 1)], "BA n=2")
# BB : n = 3, d = 2 -- QUATRE fenetres qui se chevauchent deux a deux.
casBB = RuleSystem(3, 2, [NoSquare(3, 1)], "BB n=3 d=2")
# BC : n = 3, d = 3 -- la contrainte mord moins ; verifie qu'elle ne mord pas
#      quand elle ne doit pas.
casBC = RuleSystem(3, 3, [NoSquare(3, 1)], "BC n=3 d=3")

NS_CAS = (("BA n = 2", casBA), ("BB n=3 d=2", casBB), ("BC n=3 d=3", casBC))

print()
print("-- NoSquare : surete --")
for nom, rs in NS_CAS:
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- NoSquare : la regle doit etre INVOQUEE --")
_inv = 0
for nom, rs in NS_CAS:
    rnd8 = random.Random(61)
    for sol in echantillon(toutes_solutions(rs) or [], 40):
        for k in (2, 3):
            dom = domaines(rs, indices(sol, k, rnd8))
            for cn in rs.constraints:
                if getattr(cn, "kind", None) == "NOSQUARE":
                    pp, _ = propager_nosquare(cn, dom)
                    if pp:
                        _inv += 1
print("  declenchements = %d" % _inv)
if not _inv:
    print("  ECHEC : NoSquare est inerte.")
    echecs += 1
else:
    print("  OK : la regle est operante.")


# ---- test negatif : DEUX cellules suffiraient ---------------------------
# Le bug de granularite, une fois de plus : declencher a partir de DEUX
# singletons au lieu de trois, c'est-a-dire interdire une paire monochrome
# alors que seule la fenetre COMPLETE est interdite.

def _nosquare_a_deux(cn, dom):
    val = cn.val
    prog = False
    n = cn.n
    for r in range(n - 1):
        for c in range(n - 1):
            f = (r * n + c, r * n + c + 1, (r + 1) * n + c, (r + 1) * n + c + 1)
            surs = [i for i in f if dom[i] == {val}]
            if len(surs) < 2:                  # LE BUG : deux suffisent
                continue
            for cible in f:
                if cible in surs or val not in dom[cible]:
                    continue
                dom[cible].discard(val)
                prog = True
                if not dom[cible]:
                    return prog, True
    return prog, False


print()
print("-- test negatif NoSquare : declenche a DEUX au lieu de trois --")
_det = False
for nom, rs in NS_CAS:
    v = cas_surete("a-deux " + nom, rs,
                   prop=_moteur_simple({"NOSQUARE": _nosquare_a_deux}))
    if v:
        _det = True
if _det:
    print("  OK : le canari mord.")
else:
    print("  ECHEC : NoSquare declenche a deux passe le canari.")
    echecs += 1


# ---- 14BIS : VERIFICATION MECANIQUE, PAS PRESOMPTION --------------------
# Pour chaque propagateur, l'objet parcouru doit etre IDENTIQUE avant et apres
# des rognages arbitraires des domaines. Un objet FIXE releve de l'invariant 14
# tel quel ; un objet INDUIT engage 14bis, qui n'est pas tranche.
#
# Ce test est ecrit pour ECHOUER a l'etape 10 sur `Connected`, dont le graphe
# des cases passables depend des domaines. C'est ainsi qu'on saura que 14bis
# est engage, au lieu de le decouvrir apres coup.

print()
print("-- 14bis : l'objet d'inference est-il FIXE sous rognage ? --")
_sys14 = [
    ("AllDiff", RuleSystem(3, 3, [AllDiff([0, 1])], "a")),
    ("Count", RuleSystem(3, 3, [Count([0, 1], 1, 1, 1)], "b")),
    ("SumRange", RuleSystem(3, 3, [SumRange([0, 1], 0, 2, 3)], "c")),
    ("NeqAdj", RuleSystem(3, 3, [NeqAdj([0, 1])], "d")),
    ("Mono", RuleSystem(3, 3, [Mono([0, 1])], "e")),
    ("PairDiff", RuleSystem(3, 3, [PairDiff([(0, 1)], 1, 3)], "f")),
    ("PairRatio", RuleSystem(3, 3, [PairRatio([(0, 1)], 1)], "g")),
    ("NoTriple", RuleSystem(3, 3, [NoTriple([0, 1, 2, 3])], "h")),
    ("NoSquare", RuleSystem(3, 3, [NoSquare(3, 1)], "i")),
    ("Connected", RuleSystem(3, 2, [Connected(3, 1)], "j")),
]
_rnd14 = random.Random(67)
_induits = []
for nom, rs in _sys14:
    cn = rs.constraints[0]
    N = rs.n * rs.n
    ref = objet_inference(cn, domaines(rs, [UNASSIGNED] * N))
    if ref is None:
        print("  %-10s AUCUN objet declare -- 14bis non verifiable" % nom)
        echecs += 1
        continue
    fixe = True
    for _ in range(40):
        dom = domaines(rs, [UNASSIGNED] * N)
        for i in range(N):                       # rognages arbitraires
            for v in range(rs.d):
                if len(dom[i]) > 1 and _rnd14.random() < 0.4:
                    dom[i].discard(v)
        if objet_inference(cn, dom) != ref:
            fixe = False
            break
    st = statut_objet(cn.kind, fixe)
    print("  %-10s %-19s (%d elements)" % (nom, st, len(ref)))
    if st == "INDUIT-SANS-PREUVE":
        _induits.append(nom)
if _induits:
    print("  ECHEC : objet INDUIT sans preuve de surete ecrite : %s."
          % ", ".join(_induits))
    print("  L'invariant 14ter exige que la preuve soit ECRITE ET REFERENCEE "
          "avant d'adopter le propagateur.")
    echecs += 1
else:
    print("  OK : aucun objet induit sans preuve.")
for _k, _quoi in sorted(SURETE_OBJET_INDUIT.items()):
    print("  preuve declaree pour %s : %s" % (_k, _quoi))

# --- LA TROISIEME ISSUE DOIT ETRE ATTEIGNABLE (invariant 9) ---
# Un canari jamais vu echouer ne verifie rien. On evalue directement la
# fonction de decision sur un `kind` fictif, non declare.
_essais_statut = [
    ("kind fixe", statut_objet("ALLDIFF", True), "FIXE"),
    ("kind induit declare", statut_objet("CONNECTED", False), "INDUIT-PROUVE"),
    ("kind induit NON declare", statut_objet("FICTIF", False),
     "INDUIT-SANS-PREUVE"),
]
print()
print("-- 14ter : les trois issues sont-elles atteignables ? --")
for _nom, _obtenu, _attendu in _essais_statut:
    _ok = (_obtenu == _attendu)
    print("  %-24s -> %-19s %s" % (_nom, _obtenu, "OK" if _ok else "ECHEC"))
    if not _ok:
        echecs += 1


# ==========================================================================
# Connected -- objet INDUIT, et le piege est la CONDITION D'AMORCAGE.
# ==========================================================================
#
# La preuve est dans `engine/propagate.py`, ecrite avant le code. Ici on la
# met a l'epreuve, en construisant a la main les configurations que le
# generateur ne produit pas.

# CA : d = 2 -- le regime naturel de Connected : `val` ou pas `val`.
casCA = RuleSystem(3, 2, [Connected(3, 1)], "CA d=2")
# CB : d = 2 avec un Count qui force une composante de taille moyenne, donc
#      des ancres CERTAINES apparaissent souvent.
casCB = RuleSystem(3, 2, [Connected(3, 1),
                          Count(list(range(9)), 1, 3, 5)], "CB ancre")
# CC : d = 3 -- `val` minoritaire, donc |F| reste souvent VIDE : c'est le cas
#      ou aucun retrait n'est justifie, et ou un propagateur trop zele mord.
casCC = RuleSystem(3, 3, [Connected(3, 1)], "CC d=3")

CO_CAS = (("CA d = 2", casCA), ("CB ancre", casCB), ("CC d = 3", casCC))

print()
print("-- Connected : surete --")
for nom, rs in CO_CAS:
    v = cas_surete(nom, rs)
    if v is None or v > 0:
        echecs += 1

print()
print("-- Connected : la regle doit etre INVOQUEE --")
_inv = _contra = 0
for nom, rs in CO_CAS:
    rnd9 = random.Random(71)
    for sol in echantillon(toutes_solutions(rs) or [], 60):
        for k in (3, 4, 5):
            dom = domaines(rs, indices(sol, k, rnd9))
            for cn in rs.constraints:
                if getattr(cn, "kind", None) == "CONNECTED":
                    pp, ct = propager_connected(cn, dom)
                    if pp:
                        _inv += 1
                    if ct:
                        _contra += 1
print("  retraits = %d   contradictions = %d" % (_inv, _contra))
if not _inv:
    print("  ECHEC : le retrait par inaccessibilite est inerte.")
    echecs += 1
else:
    print("  OK : la regle est operante.")


# ---- TEST NEGATIF : L'ANCRE OUBLIEE -------------------------------------
# LE piege de cette contrainte. Sans cellule CERTAINEMENT `val`, la composante
# peut etre n'importe ou -- ou vide, `feasible()` acceptant zero ou une seule
# cellule `val`. Partir d'une cellule seulement POSSIBLE est donc faux.

def _connected_sans_ancre(cn, dom):
    val, n = cn.val, cn.n
    passables = set(i for i in cn.region if val in dom[i])
    certaines = [i for i in cn.region if dom[i] == {val}]
    depart = certaines[0] if certaines else (
        min(passables) if passables else None)      # LE BUG
    if depart is None:
        return False, False
    vus, pile = {depart}, [depart]
    while pile:
        x = pile.pop()
        for y in neighbors4(x, n):
            if y in passables and y not in vus:
                vus.add(y)
                pile.append(y)
    prog = False
    for i in passables:
        if i in vus:
            continue
        dom[i].discard(val)
        prog = True
        if not dom[i]:
            return prog, True
    return prog, False


print()
print("-- test negatif Connected : ancre PRISE PARMI LES POSSIBLES --")
_det = False
for nom, rs in CO_CAS:
    v = cas_surete("sans-ancre " + nom, rs,
                   prop=_moteur_simple({"CONNECTED": _connected_sans_ancre}))
    if v:
        _det = True
if _det:
    print("  OK : le canari mord -- l'ancre doit etre CERTAINE.")
else:
    print("  ECHEC : une ancre seulement possible passe le canari.")
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


def croisement_surete(nom, rs, prop=None, verbeux=True,
                      max_sols=None, max_taille=None):
    """Surete sur toutes les solutions x tous les sous-ensembles d'indices.

    REGIME EXHAUSTIF par defaut : les grilles de croisement sont minuscules
    expres pour que ce soit calculable en entier -- un echantillon aleatoire
    raterait precisement la configuration rare qui declenche l'interaction.

    REGIME ECHANTILLON quand `max_sols` ou `max_taille` est donne. Necessaire
    des que la contrainte exige une region de plus de trois cellules, donc une
    grille de plus de quatre cases (`NoTriple`, `NoSquare`). Le regime est
    IMPRIME a chaque ligne : un croisement echantillonne ne doit pas etre lu
    comme un croisement exhaustif.
    """
    fonction = prop or propager
    sols = toutes_solutions(rs)
    if sols is None:
        print("  %-30s INDETERMINE : au-dela du plafond" % nom)
        return None
    N = rs.n * rs.n
    tmax = N if max_taille is None else min(max_taille, N)
    retenues = echantillon(sols, max_sols)
    viol = essais = 0
    for sol in retenues:
        for taille in range(tmax + 1):
            for pris in itertools.combinations(range(N), taille):
                essais += 1
                g = [sol[i] if i in pris else UNASSIGNED for i in range(N)]
                dom = domaines(rs, g)
                _, contra = fonction(rs, dom)
                if contra or not domaines_contiennent(dom, sol):
                    viol += 1
    if verbeux:
        exhaustif = (max_sols is None and max_taille is None)
        print("  %-30s sols=%d/%d essais=%-6d %s VIOLATIONS=%d"
              % (nom, len(retenues), len(sols), essais,
                 "exhaustif" if exhaustif else "ECHANTILLON<=%d" % tmax, viol))
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

_moteur = _moteur_simple


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


def _paire(titre, rs_chev, rs_disj, bug, max_sols=None, max_taille=None):
    """Un croisement complet : surete des deux cotes, puis le bug injecte, qui
    doit mordre sur le CHEVAUCHANT et rester muet sur le TEMOIN disjoint."""
    print()
    print("-- croisement %s --" % titre)
    faute = 0
    for etiq, rs in (("surete chevauche", rs_chev), ("surete disjoint ", rs_disj)):
        v = croisement_surete("  " + etiq, rs,
                              max_sols=max_sols, max_taille=max_taille)
        if v is None or v > 0:
            faute += 1
    vc = croisement_surete("  bug chevauche  ", rs_chev, prop=bug,
                           max_sols=max_sols, max_taille=max_taille)
    vd = croisement_surete("  bug disjoint   ", rs_disj, prop=bug,
                           max_sols=max_sols, max_taille=max_taille)
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


# ---- paires impliquant NeqAdj -------------------------------------------

def _neq_bugue_forme(d):
    """BUG D'INTERACTION, classe de l'invariant 14 : deduire le CONTENU d'un
    domaine de sa FORME. Ici « domaine deja rogne = cellule decidee », donc on
    prend son minimum comme si la valeur etait fixee. Exige qu'un AUTRE
    propagateur ait rogne partiellement une cellule partagee."""
    def f(cn, dom):
        R = cn.region
        prog = False
        for k in range(len(R) - 1):
            for a, b in ((R[k], R[k + 1]), (R[k + 1], R[k])):
                if len(dom[a]) == 1:
                    v = next(iter(dom[a]))
                elif 1 < len(dom[a]) < d:
                    v = min(dom[a])          # LE BUG
                else:
                    continue
                if v not in dom[b]:
                    continue
                dom[b].discard(v)
                prog = True
                if not dom[b]:
                    return prog, True
        return prog, False
    return f


_bug_neq = _moteur({"NEQADJ": _neq_bugue_forme(3)})

echecs += _paire(
    "AllDiff |R|<d  x  NeqAdj",
    RuleSystem(2, 3, [AllDiff([0, 1]), NeqAdj([1, 2])], "N1c"),
    RuleSystem(2, 3, [AllDiff([0, 1]), NeqAdj([2, 3])], "N1d"),
    _bug_neq)

echecs += _paire(
    "Count lo=hi=1  x  NeqAdj",
    RuleSystem(2, 3, [Count([0, 1], 1, 1, 1), NeqAdj([1, 2])], "N2c"),
    RuleSystem(2, 3, [Count([0, 1], 1, 1, 1), NeqAdj([2, 3])], "N2d"),
    _bug_neq)

echecs += _paire(
    "SumRange  x  NeqAdj",
    RuleSystem(2, 3, [SumRange([0, 1], 0, 2, 3), NeqAdj([1, 2])], "N3c"),
    RuleSystem(2, 3, [SumRange([0, 1], 0, 2, 3), NeqAdj([2, 3])], "N3d"),
    _bug_neq)


# ---- paires impliquant Mono ---------------------------------------------
#
# NOTE : le propagateur Mono de production ne fait AUCUNE lecture de forme,
# donc l'invariant 14 le declare sur par construction. Le bug injecte ici en
# introduit une DELIBEREMENT -- c'est la seule facon de fabriquer une
# interaction unsound sur cette contrainte, et c'est en soi une confirmation
# de l'invariant.

def _mono_bugue_forme(d):
    """BUG D'INTERACTION : « domaine deja rogne = cellule decidee », donc on
    borne `dom[b]` par son MINIMUM au lieu de son maximum dans le sens
    ARRIERE. Exige qu'un autre propagateur ait rogne partiellement `b`."""
    def f(cn, dom):
        prog, c = propager_mono_avant(cn, dom)   # ce sens reste correct
        if c:
            return True, True
        R = cn.region
        for k in range(len(R) - 1, 0, -1):
            a, b = R[k - 1], R[k]
            if not dom[a] or not dom[b]:
                return True, True
            seuil = min(dom[b]) if 1 < len(dom[b]) < d else max(dom[b])
            trop = [v for v in dom[a] if v > seuil]
            if trop:
                for v in trop:
                    dom[a].discard(v)
                prog = True
                if not dom[a]:
                    return prog, True
        return prog, False
    return f


_bug_mono = _moteur({"MONO": _mono_bugue_forme(3)})

echecs += _paire(
    "AllDiff |R|<d  x  Mono",
    RuleSystem(2, 3, [AllDiff([0, 1]), Mono([1, 2])], "M1c"),
    RuleSystem(2, 3, [AllDiff([0, 1]), Mono([2, 3])], "M1d"),
    _bug_mono)

# ORDRE DE LA REGION IMPOSE PAR LE BUG. Le bug injecte porte sur le sens
# ARRIERE, qui lit `dom[b]` -- la cellule la PLUS LOIN dans l'ordre de la
# region. Il faut donc que la cellule partagee soit ce `b`, pas le `a`.
# Avec `Mono([1, 2])` et Count sur `[0, 1]`, l'autre propagateur rogne le `a`
# et le bug ne voit jamais de domaine partiel : les deux croisements ont
# ECHOUE avant d'etre corriges ainsi.
#
# TROISIEME OCCURRENCE DE LA MEME LECON, et elle se precise : il ne suffit pas
# que l'un des deux puisse ROGNER une cellule partagee -- il faut qu'il rogne
# LA cellule que l'inference injectee va lire.
echecs += _paire(
    "Count lo=hi=1  x  Mono",
    RuleSystem(2, 3, [Count([0, 1], 1, 1, 1), Mono([2, 1])], "M2c"),
    RuleSystem(2, 3, [Count([0, 1], 1, 1, 1), Mono([3, 2])], "M2d"),
    _bug_mono)

echecs += _paire(
    "SumRange  x  Mono",
    RuleSystem(2, 3, [SumRange([0, 1], 0, 2, 3), Mono([2, 1])], "M3c"),
    RuleSystem(2, 3, [SumRange([0, 1], 0, 2, 3), Mono([3, 2])], "M3d"),
    _bug_mono)

echecs += _paire(
    "NeqAdj  x  Mono",
    RuleSystem(2, 3, [NeqAdj([0, 1]), Mono([1, 2])], "M4c"),
    RuleSystem(2, 3, [NeqAdj([0, 1]), Mono([2, 3])], "M4d"),
    _bug_mono)


# ---- paires impliquant PairDiff -----------------------------------------
#
# `propager_pairdiff` ne fait AUCUNE lecture de forme : il est sur par
# construction (invariant 14), comme `Mono`. Le bug injecte doit donc, la
# encore, en introduire une DELIBEREMENT.

def _pairdiff_bugue_forme(d):
    """BUG D'INTERACTION : « domaine deja rogne = cellule decidee », donc on
    cherche le support dans {min(dom[y])} seulement au lieu de tout `dom[y]`.
    Exige qu'un autre propagateur ait rogne partiellement `y`."""
    def f(cn, dom):
        k = cn.k
        prog = False
        for a, b in cn.pairs:
            for x, y in ((a, b), (b, a)):
                if not dom[x] or not dom[y]:
                    return prog, True
                supports = ({min(dom[y])} if 1 < len(dom[y]) < d
                            else dom[y])          # LE BUG
                sans = [v for v in dom[x]
                        if not any(abs(v - w) >= k for w in supports)]
                if sans:
                    for v in sans:
                        dom[x].discard(v)
                    prog = True
                    if not dom[x]:
                        return prog, True
        return prog, False
    return f


_bug_pd = _moteur({"PAIRDIFF": _pairdiff_bugue_forme(3)})

for _titre, _autre in (
        ("AllDiff |R|<d", AllDiff([0, 1])),
        ("Count lo=hi=1", Count([0, 1], 1, 1, 1)),
        ("SumRange", SumRange([0, 1], 0, 2, 3)),
        ("NeqAdj", NeqAdj([0, 1])),
        ("Mono", Mono([0, 1]))):
    echecs += _paire(
        "%s  x  PairDiff" % _titre,
        RuleSystem(2, 3, [_autre, PairDiff([(2, 1)], 1, 2)], "PDc"),
        RuleSystem(2, 3, [_autre, PairDiff([(3, 2)], 1, 2)], "PDd"),
        _bug_pd)


# ---- paires impliquant PairRatio ----------------------------------------

def _pairstep_bugue_forme(d):
    """BUG D'INTERACTION : support cherche dans {min(dom[y])} quand `y` est
    partiellement rogne. Exige qu'un AUTRE propagateur ait fait ce rognage."""
    def f(cn, dom):
        delta = cn.delta
        prog = False
        for a, b in cn.pairs:
            for x, y in ((a, b), (b, a)):
                if not dom[x] or not dom[y]:
                    return prog, True
                supports = ({min(dom[y])} if 1 < len(dom[y]) < d
                            else dom[y])          # LE BUG
                sans = [v for v in dom[x]
                        if not any(abs(v - w) in (0, delta) for w in supports)]
                if sans:
                    for v in sans:
                        dom[x].discard(v)
                    prog = True
                    if not dom[x]:
                        return prog, True
        return prog, False
    return f


_bug_pr = _moteur({"PAIRSTEP": _pairstep_bugue_forme(3)})

# La derniere paire est la plus interessante : PairDiff x PairRatio, les deux
# propagateurs qui PARTAGENT `_arc_consistance`. C'est le croisement qui couvre
# le risque assume au commit precedent.
for _titre, _autre in (
        ("AllDiff |R|<d", AllDiff([0, 1])),
        ("Count lo=hi=1", Count([0, 1], 1, 1, 1)),
        ("SumRange", SumRange([0, 1], 0, 2, 3)),
        ("NeqAdj", NeqAdj([0, 1])),
        # ORDRE INVERSE, ET C'EST LA QUATRIEME FORME DE LA MEME LECON.
        # `Mono([0, 1])` ne peut que RELEVER le plancher de `dom[1]`, qui vaut
        # alors {1, 2} : son minimum, 1, supporte toutes les valeurs a delta=1,
        # donc le bug ne retire rien. Il faut `Mono([1, 0])`, qui ABAISSE le
        # plafond et produit `dom[1] = {0, 1}` -- le minimum 0 ne supporte plus
        # la valeur 2, et le bug mord.
        # Il ne suffit donc pas que l'autre propagateur rogne LA cellule lue :
        # il faut qu'il puisse produire le domaine partiel PARTICULIER que
        # l'inference injectee lit de travers.
        ("Mono", Mono([1, 0])),
        ("PairDiff (helper partage)", PairDiff([(0, 1)], 1, 2))):
    echecs += _paire(
        "%s  x  PairRatio" % _titre,
        RuleSystem(2, 3, [_autre, PairRatio([(2, 1)], 1)], "PRc"),
        RuleSystem(2, 3, [_autre, PairRatio([(3, 2)], 1)], "PRd"),
        _bug_pr)


# ---- paires impliquant NoTriple -----------------------------------------
#
# Ces croisements sont a n=3 : `NoTriple` exige une region de 4 cellules pour
# avoir deux fenetres, et le TEMOIN disjoint doit loger ailleurs. Une grille de
# 4 cases n'y suffit pas. Le regime devient donc ECHANTILLON, et il est
# imprime a chaque ligne -- une couverture echantillonnee ne doit pas etre lue
# comme exhaustive.

def _notriple_bugue_forme(d):
    """BUG D'INTERACTION : « domaine deja rogne = cellule decidee a son
    minimum », substitue au test de singleton. Exige qu'un AUTRE propagateur
    ait rogne partiellement une cellule de la fenetre."""
    def _valeur(dm):
        if len(dm) == 1:
            return next(iter(dm))
        if 1 < len(dm) < d:
            return min(dm)                 # LE BUG
        return None

    def f(cn, dom):
        prog = False
        for k in range(len(cn.region) - 2):
            fenetre = (cn.region[k], cn.region[k + 1], cn.region[k + 2])
            for i in range(3):
                cible = fenetre[i]
                a, b = [fenetre[j] for j in range(3) if j != i]
                va, vb = _valeur(dom[a]), _valeur(dom[b])
                if va is None or va != vb or va not in dom[cible]:
                    continue
                dom[cible].discard(va)
                prog = True
                if not dom[cible]:
                    return prog, True
        return prog, False
    return f


_bug_nt = _moteur({"NOTRIPLE": _notriple_bugue_forme(3)})

for _titre, _autre in (
        ("AllDiff |R|<d", AllDiff([0, 1])),
        ("Count lo=hi=1", Count([0, 1], 1, 1, 1)),
        ("SumRange", SumRange([0, 1], 0, 2, 3)),
        ("NeqAdj", NeqAdj([0, 1])),
        ("Mono", Mono([0, 1])),
        ("PairDiff", PairDiff([(0, 1)], 1, 3)),
        ("PairRatio", PairRatio([(0, 1)], 1))):
    echecs += _paire(
        "%s  x  NoTriple" % _titre,
        RuleSystem(3, 3, [_autre, NoTriple([0, 1, 2, 3])], "NTc"),
        RuleSystem(3, 3, [_autre, NoTriple([5, 6, 7, 8])], "NTd"),
        _bug_nt, max_sols=120, max_taille=3)


# ---- paires impliquant NoSquare -----------------------------------------
#
# PROBLEME STRUCTUREL, ET IL ANNONCE CELUI DE `Connected` : les fenetres de
# `NoSquare` couvrent **toute la grille**. Aucune autre contrainte ne peut donc
# lui etre DISJOINTE, et le temoin disjoint utilise pour les huit propagateurs
# precedents est **impossible a construire**.
#
# Il est remplace par un controle **strictement plus fort** : le meme systeme,
# avec le propagateur de l'autre contrainte DESACTIVE. Les deux mondes ont
# alors exactement le meme ensemble de solutions -- seule change la capacite de
# l'autre propagateur a rogner. Si le bug ne mord que lorsque l'autre
# propagateur tourne, l'interaction est demontree sans dependre d'une geometrie.

def _moteur_restreint(remplacants, kinds_actifs):
    """Comme `_moteur`, mais seuls les `kind` listes sont propages du tout.
    Les autres contraintes restent PRESENTES -- donc les solutions sont les
    memes -- mais ne filtrent pas."""
    def _p(rs, dom):
        for _ in range(60):
            prog = False
            for cn in rs.constraints:
                k = getattr(cn, "kind", None)
                if k not in kinds_actifs:
                    continue
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


def _nosquare_bugue_forme(d):
    """BUG D'INTERACTION, classe de l'invariant 14 : « domaine deja rogne =
    cellule decidee a son minimum », substitue au test de singleton."""
    def _est_val(dm, val):
        if len(dm) == 1:
            return val in dm
        if 1 < len(dm) < d:
            return min(dm) == val              # LE BUG
        return False

    def f(cn, dom):
        val = cn.val
        prog = False
        n = cn.n
        for r in range(n - 1):
            for c in range(n - 1):
                fen = (r * n + c, r * n + c + 1,
                       (r + 1) * n + c, (r + 1) * n + c + 1)
                surs = [i for i in fen if _est_val(dom[i], val)]
                if len(surs) != 3:
                    continue
                cible = [i for i in fen if i not in surs][0]
                if val not in dom[cible]:
                    continue
                dom[cible].discard(val)
                prog = True
                if not dom[cible]:
                    return prog, True
        return prog, False
    return f


# La chaine `NoTriple -> NoSquare` a besoin de QUATRE cellules posees pour
# s'amorcer : deux pour que NoTriple retire une valeur, deux de plus pour
# completer la fenetre 2x2. A `max_taille = 3` le croisement ne pouvait pas
# se declencher -- couverture aveugle, pas bug inerte (invariant 15).
NS_TAILLE = 4


def _paire_nosquare(titre, rs, autre_kind, bug_fn):
    """Croisement sans temoin disjoint : le controle est le meme systeme avec
    le propagateur de l'autre contrainte desactive."""
    print()
    print("-- croisement %s  x  NoSquare (controle : autre propagateur OFF) --"
          % titre)
    faute = 0
    v = croisement_surete("  surete (tout actif)", rs,
                          max_sols=120, max_taille=NS_TAILLE)
    if v is None or v > 0:
        faute += 1
    avec = croisement_surete(
        "  bug, autre ACTIF  ", rs,
        prop=_moteur_restreint({"NOSQUARE": bug_fn}, {autre_kind, "NOSQUARE"}),
        max_sols=120, max_taille=NS_TAILLE)
    sans = croisement_surete(
        "  bug, autre INACTIF", rs,
        prop=_moteur_restreint({"NOSQUARE": bug_fn}, {"NOSQUARE"}),
        max_sols=120, max_taille=NS_TAILLE)
    if not avec:
        print("  ECHEC : le bug d'interaction ne mord pas.")
        faute += 1
    elif sans:
        print("  ECHEC : il mord AUSSI sans l'autre propagateur (%d) -- bug "
              "simple, pas interaction." % sans)
        faute += 1
    else:
        print("  OK : mord avec l'autre propagateur (%d), muet sans lui (%d)."
              % (avec, sans))
    return faute


_bug_ns = _nosquare_bugue_forme(3)

# CINQUIEME FORME DE LA MEME LECON, et elle se lit maintenant sans tatonner.
# Le bug lit `min(dom) == val` avec `val = 1` : il lui faut donc un domaine
# partiel EGAL A {1, 2}, c'est-a-dire dont la valeur 0 a ete retiree.
#   - `Count([0,1], val=1, ...)` ne retire jamais que la valeur 1 elle-meme :
#     il produit {0, 2}, jamais {1, 2}. STRUCTURELLEMENT incapable.
#   - `SumRange([0,1], lo=0, ...)` n'a que son PLAFOND actif (lo = 0 rend le
#     plancher inerte), donc il ne retire que les GRANDES valeurs. Idem.
# Corriges en `Count(val=0)` et `SumRange(lo=3)`, qui retirent la valeur 0.
# Les deux ont ete constates en faisant echouer le croisement, pas devines.
for _titre, _autre, _kind in (
        ("AllDiff |R|<d", AllDiff([0, 1]), "ALLDIFF"),
        ("Count val=0", Count([0, 1], 0, 1, 1), "COUNT"),
        ("SumRange plancher", SumRange([0, 1], 3, 4, 3), "SUM"),
        ("NeqAdj", NeqAdj([0, 1]), "NEQADJ"),
        ("Mono", Mono([1, 0]), "MONO"),
        ("PairDiff", PairDiff([(0, 1)], 1, 3), "PAIRDIFF"),
        ("PairRatio", PairRatio([(0, 1)], 1), "PAIRSTEP"),
        ("NoTriple", NoTriple([0, 1, 2, 3]), "NOTRIPLE")):
    echecs += _paire_nosquare(
        _titre,
        RuleSystem(3, 3, [_autre, NoSquare(3, 1)], "NSc"),
        _kind, _bug_ns)


# ---- paires impliquant Connected ----------------------------------------
#
# Comme `NoSquare`, `Connected` porte sur TOUTE la grille : aucun temoin
# disjoint n'est constructible. Meme controle, strictement plus fort : le meme
# systeme avec le propagateur de l'autre contrainte DESACTIVE.

def _connected_bugue_forme(d):
    """BUG D'INTERACTION, classe de l'invariant 14 : deduire le CONTENU d'un
    domaine de sa FORME. Ici, une cellule au domaine deja rogne est tenue pour
    CERTAINEMENT `val` -- donc utilisable comme ancre. Exige qu'un AUTRE
    propagateur ait rogne partiellement une cellule."""
    def f(cn, dom):
        val, n = cn.val, cn.n
        passables = set(i for i in cn.region if val in dom[i])
        certaines = [i for i in cn.region
                     if dom[i] == {val}
                     or (1 < len(dom[i]) < d and val in dom[i])]   # LE BUG
        if not certaines:
            return False, False
        depart = certaines[0]
        vus, pile = {depart}, [depart]
        while pile:
            x = pile.pop()
            for y in neighbors4(x, n):
                if y in passables and y not in vus:
                    vus.add(y)
                    pile.append(y)
        for c in certaines:
            if c not in vus:
                return False, True
        prog = False
        for i in passables:
            if i in vus:
                continue
            dom[i].discard(val)
            prog = True
            if not dom[i]:
                return prog, True
        return prog, False
    return f


def _paire_connected(titre, rs, autre_kind, bug_fn, kind_bugue="CONNECTED"):
    print()
    print("-- croisement %s  x  Connected (controle : autre propagateur OFF) --"
          % titre)
    faute = 0
    v = croisement_surete("  surete (tout actif)", rs,
                          max_sols=120, max_taille=NS_TAILLE)
    if v is None or v > 0:
        faute += 1
    avec = croisement_surete(
        "  bug, autre ACTIF  ", rs,
        prop=_moteur_restreint({kind_bugue: bug_fn},
                               {autre_kind, "CONNECTED"}),
        max_sols=120, max_taille=NS_TAILLE)
    sans = croisement_surete(
        "  bug, autre INACTIF", rs,
        prop=_moteur_restreint({kind_bugue: bug_fn}, {kind_bugue}),
        max_sols=120, max_taille=NS_TAILLE)
    if not avec:
        print("  ECHEC : le bug d'interaction ne mord pas.")
        faute += 1
    elif sans:
        print("  ECHEC : il mord AUSSI sans l'autre propagateur (%d) -- bug "
              "simple, pas interaction." % sans)
        faute += 1
    else:
        print("  OK : mord avec l'autre propagateur (%d), muet sans lui (%d)."
              % (avec, sans))
    return faute


_bug_co = _connected_bugue_forme(3)

for _titre, _autre, _kind in (
        ("AllDiff |R|<d", AllDiff([0, 1]), "ALLDIFF"),
        ("Count val=0", Count([0, 1], 0, 1, 1), "COUNT"),
        ("SumRange plancher", SumRange([0, 1], 3, 4, 3), "SUM"),
        ("NeqAdj", NeqAdj([0, 1]), "NEQADJ"),
        # CINQUIEME LECON, SIXIEME FORME. Le bug prend pour ancre une cellule
        # au domaine partiel CONTENANT `val`, et `certaines[0]` retient le PLUS
        # PETIT INDICE. Avec `Mono([1, 0])`, la fausse ancre (indice 1) est
        # toujours precedee par la VRAIE ancre (indice 0) qui l'a causee : le
        # bug est MASQUE. `Mono([4, 0])` place la fausse ancre en 0 et la vraie
        # en 4. Constate en faisant echouer le croisement.
        ("Mono", Mono([4, 0]), "MONO"),
        ("PairDiff", PairDiff([(0, 1)], 1, 3), "PAIRDIFF"),
        ("PairRatio", PairRatio([(0, 1)], 1), "PAIRSTEP"),
        ("NoTriple", NoTriple([0, 1, 2, 3]), "NOTRIPLE"),
):
    echecs += _paire_connected(
        _titre,
        RuleSystem(3, 3, [_autre, Connected(3, 1)], "COc"),
        _kind, _bug_co)

# NoSquare x Connected : LE BUG CHANGE DE COTE, et la raison est structurelle.
# Les deux propagateurs ne font que RETIRER `val` ; aucun ne produit jamais un
# domaine partiel CONTENANT `val`, qui est ce dont le bug d'ancre a besoin.
# Le sens Connected -> NoSquare, lui, se declenche : Connected retire `val=1`
# et laisse {0, 2}, dont le MINIMUM vaut 0 -- le `val` de NoSquare. Le bug de
# forme de NoSquare y lit une cellule « certaine » qui ne l'est pas.
# UNE PAIRE PEUT N'ETRE DECLENCHABLE QUE DANS UN SEUL SENS.
echecs += _paire_connected(
    "NoSquare(v0)", RuleSystem(3, 3, [NoSquare(3, 0), Connected(3, 1)], "COn"),
    "NOSQUARE", _nosquare_bugue_forme(3), kind_bugue="NOSQUARE")



# ==========================================================================
# ARTICULATION -- le forcage par sommet separateur (drapeau, defaut OFF)
# ==========================================================================
#
# LA PREUVE NE DISPENSE PAS DU TEST. Le forcage etait prouve depuis le 26/08 et
# n'a jamais tourne. La journee du 26 a produit dix cas ou un raisonnement juste
# accompagnait un instrument faux ; c'est ce que cette section refuse de
# reproduire.
#
# Les cas limites ci-dessous sont construits A LA MAIN, sur des domaines poses
# cellule par cellule : le generateur ne produit pas de couloirs.

import propagate as _PG

print()
print("== ARTICULATION : forcage par sommet separateur ==")


def _co(val=1, n=3):
    for cn in RuleSystem(n, 2, [Connected(n, val)], "x").constraints:
        if getattr(cn, "kind", None) == "CONNECTED":
            return cn
    raise AssertionError("Connected sans propagateur")


def _dom_de(spec, n=3):
    """spec : {indice: ensemble}. Absent -> {0} (impassable)."""
    return [set(spec.get(i, {0})) for i in range(n * n)]


def _forces(dom_avant, dom_apres, val=1):
    return sorted(i for i in range(len(dom_avant))
                  if dom_apres[i] == {val} and dom_avant[i] != {val})


# GRILLE 3x3, indices 0..8 en lignes. `val` = 1.
#   0 1 2
#   3 4 5
#   6 7 8
CAS_ART = (
    # COULOIR : seuls 0,1,2,5,8 peuvent valoir 1 ; ancres en 0 et 8. Tout
    # chemin de 0 a 8 passe par 1, 2 et 5 : les trois sont forces.
    ("couloir",
     {0: {1}, 1: {0, 1}, 2: {0, 1}, 5: {0, 1}, 8: {1}},
     [1, 2, 5]),
    # ANCRE UNIQUE : meme couloir, mais 8 n'est que POSSIBLE. S peut se reduire
    # a {0} : RIEN n'est force. C'est le piege de la regle.
    ("ancre unique",
     {0: {1}, 1: {0, 1}, 2: {0, 1}, 5: {0, 1}, 8: {0, 1}},
     []),
    # AUCUNE ANCRE : rien, evidemment, mais il faut que ce soit teste.
    ("aucune ancre",
     {0: {0, 1}, 1: {0, 1}, 2: {0, 1}, 5: {0, 1}, 8: {0, 1}},
     []),
    # DEUX CHEMINS : la grille entiere est passable, deux ancres opposees. Il
    # n'existe aucun sommet separateur : rien n'est force. Un propagateur trop
    # zele mord ici.
    ("deux chemins",
     dict([(0, {1}), (8, {1})] + [(i, {0, 1}) for i in range(1, 8)]),
     []),
    # ANCRES ADJACENTES : aucun sommet entre elles.
    ("ancres adjacentes",
     dict([(0, {1}), (1, {1})] + [(i, {0, 1}) for i in range(2, 9)]),
     []),
    # SEPARATEUR DEJA CERTAIN : 1 est deja {1}. Separateur, mais rien a
    # forcer -- et surtout, pas de boucle infinie ni de faux progres.
    ("separateur deja certain",
     {0: {1}, 1: {1}, 2: {0, 1}, 5: {0, 1}, 8: {1}},
     [2, 5]),
    # TROIS ANCRES, separateur qui ne separe PAS de la premiere ancre : il
    # separe 8 de 6. L'ancrage unique doit quand meme l'attraper (il separe
    # alors 0 de l'une des deux).
    ("trois ancres",
     {0: {1}, 3: {0, 1}, 6: {1}, 1: {0, 1}, 2: {0, 1}, 5: {0, 1}, 8: {1}},
     [1, 2, 5, 3]),
)

print()
print("-- articulation OFF : la regle doit etre INERTE --")
_PG.ARTICULATION = False
_faute = 0
for _nom, _spec, _att in CAS_ART:
    _d0 = _dom_de(_spec)
    _d1 = _dom_de(_spec)
    propager_connected(_co(), _d1)
    _f = _forces(_d0, _d1)
    if _f:
        print("  %-24s ECHEC : force %s alors que le drapeau est OFF"
              % (_nom, _f))
        _faute += 1
if _faute:
    echecs += _faute
else:
    print("  OK : drapeau OFF, aucun forcage. Le bras de reference est intact.")

print()
print("-- articulation ON : cas limites construits a la main --")
_PG.ARTICULATION = True
for _nom, _spec, _att in CAS_ART:
    _d0 = _dom_de(_spec)
    _d1 = _dom_de(_spec)
    _, _ct = propager_connected(_co(), _d1)
    _f = _forces(_d0, _d1)
    _ok = (not _ct) and _f == sorted(_att)
    print("  %-24s force=%-12s attendu=%-12s %s"
          % (_nom, _f, sorted(_att), "OK" if _ok else "ECHEC"))
    if not _ok:
        echecs += 1

print()
print("-- articulation : surete sur les systemes de Connected --")
for _nom, _rs in CO_CAS:
    _v = cas_surete("art " + _nom, _rs)
    if _v is None or _v > 0:
        echecs += 1

# ---- TEST NEGATIF 1 : FORCAGE SUR ANCRE UNIQUE --------------------------
# Le piege propre a l'articulation. Avec une seule ancre, S peut se reduire a
# {a} : aucun sommet n'est traverse, et tout forcage est faux.

def _art_ancre_unique(cn, dom):
    val, n = cn.val, cn.n
    passables = set(i for i in cn.region if val in dom[i])
    certaines = [i for i in cn.region if dom[i] == {val}]
    if not certaines:
        return False, False
    depart = certaines[0]
    vus = _PG._accessibles(passables, depart, n)
    for f in certaines:
        if f not in vus:
            return False, True
    prog = False
    for i in passables:
        if i not in vus:
            dom[i].discard(val)
            prog = True
            if not dom[i]:
                return prog, True
    passables = set(i for i in cn.region if val in dom[i])
    # LE BUG : les « autres » ancres sont remplacees par les cellules
    # ACCESSIBLES, donc une seule ancre suffit a declencher le forcage.
    autres = [i for i in passables if i != depart]                  # LE BUG
    for v in passables:
        if v == depart or dom[v] == {val}:
            continue
        joignables = _PG._accessibles(passables - {v}, depart, n)
        if any(b not in joignables for b in autres):
            dom[v] = {val}
            prog = True
    return prog, False


print()
print("-- test negatif 1 : forcage sur ANCRE UNIQUE --")
_det = False
for _nom, _rs in CO_CAS:
    if cas_surete("ancre-unique " + _nom, _rs,
                  prop=_moteur_simple({"CONNECTED": _art_ancre_unique})):
        _det = True
if _det:
    print("  OK : le canari mord -- il faut DEUX ancres certaines.")
else:
    print("  ECHEC : un forcage sur ancre unique passe le canari.")
    echecs += 1


# ---- TEST NEGATIF 2 : ANCRE = TOUT DOMAINE SINGLETON ---------------------
#
# PREMIERE VERSION ECARTEE, ET LA RAISON VAUT D'ETRE ECRITE. Le bug candidat
# etait « calculer la separation sur la REGION au lieu des passables ». Il rend
# 0 violation -- non parce qu'il serait sur, mais parce qu'il est INERTE : la
# grille 3x3 pleine est 2-connexe, donc sans sommet separateur. Un canari qui
# ne mord pas parce que son bug ne fait rien ne teste rien. C'est le motif du
# projet applique au test negatif lui-meme.
#
# LE BUG RETENU est unsound et il se declenche : toute cellule au domaine
# SINGLETON est prise pour une ancre, quelle que soit sa valeur. Une cellule
# fixee a `0` devient un point d'attache de la composante des `1`.

def _art_ancre_singleton(cn, dom):
    val, n = cn.val, cn.n
    passables = set(i for i in cn.region if val in dom[i])
    certaines = [i for i in cn.region if len(dom[i]) == 1]           # LE BUG
    if len(certaines) < 2:
        return False, False
    depart, autres = certaines[0], certaines[1:]
    prog = False
    for v in passables:
        if v == depart or dom[v] == {val}:
            continue
        joignables = _PG._accessibles(passables - {v}, depart, n)
        if any(b not in joignables for b in autres):
            dom[v] = {val}
            prog = True
    return prog, False


print()
print("-- test negatif 2 : ancre = TOUT domaine singleton --")
_det2 = False
for _nom, _rs in CO_CAS:
    if cas_surete("singleton " + _nom, _rs,
                  prop=_moteur_simple({"CONNECTED": _art_ancre_singleton})):
        _det2 = True
if _det2:
    print("  OK : le canari mord -- une ancre est {val}, pas un singleton.")
else:
    print("  ECHEC : une ancre de valeur quelconque passe le canari.")
    echecs += 1


# ---- LA REGLE DOIT MORDRE ------------------------------------------------
print()
print("-- articulation : la regle doit FORCER quelque chose --")
_nf = 0
for _nom, _rs in CO_CAS:
    _rnd = random.Random(313)
    for _sol in echantillon(toutes_solutions(_rs) or [], 60):
        for _k in (3, 4, 5):
            _g = indices(_sol, _k, _rnd)
            _dA, _dB = domaines(_rs, _g), domaines(_rs, _g)
            _PG.ARTICULATION = False
            for _cn in _rs.constraints:
                if getattr(_cn, "kind", None) == "CONNECTED":
                    propager_connected(_cn, _dA)
            _PG.ARTICULATION = True
            for _cn in _rs.constraints:
                if getattr(_cn, "kind", None) == "CONNECTED":
                    propager_connected(_cn, _dB)
            _nf += len(_forces(_dA, _dB))
print("  cellules forcees par l'articulation SEULE : %d" % _nf)
if not _nf:
    print("  ECHEC : l'articulation est INERTE -- la mesure de controle ne")
    print("  comparerait alors que deux fois le meme propagateur, et son")
    print("  resultat serait vide de sens.")
    echecs += 1
else:
    print("  OK : la regle ajoute des deductions.")


# ---- CROISEMENTS : les dix propagateurs, articulation ACTIVE -------------
# Le bug d'interaction est celui de l'invariant 14, transpose au forcage :
# une cellule au domaine deja rogne est tenue pour une ANCRE. Il exige qu'un
# AUTRE propagateur ait produit ce domaine partiel.

def _art_bugue_forme(d):
    def f(cn, dom):
        val, n = cn.val, cn.n
        passables = set(i for i in cn.region if val in dom[i])
        certaines = [i for i in cn.region
                     if dom[i] == {val}
                     or (1 < len(dom[i]) < d and val in dom[i])]     # LE BUG
        if len(certaines) < 2:
            return False, False
        depart, autres = certaines[0], certaines[1:]
        vus = _PG._accessibles(passables, depart, n)
        if any(b not in vus for b in autres):
            return False, True
        prog = False
        for v in passables:
            if v == depart or dom[v] == {val}:
                continue
            joignables = _PG._accessibles(passables - {v}, depart, n)
            if any(b not in joignables for b in autres):
                dom[v] = {val}
                prog = True
        return prog, False
    return f


_PG.ARTICULATION = True
_bug_art = _art_bugue_forme(3)

for _titre, _autre, _kind in (
        ("AllDiff |R|<d", AllDiff([0, 1]), "ALLDIFF"),
        ("Count val=0", Count([0, 1], 0, 1, 1), "COUNT"),
        ("SumRange plancher", SumRange([0, 1], 3, 4, 3), "SUM"),
        ("NeqAdj", NeqAdj([0, 1]), "NEQADJ"),
        ("Mono", Mono([4, 0]), "MONO"),
        ("PairDiff", PairDiff([(0, 1)], 1, 3), "PAIRDIFF"),
        ("PairRatio", PairRatio([(0, 1)], 1), "PAIRSTEP"),
        ("NoTriple", NoTriple([0, 1, 2, 3]), "NOTRIPLE"),
        ("NoSquare", NoSquare(3, 0), "NOSQUARE"),
):
    echecs += _paire_connected(
        "ART " + _titre,
        RuleSystem(3, 3, [_autre, Connected(3, 1)], "ARc"),
        _kind, _bug_art)

# LE DRAPEAU EST REMIS A False. Rien ne doit fuir hors de cette section : le
# bras de reference de la mesure doit rester celui du 26/08.
_PG.ARTICULATION = False
print()
print("-- drapeau remis a False : %s --" % (not _PG.ARTICULATION))
if _PG.ARTICULATION:
    print("  ECHEC : le drapeau a fuite.")
    echecs += 1

print()
if echecs:
    print("ECHEC : %d section(s) en defaut." % echecs)
    sys.exit(1)
print("OK : aucune divergence, aucune violation de surete.")
