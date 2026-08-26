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

## A EST UN CHANTIER DE DEBIT

Le projet A -- la propagation sur domaines -- n'existe **pas** pour deduire
mieux. Il existe pour rendre **n=5 praticable sous la borne de 20 s**. Le
critere de succes est un **cout par systeme**, pas un taux de resolution.

Corollaire : ne pas brancher la propagation dans une hierarchie a n=4, ou T0
seul resout deja 60 a 92 % des instances. Affiner un instrument dans un regime
sature est le motif du projet applique au chantier lui-meme.

La mesure que le gel de `t0_legacy` rend possible :

    gain_propagation = (resistance_T0 - resistance_prop) / resistance_T0

L'hypothese predit un gain **faible** pour `connect`, **fort** pour `static` --
un systeme localement decomposable voit sa resistance recuperee par des
propagateurs locaux plus forts ; un systeme non decomposable, non, **par
definition**. C'est l'ecart entre les deux instruments qui est le signal, et il
n'a de sens que parce que **l'un des deux ne bouge jamais**.

## LE MOTIF DU PROJET — a lire avant les invariants, ils en decoulent

**Sept fois** dans ce projet, un instrument a mesure autre chose que ce qu'il
annoncait : quatre metriques, deux techniques de deduction inertes, un test
negatif vide.

**Aucune n'etait fausse au sens du code.** Chacune etait correcte, et sans
prise sur le regime ou elle servait. Le defaut ne se voit **jamais dans le
code** — seulement en confrontant l'instrument a ce qu'il pretend distinguer.

    Donc : avant d'adopter tout instrument — metrique, technique, canari,
    test — EXHIBER un cas qu'il classe positivement et un cas qu'il classe
    negativement. S'il n'y en a qu'un des deux, il ne mesure rien.

Les sept cas, pour que la liste ne se reconstitue pas de memoire :

1. **T1 faux** — remplissait la grille et se trompait de solution.
2. **Profondeur v1** — saturait vers 2-3 pour tout, sudoku compris.
3. **T2 sature** — 100 % contre 100 %, et le verdict automatique imprimait une
   refutation jamais etablie.
4. **T3 paire nue, inerte** — correcte, verifiee, jamais declenchee.
5. **T3 paire cachee, inerte** — meme cause structurelle, seconde tentative.
6. **Resistance a T0 confondue** — par la densite d'indices, confondant
   journalise et affiche dans la colonne d'a cote.
7. **Test negatif de `canary8` vide** — il renforcait T0 avec **T1**, qui est
   un no-op dans cet espace. Zero divergence detectee : le test ne prouvait
   rien tout en ayant l'air de conclure.
8. **Echantillon de `canary3` aligne sur l'enumeration** -- les sept
   croisements de `NoTriple` rendaient **zero violation** sous un bug reel.
   Cause : `sols[:k]` sur une enumeration **lexicographique** n'est pas un
   echantillon, c'est un **coin** de l'espace -- toutes les grilles retenues
   partagent les memes petites valeurs en tete. Sur un tirage **aleatoire de
   meme taille**, le meme bug produit des centaines de violations.

Le septieme et le huitieme sont les plus instructifs, et le huitieme est d'un
cran au-dessus de tous les autres :

    le septieme faussait un TEST. Le huitieme faussait la MESURE DE
    COUVERTURE des tests -- il ne disait pas une chose fausse sur le moteur,
    il disait une chose fausse sur ce que les canaris verifiaient.

**LE MOTIF S'APPLIQUE RECURSIVEMENT.** Chaque etage de verification est
lui-meme un instrument, et justiciable de la meme regle que ce qu'il verifie :
la metrique, puis le canari qui la garde, puis le test negatif qui garde le
canari, puis l'echantillon sur lequel ce test porte. **Aucun etage n'est
exempt du fait d'etre un etage de controle** -- au contraire, plus un
dispositif est en amont, moins sa defaillance est visible, parce que tout ce
qui est en aval continue d'imprimer des resultats d'apparence normale.

Le huitieme a de plus ete introduit **dans le commit meme qui ajoutait la
couverture qu'il annulait**. Un test negatif qui ne teste rien est une metrique
confondue a l'etage du meta-outillage. Rien ne protege automatiquement de ce
motif, pas meme les regles ecrites pour s'en proteger.

