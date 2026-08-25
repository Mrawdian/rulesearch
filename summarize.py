#!/usr/bin/env python3
"""
Agrege tous les journaux en un summary.md unique.
C'est le SEUL fichier a lire en debut de session : il doit tenir en une
page et repondre a la seule question qui compte -- qu'est-ce qui a survecu,
et l'hypothese de fracture locale/non-locale tient-elle ?
"""
import collections, glob, json, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

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
w("## versions du DSL presentes")
for h, c in by_hash.most_common():
    w("- `%s` : %d systemes" % (h, c))
w("")
w("Les lignes de dsl_hash differents ne sont pas comparables entre elles.")
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
