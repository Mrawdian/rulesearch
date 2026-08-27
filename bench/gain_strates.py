#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTROLE DU RESULTAT FAVORABLE (garde 2, regime du dixieme cas).

La prediction -- gain FORT sur `static-ref`, FAIBLE sur `connect` -- est
confirmee : 0,699 contre 0,237, p = 0,0005. **Un resultat favorable merite
exactement le controle qu'aurait recu son contraire, et il le recoit moins
souvent.** Ce script est ce controle.

DEUX CONFONDANTS A ECARTER, nommes AVANT de les mesurer :

1. LA COMPOSITION. `connect` et `static` n'ont ni les memes contraintes ni les
   memes densites d'indices. La resistance a T0 avait DEJA ete confondue par
   `clue_frac` une fois dans ce projet. Si `connect` a mecaniquement moins de
   cellules recuperables, le gain plus faible ne dit rien sur la
   decomposabilite.

2. « CONNECTED RESISTE » vs « MON PROPAGATEUR NE FAIT PAS GRAND-CHOSE ». Le
   diagnostic donne 77 retraits pour CONNECTED contre 358 pour PAIRSTEP. Il
   agit, mais peu. La difference entre les deux lectures est exactement celle
   que le chantier a passe la journee a confondre.

   LE CONTROLE DECISIF : a l'INTERIEUR du tag `connect`, comparer les systemes
   QUI PORTENT `Connected` a ceux qui n'en portent pas. Les seconds sont
   relationnels purs -- PairDiff, PairRatio -- donc localement decomposables.
   Si le gain faible tenait a la faiblesse du propagateur ou a la composition
   du tag, les deux sous-groupes se ressembleraient. S'il tient a
   `Connected` lui-meme, ils divergeront, ET les relationnels purs
   ressembleront a `static`.
"""
import argparse
import collections
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(HERE)
ENGINE = os.environ.get("RS_ENGINE") or os.path.join(RACINE, "engine")
sys.path.insert(0, ENGINE)
sys.path.insert(0, RACINE)
sys.path.insert(0, HERE)

from rulesearch import UNASSIGNED, random_solution, minimal_clues
from t0_legacy import resistance as resistance_t0
from gain_propagation import (resistance_prop, configs_journalisees,
                              reconstruire, permutation)


def mesures_instances(rs, instances, graine):
    """Une ligne PAR INSTANCE : les bruts, plus la densite d'indices."""
    random.seed(graine)
    n2 = rs.n * rs.n
    out = []
    for _ in range(instances):
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        inc, left_t0 = resistance_t0(rs, puz)
        _, left_pr = resistance_prop(rs, puz)
        if left_pr > left_t0:
            raise AssertionError("gain negatif : bug, pas resultat.")
        out.append({
            "inc": inc,
            "t0": left_t0,
            "pr": left_pr,
            "clue_frac": (n2 - inc) / float(n2),
        })
    return out


def agrege(lignes):
    t0 = sum(l["t0"] for l in lignes)
    pr = sum(l["pr"] for l in lignes)
    inc = sum(l["inc"] for l in lignes)
    if not t0:
        return None
    return {"n": len(lignes), "inc": inc, "t0": t0, "pr": pr,
            "gain_agrege": (t0 - pr) / float(t0),
            "resistance_t0": t0 / float(inc) if inc else 0.0}


def gains_par_ligne(lignes):
    return [(l["t0"] - l["pr"]) / float(l["t0"]) for l in lignes if l["t0"]]


