# CLAUDE.md — rulesearch

Lis ce fichier en entier avant toute action. Puis `summary.md`. Puis
`DECISIONS.md`. Ne touche pas au code avant ces trois lectures.

## Ce qu'on cherche

L'espace des **systemes de regles** de puzzles, pas l'espace des instances.
Generer un sudoku est resolu ; chercher quelles familles de regles produisent
des puzzles bien poses ne l'est pas.

Un systeme est retenu (CANDIDAT) s'il produit des instances a solution
unique, resolubles par deduction pure sans devinette, avec peu d'indices
et un niveau de technique superieur au plus faible.

Verdicts possibles : MORT, SUR-CONTRAINT, LIBRE, DEVINETTE, PLAT, CANDIDAT,
plus deux abandons a ne pas confondre :

- **TIMEOUT** : budget de **noeuds** epuise dans `count_solutions`.
- **TROP-CHER** : budget de **temps par systeme** depasse (`--max-seconds`,
  20 s par defaut), impose par **SIGALRM**. Le record porte alors un champ
  `phase` disant quelle fonction consommait le temps.
  `count_solutions` avait un budget de noeuds, mais
  `random_solution` et `minimal_clues` n'en avaient aucun : un systeme vivant
  et couteux pouvait bloquer un bloc entier.

La surete de cette interruption est gardee par `canary/canary5.py`, dans les
deux sens : faux negatif (l'alarme ne se declenche pas) et faux positif (un
systeme sain etiquete TROP-CHER, qui disparaitrait des candidats sans
laisser de trace). Ce chemin a deja echoue silencieusement une fois.

TROP-CHER n'est pas qu'une rustine : un systeme trop cher a evaluer a n=4 est
un **fait sur le systeme**. La question ouverte est de savoir si la
connectivite en produit systematiquement -- `summarize.py` ventile les
TROP-CHER avec et sans CONNECTED.

## Ce que l'oracle ne couvre pas

La structure est calculable. L'interet de jouer ne l'est pas. Ce moteur est
un **filtre d'elimination**, jamais un juge. Ne jamais ecrire qu'un systeme
est "bon" ou "amusant" : il est bien pose, c'est tout.

## Invariants durs — ne jamais violer

1. Les canaris tournent avant tout run. `--skip-canary` est reserve au debug.
   Un banc casse produit du bruit indistinguable de vrais resultats.
2. Ne jamais comparer des lignes de `dsl_hash` differents. Le hash change des
   qu'un fichier de `engine/` change.
3. Toute nouvelle technique de deduction exige un canari de CORRECTION avant
   d'etre utilisee : la deduction doit retrouver EXACTEMENT la solution
   d'origine, pas seulement remplir la grille.
4. Ne conclure sur aucune hypothese sous 20 candidats par groupe compare.
5. La tache nocturne headless n'ecrit que des analyses. Elle ne modifie pas
   `engine/`, ne change pas les seuils, ne supprime aucun journal.

## Erreurs deja payees — ne pas les refaire

- **T1 faux (corrige).** "hidden single" n'est valide que sur un ALLDIFF de
  taille exactement d. Applique a toute region, il force des valeurs a tort.
  Invisible sur le sudoku, qui satisfait la condition partout. C'est ce qui a
  motive l'invariant 3.
- **DSL v1 trop pauvre.** Regions statiques seules (lignes, colonnes, blocs,
  diagonales) : l'espace ne pouvait produire que des variantes de sudoku. Ce
  n'etait pas un probleme de solveur mais de langage.
- **Mesure de profondeur vide.** Compter les passes d'une technique unique
  sature vers 2-3 pour tout, sudoku compris. La profondeur ne veut dire
  quelque chose que relativement a une hierarchie de techniques.

## Hypothese en cours

La ligne de fracture entre systemes plats et systemes profonds n'est pas
"quelles contraintes" mais **decomposable localement ou non**. La
connectivite (`Connected`) est le seul type non decomposable en contraintes
locales.

Test : parmi les CANDIDATS, ceux contenant CONNECTED atteignent-ils T2
nettement plus souvent que les autres, a taux de candidats comparable ?
`summarize.py` calcule cet ecart et refuse de conclure sous 20 par groupe.

Sur 49 systemes (echantillon sans valeur statistique) : config `connect`
12,5 % de candidats tous a T2, config statique 0 %. Va dans le sens de
l'hypothese, ne la prouve pas.

