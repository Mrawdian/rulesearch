#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gain_propagation = (resistance_T0 - resistance_prop) / resistance_T0

CE QUE CETTE MESURE TESTE. Des propagateurs locaux plus forts RECUPERENT la
resistance d'un systeme localement decomposable, et pas celle d'un systeme qui
ne l'est pas -- par definition. C'est un test direct de l'hypothese centrale,
et il n'exige PAS n=5 : c'est la profondeur qui l'exigeait, pas la
decomposabilite.

PREDICTION, ecrite et poussee AVANT que ceci ne tourne (DECISIONS.md) :
    gain FORT sur `static-ref`, gain FAIBLE sur `connect`.

POURQUOI LA SATURATION FORTE EST UN FILTRE ET NON UN REMPLACEMENT. Les
propagateurs omettent deliberement les detections que `feasible()` fait
(invariant 21). Une saturation qui les REMPLACE serait parfois plus FAIBLE que
T0, le gain deviendrait negatif, et la mesure ne voudrait rien dire. Ici :
propagation d'abord, puis `apply_T0_legacy` -- **le T0 GELE lui-meme**, donc
la saturation forte est **>= la reference par construction**, et
`gain >= 0` toujours.

AUCUN BRANCHEMENT. Ce fichier est hors de `engine/` : `dsl_hash` ne bouge pas,
`t0_legacy` reste la reference de la serie, la production n'est pas touchee.
"""
import argparse
import collections
import json
import glob
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(HERE)
ENGINE = os.environ.get("RS_ENGINE") or os.path.join(RACINE, "engine")
sys.path.insert(0, ENGINE)
sys.path.insert(0, RACINE)

from rulesearch import UNASSIGNED, random_solution, minimal_clues
from propagate import domaines, propager
import propagate as PG
from t0_legacy import (apply_T0_legacy, candidates_legacy,
                       resistance as resistance_t0)
import run as RUN


# ---------- la saturation forte : propagation EN FILTRE devant T0 ----------

def domaines_fc(rs, g):
    """Domaines apres FORWARD-CHECKING gele : pour chaque cellule libre, les
    valeurs que `feasible()` accepte. C'est la borne basse -- exactement ce que
    `t0_legacy` sait, et rien de plus."""
    return [{g[i]} if g[i] != UNASSIGNED else set(candidates_legacy(rs, g, i))
            for i in range(rs.n * rs.n)]


def resistance_prop(rs, puzzle, articulation=False):
    """Enveloppe : pose ET RESTAURE le drapeau `ARTICULATION`.

    Le forcage par sommet separateur (27/08/2026) est active ici et nulle part
    ailleurs. La restauration en `finally` est ce qui garantit qu'aucune fuite
    n'atteint le bras de reference, qui doit rester BYTE POUR BYTE celui du
    26/08 -- sans quoi les deux bras ne seraient pas comparables, et le
    controle de circularite ne controlerait rien.
    """
    ancien = PG.ARTICULATION
    PG.ARTICULATION = articulation
    try:
        return _resistance_prop(rs, puzzle)
    finally:
        PG.ARTICULATION = ancien


def _resistance_prop(rs, puzzle):
    """(inconnues, restantes) apres saturation par un propagateur local PLUS
    FORT : forward-checking gele, PUIS propagation sur ces domaines.

    T0 gele revient a « poser les singletons de `candidates_legacy` » : cette
    saturation le SUBSUME donc, et `gain >= 0` par construction. Tout ce qui
    depasse vient de `propager`, c'est-a-dire de A.
    """
    n2 = rs.n * rs.n
    g = list(puzzle)
    while True:
        dom = domaines_fc(rs, g)
        if any(not dom[i] for i in range(n2)):
            break
        _, contra = propager(rs, dom)
        if contra:
            break
        pose = False
        for i in range(n2):
            if g[i] == UNASSIGNED and len(dom[i]) == 1:
                g[i] = next(iter(dom[i]))
                pose = True
        if not pose:
            break
    inconnues = sum(1 for x in puzzle if x == UNASSIGNED)
    restantes = sum(1 for x in g if x == UNASSIGNED)
    return inconnues, restantes


# ---------- reconstruction des systemes journalises ----------

def configs_journalisees(tags, d):
    """(tag, seed, familles, n, d) -> ensemble des idx vus, depuis runs/."""
    out = collections.defaultdict(set)
    for cfg_path in glob.glob(os.path.join(RACINE, "runs", "*", "config.json")):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
        except Exception:
            continue
        if cfg.get("tag") not in tags or cfg.get("d") != d:
            continue
        res = os.path.join(os.path.dirname(cfg_path), "results.jsonl")
        if not os.path.exists(res):
            continue
        cle = (cfg["tag"], cfg["seed"], cfg["families"], cfg["n"], cfg["d"])
        with open(res) as f:
            for ligne in f:
                try:
                    r = json.loads(ligne)
                except Exception:
                    continue
                if isinstance(r.get("idx"), int):
                    out[cle].add(r["idx"])
    return out


def reconstruire(cle, idx_voulus):
    """Rejoue `gen_system` depuis la graine, comme canary8. Rend {idx: rs}."""
    tag, seed, familles, n, d = cle
    rng = random.Random(seed)
    fam = familles.split(",")
    vus = {}
    if not idx_voulus:
        return vus
    for k in range(max(idx_voulus) + 1):
        rs = RUN.gen_system(n, d, rng, fam)
        if k in idx_voulus and rs is not None:
            vus[k] = rs
    return vus


# ---------- test de permutation, stdlib seule ----------

def permutation(a, b, n_iter=2000, graine=20260826):
    if not a or not b:
        return None
    obs = abs(sum(a) / len(a) - sum(b) / len(b))
    tout = list(a) + list(b)
    na = len(a)
    rng = random.Random(graine)
    extremes = 0
    for _ in range(n_iter):
        rng.shuffle(tout)
        m1 = sum(tout[:na]) / na
        m2 = sum(tout[na:]) / (len(tout) - na)
        if abs(m1 - m2) >= obs - 1e-12:
            extremes += 1
    return (extremes + 1.0) / (n_iter + 1.0)


# ---------- mesure d'un systeme ----------

def mesurer_systeme(rs, instances, graine):
    """Rend (inconnues, left_T0, left_prop, left_prop_ART, n) en BRUT.

    LES TROIS MESURES SONT APPARIEES sur le MEME puzzle. C'est ce qui rend le
    controle de circularite lisible : entre le bras du 26/08 et celui du
    27/08, la SEULE chose qui change est le drapeau -- pas le tirage, pas le
    systeme, pas les indices.

    ORDRE ATTENDU PAR CONSTRUCTION, et non par observation :
        left_T0  >=  left_prop  >=  left_prop_ART
    la propagation etant un FILTRE devant la meme saturation T0 gelee, et
    l'articulation n'ajoutant que des deductions. Toute inversion est un BUG :
    le banc s'arrete plutot que de la rapporter.
    """
    random.seed(graine)
    it = lt = lp = la = 0
    n = 0
    for _ in range(instances):
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        a, b = resistance_t0(rs, puz)
        c, e = resistance_prop(rs, puz, articulation=False)
        c2, f = resistance_prop(rs, puz, articulation=True)
        assert a == c == c2, "les mesures ne partent pas du meme puzzle"
        if e > b:
            raise AssertionError(
                "resistance_prop > resistance_T0 : la saturation forte est "
                "plus faible que la reference, ce qui est impossible par "
                "construction. Bug, pas resultat.")
        if f > e:
            raise AssertionError(
                "l'articulation LAISSE PLUS de cellules que sans elle : une "
                "regle qui n'ajoute que des deductions ne peut pas en "
                "retirer. Bug, pas resultat.")
        it += a
        lt += b
        lp += e
        la += f
        n += 1
    return (it, lt, lp, la, n)


# ---------- GARDE 1 : le canari de non-redondance ----------

def canari_non_redondance(echantillon, instances):
    """Si deux resistances coincident partout, le gain ne mesure rien. Si
    l'une sature -- 0 % ou 100 % -- c'est le troisieme cas du motif. Dans
    tous ces cas : ARRET, pas d'interpretation.

    AJOUT DU 27/08 : le meme test porte desormais sur l'ARTICULATION. Si elle
    ne change aucune resistance, le controle de circularite comparerait deux
    fois le MEME propagateur -- et un resultat « la resistance survit » ne
    dirait alors rien du tout. Un instrument qui ne distingue pas ne controle
    pas.
    """
    print("== GARDE 1 : canari de non-redondance ==")
    identiques = differentes = 0
    art_id = art_diff = 0
    it_tot = lt_tot = lp_tot = la_tot = 0
    for rs in echantillon:
        it, lt, lp, la, n = mesurer_systeme(rs, instances, 909)
        if not n:
            continue
        it_tot += it
        lt_tot += lt
        lp_tot += lp
        la_tot += la
        if lt == lp:
            identiques += 1
        else:
            differentes += 1
        if lp == la:
            art_id += 1
        else:
            art_diff += 1
    tot = identiques + differentes
    print("  systemes : %d   T0 vs prop -- identiques : %d   differentes : %d"
          % (tot, identiques, differentes))
    print("  articulation : identiques : %d   differentes : %d"
          % (art_id, art_diff))
    print("  brut : inconnues=%d  restantes_T0=%d  restantes_prop=%d  "
          "restantes_ART=%d" % (it_tot, lt_tot, lp_tot, la_tot))
    if not tot:
        print("  ECHEC : aucun systeme mesurable.")
        return False
    if differentes == 0:
        print("  ARRET : les deux resistances coincident PARTOUT.")
        print("  Le gain ne mesure rien -- une seconde mesure qui suit")
        print("  exactement la premiere n'ajoute pas d'information, elle")
        print("  ajoute de la confiance injustifiee.")
        return False
    if art_diff == 0:
        print("  ARRET : L'ARTICULATION EST INERTE sur ces systemes.")
        print("  Elle ne change AUCUNE resistance. Le controle de circularite")
        print("  comparerait alors deux fois le MEME propagateur, et son")
        print("  resultat -- quel qu'il soit -- ne dirait rien sur la force")
        print("  du propagateur. C'est exactement le piege qu'il vient")
        print("  fermer : un instrument qui ne distingue pas ne controle pas.")
        return False
    if it_tot and (lt_tot == 0 or lt_tot == it_tot):
        print("  ARRET : la reference SATURE (0 %% ou 100 %% de restantes).")
        print("  Troisieme cas du motif : un indicateur sature imprime des")
        print("  chiffres sans distinguer quoi que ce soit.")
        return False
    if it_tot and lp_tot == 0:
        print("  ARRET : la saturation forte resout TOUT : le gain vaut 1")
        print("  partout et ne peut plus discriminer.")
        return False
    print("  OK : les trois mesures different, aucune ne sature.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=3)
    ap.add_argument("--tags", default="static-ref,connect")
    ap.add_argument("--systemes", type=int, default=200,
                    help="systemes echantillonnes par tag")
    ap.add_argument("--instances", type=int, default=6)
    ap.add_argument("--canari-systemes", type=int, default=25)
    a = ap.parse_args()
    tags = a.tags.split(",")

    print("gain_propagation  d=%d  tags=%s  systemes/tag=%d  instances=%d"
          % (a.d, a.tags, a.systemes, a.instances))
    print("  PREDICTION (ecrite avant, DECISIONS.md) :")
    print("    gain FORT sur static-ref, gain FAIBLE sur connect")
    print()

    trouve = configs_journalisees(tags, a.d)
    if not trouve:
        print("aucune serie journalisee pour ces tags a d=%d." % a.d)
        return
    par_tag = collections.defaultdict(list)
    for cle, idxs in trouve.items():
        # ECHANTILLON ALEATOIRE, jamais un prefixe (invariant 15) : l'ordre des
        # idx suit l'ordre de generation, qui est structure.
        rng = random.Random(4242 + hash(cle) % 1000)
        liste = sorted(idxs)
        if len(liste) > a.systemes:
            liste = rng.sample(liste, a.systemes)
        for idx, rs in reconstruire(cle, set(liste)).items():
            par_tag[cle[0]].append(rs)
    for t in tags:
        print("  %-12s systemes reconstruits : %d" % (t, len(par_tag[t])))
    print()

    # TIRAGE ALEATOIRE, JAMAIS UN PREFIXE (invariant 15). `par_tag[t]` est
    # ordonne par `idx`, donc par ordre de generation : un prefixe en
    # echantillonne un coin. Ce garde avait ete ecrit avec un prefixe et a
    # conclu a tort que les deux resistances coincidaient partout.
    ech = []
    _rng_ech = random.Random(31337)
    for t in tags:
        _pool = par_tag[t]
        ech.extend(_rng_ech.sample(_pool, min(a.canari_systemes, len(_pool))))
    if not canari_non_redondance(ech, a.instances):
        print()
        print("MESURE NON EFFECTUEE : le garde 1 n'est pas passe.")
        sys.exit(2)

    print()
    print("== MESURE ==")
    brut = {}
    gains = {}
    gains_art = {}
    for t in tags:
        it = lt = lp = la = 0
        g, ga = [], []
        for rs in par_tag[t]:
            a1, b1, e1, f1, n1 = mesurer_systeme(rs, a.instances, 707)
            if not n1 or b1 == 0:
                continue
            it += a1
            lt += b1
            lp += e1
            la += f1
            g.append((b1 - e1) / float(b1))
            ga.append((b1 - f1) / float(b1))
        brut[t] = (it, lt, lp, la)
        gains[t] = g
        gains_art[t] = ga
        # LES BRUTS, JAMAIS LE RATIO SEUL : refaire le rapport a la main est le
        # seul controle qui ne passe pas par le chiffre qu'on veut lire.
        print("  %-12s n=%-4d  inconnues=%-7d  restantes_T0=%-7d  "
              "restantes_prop=%-7d  restantes_ART=%-7d"
              % (t, len(g), it, lt, lp, la))
        if lt:
            print("               SANS articulation : agrege = %.3f   "
                  "moyen = %.3f" % ((lt - lp) / float(lt),
                                    sum(g) / len(g) if g else float("nan")))
            print("               AVEC articulation : agrege = %.3f   "
                  "moyen = %.3f" % ((lt - la) / float(lt),
                                    sum(ga) / len(ga) if ga else float("nan")))
    print()
    if len(tags) == 2 and all(gains[t] for t in tags):
        for nom, G in (("SANS articulation (bras du 26/08)", gains),
                       ("AVEC articulation (controle du 27/08)", gains_art)):
            p = permutation(G[tags[0]], G[tags[1]])
            m0 = sum(G[tags[0]]) / len(G[tags[0]])
            m1 = sum(G[tags[1]]) / len(G[tags[1]])
            print("  ECART ENTRE TAGS, %s :" % nom)
            print("    %s %.3f  vs  %s %.3f   p = %.4f"
                  % (tags[0], m0, tags[1], m1, p))
        print()
        print("  LE CONTROLE DE CIRCULARITE SE LIT SUR LA LIGNE `connect`,")
        print("  ET SUR ELLE SEULE :")
        print("    - si le gain AVEC articulation y reste bas, la resistance")
        print("      est une propriete de LA CONTRAINTE et non de notre")
        print("      implementation : la circularite tombe ;")
        print("    - s'il monte vers celui de static-ref, ce qu'on mesurait")
        print("      etait la FAIBLESSE DE NOTRE PROPAGATEUR, et l'hypothese")
        print("      centrale perd son meilleur soutien.")
        print("  Les deux issues etaient ecrites AVANT la mesure")
        print("  (DECISIONS.md, 27/08). Aucune n'est l'issue esperee.")


if __name__ == "__main__":
    main()
