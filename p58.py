# -*- coding: utf-8 -*-
import io

def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, s): io.open(p, "w", encoding="utf-8").write(s)

P = "bench/gain_propagation.py"
s = rd(P)

# ---- import du module pour piloter le drapeau ----
OLD = "from propagate import domaines, propager\n"
assert s.count(OLD) == 1
s = s.replace(OLD, "from propagate import domaines, propager\nimport propagate as PG\n", 1)

# ---- resistance_prop : parametree par le drapeau ----
OLD = "def resistance_prop(rs, puzzle):"
assert s.count(OLD) == 1
NEW = ("""def resistance_prop(rs, puzzle, articulation=False):
    \"\"\"Enveloppe : pose ET RESTAURE le drapeau `ARTICULATION`.

    Le forcage par sommet separateur (27/08/2026) est active ici et nulle part
    ailleurs. La restauration en `finally` est ce qui garantit qu'aucune fuite
    n'atteint le bras de reference, qui doit rester BYTE POUR BYTE celui du
    26/08 -- sans quoi les deux bras ne seraient pas comparables.
    \"\"\"
    ancien = PG.ARTICULATION
    PG.ARTICULATION = articulation
    try:
        return _resistance_prop(rs, puzzle)
    finally:
        PG.ARTICULATION = ancien


def _resistance_prop(rs, puzzle):""")
s = s.replace(OLD, NEW, 1)

# ---- mesurer_systeme : TROIS mesures appariees sur le meme puzzle ----
OLD = '''def mesurer_systeme(rs, instances, graine):
    """Rend (inc_t0, left_t0, inc_pr, left_pr) en BRUT, jamais de ratio."""
    random.seed(graine)
    it = lt = ip = lp = 0
    n = 0
    for _ in range(instances):
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        a, b = resistance_t0(rs, puz)
        c, e = resistance_prop(rs, puz)
        assert a == c, "les deux mesures ne partent pas du meme puzzle"
        if e > b:
            raise AssertionError(
                "resistance_prop > resistance_T0 : la saturation forte est "
                "plus faible que la reference, ce qui est impossible par "
                "construction. Bug, pas resultat.")
        it += a
        lt += b
        ip += c
        lp += e
        n += 1
    return (it, lt, ip, lp, n)'''
assert s.count(OLD) == 1
NEW = '''def mesurer_systeme(rs, instances, graine):
    """Rend (inc, left_T0, left_prop, left_prop_ART, n) en BRUT.

    LES TROIS MESURES SONT APPARIEES sur le MEME puzzle. C'est ce qui rend le
    controle de circularite lisible : la seule chose qui change entre le bras
    du 26/08 et celui du 27/08 est le drapeau, pas le tirage.

    ORDRE ATTENDU, par construction et non par observation :
        left_T0  >=  left_prop  >=  left_prop_ART
    la propagation etant un FILTRE devant la meme saturation T0 gelee, et
    l'articulation n'ajoutant que des deductions. Toute inversion est un BUG,
    et le banc s'arrete plutot que de la rapporter.
    """
    random.seed(graine)
    it = lt = lp = la = 0
    n = 0
    for _ in range(instances):
        sol = random_solution(rs)
        if sol is None:
            continue
        puz = minimal_clues(rs, sol)
        a, b = resistance_t0(rs, puz)
        c, e = resistance_prop(rs, puz, articulation=False)
        c2, f = resistance_prop(rs, puz, articulation=True)
        assert a == c == c2, "les mesures ne partent pas du meme puzzle"
        if e > b:
            raise AssertionError(
                "resistance_prop > resistance_T0 : la saturation forte est "
                "plus faible que la reference, ce qui est impossible par "
                "construction. Bug, pas resultat.")
        if f > e:
            raise AssertionError(
                "l'articulation LAISSE PLUS de cellules que sans elle : une "
                "regle qui n'ajoute que des deductions ne peut pas en retirer. "
                "Bug, pas resultat.")
        it += a
        lt += b
        lp += e
        la += f
        n += 1
    return (it, lt, lp, la, n)'''