def afficher(nom, lignes):
    a = agrege(lignes)
    if a is None:
        print("  %-34s aucune resistance a recuperer" % nom)
        return None
    g = gains_par_ligne(lignes)
    print("  %-34s inst=%-5d inconnues=%-7d T0=%-7d prop=%-7d "
          "resist=%.3f gain_agr=%.3f gain_moy=%.3f"
          % (nom, a["n"], a["inc"], a["t0"], a["pr"], a["resistance_t0"],
             a["gain_agrege"], sum(g) / len(g) if g else float("nan")))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=3)
    ap.add_argument("--systemes", type=int, default=60)
    ap.add_argument("--instances", type=int, default=5)
    a = ap.parse_args()
    tags = ["static-ref", "connect"]

    trouve = configs_journalisees(tags, a.d)
    par_tag = collections.defaultdict(list)
    for cle, idxs in trouve.items():
        rng = random.Random(9091 + hash(cle) % 997)
        liste = sorted(idxs)
        if len(liste) > a.systemes:
            liste = rng.sample(liste, a.systemes)   # jamais un prefixe
        for _idx, rs in reconstruire(cle, set(liste)).items():
            par_tag[cle[0]].append(rs)

    print("CONTROLE DU RESULTAT FAVORABLE  d=%d  instances=%d" % (a.d, a.instances))
    print()
    lignes = {"static-ref": [], "connect_avec_CONNECTED": [],
              "connect_sans_CONNECTED": []}
    for t in tags:
        for i, rs in enumerate(par_tag[t]):
            kinds = {getattr(c, "kind", None) for c in rs.constraints}
            if t == "static-ref":
                cle = "static-ref"
            else:
                cle = ("connect_avec_CONNECTED" if "CONNECTED" in kinds
                       else "connect_sans_CONNECTED")
            try:
                lignes[cle].extend(mesures_instances(rs, a.instances, 808 + i))
            except AssertionError as e:
                print("ARRET :", e)
                sys.exit(1)

    print("-- par groupe --")
    g = {}
    for cle in ("static-ref", "connect_sans_CONNECTED",
                "connect_avec_CONNECTED"):
        g[cle] = afficher(cle, lignes[cle]) or []

    print()
    print("-- LE CONTROLE DECISIF : a l'interieur du tag `connect` --")
    if g["connect_sans_CONNECTED"] and g["connect_avec_CONNECTED"]:
        p = permutation(g["connect_sans_CONNECTED"], g["connect_avec_CONNECTED"])
        m1 = sum(g["connect_sans_CONNECTED"]) / len(g["connect_sans_CONNECTED"])
        m2 = sum(g["connect_avec_CONNECTED"]) / len(g["connect_avec_CONNECTED"])
        print("  sans CONNECTED %.3f  vs  avec CONNECTED %.3f   p = %.4f"
              % (m1, m2, p))
        print("  Meme tag, meme generateur, memes familles de contraintes :")
        print("  la composition du tag ne peut PAS expliquer un ecart ici.")
    else:
        print("  INDETERMINE : un des deux sous-groupes est vide.")

    if g["static-ref"] and g["connect_sans_CONNECTED"]:
        p = permutation(g["static-ref"], g["connect_sans_CONNECTED"])
        m1 = sum(g["static-ref"]) / len(g["static-ref"])
        m2 = sum(g["connect_sans_CONNECTED"]) / len(g["connect_sans_CONNECTED"])
        print()
        print("  static-ref %.3f  vs  connect SANS CONNECTED %.3f   p = %.4f"
              % (m1, m2, p))
        print("  Si ces deux-la se ressemblent, c'est `Connected` qui porte")
        print("  l'ecart, et non le tag.")

    print()
    print("-- CONFONDANT 1 : densite d'indices, stratifiee --")
    for cle in ("static-ref", "connect_sans_CONNECTED",
                "connect_avec_CONNECTED"):
        L = sorted(lignes[cle], key=lambda x: x["clue_frac"])
        if len(L) < 30:
            print("  %-34s trop peu d'instances pour stratifier" % cle)
            continue
        t = len(L) // 3
        for nom, sous in (("bas", L[:t]), ("median", L[t:2 * t]),
                          ("haut", L[2 * t:])):
            afficher("%s / clue_frac %s" % (cle, nom), sous)


if __name__ == "__main__":
    main()
