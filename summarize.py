#!/usr/bin/env python3
"""
Agrege tous les journaux en un summary.md unique.
C'est le SEUL fichier a lire en debut de session : il doit tenir en une
page et repondre a la seule question qui compte -- qu'est-ce qui a survecu,
et l'hypothese de fracture locale/non-locale tient-elle ?
"""
import collections, glob, hashlib, json, os, random, subprocess
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

# Seuils partages par toutes les comparaisons du resume.
MIN_GROUPE = 20      # sous ce nombre, on refuse de tester
N_PERM = 2000        # melanges du test de permutation
SEUIL_P = 0.05


def _test_permutation_valeurs(va, vb, n_iter=N_PERM, graine=20260826):
    """Test de permutation bilateral sur deux listes de valeurs numeriques."""
    if len(va) < MIN_GROUPE or len(vb) < MIN_GROUPE:
        return None
    obs = abs(sum(va) / len(va) - sum(vb) / len(vb))
    pool = list(va) + list(vb)
    na = len(va)
    rng = random.Random(graine)
    au_moins = 0
    for _ in range(n_iter):
        rng.shuffle(pool)
        if abs(sum(pool[:na]) / na - sum(pool[na:]) / (len(pool) - na)) >= obs:
            au_moins += 1
    return (au_moins + 1.0) / (n_iter + 1.0)


def hashs_reproductibles(limite=80):
    """
    dsl_hash de chaque version de engine/ presente dans l'historique git.

    Un hash absent de cet ensemble designe un moteur dont la SOURCE N'EXISTE
    PLUS -- typiquement un etat de travail transitoire capte par la production.
    La serie reste une donnee valide, mais elle n'est pas rejouable, et c'est
    ce qui doit etre dit. Le danger n'est pas la serie non reproductible :
    c'est la serie non reproductible qu'on croit reproductible.

    Rend None si git est indisponible -- on s'abstient alors de marquer.
    """
    def git(args, binaire=False):
        return subprocess.run(["git"] + args, cwd=HERE, timeout=30,
                              capture_output=True, text=not binaire)
    try:
        r = git(["log", "--format=%H", "--", "engine"])
        if r.returncode != 0:
            return None
        connus = set()
        for commit in r.stdout.split()[:limite]:
            t = git(["ls-tree", "--name-only", commit, "engine/"])
            fichiers = sorted(f for f in t.stdout.split() if f.endswith(".py"))
            if not fichiers:
                continue
            h = hashlib.sha256()
            for f in fichiers:
                b = git(["show", "%s:%s" % (commit, f)], binaire=True)
                if b.returncode != 0:
                    break
                h.update(b.stdout)
            else:
                connus.add(h.hexdigest()[:12])
        return connus
    except Exception:
        return None


recs = []
for f in glob.glob(os.path.join(HERE, "runs", "*", "results.jsonl")):
    tag = os.path.basename(os.path.dirname(f)).split("-")[-1]
    for line in open(f):
        try:
            r = json.loads(line)
        except Exception:
            continue
        r["tag"] = tag
        recs.append(r)

out = []
w = out.append
w("# rulesearch — resume automatique")
w("")
w("genere %s UTC — %d systemes evalues" %
  (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), len(recs)))
w("")

by_hash = collections.Counter(r.get("dsl_hash") for r in recs)
reproductibles = hashs_reproductibles()
w("## versions du DSL presentes")
orphelins = 0
for h, c in by_hash.most_common():
    if reproductibles is not None and h not in reproductibles:
        orphelins += c
        w("- `%s` : %d systemes — **NON REPRODUCTIBLE** (aucun commit ne porte "
          "ce moteur)" % (h, c))
    else:
        w("- `%s` : %d systemes" % (h, c))
w("")
w("Les lignes de dsl_hash differents ne sont pas comparables entre elles.")
if reproductibles is None:
    w("")
    w("*(git indisponible : reproductibilite non verifiee)*")
elif orphelins:
    w("")
    w("**%d enregistrements (%.0f%%) proviennent d'un moteur dont la source "
      "n'existe plus** — ni dans git, ni sur le disque. Donnee valide mais non "
      "rejouable : ne pas la citer comme reproductible." %
      (orphelins, 100.0 * orphelins / max(1, len(recs))))
