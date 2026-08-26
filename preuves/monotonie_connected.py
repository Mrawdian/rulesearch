# -*- coding: utf-8 -*-
"""VERIFICATION EMPIRIQUE des deux affirmations de monotonie sur graphe induit.

A. INACCESSIBILITE : P' inclus dans P  =>  l'ensemble des cellules retirees
   ne peut que CROITRE.
B. ARTICULATION : P' inclus dans P  =>  l'ensemble des cellules FORCEES ne
   peut que CROITRE.  (contredit la premisse "les points d'articulation ne
   sont pas monotones")

On tire des graphes-grilles au hasard, on supprime des sommets au hasard, et
on compare les deux ensembles. Un seul contre-exemple suffit a refuter.
"""
import random, itertools, sys

def voisins(i, n):
    r, c = divmod(i, n)
    out = []
    if c > 0: out.append(i-1)
    if c < n-1: out.append(i+1)
    if r > 0: out.append(i-n)
    if r < n-1: out.append(i+n)
    return out

def accessibles(P, depart, n):
    if depart not in P: return set()
    vus, pile = {depart}, [depart]
    while pile:
        x = pile.pop()
        for y in voisins(x, n):
            if y in P and y not in vus:
                vus.add(y); pile.append(y)
    return vus

def relie(P, a, b, n, interdit=None):
    Q = set(P) - ({interdit} if interdit is not None else set())
    return b in accessibles(Q, a, n) if a in Q else False

def forces_articulation(P, fixes, n):
    """cellules par lesquelles TOUT chemin entre deux fixes doit passer."""
    if len(fixes) < 2: return set()
    a = fixes[0]
    for b in fixes[1:]:
        if not relie(P, a, b, n): return None   # infaisable
    out = set()
    for x in P:
        if x in fixes: continue
        for b in fixes[1:]:
            if not relie(P, a, b, n, interdit=x):
                out.add(x); break
    return out

def retires_inaccessibilite(P, fixes, n, N):
    if not fixes: return set()
    A = accessibles(P, fixes[0], n)
    return set(i for i in range(N) if i not in A)

n = 4; N = n*n
rng = random.Random(11)
ctre_A = ctre_B = 0
essais = 0
for _ in range(4000):
    P = set(i for i in range(N) if rng.random() < 0.7)
    fixes = [i for i in sorted(P) if rng.random() < 0.25][:3]
    if len(fixes) < 2: continue
    if not all(relie(P, fixes[0], b, n) for b in fixes[1:]): continue
    # P' obtenu en retirant des sommets non fixes
    Pp = set(i for i in P if i in fixes or rng.random() < 0.8)
    if Pp == P: continue
    if not all(relie(Pp, fixes[0], b, n) for b in fixes[1:]): continue
    essais += 1
    rA, rAp = (retires_inaccessibilite(P, fixes, n, N),
               retires_inaccessibilite(Pp, fixes, n, N))
    if not rA <= rAp:
        ctre_A += 1
        if ctre_A == 1: print("CONTRE-EXEMPLE A :", sorted(P), fixes, sorted(Pp))
    fB, fBp = forces_articulation(P, fixes, n), forces_articulation(Pp, fixes, n)
    if fB is not None and fBp is not None and not fB <= fBp:
        ctre_B += 1
        if ctre_B == 1:
            print("CONTRE-EXEMPLE B :")
            print("  P  =", sorted(P), " forces =", sorted(fB))
            print("  P' =", sorted(Pp), " forces =", sorted(fBp))

print()
print("essais retenus      :", essais)
print("contre-exemples A (inaccessibilite) :", ctre_A)
print("contre-exemples B (articulation)    :", ctre_B)
print()
print("A monotone" if not ctre_A else "A NON MONOTONE")
print("B monotone" if not ctre_B else "B NON MONOTONE")
