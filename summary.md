# rulesearch — resume automatique

genere 2026-08-25 19:32 UTC — 373 systemes evalues

## versions du DSL presentes
- `0327bdc4c76a` : 249 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 131 | 64 | 17 | 6 | 14 | 6 | 9 | 13 | 9.9% |
| ref | 4 | 3 | 118 | 23 | 54 | 0 | 17 | 4 | 0 | 20 | 16.9% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 16, dont T2 : 100%
- candidats SANS connectivite : 24, dont T2 : 100%
- **echantillon trop faible pour conclure**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.27 — MONO@cols + NEQADJ@rows
- `T2` indices=0.29 — CONNECTED(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.31 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.31 — NEQADJ@cols + SUM(5+-0)@rows
- `T2` indices=0.31 — NEQADJ@blocks + MONO@cols
- `T2` indices=0.32 — NEQADJ@blocks + NEQADJ@cols
- `T2` indices=0.33 — SUM(2+-1)@blocks + NEQADJ@diags + SUM(2+-0)@blocks
- `T2` indices=0.34 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.38 — SUM(2+-1)@blocks + SUM(2+-1)@cols + NEQADJ@cols
- `T2` indices=0.39 — SUM(2+-0)@diags + MONO@cols
- `T2` indices=0.39 — MONO@rows + MONO@diags
- `T2` indices=0.39 — COUNT(v2,1-2)@cols + MONO@rows
- `T2` indices=0.40 — MONO@blocks + PAIRSTEP(1)@adj
- `T2` indices=0.41 — CONNECTED(v1) + COUNT(v1,8-9)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.41 — CONNECTED(v0) + COUNT(v0,8-9)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.42 — MONO@blocks + MONO@diags
- `T2` indices=0.42 — PAIRSTEP(2)@knight + PAIRSTEP(2)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,6-7)@grid
- `T2` indices=0.44 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + CONNECTED(v1) + COUNT(v1,4-5)@grid + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.46 — MONO@blocks + SUM(2+-1)@diags
- `T2` indices=0.46 — MONO@blocks + NEQADJ@diags
- `T2` indices=0.47 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,4-6)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.47 — SUM(7+-1)@cols + COUNT(v1,2-2)@cols + NOTRIPLE@blocks
- `T2` indices=0.47 — NEQADJ@rows + SUM(2+-0)@diags

## cout
- temps total 0.1 h, dont 7% brule sur des systemes MORT
- TROP-CHER : 9 systemes abandonnes (2.4% des systemes), 88% du temps total
  dont 9 avec CONNECTED, 0 sans (un systeme trop cher a evaluer est un fait sur le systeme, pas seulement un incident)
