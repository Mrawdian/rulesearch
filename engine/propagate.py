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
from dsl2 import neighbors4


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


# ---------- NOTRIPLE ----------
#
# `NoTriple(region)` : pas trois valeurs identiques consecutives dans la region.
#
# Regle unique : dans une fenetre (a, b, c) de trois cellules consecutives, si
# DEUX d'entre elles sont reduites au meme singleton `{v}`, la troisieme ne
# peut pas valoir `v`. Les trois positions sont symetriques -- ce n'est pas
# « trois regles » mais une seule, appliquee aux trois choix de la cellule
# restante.
#
# LE PIEGE : `NoTriple` n'est PAS un `NeqAdj`. **Deux** valeurs identiques
# consecutives sont parfaitement licites. Un propagateur qui interdirait `v` a
# la voisine d'une cellule valant `v` serait faux. C'est le meme piege que
# `NeqAdj` traite comme un `AllDiff`, d'un cran plus fin : appliquer une regle
# a la mauvaise granularite.
#
# AUDIT DE FORME (invariant 14) : une seule lecture, `len(dom[i]) == 1`, la
# forme admise.
#
# 14BIS : les fenetres sont les triplets **consecutifs de la region**, donc un
# objet **FIXE par la contrainte** -- il ne depend pas des domaines courants et
# ne bouge pas quand ils retrecissent. L'inference porte cellule par cellule
# sur un index fixe. **14 suffit, 14bis n'est pas engage.**


def _fenetres_triples(region):
    return [(region[k], region[k + 1], region[k + 2])
            for k in range(len(region) - 2)]


def propager_notriple(cn, dom):
    prog = False
    for fenetre in _fenetres_triples(cn.region):
        for i in range(3):
            cible = fenetre[i]
            autres = [fenetre[j] for j in range(3) if j != i]
            a, b = autres
            if len(dom[a]) != 1 or len(dom[b]) != 1:
                continue
            va = next(iter(dom[a]))
            if va != next(iter(dom[b])):
                continue
            if va not in dom[cible]:
                continue
            dom[cible].discard(va)
            prog = True
            if not dom[cible]:
                return prog, True
    return prog, False


# ---------- NOSQUARE ----------
#
# `NoSquare(n, val)` : aucun carre 2x2 monochrome de valeur `val`.
#
# Regle unique : dans une fenetre 2x2, si TROIS cellules sont reduites au
# singleton `{val}`, la quatrieme ne peut pas valoir `val`.
#
# LES FENETRES SONT CONSTRUITES ICI, A PARTIR DE `n`. La contrainte declare
# `region = toute la grille`, ce qui est **sur-inclusif mais correct** : cela
# ne rend `touch[i]` que trop large, jamais trop etroit. **`dsl2.py` n'est pas
# modifie** -- son diff vide reste la preuve mecanique que `feasible()` est
# conservee pendant tout A, et cette preuve vaut plus qu'une optimisation
# d'indexation. Voir DECISIONS.md.
#
# AUDIT DE FORME (invariant 14) : une seule lecture, `dom[i] == {val}`, la
# forme admise.
#
# 14BIS : les fenetres se calculent depuis `cn.n` **seul** -- elles ne
# regardent jamais `dom`. Objet FIXE. C'est verifie **mecaniquement** par
# `canary3` via `objet_inference()` ci-dessous, pas seulement affirme.


def _fenetres_carres(cn):
    n = cn.n
    return [(r * n + c, r * n + c + 1, (r + 1) * n + c, (r + 1) * n + c + 1)
            for r in range(n - 1) for c in range(n - 1)]


def propager_nosquare(cn, dom):
    val = cn.val
    cible_val = {val}
    prog = False
    for fenetre in _fenetres_carres(cn):
        surs = [i for i in fenetre if dom[i] == cible_val]
        if len(surs) != 3:
            continue
        reste = [i for i in fenetre if i not in surs]
        cible = reste[0]
        if val not in dom[cible]:
            continue
        dom[cible].discard(val)
        prog = True
        if not dom[cible]:
            return prog, True
    return prog, False


