#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONTROLE BLOQUANT : OU L'ARTICULATION MORD-ELLE ?

Le controle de circularite se lit sur `r`, la fraction du residu que
l'articulation recupere sur le sous-groupe `connect_avec_CONNECTED`. Un `r`
faible n'y a de sens QUE si la regle s'y applique reellement.

    Si le forcage se concentrait sur les systemes SANS `Connected`, un `r`
    faible sur le sous-groupe ne dirait rien du tout : ce serait le garde de
    non-redondance qui echoue, une strate plus bas, en passant inapercu parce
    qu'il rendrait le chiffre qu'on espere.

C'est donc un CONTROLE BLOQUANT, au meme titre que les solutions fausses : il
se lit AVANT `r`, et s'il ne passe pas, `r` n'est pas lu.

Trois groupes, la meme partition que `gain_strates` :
    static-ref, connect_sans_CONNECTED, connect_avec_CONNECTED
"""
import collections
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RACINE, "engine"))
sys.path.insert(0, RACINE)
sys.path.insert(0, HERE)

from rulesearch import UNASSIGNED, random_solution, minimal_clues
import propagate as PG
from propagate import propager_connected
from t0_legacy import candidates_legacy
from gain_propagation import configs_journalisees, reconstruire

PAR_GROUPE = 500          # plafond par groupe, tirage ALEATOIRE (invariant 15)
INSTANCES = 4


def domaines_fc(rs, g):
    return [{g[i]} if g[i] != UNASSIGNED else set(candidates_legacy(rs, g, i))
            for i in range(rs.n * rs.n)]


def sonde(rs, C, graine):
    """Compte, sur des puzzles reels, ou la regle PEUT conclure et ou elle
    conclut EFFECTIVEMENT. On ne mesure pas la resistance ici : on mesure
    l'APPLICABILITE de la regle, ce dont `r` ne rend pas compte."""
    random.seed(graine)
    cns = [c for c in rs.constraints if getattr(c, "kind", None) == "CONNECTED"]
    C["systemes"] += 1
    if not cns:
        return
    for _ in range(INSTANCES):
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        dom = domaines_fc(rs, list(puz))
        for cn in cns:
            C["appels"] += 1
            F = [i for i in cn.region if dom[i] == {cn.val}]
            if len(F) < 2:
                continue
            C["precondition"] += 1
            avant = [set(x) for x in dom]
            PG.ARTICULATION = True
            try:
                propager_connected(cn, dom)
            finally:
                PG.ARTICULATION = False
            forces = sum(1 for i in range(len(dom))
                         if dom[i] == {cn.val} and avant[i] != {cn.val})
            if forces:
                C["appels_qui_forcent"] += 1
                C["cellules_forcees"] += forces
            dom = avant


def main():
    tags = ["static-ref", "connect"]
    trouve = configs_journalisees(tags, 3)
    groupes = collections.defaultdict(list)
    for cle, idxs in trouve.items():
        rng = random.Random(4242 + hash(cle) % 1000)
        liste = sorted(idxs)
        if len(liste) > 40:
            liste = rng.sample(liste, 40)
        for _idx, rs in reconstruire(cle, set(liste)).items():
            if cle[0] == "static-ref":
                groupes["static-ref"].append(rs)
            else:
                kinds = {getattr(c, "kind", None) for c in rs.constraints}
                groupes["connect_avec_CONNECTED" if "CONNECTED" in kinds
                        else "connect_sans_CONNECTED"].append(rs)

    print("CONTROLE BLOQUANT : LOCALISATION DU FORCAGE  (d=3, n=4)", flush=True)
    print(flush=True)
    C = {}
    ordre = ("static-ref", "connect_sans_CONNECTED", "connect_avec_CONNECTED")
    for nom in ordre:
        pool = groupes[nom]
        # TIRAGE ALEATOIRE, JAMAIS UN PREFIXE (invariant 15).
        rng = random.Random(77777)
        if len(pool) > PAR_GROUPE:
            pool = rng.sample(pool, PAR_GROUPE)
        C[nom] = collections.Counter()
        for i, rs in enumerate(pool):
            sonde(rs, C[nom], 9200 + i)
        print("  %-24s systemes=%-5d appels=%-6d precond=%-6d "
              "forcent=%-6d cellules=%-6d"
              % (nom, C[nom]["systemes"], C[nom]["appels"],
                 C[nom]["precondition"], C[nom]["appels_qui_forcent"],
                 C[nom]["cellules_forcees"]), flush=True)

    total = sum(C[n]["cellules_forcees"] for n in ordre)
    cible = C["connect_avec_CONNECTED"]["cellules_forcees"]
    print(flush=True)
    print("  cellules forcees au total          : %d" % total, flush=True)
    print("  dont sur connect_avec_CONNECTED    : %d" % cible, flush=True)
    if not total:
        print(flush=True)
        print("  BLOQUANT : l'articulation ne force RIEN nulle part.", flush=True)
        print("  `r` ne serait pas une mesure de resistance mais une mesure", flush=True)
        print("  d'inertie. NE PAS LIRE r.", flush=True)
        sys.exit(2)
    print("  part                               : %.1f %%"
          % (100.0 * cible / total), flush=True)
    print(flush=True)
    if not cible:
        print("  BLOQUANT : le forcage a lieu AILLEURS QUE sur le sous-groupe", flush=True)
        print("  ou `r` se lit. Un r faible y serait de l'inertie deguisee en", flush=True)
        print("  resistance -- le garde de non-redondance qui echoue une", flush=True)
        print("  strate plus bas, et qui passe inapercu parce qu'il rend le", flush=True)
        print("  chiffre qu'on espere. NE PAS LIRE r.", flush=True)
        sys.exit(2)
    print("  CONTROLE PASSE : la regle s'applique bien la ou `r` se lit.", flush=True)
    print("  %d appels y atteignent la precondition, %d y forcent."
          % (C["connect_avec_CONNECTED"]["precondition"],
             C["connect_avec_CONNECTED"]["appels_qui_forcent"]), flush=True)


if __name__ == "__main__":
    main()
