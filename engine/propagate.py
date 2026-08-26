"""
PROPAGATION SUR DOMAINES -- projet A. Premier propagateur : ALLDIFF.

POURQUOI UN MODULE SEPARE, ET PAS UNE METHODE SUR LES CLASSES DE CONTRAINTES.
`feasible()` est conservee telle quelle pendant tout A (decision de
l'utilisateur, voir DECISIONS.md) : c'est le solveur exhaustif qui produit la
verite contre laquelle canary3 valide les propagateurs, et il s'appuie sur
`feasible()`. Si propagation et faisabilite partageaient du code, canary3
comparerait une erreur a elle-meme.

Loger les propagateurs ici plutot que dans `rulesearch.py` / `dsl2.py` rend
cette conservation VERIFIABLE PAR DIFF : ces deux fichiers ne bougent pas d'une
ligne. Une revue humaine peut se tromper ; un diff vide, non.

Consequence assumee : la logique de chaque contrainte est ecrite deux fois.
C'est l'invariant 10 de CLAUDE.md -- le prix de l'independance de l'oracle,
pas une dette technique a resorber.

CE MODULE N'EST PAS ENCORE BRANCHE SUR LA HIERARCHIE DE DEDUCTION. T0/T1/T2 et
la metrique de resistance restent inchanges (`t0_legacy`). Il existe, il est
verrouille par canary3, il ne tourne pas en production.

REGLE DE CONCEPTION, valable pour les neuf propagateurs suivants :
un propagateur ne doit RIEN conclure quand il ne peut pas conclure. En cas de
doute sur une regle de filtrage, ne pas la mettre. Un propagateur incomplet est
CORRECT ; un propagateur trop zele produit des solutions FAUSSES. Le risque est
asymetrique et le canari ne rattrape que le second.
"""
from rulesearch import UNASSIGNED


# ---------- CRITERE D'AUDIT (invariant 14 de CLAUDE.md) ----------
#
# Tout propagateur de ce module doit pouvoir etre relu ainsi, AVANT tout test :
#
#   chercher chaque endroit ou il teste une propriete de FORME d'un domaine
#   -- `len(dom[i]) == 1`, `len(dom[i]) == d`, `len(dom[i]) > 1`, « domaine
#   intact », « domaine deja rogne » -- plutot que l'APPARTENANCE d'une valeur.
#   Chaque occurrence est un point d'unsoundness potentiel par interaction.
#
# Un propagateur qui ne raisonne que sur `v in dom[i]`, `min(dom[i])`,
# `max(dom[i])` est SUR PAR CONSTRUCTION vis-a-vis des interactions : ces
# lectures portent sur le contenu, et le contenu ne fait que retrecir.
#
# LA SEULE FORME ADMISE est `len(dom[i]) == 1`, et seulement parce qu'elle
# DETERMINE le contenu exactement : un singleton a un unique membre, qu'on lit
# ensuite. Toutes les autres tailles sont des proxys du contenu, et un proxy
# est faux des qu'un autre propagateur a rogne PARTIELLEMENT la cellule.


# ---------- representation ----------

def domaines(rs, g):
    """Domaines initiaux depuis une grille partielle : singleton si assignee,
    {0..d-1} sinon. Aucun filtrage n'est fait ici."""
    plein = set(range(rs.d))
    return [{g[i]} if g[i] != UNASSIGNED else set(plein)
            for i in range(rs.n * rs.n)]


def domaines_contiennent(dom, sol):
    """Vrai si chaque valeur de `sol` survit dans le domaine de sa cellule.
    C'est le test de SURETE : un propagateur qui le viole a retire une valeur
    qui appartenait a une solution reelle."""
    return all(sol[i] in dom[i] for i in range(len(sol)))


# ---------- ALLDIFF ----------

def propager_alldiff(cn, dom):
    """UNE SEULE regle : une cellule dont le domaine est reduit a {v} interdit
    v a toutes les autres cellules de la region.

    Valide pour TOUTE taille de region -- |R| < d, |R| == d, |R| > d -- parce
    qu'elle ne suppose jamais que chaque valeur doive apparaitre. C'est
    exactement l'hypothese sur laquelle T1 s'etait trompe.

    Ce qui n'est DELIBEREMENT pas fait :
      - aucun raisonnement de comptage (« il reste k cellules et k valeurs ») :
        faux des que |R| < d, et le cas C de canary3 le verifie ;
      - aucun filtrage par couplage maximal (Regin) : ecarte, voir DECISIONS.md.
        Un AllDiff complet resoudrait localement des configurations dont la
        difficulte est precisement ce que le projet mesure.

    Note : la regle porte sur les DOMAINES singletons, pas sur les cellules
    assignees. C'est ce qui la rend strictement plus forte que le
    forward-checking de `candidates()` -- une cellule peut etre reduite a une
    seule valeur sans avoir ete assignee.

    Retourne (progres, contradiction). Contradiction = domaine vide.
    """
    prog = False
    for i in cn.region:
        if len(dom[i]) != 1:
            continue
        v = next(iter(dom[i]))
        for j in cn.region:
            if j == i or v not in dom[j]:
                continue
            dom[j].discard(v)
            prog = True
            if not dom[j]:
                return prog, True
    return prog, False


