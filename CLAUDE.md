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
7bis. **Toute nouvelle metrique doit etre testee contre les variables DEJA
   JOURNALISEES avant d'etre adoptee** -- `clue_frac` en premier, puis
   `total_grids`, `n`, `d`. Le confondant n'est presque jamais exotique : il
   est dans le journal, a cote. La "resistance a T0" normalisee sur la grille
   affichait 74 % contre 98 % ; l'ecart etait entierement du a la densite
   d'indices, visible dans la colonne voisine du meme tableau.
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
- **Resistance a T0 confondue par la densite d'indices (26/08/2026).**
  Normalisee sur la grille entiere, elle donnait 74 % contre 98 % --
  ecart entierement explique par `clue_frac` (6,0 indices contre 9,5). En
  points ajoutes par T0, les deux groupes etaient identiques. Le
  confondant etait journalise et affiche dans la colonne d'a cote.
  Corrigee par normalisation sur les cases inconnues ; le signal survit
  (facteur 2,2, p = 0,0005). Sixieme metrique du projet a mesurer autre
  chose que ce qu'elle annonce -- d'ou l'invariant 7bis.
- **Mesure de profondeur vide.** Compter les passes d'une technique unique
  sature vers 2-3 pour tout, sudoku compris. La profondeur ne veut dire
  quelque chose que relativement a une hierarchie de techniques.

## Le motif qui revient : des metriques qui mesurent autre chose

**Six fois** le projet a produit un chiffre qui ne mesurait pas ce qu'il
annoncait :

1. **T1 faux** : remplissait la grille et se trompait de solution.
2. **Profondeur v1** : saturait vers 2-3 pour tout, sudoku compris.
3. **T2 sature** : 100 % contre 100 %, et le verdict automatique imprimait
   une refutation non etablie.
4. **T3 inerte** : correct, verifie, et jamais declenche.
5. **Effort confondu avec profondeur** : le nombre d'invocations mesure le
   caractere laborieux, pas la structure.
6. **Resistance a T0 confondue avec la densite d'indices** : le confondant
   etait dans la colonne voisine du meme tableau.

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

## Metrique principale : la resistance a T0

    resistance = t0_left / t0_unknown
               = cases restantes apres saturation de T0 SEULE
                 / cases inconnues du puzzle initial

Fraction du travail que la technique la plus faible ne fait pas. Adoptee le
26/08/2026 en remplacement de `max_level`, pour trois raisons :

1. **elle ne sature pas** -- `max_level >= 2` vaut 100 % partout ;
2. elle est significative aux deux domaines (d=3 : 39,2 % contre 18,1 %,
   p = 0,0005 ; d=4 : 40,4 % contre 23,2 %, p = 0,0005) ;
3. **elle ne depend d'aucune technique dont la disponibilite varie entre les
   groupes compares.** Point decisif : `max_level` est confondu a d=4, ou
   `static` dispose de T1 (34,4 % de regions eligibles) et `connect` jamais
   (0,0 %). Comparer deux groupes dont l'un a trois niveaux et l'autre deux
   n'a pas de sens. T0, lui, est disponible partout.

Normalisee sur les cases **inconnues**, jamais sur la grille : normaliser sur
la grille la rend confondue par la densite d'indices. Les journaux portent les
**deux bruts**, pas le ratio -- une normalisation peut changer, un ratio
journalise ne se recalcule pas.

`canary7` garde ses deux bornes : nulle quand T0 resout tout, strictement
positive sinon.

### CE QU'ELLE MESURE, ET CE QU'ELLE NE MESURE PAS

**La resistance a T0 mesure la NON-LOCALITE de la contrainte, pas la
PROFONDEUR de la deduction.** Ce sont deux choses differentes et les confondre
serait la septieme metrique du projet a mesurer autre chose que ce qu'elle
annonce.

Un systeme qui resiste a T0 et tombe **entierement** a T2 est **PLAT au sens du
projet** : il a demande une technique plus forte que la propagation locale, pas
une hierarchie de techniques. La resistance dit "la propagation locale ne suffit
pas ici", elle ne dit rien de la richesse de ce qu'il faut a la place.

