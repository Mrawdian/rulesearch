"""
DSL v2 : ce qui manquait au v1.

v1 = regions statiques (lignes, colonnes, blocs, diagonales) -> redecouvre le sudoku.
v2 ajoute trois familles qui n'ont pas d'equivalent en v1 :

  CAGES        : partitions connexes aleatoires de la grille (l'espace des
                 partitions est enorme, contrairement aux 4 familles fixes)
  RELATIONNEL  : contraintes sur des PAIRES definies par la geometrie
                 (adjacence, saut de cavalier) et non sur des ensembles
  CONNECTIVITE : les cellules d'une valeur donnee forment une composante
                 connexe. NON DECOMPOSABLE en contraintes locales -> c'est
                 le seul type qui devrait resister a la propagation naive.
"""
import random
from rulesearch import UNASSIGNED


def neighbors4(i, n):
    r, c = divmod(i, n)
    out = []
    if r > 0: out.append(i - n)
    if r < n - 1: out.append(i + n)
    if c > 0: out.append(i - 1)
    if c < n - 1: out.append(i + 1)
    return out


def knight_pairs(n):
    out = []
    for i in range(n * n):
        r, c = divmod(i, n)
        for dr, dc in ((1, 2), (2, 1), (-1, 2), (-2, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n:
                out.append((i, rr * n + cc))
    return out


def adj_pairs(n):
    out = []
    for i in range(n * n):
        r, c = divmod(i, n)
        if c < n - 1: out.append((i, i + 1))
        if r < n - 1: out.append((i, i + n))
    return out


def random_cages(n, rng, min_size=2, max_size=4):
    """partition de la grille en zones connexes de taille aleatoire"""
    remaining = set(range(n * n))
    cages = []
    while remaining:
        seed = rng.choice(sorted(remaining))
        target = rng.randint(min_size, max_size)
        cage = [seed]
        remaining.discard(seed)
        frontier = [x for x in neighbors4(seed, n) if x in remaining]
        while len(cage) < target and frontier:
            pick = rng.choice(frontier)
            if pick not in remaining:
                frontier.remove(pick)
                continue
            cage.append(pick)
            remaining.discard(pick)
            frontier = [x for x in frontier if x in remaining]
            frontier += [x for x in neighbors4(pick, n) if x in remaining]
        cages.append(cage)
    return cages


# ---------- contraintes relationnelles ----------

class PairDiff:
    """pour chaque paire (a,b) de la liste : |g[a]-g[b]| >= k"""
    kind = "PAIRDIFF"
    def __init__(self, pairs, k, n):
        self.pairs, self.k = pairs, k
        self.region = sorted({x for p in pairs for x in p})
        self.by_cell = {}
        for a, b in pairs:
            self.by_cell.setdefault(a, []).append(b)
            self.by_cell.setdefault(b, []).append(a)
    def feasible(self, g):
        for a, b in self.pairs:
            if g[a] != UNASSIGNED and g[b] != UNASSIGNED:
                if abs(g[a] - g[b]) < self.k:
                    return False
        return True
    def __repr__(self):
        return f"PAIRDIFF(>={self.k})"


class PairRatio:
    """pour chaque paire adjacente : soit egales, soit l'une = l'autre + delta"""
    kind = "PAIRSTEP"
    def __init__(self, pairs, delta):
        self.pairs, self.delta = pairs, delta
        self.region = sorted({x for p in pairs for x in p})
    def feasible(self, g):
        for a, b in self.pairs:
            if g[a] != UNASSIGNED and g[b] != UNASSIGNED:
                if abs(g[a] - g[b]) not in (0, self.delta):
                    return False
        return True
    def __repr__(self):
        return f"PAIRSTEP(d={self.delta})"


# ---------- connectivite : le type qui resiste ----------

class Connected:
    """
    les cellules de valeur `val` forment UNE composante connexe (4-connexite).
    Sur assignation partielle : infaisable si les cellules DEJA assignees a
    `val` ne peuvent plus etre reliees en n'empruntant que des cellules
    valant `val` ou encore libres.
    """
    kind = "CONNECTED"
    def __init__(self, n, val):
        self.n, self.val = n, val
        self.region = list(range(n * n))
    def feasible(self, g):
        n, val = self.n, self.val
        fixed = [i for i in range(n * n) if g[i] == val]
        if len(fixed) <= 1:
            return True
        passable = set(i for i in range(n * n) if g[i] == val or g[i] == UNASSIGNED)
        start = fixed[0]
        stack, seen = [start], {start}
        while stack:
            x = stack.pop()
            for y in neighbors4(x, n):
                if y in passable and y not in seen:
                    seen.add(y)
                    stack.append(y)
        return all(f in seen for f in fixed)
    def __repr__(self):
        return f"CONNECTED(v={self.val})"


class NoSquare:
    """aucun carre 2x2 monochrome de valeur `val`"""
    kind = "NOSQUARE"
    def __init__(self, n, val):
        self.n, self.val = n, val
        self.region = list(range(n * n))
    def feasible(self, g):
        n, val = self.n, self.val
        for r in range(n - 1):
            for c in range(n - 1):
                q = [g[r * n + c], g[r * n + c + 1], g[(r + 1) * n + c], g[(r + 1) * n + c + 1]]
                if all(x == val for x in q):
                    return False
        return True
    def __repr__(self):
        return f"NOSQUARE(v={self.val})"