# ---------- COUNT ----------
#
# `Count(region, val, lo, hi)` : le nombre de cellules valant `val` dans la
# region est dans [lo, hi].
#
# DEUX SENS, et ils sont bien distincts :
#   - INTERDICTION : si le minimum atteignable vaut deja `hi`, aucune autre
#     cellule ne peut prendre `val` ;
#   - FORCAGE      : si le maximum atteignable vaut `lo`, toutes les cellules
#     qui peuvent encore prendre `val` doivent la prendre.
#
# Ils sont dans le meme commit parce que `canary3` les rejette SEPAREMENT dans
# son test negatif -- chacun a son bug injecte, chacun est vu mordre. Sans
# cette separation, ils auraient du etre commites un par un.
#
# Minimum atteignable = nombre de cellules DEJA reduites a {val}.
# Maximum atteignable = nombre de cellules qui PEUVENT encore valoir `val`.
#
# Ce qui n'est deliberement PAS fait : aucune detection de contradiction par
# comptage (`|sur| > hi`, `|poss| < lo`). Elle serait correcte, mais
# `feasible()` la fait deja et reste l'oracle. Seul un domaine VIDE est
# signale comme contradiction, comme pour AllDiff.


def _count_etat(cn, dom):
    """(cellules certainement `val`, cellules pouvant valoir `val`).

    « Certainement » se lit sur le DOMAINE reduit a un singleton, pas sur une
    assignation : c'est ce qui rend la regle plus forte que le
    forward-checking.
    """
    sur = [i for i in cn.region if len(dom[i]) == 1 and cn.val in dom[i]]
    poss = [i for i in cn.region if cn.val in dom[i]]
    return sur, poss


def propager_count_interdiction(cn, dom):
    """Si `hi` cellules valent deja `val`, aucune autre ne le peut."""
    sur, poss = _count_etat(cn, dom)
    if len(sur) != cn.hi:
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


def propager_count_forcage(cn, dom):
    """Si seules `lo` cellules peuvent encore valoir `val`, toutes doivent."""
    sur, poss = _count_etat(cn, dom)
    if len(poss) != cn.lo:
        return False, False
    prog = False
    for i in poss:
        if dom[i] != {cn.val}:
            dom[i].clear()
            dom[i].add(cn.val)
            prog = True
    return prog, False


def propager_count(cn, dom):
    p1, c1 = propager_count_interdiction(cn, dom)
    if c1:
        return True, True
    p2, c2 = propager_count_forcage(cn, dom)
    return (p1 or p2), c2


# ---------- SUM ----------
#
# `SumRange(region, lo, hi, d)` : la somme des valeurs de la region est dans
# [lo, hi]. Meme famille de bornes que `Count`, donc meme gabarit a deux sens.
#
#   PLAFOND (borne `hi`) : une valeur est impossible si, meme en donnant aux
#     autres cellules leur MINIMUM, la somme depasse `hi`.
#   PLANCHER (borne `lo`) : une valeur est impossible si, meme en donnant aux
#     autres cellules leur MAXIMUM, la somme n'atteint pas `lo`.
#
# C'est la coherence aux bornes, rien de plus. Le raisonnement se lit sur les
# min/max des DOMAINES, ce qui le rend plus fort que `feasible()`, qui borne
# les cellules inconnues par `d-1` sans regarder ce qu'elles peuvent valoir.
#
# Ce qui n'est deliberement PAS fait : aucune recherche de sous-ensembles
# realisables (« quelles combinaisons somment exactement a lo »). Correcte mais
# exponentielle, et surtout elle resoudrait localement des configurations dont
# la difficulte est ce que le projet mesure. Meme motif que le rejet de Regin.


def _sum_domaine_vide(cn, dom):
    return any(not dom[i] for i in cn.region)