# ---------- CONNECTED ----------
#
# `Connected(n, val)` : les cellules valant `val` forment UNE composante
# connexe (4-connexite).
#
# ===================== LA PREUVE, AVANT LE CODE =====================
#
# Notations, a l'etat de domaines courant :
#   P = { i : val dans dom[i] }        les cellules POSSIBLEMENT `val`
#   F = { i : dom[i] == {val} }        les cellules CERTAINEMENT `val`
#   F inclus dans P.
#
# Soit `sigma` une solution compatible avec les domaines, et
# S = { i : sigma[i] = val }.
#
#   (1) S est inclus dans P. C'est la SUR-APPROXIMATION (invariant 14ter) :
#       les domaines ne font qu'ENCADRER les valeurs possibles, donc
#       sigma[i] = val implique val dans dom[i].
#   (2) `Connected` impose que S soit connexe pour la 4-connexite.
#   (3) Si s appartient a F, alors sigma[s] = val, donc s appartient a S.
#
# REGLE DE RETRAIT. Soit A l'ensemble des cellules accessibles depuis `s` en ne
# traversant que des cellules de P. Pour tout i de S, (2) et (3) donnent un
# chemin de i a s ENTIEREMENT dans S, donc -- par (1) -- entierement dans P.
# Donc S est inclus dans A. Contraposee : i hors de A implique sigma[i] != val.
# **Le retrait de `val` hors de A est sur.**
#
# REGLE DE CONTRADICTION. Si une cellule de F est hors de A, alors deux
# cellules certainement `val` ne peuvent pas etre reliees dans P : aucune
# solution n'existe. **La contradiction est sure.**
#
# CONDITION D'AMORCAGE, ET C'EST LE PIEGE. Il faut |F| >= 1. Sans ancre
# CERTAINE, la composante peut etre n'importe ou -- ou vide, `feasible()`
# acceptant zero ou une cellule `val`. Un propagateur qui retirerait a partir
# d'une cellule seulement POSSIBLE serait faux. `canary3` injecte exactement
# ce bug.
#
# 14TER : l'objet parcouru -- le graphe induit sur P -- est INDUIT par les
# domaines, pas fixe. Il est declare dans `SURETE_OBJET_INDUIT` avec les deux
# regles ci-dessus, et SEULEMENT elles.
#
# ---------- LE FORCAGE PAR SOMMET SEPARATEUR (articulation) ----------
#
# OUVERT LE 27/08/2026, apres avoir ete ferme deux fois. Ce qui a change n'est
# pas le critere de reouverture -- il portait sur le DEBIT -- mais la QUESTION.
# Sous « quelle est la resistance a T0 ? », une regle forte DISSOUT ce qu'on
# mesure et l'ecarter protege l'instrument. Sous « cette resistance est-elle
# recuperable par propagation LOCALE ? », la regle la plus forte n'est plus une
# menace : elle EST le controle. Voir DECISIONS.md.
#
# PREUVE. Memes notations que ci-dessus : sigma une solution compatible avec
# les domaines, S = { i : sigma[i] = val }, P les passables, F les certaines.
# On a (1) S inclus dans P, (2) S connexe, (3) F inclus dans S.
#
# Soient a et b deux elements DISTINCTS de F, et v une cellule de P. Par (3),
# a et b sont dans S ; par (2), il existe un chemin de a a b entierement dans
# S, donc -- par (1) -- entierement dans P. Si TOUT chemin de a a b dans P
# passe par v, ce chemin-la y passe aussi, donc v appartient a S :
# **sigma[v] = val**. Le forcage `dom[v] := {val}` est sur.
#
# C'est le meme argument que le retrait, et il vit dans la meme relaxation
# « chaque cellule peut prendre n'importe quelle valeur de son domaine »
# (invariant 14ter) : il n'utilise les domaines que comme SUR-APPROXIMATION.
#
# CONDITION D'AMORCAGE, plus forte que pour le retrait : il faut |F| >= 2.
# Avec UNE SEULE ancre, S peut se reduire a {a} et aucun sommet n'est
# traverse. Un forcage sur ancre unique est FAUX ; `canary3` injecte
# exactement ce bug.
#
# PRECONDITION NON NEGOCIABLE : toutes les ancres doivent DEJA etre reliees a
# `a` dans P. Sinon le systeme est infaisable, tout sommet « separe »
# vacuement, et la regle forcerait la grille entiere. Le retrait par
# inaccessibilite tourne AVANT et rend `contra` dans ce cas : la precondition
# est donc etablie par construction, et non supposee.
#
# ANCRAGE SUR UNE SEULE ANCRE, ET CE N'EST PAS UNE PERTE. On ne teste que les
# paires (a, b) avec a = certaines[0]. Si v separe b de c, alors apres retrait
# de v les composantes de a, b, c ne peuvent pas etre toutes egales : v separe
# donc a de b, ou a de c. **Aucun sommet separateur n'echappe a l'ancrage
# unique.** Cout ramene de |F|^2.|P|^2 a |F|.|P|^2.
#
# MONOTONIE, verifiee dans preuves/monotonie_connected.py : P' inclus dans P
# implique que l'ensemble des cellules forcees ne peut que CROITRE. Ce n'est
# pas requis pour la surete -- la sur-approximation suffit -- mais cela ferme
# la reserve de 14bis sur un objet INDUIT non monotone.
#
# DRAPEAU PAR DEFAUT A False. La mesure de controle l'active a part. Le
# propagateur par defaut reste BYTE POUR BYTE celui qui a produit la mesure du
# 26/08 : les deux bras sont comparables sans qu'il faille en discuter.

