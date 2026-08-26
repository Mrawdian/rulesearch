"""
T0 HISTORIQUE — MODULE GELE. NE JAMAIS MODIFIER.

Ce fichier fige la definition de T0 telle qu'elle existait le 2026-08-26,
avant l'ouverture du chantier A (etat de candidats explicite). Il est la
reference de la **metrique acquise** du projet, la resistance a T0 :

    resistance = t0_left / t0_unknown

RAISON DU GEL, et elle n'est pas la comparabilite.

La resistance a T0 mesure la non-localite d'une contrainte **RELATIVEMENT A UN
PROPAGATEUR DONNE**. Renforcer le propagateur deplace la frontiere qu'on
mesure. Un T0 plus fort resoudrait davantage de systemes a connectivite, donc
mesurerait **moins bien exactement ce qu'il doit mesurer**. Le propagateur de
reference doit donc etre gele **par nature**, pas par commodite : ce n'est pas
une precaution d'archivage, c'est la definition de l'instrument.

Le T0 fige ici est un FORWARD-CHECKING : une valeur est candidate si, une fois
posee, toutes les contraintes touchant la cellule restent faisables **compte
tenu des seules cellules deja assignees**. Il ne regarde pas les domaines des
autres cellules. C'est precisement ce que la propagation du chantier A rendra
plus fort — et c'est pourquoi elle ne doit pas servir a cette mesure.

CE QUE CE GEL NE PROTEGE PAS A LUI SEUL
---------------------------------------
Ce module appelle `rs.feasible(g, changed=i)`. Son comportement depend donc
aussi des methodes `feasible()` des contraintes, qui vivent ailleurs. Figer ce
fichier ne suffit pas : il faut que la SEMANTIQUE de `feasible()` reste
inchangee.

C'est `canary/canary8.py` qui verrouille l'ensemble, en comparant les valeurs
produites ici a un **corpus de reference aux valeurs attendues figees**
(`canary/t0_reference.json`). Il ne compare pas a du code courant — qui va
changer — mais a des nombres. Toute divergence signale qu'on a touche a ce
qu'on ne devait pas, que ce soit ici ou dans une contrainte.

CONTRAINTE SUR LE CHANTIER A : `feasible()` doit etre CONSERVEE telle quelle.
La propagation sur domaines s'ajoute **a cote** (`propagate(dom)`), elle ne
remplace pas `feasible(g)`.
"""
from rulesearch import UNASSIGNED


def candidates_legacy(rs, g, i):
    """
    Valeurs possibles pour la cellule i — forward-checking, version 2026-08-26.
    Copie figee de `deduction.candidates`. NE PAS SYNCHRONISER avec elle.
    """
    out = []
    for v in range(rs.d):
        g[i] = v
        if rs.feasible(g, changed=i):
            out.append(v)
    g[i] = UNASSIGNED
    return out


def apply_T0_legacy(rs, g):
    """Une passe de naked single. Copie figee de `deduction.apply_T0`."""
    prog = False
    for i in range(rs.n * rs.n):
        if g[i] != UNASSIGNED:
            continue
        c = candidates_legacy(rs, g, i)
        if not c:
            return prog, True
        if len(c) == 1:
            g[i] = c[0]
            prog = True
    return prog, False


def saturate_T0_legacy(rs, puzzle):
    """Sature T0 SEUL jusqu'au point fixe. Rend la grille obtenue."""
    g = list(puzzle)
    while True:
        prog, contra = apply_T0_legacy(rs, g)
        if contra or not prog:
            return g


def resistance(rs, puzzle):
    """
    Les deux BRUTS de la metrique acquise, jamais le ratio :

        (cases inconnues du puzzle initial, cases restantes apres T0 seul)

    Le ratio n'est pas journalise : une normalisation peut changer — elle a
    deja change une fois — et un ratio journalise ne se recalcule pas.
    """
    g = saturate_T0_legacy(rs, puzzle)
    inconnues = sum(1 for x in puzzle if x == UNASSIGNED)
    restantes = sum(1 for x in g if x == UNASSIGNED)
    return inconnues, restantes
