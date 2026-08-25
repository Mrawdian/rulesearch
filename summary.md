# rulesearch — resume automatique

genere 2026-08-25 18:03 UTC — 124 systemes evalues

## versions du DSL presentes
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 7 | 5.6% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 3, dont T2 : 100%
- candidats SANS connectivite : 4, dont T2 : 100%
- **echantillon trop faible pour conclure**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.40 — MONO@blocks + PAIRSTEP(1)@adj
- `T2` indices=0.47 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,4-6)@grid + PAIRSTEP(1)@adj
- `T2` indices=0.50 — ALLDIFF@cages(3-5) + SUM@cages(3-5) + NOTRIPLE@diags
- `T2` indices=0.50 — COUNT(v2,1-1)@cols + MONO@blocks
- `T2` indices=0.50 — CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,8-10)@grid + SUM(5+-1)@blocks
- `T2` indices=0.53 — SUM@cages(3-5) + NEQADJ@blocks
- `T2` indices=0.54 — MONO@cols + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,2-6)@grid + NOTRIPLE@blocks

## cout
- temps total 0.0 h, dont 69% brule sur des systemes MORT
