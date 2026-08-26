#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MESURE DE DEBIT -- le critere de succes de A.

A est un chantier de DEBIT : il existe pour rendre n=5 praticable sous la
borne de 20 s par systeme, pas pour deduire mieux. Cet outil mesure le seul
chiffre qui tranche : le cout par systeme, AVEC et SANS propagation.

CE FICHIER N'EST PAS DANS engine/ ET NE DOIT PAS Y ALLER.
  - il ne change pas `dsl_hash`, donc il ne rompt aucune serie ;
  - il contient un solveur PROTOTYPE qui consomme des domaines. Ce prototype
    n'est pas le moteur : il sert a decider SI le branchement vaut la peine.
    Le brancher serait une autre decision, prise sur ces chiffres.

POURQUOI UN PROTOTYPE DE SOLVEUR EST NECESSAIRE. `count_solutions` prend une
GRILLE, pas des domaines. Une propagation appliquee avant l'appel ne peut donc
transmettre que les domaines devenus SINGLETONS -- tout le reste du filtrage
est perdu a l'interface. Mesurer « avec propagation » en pre-traitement seul
sous-estimerait donc massivement le gain, et conclurait a tort que A ne sert a
rien. Le prototype fait descendre la propagation DANS la recherche, ou elle
travaille reellement.

Les deux solveurs comptent les memes solutions : `verifier_accord()` le
verifie sur chaque instance, et un desaccord arrete la mesure. Une mesure de
debit entre deux solveurs qui ne calculent pas la meme chose ne vaut rien.
"""
import argparse
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(HERE)
ENGINE = os.environ.get("RS_ENGINE") or os.path.join(RACINE, "engine")
sys.path.insert(0, ENGINE)
sys.path.insert(0, RACINE)

from rulesearch import (UNASSIGNED, count_solutions, random_solution,
                        minimal_clues)
from propagate import domaines, propager
import run as RUN


# ---------- solveur PROTOTYPE : la propagation descend dans la recherche ----

def compter_solutions_prop(rs, grille, cap=2, budget=200000):
    """Compte les solutions (arret a `cap`) en maintenant des domaines.

    Correct meme si des contraintes n'ont pas de propagateur : chaque
    assignation est validee par `rs.feasible`, qui reste l'oracle. La
    propagation ne fait qu'elaguer -- elle n'autorise jamais rien.
    """
    n2 = rs.n * rs.n
    g = list(grille)
    dom = domaines(rs, g)
    noeuds = [0]
    trouve = [0]

    _, contra = propager(rs, dom)
    if contra:
        return 0, noeuds[0]

    def rec(dom, g):
        if trouve[0] >= cap or noeuds[0] > budget:
            return
        libres = [i for i in range(n2) if g[i] == UNASSIGNED]
        if not libres:
            trouve[0] += 1
            return
        # cellule au plus petit domaine : c'est la propagation qui rend ce
        # choix possible, et c'est une part du gain qu'on mesure.
        i = min(libres, key=lambda k: len(dom[k]))
        for v in sorted(dom[i]):
            noeuds[0] += 1
            if noeuds[0] > budget:
                return
            g[i] = v
            if rs.feasible(g, changed=i):
                d2 = [set(x) for x in dom]
                d2[i] = {v}
                _, ct = propager(rs, d2)
                if not ct and all(d2[k] for k in range(n2)):
                    rec(d2, g)
            g[i] = UNASSIGNED
            if trouve[0] >= cap:
                return

    rec(dom, g)
    return trouve[0], noeuds[0]


def verifier_accord(rs, puzzle, cap=2):
    """Les deux solveurs doivent rendre le MEME compte. Sinon la mesure est
    sans objet et il faut s'arreter, pas moyenner."""
    a = count_solutions(rs, puzzle, cap=cap)
    b, _ = compter_solutions_prop(rs, puzzle, cap=cap)
    return a, b


# ---------- minimal_clues, version prototype ----------

def minimal_clues_prop(rs, sol):
    """Copie de `minimal_clues` ou le seul changement est le solveur appele.
    Volontairement dupliquee et NON factorisee : les deux versions doivent
    pouvoir diverger, c'est tout l'objet de la mesure (invariant 10)."""
    n = rs.n
    cells = list(range(n * n))
    random.shuffle(cells)
    puz = list(sol)
    for i in cells:
        keep = puz[i]
        puz[i] = UNASSIGNED
        cnt, _ = compter_solutions_prop(rs, puz, cap=2)
        if cnt != 1:
            puz[i] = keep
    return puz


# ---------- mesure ----------

