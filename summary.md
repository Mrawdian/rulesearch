# rulesearch — resume automatique

genere 2026-08-25 19:41 UTC — 680 systemes evalues

## versions du DSL presentes
- `0327bdc4c76a` : 556 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 296 | 142 | 32 | 11 | 32 | 15 | 32 | 29 | 9.8% |
| ref | 4 | 3 | 260 | 54 | 115 | 0 | 31 | 11 | 0 | 49 | 18.8% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 32, dont T2 : 100%
- candidats SANS connectivite : 53, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **32 systemes avec CONNECTED sur 301 (10.6%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
- Ces systemes sont les plus couteux a evaluer, donc vraisemblablement les plus profonds -- ceux que l'hypothese predit justement comme atteignant T2.
- **L'echantillon est donc tronque du cote meme que l'hypothese predit, et la troncature joue CONTRE elle.** Tout ecart T2 favorable observe est une **borne inferieure**, pas une estimation.
- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. Il peut n'etre qu'un effet de la borne de temps.

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,1-3)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.22 — CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.22 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-3)@grid
- `T2` indices=0.22 — NEQADJ@cols + MONO@rows
- `T2` indices=0.24 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.25 — NEQADJ@cols + COUNT(v0,0-1)@cols + NEQADJ@blocks
- `T2` indices=0.26 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@adj + PAIRDIFF(>=1)@knight
- `T2` indices=0.27 — MONO@cols + NEQADJ@rows
- `T2` indices=0.27 — COUNT(v2,1-1)@cols + NEQADJ@rows + COUNT(v1,2-3)@rows
- `T2` indices=0.28 — NEQADJ@blocks + SUM(6+-1)@cols
- `T2` indices=0.29 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,4-8)@grid
- `T2` indices=0.29 — NOTRIPLE@diags + MONO@rows + NEQADJ@cols
- `T2` indices=0.29 — CONNECTED(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.30 — NOTRIPLE@rows + SUM(6+-0)@cols
- `T2` indices=0.31 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.31 — NEQADJ@cols + SUM(5+-0)@rows
- `T2` indices=0.31 — NEQADJ@blocks + MONO@cols
- `T2` indices=0.32 — NEQADJ@blocks + NEQADJ@cols
- `T2` indices=0.33 — SUM(3+-1)@cols + MONO@blocks
- `T2` indices=0.33 — SUM(2+-1)@blocks + NEQADJ@diags + SUM(2+-0)@blocks
- `T2` indices=0.34 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,4-6)@grid
- `T2` indices=0.34 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + COUNT(v2,4-6)@grid
- `T2` indices=0.34 — SUM(2+-1)@cols + MONO@blocks

## cout
- temps total 0.2 h, dont 3% brule sur des systemes MORT
- TROP-CHER : 32 systemes abandonnes (4.7% des systemes), 95% du temps total
  dont 32 avec CONNECTED, 0 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 13.1% sur 244 systemes
  - sans CONNECTED : 0.0% sur 52 systemes