Si l'hypothese tombe, le DSL v2 n'est qu'un v1 elargi et il faut chercher la
fracture ailleurs.

## Question ouverte : le budget de noeuds de count_solutions

En construisant `canary5.py`, seul `minimal_clues` avait ete rendu
pathologique. Des systemes ont pourtant ete interrompus par l'alarme en
**`phase == "count_solutions"`**, fonction qui n'avait pas ete truquee.

Si `count_solutions` peut consommer 3 s et plus alors qu'elle possede un budget
de **noeuds**, ce budget ne borne pas ce qu'on croit. Ce serait un **defaut du
solveur**, pas une simple lenteur : un budget de noeuds cense garantir une
terminaison bornee qui ne la garantit pas.

Non tranche, et **a ne pas corriger a l'aveugle**. La mesure qui repond est la
distribution du champ `phase` sur les vrais TROP-CHER de production. Si
`count_solutions` y domine, le budget de noeuds est a revoir ; s'il est
marginal, l'observation etait un artefact du banc.

Ne pas toucher au solveur avant d'avoir cette distribution.

## Prochaine tache, par priorite

1. **Debit.** ~70 % du temps machine part a decouvrir par solveur complet
   qu'un systeme n'a aucune solution.

   FAIT (25/08) : le pre-filtre par propagation est en place
   (`engine/prefilter.py`, canari `canary/canary4.py`). Il attrape 15-30 %
   des morts pour un cout negligeable, zero faux positif. Gain reel : de
   l'ordre de 20 %, pas le facteur ~30 qui figurait ici. Cette estimation
   etait fausse d'un ordre de grandeur.

   MESURE ET ECARTE : renforcer le pre-filtre avec T2 attrape 52 % des morts
   mais coute un tiers du temps qu'il economise. Ratio nettement moins bon
   que T0 seul.

   MESURE ET ECARTE : reordonner le solveur n'apporte rien. MRV dynamique
   reduit les noeuds de 35 % mais DOUBLE le temps -- le calcul du domaine a
   chaque noeud coute plus que les branches evitees. L'ordre statique par
   degre gagne 5 %, dans le bruit. Les trois variantes donnent des comptes
   de solutions identiques, donc la mesure est fiable.

   GOULOT RESTANT, non traite : le cout par appel a `feasible`. Chaque
   contrainte recalcule sa region entiere a chaque assignation. C'est la que
   part le temps, et le rendre incrementiel demanderait de toucher au
   solveur -- ce que la section suivante interdit. A rouvrir explicitement
   dans DECISIONS.md si le debit reste bloquant.
2. Etendre a n=5 et n=6 une fois le pre-filtre en place.
3. Ajouter T3 (paires/triplets nus) si et seulement si T2 sature.

## Ce qu'il ne faut pas faire

- Elargir le DSL sans ajouter le canari correspondant.
- Reecrire le solveur "au propre". Il marche et il est verifie.
- Ajouter des dependances. Stdlib seule, c'est un choix : le moteur doit
  tourner sur pypy3 sans installation.
- Conclure sur des echantillons faibles parce que la tendance est jolie.

## Protocole de session (Claude Code)

Le depot est sur un serveur distant. Alias SSH : `rulesearch`, chemin
`/home/rulesearch/rulesearch`.

A chaque intervention, dans cet ordre :

1. Lire `CLAUDE.md`, `DECISIONS.md`, puis `WORKLOG.md` (entree la plus
   recente en haut) avant toute action.
2. Verifier que le depot local du serveur est a jour : `git pull`.
3. Faire le travail demande.
4. Verifier reellement : les trois canaris doivent passer, et pour tout
   probleme de service, l'observer demarrer et tourner -- pas seulement
   constater que la commande n'a pas renvoye d'erreur.
5. Ecrire l'entree dans `WORKLOG.md` selon le gabarit du fichier.
6. Commit et push.

Distinguer toujours ce qui a ete verifie de ce qui est suppose. Une cause
plausible non testee s'ecrit comme telle.

Si une commande est refusee (sudo, droits, reseau), le dire dans le
WORKLOG et s'arreter la plutot que de contourner.

Une decision structurante (changement de seuil, de metrique, d'hypothese,
abandon d'une piste) s'ajoute a `DECISIONS.md` avec sa raison et son
critere de reouverture. Ne jamais reecrire une entree existante.
