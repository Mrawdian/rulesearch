# rulesearch — resume automatique

genere 2026-08-26 08:37 UTC — 33951 systemes evalues

## versions du DSL presentes
- `89c65c03c4ad` : 24977 systemes
- `615abe43d6bc` : 7172 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `0327bdc4c76a` : 853 systemes
- `12564867381b` : 531 systemes
- `12a0c0c5e34b` : 294 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

**7466 enregistrements (22%) proviennent d'un moteur dont la source n'existe plus** — ni dans git, ni sur le disque. Donnee valide mais non rejouable : ne pas la citer comme reproductible.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 15150 | 7561 | 990 | 521 | 1483 | 1215 | 1656 | 1531 | 10.1% |
| d4 | 4 | 4 | 3833 | 1754 | 984 | 21 | 279 | 251 | 190 | 262 | 6.8% |
| ref | 4 | 3 | 14844 | 3512 | 6229 | 9 | 2044 | 757 | 6 | 2287 | 15.4% |

## hypothese : la fracture est locale / non-locale

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 1603, dont T2 : 100%
- candidats SANS connectivite : 2484, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **1841 systemes avec CONNECTED sur 14012 (13.1%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
- Ces systemes sont les plus couteux a evaluer, donc vraisemblablement les plus profonds -- ceux que l'hypothese predit justement comme atteignant T2.
- **L'echantillon est donc tronque du cote meme que l'hypothese predit, et la troncature joue CONTRE elle.** Tout ecart T2 favorable observe est une **borne inferieure**, pas une estimation.
- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. Il peut n'etre qu'un effet de la borne de temps.

## profondeur en continu (le seuil binaire sature, pas ceci)

**Cette mesure evalue l'EFFORT de deduction, pas la PROFONDEUR.** Un
systeme qui demande trois fois T2 est plus laborieux, pas plus profond
qu'un systeme qui en demande deux. Confondre les deux serait la
cinquieme metrique du projet a mesurer autre chose que ce qu'elle
annonce.

`max_level >= 2` vaut 100 % partout : le seuil ne discrimine plus. Le
nombre d'invocations par niveau, lui, varie -- c'est une mesure continue
qui ne sature pas.

- `89c65c03c4ad` — 2922 candidats
  - AVEC connectivite (1124) : T0=13.16 T1=0.00 T2=2.91 — pondere **5.82**
  - SANS connectivite (1798) : T0=15.90 T1=0.01 T2=2.66 — pondere **5.33**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `615abe43d6bc` — 945 candidats
  - AVEC connectivite (397) : T0=12.99 T1=0.00 T2=2.95 — pondere **5.90**
  - SANS connectivite (548) : T0=15.85 T1=0.00 T2=2.67 — pondere **5.34**
  - test de permutation : p = 0.0060 — **A NE PAS RETENIR** : serie NON REPRODUCTIBLE. Un ecart significatif issu d'un moteur dont la source n'existe plus n'est pas un resultat, il n'est pas rejouable.
- `0327bdc4c76a` — 107 candidats
  - AVEC connectivite (38) : T0=12.34 T1=0.00 T2=2.92 — pondere **5.84**
  - SANS connectivite (69) : T0=15.97 T1=0.00 T2=2.45 — pondere **4.90**
  - test de permutation : **p = 0.1569** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `12564867381b` — 75 candidats
  - AVEC connectivite (28) : T0=12.82 T1=0.00 T2=2.79 — pondere **5.57**
  - SANS connectivite (47) : T0=15.09 T1=0.00 T2=2.68 — pondere **5.36**
  - test de permutation : **p = 0.8296** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `12a0c0c5e34b` — 31 candidats
  - AVEC connectivite (13) : T0=13.31 T1=0.00 T2=3.08 — pondere **6.15**
  - SANS connectivite (18) : T0=15.83 T1=0.00 T2=2.94 — pondere **5.89**
  - *groupes trop petits (< 20) — aucun test, aucune conclusion*

### ce que les series reproductibles etablissent

**1 serie(s) reproductible(s) sur 3 etablissent l'ecart** : `89c65c03c4ad` (p=0.0005).

*Test de permutation bilateral, 2000 melanges, stdlib seule. Un ecart non*
*significatif ne dit pas qu'il n'y a pas d'effet : il dit que ces donnees*
*ne permettent pas de le distinguer du hasard.*


## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRSTEP(1)@adj + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — SUM(7+-1)@cols + MONO@blocks + MONO@rows
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid
- `T2` indices=0.12 — PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,4-5)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v0) + COUNT(v0,1-2)@grid
- `T2` indices=0.12 — MONO@rows + SUM(4+-1)@cols + COUNT(v2,0-0)@blocks
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,1-3)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v1) + COUNT(v1,1-5)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-5)@grid
- `T2` indices=0.12 — CONNECTED(v2) + COUNT(v2,1-5)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-3)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v0) + COUNT(v0,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,1-2)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRSTEP(1)@knight + CONNECTED(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v1) + COUNT(v1,1-5)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-2)@grid
- `T2` indices=0.12 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-4)@grid + PAIRDIFF(>=1)@adj + PAIRDIFF(>=1)@knight

## cout
- temps total 10.8 h, dont 2% brule sur des systemes MORT
- TROP-CHER : 1852 systemes abandonnes (5.5% des systemes), 96% du temps total
  dont 1841 avec CONNECTED, 11 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 13.4% sur 12391 systemes
  - sans CONNECTED : 0.0% sur 2759 systemes
