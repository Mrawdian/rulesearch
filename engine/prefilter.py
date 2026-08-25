"""
Pre-filtre des systemes MORT.

Propagation seule sur grille vide, sans backtracking. Si elle atteint une
contradiction, le systeme n'a aucune solution et le solveur complet est
inutile.

SURETE : le pre-filtre ne peut produire que des vrais positifs. Il ne
declare MORT que sur contradiction effectivement derivee, jamais sur
absence de progres. Un faux positif ferait disparaitre silencieusement un
candidat -- c'est le seul risque et il est exclu par construction. Le
canari le verifie empiriquement.

Mesure sur 240 systemes 4x4 (deux echantillons) :
  T0 seul : 24-31 % des morts attrapes, cout negligeable (0,03 s)
  T0+T2   : 52 % attrapes, mais 4,7 s de cout contre 14 s de solveur
            economise -- ratio nettement moins bon
On garde T0 seul.
"""
from rulesearch import UNASSIGNED
from deduction import apply_T0

MAX_ROUNDS = 6


def is_dead(rs, max_rounds=MAX_ROUNDS):
    """True = MORT prouve par propagation. False = indetermine, il faut le solveur."""
    g = [UNASSIGNED] * (rs.n * rs.n)
    for _ in range(max_rounds):
        progress, contradiction = apply_T0(rs, g)
        if contradiction:
            return True
        if not progress:
            return False
    return False