**Les septieme et huitieme cas ont ete trouves par Claude Code, sans que
l'utilisateur le demande.** C'est le **mode de travail attendu**, pas une exception : signaler
ce qui contredit l'hypothese ou rend une mesure douteuse fait partie de la
tache, meme hors de ce qui a ete demande. La moitie des cas de cette liste ont
ete identifies ainsi.

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
10. **Certaines duplications sont DELIBEREES. Ne jamais les factoriser.**
   `engine/t0_legacy.py` duplique `candidates` et `apply_T0` depuis
   `deduction.py`, et les deux copies vont **diverger volontairement** : l'une
   est l'instrument de mesure gele, l'autre le moteur qui evolue. Les
   factoriser detruirait le gel **sans que rien ne plante** -- `canary8`
   crierait, et la tentation serait de regenerer son corpus.
   Meme regle a venir pour `feasible()` et `propagate()` : la duplication de la
   logique de chaque contrainte est le **prix de l'independance de l'oracle**,
   pas une dette technique.
   Regle generale : **une duplication documentee comme deliberee est un
   invariant, pas un defaut.** Avant de factoriser deux fonctions semblables
   dans `engine/`, verifier qu'aucune n'est declaree gelee.

14ter. **Le critere de surete n'est pas la forme de l'objet, c'est la
   SUR-APPROXIMATION.**
   Une inference est sure si elle n'utilise les domaines **que comme
   sur-approximation des valeurs possibles** -- autrement dit si elle est
   valide dans la relaxation « chaque cellule peut prendre n'importe quelle
   valeur de son domaine ». Rien d'autre n'est requis.
   **L'invariant 14 en est le cas particulier** : lire la FORME d'un domaine,
   c'est affirmer sur son contenu quelque chose de **plus fort** que
   `sigma[i] dans dom[i]`. D'ou l'unsoundness.
   **Un objet INDUIT n'est pas dangereux en soi.** S'il est construit par
   APPARTENANCE, toute conclusion valide dans la relaxation vaut pour toutes
   les solutions. La monotonie est une condition **suffisante et non
   necessaire** -- utile pour la confluence, pas pour la surete.
   Trois issues, donc, et non deux : **FIXE**, **INDUIT-PROUVE**,
   **INDUIT-SANS-PREUVE**. Seule la troisieme interdit, et elle interdit
   parce que la preuve n'a pas ete ecrite -- pas parce que l'objet est
   induit.

17. **14bis se VERIFIE mecaniquement, il ne se presume pas.**
   Chaque propagateur declare dans `objet_inference()` l'objet qu'il
   parcourt. `canary3` verifie que cet objet est **identique avant et apres
   des rognages arbitraires** des domaines.
   Objet **FIXE** -> l'invariant 14 s'applique tel quel. Objet **INDUIT** ->
   14bis est engage et doit etre **tranche avant** d'adopter le propagateur.
   Les neuf propagateurs actuels sont tous FIXES. **Le test est ecrit pour
   ECHOUER sur `Connected`**, dont le graphe des cases passables depend des
   domaines : c'est ainsi qu'on saura que 14bis est engage, au lieu de le
   decouvrir apres coup.
   Un propagateur qui ne declare aucun objet fait echouer le canari : on ne
   peut pas ne pas repondre a la question.

18. **Quand le temoin disjoint est impossible, le controle devient : le meme
   systeme, l'autre propagateur DESACTIVE.**
   `NoSquare` couvre toute la grille, donc aucune contrainte ne peut lui
   etre disjointe -- et `Connected` aura la meme propriete. Le controle par
   geometrie est alors remplace par un controle **strictement plus fort** :
   les deux mondes ont **exactement le meme ensemble de solutions**, seule
   change la capacite de l'autre propagateur a rogner. Si le bug ne mord que
   lorsque l'autre propagateur tourne, l'interaction est demontree sans
   dependre d'une geometrie.

16. **Une coincidence entre verifications INDEPENDANTES est un defaut commun,
   pas un fait.**
   Quand plusieurs verifications independantes rendent **le meme verdict
   simultanement**, suspecter le **dispositif partage** avant de croire au
   verdict.
   C'est un raisonnement sur la **STRUCTURE du resultat**, pas sur son
   contenu, et il ne demande de comprendre aucun des cas : sept croisements
   independants ne deviennent pas tous inertes en meme temps, donc la cause
   est **commune**, donc elle est **en amont des sept** -- dans ce qu'ils
   partagent, pas dans ce qui les distingue.
   C'est ce qui a evite de conclure a sept propagateurs inertes le
   26/08/2026, alors que le defaut etait dans l'echantillonnage (cas 8).
   Procedure : **diagnostiquer separement avant toute correction.** Un
   diagnostic qui cherche exhaustivement une configuration declenchante
   tranche entre les deux lectures en une execution.

