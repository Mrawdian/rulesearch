# rulesearch — resume automatique

genere 2026-09-05 13:15 UTC — 390068 systemes evalues

## versions du DSL presentes
- `5c556c16ea8b` : 306724 systemes
- `89c65c03c4ad` : 29619 systemes
- `ab89a63b01ef` : 18378 systemes
- `06fe04a859f1` : 9167 systemes
- `615abe43d6bc` : 7172 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `62448a55927e` : 6239 systemes
- `e3baecf8377b` : 5149 systemes
- `23303c299f39` : 1743 systemes
- `e40600351a72` : 1441 systemes
- `0327bdc4c76a` : 853 systemes
- `e80bc1b2b437` : 677 systemes
- `0a74109317e5` : 537 systemes
- `12564867381b` : 531 systemes
- `8f22f0d2d442` : 507 systemes
- `b71bb0907fb5` : 381 systemes
- `12a0c0c5e34b` : 294 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `e8a1f930f7b9` : 207 systemes
- `84fba70921e0` : 206 systemes
- `6680f7b47e6f` : 124 systemes
- `cf6a4d3246d8` : 60 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)
- `9e54e42681ed` : 59 systemes — **NON REPRODUCTIBLE** (aucun commit ne porte ce moteur)

Les lignes de dsl_hash differents ne sont pas comparables entre elles.

### regroupement possible par moteur ACTIF (lecture, pas equivalence)

- moteur actif `0caa9267db60` (346326 systemes) : `06fe04a859f1`, `0a74109317e5`, `23303c299f39`, `5c556c16ea8b`, `62448a55927e`, `84fba70921e0`, `8f22f0d2d442`, `9e54e42681ed`, `ab89a63b01ef`, `b71bb0907fb5`, `cf6a4d3246d8`, `e40600351a72`, `e80bc1b2b437`, `e8a1f930f7b9`
  modules actifs : rulesearch.py, dsl2.py, deduction.py, prefilter.py, t0_legacy.py

Ces dsl_hash different par des fichiers de `engine/` **qui n'etaient pas sur le chemin d'execution**. Les regrouper est defendable et doit etre **dit explicitement** a chaque fois qu'on le fait. **`dsl_hash` reste l'invariant dur** : en cas de doute, ne pas regrouper.

*45054 enregistrements sont anterieurs au champ `engine_active_hash` et ne peuvent etre regroupes avec aucun autre.*

**7585 enregistrements (2%) proviennent d'un moteur dont la source n'existe plus** — ni dans git, ni sur le disque. Donnee valide mais non rejouable : ne pas la citer comme reproductible.

## verdicts par configuration

| tag | n | d | total | MORT | LIBRE | DEVIN. | PLAT | S-CONTR | TROP-CHER | CAND | %cand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 4 | 124 | 76 | 21 | 2 | 5 | 11 | 0 | 7 | 5.6% |
| connect | 4 | 3 | 193898 | 96291 | 13203 | 6460 | 19710 | 15264 | 20573 | 19925 | 10.3% |
| d4 | 4 | 4 | 5991 | 2749 | 1523 | 30 | 421 | 404 | 284 | 430 | 7.2% |
| ref | 4 | 3 | 190055 | 44251 | 80204 | 78 | 26447 | 9830 | 71 | 29160 | 15.3% |

## hypothese : la fracture est locale / non-locale

**`max_level` est SATURE** (100 % des candidats a T2) : cette section est
conservee pour memoire, la mesure qui fait foi est la **resistance a T0**
ci-dessous.

Attendu si l'hypothese tient : parmi les CANDIDATS, ceux dont le systeme
contient CONNECTED atteignent T2 nettement plus souvent que les autres.

- candidats AVEC connectivite : 20052, dont T2 : 100%
- candidats SANS connectivite : 29470, dont T2 : 100%
- **l'hypothese ne tient pas — le v2 n'est qu'un v1 elargi**

### censure de l'echantillon

- **20847 systemes avec CONNECTED sur 160666 (13.0%) sont abandonnes en TROP-CHER** et ne figurent donc pas dans la mesure ci-dessus.
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

*45232 candidats sur 49522 portent les champs bruts (91%).*

