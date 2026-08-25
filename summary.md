# rulesearch — resume automatique

genere 2026-08-25 19:36 UTC — 476 systemes evalues

## versions du DSL presentes
- `0327bdc4c76a` : 352 systemes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 191 | 92 | 22 | 6 | 21 | 10 | 19 | 19 | 9.9% |
| ref | 4 | 3 | 161 | 35 | 76 | 0 | 20 | 5 | 0 | 25 | 15.5% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 22, dont T2 : 100%
- candidats SANS connectivite : 29, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.21 — PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.24 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.25 — NEQADJ@cols + COUNT(v0,0-1)@cols + NEQADJ@blocks
- `T2` indices=0.27 — MONO@cols + NEQADJ@rows
- `T2` indices=0.27 — COUNT(v2,1-1)@cols + NEQADJ@rows + COUNT(v1,2-3)@rows
- `T2` indices=0.29 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + COUNT(v1,4-8)@grid
- `T2` indices=0.29 — NOTRIPLE@diags + MONO@rows + NEQADJ@cols
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
- `T2` indices=0.39 — MONO@rows + MONO@blocks
- `T2` indices=0.40 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-4)@grid + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.40 — MONO@blocks + PAIRSTEP(1)@adj
- `T2` indices=0.41 — CONNECTED(v1) + COUNT(v1,8-9)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.41 — CONNECTED(v0) + COUNT(v0,8-9)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.42 — MONO@blocks + MONO@diags

## cout
- temps total 0.1 h, dont 4% brule sur des systemes MORT
- TROP-CHER : 19 systemes abandonnes (4.0% des systemes), 93% du temps total
  dont 19 avec CONNECTED, 0 sans (un systeme trop cher a evaluer est un fait sur le systeme, pas seulement un incident)
