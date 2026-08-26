# rulesearch — resume automatique

genere 2026-08-26 16:01 UTC — 52673 systemes evalues

## versions du DSL presentes
- `89c65c03c4ad` : 29619 systemes
- `06fe04a859f1` : 7490 systemes
- `615abe43d6bc` : 7172 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `e3baecf8377b` : 5149 systemes
- `e40600351a72` : 1441 systemes
- `0327bdc4c76a` : 853 systemes
- `12564867381b` : 531 systemes
- `12a0c0c5e34b` : 294 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `6680f7b47e6f` : 124 systemes

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

### regroupement possible par moteur ACTIF (lecture, pas equivalence)

- moteur actif `0caa9267db60` (8931 systemes) : `06fe04a859f1`, `e40600351a72`
  modules actifs : rulesearch.py, dsl2.py, deduction.py, prefilter.py, t0_legacy.py

Ces dsl_hash different par des fichiers de `engine/` **qui n'etaient pas sur le chemin d'execution**. Les regrouper est defendable et doit etre **dit explicitement** a chaque fois qu'on le fait. **`dsl_hash` reste l'invariant dur** : en cas de doute, ne pas regrouper.

*45054 enregistrements sont anterieurs au champ `engine_active_hash` et ne peuvent etre regroupes avec aucun autre.*

**7466 enregistrements (14%) proviennent d'un moteur dont la source n'existe plus** — ni dans git, ni sur le disque. Donnee valide mais non rejouable : ne pas la citer comme reproductible.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 23534 | 11729 | 1593 | 804 | 2346 | 1867 | 2513 | 2386 | 10.1% |
| d4 | 4 | 4 | 5991 | 2749 | 1523 | 30 | 421 | 404 | 284 | 430 | 7.2% |
| ref | 4 | 3 | 23024 | 5333 | 9726 | 14 | 3217 | 1174 | 10 | 3550 | 15.4% |

## hypothese : la fracture est locale / non-locale

