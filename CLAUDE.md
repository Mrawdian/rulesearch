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
   **Purger `__pycache__` apres toute modification de `engine/`** : un
   bytecode perime peut faire tourner un code different de la source, alors
   que `dsl_hash` ne hache que les `.py`. Constate le 26/08/2026.
2. Ne jamais comparer des lignes de `dsl_hash` differents. Le hash change des
   qu'un fichier de `engine/` change.
3. Toute nouvelle technique de deduction exige un canari de CORRECTION avant
   d'etre utilisee : la deduction doit retrouver EXACTEMENT la solution
   d'origine, pas seulement remplir la grille.
4. Ne conclure sur aucune hypothese sous 20 candidats par groupe compare.
5. La tache nocturne headless n'ecrit que des analyses. Elle ne modifie pas
   `engine/`, ne change pas les seuils, ne supprime aucun journal.
6. **Toute technique de deduction doit prouver qu'elle se declenche.** Une
   technique correcte mais inerte est du code mort deguise en mesure : elle
   laisse croire que la hierarchie discrimine sur un niveau qui n'existe
   pas en pratique. `canary6` l'exige pour tout niveau <= 
   `DEFAULT_MAX_LEVEL` ; relever cette constante sans rendre la technique
   operante fait echouer les canaris, donc bloque le run.
7. **Toute nouvelle metrique doit etre testee dans le regime ou on compte
   l'utiliser**, pas seulement sur un cas ou elle discrimine. Une metrique
   validee sur un cas facile puis deployee sur un regime saturant ne
   mesure plus rien, et le pire est qu'elle continue d'imprimer des
   chiffres. Voir la liste ci-dessous : c'est l'erreur la plus repetee du
   projet.

## Erreurs deja payees — ne pas les refaire

- **T1 faux (corrige).** "hidden single" n'est valide que sur un ALLDIFF de
  taille exactement d. Applique a toute region, il force des valeurs a tort.
  Invisible sur le sudoku, qui satisfait la condition partout. C'est ce qui a
  motive l'invariant 3.
- **DSL v1 trop pauvre.** Regions statiques seules (lignes, colonnes, blocs,
  diagonales) : l'espace ne pouvait produire que des variantes de sudoku. Ce
  n'etait pas un probleme de solveur mais de langage.
- **T2 a sature (26/08/2026).** Tous les candidats atteignant T2, la
  fraction "atteint T2" valait 100 % dans les deux groupes compares. Le
  verdict automatique de `summarize.py` imprimait alors
  "l'hypothese ne tient pas" -- une **refutation jamais etablie**, produite
  par un `a < b + 0.05` satisfait par 1,0 < 1,05. Saturation n'est pas
  absence d'effet. Corrige : le resume imprime desormais INDICATEUR SATURE
  et refuse de conclure.
- **T3 correct mais inerte, DEUX FOIS (26/08/2026).** Paire nue, puis paire
  cachee : les deux implementees, les deux verifiees correctes par
  `canary3` sur les cinq familles, les deux **jamais declenchees**. La
  cause n'est pas le choix de la technique mais le moteur lui-meme -- voir
  la section sur les techniques d'elimination. Chercher une troisieme
  technique d'elimination serait la troisieme fois. D'ou `canary6`.
- **Mesure de profondeur vide.** Compter les passes d'une technique unique
  sature vers 2-3 pour tout, sudoku compris. La profondeur ne veut dire
  quelque chose que relativement a une hierarchie de techniques.

## Le motif qui revient : des metriques qui mesurent autre chose

**Quatre fois** le projet a produit un chiffre qui ne mesurait pas ce qu'il
annoncait :

1. **T1 faux** : remplissait la grille et se trompait de solution.
2. **Profondeur v1** : saturait vers 2-3 pour tout, sudoku compris.
3. **T2 sature** : 100 % contre 100 %, et le verdict automatique imprimait
   une refutation non etablie.
4. **T3 inerte** : correct, verifie, et jamais declenche.

Les cas 3 et 4 partagent une cause precise : **une metrique livree sans
avoir ete testee dans le regime ou elle allait servir**. Le cas 4 est
survenu immediatement apres que cette regle ait ete ecrite -- l'ecrire ne
suffit donc pas, d'ou son passage en invariant dur (6 et 7) et sa mise en
canari (`canary6`).

Regle operationnelle : une metrique n'est acquise que lorsqu'un canari
echoue quand elle cesse de mesurer. Un document ne l'a jamais garantie.

## Pourquoi le moteur ne peut pas porter de technique d'ELIMINATION

Le moteur n'a **aucune representation des candidats** : `candidates()` les
recalcule a chaque appel a partir de `feasible()`. Il n'existe aucun endroit ou
inscrire "la valeur v n'est plus possible en case k".

Consequence, et c'est un **theoreme, pas une observation** : une technique dont
la conclusion est "eliminer des candidats" ne peut produire d'effet que si
l'elimination reduit une cellule a une seule valeur -- cas que T0 traite deja.
Toute technique d'elimination est donc **inerte par construction**, quelle que
soit sa correction.

Deux l'ont confirme, l'une apres l'autre :
- **paire nue** : deux cellules aux memes deux candidats. Elimine ces valeurs
  ailleurs dans la region. 0 invocation.
- **paire cachee** : deux valeurs n'ayant que les deux memes cases. Reserve ces
  cases, elimine le reste. 0 invocation. La demonstration est directe : si u et
  v n'ont que les cases {i,j}, alors u et v sont tous deux candidats en i comme
  en j, donc l'elimination laisse exactement deux candidats, jamais un seul.
  Et le cas ou il n'en resterait qu'un est deja capture par T1.