**Ce qui est ACQUIS au 26/08/2026** : la connectivite produit des systemes que
la propagation locale ne resout pas. Etabli, teste, survivant a la candidature,
au verdict, au domaine, au nombre de grilles et a la densite d'indices.

**Ce que cela ne demontre PAS** : l'hypothese de fracture locale / non-locale.
Le resultat en est **coherent** -- c'est meme ce qu'elle predirait -- mais
coherence n'est pas demonstration. L'hypothese porte sur la PROFONDEUR des
systemes a connectivite, et la profondeur n'est pas ce qui a ete mesure.

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

**Enonce.** La ligne de fracture entre systemes plats et systemes profonds
n'est pas "quelles contraintes" mais **decomposable localement ou non**. La
connectivite (`Connected`) est le seul type non decomposable en contraintes
locales.

### Ce qui est ACQUIS

- **La connectivite produit des systemes que la propagation locale ne resout
  pas.** Resistance a T0 : `connect` 24,5 % contre `static` 8,9 % sur tous les
  systemes evaluables (p = 0,0005), 44,4 % contre 26,8 % sur les seuls
  candidats. Survit hors du filtre de candidature, a verdict egal, aux deux
  domaines, a `total_grids` et a `clue_frac` stratifie. Voir DECISIONS.md.
- **T0 resout integralement 60 a 92 % des instances a n=4** (60 % sur
  `connect` d=3, 92 % sur `static` d=3). Mesure, pas suppose.
- **T2 est sature** : 100 % des candidats l'atteignent, dans les deux groupes.
- **T1 n'a de domaine que sur les systemes portant un ALLDIFF de taille d**,
  donc jamais sur `connect,relational` qui n'en produit aucun.

### Ce qui n'est PAS acquis

- **L'hypothese elle-meme.** Elle porte sur la PROFONDEUR, et ce qui est mesure
  est la resistance a la propagation locale. Le resultat est **coherent avec**
  l'hypothese sans la demontrer.
- Aucune mesure de profondeur exploitable n'existe : `max_level` sature, et il
  n'y a pas de palier entre T0 et T2.

### Pourquoi n=4 ne peut PAS y repondre

**T0 resout integralement 60 a 92 % des instances.** Il ne reste en moyenne
que 0,3 a 4,1 cases apres la propagation la plus faible. Une hierarchie de
techniques n'a **structurellement pas la place** de se deployer sur ce residu :
seize cases se resolvent par la technique la plus faible, et aucune technique
intermediaire n'y changera rien.

Ce n'est pas un echec, c'est un **resultat** : la profondeur n'est pas
mesurable a n=4. Elle ne le deviendra qu'a n=5 ou n=6, ou le residu apres
propagation locale est assez grand pour qu'une hierarchie ait un sens.

Consequence directe sur l'ordre des travaux : **le debit redevient le
probleme**, et il le redevient avant la profondeur. Voir la priorite 1
ci-dessous.

## Prochaine tache, par priorite

L'ordre a change le 26/08/2026 : **A d'abord, n=5 ensuite.**

1. **Decider d'ouvrir A ou non** -- etat de candidats explicite dans `engine/`.
   Le perimetre exact, contrainte par contrainte, est dans `PERIMETRE-A.md`.
   C'est la seule voie connue vers une metrique de profondeur non saturee, et
   c'est aussi ce qui rend n=5 abordable.

2. **n=5 -- PAS ENCORE LANCABLE.** Le cout par systeme y explose, et la borne
   `--max-seconds` censurerait **exactement les systemes profonds**, c'est-a-dire
   ceux qu'on cherche. Lancer n=5 avant A produirait un echantillon tronque du
   cote qui compte. A d'abord.

3. Ne pas ajouter de technique de deduction avant A : sans etat de candidats,
   toute technique d'ELIMINATION est inerte (deux l'ont ete), et la seule
   famille de POSE au-dela de T2 a un cout multiplicatif.

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
