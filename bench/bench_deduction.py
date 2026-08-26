#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MESURE DE DEBIT SUR LA PHASE QUI COUTE REELLEMENT : `solve_graded`.

POURQUOI CE SECOND BANC. Le premier (`bench_debit.py`) mesurait
`count_solutions` et `minimal_clues`. Les journaux de production tranchent :
sur 58905 systemes, les **3135 TROP-CHER se declenchent TOUS dans
`solve_graded`**, aucun ailleurs. Le premier banc mesurait donc une phase qui
n'est pas le goulot -- et il concluait, a tort, que la propagation ne sert a
rien.

Le cout est aussi tres dissymetrique : median 14 ms, p90 149 ms, **p99
20 000 ms**. C'est 1 % des systemes qui consomme le budget, et ce banc les
cherche au lieu de moyenner sur la population facile.

CE QUE `apply_T2` COUTE. Pour chaque cellule libre, pour chaque valeur
candidate, il COPIE la grille et sature T0+T1 -- ou T0 recalcule les candidats
de chaque cellule par `d` appels a `feasible()`. La propagation remplace les
deux : les candidats sont une lecture de domaine, la saturation est un point
fixe sur des ensembles.

CE QUE LE PROTOTYPE NE PEUT PAS FAIRE, ET IL FAUT LE LIRE AVANT LES CHIFFRES.
`Connected` n'a PAS de propagateur (etape 10). Sur la famille `connect` -- celle
qui coute le plus -- la propagation est donc structurellement plus faible, et
tout gain mesure y est un MINORANT de ce que A donnerait une fois Connected
ecrit. Sur `static`, le gain mesure est le gain reel.

LE PROTOTYPE DEDUIT AUTREMENT, PAS SEULEMENT PLUS VITE. La saturation interne
de T2 change, donc les eliminations changent, donc le verdict peut changer.
Les divergences sont COMPTEES et affichees : un gain de temps obtenu en
deduisant moins n'est pas un gain.
"""
import argparse
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

from rulesearch import UNASSIGNED, random_solution, minimal_clues
from deduction import (solve_graded, apply_T0, apply_T1, apply_T2,
                       candidates, saturate_low)
from propagate import domaines, propager, PROPAGATEURS
import run as RUN


# ---------- borne de temps, la MEME que la production ----------
#
# `run.py` entoure chaque systeme d'un SIGALRM. Le banc ne le faisait pas :
# sur `connect`, dont le p99 est deja a 20 s, un seul systeme pathologique le
# bloquait indefiniment -- et ce sont precisement ceux qu'on veut mesurer.
#
# La borne s'applique SEPAREMENT aux deux implementations. Une instance
# interrompue n'est pas jetee, elle est CLASSEE : jeter les instances lentes
# reviendrait a mesurer la population facile, ce qui est deja arrive une fois.

class TropLent(Exception):
    pass


def _alarme(signum, frame):
    raise TropLent()


signal.signal(signal.SIGALRM, _alarme)


def borner(fn, secondes):
    """(resultat, duree, interrompu). `resultat` vaut None si interrompu."""
    t0 = time.time()
    signal.alarm(int(secondes))
    try:
        r = fn()
        return r, time.time() - t0, False
    except TropLent:
        return None, time.time() - t0, True
    finally:
        signal.alarm(0)


# ---------- prototype : la hierarchie, saturee par propagation -------------

def _assigner_singletons(dom, g):
    for i in range(len(g)):
        if g[i] == UNASSIGNED and len(dom[i]) == 1:
            g[i] = next(iter(dom[i]))


def _saturation_acceleree(rs, g):
    """Saturation basse de `apply_T2`, avec la propagation EN FILTRE DEVANT.

    Rend True si contradiction. EGALE OU PLUS FORTE que `saturate_low` :
      - la propagation ne retire que des valeurs impossibles, donc une
        contradiction qu'elle trouve en est une ;
      - si elle n'en trouve pas, on fait le travail complet, inchange.
    Le gain vient des cas ou elle tranche AVANT que le travail cher commence.
    """
    dom = domaines(rs, g)
    _, contra = propager(rs, dom)
    if contra:
        return True
    for i in range(len(g)):
        if g[i] == UNASSIGNED and len(dom[i]) == 1:
            g[i] = next(iter(dom[i]))
    return saturate_low(rs, g)


def _apply_T2_accelere(rs, g):
    """Copie de `apply_T2` dont le SEUL changement est la saturation interne.
    Duplication deliberee et locale au banc : `engine/` n'est pas touche."""
    prog = False
    for i in range(rs.n * rs.n):
        if g[i] != UNASSIGNED:
            continue
        cand = candidates(rs, g, i)
        alive = []
        for v in cand:
            trial = list(g)
            trial[i] = v
            if not _saturation_acceleree(rs, trial):
                alive.append(v)
        if not alive:
            return prog, True
        if len(alive) < len(cand):
            if len(alive) == 1:
                g[i] = alive[0]
            prog = True
    return prog, False