ARTICULATION = False


def _accessibles(passables, depart, n):
    if depart not in passables:
        return set()
    vus, pile = {depart}, [depart]
    while pile:
        x = pile.pop()
        for y in neighbors4(x, n):
            if y in passables and y not in vus:
                vus.add(y)
                pile.append(y)
    return vus


def propager_connected(cn, dom):
    val, n = cn.val, cn.n
    passables = set(i for i in cn.region if val in dom[i])
    certaines = [i for i in cn.region if dom[i] == {val}]
    if not certaines:
        # PAS D'ANCRE : aucun retrait n'est justifie. Ne rien conclure quand
        # on ne peut pas conclure.
        return False, False

    depart = certaines[0]
    vus = {depart}
    pile = [depart]
    while pile:
        x = pile.pop()
        for y in neighbors4(x, n):
            if y in passables and y not in vus:
                vus.add(y)
                pile.append(y)

    for f in certaines:
        if f not in vus:
            return False, True          # deux `val` certaines non reliables

    prog = False
    for i in passables:
        if i in vus:
            continue
        dom[i].discard(val)
        prog = True
        if not dom[i]:
            return prog, True

    if ARTICULATION and len(certaines) >= 2:
        # A ce point, toutes les ancres sont reliees a `depart` dans P : la
        # boucle ci-dessus a rendu `contra` sinon. La precondition tient.
        passables = set(i for i in cn.region if val in dom[i])
        autres = certaines[1:]
        for v in passables:
            if v == depart or dom[v] == {val}:
                continue
            joignables = _accessibles(passables - {v}, depart, n)
            if any(b not in joignables for b in autres):
                # `val` est dans dom[v] puisque v est passable : ce forcage ne
                # peut pas vider un domaine.
                dom[v] = {val}
                prog = True

    return prog, False


