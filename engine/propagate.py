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


# ---------- orchestration ----------

PROPAGATEURS = {
    "ALLDIFF": propager_alldiff,
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
