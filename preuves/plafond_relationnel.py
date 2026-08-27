# -*- coding: utf-8 -*-
"""gain = 1,000 EXACTEMENT sur 28539 instances : plafond ou bug ?

Un indicateur qui vaut 1 partout est sature -- troisieme cas du motif. Et
`resistance_prop` = 0 signifie « la grille est entierement remplie ». Si elle
est remplie AVEC DE FAUSSES VALEURS, ce n'est pas un plafond, c'est une
unsoundness que canary3 ne couvre pas (c'est du code de banc).

On verifie donc deux choses :
  1. la grille saturee EGALE la solution d'origine ;
  2. de quoi sont faits ces systemes -- « relationnels purs » est une
     hypothese de ma part, pas un fait.
"""
import collections, random, sys
R = "/home/rulesearch/rulesearch"
for p in (R + "/engine", R + "/bench", R):
    sys.path.insert(0, p)
from rulesearch import UNASSIGNED, random_solution, minimal_clues
from t0_legacy import resistance as resistance_t0, candidates_legacy
from propagate import propager
import run as RUN

def saturer(rs, puz):
    n2 = rs.n * rs.n
    g = list(puz)
    while True:
        dom = [{g[i]} if g[i] != UNASSIGNED else set(candidates_legacy(rs, g, i))
               for i in range(n2)]
        if any(not dom[i] for i in range(n2)): break
        _, contra = propager(rs, dom)
        if contra: break
        pose = False
        for i in range(n2):
            if g[i] == UNASSIGNED and len(dom[i]) == 1:
                g[i] = next(iter(dom[i])); pose = True
        if not pose: break
    return g

rng = random.Random(9091)
compo = collections.Counter()
verifiees = fausses = pleines = partielles = 0
sys_sans = 0
for k in range(300):
    rs = RUN.gen_system(4, 3, rng, ["connect", "relational"])
    if rs is None: continue
    kinds = {getattr(c, "kind", None) for c in rs.constraints}
    if "CONNECTED" in kinds: continue
    sys_sans += 1
    compo[tuple(sorted(kinds))] += 1
    random.seed(808 + k)
    for _ in range(4):
        sol = random_solution(rs)
        if sol is None: continue
        puz = minimal_clues(rs, sol)
        g = saturer(rs, puz)
        verifiees += 1
        if all(x != UNASSIGNED for x in g):
            pleines += 1
            if g != sol:
                fausses += 1
        else:
            partielles += 1
    if sys_sans >= 60: break

print("systemes connect SANS CONNECTED : %d" % sys_sans)
print("instances verifiees=%d  grilles pleines=%d  partielles=%d"
      % (verifiees, pleines, partielles))
print("GRILLES PLEINES ET FAUSSES : %d" % fausses)
print()
print("composition de ces systemes :")
for k, c in compo.most_common(8):
    print("   %-40s %d" % (",".join(x for x in k if x), c))