s = s.replace(OLD, NEW, 1)

# ---- garde 1 : verifier AUSSI que l'articulation n'est pas inerte ----
OLD = '''    identiques = differentes = 0
    lt_tot = lp_tot = it_tot = 0
    for rs in echantillon:
        it, lt, ip, lp, n = mesurer_systeme(rs, instances, 909)
        if not n:
            continue
        it_tot += it
        lt_tot += lt
        lp_tot += lp
        if lt == lp:
            identiques += 1
        else:
            differentes += 1'''
assert s.count(OLD) == 1
NEW = '''    identiques = differentes = 0
    art_identiques = art_differentes = 0
    lt_tot = lp_tot = la_tot = it_tot = 0
    for rs in echantillon:
        it, lt, lp, la, n = mesurer_systeme(rs, instances, 909)
        if not n:
            continue
        it_tot += it
        lt_tot += lt
        lp_tot += lp
        la_tot += la
        if lt == lp:
            identiques += 1
        else:
            differentes += 1
        if lp == la:
            art_identiques += 1
        else:
            art_differentes += 1'''
s = s.replace(OLD, NEW, 1)

OLD = '''    print("  brut : inconnues=%d  restantes_T0=%d  restantes_prop=%d"
          % (it_tot, lt_tot, lp_tot))'''
assert s.count(OLD) == 1
NEW = '''    print("  articulation : resistances identiques : %d   differentes : %d"
          % (art_identiques, art_differentes))
    print("  brut : inconnues=%d  restantes_T0=%d  restantes_prop=%d  "
          "restantes_prop_ART=%d" % (it_tot, lt_tot, lp_tot, la_tot))'''
s = s.replace(OLD, NEW, 1)

OLD = '''    print("  OK : les deux mesures different, aucune ne sature.")
    return True'''
assert s.count(OLD) == 1
NEW = '''    if art_differentes == 0:
        print("  ARRET : L'ARTICULATION EST INERTE sur ces systemes.")
        print("  Elle ne change AUCUNE resistance. Le controle de circularite")
        print("  comparerait alors deux fois le MEME propagateur, et son")
        print("  resultat -- quel qu'il soit -- ne dirait rien sur la force")
        print("  du propagateur. C'est precisement le piege qu'il vient")
        print("  fermer : un instrument qui ne distingue pas ne controle pas.")
        return False
    print("  OK : les trois mesures different, aucune ne sature.")
    return True'''
s = s.replace(OLD, NEW, 1)

