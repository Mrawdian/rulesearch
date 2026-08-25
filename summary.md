# rulesearch — resume automatique

genere 2026-08-25 22:20 UTC — 8089 systemes evalues

## versions du DSL presentes
- `615abe43d6bc` : 7112 systemes
- `0327bdc4c76a` : 853 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 4033 | 2036 | 255 | 141 | 387 | 320 | 414 | 432 | 10.7% |
| ref | 4 | 3 | 3932 | 948 | 1662 | 1 | 523 | 187 | 2 | 609 | 15.5% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 435, dont T2 : 100%
- candidats SANS connectivite : 613, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **414 systemes avec CONNECTED sur 3367 (12.3%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
- Ces systemes sont les plus couteux a evaluer, donc vraisemblablement les plus profonds -- ceux que l'hypothese predit justement comme atteignant T2.
- **L'echantillon est donc tronque du cote meme que l'hypothese predit, et la troncature joue CONTRE elle.** Tout ecart T2 favorable observe est une **borne inferieure**, pas une estimation.
- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. Il peut n'etre qu'un effet de la borne de temps.

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRSTEP(1)@adj + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid
- `T2` indices=0.12 — PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,4-5)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.12 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-3)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v0) + COUNT(v0,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-5)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.14 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.14 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.15 — PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.16 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.16 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,4-6)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj
- `T2` indices=0.17 — PAIRSTEP(2)@adj + CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.17 — PAIRSTEP(2)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.17 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRSTEP(2)@adj + PAIRSTEP(2)@adj
- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.18 — CONNECTED(v2) + COUNT(v2,2-5)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj
- `T2` indices=0.18 — MONO@blocks + MONO@cols + COUNT(v2,2-2)@diags
- `T2` indices=0.18 — MONO@cols + NOTRIPLE@rows + SUM(2+-1)@rows
- `T2` indices=0.19 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight

## cout
- temps total 2.4 h, dont 2% brule sur des systemes MORT
- TROP-CHER : 416 systemes abandonnes (5.1% des systemes), 96% du temps total
  dont 414 avec CONNECTED, 2 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 12.5% sur 3310 systemes
  - sans CONNECTED : 0.0% sur 723 systemes