def solve_graded_prop(rs, puzzle):
    """Copie de `solve_graded` dont le seul changement est `apply_T2`.
    Une passe de propagation est faite en entree : elle ne peut que retirer des
    valeurs impossibles, donc elle n'ote aucune solution."""
    n2 = rs.n * rs.n
    g = list(puzzle)
    dom = domaines(rs, g)
    _, contra = propager(rs, dom)
    if contra:
        return {"solved": False, "contradiction": True, "max_level": -1,
                "grille": None}
    for i in range(n2):
        if g[i] == UNASSIGNED and len(dom[i]) == 1:
            g[i] = next(iter(dom[i]))

    top = -1
    while True:
        p0, c0 = apply_T0(rs, g)
        if c0:
            return {"solved": False, "contradiction": True, "max_level": top,
                    "grille": None}
        if p0:
            top = max(top, 0)
            continue
        p1, c1 = apply_T1(rs, g)
        if c1:
            return {"solved": False, "contradiction": True, "max_level": top,
                    "grille": None}
        if p1:
            top = max(top, 1)
            continue
        p2, c2 = _apply_T2_accelere(rs, g)
        if c2:
            return {"solved": False, "contradiction": True, "max_level": top,
                    "grille": None}
        if p2:
            top = max(top, 2)
            continue
        break
    solved = all(x != UNASSIGNED for x in g)
    return {"solved": solved, "contradiction": False, "max_level": top,
            "grille": list(g)}


def grille_base(rs, puzzle):
    """Grille atteinte par la hierarchie actuelle. Meme boucle que
    `solve_graded`, mais elle rend `g` -- que `solve_graded` ne rend pas.
    Duplication deliberee et locale au banc : on ne touche pas a `engine/`."""
    g = list(puzzle)
    while True:
        p0, c0 = apply_T0(rs, g)
        if c0:
            return None
        if p0:
            continue
        p1, c1 = apply_T1(rs, g)
        if c1:
            return None
        if p1:
            continue
        p2, c2 = apply_T2(rs, g)
        if c2:
            return None
        if p2:
            continue
        break
    return g