def mesurer(n, d, familles, graine, combien, instances, plafond_s):
    rng = random.Random(graine)
    lignes = []
    desaccords = 0
    sans_solution = 0
    nuls = 0
    for idx in range(combien):
        rs = None
        for _ in range(20):
            rs = RUN.gen_system(n, d, rng, familles)
            if rs is not None:
                break
        if rs is None:
            nuls += 1
            continue
        random.seed(graine * 1000 + idx)
        t_sol = t_mc_base = t_mc_prop = t_cs_base = t_cs_prop = 0.0
        nb = 0
        depasse = False
        for _ in range(instances):
            t0 = time.time()
            sol = random_solution(rs)
            t_sol += time.time() - t0
            if sol is None:
                continue

            etat = random.getstate()
            t0 = time.time()
            puz = minimal_clues(rs, sol)
            t_mc_base += time.time() - t0

            # meme tirage de cellules pour les deux : sinon on compare deux
            # puzzles differents et le temps ne veut rien dire.
            random.setstate(etat)
            t0 = time.time()
            puz2 = minimal_clues_prop(rs, sol)
            t_mc_prop += time.time() - t0

            t0 = time.time()
            a = count_solutions(rs, puz, cap=2)
            t_cs_base += time.time() - t0
            t0 = time.time()
            b, _ = compter_solutions_prop(rs, puz, cap=2)
            t_cs_prop += time.time() - t0
            if a != b or puz != puz2:
                desaccords += 1
            nb += 1
            if max(t_mc_base, t_mc_prop) > plafond_s:
                depasse = True
                break
        if not nb:
            sans_solution += 1
            print("  %-30s AUCUNE SOLUTION TROUVEE (%.2fs perdus)"
                  % (rs.label[:30], t_sol))
            sys.stdout.flush()
            continue
        lignes.append((rs.label, nb, t_sol, t_mc_base, t_mc_prop,
                       t_cs_base, t_cs_prop, depasse))
        print("  %-26s i=%d  rnd=%6.2fs | mc base=%7.3f prop=%7.3f x%.2f "
              "| cs base=%7.3f prop=%7.3f %s"
              % (rs.label[:26], nb, t_sol, t_mc_base, t_mc_prop,
                 (t_mc_base / t_mc_prop) if t_mc_prop > 0 else float("inf"),
                 t_cs_base, t_cs_prop, "(PLAFOND)" if depasse else ""))
        sys.stdout.flush()
    return lignes, desaccords, sans_solution, nuls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--d", type=int, default=3)
    ap.add_argument("--families", default="static")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--systems", type=int, default=8)
    ap.add_argument("--instances", type=int, default=3)
    ap.add_argument("--cap-seconds", type=float, default=20.0)
    a = ap.parse_args()

    print("MESURE DE DEBIT  n=%d d=%d familles=%s systemes=%d instances=%d"
          % (a.n, a.d, a.families, a.systems, a.instances))
    print("  rnd = random_solution   -- NON substituable par la propagation")
    print("  mc  = minimal_clues     -- domine par count_solutions")
    print("  cs  = count_solutions   -- un appel isole, pour reference")
    print()
    lignes, desaccords, sans_sol, nuls = mesurer(
        a.n, a.d, a.families.split(","), a.seed, a.systems, a.instances,
        a.cap_seconds)
    print()
    if nuls:
        print("%d systemes non generables a n=%d (ignores)." % (nuls, a.n))
    if sans_sol:
        print("%d systemes SANS solution trouvee -- non mesures, mais leur cout"
              " est reel et il est PERDU pour les deux solveurs." % sans_sol)
    if desaccords:
        print("ARRET : %d desaccords entre les deux solveurs." % desaccords)
        print("Une mesure de debit entre deux solveurs qui ne calculent pas la")
        print("meme chose ne vaut rien.")
        sys.exit(1)
    if not lignes:
        print("aucun systeme mesure.")
        return
    ni = sum(l[1] for l in lignes)
    ts = sum(l[2] for l in lignes)
    mb, mp = sum(l[3] for l in lignes), sum(l[4] for l in lignes)
    cb, cp = sum(l[5] for l in lignes), sum(l[6] for l in lignes)
    print("accord de comptage ET de puzzle : OK sur %d instances" % ni)
    print()
    print("  random_solution : %8.2f s   (non substituable)" % ts)
    print("  minimal_clues   : %8.2f s base  ->  %8.2f s prop   x%.2f"
          % (mb, mp, (mb / mp) if mp > 0 else float("inf")))
    print("  count_solutions : %8.3f s base  ->  %8.3f s prop   x%.2f"
          % (cb, cp, (cb / cp) if cp > 0 else float("inf")))
    tot_b, tot_p = ts + mb + cb, ts + mp + cp
    print()
    print("  TOTAL par systeme : base %.2f s   prop %.2f s   x%.2f"
          % (tot_b / max(1, len(lignes)), tot_p / max(1, len(lignes)),
             (tot_b / tot_p) if tot_p > 0 else float("inf")))
    part = 100.0 * ts / tot_b if tot_b else 0
    print("  part de random_solution dans le cout de base : %.0f%%" % part)
    if part > 50:
        print("  => LE COUT EST MAJORITAIREMENT HORS DE PORTEE DE LA "
              "PROPAGATION telle qu'elle est branchable aujourd'hui.")
    depasses = sum(1 for l in lignes if l[7])
    if depasses:
        print("  %d/%d systemes au plafond de %.0f s : leurs temps sont des "
              "BORNES INFERIEURES." % (depasses, len(lignes), a.cap_seconds))


if __name__ == "__main__":
    main()
