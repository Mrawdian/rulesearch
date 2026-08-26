"""
CANARI DE DECLENCHEMENT DES TECHNIQUES DE DEDUCTION.

Une technique correcte mais qui ne se declenche JAMAIS est du code mort qui se
fait passer pour une mesure. Elle ne fausse aucun resultat -- elle fait pire :
elle laisse croire que la hierarchie discrimine sur un niveau qui n'existe pas
en pratique, et toute conclusion tiree de "aucun systeme n'atteint TN" est
alors un artefact.

C'est arrive avec T3 (paire nue). T3 est CORRECT -- canary3 le verifie sur les
cinq familles -- et pourtant inerte : c'est une technique d'ELIMINATION de
candidats, alors que le moteur n'a aucune representation des candidats.
`candidates()` les recalcule a chaque appel, donc une elimination ne se
materialise que si elle reduit une cellule a une seule valeur... cas que T0
traite deja. Zero invocation sur 30 instances de reference.

Ce canari verifie DEUX proprietes, et la seconde a ete ajoutee apres qu'une
technique redondante ait failli passer :

  A. **DECLENCHEMENT** -- toute technique activee s'invoque au moins une fois.
  B. **DISCRIMINATION** -- la technique du niveau le plus eleve doit CHANGER la
     distribution de `max_level`. Une technique qui s'invoque sans rien
     reclasser est un **renommage** : elle deplace des systemes d'une etiquette
     a l'autre sans creer de palier. Le cas s'est presente concretement : dans
     l'espace explore `t1_regions()` est vide, donc `saturate_low()` vaut T0
     seul, donc une "contradiction saturant T0 seul" aurait ete identique a T2
     -- elle se serait invoquee normalement et n'aurait rien mesure de neuf.

Se declencher ne suffit pas. Le seuil d'activation est
`DEFAULT_MAX_LEVEL` : relever cette constante sans rendre la technique operante
fait echouer ce canari, donc bloque le run. C'est l'invariant voulu.

Les niveaux au-dela de DEFAULT_MAX_LEVEL sont mesures et affichés a titre
informatif, sans faire echouer : ils ne sont pas en service.

Sortie non nulle = une technique activee ne se declenche jamais.
"""
import collections
import os
import random
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "engine"))

from rulesearch import *
from dsl2 import *
from deduction import solve_graded, DEFAULT_MAX_LEVEL

N = 4
SONDE_MAX = 3          # on observe au-dela de ce qui est active
INSTANCES = 10

rng_cages = random.Random(5)
cages = random_cages(N, rng_cages)

# Cas de reference : choisis pour couvrir des regimes de deduction differents.
# sudoku4 reste sur T0 ; connect fait travailler T2 ; cages+sum sollicite T1.
REFERENCES = [
    ("sudoku4", RuleSystem(N, 4, [AllDiff(R) for R in rows(N) + cols(N) + blocks(N)], "s")),
    ("connect", RuleSystem(N, 2, [Connected(N, 1), NoSquare(N, 1),
                                  Count(list(range(16)), 1, 7, 9)], "c")),
    ("cages+sum", RuleSystem(N, 4, [AllDiff(R) for R in rows(N) + cols(N)]
                             + [SumRange(C, len(C), len(C) * 2, 4) for C in cages], "g")),
]

print("niveau maximal active (DEFAULT_MAX_LEVEL) : T%d" % DEFAULT_MAX_LEVEL)
print()
print("== A. DECLENCHEMENT : chaque technique activee s'invoque-t-elle ? ==")

total = collections.Counter()
for nom, rs in REFERENCES:
    random.seed(23)
    acc = collections.Counter()
    tot = 0
    for _ in range(INSTANCES):
        sol = random_solution(rs)
        if sol is None:
            continue
        tot += 1
        r = solve_graded(rs, minimal_clues(rs, sol), max_level=SONDE_MAX)
        for k, v in r["uses"].items():
            acc[k] += v
            total[k] += v
    print("%-12s instances=%2d  invocations %s"
          % (nom, tot, {("T%d" % k): acc[k] for k in sorted(r["uses"])}))

print()
muettes = []
for niveau in range(0, DEFAULT_MAX_LEVEL + 1):
    etat = "OK" if total[niveau] else "JAMAIS DECLENCHEE"
    print("  T%d  active   : %5d invocations   %s" % (niveau, total[niveau], etat))
    if not total[niveau]:
        muettes.append(niveau)

for niveau in range(DEFAULT_MAX_LEVEL + 1, SONDE_MAX + 1):
    note = ("absente ou inactive (n'echoue pas)" if not total[niveau]
            else "operante mais NON ACTIVEE -- relever DEFAULT_MAX_LEVEL ?")
    print("  T%d  inactive : %5d invocations   %s" % (niveau, total[niveau], note))

# ---------------------------------------------------------------- B
print()
print("== B. DISCRIMINATION : le niveau le plus eleve reclasse-t-il ? ==")
renommage = False
if DEFAULT_MAX_LEVEL >= 1:
    def distribution(niveau_max):
        d = collections.Counter()
        for _nom, rs in REFERENCES:
            random.seed(23)
            for _ in range(INSTANCES):
                sol = random_solution(rs)
                if sol is None:
                    continue
                r = solve_graded(rs, minimal_clues(rs, sol), max_level=niveau_max)
                d[r["max_level"]] += 1
        return d

    haut = distribution(DEFAULT_MAX_LEVEL)
    bas = distribution(DEFAULT_MAX_LEVEL - 1)
    print("  avec T%d      : %s" % (DEFAULT_MAX_LEVEL, dict(sorted(haut.items()))))
    print("  sans T%d      : %s" % (DEFAULT_MAX_LEVEL, dict(sorted(bas.items()))))
    if haut == bas:
        renommage = True
        print("  ECHEC : T%d ne reclasse AUCUN systeme." % DEFAULT_MAX_LEVEL)
        print("          La distribution est identique avec et sans elle : la")
        print("          technique est un RENOMMAGE, pas un palier. Elle")
        print("          s'invoque, mais elle ne mesure rien de neuf.")
    else:
        deplaces = sum((haut - bas).values())
        print("  OK : la distribution change (%d systemes reclasses)." % deplaces)
else:
    print("  (aucun niveau au-dessus de T0 : rien a verifier)")

print()
if muettes or renommage:
    if muettes:
        print("ECHEC : technique(s) activee(s) qui ne se declenchent jamais : %s"
              % ", ".join("T%d" % k for k in muettes))
        print("Une technique activee mais inerte fait croire que la hierarchie")
        print("discrimine sur un niveau qui n'existe pas en pratique.")
        print("Soit la rendre operante, soit abaisser DEFAULT_MAX_LEVEL.")
    if renommage:
        print("ECHEC : T%d s'invoque mais ne reclasse rien -- renommage."
              % DEFAULT_MAX_LEVEL)
        print("Une technique doit creer un palier, pas deplacer une etiquette.")
    sys.exit(1)

print("OK : toute technique activee se declenche, et le niveau le plus eleve")
print("     reclasse effectivement des systemes.")