w("")

w("## verdicts par configuration")
w("")
w("| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|")
groups = collections.defaultdict(list)
for r in recs:
    groups[(r["tag"], r.get("n"), r.get("d"))].append(r)
for (tag, n, d), rs in sorted(groups.items()):
    c = collections.Counter(x["verdict"] for x in rs)
    tot = len(rs)
    w("| %s | %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %.1f%% |" % (
        tag, n, d, tot, c["MORT"], c["LIBRE"], c["DEVINETTE"], c["PLAT"],
        c["SUR-CONTRAINT"], c["TROP-CHER"], c["CANDIDAT"],
        100 * c["CANDIDAT"] / max(1, tot)))
w("")

# hypothese de fracture : la connectivite produit-elle plus de T2 ?
w("## hypothese : la fracture est locale / non-locale")
w("")
w("**`max_level` est SATURE** (100 % des candidats a T2) : cette section est")
w("conservee pour memoire, la mesure qui fait foi est la **resistance a T0**")
w("ci-dessous.")
w("")
w("Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme")
w("contient CONNECTED atteignent T2 nettement plus souvent que les autres.")
w("")
cands = [r for r in recs if r["verdict"] == "CANDIDAT"]
with_conn = [r for r in cands if "CONNECTED" in r.get("sys", "")]
without = [r for r in cands if "CONNECTED" not in r.get("sys", "")]


def t2frac(rs):
    if not rs:
        return None
    return sum(1 for r in rs if r.get("max_level", -1) >= 2) / len(rs)


a, b = t2frac(with_conn), t2frac(without)
w("- candidats AVEC connectivite : %d, dont T2 : %s" %
  (len(with_conn), "%.0f%%" % (100 * a) if a is not None else "n/a"))
w("- candidats SANS connectivite : %d, dont T2 : %s" %
  (len(without), "%.0f%%" % (100 * b) if b is not None else "n/a"))
if a is not None and b is not None:
    # Un indicateur saturé ne mesure pas l'absence d'effet : il mesure sa
    # propre cecite. Imprimer une refutation dans ce cas serait affirmer
    # ce qu'on n'a pas etabli -- pire qu'un resume muet.
    if (a == 1.0 and b == 1.0) or (a == 0.0 and b == 0.0):
        w("- **INDICATEUR SATURE — la mesure ne discrimine plus, verdict "
          "impossible**")
        w("  Les deux groupes sont a %.0f%%. `max_level >= 2` ne separe "
          "plus rien : ce n'est pas une absence d'effet, c'est un "
          "instrument aveugle. Aucune conclusion, ni pour ni contre "
          "l'hypothese, ne peut etre tiree de cette ligne." % (100 * a))
    elif len(with_conn) < 20 or len(without) < 20:
        w("- **echantillon trop faible pour conclure**")
    elif a > b + 0.20:
        w("- **l'hypothese tient sur ces donnees**")
    elif a < b + 0.05:
        w("- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**")
    else:
        w("- ecart non concluant")
w("")

# Censure de l'echantillon par la borne de temps. Point essentiel pour
# lire l'ecart T2 ci-dessus : il ne s'annule pas, il se biaise.
conn_tous = [r for r in recs if "CONNECTED" in r.get("sys", "")]
conn_censures = [r for r in conn_tous if r["verdict"] == "TROP-CHER"]
if conn_censures:
    w("### censure de l'echantillon")
    w("")
    w("- **%d systemes avec CONNECTED sur %d (%.1f%%) sont abandonnes en "
      "TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus." %
      (len(conn_censures), len(conn_tous),
       100 * len(conn_censures) / max(1, len(conn_tous))))
    w("- Ces systemes sont les plus couteux a evaluer, donc "
      "vraisemblablement les plus profonds -- ceux que l'hypothese "
      "predit justement comme atteignant T2.")
    w("- **L'echantillon est donc tronque du cote meme que l'hypothese "
      "predit, et la troncature joue CONTRE elle.** Tout ecart T2 "
      "favorable observe est une **borne inferieure**, pas une "
      "estimation.")
    w("- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. "
      "Il peut n'etre qu'un effet de la borne de temps.")
    w("")