**Regle : seules les techniques qui POSENT une valeur ("la case k vaut v")
peuvent fonctionner sur ce moteur.** T0, T1 et T2 en sont. Avant d'implementer
toute nouvelle technique, verifier cette propriete -- pas apres.

## Si quelqu'un rouvre l'option d'un etat de candidats explicite

Le risque est **asymetrique, et c'est le point qui doit etre lu avant de
commencer**. Un bug de propagation ne plante pas : il retire un candidat de
trop, la deduction remplit quand meme la grille, et rend une solution FAUSSE.
C'est exactement le mode de defaillance du bug T1 -- mais reparti sur tout le
moteur au lieu d'une seule fonction, et sur chaque type de contrainte, y
compris `Connected` qui est la plus difficile a propager correctement puisque
non decomposable localement.

`canary3` reste le filet : il exige que la deduction retrouve EXACTEMENT la
solution d'origine. Ne jamais entreprendre ce chantier sans l'etendre d'abord.

## Etat de la mesure de profondeur -- a lire avant d'en tirer quoi que ce soit

- `max_level >= 2` vaut **100 % partout** : le seuil est SATURE, il ne
  discrimine plus. Aucune conclusion, ni pour ni contre l'hypothese, ne peut
  en etre tiree.
- **T1 n'a jamais ete invoquee en production.** La hierarchie effective est
  **T0/T2**, pas T0/T1/T2. Le niveau intermediaire est vide.
- Il n'y a **pas de T3** : deux techniques d'elimination ont ete implementees,
  verifiees correctes, et retirees pour inertie. Voir plus haut.
- Ce qui discrimine encore : la mesure **continue** publiee par
  `summarize.py` -- invocations par niveau, ponderees. Les systemes a
  connectivite demandent plus de T2 et moins de T0. Ecart faible, dans le sens
  de l'hypothese, sur trois series sur quatre.

**EFFORT N'EST PAS PROFONDEUR.** La mesure continue compte des invocations :
elle dit qu'un systeme est plus **laborieux**, pas qu'il est plus **profond**.
La profondeur au sens du projet est le niveau de technique requis -- une
propriete structurelle -- alors que le nombre d'invocations depend aussi de la
taille du systeme, du nombre de cellules libres et de l'ordre de parcours.
Ecrire "plus profond" a partir de ce chiffre serait la **cinquieme** metrique
du projet a mesurer autre chose que ce qu'elle annonce. L'avertissement figure
aussi dans `summary.md`, a cote du chiffre.

Et tant qu'un test de significativite ne tranche pas, cet ecart **n'est pas un
resultat** : `summarize.py` applique un test de permutation et refuse de
conclure au-dessus de p = 0,05, exactement comme il refuse sous 20 candidats
par groupe.

## Pourquoi T1 n'a aucun domaine d'application

Mesure du 26/08/2026, qui explique les 0 invocations de T1 :

    connect     n=4 d=3   0 systeme sur 600 avec une region T1 eligible
                          0 contrainte ALLDIFF generee, tout court
    static-ref  n=4 d=3   0 systeme sur 590, 0 ALLDIFF
    baseline    n=4 d=4   126 systemes sur 600 (21 %), 322 ALLDIFF de taille d

`t1_regions()` n'accepte qu'un ALLDIFF de taille **exactement d** -- restriction
correcte, c'est elle qui corrige le bug T1. Or a n=4 et d=3, les regions
structurelles (lignes, colonnes, blocs) sont de taille 4, donc ni de taille d,
ni meme porteuses d'un ALLDIFF : un ALLDIFF sur 4 cases avec 3 valeurs est
infaisable par principe des tiroirs, et le generateur n'en produit pas.

T1 n'est donc ni fausse ni inerte : elle est **sans domaine** dans l'espace que
la file explore actuellement. Elle redevient utile des que d = taille de region,
ce qui est le cas de `baseline` a d=4.

Consequence a ne pas manquer : `saturate_low()` (T0+T1) se reduit a **T0 seul**
dans cet espace. Toute technique definie comme "T2 mais avec T0 seul au lieu de
T0+T1" y est donc **exactement identique a T2**, pas une version affaiblie.

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
3. **T2 a sature, donc T3 est requis -- mais T3 tel qu'implemente est
   inerte.** Choix a trancher, non tranche :
   - **A.** donner au moteur un etat de candidats explicite (un domaine par
     cellule, propage et reduit). Rend operantes T3 et toute technique
     d'elimination. Touche `engine/` en profondeur.
   - **B.** une technique qui POSE des valeurs au lieu d'en eliminer.
     Compatible avec le moteur actuel. La seule famille connue qui
     convienne est la contradiction (comme T2), mais a profondeur 2 le
     cout est **multiplicatif** et non additif : T2 imbrique dans T2. Elle
     censurerait davantage de systemes profonds -- donc detruirait la
     mesure qu'elle permet. Non retenue en l'etat.
   Reformulation retenue : A etant la **seule voie connue** vers une
   metrique non saturee, la question n'est plus *quand* reecrire le
   moteur mais **accepte-t-on de ne jamais mesurer la profondeur au-dela
   de T2**. Une piste moins couteuse existe : combler le trou entre T0 et
   T2, puisque T1 est sans emploi dans l'espace explore.

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
