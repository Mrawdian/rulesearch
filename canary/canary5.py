"""
CANARI DE SURETE DE L'INTERRUPTION PAR ALARME.

Ce chemin de code a deja echoue silencieusement une fois : une borne de temps
testee ENTRE les appels couteux ne pouvait rien interrompre quand le blocage
etait DANS un appel. Le compteur affichait "TROP-CHER : 0", ce qui se lisait a
tort comme "aucun systeme trop cher". Il ne doit plus pouvoir le faire.

Deux verifications symetriques, les deux modes de defaillance :

  A. FAUX NEGATIF -- l'alarme ne se declenche pas. Un systeme pathologique
     gele un bloc entier indefiniment. C'est ce qui est arrive.
     On rend `minimal_clues` volontairement pathologique : boucle de calcul
     pur, sans appel systeme et sans test d'heure, que SEUL un signal peut
     interrompre. TROP-CHER doit sortir, avec phase == "minimal_clues" et
     interrompu == True.

  B. FAUX POSITIF -- l'alarme se declenche sur un systeme normal. Un systeme
     sain serait etiquete TROP-CHER et disparaitrait des candidats, sans
     laisser de trace : exactement le mode de defaillance du pre-filtre que
     surveille canary4.
     Avec un budget large et le vrai `minimal_clues`, aucun record ne doit
     porter TROP-CHER sans avoir reellement consomme son budget.

Le test s'execute dans un repertoire temporaire (`run.HERE` redirige, `engine/`
lie symboliquement) : ni `runs/`, ni `found/`, ni `summary.md` du depot ne sont
touches.

Sortie non nulle = l'interruption par alarme n'est pas fiable.
"""
import glob
import json
import os
import shutil
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "engine"))

import run

VRAI_MINIMAL_CLUES = run.minimal_clues
VRAI_HERE = run.HERE


def lance(tag, seed, n_systemes, max_seconds):
    """Execute run.main() dans un bac a sable et rend les records produits."""
    bac = tempfile.mkdtemp(prefix="canary5-")
    try:
        os.symlink(os.path.join(VRAI_HERE, "engine"), os.path.join(bac, "engine"))
        run.HERE = bac
        sys.argv = ["run.py", "--n", "4", "--d", "3", "--tag", tag,
                    "--families", "connect,relational", "--seed", str(seed),
                    "--max-systems", str(n_systemes),
                    "--max-seconds", str(max_seconds), "--skip-canary"]
        try:
            run.main()
        except SystemExit:
            pass
        recs = []
        for f in glob.glob(os.path.join(bac, "runs", "*", "results.jsonl")):
            for ligne in open(f):
                ligne = ligne.strip()
                if ligne:
                    recs.append(json.loads(ligne))
        return recs
    finally:
        run.HERE = VRAI_HERE
        shutil.rmtree(bac, ignore_errors=True)


def bloque_sans_relache(rs, sol):
    """Ne rend jamais la main d'elle-meme et ne consulte jamais l'heure."""
    x = 0
    fin = time.time() + 600
    while time.time() < fin:
        x += 1
    return sol


ok = True
impl = "pypy3" if hasattr(sys, "pypy_version_info") else "cpython"
print("== interpreteur : %s ==" % impl)
print()

# ---------------------------------------------------------------- A
SEUIL_A = 3
print("== A. FAUX NEGATIF : l'alarme doit interrompre un appel bloquant ==")
run.minimal_clues = bloque_sans_relache
try:
    recs_a = lance("canary5a", 7, 40, SEUIL_A)
finally:
    run.minimal_clues = VRAI_MINIMAL_CLUES

cher = [r for r in recs_a if r["verdict"] == "TROP-CHER"]
autres = [r for r in recs_a if r["verdict"] != "TROP-CHER"]
phases = sorted(set(r.get("phase") for r in cher))
print("  systemes             : %d" % len(recs_a))
print("  TROP-CHER            : %d, phases %s" % (len(cher), phases))
print("  autres verdicts      : %d" % len(autres))

if not cher:
    print("  ECHEC : aucun TROP-CHER -- l'alarme ne se declenche pas.")
    print("          un systeme pathologique gelerait un bloc entier.")
    ok = False
else:
    vises = [r for r in cher if r.get("phase") == "minimal_clues"]
    if not vises:
        print("  ECHEC : aucun TROP-CHER en phase 'minimal_clues' (phases vues : %s)"
              % phases)
        ok = False
    elif not all(r.get("interrompu") for r in vises):
        print("  ECHEC : 'interrompu' absent -- l'arret ne vient pas du signal.")
        ok = False
    else:
        trop_long = [r for r in vises if r["ms"] > (SEUIL_A + 5) * 1000]
        if trop_long:
            print("  ECHEC : %d ms pour un seuil de %d s -- interruption trop tardive."
                  % (trop_long[0]["ms"], SEUIL_A))
            ok = False
        else:
            print("  OK : interrompu en phase minimal_clues, elapsed_s=%s"
                  % vises[0].get("elapsed_s"))

# l'alarme doit etre desarmee apres chaque systeme : sinon elle deborderait
# sur le suivant et TOUT deviendrait TROP-CHER.
if cher and not autres:
    print("  ECHEC : tous les systemes sont TROP-CHER -- l'alarme n'est pas")
    print("          desarmee entre deux systemes (signal.alarm(0) manquant).")
    ok = False
elif autres:
    print("  OK : %d systemes evalues normalement apres interruption"
          " (alarme bien desarmee)" % len(autres))
print()

# ---------------------------------------------------------------- B
SEUIL_B = 30
print("== B. FAUX POSITIF : un systeme normal ne doit pas etre TROP-CHER ==")
recs_b = lance("canary5b", 11, 12, SEUIL_B)
cher_b = [r for r in recs_b if r["verdict"] == "TROP-CHER"]
sains = [r for r in recs_b if r["verdict"] != "TROP-CHER"]
print("  systemes             : %d" % len(recs_b))
print("  TROP-CHER            : %d" % len(cher_b))
print("  verdicts normaux     : %d" % len(sains))

if not sains:
    print("  ECHEC : aucun systeme evalue normalement -- l'alarme frappe tout.")
    ok = False
else:
    # Un TROP-CHER n'est legitime que s'il a reellement consomme son budget.
    # Une alarme qui tombe avant le seuil est un faux positif : elle
    # supprimerait un systeme sain, comme un faux positif du pre-filtre.
    premature = [r for r in cher_b if r["ms"] < SEUIL_B * 900]
    if premature:
        print("  ECHEC : %d TROP-CHER premature(s), le plus court a %d ms"
              " pour un seuil de %d s." % (len(premature),
                                           min(r["ms"] for r in premature),
                                           SEUIL_B))
        print("          un systeme sain serait supprime sans laisser de trace.")
        ok = False
    else:
        print("  OK : %d systemes sains, aucun etiquete TROP-CHER a tort"
              % len(sains))
print()

if not ok:
    print("ECHEC : l'interruption par alarme n'est pas fiable.")
    sys.exit(1)
print("OK : aucun faux negatif, aucun faux positif.")