def _resistance(r):
    """cases restantes apres T0 seul / cases inconnues initiales, ou None"""
    inc = r.get("t0_unknown")
    left = r.get("t0_left")
    if not inc:
        return None
    return float(left) / inc


w("## resistance a T0 — METRIQUE PRINCIPALE")
w("")
w("`resistance = t0_left / t0_unknown` : la fraction du travail de deduction")
w("que la technique la **plus faible** ne fait pas. Elle ne sature pas, et ne")
w("depend d'aucune technique dont la disponibilite varie selon les familles")
w("— contrairement a `max_level`, que T1 rend incomparable entre `connect`")
w("(aucun ALLDIFF, donc jamais de T1) et `static`.")
w("")
w("Normalisee sur les cases **inconnues**, pas sur la grille : normaliser sur")
w("la grille la rendait confondue par la densite d'indices.")
w("")

_avec_res = [r for r in cands if _resistance(r) is not None]
if not _avec_res:
    w("*Aucun enregistrement ne porte encore `t0_unknown` / `t0_left`. Les")
    w("champs ont ete ajoutes le 26/08/2026 : seuls les blocs posterieurs les")
    w("portent. Metrique indisponible sur cette serie.*")
else:
    w("*%d candidats sur %d portent les champs bruts (%.0f%%).*"
      % (len(_avec_res), len(cands), 100.0 * len(_avec_res) / max(1, len(cands))))
    w("")
    for _h, _n in by_hash.most_common():
        _sous = [r for r in _avec_res if r.get("dsl_hash") == _h]
        if len(_sous) < MIN_GROUPE:
            continue
        _a = [r for r in _sous if "CONNECTED" in r.get("sys", "")]
        _b = [r for r in _sous if "CONNECTED" not in r.get("sys", "")]
        _va = [_resistance(r) for r in _a]
        _vb = [_resistance(r) for r in _b]
        _rep = (reproductibles is None) or (_h in reproductibles)
        w("- `%s` — %d candidats%s"
          % (_h, len(_sous), "" if _rep else " (**NON REPRODUCTIBLE**)"))
        if _va:
            w("  - AVEC connectivite (%d) : resistance **%.1f%%**"
              % (len(_va), 100.0 * sum(_va) / len(_va)))
        if _vb:
            w("  - SANS connectivite (%d) : resistance **%.1f%%**"
              % (len(_vb), 100.0 * sum(_vb) / len(_vb)))
        _p = _test_permutation_valeurs(_va, _vb)
        if _p is None:
            w("  - *groupes trop petits (< %d) — aucun test*" % MIN_GROUPE)
        elif _p < SEUIL_P and not _rep:
            w("  - p = %.4f — **A NE PAS RETENIR** : serie non reproductible." % _p)
        elif _p < SEUIL_P:
            w("  - test de permutation : **p = %.4f** — significatif." % _p)
        else:
            w("  - test de permutation : **p = %.4f** — **NON SIGNIFICATIF**." % _p)
w("")

w("## profondeur en continu (secondaire — le seuil binaire sature, pas ceci)")
w("")
w("**Cette mesure evalue l'EFFORT de deduction, pas la PROFONDEUR.** Un")
w("systeme qui demande trois fois T2 est plus laborieux, pas plus profond")
w("qu'un systeme qui en demande deux. Confondre les deux serait la")
w("cinquieme metrique du projet a mesurer autre chose que ce qu'elle")
w("annonce.")
w("")
w("`max_level >= 2` vaut 100 % partout : le seuil ne discrimine plus. Le")
w("nombre d'invocations par niveau, lui, varie -- c'est une mesure continue")
w("qui ne sature pas.")
w("")


def _uses(r, k):
    return (r.get("level_uses") or {}).get(str(k), 0)


def _moy(g, k):
    return (sum(_uses(r, k) for r in g) / len(g)) if g else 0.0


def _pondere(g):
    """invocations ponderees par le niveau : un T2 pese plus qu'un T0"""
    if not g:
        return 0.0
    return sum(sum(int(k) * v for k, v in (r.get("level_uses") or {}).items())
               for r in g) / len(g)


def _score(r):
    """invocations ponderees par le niveau, pour un enregistrement"""
    return sum(int(k) * v for k, v in (r.get("level_uses") or {}).items())


