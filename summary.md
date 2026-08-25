# rulesearch — resume automatique

genere 2026-08-25 19:44 UTC — 874 systemes evalues

## versions du DSL presentes
- `0327bdc4c76a` : 750 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 385 | 196 | 34 | 13 | 42 | 23 | 40 | 33 | 8.6% |
| ref | 4 | 3 | 365 | 81 | 157 | 0 | 52 | 13 | 0 | 62 | 17.0% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 36, dont T2 : 100%
- candidats SANS connectivite : 66, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **40 systemes avec CONNECTED sur 371 (10.8%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
- Ces systemes sont les plus couteux a evaluer, donc vraisemblablement les plus profonds -- ceux que l'hypothese predit justement comme atteignant T2.
- **L'echantillon est donc tronque du cote meme que l'hypothese predit, et la troncature joue CONTRE elle.** Tout ecart T2 favorable observe est une **borne inferieure**, pas une estimation.
- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. Il peut n'etre qu'un effet de la borne de temps.

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.16 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,1-3)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.22 — CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.22 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-3)@grid
- `T2` indices=0.22 — NEQADJ@cols + MONO@rows
- `T2` indices=0.23 — CONNECTED(v2) + COUNT(v2,2-4)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.24 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.25 — MONO@blocks + MONO@rows + COUNT(v2,0-0)@diags
- `T2` indices=0.25 — NEQADJ@cols + COUNT(v0,0-1)@cols + NEQADJ@blocks
- `T2` indices=0.26 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@adj + PAIRDIFF(>=1)@knight
- `T2` indices=0.27 — MONO@cols + NEQADJ@rows
- `T2` indices=0.27 — COUNT(v2,1-1)@cols + NEQADJ@rows + COUNT(v1,2-3)@rows
- `T2` indices=0.28 — NEQADJ@blocks + SUM(6+-1)@cols
- `T2` indices=0.29 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,4-8)@grid
- `T2` indices=0.29 — NOTRIPLE@diags + MONO@rows + NEQADJ@cols
- `T2` indices=0.29 — CONNECTED(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.30 — NOTRIPLE@rows + SUM(6+-0)@cols
- `T2` indices=0.31 — MONO@blocks + MONO@diags
- `T2` indices=0.31 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.31 — NEQADJ@cols + SUM(5+-0)@rows
- `T2` indices=0.31 — PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid
- `T2` indices=0.31 — NEQADJ@blocks + MONO@cols
- `T2` indices=0.32 — NEQADJ@blocks + NEQADJ@cols

## cout
- temps total 0.2 h, dont 3% brule sur des systemes MORT
- TROP-CHER : 40 systemes abandonnes (4.6% des systemes), 95% du temps total
  dont 40 avec CONNECTED, 0 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 12.7% sur 314 systemes
  - sans CONNECTED : 0.0% sur 71 systemes