# ---------- 14BIS : l'objet d'inference est-il FIXE ou INDUIT ? ----------
#
# L'invariant 14 couvre les inferences dont l'entree est l'appartenance d'une
# valeur a un domaine. **14bis** -- non tranche -- porte sur celles dont
# l'entree est une propriete d'un objet construit a partir de PLUSIEURS
# domaines et non monotone sous retrecissement.
#
# Le critere operatoire se teste : **l'objet sur lequel porte l'inference
# depend-il des domaines courants ?** Chaque propagateur declare ici l'objet
# qu'il parcourt. `canary3` verifie MECANIQUEMENT que cet objet est identique
# avant et apres des rognages arbitraires.
#
# Attendu : les neuf propagateurs actuels sont FIXES. `Connected` est INDUIT --
# ses sommets passables sont ceux dont le domaine CONTIENT `val`.
#
# ETRE INDUIT N'EST PAS ETRE DANGEREUX (invariant 14ter). Ce qui rend une
# inference sure est qu'elle n'utilise les domaines que comme
# SUR-APPROXIMATION des valeurs possibles -- donc qu'elle soit valide dans la
# relaxation « chaque cellule peut prendre n'importe quelle valeur de son
# domaine ». Un objet induit CONSTRUIT PAR APPARTENANCE satisfait cela.
#
# Le test rend donc TROIS issues et non deux : FIXE, INDUIT-PROUVE,
# INDUIT-SANS-PREUVE. Seule la troisieme interdit.

# Regles dont l'objet d'inference est INDUIT par les domaines, mais dont la
# SURETE EST PROUVEE (invariant 14ter). La valeur nomme la ou les regles
# couvertes : une regle non nommee ici n'est PAS couverte, meme sur la meme
# contrainte. Voir DECISIONS.md, 26/08/2026.
SURETE_OBJET_INDUIT = {
    # NE NOMMER QUE LES REGLES REELLEMENT ECRITES. Le forcage par sommet
    # separateur y figure depuis le 27/08/2026 parce qu'il est ECRIT, et non
    # parce qu'il est prouve : il l'etait deja quand il n'y avait pas sa place.
    "CONNECTED": ("retrait par inaccessibilite depuis une cellule certainement "
                  "`val` ; detection de contradiction ; forcage des sommets "
                  "separant deux cellules certainement `val` (drapeau "
                  "ARTICULATION, defaut False). Valides dans la relaxation : "
                  "toute solution a son ensemble de cellules `val` inclus dans "
                  "P et connexe."),
}


def statut_objet(kind, fixe):
    """Trois issues, pas deux (invariant 14ter) :
      'FIXE'            -- objet independant des domaines, invariant 14 suffit
      'INDUIT-PROUVE'   -- objet induit, surete etablie et referencee
      'INDUIT-SANS-PREUVE' -- INTERDIT tant que la preuve n'est pas ecrite
    """
    if fixe:
        return "FIXE"
    if kind in SURETE_OBJET_INDUIT:
        return "INDUIT-PROUVE"
    return "INDUIT-SANS-PREUVE"


def objet_inference(cn, dom):
    """Objet parcouru par le propagateur de `cn`, sous l'etat `dom`."""
    k = getattr(cn, "kind", None)
    if k == "CONNECTED":
        # INDUIT : les cellules passables sont celles dont le domaine CONTIENT
        # `val`. L'objet change donc quand les domaines retrecissent.
        return tuple(i for i in cn.region if cn.val in dom[i])
    if k == "NOTRIPLE":
        return tuple(_fenetres_triples(cn.region))
    if k == "NOSQUARE":
        return tuple(_fenetres_carres(cn))
    if k in ("PAIRDIFF", "PAIRSTEP"):
        return tuple(tuple(p) for p in cn.pairs)
    if k in ("ALLDIFF", "COUNT", "SUM", "NEQADJ", "MONO"):
        return tuple(cn.region)
    return None


# ---------- orchestration ----------

PROPAGATEURS = {
    "ALLDIFF": propager_alldiff,
    "COUNT": propager_count,
    "SUM": propager_sum,
    "NEQADJ": propager_neqadj,
    "MONO": propager_mono,
    "PAIRDIFF": propager_pairdiff,
    "PAIRSTEP": propager_pairstep,
    "NOTRIPLE": propager_notriple,
    "NOSQUARE": propager_nosquare,
    "CONNECTED": propager_connected,
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