- `5c556c16ea8b` — 39267 candidats
  - AVEC connectivite (15924) : resistance **41.1%**
  - SANS connectivite (23343) : resistance **21.3%**
  - test de permutation : **p = 0.0005** — significatif.
- `89c65c03c4ad` — 264 candidats
  - AVEC connectivite (106) : resistance **46.7%**
  - SANS connectivite (158) : resistance **21.4%**
  - test de permutation : **p = 0.0005** — significatif.
- `ab89a63b01ef` — 2280 candidats
  - AVEC connectivite (944) : resistance **41.1%**
  - SANS connectivite (1336) : resistance **21.6%**
  - test de permutation : **p = 0.0005** — significatif.
- `06fe04a859f1` — 1195 candidats
  - AVEC connectivite (476) : resistance **41.0%**
  - SANS connectivite (719) : resistance **20.8%**
  - test de permutation : **p = 0.0005** — significatif.
- `62448a55927e` — 798 candidats
  - AVEC connectivite (333) : resistance **40.1%**
  - SANS connectivite (465) : resistance **20.2%**
  - test de permutation : **p = 0.0005** — significatif.
- `e3baecf8377b` — 657 candidats
  - AVEC connectivite (268) : resistance **42.1%**
  - SANS connectivite (389) : resistance **21.0%**
  - test de permutation : **p = 0.0005** — significatif.
- `23303c299f39` — 225 candidats
  - AVEC connectivite (91) : resistance **43.9%**
  - SANS connectivite (134) : resistance **20.7%**
  - test de permutation : **p = 0.0005** — significatif.
- `e40600351a72` — 194 candidats
  - AVEC connectivite (87) : resistance **40.0%**
  - SANS connectivite (107) : resistance **20.5%**
  - test de permutation : **p = 0.0005** — significatif.
- `e80bc1b2b437` — 75 candidats
  - AVEC connectivite (38) : resistance **36.9%**
  - SANS connectivite (37) : resistance **20.6%**
  - test de permutation : **p = 0.0005** — significatif.
- `0a74109317e5` — 80 candidats
  - AVEC connectivite (36) : resistance **37.5%**
  - SANS connectivite (44) : resistance **20.2%**
  - test de permutation : **p = 0.0005** — significatif.
- `8f22f0d2d442` — 65 candidats
  - AVEC connectivite (21) : resistance **41.0%**
  - SANS connectivite (44) : resistance **18.3%**
  - test de permutation : **p = 0.0005** — significatif.
- `b71bb0907fb5` — 53 candidats
  - AVEC connectivite (22) : resistance **42.1%**
  - SANS connectivite (31) : resistance **15.4%**
  - test de permutation : **p = 0.0005** — significatif.
- `e8a1f930f7b9` — 28 candidats
  - AVEC connectivite (11) : resistance **46.0%**
  - SANS connectivite (17) : resistance **15.9%**
  - *groupes trop petits (< 20) — aucun test*
- `84fba70921e0` — 33 candidats
  - AVEC connectivite (11) : resistance **45.2%**
  - SANS connectivite (22) : resistance **19.3%**
  - *groupes trop petits (< 20) — aucun test*

## profondeur en continu (secondaire — le seuil binaire sature, pas ceci)

**Cette mesure evalue l'EFFORT de deduction, pas la PROFONDEUR.** Un
systeme qui demande trois fois T2 est plus laborieux, pas plus profond
qu'un systeme qui en demande deux. Confondre les deux serait la
cinquieme metrique du projet a mesurer autre chose que ce qu'elle
annonce.

`max_level >= 2` vaut 100 % partout : le seuil ne discrimine plus. Le
nombre d'invocations par niveau, lui, varie -- c'est une mesure continue
qui ne sature pas.