# ---- la mesure principale : remplacement du bloc de fin ----
ANC = '    print("== MESURE ==")
'
assert s.count(ANC) == 1
s = s[:s.index(ANC) + len(ANC)] + '''    brut = {}
    gains = {}
    gains_art = {}
    for t in tags:
        it = lt = lp = la = 0
        g, ga = [], []
        for rs in par_tag[t]:
            a1, b1, e1, f1, n1 = mesurer_systeme(rs, a.instances, 707)
            if not n1 or b1 == 0:
                continue
            it += a1
            lt += b1
            lp += e1
            la += f1
            g.append((b1 - e1) / float(b1))
            ga.append((b1 - f1) / float(b1))
        brut[t] = (it, lt, lp, la)
        gains[t] = g
        gains_art[t] = ga
        # LES BRUTS, JAMAIS LE RATIO SEUL. Refaire le rapport a la main est le
        # seul controle qui ne passe pas par le chiffre qu'on veut lire.
        print("  %-12s n=%-4d  inconnues=%-6d  restantes_T0=%-6d  "
              "restantes_prop=%-6d  restantes_ART=%-6d"
              % (t, len(g), it, lt, lp, la))
        if lt:
            print("               SANS articulation : gain agrege = %.3f   "
                  "moyen = %.3f" % ((lt - lp) / float(lt),
                                    sum(g) / len(g) if g else float("nan")))
            print("               AVEC articulation : gain agrege = %.3f   "
                  "moyen = %.3f" % ((lt - la) / float(lt),
                                    sum(ga) / len(ga) if ga else float("nan")))
    print()
    if len(tags) == 2 and all(gains[t] for t in tags):
        for nom, G in (("SANS articulation (bras du 26/08)", gains),
                       ("AVEC articulation (controle du 27/08)", gains_art)):
            p = permutation(G[tags[0]], G[tags[1]])
            m0 = sum(G[tags[0]]) / len(G[tags[0]])
            m1 = sum(G[tags[1]]) / len(G[tags[1]])
            print("  ECART ENTRE TAGS, %s :" % nom)
            print("    %s %.3f  vs  %s %.3f   p = %.4f"
                  % (tags[0], m0, tags[1], m1, p))
        print()
        print("  LE CONTROLE DE CIRCULARITE SE LIT SUR LA LIGNE `connect`,")
        print("  ET SUR ELLE SEULE :")
        print("    - si le gain AVEC articulation y reste bas, la resistance")
        print("      est une propriete de LA CONTRAINTE et non de notre")
        print("      implementation : la circularite tombe ;")
        print("    - s'il monte vers celui de static-ref, ce qu'on mesurait")
        print("      etait la FAIBLESSE DE NOTRE PROPAGATEUR, et l'hypothese")
        print("      centrale perd son meilleur soutien.")
        print("  Les deux issues etaient ecrites AVANT la mesure")
        print("  (DECISIONS.md, 27/08). Aucune n'est l'issue esperee.")


if __name__ == "__main__":
    main()
'''
wr(P, s)
print("gain_propagation.py : bras articulation")


# ================= gain_strates.py : intra-tag avec articulation =========
P = "bench/gain_strates.py"
s = rd(P)

OLD = """        inc, left_t0 = resistance_t0(rs, puz)
        _, left_pr = resistance_prop(rs, puz)
        if left_pr > left_t0:
            raise AssertionError("gain negatif : bug, pas resultat.")
        out.append({
            "inc": inc,
            "t0": left_t0,
            "pr": left_pr,
            "clue_frac": (n2 - inc) / float(n2),
        })"""
assert s.count(OLD) == 1
NEW = """        inc, left_t0 = resistance_t0(rs, puz)
        _, left_pr = resistance_prop(rs, puz, articulation=False)
        _, left_ar = resistance_prop(rs, puz, articulation=True)
        if left_pr > left_t0 or left_ar > left_pr:
            raise AssertionError("gain negatif : bug, pas resultat.")
        out.append({
            "inc": inc,
            "t0": left_t0,
            "pr": left_pr,
            "ar": left_ar,
            "clue_frac": (n2 - inc) / float(n2),
        })"""
s = s.replace(OLD, NEW, 1)

OLD = """def agrege(lignes):
    t0 = sum(l["t0"] for l in lignes)
    pr = sum(l["pr"] for l in lignes)
    inc = sum(l["inc"] for l in lignes)
    if not t0:
        return None
    return {"n": len(lignes), "inc": inc, "t0": t0, "pr": pr,
            "gain_agrege": (t0 - pr) / float(t0),
            "resistance_t0": t0 / float(inc) if inc else 0.0}


def gains_par_ligne(lignes):
    return [(l["t0"] - l["pr"]) / float(l["t0"]) for l in lignes if l["t0"]]


def afficher(nom, lignes):
    a = agrege(lignes)
    if a is None:
        print("  %-34s aucune resistance a recuperer" % nom)
        return None
    g = gains_par_ligne(lignes)
    print("  %-34s inst=%-5d inconnues=%-7d T0=%-7d prop=%-7d "
          "resist=%.3f gain_agr=%.3f gain_moy=%.3f"
          % (nom, a["n"], a["inc"], a["t0"], a["pr"], a["resistance_t0"],
             a["gain_agrege"], sum(g) / len(g) if g else float("nan")))
    return g"""
