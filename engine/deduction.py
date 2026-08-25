"""
HIERARCHIE DE DEDUCTION.

v1 ne connaissait qu'une technique ("une seule valeur reste possible ici"),
donc la profondeur saturait vers 2-3 pour tout, sudoku compris : elle ne
mesurait rien.

v2 : trois niveaux, du moins cher au plus cher.
  T0 naked single : une seule valeur reste possible pour une cellule
  T1 hidden single : dans une region, une valeur ne peut aller qu'en une cellule
  T2 contradiction a profondeur 1 : supposer v, saturer T0+T1, si contradiction
     alors eliminer v

La METRIQUE devient le niveau MAXIMAL necessaire, et le nombre de fois ou
chaque niveau a du etre invoque. Un puzzle qui ne tombe qu'a T2 est
structurellement plus profond qu'un puzzle resolu par T0 seul.
"""
from rulesearch import UNASSIGNED


def candidates(rs, g, i):
    out = []
    for v in range(rs.d):
        g[i] = v
        if rs.feasible(g, changed=i):
            out.append(v)
    g[i] = UNASSIGNED
    return out


def apply_T0(rs, g):
    """naked single. retourne (progres, contradiction)"""
    prog = False
    for i in range(rs.n * rs.n):
        if g[i] != UNASSIGNED:
            continue
        c = candidates(rs, g, i)
        if not c:
            return prog, True
        if len(c) == 1:
            g[i] = c[0]
            prog = True
    return prog, False


def t1_regions(rs):
    """
    BUG CORRIGE : hidden single n'est valide QUE sur une region ou chaque
    valeur du domaine DOIT apparaitre. C'est le cas d'un ALLDIFF de taille
    exactement d (principe des tiroirs), pas d'une region quelconque.
    Applique a toute region, T1 force des valeurs a tort -- invisible sur
    le sudoku (qui satisfait la condition) et faux partout ailleurs.
    """
    out = []
    for c in rs.constraints:
        if c.kind == "ALLDIFF" and len(c.region) == rs.d:
            out.append(c.region)
    return out


def apply_T1(rs, g):
    """hidden single : dans une region, une valeur n'a qu'une case possible"""
    prog = False
    for R in t1_regions(rs):
        free = [i for i in R if g[i] == UNASSIGNED]
        if not free:
            continue
        cand = {i: candidates(rs, g, i) for i in free}
        if any(not v for v in cand.values()):
            return prog, True
        for v in range(rs.d):
            spots = [i for i in free if v in cand[i]]
            if len(spots) == 1:
                i = spots[0]
                if g[i] == UNASSIGNED:
                    g[i] = v
                    prog = True
    return prog, False


def saturate_low(rs, g):
    """T0 + T1 jusqu'a stabilite"""
    while True:
        p0, c0 = apply_T0(rs, g)
        if c0:
            return True
        p1, c1 = apply_T1(rs, g)
        if c1:
            return True
        if not (p0 or p1):
            return False


def apply_T2(rs, g):
    """contradiction a profondeur 1"""
    prog = False
    for i in range(rs.n * rs.n):
        if g[i] != UNASSIGNED:
            continue
        cand = candidates(rs, g, i)
        alive = []
        for v in cand:
            trial = list(g)
            trial[i] = v
            if not saturate_low(rs, trial):
                alive.append(v)
        if not alive:
            return prog, True
        if len(alive) < len(cand):
            if len(alive) == 1:
                g[i] = alive[0]
            prog = True
    return prog, False


def solve_graded(rs, puzzle, max_level=2):
    """
    Retourne dict : solved, max_level, uses par niveau.
    max_level = -1 si non resolu sans devinette.
    """
    g = list(puzzle)
    uses = {0: 0, 1: 0, 2: 0}
    top = -1
    while True:
        p0, c0 = apply_T0(rs, g)
        if c0:
            return {"solved": False, "contradiction": True, "max_level": top, "uses": uses}
        if p0:
            uses[0] += 1
            top = max(top, 0)
            continue
        p1, c1 = apply_T1(rs, g)
        if c1:
            return {"solved": False, "contradiction": True, "max_level": top, "uses": uses}
        if p1:
            uses[1] += 1
            top = max(top, 1)
            continue
        if max_level >= 2:
            p2, c2 = apply_T2(rs, g)
            if c2:
                return {"solved": False, "contradiction": True, "max_level": top, "uses": uses}
            if p2:
                uses[2] += 1
                top = max(top, 2)
                continue
        break
    solved = all(x != UNASSIGNED for x in g)
    return {"solved": solved, "contradiction": False, "max_level": top, "uses": uses}