- `5c556c16ea8b` — 39267 candidats
  - AVEC connectivite (15924) : T0=13.01 T1=0.00 T2=2.97 — pondere **5.95**
  - SANS connectivite (23343) : T0=15.92 T1=0.00 T2=2.65 — pondere **5.30**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `89c65c03c4ad` — 3389 candidats
  - AVEC connectivite (1304) : T0=13.03 T1=0.00 T2=2.97 — pondere **5.94**
  - SANS connectivite (2085) : T0=15.85 T1=0.02 T2=2.65 — pondere **5.32**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `ab89a63b01ef` — 2280 candidats
  - AVEC connectivite (944) : T0=13.04 T1=0.00 T2=3.02 — pondere **6.03**
  - SANS connectivite (1336) : T0=15.96 T1=0.00 T2=2.66 — pondere **5.32**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `06fe04a859f1` — 1195 candidats
  - AVEC connectivite (476) : T0=13.10 T1=0.00 T2=3.02 — pondere **6.05**
  - SANS connectivite (719) : T0=15.94 T1=0.00 T2=2.61 — pondere **5.22**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `615abe43d6bc` — 945 candidats
  - AVEC connectivite (397) : T0=12.99 T1=0.00 T2=2.95 — pondere **5.90**
  - SANS connectivite (548) : T0=15.85 T1=0.00 T2=2.67 — pondere **5.34**
  - test de permutation : p = 0.0060 — **A NE PAS RETENIR** : serie NON REPRODUCTIBLE. Un ecart significatif issu d'un moteur dont la source n'existe plus n'est pas un resultat, il n'est pas rejouable.
- `62448a55927e` — 798 candidats
  - AVEC connectivite (333) : T0=12.91 T1=0.00 T2=2.85 — pondere **5.71**
  - SANS connectivite (465) : T0=16.20 T1=0.00 T2=2.66 — pondere **5.32**
  - test de permutation : **p = 0.0995** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `e3baecf8377b` — 657 candidats
  - AVEC connectivite (268) : T0=13.02 T1=0.00 T2=3.09 — pondere **6.18**
  - SANS connectivite (389) : T0=16.01 T1=0.00 T2=2.62 — pondere **5.23**
  - test de permutation : **p = 0.0005** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `23303c299f39` — 225 candidats
  - AVEC connectivite (91) : T0=13.08 T1=0.00 T2=3.23 — pondere **6.46**
  - SANS connectivite (134) : T0=16.22 T1=0.00 T2=2.61 — pondere **5.22**
  - test de permutation : **p = 0.0060** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `e40600351a72` — 194 candidats
  - AVEC connectivite (87) : T0=12.83 T1=0.00 T2=2.89 — pondere **5.77**
  - SANS connectivite (107) : T0=16.52 T1=0.00 T2=2.63 — pondere **5.25**
  - test de permutation : **p = 0.2394** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `0327bdc4c76a` — 107 candidats
  - AVEC connectivite (38) : T0=12.34 T1=0.00 T2=2.92 — pondere **5.84**
  - SANS connectivite (69) : T0=15.97 T1=0.00 T2=2.45 — pondere **4.90**
  - test de permutation : **p = 0.1569** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `e80bc1b2b437` — 75 candidats
  - AVEC connectivite (38) : T0=13.03 T1=0.00 T2=2.47 — pondere **4.95**
  - SANS connectivite (37) : T0=16.00 T1=0.00 T2=2.70 — pondere **5.41**
  - test de permutation : **p = 0.5177** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `0a74109317e5` — 80 candidats
  - AVEC connectivite (36) : T0=14.11 T1=0.00 T2=2.72 — pondere **5.44**
  - SANS connectivite (44) : T0=16.16 T1=0.00 T2=2.45 — pondere **4.91**
  - test de permutation : **p = 0.4788** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `12564867381b` — 75 candidats
  - AVEC connectivite (28) : T0=12.82 T1=0.00 T2=2.79 — pondere **5.57**
  - SANS connectivite (47) : T0=15.09 T1=0.00 T2=2.68 — pondere **5.36**
  - test de permutation : **p = 0.8296** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `8f22f0d2d442` — 65 candidats
  - AVEC connectivite (21) : T0=13.38 T1=0.00 T2=2.71 — pondere **5.43**
  - SANS connectivite (44) : T0=15.98 T1=0.00 T2=2.43 — pondere **4.86**
  - test de permutation : **p = 0.4113** — **NON SIGNIFICATIF**, l'ecart est compatible avec le bruit. Ne pas conclure.
- `b71bb0907fb5` — 53 candidats
  - AVEC connectivite (22) : T0=12.32 T1=0.00 T2=3.14 — pondere **6.27**
  - SANS connectivite (31) : T0=16.16 T1=0.00 T2=2.00 — pondere **4.00**
  - test de permutation : **p = 0.0110** — ecart significatif au seuil 0.05, sur une serie reproductible.