**`max_level` est SATURE** (100 % des candidats a T2) : cette section est
conservee pour memoire, la mesure qui fait foi est la **resistance a T0**
ci-dessous.

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 2513, dont T2 : 100%
- candidats SANS connectivite : 3860, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **2787 systemes avec CONNECTED sur 21710 (12.8%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
- Ces systemes sont les plus couteux a evaluer, donc vraisemblablement les plus profonds -- ceux que l'hypothese predit justement comme atteignant T2.
- **L'echantillon est donc tronque du cote meme que l'hypothese predit, et la troncature joue CONTRE elle.** Tout ecart T2 favorable observe est une **borne inferieure**, pas une estimation.
- Corollaire : un ecart faible ou nul ne refute PAS l'hypothese. Il peut n'etre qu'un effet de la borne de temps.

## resistance a T0 — METRIQUE PRINCIPALE

`resistance = t0_left / t0_unknown` : la fraction du travail de deduction
que la technique la **plus faible** ne fait pas. Elle ne sature pas, et ne
depend d'aucune technique dont la disponibilite varie selon les familles
— contrairement a `max_level`, que T1 rend incomparable entre `connect`
(aucun ALLDIFF, donc jamais de T1) et `static`.

Normalisee sur les cases **inconnues**, pas sur la grille : normaliser sur
la grille la rendait confondue par la densite d'indices.

*2083 candidats sur 6373 portent les champs bruts (33%).*

- `89c65c03c4ad` — 264 candidats
  - AVEC connectivite (106) : resistance **46.7%**
  - SANS connectivite (158) : resistance **21.4%**
  - test de permutation : **p = 0.0005** — significatif.
- `06fe04a859f1` — 968 candidats
  - AVEC connectivite (375) : resistance **41.4%**
  - SANS connectivite (593) : resistance **20.9%**
  - test de permutation : **p = 0.0005** — significatif.
- `e3baecf8377b` — 657 candidats
  - AVEC connectivite (268) : resistance **42.1%**
  - SANS connectivite (389) : resistance **21.0%**
  - test de permutation : **p = 0.0005** — significatif.
- `e40600351a72` — 194 candidats
  - AVEC connectivite (87) : resistance **40.0%**
  - SANS connectivite (107) : resistance **20.5%**
  - test de permutation : **p = 0.0005** — significatif.

## profondeur en continu (secondaire — le seuil binaire sature, pas ceci)

**Cette mesure evalue l'EFFORT de deduction, pas la PROFONDEUR.** Un
systeme qui demande trois fois T2 est plus laborieux, pas plus profond
qu'un systeme qui en demande deux. Confondre les deux serait la
cinquieme metrique du projet a mesurer autre chose que ce qu'elle
annonce.

`max_level >= 2` vaut 100 % partout : le seuil ne discrimine plus. Le
nombre d'invocations par niveau, lui, varie -- c'est une mesure continue
qui ne sature pas.

- `89c65c03c4ad` — 3389 candidats
  - AVEC connectivite (1304) : T0=13.03 T1=0.00 T2=2.97 — pondere **5.94**
  - SANS connectivite (2085) : T0=15.85 T1=0.02 T2=2.65 — pondere **5.32**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `06fe04a859f1` — 968 candidats
  - AVEC connectivite (375) : T0=13.22 T1=0.00 T2=3.04 — pondere **6.08**
  - SANS connectivite (593) : T0=16.04 T1=0.00 T2=2.64 — pondere **5.27**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `615abe43d6bc` — 945 candidats
  - AVEC connectivite (397) : T0=12.99 T1=0.00 T2=2.95 — pondere **5.90**
  - SANS connectivite (548) : T0=15.85 T1=0.00 T2=2.67 — pondere **5.34**
  - test de permutation : p = 0.0060 — **A NE PAS RETENIR** : serie NON REPRODUCTIBLE. Un ecart significatif issu d'un moteur dont la source n'existe plus n'est pas un resultat, il n'est pas rejouable.
- `e3baecf8377b` — 657 candidats
  - AVEC connectivite (268) : T0=13.02 T1=0.00 T2=3.09 — pondere **6.18**
  - SANS connectivite (389) : T0=16.01 T1=0.00 T2=2.62 — pondere **5.23**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `e40600351a72` — 194 candidats
  - AVEC connectivite (87) : T0=12.83 T1=0.00 T2=2.89 — pondere **5.77**
  - SANS connectivite (107) : T0=16.52 T1=0.00 T2=2.63 — pondere **5.25**
  - test de permutation : **p = 0.2394** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
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

**3 serie(s) reproductible(s) sur 6 etablissent l'ecart** : `89c65c03c4ad` (p=0.0005), `06fe04a859f1` (p=0.0005), `e3baecf8377b` (p=0.0005).

*Test de permutation bilateral, 2000 melanges, stdlib seule. Un ecart non*
*significatif ne dit pas qu'il n'y a pas d'effet : il dit que ces donnees*
*ne permettent pas de le distinguer du hasard.*


## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-2)@grid
- `T2` indices=0.06 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-3)@grid
- `T2` indices=0.06 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRSTEP(1)@adj + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-4)@grid
- `T2` indices=0.12 — SUM(1+-1)@cols + MONO@rows
- `T2` indices=0.12 — SUM(7+-1)@cols + MONO@blocks + MONO@rows
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid
- `T2` indices=0.12 — PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,4-5)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v0) + COUNT(v0,1-2)@grid
- `T2` indices=0.12 — MONO@rows + SUM(4+-1)@cols + COUNT(v2,0-0)@blocks
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-2)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,1-3)@grid
- `T2` indices=0.12 — CONNECTED(v2) + COUNT(v2,1-5)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — CONNECTED(v1) + NOSQUARE(v1) + COUNT(v1,1-4)@grid + PAIRDIFF(>=1)@adj + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v1) + COUNT(v1,1-5)@grid
- `T2` indices=0.12 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,2-5)@grid
- `T2` indices=0.12 — CONNECTED(v1) + COUNT(v1,1-4)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — CONNECTED(v3) + NOSQUARE(v3) + COUNT(v3,1-2)@grid + PAIRDIFF(>=1)@adj + PAIRDIFF(>=2)@knight
- `T2` indices=0.12 — CONNECTED(v1) + COUNT(v1,1-4)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=1)@adj
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.12 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@knight + PAIRDIFF(>=2)@adj
- `T2` indices=0.12 — PAIRDIFF(>=1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + PAIRDIFF(>=1)@knight

## cout
- temps total 16.3 h, dont 2% brule sur des systemes MORT
- TROP-CHER : 2807 systemes abandonnes (5.3% des systemes), 96% du temps total
  dont 2787 avec CONNECTED, 20 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 13.1% sur 19209 systemes
  - sans CONNECTED : 0.0% sur 4325 systemes
