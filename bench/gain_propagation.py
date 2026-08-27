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


def resistance_prop(rs, puzzle):
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
    """Rend (inc_t0, left_t0, inc_pr, left_pr) en BRUT, jamais de ratio."""
    random.seed(graine)
    it = lt = ip = lp = 0
    n = 0
    for _ in range(instances):
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        a, b = resistance_t0(rs, puz)
        c, e = resistance_prop(rs, puz)
        assert a == c, "les deux mesures ne partent pas du meme puzzle"
        if e > b:
            raise AssertionError(
                "resistance_prop > resistance_T0 : la saturation forte est "
                "plus faible que la reference, ce qui est impossible par "
                "construction. Bug, pas resultat.")
        it += a
        lt += b
        ip += c
        lp += e
        n += 1
    return (it, lt, ip, lp, n)


# ---------- GARDE 1 : le canari de non-redondance ----------

def canari_non_redondance(echantillon, instances):
    """Si les deux resistances coincident partout, le gain ne mesure rien.
    Si l'une sature -- 0 % ou 100 % -- c'est le troisieme cas du motif.
    Dans les deux cas : ARRET, pas d'interpretation."""
    print("== GARDE 1 : canari de non-redondance ==")
    identiques = differentes = 0
    lt_tot = lp_tot = it_tot = 0
    for rs in echantillon:
        it, lt, ip, lp, n = mesurer_systeme(rs, instances, 909)
        if not n:
            continue
        it_tot += it
        lt_tot += lt
        lp_tot += lp
        if lt == lp:
            identiques += 1
        else:
            differentes += 1
    tot = identiques + differentes
    print("  systemes : %d   resistances identiques : %d   differentes : %d"
          % (tot, identiques, differentes))
    print("  brut : inconnues=%d  restantes_T0=%d  restantes_prop=%d"
          % (it_tot, lt_tot, lp_tot))
    if not tot:
        print("  ECHEC : aucun systeme mesurable.")
        return False
    if differentes == 0:
        print("  ARRET : les deux resistances coincident PARTOUT.")
        print("  Le gain ne mesure rien -- une seconde mesure qui suit")
        print("  exactement la premiere n'ajoute pas d'information, elle")
        print("  ajoute de la confiance injustifiee.")
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
    print("  OK : les deux mesures different, aucune ne sature.")
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
    for t in tags:
        it = lt = ip = lp = 0
        g = []
        for rs in par_tag[t]:
            a1, b1, c1, e1, n1 = mesurer_systeme(rs, a.instances, 707)
            if not n1 or b1 == 0:
                continue
            it += a1
            lt += b1
            ip += c1
            lp += e1
            g.append((b1 - e1) / float(b1))
        brut[t] = (it, lt, ip, lp)
        gains[t] = g
        # les QUATRE bruts, jamais le ratio seul : `ip` doit valoir `it`,
        # et l'imprimer est le controle que les deux mesures partent bien du
        # meme puzzle.
        print("  %-12s n=%-4d  inconnues=%-6d (%d)  restantes_T0=%-6d  "
              "restantes_prop=%-6d" % (t, len(g), it, ip, lt, lp))
        if lt:
            print("               gain agrege = %.3f   gain moyen par systeme "
                  "= %.3f" % ((lt - lp) / float(lt),
                              sum(g) / len(g) if g else float("nan")))
    print()
    if len(tags) == 2 and all(gains[t] for t in tags):
        p = permutation(gains[tags[0]], gains[tags[1]])
        m0 = sum(gains[tags[0]]) / len(gains[tags[0]])
        m1 = sum(gains[tags[1]]) / len(gains[tags[1]])
        print("  ECART ENTRE TAGS : %s %.3f  vs  %s %.3f   p = %.4f"
              % (tags[0], m0, tags[1], m1, p))
        print()
        print("  GARDE 2 -- la prediction etait : gain FORT sur static-ref,")
        print("  gain FAIBLE sur connect. Si ce resultat la confirme, il")
        print("  merite EXACTEMENT le controle qu'aurait recu son contraire.")
        print("  Les quatre bruts ci-dessus sont la pour ca : refaire le")
        print("  rapport a la main, sans passer par le chiffre agrege.")


if __name__ == "__main__":
    main()