assert s.count(OLD) == 1
NEW = """def agrege(lignes):
    t0 = sum(l["t0"] for l in lignes)
    pr = sum(l["pr"] for l in lignes)
    ar = sum(l["ar"] for l in lignes)
    inc = sum(l["inc"] for l in lignes)
    if not t0:
        return None
    return {"n": len(lignes), "inc": inc, "t0": t0, "pr": pr, "ar": ar,
            "gain_agrege": (t0 - pr) / float(t0),
            "gain_art": (t0 - ar) / float(t0),
            "resistance_t0": t0 / float(inc) if inc else 0.0}


def gains_par_ligne(lignes, cle="pr"):
    return [(l["t0"] - l[cle]) / float(l["t0"]) for l in lignes if l["t0"]]


def afficher(nom, lignes):
    a = agrege(lignes)
    if a is None:
        print("  %-34s aucune resistance a recuperer" % nom)
        return None, None
    g = gains_par_ligne(lignes, "pr")
    ga = gains_par_ligne(lignes, "ar")
    print("  %-34s inst=%-5d T0=%-7d prop=%-7d ART=%-7d resist=%.3f "
          "gain=%.3f gain_ART=%.3f"
          % (nom, a["n"], a["t0"], a["pr"], a["ar"], a["resistance_t0"],
             a["gain_agrege"], a["gain_art"]))
    return g, ga"""
s = s.replace(OLD, NEW, 1)

s = s.replace('        g[cle] = afficher(cle, lignes[cle]) or []',
              '        g[cle], ga[cle] = afficher(cle, lignes[cle])\n'
              '        g[cle] = g[cle] or []\n'
              '        ga[cle] = ga[cle] or []', 1)
s = s.replace("    print(\"-- par groupe --\")\n    g = {}",
              "    print(\"-- par groupe --\")\n    g = {}\n    ga = {}", 1)

# le controle intra-tag : les DEUX bras
OLD = '''    if g["connect_sans_CONNECTED"] and g["connect_avec_CONNECTED"]:
        p = permutation(g["connect_sans_CONNECTED"], g["connect_avec_CONNECTED"])
        m1 = sum(g["connect_sans_CONNECTED"]) / len(g["connect_sans_CONNECTED"])
        m2 = sum(g["connect_avec_CONNECTED"]) / len(g["connect_avec_CONNECTED"])
        print("  sans CONNECTED %.3f  vs  avec CONNECTED %.3f   p = %.4f"
              % (m1, m2, p))'''
assert s.count(OLD) == 1
NEW = '''    if g["connect_sans_CONNECTED"] and g["connect_avec_CONNECTED"]:
        for nom, G in (("SANS articulation", g), ("AVEC articulation", ga)):
            p = permutation(G["connect_sans_CONNECTED"],
                            G["connect_avec_CONNECTED"])
            m1 = (sum(G["connect_sans_CONNECTED"])
                  / len(G["connect_sans_CONNECTED"]))
            m2 = (sum(G["connect_avec_CONNECTED"])
                  / len(G["connect_avec_CONNECTED"]))
            print("  %-18s sans CONNECTED %.3f  vs  avec CONNECTED %.3f"
                  "   p = %.4f" % (nom, m1, m2, p))'''
s = s.replace(OLD, NEW, 1)

# le second contraste utilise encore g[...] : le laisser sur le bras sans art
OLD = '''    if g["static-ref"] and g["connect_sans_CONNECTED"]:'''
assert s.count(OLD) == 1
NEW = '''    # RAPPEL : `connect_sans_CONNECTED` est AU PLAFOND (gain 1,000). Toute
    # comparaison qui l'implique est une comparaison de plafond et ne peut pas
    # etayer un « ils se ressemblent ». Affiche pour memoire, pas pour conclure.
    if g["static-ref"] and g["connect_sans_CONNECTED"]:'''
s = s.replace(OLD, NEW, 1)
wr(P, s)
print("gain_strates.py : bras articulation")
