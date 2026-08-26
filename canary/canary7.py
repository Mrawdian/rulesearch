"""
CANARI DE SURETE DE LA RESISTANCE A T0.

    resistance = t0_left / t0_unknown
               = cases restantes apres saturation de T0 SEULE
                 / cases inconnues du puzzle initial

Cette metrique est devenue la mesure principale du projet apres que
`max_level` ait sature (100 % partout). Une metrique principale qui ne
separerait pas les deux cas extremes ne mesurerait rien du tout -- et
l'historique du projet montre que ca arrive sans que rien ne le signale.

Deux verifications, aux deux bornes :

  A. **Resistance NULLE** sur une instance que T0 resout INTEGRALEMENT. S'il ne
     reste aucune case, la resistance doit valoir exactement 0. Une metrique
     qui rendrait autre chose que 0 ici compterait du travail inexistant.

  B. **Resistance STRICTEMENT POSITIVE** sur une instance que T0 ne resout pas.
     S'il reste des cases et que la metrique vaut 0, elle est aveugle a
     precisement ce qu'elle est censee mesurer.

Le canari echoue aussi s'il n'arrive pas a EXHIBER l'un des deux cas : ne pas
trouver d'instance resistante signifierait que la mesure est constante, donc
sans pouvoir discriminant.

Sortie non nulle = la resistance a T0 n'est pas fiable.
"""
import os
import random
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "engine"))

from rulesearch import UNASSIGNED, random_solution, minimal_clues
from deduction import apply_T0
import run as RUN

BUDGET = 240.0
N_CONFIRMATIONS = 5


def resistance(rs, puz):
    """Rend (inconnues, restantes) apres saturation de T0 seule."""
    g = list(puz)
    while True:
        prog, contra = apply_T0(rs, g)
        if contra or not prog:
            break
    inconnues = sum(1 for x in puz if x == UNASSIGNED)
    restantes = sum(1 for x in g if x == UNASSIGNED)
    return inconnues, restantes


# `static` sature presque toujours sous T0, `connect` resiste souvent :
# les deux bornes se trouvent donc en balayant ces deux familles.
CONFIGS = [(4, 3, ["static"]), (4, 3, ["connect", "relational"])]

nuls = []          # cas A : T0 resout tout
resistants = []    # cas B : T0 laisse des cases
rng = random.Random(31)
random.seed(31)
t0 = time.time()
examinees = 0

while (len(nuls) < N_CONFIRMATIONS or len(resistants) < N_CONFIRMATIONS) \
        and time.time() - t0 < BUDGET:
    for n, d, fams in CONFIGS:
        rs = RUN.gen_system(n, d, rng, fams)
        if rs is None:
            continue
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        inconnues, restantes = resistance(rs, puz)
        if inconnues == 0:
            continue          # puzzle deja complet : hors sujet
        examinees += 1
        if restantes == 0 and len(nuls) < N_CONFIRMATIONS:
            nuls.append((rs.label, inconnues, restantes))
        elif restantes > 0 and len(resistants) < N_CONFIRMATIONS:
            resistants.append((rs.label, inconnues, restantes))

print("instances examinees : %d" % examinees)
print()

ok = True

print("== A. T0 resout INTEGRALEMENT -> resistance doit valoir 0 ==")
if not nuls:
    print("  ECHEC : aucune instance integralement resolue par T0 n'a pu etre")
    print("          exhibee dans le budget. Borne basse non verifiable.")
    ok = False
else:
    for label, inc, rest in nuls:
        r = float(rest) / inc
        etat = "OK" if r == 0.0 else "ECHEC"
        if r != 0.0:
            ok = False
        print("  inconnues=%2d restantes=%2d  resistance=%.3f  %s   %s"
              % (inc, rest, r, etat, label[:44]))

print()
print("== B. T0 ne resout PAS tout -> resistance doit etre > 0 ==")
if not resistants:
    print("  ECHEC : aucune instance resistante n'a pu etre exhibee. La mesure")
    print("          serait constante, donc sans pouvoir discriminant.")
    ok = False
else:
    for label, inc, rest in resistants:
        r = float(rest) / inc
        etat = "OK" if r > 0.0 else "ECHEC"
        if r <= 0.0:
            ok = False
        print("  inconnues=%2d restantes=%2d  resistance=%.3f  %s   %s"
              % (inc, rest, r, etat, label[:44]))

print()
if not ok:
    print("ECHEC : la resistance a T0 ne separe pas ses deux bornes.")
    sys.exit(1)
print("OK : resistance nulle quand T0 resout tout, strictement positive sinon.")
