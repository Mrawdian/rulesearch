# rulesearch — resume automatique

genere 2026-08-25 21:52 UTC — 6842 systemes evalues

## versions du DSL presentes
- `615abe43d6bc` : 5865 systemes
- `0327bdc4c76a` : 853 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 3403 | 1717 | 220 | 118 | 332 | 263 | 346 | 364 | 10.7% |
| ref | 4 | 3 | 3315 | 787 | 1385 | 1 | 456 | 163 | 1 | 522 | 15.7% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 367, dont T2 : 100%
- candidats SANS connectivite : 526, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **346 systemes avec CONNECTED sur 2846 (12.2%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
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
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-5)@grid
- `T2` indices=0.14 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.16 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.16 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,4-6)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj
- `T2` indices=0.17 — PAIRSTEP(2)@adj + CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.17 — PAIRSTEP(2)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.18 — CONNECTED(v2) + COUNT(v2,2-5)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj
- `T2` indices=0.18 — MONO@blocks + MONO@cols + COUNT(v2,2-2)@diags
- `T2` indices=0.18 — MONO@cols + NOTRIPLE@rows + SUM(2+-1)@rows
- `T2` indices=0.20 — COUNT(v1,0-1)@cols + SUM(5+-0)@blocks + MONO@diags
- `T2` indices=0.20 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.20 — SUM(6+-0)@cols + MONO@blocks
- `T2` indices=0.20 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.21 — PAIRSTEP(2)@adj + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-4)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,1-3)@grid
- `T2` indices=0.21 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRDIFF(>=1)@knight + CONNECTED(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.21 — COUNT(v1,0-0)@cols + MONO@blocks + COUNT(v0,1-1)@diags

## cout
- temps total 2.0 h, dont 2% brule sur des systemes MORT
- TROP-CHER : 347 systemes abandonnes (5.1% des systemes), 96% du temps total
  dont 346 avec CONNECTED, 1 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 12.4% sur 2789 systemes
  - sans CONNECTED : 0.0% sur 614 systemes
