# rulesearch — resume automatique

genere 2026-08-25 19:29 UTC — 194 systemes evalues

## versions du DSL presentes
- `6680f7b47e6f` : 124 systemes
- `0327bdc4c76a` : 70 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 41 | 15 | 8 | 1 | 4 | 3 | 2 | 8 | 19.5% |
| ref | 4 | 3 | 29 | 10 | 5 | 0 | 5 | 0 | 0 | 9 | 31.0% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 11, dont T2 : 100%
- candidats SANS connectivite : 13, dont T2 : 100%
- **echantillon trop faible pour conclure**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.18 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.27 — MONO@cols + NEQADJ@rows
- `T2` indices=0.31 — NEQADJ@cols + SUM(5+-0)@rows
- `T2` indices=0.34 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.39 — SUM(2+-0)@diags + MONO@cols
- `T2` indices=0.39 — COUNT(v2,1-2)@cols + MONO@rows
- `T2` indices=0.40 — MONO@blocks + PAIRSTEP(1)@adj
- `T2` indices=0.41 — CONNECTED(v1) + COUNT(v1,8-9)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.41 — CONNECTED(v0) + COUNT(v0,8-9)@grid + PAIRSTEP(2)@knight
- `T2` indices=0.42 — PAIRSTEP(2)@knight + PAIRSTEP(2)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,6-7)@grid
- `T2` indices=0.44 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + CONNECTED(v1) + COUNT(v1,4-5)@grid + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,3-6)@grid
- `T2` indices=0.46 — MONO@blocks + SUM(2+-1)@diags
- `T2` indices=0.47 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,4-6)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.49 — CONNECTED(v1) + COUNT(v1,7-8)@grid + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,7-11)@grid + CONNECTED(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.50 — ALLDIFF@cages(3-5) + SUM@cages(3-5) + NOTRIPLE@diags
- `T2` indices=0.50 — COUNT(v2,1-1)@cols + MONO@blocks
- `T2` indices=0.50 — CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,8-10)@grid + SUM(5+-1)@blocks
- `T2` indices=0.51 — COUNT(v2,2-2)@blocks + SUM(5+-1)@rows
- `T2` indices=0.51 — SUM(6+-1)@rows + MONO@diags
- `T2` indices=0.52 — MONO@blocks
- `T2` indices=0.53 — SUM@cages(3-5) + NEQADJ@blocks
- `T2` indices=0.54 — MONO@diags + NEQADJ@rows
- `T2` indices=0.54 — CONNECTED(v1) + COUNT(v1,3-6)@grid + CONNECTED(v0) + COUNT(v0,6-9)@grid
- `T2` indices=0.54 — MONO@cols + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + NOTRIPLE@blocks

## cout
- temps total 0.0 h, dont 17% brule sur des systemes MORT
- TROP-CHER : 2 systemes abandonnes (1.0% des systemes), 73% du temps total
  dont 2 avec CONNECTED, 0 sans (un systeme trop cher a evaluer est un fait sur le systeme, pas seulement un incident)