def propager_sum_plafond(cn, dom):
    """Borne `hi` : retire les valeurs TROP GRANDES."""
    if _sum_domaine_vide(cn, dom):
        return False, True
    mn = [min(dom[i]) for i in cn.region]
    total_min = sum(mn)
    prog = False
    for k, i in enumerate(cn.region):
        plafond = cn.hi - (total_min - mn[k])
        trop = [v for v in dom[i] if v > plafond]
        if not trop:
            continue
        for v in trop:
            dom[i].discard(v)
        prog = True
        if not dom[i]:
            return prog, True
    return prog, False


def propager_sum_plancher(cn, dom):
    """Borne `lo` : retire les valeurs TROP PETITES."""
    if _sum_domaine_vide(cn, dom):
        return False, True
    mx = [max(dom[i]) for i in cn.region]
    total_max = sum(mx)
    prog = False
    for k, i in enumerate(cn.region):
        plancher = cn.lo - (total_max - mx[k])
        trop = [v for v in dom[i] if v < plancher]
        if not trop:
            continue
        for v in trop:
            dom[i].discard(v)
        prog = True
        if not dom[i]:
            return prog, True
    return prog, False


def propager_sum(cn, dom):
    p1, c1 = propager_sum_plafond(cn, dom)
    if c1:
        return True, True
    p2, c2 = propager_sum_plancher(cn, dom)
    return (p1 or p2), c2


# ---------- NEQADJ ----------
#
# `NeqAdj(region)` : deux cellules consecutives DANS L'ORDRE DE LA REGION
# doivent differer.
#
# UNE SEULE regle : une cellule dont le domaine est reduit a `{v}` interdit `v`
# a ses VOISINES IMMEDIATES -- pas au reste de la region.
#
# LE PIEGE, et il est celui de T1 sous un autre habit : `NeqAdj` n'est PAS un
# `AllDiff`. Sur une region de trois cellules ou plus, les extremites peuvent
# parfaitement etre egales. Un propagateur qui retirerait `v` de toute la
# region serait faux des que `|region| >= 3`, et le cas est construit a la main
# dans canary3 pour cette raison.
#
# Audit de forme : un seul test, `len(dom[a]) == 1`, la forme admise.


def propager_neqadj(cn, dom):
    R = cn.region
    prog = False
    for k in range(len(R) - 1):
        for a, b in ((R[k], R[k + 1]), (R[k + 1], R[k])):
            if len(dom[a]) != 1:
                continue
            v = next(iter(dom[a]))
            if v not in dom[b]:
                continue
            dom[b].discard(v)
            prog = True
            if not dom[b]:
                return prog, True
    return prog, False


# ---------- MONO ----------
#
# `Mono(region)` : la suite est non decroissante le long de la region.
# `feasible()` ne verifie que les paires **assignees** ; sur une grille
# complete cela revient bien a la monotonie de toute la suite, et c'est contre
# les grilles completes que la propagation doit etre sure.
#
# DEUX SENS :
#   AVANT   : `dom[b]` ne peut contenir de valeur < min(dom[a])
#   ARRIERE : `dom[a]` ne peut contenir de valeur > max(dom[b])
#
# AUDIT DE FORME (invariant 14) : ce propagateur ne fait **aucune** lecture de
# forme. Il ne lit que `min(dom[i])`, `max(dom[i])` et l'appartenance -- donc
# il est **sur par construction** vis-a-vis des interactions. C'est le premier
# du chantier dans ce cas, et c'est verifiable par simple relecture.
#
# Une seule passe ne suffit pas sur une region de trois cellules ou plus : la
# contrainte se propage de proche en proche. Le point fixe est assure par
# `propager()`, qui reboucle tant qu'il y a progres.


def propager_mono_avant(cn, dom):
    """`dom[b]` >= min(dom[a]) pour chaque paire consecutive."""
    R = cn.region
    prog = False
    for k in range(len(R) - 1):
        a, b = R[k], R[k + 1]
        if not dom[a] or not dom[b]:
            return prog, True
        seuil = min(dom[a])
        trop = [v for v in dom[b] if v < seuil]
        if not trop:
            continue
        for v in trop:
            dom[b].discard(v)
        prog = True
        if not dom[b]:
            return prog, True
    return prog, False


def propager_mono_arriere(cn, dom):
    """`dom[a]` <= max(dom[b]) pour chaque paire consecutive."""
    R = cn.region
    prog = False
    for k in range(len(R) - 1, 0, -1):
        a, b = R[k - 1], R[k]
        if not dom[a] or not dom[b]:
            return prog, True
        seuil = max(dom[b])
        trop = [v for v in dom[a] if v > seuil]
        if not trop:
            continue
        for v in trop:
            dom[a].discard(v)
        prog = True
        if not dom[a]:
            return prog, True
    return prog, False