# ---------- mesure ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--d", type=int, default=3)
    ap.add_argument("--families", default="static")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--systems", type=int, default=40)
    ap.add_argument("--instances", type=int, default=2)
    ap.add_argument("--montrer-lents", type=int, default=6)
    ap.add_argument("--cap-seconds", type=float, default=20.0,
                    help="borne par instance ET par implementation, identique a la production")
    a = ap.parse_args()

    print("DEBIT SUR solve_graded  n=%d d=%d familles=%s systemes=%d"
          % (a.n, a.d, a.families, a.systems))
    print("  base = solve_graded (T0/T1/T2, moteur actuel)")
    print("  prop = meme hierarchie, saturation par propagation")
    manquants = sorted({k for k in ("ALLDIFF", "COUNT", "SUM", "NEQADJ",
                                    "MONO", "PAIRDIFF", "PAIRSTEP",
                                    "NOTRIPLE", "NOSQUARE", "CONNECTED")
                        if k not in PROPAGATEURS})
    if manquants:
        print()
        print("  *** CONTRAINTES SANS PROPAGATEUR : %s" % ", ".join(manquants))
        print("  *** Sur les systemes qui en portent une, la propagation ne la")
        print("  *** voit pas du tout : un gain de temps y est CONFONDU, pas")
        print("  *** conservateur -- une part du temps economise est du travail")
        print("  *** NON FAIT. Voir la ventilation COUVERT / NON COUVERT.")
    print()
    rng = random.Random(a.seed)
    mesures = []
    div_res = div_niv = 0
    niv_bas = niv_haut = 0
    faux_base = faux_prop = 0
    n_deux = n_base_seule = n_prop_seule = n_aucune = 0
    couv = {True: [0, 0.0, 0.0, 0, 0], False: [0, 0.0, 0.0, 0, 0]}
    # par population : [instances, t_base, t_prop, res_perdu, niv_haut]
    res_perdu = res_gagne = 0
    n_surete = 0
    exemples_debloques = []
    sans_sol = 0
    for idx in range(a.systems):
        rs = None
        for _ in range(20):
            rs = RUN.gen_system(a.n, a.d, rng, a.families.split(","))
            if rs is not None:
                break
        if rs is None:
            continue
        couvert = all(getattr(c, "kind", None) in PROPAGATEURS
                      for c in rs.constraints)
        random.seed(a.seed * 1000 + idx)
        tb = tp = 0.0
        nb = 0
        for _ in range(a.instances):
            sol = random_solution(rs)
            if sol is None:
                continue
            puz = minimal_clues(rs, sol)
            rb, dtb, coupe_b = borner(lambda: solve_graded(rs, puz),
                                      a.cap_seconds)
            rp, dtp, coupe_p = borner(lambda: solve_graded_prop(rs, puz),
                                      a.cap_seconds)
            nb += 1
            if coupe_b and coupe_p:
                n_aucune += 1
                continue
            if coupe_b and not coupe_p:
                # LE RESULTAT LE PLUS FORT QUE A PUISSE PRODUIRE : un systeme
                # qui devient MESURABLE alors qu'il ne l'etait pas.
                n_prop_seule += 1
                if len(exemples_debloques) < 5:
                    exemples_debloques.append((rs.label, dtp))
                continue
            if coupe_p and not coupe_b:
                n_base_seule += 1
                continue
            n_deux += 1
            # les temps ne sont cumules que si LES DEUX ont fini : sinon on
            # comparerait un temps mesure a un temps tronque.
            tb += dtb
            tp += dtp
            couv[couvert][0] += 1
            couv[couvert][1] += dtb
            couv[couvert][2] += dtp
            if rb["solved"] != rp["solved"]:
                div_res += 1
                if rb["solved"] and not rp["solved"]:
                    res_perdu += 1      # le prototype resout MOINS
                    couv[couvert][3] += 1
                else:
                    res_gagne += 1      # le prototype resout PLUS
            if rb["max_level"] != rp["max_level"]:
                div_niv += 1
                if rp["max_level"] < rb["max_level"]:
                    niv_bas += 1
                else:
                    niv_haut += 1
                    couv[couvert][4] += 1
            # COINCIDENCE DES SOLUTIONS, pas seulement des verdicts.
            # Une divergence de niveau avec la meme solution est ATTENDUE.
            # Une divergence de SOLUTION serait une unsoundness que canary3
            # n'aurait pas attrapee.
            gp = rp.get("grille")
            if rp["solved"] and gp is not None and gp != sol:
                faux_prop += 1
            # `grille_base` refait le travail de `solve_graded` : on ne le paie
            # que sur les instances rapides, et on DIT combien ont ete
            # verifiees plutot que de laisser croire a une couverture totale.
            if dtb < 2.0:
                gb, _, coupe = borner(lambda: grille_base(rs, puz), 5)
                if not coupe:
                    n_surete += 1
                    if gb is not None and all(x != UNASSIGNED for x in gb) \
                            and gb != sol:
                        faux_base += 1
        if not nb:
            sans_sol += 1
            continue
        mesures.append((rs.label, nb, tb, tp))

    if not mesures:
        print("aucun systeme mesure.")
        return
    mesures.sort(key=lambda m: -m[2])
    print("  les %d systemes les plus couteux (c'est eux qui font le budget) :"
          % min(a.montrer_lents, len(mesures)))
    for lab, nb, tb, tp in mesures[:a.montrer_lents]:
        print("    %-30s base=%8.3fs prop=%8.3fs  x%.2f"
              % (lab[:30], tb, tp, (tb / tp) if tp > 0 else float("inf")))
    TB = sum(m[2] for m in mesures)
    TP = sum(m[3] for m in mesures)
    NI = sum(m[1] for m in mesures)
    print()
    print("  systemes mesures : %d   instances : %d   sans solution : %d"
          % (len(mesures), NI, sans_sol))
    print()
    print("  ISSUES PAR INSTANCE (borne %.0f s, la meme qu'en production) :"
          % a.cap_seconds)
    print("    les deux finissent        : %d" % n_deux)
    print("    base ABANDONNE, prop finit: %d   <-- systemes rendus MESURABLES"
          % n_prop_seule)
    print("    prop abandonne, base finit: %d" % n_base_seule)
    print("    aucune ne finit           : %d" % n_aucune)
    for lab, dt in exemples_debloques:
        print("      debloque : %-40s en %.2f s" % (lab[:40], dt))
    if n_prop_seule:
        print("    Ce compte vaut plus que le rapport des temps : ce n'est pas")
        print("    un gain de vitesse, c'est un systeme qui entre dans la"
              " mesure.")
    print()
    print("  temps compares sur les %d instances ou LES DEUX finissent :"
          % n_deux)
    print("  TOTAL base = %.3f s     TOTAL prop = %.3f s     x%.2f"
          % (TB, TP, (TB / TP) if TP > 0 else float("inf")))
    print("  cout moyen par instance : base %.4f s   prop %.4f s"
          % (TB / NI, TP / NI))
    # la queue, seule population qui compte pour le budget
    q = mesures[:max(1, len(mesures) // 10)]
    qb, qp = sum(m[2] for m in q), sum(m[3] for m in q)
    print("  DECILE LE PLUS COUTEUX : base %.3f s  prop %.3f s  x%.2f"
          % (qb, qp, (qb / qp) if qp > 0 else float("inf")))
    print()
    print("  divergences resolu/non-resolu : %d / %d instances" % (div_res, NI))
    if div_res:
        print("    sens : %d resolus par la base SEULE  <-- deduction PERDUE"
              % res_perdu)
        print("           %d resolus par le prototype SEUL" % res_gagne)
        if res_perdu:
            print("    Une part du gain de temps est payee en deduction "
                  "perdue.")
            if couv[False][0]:
                print("    Attendu sur la population NON COUVERTE : la "
                      "saturation interne")
                print("    de T2 y est plus faible, le rapport de temps est "
                      "CONFONDU.")
            else:
                print("    TOUTE la population est COUVERTE : cette perte "
                      "n'est PAS")
                print("    imputable a une contrainte non propagee. Le "
                      "prototype est donc")
                print("    plus faible que T0 sur au moins une regle -- a "
                      "comprendre.")
    print("  divergences de max_level      : %d / %d instances" % (div_niv, NI))
    if div_niv:
        print("    sens : %d plus BAS (attendu : la propagation absorbe ce que"
              " T2 faisait)" % niv_bas)
        print("           %d plus HAUT %s" % (niv_haut,
              "" if not niv_haut else "<-- INATTENDU, a comprendre avant "
              "d'aller plus loin"))
        if niv_haut and not couv[False][0]:
            print("           sur population ENTIEREMENT COUVERTE : le "
                  "prototype est")
            print("           plus FAIBLE que T0 au niveau bas, il n'y a pas "
                  "d'excuse")
            print("           de couverture. Ne pas lire le rapport de temps "
                  "comme un gain.")
    print()
    print("  POPULATION COUVERTE vs CONFONDUE :")
    for cle, nom in ((True, "COUVERT (tous propagateurs presents)"),
                     (False, "NON COUVERT (contrainte sans propagateur)")):
        ni_, tb_, tp_, rp_, nh_ = couv[cle]
        if not ni_:
            print("    %-42s aucune instance" % nom)
            continue
        print("    %-42s n=%-4d base=%7.3fs prop=%7.3fs x%.2f"
              % (nom, ni_, tb_, tp_, (tb_ / tp_) if tp_ > 0 else float("inf")))
        print("      %sdeduction perdue : %d   max_level plus haut : %d"
              % (" " * 40, rp_, nh_))
    if couv[False][0]:
        print("    Sur la population NON COUVERTE le prototype ne voit pas")
        print("    certaines contraintes : une part du temps economise est du")
        print("    travail NON FAIT. Ce rapport n'est PAS un gain de debit.")
    print()
    print("  CONTROLE DE SURETE -- les solutions coincident-elles ?")
    print("    instances effectivement verifiees : %d (les rapides)"
          % n_surete)
    print("    solutions FAUSSES, moteur actuel : %d / %d" % (faux_base,
                                                              n_surete))
    print("    solutions FAUSSES, prototype     : %d / %d" % (faux_prop,
                                                              n_deux))
    if faux_base or faux_prop:
        print("    *** UNSOUNDNESS. Un solveur remplit la grille et se trompe.")
        print("    *** C'est le seul resultat qui compte : tout arreter.")
    else:
        print("    aucune : les divergences de niveau ne changent pas la"
              " solution atteinte.")
    if div_res or div_niv:
        print()
        print("  => le prototype ne deduit PAS la meme chose. Un gain de temps")
        print("     obtenu en deduisant moins n'est pas un gain de debit.")


if __name__ == "__main__":
    main()