15. **Un PREFIXE d'enumeration n'est jamais un echantillon.**
   `toutes_solutions` enumere dans l'ordre lexicographique. `sols[:k]` retient
   donc des grilles qui partagent toutes les memes petites valeurs en tete :
   un **coin** de l'espace, pas l'espace. Utiliser `echantillon()`, tirage
   aleatoire a graine fixe -- reproductible, et **non aligne sur l'ordre
   d'enumeration**.
   Corollaire general : **quand une couverture est reduite, verifier que la
   reduction est independante de l'ordre dans lequel les cas ont ete
   produits.** Une troncature suit toujours l'ordre du generateur, et l'ordre
   du generateur est structure.
   Et quand un croisement rend zero, **distinguer bug inerte de couverture
   aveugle avant de conclure** : les deux impriment exactement la meme ligne.

14. **La classe des bugs d'interaction est CERNEE : deduire le CONTENU d'un
   domaine de sa FORME.**
   Tout ce qui repose sur une lecture **perimee** est structurellement inerte :
   les domaines ne font que **retrecir**, donc une lecture perimee donne
   toujours un propagateur plus **faible**, jamais plus zele. Deduction
   manquee, pas solution fausse.
   Ce qui rend un propagateur **trop zele** par interaction, c'est de croire un
   domaine plus PETIT qu'il n'est. Or un propagateur ne peut pas lire l'avenir
   -- il ne peut y arriver qu'en **inferant le contenu depuis la forme** :
   « domaine plein ou singleton », « domaine deja rogne = cellule decidee ».
   Vrai dans le monde du forward-checking d'ou l'on vient, **faux** des qu'un
   autre propagateur a rogne PARTIELLEMENT une cellule partagee.
   C'est le gabarit du test negatif de chaque croisement.
   **ET C'EST D'ABORD UN CRITERE DE RELECTURE, PAS DE TEST.** Tout propagateur
   s'audite **avant d'ecrire la moindre ligne de test** : chercher chaque
   endroit ou il teste une propriete de **forme** d'un domaine --
   `len(dom) == 1`, `len(dom) == d`, `len(dom) > 1`, « intact », « deja
   rogne » -- plutot que l'**appartenance** d'une valeur. Chaque occurrence est
   un point d'unsoundness potentiel par interaction.
   Un propagateur qui ne raisonne que sur `v in dom[i]`, `min(dom[i])`,
   `max(dom[i])` est **sur par construction** vis-a-vis des interactions : ces
   lectures portent sur le contenu, et le contenu ne fait que retrecir.
   **Seule forme admise : `len(dom) == 1`**, et uniquement parce qu'elle
   **determine** le contenu exactement -- un singleton a un unique membre,
   qu'on lit ensuite. Toute autre taille est un **proxy** du contenu, et un
   proxy est faux des qu'un autre propagateur a rogne partiellement la cellule.
   Le critere est ecrit en tete de `engine/propagate.py`, la ou on le relit.

13. **Chaque propagateur ajoute un CROISEMENT contre TOUS les precedents.**
   Les cas limites sont construits a la main (invariant 8), mais leurs
   **croisements** venaient du generateur, qui n'assemble que les paires que
   les familles du DSL produisent naturellement. Dix propagateurs = 45 paires ;
   le generateur n'en couvrira qu'une fraction. C'est la faiblesse de
   couverture payee avec T1.
   Donc : pour chaque paire de propagateurs branches, un systeme portant les
   deux contraintes dans leur configuration limite respective, **sur des
   regions qui SE CHEVAUCHENT**.
   **Le chevauchement est le mecanisme, pas le decor** : deux propagateurs sur
   des regions disjointes ne peuvent pas interagir. Chaque croisement porte
   donc un **temoin disjoint** qui doit rester **muet** la ou le croisement
   chevauchant crie -- sinon le bug injecte est un bug simple et le croisement
   ne prouve rien.
   Le test negatif d'un croisement doit etre un bug **d'interaction**, jamais
   la reinjection d'un bug simple.
   **Le chevauchement doit porter sur LA cellule que l'inference injectee
   LIT.** Trois croisements ont echoue avant d'etre corriges, chaque fois pour
   la meme raison sous un habit different : partager une cellule ne suffit pas,
   il faut que l'autre propagateur puisse effectivement la **rogner**, et qu'il
   rogne **celle-la** et pas une voisine.
   - `X1` : avec `lo == 0` le forcage de Count ne se declenche jamais.
   - `Count x SumRange` : avec `hi == |R|` l'interdiction ne peut rien retirer
     dans sa propre region.
   - `Count/SumRange x Mono` : l'autre propagateur rognait le `a` de la paire
     alors que le bug lit le `b`. Corrige en inversant l'ordre de la region.
   - `Mono x PairRatio` : la cellule partagee etait bien rognee, mais **du
     mauvais cote**. `Mono([0, 1])` ne peut que RELEVER le plancher, et le
     domaine partiel obtenu ne trompait pas l'inference injectee ; il fallait
     `Mono([1, 0])`, qui ABAISSE le plafond.
   Enonce complet, apres quatre echecs : il faut que l'autre propagateur
   puisse produire **le domaine partiel PARTICULIER que l'inference injectee
   lit de travers** -- pas seulement rogner, pas seulement rogner la bonne
   cellule.
   Un croisement qui ne peut rien declencher est un canari vide de plus.
   Cout quadratique, **assume** : c'est la seule couverture qui ne depende pas
   du generateur.

