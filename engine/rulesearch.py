"""
Recherche dans l'espace des SYSTEMES DE REGLES (pas des instances).

Un systeme de regles = un ensemble de contraintes sur une grille n x n
a valeurs dans {0..d-1}.

Pour chaque systeme on mesure, par le calcul seul :
  - taux d'instances a solution unique
  - taux d'instances resolubles par deduction pure (sans devinette)
  - profondeur de deduction moyenne
  - densite d'indices necessaire

Un systeme est un CANDIDAT si : deduction pure frequente, peu d'indices
necessaires, profondeur non triviale.
"""
import random
from itertools import combinations

UNASSIGNED = -1


# ---------- regions ----------

def rows(n):
    return [[r * n + c for c in range(n)] for r in range(n)]

def cols(n):
    return [[r * n + c for r in range(n)] for c in range(n)]

def diags(n):
    return [[i * n + i for i in range(n)], [i * n + (n - 1 - i) for i in range(n)]]

def blocks(n):
    # seulement si n est un carre parfait
    b = int(round(n ** 0.5))
    if b * b != n:
        return []
    out = []
    for br in range(b):
        for bc in range(b):
            out.append([(br * b + r) * n + (bc * b + c) for r in range(b) for c in range(b)])
    return out

REGION_FAMILIES = {
    "rows": rows,
    "cols": cols,
    "diags": diags,
    "blocks": blocks,
}


# ---------- contraintes ----------
# chaque contrainte expose feasible(grid) -> bool sur assignation PARTIELLE

class Count:
    """le nombre de cellules valant `val` dans la region est dans [lo, hi]"""
    kind = "COUNT"
    def __init__(self, region, val, lo, hi):
        self.region, self.val, self.lo, self.hi = region, val, lo, hi
    def feasible(self, g):
        cur = unk = 0
        for i in self.region:
            if g[i] == UNASSIGNED:
                unk += 1
            elif g[i] == self.val:
                cur += 1
        return cur <= self.hi and cur + unk >= self.lo
    def __repr__(self):
        return f"COUNT(v={self.val},[{self.lo},{self.hi}])"


class AllDiff:
    kind = "ALLDIFF"
    def __init__(self, region):
        self.region = region
    def feasible(self, g):
        seen = set()
        for i in self.region:
            v = g[i]
            if v != UNASSIGNED:
                if v in seen:
                    return False
                seen.add(v)
        return True
    def __repr__(self):
        return "ALLDIFF"


class SumRange:
    kind = "SUM"
    def __init__(self, region, lo, hi, d):
        self.region, self.lo, self.hi, self.d = region, lo, hi, d
    def feasible(self, g):
        s = unk = 0
        for i in self.region:
            if g[i] == UNASSIGNED:
                unk += 1
            else:
                s += g[i]
        return s <= self.hi and s + unk * (self.d - 1) >= self.lo
    def __repr__(self):
        return f"SUM([{self.lo},{self.hi}])"


class NeqAdj:
    """cellules consecutives dans l'ordre de la region doivent differer"""
    kind = "NEQADJ"
    def __init__(self, region):
        self.region = region
    def feasible(self, g):
        for a, b in zip(self.region, self.region[1:]):
            if g[a] != UNASSIGNED and g[b] != UNASSIGNED and g[a] == g[b]:
                return False
        return True
    def __repr__(self):
        return "NEQADJ"


class NoTriple:
    """pas trois valeurs identiques consecutives dans la region"""
    kind = "NOTRIPLE"
    def __init__(self, region):
        self.region = region
    def feasible(self, g):
        R = self.region
        for k in range(len(R) - 2):
            a, b, c = g[R[k]], g[R[k + 1]], g[R[k + 2]]
            if a != UNASSIGNED and a == b == c:
                return False
        return True
    def __repr__(self):
        return "NOTRIPLE"


class Mono:
    """non decroissant le long de la region (paires assignees seulement)"""
    kind = "MONO"
    def __init__(self, region):
        self.region = region
    def feasible(self, g):
        for a, b in zip(self.region, self.region[1:]):
            if g[a] != UNASSIGNED and g[b] != UNASSIGNED and g[a] > g[b]:
                return False
        return True
    def __repr__(self):
        return "MONO"


# ---------- systeme de regles ----------

class RuleSystem:
    def __init__(self, n, d, constraints, label):
        self.n, self.d = n, d
        self.constraints = constraints
        self.label = label
        # index cellule -> contraintes qui la touchent (pour propagation ciblee)
        self.touch = [[] for _ in range(n * n)]
        for c in constraints:
            for i in c.region:
                self.touch[i].append(c)

    def feasible(self, g, changed=None):
        cs = self.touch[changed] if changed is not None else self.constraints
        for c in cs:
            if not c.feasible(g):
                return False
        return True

    def __repr__(self):
        return self.label


# ---------- solveur : compte les solutions (arret a `cap`) ----------

