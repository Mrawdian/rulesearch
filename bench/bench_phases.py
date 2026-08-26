#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VENTILATION DU TEMPS PAR PHASE, A n=5, AVEC LE MOTEUR ACTUEL SEUL.

La question qu'il faut trancher AVANT de conclure quoi que ce soit sur A :
la propagation n'accelere que `solve_graded`. En production,
`random_solution` et `minimal_clues` n'en beneficient d'aucune facon.
**Si elles dominent le cout a n=5, un facteur 4 sur `solve_graded` ne fera pas
passer n=5 sous la borne**, et A ne suffit pas.

Aucun prototype ici : on mesure le moteur tel qu'il tourne, avec la meme borne
SIGALRM de 20 s que `run.py`, et on enregistre la phase EN COURS au moment de
l'interruption -- c'est le champ `phase` des verdicts TROP-CHER.

A n=4 la production repond deja : les 3135 TROP-CHER sont TOUS dans
`solve_graded`. Rien ne garantit que ce soit encore vrai a n=5, et c'est
precisement ce qu'on va voir.
"""
import argparse
import collections
import os
import random
import signal
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(HERE)
ENGINE = os.environ.get("RS_ENGINE") or os.path.join(RACINE, "engine")
sys.path.insert(0, ENGINE)
sys.path.insert(0, RACINE)

from rulesearch import (UNASSIGNED, count_solutions, random_solution,
                        minimal_clues)
from deduction import solve_graded
from prefilter import is_dead
from t0_legacy import resistance as t0_resistance
import run as RUN

PHASE = "?"


class TropLent(Exception):
    pass


def _alarme(signum, frame):
    raise TropLent()


signal.signal(signal.SIGALRM, _alarme)


def evaluer(rs, instances):
    """Mirroir des phases de `run.evaluate_system`, chronometre.
    Rend (temps_par_phase, phase_a_l_interruption ou None)."""
    global PHASE
    t = collections.OrderedDict(
        (k, 0.0) for k in ("prefilter", "random_solution", "minimal_clues",
                           "count_solutions", "solve_graded", "resistance_T0"))

    def chrono(nom, fn):
        global PHASE
        PHASE = nom
        t0 = time.time()
        try:
            return fn()
        finally:
            t[nom] += time.time() - t0

    if chrono("prefilter", lambda: is_dead(rs)):
        return t, None, True          # MORT au prefiltre

    for _ in range(instances):
        sol = chrono("random_solution", lambda: random_solution(rs))
        if sol is None:
            continue
        puz = chrono("minimal_clues", lambda: minimal_clues(rs, sol))
        chrono("count_solutions", lambda: count_solutions(rs, puz, cap=2))
        chrono("solve_graded", lambda: solve_graded(rs, puz))
        chrono("resistance_T0", lambda: t0_resistance(rs, puz))
    return t, None, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--d", type=int, default=3)
    ap.add_argument("--families", default="static")
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--systems", type=int, default=30)
    ap.add_argument("--instances", type=int, default=12)
    ap.add_argument("--cap-seconds", type=float, default=20.0)
    a = ap.parse_args()

    print("VENTILATION PAR PHASE  n=%d d=%d familles=%s systemes=%d "
          "instances=%d borne=%.0fs"
          % (a.n, a.d, a.families, a.systems, a.instances, a.cap_seconds))
    print("  moteur actuel SEUL -- aucun prototype")
    print()

    rng = random.Random(a.seed)
    total = collections.OrderedDict()
    interrompus = collections.Counter()
    temps_interrompus = collections.Counter()
    morts = n_ok = 0
    temps_systeme = []
    for idx in range(a.systems):
        rs = None
        for _ in range(20):
            rs = RUN.gen_system(a.n, a.d, rng, a.families.split(","))
            if rs is not None:
                break
        if rs is None:
            continue
        random.seed(a.seed * 1000 + idx)
        t0 = time.time()
        signal.alarm(int(a.cap_seconds))
        coupe = False
        try:
            t, _, mort = evaluer(rs, a.instances)
        except TropLent:
            coupe = True
            mort = False
            t = None
        finally:
            signal.alarm(0)
        dt = time.time() - t0
        temps_systeme.append(dt)
        if coupe:
            interrompus[PHASE] += 1
            # UN SYSTEME INTERROMPU CONSOMME LA BORNE ENTIERE, et il la
            # consomme DANS la phase ou il a ete coupe. L'ignorer revient a
            # exclure du calcul la population qui fait le budget.
            temps_interrompus[PHASE] += dt
            print("  %-32s INTERROMPU a %5.1fs dans %s"
                  % (rs.label[:32], dt, PHASE))
            sys.stdout.flush()
            continue
        if mort:
            morts += 1
        n_ok += 1
        for k, v in t.items():
            total[k] = total.get(k, 0.0) + v

    print()
    print("  systemes termines : %d   morts au prefiltre : %d   interrompus : %d"
          % (n_ok, morts, sum(interrompus.values())))
    if interrompus:
        print("  PHASE AU MOMENT DE L'INTERRUPTION :")
        for ph, c in interrompus.most_common():
            print("    %-18s %d" % (ph, c))
    if temps_systeme:
        temps_systeme.sort()
        m = len(temps_systeme)
        print("  temps par systeme : median %.3fs  p90 %.3fs  max %.3fs"
              % (temps_systeme[m // 2], temps_systeme[int(m * 0.9)],
                 temps_systeme[-1]))
    tt = sum(total.values())
    ti = sum(temps_interrompus.values())
    if not (tt or ti):
        print("  aucun temps cumule.")
        return
    if tt:
        print()
        print("  repartition sur les systemes TERMINES seuls (%.2f s) --"
              " INDICATIVE :" % tt)
        for k, v in sorted(total.items(), key=lambda kv: -kv[1]):
            print("    %-18s %8.3f s   %5.1f %%" % (k, v, 100.0 * v / tt))

    # ---- LE CHIFFRE QUI COMPTE : le budget REEL, interrompus inclus ----
    budget = dict(total)
    for ph, v in temps_interrompus.items():
        budget[ph] = budget.get(ph, 0.0) + v
    tot_budget = sum(budget.values())
    print()
    print("  BUDGET REEL, INTERROMPUS INCLUS (%.2f s dont %.2f s de systemes"
          " coupes) :" % (tot_budget, ti))
    for k, v in sorted(budget.items(), key=lambda kv: -kv[1]):
        print("    %-18s %8.3f s   %5.1f %%"
              % (k, v, 100.0 * v / tot_budget if tot_budget else 0.0))
    part_sg = (100.0 * budget.get("solve_graded", 0.0) / tot_budget
               if tot_budget else 0.0)
    print()
    print("  UN SYSTEME INTERROMPU CONSOMME LA BORNE ENTIERE, dans la phase ou")
    print("  il a ete coupe. Calculer la repartition sur les seuls systemes")
    print("  TERMINES exclut exactement la population qui fait le budget --")
    print("  c'est le neuvieme cas du motif, et ce banc l'a reproduit une fois.")
    print()
    if part_sg < 50:
        print("  *** solve_graded ne represente que %.0f %% du BUDGET REEL."
              % part_sg)
        print("  *** La propagation n'accelere que cette phase : meme un")
        print("  *** facteur 4 dessus laisserait %.0f %% du cout intact."
              % (100 - part_sg))
        print("  *** A NE SUFFIT PAS a lui seul pour n=%d." % a.n)
    else:
        print("  solve_graded represente %.0f %% du BUDGET REEL." % part_sg)
        print("  C'est bien la que la propagation peut agir, et c'est la seule")
        print("  phase qu'elle accelere -- A vise donc le bon endroit.")


if __name__ == "__main__":
    main()
