# A EST UN CHANTIER DE DEBIT, PAS UN CHANTIER DE MESURE

**A lire avant tout le reste de ce document.**

A n'existe pas pour deduire mieux. A existe pour rendre **n=5 praticable sous
la borne de 20 s par systeme**. C'est la seule experience qui puisse trancher
l'hypothese centrale, et elle est aujourd'hui hors de portee en temps de
calcul.

**Consequence directe sur le branchement** : ce qu'il faudra verifier en
priorite est le **cout par systeme**, pas la qualite de deduction. Le critere
de succes de A est un debit, pas un taux de resolution.

**Consequence sur le n=4** : brancher la propagation dans une hierarchie a n=4
saturerait davantage un regime **deja sature** -- T0 seul y resout 60 a 92 %
des instances. Ce serait le motif du projet applique au chantier lui-meme :
un instrument plus fin dans un regime ou il n'y a plus rien a distinguer.

---

# PERIMETRE-A.md — etat de candidats explicite dans engine/

Document de decision. **Aucun code n'a ete ecrit.** Il decrit ce qu'il faudrait
reecrire, contrainte par contrainte, avec ce qui se propage facilement et ce
qui pose probleme.

Redige le 2026-08-26, apres lecture integrale de `engine/rulesearch.py`,
`engine/dsl2.py`, `engine/deduction.py`, `engine/prefilter.py`.

---

## 1. Ce qui change, en une phrase

Aujourd'hui il n'existe **aucune representation des candidats**. Pour savoir ce
qu'une cellule peut valoir, `deduction.candidates()` essaie chaque valeur et
appelle `feasible()` :

    for v in range(rs.d):
        g[i] = v
        if rs.feasible(g, changed=i):
            out.append(v)

A recalculer a chaque appel, et **uniquement contre les cellules deja
assignees** — les autres sont `UNASSIGNED`, donc invisibles.

A signifie : un domaine `dom[i] ⊆ {0..d-1}` par cellule, reduit par propagation
jusqu'au point fixe, et **partage entre contraintes**. Chaque contrainte gagne
une methode `propagate(dom) -> (modifie, contradiction)` en plus de
`feasible(g)`.

---

## 2. Consequence a lire AVANT le reste

**T0 ne voudrait plus dire la meme chose.** Aujourd'hui `candidates()` filtre
contre les valeurs **assignees** — c'est du forward-checking. Une propagation
sur domaines filtre contre les **domaines** des autres cellules, ce qui est
**strictement plus fort**.

Trois consequences :

1. **La metrique acquise change de definition.** La "resistance a T0" est
   definie comme le residu apres saturation de T0. Si T0 devient plus fort, la
   resistance mesuree baisse mecaniquement — sans que rien n'ait change dans
   les systemes. Les chiffres d'avant et d'apres **ne se comparent pas**, et
   pas seulement a cause du `dsl_hash`.
2. **La hierarchie doit etre redefinie.** Avec un etat de candidats,
   "propagation jusqu'au point fixe" absorbe T0 et une partie de T1. Les
   paliers actuels n'ont plus les memes frontieres.
3. **`canary3` doit etre etendu AVANT la premiere ligne de propagation**, pas
   apres. C'est deja un invariant ; il devient ici la condition de survie du
   chantier (voir §6).

---

## 3. Perimetre, fichier par fichier

| fichier | ce qu'il faut toucher | ampleur |
|---|---|---|
| `engine/rulesearch.py` | 6 classes de contraintes + `RuleSystem.feasible` + `count_solutions` + `deduce` + `random_solution` + `minimal_clues` | **le gros** |
| `engine/dsl2.py` | 4 classes de contraintes | moyen |
| `engine/deduction.py` | `candidates`, `apply_T0`, `apply_T1`, `apply_T2`, `saturate_low`, `solve_graded` | reecriture conceptuelle |
| `engine/prefilter.py` | `is_dead` — devient trivial (propagation deja disponible) | **simplification** |
| `canary/canary3.py` | extension obligatoire **avant** | prealable |
| `run.py`, `summarize.py` | inchanges si l'interface `solve_graded` est preservee | nul a faible |

A cela s'ajoute un **moteur de propagation** qui n'existe pas : file de
contraintes a reveiller, boucle jusqu'au point fixe, detection de
contradiction. `RuleSystem.touch` fournit deja l'index cellule -> contraintes,
donc le reveil cible est immediat. C'est la seule brique deja en place.

---

## 4. Contrainte par contrainte

### Faciles — regle de propagation standard, aucune difficulte

