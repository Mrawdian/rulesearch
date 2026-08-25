"""
CANARI DE SURETE DU PRE-FILTRE.

Un faux positif du pre-filtre supprime silencieusement un systeme qui avait
des solutions -- donc potentiellement un CANDIDAT. C'est le seul mode de
defaillance qui compte, et il ne laisserait aucune trace dans les journaux.

Sur un echantillon de systemes generes : tout systeme declare MORT par le
pre-filtre doit etre confirme MORT par le solveur complet.

Sortie non nulle = au moins un faux positif = pre-filtre inutilisable.
"""
import os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rulesearch import UNASSIGNED, count_solutions
from prefilter import is_dead
from run import gen_system

N = 150
rng = random.Random(31)
random.seed(31)
fams = ["static", "cages", "relational", "connect"]

flagged = confirmed = faux = vivants_rates = 0
t_pf = t_sv = 0.0
i = 0
while i < N:
    rs = gen_system(4, 4, rng, fams)
    if rs is None:
        continue
    i += 1
    t0 = time.time()
    dead = is_dead(rs)
    t_pf += time.time() - t0

    t0 = time.time()
    truth = count_solutions(rs, [UNASSIGNED] * 16, cap=2)
    t_sv += time.time() - t0
    if truth is None:
        continue

    if dead:
        flagged += 1
        if truth == 0:
            confirmed += 1
        else:
            faux += 1
            print("FAUX POSITIF :", rs.label)
    elif truth == 0:
        vivants_rates += 1

print("systemes           : %d" % i)
print("declares MORT      : %d, confirmes %d, FAUX POSITIFS %d" % (flagged, confirmed, faux))
print("morts non attrapes : %d (normal, le pre-filtre est incomplet)" % vivants_rates)
print("cout pre-filtre    : %.2fs   cout solveur : %.2fs" % (t_pf, t_sv))

if faux:
    print("\nECHEC : le pre-filtre supprime des systemes qui ont des solutions.")
    sys.exit(1)
print("\nOK : aucun faux positif.")
