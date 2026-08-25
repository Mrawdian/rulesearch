# rulesearch — resume automatique

genere 2026-08-25 19:09 UTC — 135 systemes evalues

## versions du DSL presentes
- `6680f7b47e6f` : 124 systemes
- `0327bdc4c76a` : 11 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 11 | 6 | 2 | 0 | 0 | 2 | 0 | 1 | 9.1% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 4, dont T2 : 100%
- candidats SANS connectivite : 4, dont T2 : 100%
- **echantillon trop faible pour conclure**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.40 — MONO@blocks + PAIRSTEP(1)@adj
- `T2` indices=0.42 — PAIRSTEP(2)@knight + PAIRSTEP(2)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,6-7)@grid
- `T2` indices=0.47 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,4-6)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.50 — ALLDIFF@cages(3-5) + SUM@cages(3-5) + NOTRIPLE@diags
- `T2` indices=0.50 — COUNT(v2,1-1)@cols + MONO@blocks
- `T2` indices=0.50 — CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,8-10)@grid + SUM(5+-1)@blocks
- `T2` indices=0.53 — SUM@cages(3-5) + NEQADJ@blocks
- `T2` indices=0.54 — MONO@cols + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + NOTRIPLE@blocks

## cout
- temps total 0.0 h, dont 68% brule sur des systemes MORT
- TROP-CHER : 0 systemes abandonnes (0.0% des systemes), 0% du temps total