| contrainte | fichier | regle de filtrage | cout |
|---|---|---|---|
| `AllDiff(R)` | rulesearch | valeur assignee retiree des autres domaines. GAC possible par couplage (Regin) si besoin | O(\|R\|·d) en naif |
| `Count(R, val, lo, hi)` | rulesearch | `cur` = cellules a `val`, `pot` = cellules pouvant valoir `val`. Si `cur == hi` retirer `val` partout ailleurs ; si `cur + pot == lo` forcer `val` sur toutes celles qui le peuvent | O(\|R\|) |
| `SumRange(R, lo, hi, d)` | rulesearch | coherence aux bornes : pour chaque cellule, `dom` ∩ `[lo - maxAutres, hi - minAutres]` | O(\|R\|·d) |
| `NeqAdj(R)` | rulesearch | binaire ≠ sur paires consecutives : retrait de la valeur fixee chez le voisin | O(\|R\|) |
| `Mono(R)` | rulesearch | balayage avant/arriere sur les bornes : `min[i] ≥ min[i-1]`, `max[i] ≤ max[i+1]` | O(\|R\|) |
| `PairDiff(pairs, k)` | dsl2 | binaire, AC directe : `v` survit dans `dom[a]` s'il existe `w ∈ dom[b]` avec `\|v-w\| ≥ k` | O(\|pairs\|·d²) |
| `PairRatio(pairs, δ)` | dsl2 | idem avec `\|v-w\| ∈ {0, δ}` | O(\|pairs\|·d²) |

Sept contraintes sur dix, sans piege. Ce sont des propagateurs de manuel.

### Moyennes — decomposition necessaire, sinon rien de grave

| contrainte | difficulte | regle |
|---|---|---|
| `NoTriple(R)` | ternaire glissante | fenetres de 3 cellules consecutives. Si deux voisines sont fixees a `v`, retirer `v` de la troisieme. AC par fenetre, pas globale |
| `NoSquare(n, val)` | quaternaire, **mal modelisee** | son `region` est **la grille entiere** : toute assignation la reveille. Il faut la **decomposer en (n-1)² contraintes de fenetre 2x2**, chacune sur 4 cellules. Regle : si 3 des 4 valent `val`, retirer `val` de la 4e |

`NoSquare` est le seul cas ou le **modele actuel est en cause** et pas la
technique : `region = list(range(n*n))` est un artefact qui rend le reveil
cible inutile. La decomposition est mecanique.

### Difficile — `Connected`, et c'est la seule

`Connected(n, val)` : les cellules valant `val` forment **une** composante
connexe en 4-connexite.

**Ce qui marche deja et se garde.** Le test de faisabilite actuel est une
accessibilite dans le sous-graphe « cellules valant `val` ou libres ». C'est
sain, polynomial, et directement reutilisable comme detection de
contradiction.

**Ce qu'on peut filtrer — regles saines et calculables :**

1. **Retrait par inaccessibilite.** Une cellule libre `x` qui n'est pas
   atteignable depuis la composante fixee dans le sous-graphe passable ne peut
   pas valoir `val` : l'y mettre creerait une seconde composante. Donc
   `val` sort de `dom[x]`. Coût : un parcours O(V+E), soit O(n²).

2. **Forcage par point d'articulation.** Si une cellule libre `x` est un
   **point d'articulation** dont le retrait separe deux cellules deja fixees a
   `val`, alors `x` **doit** valoir `val`. Donc `dom[x] = {val}`. Calculable par
   Tarjan en O(V+E).

3. **Contradiction.** Si les cellules fixees a `val` sont deja separees dans le
   passable : echec. C'est le test actuel.

Ces trois regles sont **saines mais incompletes**.

**Ce qu'on ne peut PAS avoir.** Le filtrage complet (GAC) est hors de portee :
decider si une assignation partielle s'etend en un sous-graphe connexe
contenant des sommets imposes est un probleme de type **Steiner**, NP-difficile
dans le cas general. *(Affirmation issue de la litterature, non verifiee
experimentalement dans ce projet — a confirmer avant de s'en servir comme
argument decisif.)*

Nuance qui compte pour nous : a n=4 la grille fait 16 cellules et la force
brute reste possible. Le probleme mord a **n=5 (25 cellules) et n=6 (36)** —
c'est-a-dire exactement le regime que A doit servir. Il ne faut donc pas
compter sur un filtrage complet de la connexite a la taille visee.

**Consequence de conception :** `Connected` restera le propagateur le plus
faible relativement a ce qu'il devrait faire. C'est acceptable — un propagateur
sain et incomplet ne rend jamais de resultat faux, il laisse seulement du
travail au solveur — mais il faut le savoir : **A ne rendra pas la connectivite
"facile"**, elle la rendra seulement moins couteuse.

Ironie a noter : c'est la contrainte la plus difficile a propager qui est aussi
la seule dont le projet a besoin pour son hypothese centrale.

---