def _test_permutation(a, b, n_iter=N_PERM, graine=20260826):
    """
    Test de permutation bilateral, stdlib seule (pas de scipy : invariant
    "stdlib seule" de CLAUDE.md).

    H0 : les deux groupes sont tires de la meme distribution. On melange les
    etiquettes n_iter fois et on compte la fraction des melanges dont l'ecart
    de moyennes egale ou depasse l'ecart observe.

    Rend None si un groupe est trop petit -- on s'abstient plutot que de
    produire un p ininterpretable.
    """
    if len(a) < MIN_GROUPE or len(b) < MIN_GROUPE:
        return None
    va = [_score(r) for r in a]
    vb = [_score(r) for r in b]
    obs = abs(sum(va) / len(va) - sum(vb) / len(vb))
    pool = va + vb
    na = len(va)
    rng = random.Random(graine)
    au_moins = 0
    for _ in range(n_iter):
        rng.shuffle(pool)
        m1 = sum(pool[:na]) / na
        m2 = sum(pool[na:]) / (len(pool) - na)
        if abs(m1 - m2) >= obs:
            au_moins += 1
    return (au_moins + 1.0) / (n_iter + 1.0)


_testees = []
for _h, _n in by_hash.most_common():
    _sous = [r for r in cands if r.get("dsl_hash") == _h]
    if len(_sous) < MIN_GROUPE:
        continue
    _a = [r for r in _sous if "CONNECTED" in r.get("sys", "")]
    _b = [r for r in _sous if "CONNECTED" not in r.get("sys", "")]
    w("- `%s` — %d candidats" % (_h, len(_sous)))
    w("  - AVEC connectivite (%d) : T0=%.2f T1=%.2f T2=%.2f — pondere **%.2f**"
      % (len(_a), _moy(_a, 0), _moy(_a, 1), _moy(_a, 2), _pondere(_a)))
    w("  - SANS connectivite (%d) : T0=%.2f T1=%.2f T2=%.2f — pondere **%.2f**"
      % (len(_b), _moy(_b, 0), _moy(_b, 1), _moy(_b, 2), _pondere(_b)))
    _rep = (reproductibles is None) or (_h in reproductibles)
    _p = _test_permutation(_a, _b)
    _testees.append((_h, _rep, _p))
    if _p is None:
        w("  - *groupes trop petits (< %d) — aucun test, aucune conclusion*"
          % MIN_GROUPE)
    elif _p < SEUIL_P and not _rep:
        w("  - test de permutation : p = %.4f — **A NE PAS RETENIR** : serie NON "
          "REPRODUCTIBLE. Un ecart significatif issu d'un moteur dont la source "
          "n'existe plus n'est pas un resultat, il n'est pas rejouable." % _p)
    elif _p < SEUIL_P:
        w("  - test de permutation : **p = %.4f** — ecart significatif au seuil "
          "%.2f, sur une serie reproductible." % (_p, SEUIL_P))
    else:
        w("  - test de permutation : **p = %.4f** — **NON SIGNIFICATIF**, "
          "l'ecart est compatible avec le bruit. Ne pas conclure." % (_p, ))
w("")

# Synthese : ce qui compte n'est pas qu'un p soit sorti quelque part, mais
# qu'il soit sorti sur une serie REJOUABLE.
_rep_testees = [(h, p_) for h, r, p_ in _testees if r and p_ is not None]
_rep_signif = [(h, p_) for h, p_ in _rep_testees if p_ < SEUIL_P]
w("### ce que les series reproductibles etablissent")
w("")
if not _rep_testees:
    w("**Aucune serie reproductible n'a d'echantillon suffisant pour etre "
      "testee.** L'ecart n'est ni etabli ni refute : il n'est pas mesure.")
elif _rep_signif:
    w("**%d serie(s) reproductible(s) sur %d etablissent l'ecart** : %s."
      % (len(_rep_signif), len(_rep_testees),
         ", ".join("`%s` (p=%.4f)" % (h, p_) for h, p_ in _rep_signif)))