def propager_mono(cn, dom):
    p1, c1 = propager_mono_avant(cn, dom)
    if c1:
        return True, True
    p2, c2 = propager_mono_arriere(cn, dom)
    return (p1 or p2), c2


# ---------- contraintes BINAIRES : PAIRDIFF ----------
#
# `PairDiff(pairs, k, n)` : pour chaque paire (a, b), `|v_a - v_b| >= k`.
#
# Regle unique : la **coherence d'arc**. Une valeur `v` survit dans `dom[a]`
# s'il existe au moins un **support** `w` dans `dom[b]` avec `|v - w| >= k`.
# Sinon elle est impossible et part.
#
# AUDIT DE FORME (invariant 14) : aucune lecture de forme. Le support se teste
# par **appartenance**, valeur par valeur. Sur par construction, comme `Mono`.
#
# La regle s'applique aux deux bouts de chaque paire ; ce n'est pas « deux
# sens » au sens de `Count` ou `SumRange` -- c'est **une seule regle** appliquee
# symetriquement, donc elle ne releve pas de la condition de commit separe.


def _arc_consistance(pairs, compatible, dom):
    """Coherence d'arc sur une relation binaire quelconque.

    Ce helper est PARTAGE par `PairDiff` et `PairRatio`, et ce partage est
    volontaire : seule la relation differe. Il ne tombe pas sous l'invariant 10
    (duplications delibrees), qui protege la separation entre `feasible()` et
    la propagation, pas l'ecriture deux fois d'un meme parcours de paires.
    Le risque -- un bug du helper touche les deux propagateurs -- est couvert
    par les croisements, qui les testent l'un contre l'autre.
    """
    prog = False
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            if not dom[x] or not dom[y]:
                return prog, True
            sans = [v for v in dom[x]
                    if not any(compatible(v, w) for w in dom[y])]
            if not sans:
                continue
            for v in sans:
                dom[x].discard(v)
            prog = True
            if not dom[x]:
                return prog, True
    return prog, False


def propager_pairdiff(cn, dom):
    k = cn.k
    return _arc_consistance(cn.pairs, lambda v, w: abs(v - w) >= k, dom)


# ---------- contraintes BINAIRES : PAIRSTEP ----------
#
# `PairRatio(pairs, delta)` (kind `PAIRSTEP`) : pour chaque paire,
# `|v_a - v_b|` vaut 0 ou `delta`.
#
# Meme coherence d'arc que `PairDiff`, meme helper, autre relation.
#
# CE QUI CHANGE, ET C'EST LE POINT : la relation de `PairDiff` est **monotone**
# en `w` -- le meilleur support est toujours `min(dom[b])` ou `max(dom[b])` --
# donc un test aux bornes y serait exact. Celle-ci ne l'est **pas** : le seul
# support d'une valeur peut etre une valeur **interieure** du domaine. Tester
# aux bornes serait donc correct pour l'un et FAUX pour l'autre, alors que les
# deux propagateurs se ressemblent au point de partager leur helper.
# C'est exactement l'erreur que le partage invite, et `canary3` l'injecte.
#
# AUDIT DE FORME (invariant 14) : aucune. Sur par construction.


def propager_pairstep(cn, dom):
    delta = cn.delta
    return _arc_consistance(
        cn.pairs, lambda v, w: abs(v - w) in (0, delta), dom)


# ---------- orchestration ----------

PROPAGATEURS = {
    "ALLDIFF": propager_alldiff,
    "COUNT": propager_count,
    "SUM": propager_sum,
    "NEQADJ": propager_neqadj,
    "MONO": propager_mono,
    "PAIRDIFF": propager_pairdiff,
    "PAIRSTEP": propager_pairstep,
}


def propager(rs, dom):
    """Point fixe sur toutes les contraintes qui ont un propagateur.

    Les contraintes SANS propagateur sont ignorees en silence : c'est le regime
    normal pendant tout A, ou les propagateurs arrivent un par un. Une
    contrainte ignoree ne rend pas le resultat faux, seulement moins filtre.

    Retourne (progres, contradiction).
    """
    prog_total = False
    while True:
        prog = False
        for cn in rs.constraints:
            f = PROPAGATEURS.get(getattr(cn, "kind", None))
            if f is None:
                continue
            p, contra = f(cn, dom)
            prog = prog or p
            prog_total = prog_total or p
            if contra:
                return prog_total, True
        if not prog:
            return prog_total, False
