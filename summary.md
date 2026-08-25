# rulesearch — resume automatique

genere 2026-08-25 17:43 UTC — 39 systemes evalues

## versions du DSL presentes
- `6680f7b47e6f` : 39 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 39 | 21 | 10 | 0 | 2 | 3 | 2 | 5.1% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 1, dont T2 : 100%
- candidats SANS connectivite : 1, dont T2 : 100%
- **echantillon trop faible pour conclure**

## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.50 — COUNT(v2,1-1)@cols + MONO@blocks
- `T2` indices=0.50 — CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,8-10)@grid + SUM(5+-1)@blocks

## cout
- temps total 0.0 h, dont 52% brule sur des systemes MORT