else:
    w("**AUCUNE serie reproductible n'etablit l'ecart.** %d serie(s) "
      "reproductible(s) testee(s), %d significative(s)."
      % (len(_rep_testees), 0))
    w("")
    w("A traiter comme une **absence de resultat**, pas comme une refutation :")
    w("les echantillons reproductibles sont encore trop petits pour trancher.")
    w("Tout p significatif affiche plus haut provient d'une serie NON")
    w("REPRODUCTIBLE et **ne doit pas etre mis en avant** -- son moteur")
    w("n'existe plus, la mesure n'est pas rejouable.")
w("")
w("*Test de permutation bilateral, %d melanges, stdlib seule. Un ecart non*" % N_PERM)
w("*significatif ne dit pas qu'il n'y a pas d'effet : il dit que ces donnees*")
w("*ne permettent pas de le distinguer du hasard.*")
w("")
_t1 = sum(_uses(r, 1) for r in recs)
if not _t1:
    w("**T1 n'a JAMAIS ete invoquee** sur l'ensemble des enregistrements. La")
    w("hierarchie effective en production est T0/T2, pas T0/T1/T2. Le niveau")
    w("intermediaire est vide, ce qui explique en partie que le seuil sature.")
w("")

w("## meilleurs candidats (niveau requis, puis indices les plus rares)")
w("")
cands.sort(key=lambda r: (-r.get("max_level", -1), r.get("clue_frac", 1)))
seen = set()
shown = 0
for r in cands:
    if r["sys"] in seen:
        continue
    seen.add(r["sys"])
    w("- `T%d` indices=%.2f — %s" % (r.get("max_level", -1), r.get("clue_frac", 0), r["sys"]))
    shown += 1
    if shown >= 25:
        break
w("")

w("## cout")
mort = [r for r in recs if r["verdict"] == "MORT"]
if recs:
    tot_ms = sum(r.get("ms", 0) for r in recs)
    mort_ms = sum(r.get("ms", 0) for r in mort)
    w("- temps total %.1f h, dont %.0f%% brule sur des systemes MORT" %
      (tot_ms / 3.6e6, 100 * mort_ms / max(1, tot_ms)))
    cher = [r for r in recs if r["verdict"] == "TROP-CHER"]
    cher_ms = sum(r.get("ms", 0) for r in cher)
    w("- TROP-CHER : %d systemes abandonnes (%.1f%% des systemes), "
      "%.0f%% du temps total" %
      (len(cher), 100 * len(cher) / max(1, len(recs)),
       100 * cher_ms / max(1, tot_ms)))
    if cher:
        conn = sum(1 for r in cher if "CONNECTED" in r.get("sys", ""))
        w("  dont %d avec CONNECTED, %d sans -- **chiffre CONFONDU** : "
          "seul le tag connect peut produire des systemes avec CONNECTED, "
          "ce ratio melange l'effet de la connectivite et celui de la "
          "configuration. Voir la ventilation ci-dessous." %
          (conn, len(cher) - conn))

        # Ventilation a configuration egale : dans le seul tag connect,
        # ou les deux types de systemes coexistent. C'est la comparaison
        # qui n'est pas confondue.
        dans_connect = [r for r in recs if r.get("tag") == "connect"]
        avec = [r for r in dans_connect if "CONNECTED" in r.get("sys", "")]
        sans = [r for r in dans_connect if "CONNECTED" not in r.get("sys", "")]

        def taux_cher(g):
            if not g:
                return None
            return 100.0 * sum(1 for r in g if r["verdict"] == "TROP-CHER") / len(g)

        ta, ts = taux_cher(avec), taux_cher(sans)
        w("- taux de TROP-CHER **dans le seul tag connect** "
          "(a configuration egale, non confondu) :")
        w("  - avec CONNECTED : %s sur %d systemes" %
          ("%.1f%%" % ta if ta is not None else "n/a", len(avec)))
        w("  - sans CONNECTED : %s sur %d systemes" %
          ("%.1f%%" % ts if ts is not None else "n/a", len(sans)))
        if ta is not None and ts is not None and (len(avec) < 20 or len(sans) < 20):
            w("  - *echantillon trop faible pour conclure sur cet ecart*")

with open(os.path.join(HERE, "summary.md"), "w") as f:
    f.write("\n".join(out) + "\n")
print("summary.md ecrit : %d enregistrements" % len(recs))