def count_solutions(rs, grid, cap=2, node_budget=200000):
    n, d = rs.n, rs.d
    g = list(grid)
    order = [i for i in range(n * n) if g[i] == UNASSIGNED]
    found = 0
    nodes = 0

    def rec(k):
        nonlocal found, nodes
        if found >= cap:
            return
        nodes += 1
        if nodes > node_budget:
            raise TimeoutError
        if k == len(order):
            found += 1
            return
        i = order[k]
        for v in range(d):
            g[i] = v
            if rs.feasible(g, changed=i):
                rec(k + 1)
                if found >= cap:
                    g[i] = UNASSIGNED
                    return
            g[i] = UNASSIGNED

    try:
        rec(0)
    except TimeoutError:
        return None
    return found


# ---------- deduction pure : aucune supposition ----------

def deduce(rs, grid):
    """
    Propagation : une cellule est forcee si une seule valeur du domaine
    garde toutes les contraintes faisables.
    Retourne (grille, profondeur, contradiction)
    profondeur = nombre de passes de propagation
    """
    n, d = rs.n, rs.d
    g = list(grid)
    depth = 0
    while True:
        progress = False
        depth += 1
        for i in range(n * n):
            if g[i] != UNASSIGNED:
                continue
            ok = []
            for v in range(d):
                g[i] = v
                if rs.feasible(g, changed=i):
                    ok.append(v)
                g[i] = UNASSIGNED
            if len(ok) == 0:
                return g, depth, True
            if len(ok) == 1:
                g[i] = ok[0]
                progress = True
        if not progress:
            return g, depth - 1, False


# ---------- generation d'instances ----------

def random_solution(rs, tries=60):
    n, d = rs.n, rs.d
    for _ in range(tries):
        g = [UNASSIGNED] * (n * n)
        order = list(range(n * n))
        random.shuffle(order)
        ok = True
        for i in order:
            vals = list(range(d))
            random.shuffle(vals)
            placed = False
            for v in vals:
                g[i] = v
                if rs.feasible(g, changed=i):
                    placed = True
                    break
                g[i] = UNASSIGNED
            if not placed:
                ok = False
                break
        if ok:
            # verifie globalement
            if rs.feasible(g):
                return g
    return None


def minimal_clues(rs, sol, max_removals=None):
    """retire des indices tant que l'unicite tient"""
    n = rs.n
    cells = list(range(n * n))
    random.shuffle(cells)
    puz = list(sol)
    removed = 0
    for i in cells:
        if max_removals is not None and removed >= max_removals:
            break
        keep = puz[i]
        puz[i] = UNASSIGNED
        cnt = count_solutions(rs, puz, cap=2)
        if cnt != 1:
            puz[i] = keep
        else:
            removed += 1
    return puz


# ---------- evaluation d'un systeme ----------

def evaluate(rs, n_instances=8):
    n = rs.n
    cells = n * n
    stats = {
        "instances": 0,
        "deducible": 0,
        "clue_frac": [],
        "depths": [],
        "dead": False,
    }
    for _ in range(n_instances):
        sol = random_solution(rs)
        if sol is None:
            stats["dead"] = True
            break
        puz = minimal_clues(rs, sol)
        given = sum(1 for x in puz if x != UNASSIGNED)
        stats["instances"] += 1
        stats["clue_frac"].append(given / cells)
        filled, depth, contra = deduce(rs, puz)
        if not contra and all(x != UNASSIGNED for x in filled):
            stats["deducible"] += 1
            stats["depths"].append(depth)
    return stats


# ---------- enumeration de systemes de regles ----------

def gen_random_system(n, d, rng):
    fams = [f for f in REGION_FAMILIES if REGION_FAMILIES[f](n)]
    k = rng.randint(2, 3)
    chosen = rng.sample(fams, min(k, len(fams)))
    cons = []
    parts = []
    for fam in chosen:
        regions = REGION_FAMILIES[fam](n)
        ctype = rng.choice(["ALLDIFF", "COUNT", "SUM", "NEQADJ", "NOTRIPLE", "MONO"])
        if ctype == "ALLDIFF":
            if d < n:
                continue
            for R in regions:
                cons.append(AllDiff(R))
        elif ctype == "COUNT":
            val = rng.randrange(d)
            lo = rng.randint(0, max(0, n // 2))
            hi = lo + rng.randint(0, 1)
            for R in regions:
                cons.append(Count(R, val, lo, min(hi, len(R))))
            ctype = f"COUNT(v{val},{lo}-{hi})"
        elif ctype == "SUM":
            target = rng.randint(0, (d - 1) * n)
            slack = rng.randint(0, 1)
            for R in regions:
                cons.append(SumRange(R, max(0, target - slack), target + slack, d))
            ctype = f"SUM({target}+-{slack})"
        elif ctype == "NEQADJ":
            for R in regions:
                cons.append(NeqAdj(R))
        elif ctype == "NOTRIPLE":
            for R in regions:
                cons.append(NoTriple(R))
        elif ctype == "MONO":
            for R in regions:
                cons.append(Mono(R))
        parts.append(f"{ctype}@{fam}")
    if not cons:
        return None
    return RuleSystem(n, d, cons, " + ".join(parts))
