# rulesearch — resume automatique

genere 2026-08-25 19:39 UTC — 592 systemes evalues

## versions du DSL presentes
- `0327bdc4c76a` : 468 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 251 | 119 | 29 | 7 | 28 | 13 | 29 | 23 | 9.2% |
| ref | 4 | 3 | 217 | 45 | 98 | 0 | 27 | 8 | 0 | 39 | 18.0% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 26, dont T2 : 100%
- candidats SANS connectivite : 43, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@adj
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
- `T2` indices=0.31 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.31 — NEQADJ@cols + SUM(5+-0)@rows
- `T2` indices=0.31 — NEQADJ@blocks + MONO@cols
- `T2` indices=0.32 — NEQADJ@blocks + NEQADJ@cols
- `T2` indices=0.33 — SUM(3+-1)@cols + MONO@blocks
- `T2` indices=0.33 — SUM(2+-1)@blocks + NEQADJ@diags + SUM(2+-0)@blocks
- `T2` indices=0.34 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,4-6)@grid
- `T2` indices=0.34 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + COUNT(v2,4-6)@grid
- `T2` indices=0.34 — SUM(2+-1)@cols + MONO@blocks
- `T2` indices=0.34 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.38 — SUM(2+-1)@blocks + SUM(2+-1)@cols + NEQADJ@cols
- `T2` indices=0.38 — MONO@blocks + MONO@rows
- `T2` indices=0.39 — SUM(2+-0)@diags + MONO@cols

## cout
- temps total 0.2 h, dont 3% brule sur des systemes MORT
- TROP-CHER : 29 systemes abandonnes (4.9% des systemes), 95% du temps total
  dont 29 avec CONNECTED, 0 sans (un systeme trop cher a evaluer est un fait sur le systeme, pas seulement un incident)