12. **`dsl_hash` ne se relache jamais. Le regroupement est une LECTURE.**
   Le hash porte sur tout `engine/`, y compris des modules inertes : pendant A
   chaque propagateur rompt la serie sans rien changer au comportement. On ne
   corrige PAS le hash pour autant -- un hash qui rate un changement est
   catastrophique, un hash qui en signale un inoffensif coute une rupture.
   L'attenuation est **a cote** : `engine_active_hash` (hash du **contenu** des
   modules reellement sur le chemin d'execution) permet a `summarize.py` de
   proposer un regroupement, **en le disant a chaque fois**. Jamais de
   regroupement sur la liste de **noms** : deux series peuvent declarer les
   memes modules avec du code different.
   `ENGINE_ACTIVE` dans `run.py` est **tenue a la main**. Y ajouter un module
   non branche est un mensonge journalise.

11. **`canary3` GROSSIT a chaque propagateur. Jamais de canari separe.**
   Ce que `canary3` verifie -- la deduction retrouve EXACTEMENT la solution
   d'origine -- est une propriete du **systeme de deduction entier**, pas de
   chaque technique isolee. Un propagateur AllDiff correct et un propagateur
   Count correct peuvent, **ensemble**, retirer un candidat de trop :
   **l'erreur nait de l'interaction**, et un canari par propagateur ne la
   verrait jamais.
   Chaque ajout tourne donc avec **tous les precedents actifs**. Le cout monte,
   c'est voulu : c'est la combinatoire qu'on veut couvrir.
   Deux consequences :
   - l'ordre d'ajout des propagateurs n'est pas seulement une progression de
     difficulte, c'est un **ordre de validation incrementale**. Un `canary3`
     rouge au sixieme propagateur peut accuser le sixieme **comme n'importe
     quel couple anterieur** ;
   - s'il devient trop lent pour tourner a chaque run, on le sortira de
     `run_canaries()` vers un **pre-commit**. On ne reduira **jamais** sa
     couverture pour gagner du temps.

8. **Tout canari de correction construit ses cas limites A LA MAIN.** Le
   generateur sert a couvrir le cas ordinaire, **jamais les bords**. Un canari
   qui attend ses cas du generateur ne teste que ce que le generateur produit
   -- deja paye avec T1 : code correct, zero invocation sur 8991 systemes,
   parce que l'espace genere ne contenait aucun ALLDIFF de taille d.
9. **Un canari doit avoir ete VU ECHOUER au moins une fois.** Le test negatif
   est la norme, pas l'exception : on construit deliberement le defaut qu'il
   doit attraper et on verifie qu'il l'attrape. Un canari jamais vu rouge est
   une decoration. *(Verifie pour canary5, canary6, canary7, canary8.)*
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

## Chantier A : la force du propagateur Connected est un choix, pas un maximum

A est OUVERT (26/08/2026). Perimetre dans `PERIMETRE-A.md`, decisions dans
`DECISIONS.md`.

Un point a ne pas perdre en route : **la force du propagateur `Connected`
definit la frontiere entre ce que le moteur traite comme local et ce qu'il ne
peut pas decomposer.** Un `Connected` trop bien propage rendrait le moteur
incapable d'observer la non-localite qu'il etudie -- meme piege que le T0
renforce, un etage plus haut.

Dissymetrie qui rend la chose vivable : les sept propagateurs faciles portent
des contraintes **decomposables par nature** et peuvent etre aussi forts qu'on
veut. C'est le CONTRASTE entre eux et `Connected` qui produit le signal ;
renforcer les locaux l'augmente meme.

A relire integralement avant d'ecrire le propagateur `Connected` (etape 5).

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
