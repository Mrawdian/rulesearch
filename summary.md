# rulesearch — resume automatique

genere 2026-08-25 20:03 UTC — 1846 systemes evalues

## versions du DSL presentes
- `615abe43d6bc` : 869 systemes
- `0327bdc4c76a` : 853 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 878 | 445 | 64 | 34 | 101 | 57 | 84 | 82 | 9.3% |
| ref | 4 | 3 | 844 | 197 | 373 | 0 | 114 | 30 | 1 | 129 | 15.3% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 85, dont T2 : 100%
- candidats SANS connectivite : 133, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **84 systemes avec CONNECTED sur 771 (10.9%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
- Ces systemes sont les plus couteux a evaluer, donc vraisemblablement les plus profonds -- ceux que l'hypothese predit justement comme atteignant T2.
- **L'echantillon est donc tronque du cote meme que l'hypothese predit, et la troncature joue CONTRE elle.** Tout ecart T2 favorable observe est une **borne inferieure**, pas une estimation.
- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. Il peut n'etre qu'un effet de la borne de temps.

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.14 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.16 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.17 — PAIRSTEP(2)@adj + CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.17 — PAIRSTEP(2)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.19 — PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,1-3)@grid
- `T2` indices=0.21 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-3)@grid + PAIRDIFF(>=1)@knight + CONNECTED(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.21 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.22 — MONO@rows + COUNT(v1,1-1)@blocks
- `T2` indices=0.22 — CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.22 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-3)@grid
- `T2` indices=0.22 — NEQADJ@cols + MONO@rows
- `T2` indices=0.23 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,3-4)@grid + CONNECTED(v0) + COUNT(v0,2-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.23 — CONNECTED(v2) + COUNT(v2,2-4)@grid + PAIRSTEP(2)@adj
- `T2` indices=0.24 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.24 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid
- `T2` indices=0.25 — MONO@blocks + MONO@rows + COUNT(v2,0-0)@diags
- `T2` indices=0.25 — NEQADJ@rows + MONO@cols
- `T2` indices=0.25 — PAIRSTEP(1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,5-6)@grid
- `T2` indices=0.25 — SUM(2+-0)@diags + SUM(0+-1)@blocks
- `T2` indices=0.25 — CONNECTED(v1) + COUNT(v1,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.25 — NEQADJ@cols + COUNT(v0,0-1)@cols + NEQADJ@blocks
- `T2` indices=0.25 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-4)@grid + PAIRDIFF(>=1)@knight

## cout
- temps total 0.5 h, dont 3% brule sur des systemes MORT
- TROP-CHER : 85 systemes abandonnes (4.6% des systemes), 95% du temps total
  dont 84 avec CONNECTED, 1 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 11.8% sur 714 systemes
  - sans CONNECTED : 0.0% sur 164 systemes