- `12a0c0c5e34b` — 31 candidats
  - AVEC connectivite (13) : T0=13.31 T1=0.00 T2=3.08 — pondere **6.15**
  - SANS connectivite (18) : T0=15.83 T1=0.00 T2=2.94 — pondere **5.89**
  - *groupes trop petits (< 20) — aucun test, aucune conclusion*
- `e8a1f930f7b9` — 28 candidats
  - AVEC connectivite (11) : T0=13.45 T1=0.00 T2=3.55 — pondere **7.09**
  - SANS connectivite (17) : T0=17.35 T1=0.00 T2=2.41 — pondere **4.82**
  - *groupes trop petits (< 20) — aucun test, aucune conclusion*
- `84fba70921e0` — 33 candidats
  - AVEC connectivite (11) : T0=13.27 T1=0.00 T2=3.09 — pondere **6.18**
  - SANS connectivite (22) : T0=15.36 T1=0.00 T2=2.82 — pondere **5.64**
  - *groupes trop petits (< 20) — aucun test, aucune conclusion*

### ce que les series reproductibles etablissent

**7 serie(s) reproductible(s) sur 14 etablissent l'ecart** : `5c556c16ea8b` (p=0.0005), `89c65c03c4ad` (p=0.0005), `ab89a63b01ef` (p=0.0005), `06fe04a859f1` (p=0.0005), `e3baecf8377b` (p=0.0005), `23303c299f39` (p=0.0060), `b71bb0907fb5` (p=0.0110).

*Test de permutation bilateral, 2000 melanges, stdlib seule. Un ecart non*
*significatif ne dit pas qu'il n'y a pas d'effet : il dit que ces donnees*
*ne permettent pas de le distinguer du hasard.*


## meilleurs candidats (niveau requis, puis indices les plus rares)

- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.06 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid
- `T2` indices=0.06 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — CONNECTED(v2) + COUNT(v2,1-2)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@adj
- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-4)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-3)@grid
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid
- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-2)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-2)@grid
- `T2` indices=0.06 — CONNECTED(v2) + COUNT(v2,1-4)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight
- `T2` indices=0.06 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-3)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight
- `T2` indices=0.06 — CONNECTED(v2) + COUNT(v2,1-5)@grid + PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid
- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-5)@grid + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-3)@grid + PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight
- `T2` indices=0.06 — PAIRDIFF(>=1)@adj + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid + PAIRSTEP(1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@adj + CONNECTED(v2) + COUNT(v2,1-4)@grid
- `T2` indices=0.06 — PAIRSTEP(1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-3)@grid + PAIRDIFF(>=1)@adj
- `T2` indices=0.06 — CONNECTED(v0) + COUNT(v0,1-3)@grid + PAIRDIFF(>=1)@knight + PAIRSTEP(1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v2) + NOSQUARE(v2) + COUNT(v2,1-5)@grid
- `T2` indices=0.06 — PAIRDIFF(>=1)@adj + PAIRSTEP(1)@knight + CONNECTED(v0) + COUNT(v0,1-2)@grid
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v2) + COUNT(v2,1-4)@grid
- `T2` indices=0.06 — PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid + PAIRSTEP(1)@knight
- `T2` indices=0.06 — PAIRSTEP(1)@knight + PAIRDIFF(>=1)@knight + CONNECTED(v0) + NOSQUARE(v0) + COUNT(v0,1-5)@grid

## cout
- temps total 121.2 h, dont 2% brule sur des systemes MORT
- TROP-CHER : 20928 systemes abandonnes (5.4% des systemes), 96% du temps total
  dont 20847 avec CONNECTED, 81 sans -- **chiffre CONFONDU** : seul le tag connect peut produire des systemes avec CONNECTED, ce ratio melange l'effet de la connectivite et celui de la configuration. Voir la ventilation ci-dessous.
- taux de TROP-CHER **dans le seul tag connect** (a configuration egale, non confondu) :
  - avec CONNECTED : 13.0% sur 158165 systemes
  - sans CONNECTED : 0.0% sur 35733 systemes