## 5. Ce que A rapporte, et ce qu'il ne rapporte pas

**Rapporte :**

- **Les techniques d'ELIMINATION deviennent operantes.** Paire nue, paire
  cachee, triplets, X-Wing — toute la classe aujourd'hui inerte (deux
  tentatives, deux echecs, cause structurelle documentee). C'est la seule voie
  connue vers une metrique de profondeur non saturee.
- **Le debit.** `candidates()` est appele dans la boucle la plus chaude et
  recalcule tout a chaque fois. Un domaine maintenu incrementalement supprime
  ce recalcul. **Aucune mesure ne chiffre ce gain** — c'est une attente, pas un
  resultat.
- `prefilter.is_dead` devient une simple propagation sur grille vide.

**Ne rapporte pas :**

- Ne rend pas la connexite complete (§4).
- Ne repond pas a l'hypothese centrale par lui-meme : il rend la mesure
  *possible* a n=5/n=6, il ne la fait pas.
- Ne dispense pas de n=5 : a n=4 la hierarchie n'a pas la place de se deployer,
  quel que soit le moteur.

---

## 6. Risques, dans l'ordre de gravite

1. **Le risque asymetrique, deja documente.** Un bug de propagation **ne plante
   pas** : il retire un candidat de trop, la deduction remplit quand meme la
   grille, et rend une **solution FAUSSE**. C'est le mode de defaillance du bug
   T1 — reparti sur tout le moteur et sur chaque type de contrainte. `canary3`
   est le seul filet : il exige que la deduction retrouve **exactement** la
   solution d'origine.

   **Condition non negociable : etendre `canary3` avant d'ecrire la premiere
   ligne de propagation.** Chaque propagateur doit y avoir un cas, et
   `Connected` plusieurs.

2. **La metrique acquise change de definition** (§2). Le projet perdrait sa
   seule mesure etablie le temps de la reconstruire. Il faut decider a l'avance
   si on la redefinit sur la nouvelle propagation ou si on gele une version
   « T0 historique » pour garder la continuite.

3. **Rupture de serie.** `dsl_hash` change des la premiere ligne. Toutes les
   donnees accumulees deviennent incomparables. Deja arrive plusieurs fois, le
   protocole est rode, mais le compteur repart de zero.

4. **Duree.** Sept propagateurs faciles, deux moyens, un difficile, plus un
   moteur de point fixe, plus la reecriture de `deduction.py`, plus l'extension
   prealable de `canary3`. Aucune estimation chiffree n'est donnee ici : je
   n'ai pas de base de mesure pour la produire, et une estimation inventee
   serait le genre de chiffre que ce projet passe son temps a corriger.

---

## 7. Ordre propose, si A est ouvert

Chaque etape est un point d'arret ou l'on peut renoncer sans avoir casse le
moteur en service.

1. **Etendre `canary3`** aux dix contraintes, moteur actuel inchange. Sans
   valeur en soi, mais c'est le filet. Aucun risque.
2. **Ecrire le moteur de propagation a cote**, sans le brancher : `dom`, file
   de reveil, point fixe. Les contraintes gardent `feasible()`.
3. **Les sept propagateurs faciles**, un par un, chacun valide par `canary3`
   contre le comportement actuel : la propagation ne doit jamais retirer une
   valeur qui appartient a une solution.
4. **`NoTriple` et la decomposition de `NoSquare`.**
5. **`Connected`** : d'abord la contradiction (existante), puis le retrait par
   inaccessibilite, puis le forcage par articulation. Chaque regle validee
   separement.
6. **Brancher** `deduction.py` sur les domaines, redefinir les paliers, decider
   du sort de la metrique de resistance.
7. **Puis seulement** envisager n=5.

---

## 8. Ce que je recommande

**Ouvrir A, mais pas pour la raison invoquee jusqu'ici.**

L'argument « A debloque les techniques d'elimination » est vrai et secondaire :
a n=4 la hierarchie n'a de toute facon pas la place de se deployer, donc les
techniques debloquees n'auraient rien a mesurer.

L'argument qui tient est celui du **debit**. La profondeur n'est pas mesurable
a n=4 — c'est etabli, pas suppose. Elle ne le sera qu'a n=5/n=6. Or a ces
tailles le recalcul integral de `candidates()` devient le goulot, et la borne
de temps censurerait exactement les systemes profonds. **A n'est pas un detour
avant n=5 : c'est sa condition de possibilite.**

Si A n'est pas ouvert, la consequence doit etre assumee explicitement : le
projet reste a n=4, la profondeur n'y est pas mesurable, et l'hypothese
centrale reste **ouverte indefiniment**. Ce serait un choix defendable — le
resultat acquis sur la non-localite a une valeur propre — mais c'est un choix,
pas un report.
