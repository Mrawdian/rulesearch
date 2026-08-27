# WORKLOG — rulesearch

Journal des interventions faites **sur le serveur** (`rulesearch@77.42.21.130`,
depot `/home/rulesearch/rulesearch`).

Ce fichier existe parce que Claude en chat n a **aucun acces** au serveur ni au
depot : c est son seul canal d information. Chaque entree doit donc se lire
seule, sans contexte exterieur.

Entree la plus recente **en haut**.

---

## 2026-08-27 - LE VRAI LIVRABLE N'EST PAS r, C'EST CE QUI PERMET DE CROIRE r

**Verdict du controle de circularite : elle tombe. `r = 0,034`, contre une
borne pre-inscrite a 0,194.** Le detail est dans DECISIONS.md ; ceci est la
note qui se perdrait sinon.

**CE RESULTAT A ETE ETABLI CONTRE DOUZE INSTRUMENTS DEMASQUES EN CHEMIN.** Non
pas malgre eux : contre eux. Chacun rendait des chiffres d'apparence normale.

Les dix premiers sont en tete de CLAUDE.md. Les deux derniers sont du 27/08 :

    11. Le garde d'echantillonnage du `gain_propagation` tirait un PREFIXE --
        l'invariant 15, ecrit le matin meme, viole dans le dispositif charge
        de l'appliquer. Il avait conclu « les deux resistances coincident
        PARTOUT » sur un coin de l'espace.
    12. Un test negatif de l'articulation rendait 0 violation. Non parce que
        son bug etait sur : parce qu'il etait INERTE -- la grille 3x3 pleine
        est 2-connexe, donc sans sommet separateur. UN TEST NEGATIF DONT LE
        BUG NE SE DECLENCHE PAS NE TESTE RIEN, IL RASSURE.

**Plusieurs de ces douze avaient ete ecrits pour prevenir les precedents.** Le
motif s'applique recursivement, et c'est la sa lecon la plus couteuse.

**LA CHAINE DE CONTROLE EST CE QUE CES DOUZE ECHECS ONT COUTE A CONSTRUIRE** :
pre-inscription d'un seuil derive de valeurs deja publiees ; verification que
ce seuil ne bouge pas quand la population double ; controles bloquants lus
AVANT le chiffre et dans un ordre fixe d'avance ; tirage aleatoire partout ;
bruts imprimes a cote de chaque agrege pour refaire le rapport a la main ;
tests negatifs vus mordre ; deux issues ecrites avant la mesure, dont aucune
n'etait l'issue esperee.

**Aucune de ces regles n'a ete deduite. Chacune a ete payee.**

Le chiffre `0,034` vaudra ce que vaudra la confiance qu'on peut lui accorder
dans six mois, hors de cette session. C'est le dispositif qui la porte, pas le
chiffre.

## PROTOCOLE : lancer une mesure longue sur le serveur

**Trois coupures SSH ont tue trois lancements le 27/08**, dont un diagnostic a
dix minutes de son terme. La cause n'est pas la coupure -- elle se reproduira
-- mais le fait que le processus soit rattache a la session.

    setsid nohup python3 -u <script> > <journal> 2>&1 < /dev/null &

Chaque morceau porte : `setsid` detache du groupe de processus (c'est LUI qui
manque a `nohup` seul, verifie le 27/08 : un `nohup ... &` a quand meme ete
tue), `-u` rend la sortie lisible pendant l'execution, `< /dev/null` evite le
blocage sur stdin.

**Ne jamais lire un resultat a travers `| tail`** : le tube bufferise tout
jusqu'a la fin, donc aucun progres n'est visible et une coupure fait tout
perdre. Ecrire dans un journal, lire le journal.

**Pour une sequence, un script `sh` detache une seule fois**, chaque etape
ecrivant son propre journal. Verifie le 27/08 : la coupure a tue l'enveloppe
SSH, la sequence est allee au bout de ses quatre etapes.

## 2026-08-27 - gain_propagation MESURE : la fracture est portee par Connected

**La prediction, poussee avant la mesure, est confirmee. Le controle decisif
isole `Connected`. Une reserve de circularite est signalee.**

    static-ref               gain 0,557 agrege / 0,699 moyen   (n=9258)
    connect                  gain 0,260 / 0,237                (n=12015)
    ecart                    p = 0,0005

    CONTROLE INTRA-TAG :
    connect SANS Connected   T0=47760   prop=0        gain 1,000
    connect AVEC Connected   T0=299562  prop=250801   gain 0,158
                             p = 0,0005

Meme tag, meme generateur : la composition ne peut pas expliquer l'ecart. Les
systemes sans `Connected` sont **relationnels purs, verifie et non suppose**.

**LA PROPAGATION LOCALE RECUPERE INTEGRALEMENT LA RESISTANCE DES SYSTEMES
RELATIONNELS PURS, ET 16 % DE CELLE DES SYSTEMES A CONNECTIVITE.**

**LE GARDE 1 A MORDU DEUX FOIS, CONTRE MES PROPRES INSTRUMENTS** :
1. domaines initialises PLEINS au lieu du forward-checking gele -- l'instrument
   ne testait pas ce que l'hypothese dit. Corrige.
2. **l'echantillon du garde etait un PREFIXE** : invariant 15, que j'ai ecrit
   ce matin, viole dans le dispositif charge de l'appliquer. Onzieme occurrence
   du motif, quatrieme dans un instrument ecrit pour prevenir les precedents.
   Le garde avait conclu « les deux resistances coincident PARTOUT » sur un
   coin de l'espace.

**LE PLAFOND EST VERIFIE** : `gain = 1,000` sur 28539 instances est un
indicateur sature. 200 grilles pleines sur 200, **0 fausse**. Reel, pas un bug.
Consequence : la comparaison `static` vs `connect-sans-Connected` est une
comparaison AU PLAFOND et **ma lecture annoncee avant la mesure etait invalide
dans sa forme**. Le contraste qui tient est l'intra-tag.

**Confondant `clue_frac` ecarte** : dans chaque tercile, le groupe a
`Connected` reste tres en dessous des deux autres.

**RESERVE NON DEMANDEE, ET C'EST LA PLUS IMPORTANTE** : le resultat est
partiellement **circulaire**. L'articulation a ete ecartee parce qu'on
s'attendait a ce qu'elle dissolve la difficulte ; on mesure ensuite que la
difficulte n'est pas dissoute par les regles faibles. Le controle intra-tag
ecarte la composition, **pas la force du propagateur**.

L'enonce que la mesure autorise : **`Connected` resiste aux propagateurs locaux
QUE NOUS AVONS CHOISI D'ECRIRE**, et ce choix a ete informe par l'attente qu'il
resiste.

**Non explique** : non-monotonie du gain avec `Connected` selon `clue_frac` --
0,196 / 0,062 / 0,268. Residu.

**Non fait** : la file lente a n=5. Elle n'etait justifiee que si le gain
discrimine ; il discrimine. **La decision de la lancer n'est pas prise ici.**

## 2026-08-26 - gain_propagation : prediction posee, mesure pas encore lancee

**Aucun resultat. Ce commit n'existe que pour horodater la prediction.**

L'hypothese centrale n'exigeait pas n=5 -- c'est la PROFONDEUR qui l'exigeait.
La decomposabilite locale se teste par la **recuperation** : des propagateurs
locaux plus forts recuperent la resistance d'un systeme decomposable, pas
celle d'un systeme qui ne l'est pas. **A a livre cet instrument sans le
viser.**

**PREDICTION** : gain **FORT** sur `static-ref`, **FAIBLE** sur `connect`.
La faiblesse relative de `Connected` est le **signal attendu**, pas un defaut.

**Trois gardes** : canari de non-redondance d'abord (et garde de saturation) ;
la prediction etant directionnelle et ecrite, un resultat qui la confirme
recevra le controle qu'aurait recu son contraire -- c'est le regime du dixieme
cas ; aucun branchement en production.

**Non etabli** : tout. Rien n'a encore tourne.

## 2026-08-26 - CLOTURE DE A : ce qui est etabli, ce qui ne l'est pas

**Aucun code. Verdict, et etat des lieux.**

## VERDICT

**La propagation sur domaines ne produit aucun gain de debit. n=5 ne passe pas
sous la borne de 20 s. A a echoue sur ce qu'il visait.**

    125 instances comparables : x0,99      decile le plus couteux : x0,90
    systemes rendus mesurables: 1 sur 132  aucune ne finit        : 6
    solutions fausses         : 0          deduction perdue       : 0

Enonce sans attenuation : le volume de travail -- dix propagateurs, 45
croisements, onze invariants -- rend la nuance trop facile, et le volume n'est
pas de l'avancement.

## ETABLI

- **`feasible()` est conservee pendant tout A**, et c'est verifiable
  mecaniquement : diff **vide** sur `rulesearch.py`, `dsl2.py`, `deduction.py`
  et `t0_legacy.py` entre `3cde7b2` et la cloture. Aucune revue n'est requise.
- **Dix propagateurs corrects**, chacun avec ses cas limites construits a la
  main, son test negatif vu mordre, et ses croisements contre tous les
  precedents. **0 solution fausse** sur toutes les mesures de la journee.
- **La classe des bugs d'interaction est cernee** (invariant 14) : deduire le
  CONTENU d'un domaine de sa FORME. Toute lecture perimee est inerte par
  monotonie. Le critere s'audite **par relecture**, avant tout test.
- **Le vrai critere de surete est la SUR-APPROXIMATION** (14ter) : 14 en est le
  cas particulier ; un objet INDUIT n'est pas dangereux s'il est construit par
  appartenance. Verifie **mecaniquement** sur les dix propagateurs.
- **Le retrait par inaccessibilite est sur**, preuve ecrite avant le code.
  **Le forcage par point d'articulation est sur ET monotone** aussi -- l'objet
  pertinent est l'ensemble des sommets separateurs `a`-`b`, pas l'ensemble des
  points d'articulation d'un graphe quelconque.
- **A cout egal, la propagation deduit davantage** : 11 instances resolues par
  elle seule, 63 `max_level` abaisses, 0 perdue. Second instrument du
  `gain_propagation`, **mesure et non branche**.
- **Ou part le budget a n=5** : 97 % dans `solve_graded`, sur les systemes qui
  atteignent la borne.

## NON ETABLI

- **Que n=5 soit atteignable par une quelconque voie.** A etait la voie
  identifiee ; elle ne donne rien. Aucune autre n'a ete mesuree.
- **L'origine du residu** : 1 divergence de `max_level` plus haute sur 132,
  population entierement couverte. Pas une unsoundness. **Volontairement non
  explique.**
- **La generalite des chiffres** : un seul tirage (graine 5), 30 systemes, une
  famille, une taille. Rien n'a ete replique.
- **Le gain de qualite en production** : jamais observe, `propagate.py` n'a
  jamais tourne en production. `engine_active_hash` est reste `0caa9267db60`
  d'un bout a l'autre de A.

## CE QUI A FAILLI ETRE RAPPORTE COMME UN RESULTAT

**x3,99.** Le prototype remplacait la saturation par la propagation : il
perdait les detections de contradiction que les propagateurs omettent
deliberement. En filtre devant la saturation : **x0,99**, 0 perdue.

**C'est le dixieme cas du motif, et le plus important** : la mesure fausse
allait dans le SENS ESPERE, sur le CRITERE DE SUCCES du chantier. Les neuf
autres contredisaient une attente ou etaient neutres.

    UN RESULTAT FAVORABLE MERITE LE MEME CONTROLE QU'UN RESULTAT
    DEFAVORABLE, ET IL LE RECOIT MOINS SOUVENT.

Trois des dix instruments demasques aujourd'hui avaient ete ecrits pour
prevenir les precedents.

## DECISIONS PRISES ET NON PRISES

- **L'articulation ne sera PAS ouverte.** Son critere de reouverture etait
  atteint formellement, mais **mal concu** : il devait constater un debit
  insuffisant, pas ouvrir une piste que les mesures rendent invraisemblable.
  Un seuil d'insatisfaction n'est pas une hypothese.
- **Le gain de qualite n'est PAS branche** : il deplacerait la frontiere
  mesuree.
- **Rien d'autre n'a ete decide ce soir.**

## POUR CLAUDE CHAT

Le prochain mouvement **n'est pas technique**. Si A ne debloque pas n=5, la
voie vers la profondeur mesurable n'existe plus dans sa forme actuelle : c'est
une **question de recherche**, reprise par l'utilisateur avec Mrawdian.

Ne pas proposer de renforcer les propagateurs pour recuperer le facteur : il
n'est present nulle part, ni sur la population couverte, ni sur le decile le
plus couteux, ni sur les instances qui atteignent la borne.

## 2026-08-26 - Connected, dixieme propagateur -- ET A NE REMPLIT PAS SON CRITERE

**Ordre impose et respecte** : preuve ecrite avant le code, `canary3` etendu et
croisements avant le propagateur, puis mesure de debit immediatement apres.

**Le propagateur** : inaccessibilite depuis une ancre CERTAINE + detection de
contradiction. Rien d'autre. Piege = la condition d'amorcage `|F| >= 1` ; test
negatif = ancre prise parmi les POSSIBLES, 2 / 5 / 8 violations.
Neuf croisements, **45 paires**, `canary3` a **15,4 s**.

**LE VERDICT, prototype EQUIVALENT EN DEDUCTION :**

    125 instances comparables : x0,99      decile le plus couteux : x0,90
    systemes rendus mesurables: 1 sur 132  aucune ne finit        : 6
    solutions fausses         : 0

**A ne remplit pas son critere de succes. Il n'y a pas de gain de debit.**

**LE x3,99 PRECEDENT ETAIT DE LA DEDUCTION ABANDONNEE.** Mon prototype
**remplacait** la saturation par la propagation -- il perdait donc exactement
les detections de contradiction que les propagateurs omettent deliberement,
`feasible()` etant l'oracle. 18 deductions perdues, 33 `max_level` plus hauts
sur population entierement couverte. **C'est le garde impose par l'utilisateur
qui l'a fait voir.** Corrige en FILTRE devant la saturation : 0 perdue, et le
gain disparait. **Invariant 21.**

**CE QUE A A PRODUIT, ET QUI N'EST PAS DU DEBIT** : le prototype deduit plus a
cout egal -- 11 instances resolues par lui seul, 63 `max_level` abaisses, 0
perdue. Gain de QUALITE, pas de debit. Ce n'est pas ce que A visait.

**Le critere de reouverture de l'articulation, fixe a l'avance, est ATTEINT.**
La preuve de surete est deja faite (14ter). La decision n'est pas prise ici.

**Non verifie / suppose** :
- Un seul tirage (graine 5), 30 systemes, une famille.
- **1 `max_level` plus haut** non explique, sur population couverte. Le filtre
  garantit « egal ou plus fort » sur les retraits, mais la propagation initiale
  change l'ORDRE d'examen de T2. 0 deduction perdue, 0 solution fausse.
- `propagate.py` n'est **toujours pas branche** en production.

**Bloque sur** : rien.

## 2026-08-26 - MESURE DE DEBIT : A vise le bon endroit, et Connected decide

**Demande** : mesurer le cout par systeme a n=5, avec et sans propagation ;
puis, avant toute conclusion, la ventilation par phase avec le moteur seul --
la propagation n'accelerant que `solve_graded`.

**LE CHIFFRE** (n=5, `connect`, 30 systemes, borne 20 s, moteur seul) :

    BUDGET REEL   solve_graded  100,20 s  96,8 %   <-- 5 systemes coupes
                  random_solution 2,41 s   2,3 %
                  minimal_clues   0,70 s   0,7 %

**`solve_graded` porte 97 % du budget : A vise le bon endroit.**

**LE NEUVIEME CAS S'EST REPETE DANS LE BANC ECRIT POUR L'EVITER.** Le banc
calculait sa repartition sur les systemes **TERMINES seuls** et concluait
« solve_graded ne represente que 6 % » -- l'inverse de la verite. Un systeme
interrompu consomme la borne **entiere**, dans la phase ou il a ete coupe.
Et le banc imprimait juste en dessous l'avertissement qui aurait du l'empecher.
**Ecrire la mise en garde ne suffit pas : c'est le chiffre MIS EN AVANT qui
doit porter sur la bonne population.**

**CE QUE LES DEUX MESURES POINTENT, ET C'EST LE MEME ENDROIT** : les 5 systemes
qui brulent le budget sont tous des `CONNECTED` ; les 3 systemes que le
prototype « debloque » aussi -- debloques parce qu'il **ne voit pas** la
contrainte. Sur la population **couverte**, le prototype est **plus lent**
(x0,43) et ne perd aucune deduction.

**`Connected` n'est pas le dernier propagateur : c'est le seul qui puisse
valider A.** Les neuf autres sont la condition d'existence de celui-la.

**CORRECTION D'UNE FORMULATION TROP FAVORABLE** : « tout gain sur `connect` est
un minorant » supposait un prototype equivalent plus rapide. Il est
**strictement plus faible** -- il ignore `Connected`. Le rapport n'est pas
conservateur, il est **CONFONDU**. 27 instances sur 63 ou la base resout et pas
le prototype ; 2 `max_level` plus hauts.

**Controles bloquants, tous negatifs** : **0 solution fausse** sur les deux
implementations, et 25 divergences de niveau sur 27 vers le **bas** (attendu).

**Fait** : `bench/bench_debit.py`, `bench/bench_deduction.py`,
`bench/bench_phases.py`. Hors `engine/` : `dsl_hash` inchange.
Bornes SIGALRM identiques a la production, appliquees **separement aux deux
implementations** ; quatre issues par instance ; populations couverte et
confondue separees ; sens des divergences affiche a chaque execution.

**Non verifie / suppose** :
- **Que `Connected` propage assez pour faire passer ces 5 systemes sous 20 s.**
  Rien ne le garantit, et la regle la plus forte a ete ecartee. **Premiere
  mesure a refaire apres l'etape 10.**
- Les mesures sont a n=5 sur un seul tirage de 30 systemes.
- Le prototype de `bench_deduction` n'est PAS le moteur : il sert a decider si
  le branchement vaut la peine.

**Bloque sur** : rien.

## 2026-08-26 - 14ter : la preuve tient, le critere propose non

**Demande** : prouver ou refuter la surete du retrait par inaccessibilite sur
objet induit, AVANT toute ligne de `Connected`.

**LA CONCLUSION DEMANDEE EST VRAIE** : le retrait par inaccessibilite est sur.
Toute solution `sigma` a son ensemble de cellules `val` inclus dans `P` et
connexe ; si `s` est certainement `val`, une cellule inaccessible depuis `s`
dans `P` ne peut pas etre `val`. **Condition d'amorcage : `|F| >= 1`** -- sans
ancre, aucun retrait n'est justifie.

**MAIS LA PREMISSE SUR L'ARTICULATION EST FAUSSE, et je le signale parce
qu'elle changeait une decision.** Le forcage par point d'articulation est
**sur** (meme argument) **et monotone**. L'intuition « les points
d'articulation ne sont pas monotones » vaut pour l'ensemble des points
d'articulation d'un graphe quelconque ; l'objet ici est **l'ensemble des
sommets par lesquels passe TOUT chemin a-b**, et supprimer des sommets ne cree
jamais de chemin, donc cet ensemble ne peut que **croitre**.

**Verifie empiriquement AVANT d'etre ecrit** : 1675 tirages de graphes-grilles
4x4 avec suppressions aleatoires, **zero contre-exemple** pour les deux regles.

**LE BON CRITERE (14ter)** : une inference est sure si elle n'utilise les
domaines **que comme sur-approximation des valeurs possibles**. 14 en est le
cas particulier. **Etre induit n'est pas etre dangereux** si l'objet est
construit par appartenance. La monotonie sert a la **confluence** -- donc a ce
que la metrique soit bien definie independamment de l'ordre -- **pas a la
surete**.

**CONSEQUENCE** : l'exclusion de l'articulation avait deux motifs ; le second
(14bis) s'evapore. Le premier tient entier et suffit -- un `Connected` trop
fort dissoudrait localement la difficulte mesuree. **L'exclusion est maintenue
mais repose sur un seul motif, de conception d'experience et non de
correction.** Il n'y aura plus de preuve a produire si elle est rouverte.

**Fait** : `statut_objet()` rend **trois** issues -- FIXE, INDUIT-PROUVE,
INDUIT-SANS-PREUVE -- et `SURETE_OBJET_INDUIT` nomme **les regles couvertes**,
pas seulement la contrainte : une regle non nommee n'est pas couverte, meme sur
la meme contrainte. `canary3` verifie en plus que **les trois issues sont
atteignables** (invariant 9 : un chemin jamais execute n'est pas un chemin).

**Verifie** : les neuf propagateurs sont FIXE, `Connected` sort
**INDUIT-PROUVE**, et la troisieme issue est atteinte sur un `kind` fictif.

**CE QUE « INDUIT » COUTE REELLEMENT** : ni la surete ni la confluence, mais
**l'incrementalite** -- l'objet doit etre reconstruit a chaque changement de
domaine. **Pour un chantier de debit c'est le seul cout qui compte.**

**Bloque sur** : rien.

## 2026-08-26 - NoSquare, neuvieme propagateur : 36 croisements, 14bis verifie

**Fait** : `propager_nosquare` -- dans une fenetre 2x2, si trois cellules sont
au singleton `{val}`, la quatrieme ne peut pas valoir `val`. Les fenetres sont
construites **dans le propagateur** a partir de `cn.n` : **`dsl2.py` n'est pas
touche**. Huit croisements de plus : **trente-six paires**.

**14BIS VERIFIE MECANIQUEMENT SUR LES NEUF PROPAGATEURS.** Plutot qu'argumenter,
chaque propagateur declare dans `objet_inference()` l'objet qu'il parcourt, et
`canary3` verifie qu'il est **identique avant et apres des rognages
arbitraires**. Les neuf sont **FIXES** : 14 suffit, 14bis n'est pas engage.
**Le test est ecrit pour ECHOUER sur `Connected`**, dont le graphe depend des
domaines -- on saura que 14bis est engage au lieu de le decouvrir apres coup.

**LE TEMOIN DISJOINT DEVIENT IMPOSSIBLE, ET LE CONTROLE S'AMELIORE.** Les
fenetres de `NoSquare` couvrent toute la grille : aucune contrainte ne peut lui
etre disjointe -- **et `Connected` aura la meme propriete**. Remplace par un
controle **strictement plus fort** : meme systeme, autre propagateur
**desactive**. Les deux mondes ont exactement le meme ensemble de solutions ;
seule change la capacite de l'autre a rogner. Meilleur que le controle
geometrique, qui faisait varier le systeme en meme temps que le chevauchement.
Invariant 18.

**TROIS CROISEMENTS ONT ECHOUE, CINQUIEME FORME DE LA MEME LECON** -- et cette
fois elle se lit sans tatonner. Le bug lit `min(dom) == 1`, il lui faut donc un
domaine partiel egal a `{1, 2}` :
- `Count(val=1)` ne retire jamais que la valeur 1 : il produit `{0, 2}`.
  **Structurellement incapable.**
- `SumRange(lo=0)` n'a que son plafond actif : il ne retire que les grandes
  valeurs. Idem.
- `NoTriple x NoSquare` a besoin de **quatre** cellules posees pour s'amorcer :
  couverture aveugle a `max_taille = 3`, pas bug inerte (invariant 15).

Corriges en `Count(val=0)`, `SumRange(lo=3)`, `NS_TAILLE = 4`.

**Verifie** :

    AllDiff   x NoSquare :  15 / 0     Mono      x NoSquare :  96 / 0
    Count     x NoSquare :  15 / 0     PairDiff  x NoSquare :  15 / 0
    SumRange  x NoSquare : 531 / 0     PairRatio x NoSquare :  15 / 0
    NeqAdj    x NoSquare :  15 / 0     NoTriple  x NoSquare :   3 / 0
    declenche a DEUX au lieu de trois : le canari mord

**COUT** : 3,39 s (28 paires) -> **8,23 s (36 paires)**. Conforme a
l'attribution corrigee : huit paires a n=3 et `max_taille = 4` (30 720 essais
par execution contre 15 600), pas le nombre de paires.

**Non verifie / suppose** :
- Les croisements de `NoTriple` et `NoSquare` sont **echantillonnes**, regime
  imprime a chaque ligne.
- `propagate.py` n'est **toujours pas branche**. Aucune mesure n'a encore ete
  produite par A.

**Bloque sur** : rien. **LES NEUF PROPAGATEURS FACILES ET MOYENS SONT FINIS.**
Point d'etape demande avant `Connected`.

## 2026-08-26 - NoTriple, huitieme propagateur, et un HUITIEME CAS DU MOTIF

**Fait** : `propager_notriple` -- dans une fenetre de trois consecutives, si
deux sont au meme singleton, la troisieme ne peut pas valoir cette valeur.
Sept croisements de plus : **vingt-huit paires**.

**14BIS VERIFIE SUR NoTriple** : les fenetres sont les triplets consecutifs de
la region, donc un objet **FIXE par la contrainte** -- il ne depend pas des
domaines et ne bouge pas quand ils retrecissent. **14 suffit.** La lecture
preliminaire est confirmee ; reste `NoSquare`.

**LE PIEGE** : `NoTriple` n'est pas un `NeqAdj` -- deux valeurs identiques
consecutives sont licites. Meme piege que `NeqAdj` traite comme `AllDiff`, d'un
cran plus fin. Traite comme un NeqAdj : 80 / 109 / 32 violations.

**HUITIEME CAS DU MOTIF, ET IL ETAIT DANS LE CANARI LUI-MEME.** Les sept
croisements ont d'abord rendu **zero violation** sous un bug reel. Pas un bug
inerte : **l'echantillon ne couvrait rien.** `NoTriple` exige quatre cellules
et un temoin disjoint, donc n=3, donc un echantillon au lieu de l'exhaustif --
et cet echantillon etait `sols[:30]` sur une enumeration **lexicographique**.
Toutes les grilles retenues partagent les memes petites valeurs en tete : un
**coin** de l'espace.

    sols[:30]                     : 0 violation
    tirage aleatoire, meme taille : des centaines

**Introduit dans le commit meme qui ajoutait la couverture qu'il annulait.**
Ce qui l'a fait voir : refuser de conclure « bug inerte » sur sept echecs
simultanes -- sept croisements independants ne deviennent pas tous inertes en
meme temps. Diagnostic separe avant toute correction.

**Corrige** : `echantillon()`, tirage aleatoire a graine fixe, partout ou un
prefixe etait pris. **Invariant 15**, plus la regle generale : quand une
couverture est reduite, verifier que la reduction est **independante de l'ordre
dans lequel les cas ont ete produits**. Et : un croisement qui rend zero peut
etre un bug inerte **ou** une couverture aveugle -- **les deux impriment la
meme ligne**.

**Verifie** :

    AllDiff  x NoTriple :  48 / 0      Mono      x NoTriple : 290 / 0
    Count    x NoTriple :  60 / 0      PairDiff  x NoTriple :  48 / 0
    SumRange x NoTriple :  72 / 0      PairRatio x NoTriple : 513 / 0
    NeqAdj   x NoTriple :  48 / 0

**COUT REMESURE** : 0,42 s (21 paires) -> **3,39 s (28 paires)**. Le saut vient
de la **taille de grille**, pas du nombre de paires : les croisements a n=3
font 15 600 essais contre ~600 a n=2. La croissance n'est donc pas quadratique
en paires -- elle est dominee par n. A surveiller a `NoSquare`.

**Non verifie / suppose** :
- Les croisements de `NoTriple` sont **echantillonnes** (120 solutions,
  sous-ensembles <= 3), pas exhaustifs. Le regime est **imprime a chaque
  ligne** pour qu'on ne les lise pas comme les autres.
- `propagate.py` toujours pas branche.

**Bloque sur** : rien.

## 2026-08-26 - DECISIONS DE CADRAGE : A est un chantier de debit

**Aucun code.** Quatre decisions prises apres questions, consignees avant
d'ecrire NoTriple.

**1. A est un chantier de DEBIT, pas de mesure.** A existe pour rendre n=5
praticable sous 20 s -- la seule experience qui puisse trancher l'hypothese.
Au branchement, ce qu'il faut verifier en priorite est le **cout par systeme**,
pas la qualite de deduction. Ecrit en tete de PERIMETRE-A.md et de CLAUDE.md.

**2. LA MESURE QUE LE GEL REND POSSIBLE** -- et que je n'avais pas vue :

    gain_propagation = (resistance_T0 - resistance_prop) / resistance_T0

Test plus **direct** de l'hypothese que la resistance brute : un systeme
localement decomposable voit sa resistance **recuperee** par des propagateurs
locaux plus forts ; un systeme non decomposable, **non, par definition**.
Prediction : gain **faible** pour `connect`, **fort** pour `static`.
C'est l'ecart entre deux instruments dont **l'un ne bouge jamais** qui est le
signal -- sans le gel, les deux deriveraient ensemble et l'ecart ne dirait
rien.

Au branchement : second champ, les deux resistances en **brut** (jamais le
ratio), **canari de non-redondance** (si les deux mesures coincident toujours,
l'une ne sert a rien), et le controle croise contre `count_solutions`.

**3. Connected : le point d'articulation est ECARTE, pas reporte.** Deux
motifs, aucun n'est la difficulte : un Connected trop fort dissoudrait
localement la difficulte mesuree ; et l'articulation est la **seule** inference
du chantier portant sur un objet **induit** et **non monotone**, donc l'ecarter
regle **14bis sans avoir a le trancher**. Reouverture uniquement si le debit a
n=5 est insuffisant avec l'inaccessibilite seule -- et il faudra alors prouver
14bis **avant**.

**4. NoSquare : `dsl2.py` reste intact.** Region sur-inclusive = inefficacite,
pas incorrection ; le diff vide est une preuve mecanique qui vaut plus qu'une
optimisation. Le propagateur construit ses fenetres 2x2 lui-meme. **Le commit
preparatoire de decomposition n'a plus lieu d'etre.**

**Bloque sur** : rien.

## 2026-08-26 - PairRatio, septieme propagateur : 21 paires, sept faciles finis

**Fait** : `propager_pairstep`, meme helper que `PairDiff`, autre relation.
Six croisements de plus : **vingt et une paires**. Les **sept propagateurs
faciles sont finis**.

**LE POINT DU COMMIT** : la relation de `PairDiff` est **monotone en `w`**, donc
un test **aux bornes** y serait exact. Celle de `PairRatio` ne l'est pas -- le
seul support d'une valeur peut etre une valeur **interieure**. Recopier le test
aux bornes d'un propagateur a l'autre est **exact pour l'un et faux pour
l'autre**, alors qu'ils partagent leur helper. C'est l'erreur que le partage
invite, et c'est le test negatif :

    support aux bornes : 0 / 28 / 24 / 0 violations
                         (delta=1 / delta=d-1 / delta>=d / chaine)

Zero sur `delta = 1`, ou les bornes suffisent effectivement : le canari
discrimine sur la **structure de la relation**.

**Le croisement PairDiff x PairRatio** -- celui qui couvre le risque du helper
partage, assume au commit precedent -- mord : 30 contre 0.

**QUATRIEME FORME DE LA MEME LECON.** `Mono x PairRatio` a echoue : la cellule
partagee etait bien rognee, mais **du mauvais cote**. `Mono([0, 1])` ne peut que
relever le plancher, et `dom[1] = {1, 2}` a pour minimum 1, qui supporte tout a
`delta = 1`. Il fallait `Mono([1, 0])`, qui abaisse le plafond et produit
`{0, 1}`. Enonce complet desormais dans l'invariant 13 : il faut que l'autre
propagateur puisse produire **le domaine partiel PARTICULIER que l'inference
injectee lit de travers**.

**COUT REMESURE** : 0,20 / 0,21 / 0,27 / 0,32 / **0,42 s** a 3, 6, 10, 15, 21
paires. Croissance reelle, sans consequence.

**Non verifie / suppose** :
- `propagate.py` toujours pas branche ; `engine_active_hash` inchange depuis le
  debut de A.
- Les croisements restent a n=2, pour l'exhaustivite.
- **14bis reste NON TRANCHE.** La lecture preliminaire sur NoTriple et NoSquare
  (fenetres geometriques, donc objets FIXES) n'est toujours pas verifiee dans
  le code -- c'est le premier travail de l'etape 8.

**Bloque sur** : rien.

**Pour Claude chat** : restent NoTriple et NoSquare (moyens), puis Connected.
NoSquare doit etre **decompose en (n-1)^2 fenetres 2x2** -- il est actuellement
mal modelise avec la grille entiere pour region (voir PERIMETRE-A.md).

## 2026-08-26 - PairDiff, sixieme propagateur, + 14bis ecrit

**Fait** : `propager_pairdiff`, coherence d'arc sur une relation binaire.
Cinq croisements de plus : **quinze paires**. `14bis` ecrit dans DECISIONS.md
comme generalisation candidate **non tranchee**.

**14bis, et le critere operatoire qui en decoule** : l'invariant 14 couvre les
inferences dont l'entree est l'appartenance d'une valeur a un domaine ; pas
celles dont l'entree est une propriete d'un objet construit a partir de
plusieurs domaines et **non monotone sous retrecissement**. Reformule en une
question par propagateur :

    l'objet sur lequel porte l'inference est-il FIXE par la contrainte,
    ou INDUIT par les domaines courants ?

Fixe (region, fenetre geometrique, liste de paires) -> 14 s'applique tel quel.
Induit (le graphe des cases passables de Connected) -> une propriete peut ne
pas etre monotone meme si chaque domaine ne fait que retrecir.

**Lecture preliminaire sur NoTriple et NoSquare, NON VERIFIEE DANS LE CODE** :
leurs fenetres sont **geometriques et statiques** -- triplets consecutifs,
carres 2x2 -- donc **fixes**. 14 devrait suffire, et 14bis n'isolerait bien que
Connected. **A verifier a l'ecriture, aux etapes 8 et 9.**

**Verifie** : les six propagateurs ecrits raisonnent tous sur un objet fixe.
`PairDiff` ne fait **aucune** lecture de forme : sur par construction, comme
`Mono`.

    dirige (valeur absolue oubliee) : 270 / 90 / 90 / 180 violations
    AllDiff  x PairDiff : 42 / 0     NeqAdj x PairDiff : 42 / 0
    Count    x PairDiff : 12 / 0     Mono   x PairDiff : 12 / 0
    SumRange x PairDiff : 18 / 0

**A SIGNALER** : le cas vacuous (`k = 0`) ne donne **pas** zero sous le bug,
contrairement a tous les autres propagateurs. Ce n'est pas une anomalie : le
bug ne confond pas une borne, il **change la relation**. Le signal de
discrimination n'est donc pas au meme endroit, et il faut le lire plutot que
l'attendre au meme endroit qu'ailleurs.

**Helper `_arc_consistance` partage avec PairRatio** : assume, hors invariant
10 (qui protege `feasible()` vs propagation, pas un parcours de paires). Le
risque qu'un bug du helper touche les deux est couvert par le croisement
`PairDiff x PairRatio`, qui viendra au commit suivant.

**Bloque sur** : rien.

## 2026-08-26 - Mono, cinquieme propagateur, + quatre croisements

**Fait** : `propager_mono_avant` / `propager_mono_arriere`, coherence aux
bornes sur une contrainte d'ordre. Quatre croisements de plus : **dix paires**.

**MONO EST LE PREMIER PROPAGATEUR SUR PAR CONSTRUCTION.** Il ne fait **aucune**
lecture de forme -- seulement `min`, `max` et l'appartenance -- donc
l'invariant 14 le declare immunise aux interactions, **par relecture, avant
tout test**. Le critere ne fait pas que garder : il **classe**.

Confirmation par l'autre bout : pour fabriquer une interaction unsound sur
Mono, il a fallu **introduire deliberement une lecture de forme** dans le bug
injecte. C'est exactement ce que 14 predit.

**Verifie** :

    AVANT zele   : 76 / 75 / 10 violations  (|R|=2 / |R|=3 / |R|=4,d=2)
    ARRIERE zele : 50 / 41 /  7
    AllDiff  x Mono : chevauchant  6, temoin disjoint 0
    Count    x Mono : chevauchant 12, temoin disjoint 0
    SumRange x Mono : chevauchant  6, temoin disjoint 0
    NeqAdj   x Mono : chevauchant  6, temoin disjoint 0

**DEUX CROISEMENTS ONT ECHOUE, ET J'AI CORRIGE LES CROISEMENTS, PAS LE
CANARI.** Le bug porte sur le sens ARRIERE, qui lit `dom[b]` ; avec
`Mono([1, 2])` et l'autre contrainte sur `[0, 1]`, l'autre propagateur rognait
le `a`. Corrige en inversant l'ordre de la region.

**TROISIEME OCCURRENCE DE LA MEME LECON, desormais precisee dans l'invariant
13** : partager une cellule ne suffit pas, il faut que l'autre puisse
effectivement la **rogner** -- et qu'il rogne **celle que l'inference injectee
lit**, pas une voisine.

**COUT DE canary3, REMESURE** : 0,20 s (3 paires), 0,21 s (6), **0,27 s (10)**.
La croissance est visible et reste sans effet pratique. A remesurer apres
PairRatio, et surtout apres NoSquare et Connected.

**Non verifie / suppose** :
- `propagate.py` toujours pas branche ; `engine_active_hash` inchange.
- Les croisements restent a n=2. Le controle de fond reste le solveur
  exhaustif, au branchement.

**Bloque sur** : rien.

**Pour Claude chat** : restent PairDiff et PairRatio (faciles), NoTriple et
NoSquare (moyens), Connected (dur, en dernier, et sa question ouverte sur
l'invariant 14 doit etre traitee EN PREMIER a l'etape 10).

## 2026-08-26 - NeqAdj, quatrieme propagateur, + trois croisements

**Demande** : NeqAdj puis Mono, meme gabarit, croisements contre tous les
precedents ; faire de l'invariant 14 un **critere de relecture** ; consigner la
question ouverte de Connected ; **remesurer** le cout de canary3.

**Fait** :
- `propager_neqadj` : une cellule reduite a `{v}` interdit `v` a ses **voisines
  immediates**. Une seule lecture de forme, `len(dom) == 1`.
- **Critere d'audit ecrit en tete de `engine/propagate.py`**, la ou on le relit
  avant d'ecrire un test : chercher chaque test de FORME d'un domaine, chacun
  est un point d'unsoundness potentiel. Seule forme admise `len(dom) == 1`,
  parce qu'elle **determine** le contenu au lieu d'en etre un proxy.
- Trois croisements de plus (AllDiff, Count, SumRange x NeqAdj). Six paires.

**LE PIEGE, et c'est T1 sous un troisieme habit** : `NeqAdj` n'est pas un
`AllDiff`. Sur trois cellules ou plus les **extremites peuvent etre egales**.

    NeqAdj traite comme un AllDiff : 0 / 58 / 14 violations
                                     (|R|=2 / |R|=3 / |R|=3,d=2)
    AllDiff x NeqAdj  : chevauchant 42, temoin disjoint 0
    Count   x NeqAdj  : chevauchant 12, temoin disjoint 0
    SumRange x NeqAdj : chevauchant 18, temoin disjoint 0

Zero sur `|R| = 2`, ou la confusion est effectivement sans effet.

**QUESTION OUVERTE CONSIGNEE, a trancher a l'etape 10 et pas avant** :
l'invariant 14 pourrait etre **correct et incomplet** pour Connected. Le
retrait par inaccessibilite lit de l'**appartenance**, donc il est couvert.
Mais le forcage par **point d'articulation** infere depuis la structure du
graphe induit -- une propriete de forme **collective**, alors que 14 ne parle
que de la forme d'**un** domaine. Le graphe ne fait que perdre des sommets,
ce qui est monotone, mais **l'ensemble des points d'articulation n'est pas
monotone sous suppression de sommets**. C'est la que porte le doute.

**COUT DE canary3, REMESURE et non suppose** (consigne demandee, tous les
deux propagateurs) :

    3 paires (SumRange) : 0,20 s
    6 paires (NeqAdj)   : 0,21 s

Le doublement du nombre de paires ne se voit pas. Les grilles de
croisement sont a n=2, donc l'enumeration exhaustive y coute quelques
centaines d'essais, negligeable devant la partie 1. La croissance
quadratique est reelle mais part de tres bas. **A remesurer apres Mono et
PairRatio** -- et surtout apres NoSquare et Connected, dont les regions
sont bien plus grandes.

**Bloque sur** : rien.

## 2026-08-26 - SumRange, troisieme propagateur, + deux croisements

**Demande** : SumRange, meme famille de bornes que Count, gabarit a deux sens.

**Fait** : `propager_sum_plafond` / `propager_sum_plancher` (coherence aux
bornes lue sur les **domaines**, donc plus forte que `feasible()` qui borne
toute inconnue par `d-1`). Trois cas limites a la main : `lo == hi`, `lo < hi`,
et **vacuous** `[0, |R|*(d-1)]` -- le piege, ou aucun retrait n'est jamais
justifie. Deux croisements ajoutes : AllDiff x SumRange, Count x SumRange.

**Deux sens dans le meme commit** : condition remplie.

    PLAFOND zele  : 86 / 191 / 0 violations (lo==hi / lo<hi / vacuous)
    PLANCHER zele : 87 / 188 / 0
    AllDiff x SumRange        : chevauchant 48, temoin disjoint 0
    Count(lo=hi=1) x SumRange : chevauchant 24, temoin disjoint 0

**LE CROISEMENT Count x SumRange A ECHOUE D'ABORD, ET J'AI CORRIGE LE
CROISEMENT, PAS LE CANARI.** Premiere version avec `Count(lo=1, hi=2)` sur une
region de 2 cellules : le bug ne mordait pas. Cause : avec `hi == |R|`, le sens
INTERDICTION ne peut **rien retirer dans sa propre region**, donc Count ne
pouvait pas fabriquer le domaine partiellement rogne dont le bug a besoin.
Meme lecon que X1 : **une paire de configurations limites n'est pas
automatiquement une paire ou l'interaction est observable**. Il faut que l'un
des deux puisse effectivement ROGNER une cellule partagee, pas seulement la
partager.

**Generalisation ecrite dans CLAUDE.md (invariant 14)** : la classe des bugs
d'interaction est **cernee**. Tout ce qui repose sur une lecture perimee est
inerte par monotonie -- les domaines ne font que retrecir. Le seul moyen pour
un propagateur de devenir trop zele par interaction est **d'inferer le contenu
d'un domaine depuis sa forme**. C'est desormais le gabarit du test negatif de
chaque croisement.

**Verifie** : les huit canaris passent depuis la racine et depuis `engine/`.
`rulesearch.py`, `dsl2.py`, `deduction.py`, `t0_legacy.py` : diff vide.
`canary3` complet tourne en **0,20 s** avec trois paires -- la croissance
quadratique est sans effet pratique a ce stade.

**Non verifie / suppose** :
- `propagate.py` toujours **pas branche**. `dsl_hash` passe a `23303c299f39`,
  `engine_active_hash` reste `0caa9267db60`.
- Les croisements sont a n=2 pour rester exhaustifs. Meme limite, meme reponse
  : le controle de fond est le solveur exhaustif, au branchement.
- Le cas **vacuous** de SumRange ne peut rien declencher, donc il n'exerce que
  la surete -- comme X1. Ce n'est pas un defaut, mais il ne faut pas le
  compter comme une couverture d'interaction.

**Bloque sur** : rien.

**Pour Claude chat** : restent NeqAdj, Mono, PairDiff, PairRatio (faciles),
NoTriple et NoSquare (moyens), Connected (dur, en dernier). Chaque ajout =
un propagateur + N croisements contre tous les precedents.

## 2026-08-26 - croisements manuels de propagateurs (invariant 13)

**Demande** : avant SumRange, construire a la main les croisements de paires de
propagateurs, sur des regions qui **se chevauchent**, avec un test negatif qui
soit un bug **d'interaction** et non la reinjection d'un bug simple.

**Fait** : trois systemes a n=2 / d=3, enumeration **exhaustive** (toutes les
solutions x tous les sous-ensembles d'indices) -- un echantillon aleatoire
raterait la configuration rare qui declenche l'interaction.

    X1  AllDiff |R|<d x Count lo==0, chevauchant
    X2  AllDiff |R|<d x Count lo==1, chevauchant
    X3  meme paire, DISJOINTE -- TEMOIN

**RESULTAT NEGATIF, consigne parce qu'il vaut mieux qu'une case vide** : le bug
suggere -- le **cache perime** -- est **structurellement inerte** ici. Les
domaines ne font que retrecir et les declencheurs de Count sont des egalites
sur des quantites monotones : une lecture perimee donne un `sur` plus petit et
un `poss` plus grand, donc un propagateur plus **faible**, jamais plus zele. Il
produirait une deduction manquee, pas une solution fausse. La meme monotonie
protegera les huit propagateurs suivants.

**Le bug d'interaction reel** est ailleurs : l'hypothese implicite qu'un
domaine est **plein ou singleton**, vraie dans le monde du forward-checking
d'ou l'on vient, fausse des qu'un autre propagateur a rogne partiellement une
cellule partagee.

    bug sur X2 (chevauche) : 24 violations
    bug sur X3 (DISJOINT)  :  0 violation

**Verifie** : surete 0 violation sur les trois croisements ; le temoin disjoint
reste muet la ou le chevauchant crie. Les huit canaris passent.

**CE QUE JE SIGNALE SANS QUE CE SOIT DEMANDE** : le croisement **nomme** dans
la consigne -- `|R| < d` x `lo == 0` -- donne **0 violation meme avec le bug**.
Avec `lo == 0` le sens FORCAGE ne se declenche jamais, et c'est lui qui porte
l'unsoundness. X1 exerce la surete, **pas** l'interaction ; X2 a ete ajoute
pour ca. **Une configuration limite n'est pas automatiquement une configuration
ou l'interaction est observable** -- et un croisement qui ne peut rien
declencher aurait ete un canari vide de plus.

**Non verifie / suppose** :
- Une seule paire existe aujourd'hui. Le cout quadratique (45 paires a dix
  propagateurs) n'a donc pas encore ete mesure.
- Les croisements sont a n=2, pour l'exhaustivite. Meme limite qu'au commit
  precedent, meme reponse : le controle de fond est le solveur exhaustif, au
  branchement.

**Bloque sur** : rien.

## 2026-08-26 - Count, deuxieme propagateur, deux sens dans un seul commit

**Demande** : feu vert pour Count. Les deux sens dans le meme commit
**seulement si** `canary3` les distingue separement dans son test negatif ;
sinon un seul sens par commit.

**Condition remplie**, donc les deux sont commites ensemble. Le bug injecte est
le meme des deux cotes -- confondre `lo` et `hi` -- et chaque variante ne
remplace qu'un sens, l'autre restant correct : la violation est imputable.

    INTERDICTION zelee : 0 sur lo == hi, 20 sur lo < hi, 21 sur lo == 0
    FORCAGE zele       : 0 sur lo == hi, 19 sur lo < hi,  9 sur lo == 0

Zero des deux cotes sur `lo == hi`, ou la confusion est effectivement sans
effet : le canari **discrimine**, il ne signale pas au hasard.

**Cas limites construits a la main** : `lo == hi`, `lo < hi`, et `lo == 0` --
le piege, analogue de `|R| < d` pour AllDiff : la contrainte autorise zero
occurrence, donc aucun raisonnement « une cellule doit valoir val » n'y est
valide. Surete : **0 violation** sur les trois.

**Ajoute sans que ce soit demande** : un controle que **chaque sens est invoque
au moins une fois**. Deux techniques de deduction ont deja ete ecrites,
verifiees, puis retirees pour n'avoir jamais tourne -- un propagateur inerte se
constate a l'ecriture ou jamais. Mesure : interdiction 10, forcage 5. Le
forcage ne se declenche jamais sur `lo == 0`, ce qui est normal.

**Verifie** : `rulesearch.py`, `dsl2.py`, `deduction.py`, `t0_legacy.py` ont un
**diff vide** -- la conservation de `feasible()` reste verifiable
mecaniquement.

**Non verifie / suppose** :
- `propagate.py` n'est toujours **pas branche**. `engine_active_hash` reste
  `0caa9267db60` alors que `dsl_hash` passe a `06fe04a859f1`.
- ~~section de regroupement jamais vue s'afficher~~ **VERIFIEE apres le
  commit** : la production a bascule sur `06fe04a859f1` et `summarize.py`
  affiche desormais « moteur actif `0caa9267db60` (1628 systemes) :
  `06fe04a859f1`, `e40600351a72` ». Le dispositif a ete VU fonctionner sur
  son premier cas reel, pas seulement ecrit.
- Interaction AllDiff x Count : couverte uniquement sur les systemes du
  generateur qui portent les deux. Le controle de fond -- propagation contre
  `count_solutions` -- reste a ajouter **au branchement**.

**Bloque sur** : rien.

**Pour Claude chat** : troisieme propagateur au choix parmi SumRange, NeqAdj,
Mono, PairDiff, PairRatio. Meme gabarit ; regle « les deux sens ensemble
seulement si le test negatif les separe » desormais generale.

## 2026-08-26 - engine_active : lire par-dessus les ruptures de serie

**Demande** : ne pas toucher a `dsl_hash` -- l'asymetrie est ecrasante -- mais
attenuer la rupture en journalisant les modules **reellement** sur le chemin
d'execution, pour que `summarize.py` puisse regrouper en le disant.

**Fait** :
- `run.py` : `ENGINE_ACTIVE` (liste tenue a la main), `engine_active_hash()`,
  `modules_inertes()`. Le record porte `engine_active` et
  `engine_active_hash` ; `config.json` porte en plus `engine_inertes`.
- `summarize.py` : section « regroupement possible par moteur ACTIF (lecture,
  pas equivalence) », qui n'apparait que si au moins deux `dsl_hash` partagent
  un meme moteur actif.

**POINT DE CONCEPTION** : le regroupement se fait sur le hash du **contenu**
des modules actifs, **jamais sur la liste de noms**. Regrouper sur les noms
fusionnerait deux series dont le code actif differe -- le mode de defaillance
que `dsl_hash` existe pour empecher, reintroduit un etage plus bas.

**Verifie** : `dsl_hash e40600351a72`, `engine_active 0caa9267db60`,
inertes = `['propagate.py']`. `summarize.py` tourne, 45068 enregistrements ;
la section de regroupement **ne s'affiche pas encore** (un seul moteur actif
connu) et 45054 enregistrements sont signales comme anterieurs au champ.

**Non verifie / suppose** :
- La section de regroupement n'a **jamais ete vue s'afficher**. Elle le sera au
  commit de `Count`, qui changera `dsl_hash` sans changer le moteur actif :
  c'est son premier test reel. **A verifier a ce moment-la, pas avant.**
- `run.py` n'etant pas dans `engine/`, ce commit **ne change pas** `dsl_hash`.

**Ferme** : le risque d'interaction a n plus grand ne se couvre pas par
`canary3` -- l'enumeration exhaustive impose des cas petits -- mais par le
controle croise `propagation vs count_solutions`, **a ajouter au moment du
branchement, pas avant**. Consigne dans DECISIONS.md.

**Bloque sur** : rien.

## 2026-08-26 - AllDiff, premier propagateur, avec canary3 etendu AVANT

**Demande** : etendre `canary3` (pas de `canary9` separe), puis ecrire AllDiff,
seul dans son commit.

**Raison de l'extension, donnee par l'utilisateur et desormais invariant 11** :
ce que `canary3` verifie est une propriete du **systeme de deduction entier**.
Deux propagateurs individuellement corrects peuvent, ensemble, retirer un
candidat de trop -- **l'erreur nait de l'interaction**, qu'un canari par
propagateur ne verrait jamais.

**Fait** :
- `engine/propagate.py` (nouveau) : domaines, `propager()` au point fixe,
  `propager_alldiff()`. **Module separe expres** : `rulesearch.py` et `dsl2.py`
  ne bougent pas d'une ligne, donc la conservation de `feasible()` est
  **verifiable par diff** et pas seulement par revue.
- `canary/canary3.py` : partie 2, trois cas limites **construits a la main**
  (`|R| == d`, `|R| > d`, `|R| < d`), verite de reference par **enumeration
  exhaustive** des solutions, pas par `feasible()` seule.

**Verifie** (execute et observe) :
- surete (aucune valeur d'une solution reelle retiree) : **0 violation** sur
  les trois cas limites et sur les trois systemes AllDiff du generateur ;
- **test negatif** : un AllDiff trop zele -- le hidden single non conditionne,
  soit le bug T1 en langage de domaines -- donne **0 violation sur `|R| == d`**
  (ou la regle est valide) et **46 sur `|R| < d`**. Le canari discrimine au bon
  endroit.

**QUESTION 2 DU TOUR PRECEDENT, TRANCHEE PAR LA MESURE** : sur `|R| > d`, le
retrait simple **n'atteint pas** la contradiction sur grille vide -- aucun
domaine n'est singleton, la regle ne s'amorce pas -- mais l'atteint **des qu'un
indice est pose**. Aucune regle n'a ete ajoutee pour combler le trou :
`feasible()` reste l'oracle, et un propagateur incomplet est correct.

**Non verifie / suppose** :
- **`propagate.py` n'est PAS branche** sur la hierarchie de deduction. T0/T1/T2
  et la metrique de resistance (`t0_legacy`) sont inchanges. Le module existe,
  il est verrouille, il ne tourne pas en production.
- **`dsl_hash` change quand meme** (nouveau `.py` dans `engine/`) alors que le
  comportement de production est identique : une serie se clot pour un module
  inerte.
- Les cas limites sont a n=2 et n=3 pour que l'enumeration exhaustive tienne.
  Rien ne prouve qu'un bug d'interaction n'apparaisse qu'a n plus grand -- mais
  aucun autre propagateur n'existe encore, donc aucune interaction non plus.

**Bloque sur** : rien.

**Pour Claude chat** :
- **Invariant 11** : `canary3` grossit, jamais de canari separe par
  propagateur. S'il devient trop lent, il sort vers un pre-commit -- **jamais**
  on ne reduit sa couverture.
- Prochain propagateur : `Count`, seul dans son commit, `canary3` etendu avant.
- Un `canary3` rouge au sixieme propagateur peut accuser le sixieme **ou
  n'importe quel couple anterieur**.

## 2026-08-26 - A OUVERT. Gel de T0-historique, seul, sans propagateur

**Demande** : ouvrir A. Avant toute ligne de propagation, geler la definition
actuelle de T0 dans un module intouchable dont la metrique acquise continue de
dependre.

**Cause reelle** : la propagation sur domaines est **strictement plus forte**
que le forward-checking actuel. `candidates()` filtre contre les valeurs
**assignees** ; une propagation filtre contre les **domaines**. La resistance a
T0 mesurant la non-localite **relativement a un propagateur donne**, renforcer
ce propagateur **deplace la frontiere mesuree** : un T0 plus fort resoudrait
davantage de systemes a connectivite, donc mesurerait **moins bien exactement
ce qu'il doit mesurer**. Le gel est structurel, pas une commodite d'archivage.

**Correction** :
- `engine/t0_legacy.py` (nouveau, **jamais modifiable**) : copie figee de
  `candidates`, `apply_T0`, la saturation au point fixe, et `resistance()` qui
  rend les deux bruts.
- `run.py` : la metrique se refere desormais a `t0_legacy`, plus a
  `deduction.apply_T0`.
- `canary/t0_reference.json` : 60 entrees figees.
- `canary/canary8.py` : verrou.
- `canary8` enregistre dans `run_canaries()`.

**LE GEL DU MODULE NE SUFFISAIT PAS, et c'est le point de conception.**
`t0_legacy` appelle `rs.feasible(g, changed=i)`, dont le comportement vit dans
les classes de contraintes que A va toucher. Une modification de `feasible()`
changerait les valeurs produites **sans que le fichier gele ait bouge d'une
ligne**. `canary8` ne compare donc pas a du code courant -- lequel va changer
par construction -- mais a des **nombres figes**.

Le puzzle est stocke tel quel plutot que regenere : `random_solution` et
`minimal_clues` peuvent legitimement changer sous A ; les regenerer rendrait le
canari sensible a des evolutions permises.

**Decision d'architecture prise par l'utilisateur** : `feasible()` est
CONSERVEE, la propagation s'ajoute a cote. Trois raisons, dont une que je
n'avais pas vue et qui est la plus forte : **le solveur exhaustif utilise
`feasible()`, et c'est lui qui produit la verite contre laquelle `canary3`
validera les propagateurs.** Code partage = `canary3` compare une erreur a
elle-meme. Cout assume : duplication de la logique de chaque contrainte.

**Verifie** (execute et observe) :
- **Les huit canaris passent depuis la racine ET depuis `engine/` : 16/16.**
- `canary8` passe sur les 60 entrees (40 positives, 20 nulles).
- **Test negatif dans les DEUX sens, et il mord** :
  - affaiblissement (une passe de T0 au lieu du point fixe) : **20 divergences
    sur 60** ;
  - renforcement (T0+T2, entrees `static`) : **6 sur 6**, toutes tombant a 0
    case restante contre 2 a 4 attendues.

**LE TEST NEGATIF EST LUI-MEME UN CAS DU MOTIF DU PROJET -- septieme de la
liste, desormais en tete de CLAUDE.md.** Sa premiere version renforcait T0
avec **T1**. Zero divergence : non parce que le canari etait aveugle, mais
parce que **T1 est un no-op dans cet espace**, fait etabli le matin meme et
oublie l'apres-midi. Le test ne prouvait rien tout en ayant l'air de conclure.
Deuxieme version, T0+T2 : correcte mais **impraticable**, plus de six minutes
pour huit entrees, T2 sur des systemes a connectivite etant exactement le cas
couteux. Un test juste qui ne finit pas ne vaut pas mieux qu'un test vide.
Troisieme version : les deux sens, cout maitrise, `python3 -u` -- les deux
premieres sorties avaient ete perdues par bufferage.

**Non verifie / suppose** :
- Le sens A n'est detecte que sur **20 entrees sur 60** : pour les 40 autres,
  une seule passe de T0 atteint deja le point fixe. Suffisant pour prouver que
  la comparaison mord, mais le corpus n'est pas uniformement sensible.
- Le sens B n'a ete verifie que sur **6 entrees `static`**. Les entrees a
  connectivite -- les plus importantes -- n'ont pas ete testees en
  renforcement, faute de temps de calcul.
- **`dsl_hash` change** (ajout dans `engine/`). La serie pre-A est close ; les
  donnees anterieures ne se comparent pas aux suivantes.
- Aucun propagateur n'existe. Ce commit ne contient **que le gel**.

**Bloque sur** : rien.

**QUESTIONS EN ATTENTE, non tranchees seul** :
1. **`canary3` etendu, ou un `canary9` separe ?** Dix propagateurs a venir.
   Entasser dans `canary3` le rend illisible ; le dupliquer dilue la
   responsabilite du canari de correction. Mon inclination : etendre
   `canary3`, une section par propagateur.
2. Sur `AllDiff` avec `|R| > d` (infaisable par principe des tiroirs) : le
   retrait simple suffit-il a atteindre la contradiction par saturation ? Si
   non, le propagateur dira "pas de contradiction" sur un systeme mort --
   **correct au sens incomplet, mais a constater et non a supposer**.

**Pour Claude chat** :
- **`engine/t0_legacy.py` ne doit JAMAIS etre modifie.** Si `canary8` diverge,
  c'est le reste du moteur qu'il faut corriger, pas le corpus a regenerer.
- **`feasible()` est conservee telle quelle** pendant tout A. La propagation
  s'ajoute a cote. C'est ce qui garde l'oracle independant.
- La metrique acquise se refere a `t0_legacy`, jamais a `deduction.apply_T0`.
- Un seul propagateur par commit, `canary3` etendu **avant** chacun.

## 2026-08-26 - resistance != profondeur, file reduite, PERIMETRE-A.md

**Demande** : ecrire noir sur blanc que la resistance a T0 n'est pas la
profondeur ; mettre a jour l'hypothese en cours ; reduire la file a deux
configurations ; preparer le perimetre de A sans coder.

**1. La distinction est ecrite dans `CLAUDE.md`**, a cote de la metrique, sous
le titre *CE QU'ELLE MESURE, ET CE QU'ELLE NE MESURE PAS* :

  - la resistance a T0 mesure la **non-localite de la contrainte**, pas la
    **profondeur de la deduction** ;
  - un systeme qui resiste a T0 et tombe entierement a T2 est **PLAT au sens du
    projet** ;
  - acquis : la connectivite produit des systemes que la propagation locale ne
    resout pas ;
  - **non demontre** : l'hypothese de fracture. Le resultat en est coherent,
    coherence n'est pas demonstration.

Formule comme septieme piege potentiel de la serie des metriques qui mesurent
autre chose que ce qu'elles annoncent.

**2. `Hypothese en cours` reecrite** en trois parties : ACQUIS / PAS ACQUIS /
POURQUOI n=4 NE PEUT PAS Y REPONDRE. Le troisieme point est **etabli, pas
suppose** : T0 resout integralement 60 a 92 % des instances, il ne reste que
0,3 a 4,1 cases, une hierarchie n'a structurellement pas la place de s'y
deployer.

Priorites reordonnees : **A d'abord, n=5 ensuite**, avec le motif -- a n=5 le
cout par systeme explose et `--max-seconds` censurerait exactement les systemes
profonds, donc lancer n=5 avant A produirait un echantillon tronque du cote
qui compte.

**3. `queue.json` reduit a deux configurations** : `connect` et `static-ref`
a d=3, la paire a domaine egal qui alimente la metrique acquise. Les deux tags
`-d4` sont retires. Machine liberee de moitie.

**4. `PERIMETRE-A.md`** (nouveau, 12 Ko) -- document de decision, aucun code.
Redige apres lecture integrale de `rulesearch.py`, `dsl2.py`, `deduction.py`,
`prefilter.py`.

    7 contraintes faciles : AllDiff, Count, SumRange, NeqAdj, Mono,
                            PairDiff, PairRatio -- propagateurs de manuel
    2 moyennes            : NoTriple (fenetres glissantes),
                            NoSquare (modele en cause : region = grille
                            entiere, a decomposer en (n-1)^2 fenetres 2x2)
    1 difficile           : Connected

Pour `Connected`, trois regles saines et calculables sont identifiees : retrait
par inaccessibilite, forcage par point d'articulation (Tarjan, O(V+E)), et la
detection de contradiction actuelle qui se garde telle quelle. **Le filtrage
complet est hors de portee** (probleme de type Steiner) -- affirmation
signalee dans le document comme **non verifiee experimentalement ici**.

**Trois consequences non anticipees, mises en avant dans le document** :
- **T0 changerait de sens.** `candidates()` filtre contre les valeurs
  ASSIGNEES ; une propagation filtre contre les DOMAINES, strictement plus
  fort. Donc **la metrique acquise change de definition** et ses chiffres ne se
  comparent pas de part et d'autre du chantier, independamment du `dsl_hash`.
- La hierarchie devrait etre redefinie : la propagation absorbe T0 et une
  partie de T1.
- `canary3` doit etre etendu **avant** la premiere ligne de propagation.

**Recommandation, avec un motif different de celui avance jusqu'ici** : ouvrir
A, mais **pour le debit et non pour les techniques d'elimination**. A n=4 la
hierarchie n'a pas la place de se deployer, donc les techniques debloquees
n'auraient rien a mesurer. L'argument qui tient : la profondeur ne sera
mesurable qu'a n=5/n=6, et a ces tailles le recalcul integral de
`candidates()` devient le goulot. **A n'est pas un detour avant n=5, c'est sa
condition de possibilite.**

Si A n'est pas ouvert, la consequence est ecrite : le projet reste a n=4, la
profondeur n'y est pas mesurable, l'hypothese centrale reste ouverte
indefiniment. Choix defendable, mais un choix et non un report.

**Verifie** (execute et observe) :
- **Les sept canaris passent depuis la racine ET depuis `engine/` : 14/14.**
- `queue.json` relu : deux tags, `block_systems` inchange a 15.
- `PERIMETRE-A.md` present a la racine, 11998 octets.
- Structure de `CLAUDE.md` relue section par section.

**Non verifie / suppose** :
- **Aucune ligne de A n'a ete ecrite.** Tout le document est une analyse de
  lecture : les regles de propagation proposees ne sont ni implementees ni
  testees.
- La NP-difficulte du filtrage complet de la connexite est une **affirmation de
  litterature**, non verifiee dans ce projet.
- Le gain de debit attendu de A n'est **pas chiffre**. Aucune mesure ne
  l'appuie ; c'est une attente.
- **Aucune estimation de duree n'est donnee**, faute de base de mesure. Une
  estimation inventee serait exactement le genre de chiffre que ce projet passe
  son temps a corriger.
- L'effet de la reduction de la file sur le debit des deux tags restants n'est
  pas mesure.

**Bloque sur** : rien. Aucun redemarrage requis, `queue.json` est relu a chaque
cycle.

**Pour Claude chat** :
- **`PERIMETRE-A.md` est le document de decision sur A.** Le lire avant toute
  discussion sur la reecriture du moteur.
- **La resistance a T0 n'est pas la profondeur.** Ne jamais ecrire qu'un
  systeme resistant est "profond" : il est non-local.
- **n=4 ne peut pas repondre a l'hypothese centrale.** C'est etabli. Toute
  proposition de technique intermediaire a cette taille se heurtera au fait que
  T0 resout deja 60 a 92 % des instances.
- La file ne compte plus que **deux** tags. L'absence de `connect-d4` et
  `static-d4` dans `summary.md` est deliberee.

## 2026-08-26 - invariant 7bis applique a la resistance a T0 : ACQUISE

**Demande** : la resistance des candidats `static` (18,1 %) etant tres
superieure a celle des systemes `static` en general (5 %), la metrique
pourrait mesurer le filtre de candidature plutot que la connectivite.
Appliquer 7bis a la metrique elle-meme, dans l'ordre : circularite,
`total_grids`, `n`, `d`. Et journaliser la graine d'instance.

**1. CIRCULARITE -- ECARTEE.** C'etait le risque le plus serieux, et
l'inquietude etait fondee sur le mecanisme : la resistance est bel et bien
liee au verdict (PLAT 0,9 %, LIBRE 7,2 %, SUR-CONTRAINT 34,0 %, CANDIDAT
36,1 %, DEVINETTE 56,2 %). Le filtre selectionne de la resistance.

Mais l'ecart connect/static n'en vient pas -- il **survit hors du filtre et y
est plus grand** :

    CANDIDATS seuls   connect 44,4 %  static 26,8 %   p=0,0030   facteur 1,7
    NON candidats     connect 19,8 %  static  5,1 %   p=0,0005   facteur 3,9
    TOUS evaluables   connect 24,5 %  static  8,9 %   p=0,0005   facteur 2,8

Controle severe **a verdict egal** : LIBRE p=0,0010, CANDIDAT p=0,0005. PLAT
ne montre aucun ecart (1,3 % contre 2,1 %, p=0,5077) -- normal, PLAT designe
les systemes que T0 resout, la mesure y est au plancher dans les deux
familles. C'est une verification de coherence, pas un echec.

**2. total_grids -- premiere tentative INVALIDE, refaite.** Les terciles se
sont effondres (`<=13, <=13, >13`) : `total_grids` est **censure a droite** par
`cap = MIN_GRIDS+1 = 13`. Distribution reelle `{1:2, 2:39, 3:13, 4:24, 13:442}`.
Je ne l'ai pas compte comme reussi.

Refait sur la seule coupure possible :

    au plafond (>=13)  connect 23,7 % (n=185)  static 7,8 % (n=257)  p=0,0005
    sous le plafond    connect 33,8 % (n= 75)  static 33,3 % (n=  3)  NON TESTABLE

85 % des donnees sont au plafond et l'ecart y survit. Le confondant etait
fortement desequilibre -- `connect` au plafond a 71 %, `static` a 99 % -- ce
qui rendait ce controle indispensable.

**3. d -- PASSE**, avec une stabilite frappante : d=3 24,4 contre 8,6
(p=0,0005), d=4 24,7 contre 9,1 (p=0,0005).

**4. n -- NON TESTABLE.** `n` vaut 4 partout : aucune variance. **Marque non
teste, pas reussi.**

**Controle ajoute de moi-meme, `clue_frac` stratifie** : le confondant
precedent restait desequilibre (0,507 contre 0,618) apres normalisation.
Terciles : faible p=0,0120, moyen p=0,0005, eleve p=0,1454 (n=31 connect,
manque de puissance, meme sens). Correlation residuelle resistance/clue_frac
**dans** chaque famille : r=-0,29 connect, -0,31 static -- elle joue des deux
cotes, donc ne fabrique pas l'ecart.

**Verdict : ACQUISE**, avec quatre limites explicitement listees dans
DECISIONS.md.

**Verifie** (execute et observe) :
- 520 systemes evaluables rejoues, rejeu exact valide par concordance de
  `rs.label` avec le champ `sys`.
- Les sept canaris passent depuis la racine ET depuis `engine/` : 14/14.
- `run.py` journalise `inst_seed`. Syntaxe validee.
- `dsl_hash` inchange : `run.py` n'est pas dans `engine/`.

**Non verifie / suppose** :
- **`n` n'est pas teste** et ne peut pas l'etre a n=4 seul.
- La strate `total_grids` **sous le plafond n'est pas testee** (static n=3).
- Le tercile de forte densite d'indices **n'est pas significatif**.
- Aucune correction pour tests multiples ; environ quinze tests ont ete
  effectues sur ces donnees. Avec un seuil a 0,05, on attendrait moins d'un
  faux positif -- mais les p a 0,0005 sont a la borne inferieure du test de
  permutation (2000 melanges), donc non resolus plus finement.
- Les candidats d'une meme serie ne sont pas independants (memes graines).
- Le rejeu utilise des instances fraiches : les systemes sont exacts, les
  puzzles evalues a l'epoque ne sont pas reconstitues. C'est precisement ce
  que `inst_seed` corrige **pour l'avenir**, pas retroactivement.

**Bloque sur** : rien. Aucun redemarrage requis.

**Pour Claude chat** :
- **La resistance a T0 est acquise**, pas provisoire. Elle survit a la
  candidature, au verdict, au domaine, au nombre de grilles et a la densite
  d'indices.
- Elle n'est **pas testee contre `n`** : toute extension a n=5 doit refaire ce
  controle avant de comparer quoi que ce soit entre tailles.
- `total_grids` est **censure a 13** (`cap = MIN_GRIDS+1`). Ne jamais le
  traiter comme une variable continue : 85 % des systemes sont au plafond.
- La resistance est **fortement liee au verdict** (PLAT 0,9 %, DEVINETTE
  56,2 %). Comparer des groupes de composition en verdicts differente sans
  stratifier reproduirait un confondant.
- Les evaluations posterieures au 26/08/2026 portent `inst_seed` : rejouer
  une evaluation = `gen_system` x `idx`, puis `random.seed(inst_seed)`.

## 2026-08-26 - resistance a T0 normalisee : metrique principale, canary7

**Demande** : la resistance a T0 etait confondue par la densite d'indices.
Normaliser sur les cases inconnues, recalculer sur les journaux, en faire la
metrique principale, journaliser les bruts, ajouter `canary7`, consigner.

**Cause reelle** : la mesure normalisait sur la **grille entiere**.

    connect    d=3   74,2 % de grille remplie par T0 seul
    static-ref d=3   98,0 %

24 points, presentes comme le meilleur discriminant du projet. **Artefact.**
`connect` recoit 6,0 indices et `static` 9,5 : `static` part de 59 % de grille
deja remplie contre 37 %. En points **ajoutes** par T0 : 36,7 contre 38,6 --
identiques. Verifie a la main sur mes propres chiffres.

Le confondant, `clue_frac`, etait **journalise depuis le debut et affiche dans
la colonne voisine du meme tableau**. Je ne l'ai pas regarde. Sixieme metrique
du projet a mesurer autre chose que ce qu'elle annonce.

**Correction** : normalisation sur les cases inconnues.

    resistance = t0_left / t0_unknown

**1. Recalcul sur les SYSTEMES DES JOURNAUX** (et non sur des systemes
regeneres). Les enregistrements ne portent pas encore les bruts, mais ils
portent `seed` et `idx`, et `gen_system` est deterministe a partir de
`random.Random(seed)` : rejouer `idx` appels rend **exactement** le systeme
journalise, verifie par comparaison de `rs.label` avec le champ `sys`.
Instances fraiches a graine fixe, car `random_solution`/`minimal_clues`
consomment le `random` global dont l'etat n'est pas reproductible.

    d=3 : connect 39,2 % contre static 18,1 %   facteur 2,2   p = 0,0005
    d=4 : connect 40,4 % contre static 23,2 %   facteur 1,7   p = 0,0005

**Significatif aux deux domaines** -- ce qui repond aussi a la question de
robustesse laissee ouverte : le resultat ne tient pas a un domaine particulier.

Ecart avec l'estimation a la main (facteur 8) : le rejeu porte sur les seuls
**CANDIDATS** journalises, sous-ensemble filtre, alors que la mesure initiale
prenait toute instance resoluble. Les candidats `static` resistent plus que les
systemes `static` en general. **Le facteur reel est ~2, pas ~8.**

**2. `summarize.py`** : section **resistance a T0 — METRIQUE PRINCIPALE**, avec
test de permutation, marquage des series non reproductibles, et refus de
conclure sous 20 par groupe. `max_level` conserve, explicitement marque
**SATURE**.

**3. `run.py`** : journalise **`t0_unknown`** et **`t0_left`**, les deux bruts,
**pas le ratio**. Une normalisation peut changer -- celle-ci vient de changer --
et un ratio journalise ne se recalcule pas. Calcul par saturation de T0 seule
sur une copie du puzzle, avant `solve_graded`. **`dsl_hash` inchange** :
`run.py` n'est pas dans `engine/`, la serie en cours n'est pas rompue.

**4. `canary7`** : la resistance doit valoir **0** quand T0 resout
integralement, et etre **strictement positive** sinon. Echoue aussi s'il
n'arrive pas a **exhiber** l'un des deux cas -- une mesure constante n'aurait
aucun pouvoir discriminant.

**Verifie** (execute et observe) :
- **Les sept canaris passent depuis la racine ET depuis `engine/` : 14/14.**
- `canary7` exhibe bien les deux bornes : 5 instances a resistance 0,000 (T0
  resout tout) et 5 a 0,357 / 0,500 / 0,909 / 0,917 / 1,000.
- Rejeu : 120 systemes par tag pour `connect`, `static-ref`, `static-d4`, 99
  pour `connect-d4`, avec concordance de `rs.label` exigee.
- `summarize.py` tourne et annonce *6 candidats sur 4296 portent les champs
  bruts (0 %)* -- normal, les champs viennent d'etre ajoutes, seuls les blocs
  posterieurs les portent.
- `dsl_hash` inchange, verifie : aucun nouveau hash dans `runs/`.

**Non verifie / suppose** :
- Le rejeu utilise des **instances fraiches**, pas celles evaluees a l'epoque.
  Les systemes sont exacts, les puzzles non. Les chiffres sont donc
  representatifs des systemes journalises, pas une reconstitution.
- La resistance n'a **pas encore ete testee contre les autres variables
  journalisees** (`total_grids`, `n`, `d`) -- seulement contre `clue_frac`, le
  confondant qui vient d'etre trouve. L'invariant 7bis demande plus.
- Le rejeu porte sur les CANDIDATS uniquement. La resistance sur l'ensemble des
  systemes n'est pas mesuree.
- Aucune correction pour tests multiples.
- Les series a hash orphelin sont incluses dans le rejeu, sans distinction.

**Bloque sur** : rien. Aucun redemarrage requis : `run.py` est relance a chaque
bloc, `summarize.py` et les canaris aussi.

**Pour Claude chat** :
- **La metrique principale est la resistance a T0**, `t0_left / t0_unknown`.
  `max_level` est SATURE (100 % partout) et conserve pour memoire seulement.
- **Ne jamais normaliser sur la grille entiere** : la densite d'indices differe
  systematiquement entre `connect` (6,0) et `static` (9,5). Normaliser sur les
  cases inconnues.
- Les journaux portent **deux bruts**, jamais le ratio. Si la normalisation
  change encore, tout reste recalculable.
- Un `summary.md` annoncant *0 % des candidats portent les champs bruts*
  signifie que les enregistrements sont anterieurs au 26/08/2026, pas que la
  mesure est cassee.
- Avant d'adopter une metrique, la tester contre `clue_frac` d'abord. Le
  confondant est dans le journal, a cote.

## 2026-08-26 - RELEVE CONSOLIDE : T0 sature la grille, et un discriminant fort apparait

Seuil atteint : `connect-d4` a 21 candidats, `static-d4` en a 57. Le releve
preliminaire precedent est desormais superflu.

**A. Distribution par tag (journaux)**

    tag            systemes  cands       T0      T1      T2   max_level des cands
    connect           13881   1399    41362       0    5335   {2: 1399}
    static-ref        13597   2087    94679       0    7257   {2: 2087}
    connect-d4          643     21     1037       0     124   {2: 21}
    static-d4           643     57     3637       9     300   {1: 4, 2: 53}
    baseline            124      7      341       0      32   {2: 7}

**Premier fait : la hierarchie a trois niveaux existe enfin, sur `static-d4`.**
T1 s'y invoque 9 fois, et surtout **4 candidats sur 57 ont `max_level = 1`** --
premiers candidats du projet dont T1 est le niveau le plus eleve requis. La
prediction "d=4 rend un domaine a T1" est **confirmee**, plus nettement que
dans le releve preliminaire.

**Deuxieme fait, et c'est un BIAIS A SIGNALER : la restitution est asymetrique.**
`static-d4` a 34,4 % de systemes avec region T1 eligible ; **`connect-d4` en a
0,0 %**. Les familles `connect,relational` ne produisent aucun ALLDIFF, a
aucun domaine. Donc a d=4, `static` dispose de trois niveaux et `connect` de
deux. **Comparer leur profondeur est confondu par la disponibilite meme de la
technique** -- meme classe de defaut que la comparaison d=2 contre d=4
corrigee plus tot. La comparaison connect/static a d=4 ne peut pas porter sur
`max_level` sans traiter ce point.

**B. Ce que T0 remplit a lui seul (mesure demandee, ad hoc, non versionnee)**

Saturation de T0 jusqu'au point fixe, sans jamais invoquer T1 ni T2, sur 60
instances par configuration :

    config           indices   T0 seul    reste apres   resolues
                        moy.  % grille     T0 (cases)   integralement par T0
    connect    d=3       6,0      74,2 %         4,13   36/60  (60,0 %)
    static-ref d=3       9,5      98,0 %         0,32   55/60  (91,7 %)
    connect-d4 d=4       6,3      81,2 %         3,00   40/60  (66,7 %)
    static-d4  d=4      10,0      94,7 %         0,85   53/60  (88,3 %)

**L'hypothese est largement confirmee** : T0 remplit 74 a 98 % de la grille a
lui seul, et resout **integralement** 60 a 92 % des instances. Sur les
systemes statiques il ne reste en moyenne que **0,32 case** -- il n'y a
litteralement pas de place pour une hierarchie. Seize cases se resolvent par
la technique la plus faible.

Nuance qui empeche de conclure trop vite : sur `connect` a d=3 il reste **4,13
cases** en moyenne et 40 % des instances resistent a T0. Ce n'est pas rien.
La saturation n'est donc pas uniforme -- elle est quasi totale sur `static`,
partielle sur `connect`.

**Troisieme fait, non anticipe : cette mesure est un DISCRIMINANT FORT.**

    fraction de grille resolue par T0 seul, a d=3 :
      connect     74,2 %
      static-ref  98,0 %

Un ecart de 24 points, contre 5,75 / 5,28 (soit 8,9 %) pour le score pondere
d'invocations. **Les systemes a connectivite resistent massivement plus a la
technique la plus faible** -- ce qui est exactement ce que l'hypothese de
fracture locale / non-locale predit, et mesure de facon bien plus tranchee que
tout ce qui a ete essaye jusqu'ici. L'ecart persiste a d=4 (81,2 % contre
94,7 %) mais s'y reduit de moitie.

Candidat serieux comme metrique principale, a la place du niveau requis :
**resistance a T0**, non saturee, non binaire, et sans dependance a une
structure de region -- donc pas exposee au probleme qui rend T1 indisponible
pour `connect`.

**Non verifie / suppose** :
- La partie B repose sur **60 instances par configuration**, sans test de
  significativite. L'ecart de 24 points est grand, mais il n'est pas teste.
- La partie B mesure des systemes **regeneres** (graine 2026), pas les
  systemes exactement journalises.
- "T0 arrive avant" est desormais **mesure**, mais l'inference "donc n=4 est
  trop petit pour une hierarchie fine" reste une **interpretation** : elle est
  forte pour `static` (0,32 case restante), faible pour `connect` (4,13).
- La resistance a T0 n'a **pas** ete ajoutee a `summarize.py` : aucune mesure
  n'est versionnee, conformement a la consigne de ne rien coder.
- Les 4 candidats a `max_level = 1` de `static-d4` n'ont pas ete inspectes
  individuellement.
- Aucune conclusion sur l'hypothese centrale : la comparaison a d=4 est
  confondue (voir deuxieme fait), et a d=3 la mesure de resistance a T0 n'est
  pas testee.

**Bloque sur** : rien. Le service tourne, la file a quatre configurations est
active, rien n'a ete modifie.

**Pour Claude chat** :
- **T1 fonctionne et a un domaine a d=4 sur `static` uniquement.** Les familles
  `connect,relational` ne generent aucun ALLDIFF, a aucun domaine : T1 y sera
  toujours indisponible. Ce n'est pas un bug.
- **Ne pas comparer `connect-d4` et `static-d4` sur `max_level`** : l'un a
  trois niveaux disponibles, l'autre deux. Comparaison confondue.
- La mesure la plus discriminante trouvee a ce jour est la **fraction de grille
  resolue par T0 seul** (74 % contre 98 % a d=3), pas le niveau requis ni le
  score pondere d'invocations. Elle n'est pas encore dans `summarize.py`.
- T0 resout integralement 60 a 92 % des instances a n=4. Toute discussion sur
  une hierarchie de deduction fine a cette taille doit partir de ce chiffre.

## 2026-08-26 - RELEVE PRELIMINAIRE, NON CONCLUANT : T1 a d=4

**Statut : preliminaire. Ne rien en conclure.** 150 systemes et 11 candidats
sur les tags `-d4`, tres en dessous des 20 candidats par groupe qu'exige
l'invariant 4. Ce releve est consigne parce qu'il oriente la suite, pas parce
qu'il etablit quoi que ce soit.

**Contexte** : la file est passee a quatre configurations pour rendre a T1 un
domaine d'application, T1 n'ayant jamais ete invoquee a d=3 (ALLDIFF
infaisable sur 4 cases avec 3 valeurs).

    tag            systemes  candidats       T0      T1      T2
    connect (d=3)     13318       1340    39735       0    5112
    static-ref (d=3)  13036       2001    90688       0    6954
    connect-d4           75          3      134       0      20
    static-d4            75          8      390       1      32
    baseline (d=4)      124          7      341       0      32

**Ce que ca montre** : T1 s'est declenchee **une fois**, sur `static-d4`.
Premiere invocation de T1 en production depuis le debut du projet. Le critere
de reouverture inscrit precedemment -- "si T1 reste a 0 sur les tags -d4, la
cause n'est pas le domaine" -- **ne se declenche donc pas** : la cause etait
bien le domaine, et passer a d=4 le restitue.

**Ce que ca ne montre pas** : que le trou se comble. 1 invocation sur 150
systemes, et le `max_level` des 11 candidats `-d4` vaut `{2: 11}` -- tous a T2,
aucun palier intermediaire cree. Rendre son domaine a T1 le rend non vide, pas
utile.

**Le point a creuser, et ce n'est PAS le chiffre de T1** : `baseline` tourne a
d=4 avec **21 % de systemes possedant une region T1 eligible** (mesure sur 600
systemes generes), et affiche pourtant **0 invocation** sur 124 systemes. Avoir
un domaine ne suffit donc pas : **T0 arrive avant**. La technique la plus
faible resout la grille avant que la suivante ait l'occasion de servir.

**MESURE A AJOUTER AU PROCHAIN RELEVE** (demandee, non implementee -- ne rien
coder pour l'obtenir) : parmi les instances resolues, **quelle fraction de la
grille T0 remplit-il a lui seul avant que quoi que ce soit d'autre s'invoque ?**

Hypothese que cette mesure testerait : si c'est proche de 100 %, alors **n=4
est trop petit pour qu'une hierarchie de deduction ait une structure fine** --
seize cases se resolvent par la technique la plus faible, et aucune technique
intermediaire n'y changera rien.

**Ce serait un RESULTAT, pas un echec.** Il dirait que la profondeur n'est
mesurable qu'a n=5 ou n=6. Donc que le debit redevient le probleme -- et que
l'architecture A (etat de candidats explicite) se justifie par un chemin tout
autre que celui envisage jusqu'ici : non plus pour debloquer une technique
d'elimination, mais parce que le recalcul integral de `candidates()` devient
le goulot des qu'on quitte n=4.

**Non verifie / suppose** :
- Tout ce releve porte sur 150 systemes `-d4`. Les proportions peuvent changer
  d'un ordre de grandeur.
- L'interpretation "T0 arrive avant" est une **lecture**, pas une mesure : la
  mesure qui la testerait est celle listee ci-dessus, et elle n'est pas faite.
- Les 21 % de regions eligibles a d=4 viennent de systemes **regeneres**, pas
  des systemes exactement journalises.
- Rien n'exclut que T1 se declenche davantage sur un echantillon plus large.

**Bloque sur** : rien. Consigne : laisser tourner sans rien changer jusqu'a ce
que `connect-d4` et `static-d4` aient chacun **20 candidats**.

**Pour Claude chat** :
- Ce releve est **preliminaire et non concluant**. Ne pas le citer comme
  resultat, ni pour ni contre.
- T1 fonctionne a d=4 : elle n'a jamais ete cassee, seulement privee de
  domaine. Ne pas la "reparer".
- La question ouverte n'est plus "T1 a-t-elle un domaine" mais "**une
  hierarchie de deduction a-t-elle une structure fine a n=4**". Ce sont deux
  questions differentes et la seconde peut se conclure par un non qui serait
  un resultat.

## 2026-08-26 - absence de resultat, canary6 discrimine, file corrigee a d=4

**Demande** : traiter comme une absence de resultat le fait que seule une serie
NON REPRODUCTIBLE soit significative ; etendre `canary6` pour qu'une technique
doive **reclasser** et pas seulement se declencher ; ajouter deux
configurations a d=4 pour rendre a T1 un domaine.

**1. Le resume distingue desormais reproductible et non reproductible.**
`summarize.py` affiche **A NE PAS RETENIR** sur tout p significatif issu d'une
serie non reproductible, et ajoute une section de synthese
**"ce que les series reproductibles etablissent"**.

**RESULTAT QUI A CHANGE DEPUIS LA DEMANDE.** La premisse de la demande --
"aucune serie reproductible n'etablit l'ecart" -- **n'est plus vraie**. La
serie reproductible `89c65c03c4ad` a grossi pendant la nuit (17409 systemes,
2176 candidats) et **est devenue significative** :

    89c65c03c4ad  2176 candidats   REPRODUCTIBLE
      AVEC connectivite (862)  : T0=13,25  T2=2,87  pondere 5,75
      SANS connectivite (1314) : T0=15,89  T2=2,64  pondere 5,28
      p = 0,0010

    615abe43d6bc   945 candidats  p = 0,0060  NON REPRODUCTIBLE -> ecarte
    0327bdc4c76a   107 candidats  p = 0,1569  non significatif
    12564867381b    75 candidats  p = 0,8296  non significatif

Le code ecrit pour dire "aucune serie reproductible n'etablit l'ecart" dit donc
aujourd'hui l'inverse : **1 serie reproductible sur 3 l'etablit**. Les deux
branches existent et sont exercees ; ce n'est pas une absence de garde-fou.

Reserve : avec 2176 candidats, un ecart modeste devient significatif. La taille
d'effet est de +8,9 % sur le score pondere (5,75 contre 5,28). Le p dit que
l'ecart n'est pas du hasard, pas qu'il est important.

**2. `canary6` exige desormais que la technique RECLASSE.** Second controle :
comparer la distribution de `max_level` **avec et sans** le niveau le plus
eleve. Si elle est identique, la technique est un renommage et le canari
echoue.

**3. File corrigee.** `queue.json` passe de deux a **quatre** configurations :
`connect` et `static-ref` a d=3 (conservees), plus `connect-d4` et `static-d4`
a d=4.

**Cause reelle de la demande 3, consignee dans DECISIONS.md** : imposer d=3
pour corriger un biais de comparabilite -- correction juste et necessaire -- a
**supprime un niveau entier de deduction**. A n=4, un ALLDIFF sur 4 cases avec
3 valeurs est infaisable, donc `t1_regions()` est vide, donc T1 n'a plus de
domaine. Personne ne l'a vu pendant plusieurs heures : aucun canari ne
verifiait qu'une technique conserve un domaine dans l'espace explore, et
`max_level` ne distingue pas un T1 absent d'un T1 rare.

**Verifie** (execute et observe) :
- **Les six canaris passent depuis la racine ET depuis `engine/` : 12/12.**
- `canary6` controle B verifie **dans les deux sens** : il passe sur T2 (8
  systemes reclasses, {0:27, 1:2} -> {0:21, 2:8}) et **detecte l'egalite**
  quand on compare un niveau a lui-meme -- cas qui simule exactement une
  technique redondante.
- `queue.json` relu : 4 tags, `['connect', 'static-ref', 'connect-d4',
  'static-d4']`, `block_systems` inchange a 15.
- Redemarrage confirme (processus de 39 s) et **pathspec du scheduler present
  dans le code charge** : le commit de ce tour ne sera plus absorbe.
- `summarize.py` exerce ses deux branches de synthese.

**Non verifie / suppose** :
- **Les tags `-d4` n'ont pas encore tourne.** La file est relue au cycle
  suivant ; aucun enregistrement `connect-d4` ni `static-d4` n'existe. Que T1
  retrouve effectivement un domaine a d=4 est **une prediction**, appuyee sur
  la mesure de 21 % de regions eligibles a d=4 sur `baseline`, pas sur un run.
- Le test de permutation suppose l'echangeabilite sous H0 ; les candidats d'une
  meme serie partagent generateur et graines. Le p reste indicatif.
- Aucune correction pour tests multiples (4 series testees).
- La taille d'effet n'est pas assortie d'un intervalle de confiance.
- La contradiction a propagation bornee reste **non codee**, sur consigne : si
  T1 retrouve un domaine a d=4, le trou se comble peut-etre seul.

**Bloque sur** : rien. Aucun redemarrage requis -- `queue.json` est relu a
chaque cycle, `summarize.py` et les canaris a chaque bloc.

**Pour Claude chat** :
- La file compte **quatre** tags. Un `summary.md` sans `connect-d4` /
  `static-d4` signifie que la rotation ne les a pas encore atteints, pas qu'ils
  ont echoue.
- **L'ecart est desormais etabli sur une serie reproductible** (`89c65c03c4ad`,
  p = 0,0010). C'est le premier resultat rejouable du projet sur l'hypothese
  centrale -- mais il porte sur l'EFFORT de deduction, pas sur la profondeur,
  et la taille d'effet est modeste (+8,9 %).
- Un p significatif marque **A NE PAS RETENIR** vient d'une serie dont le
  moteur n'existe plus : ne pas le citer.
- Une technique de deduction doit **creer un palier, pas deplacer une
  etiquette**. `canary6` le verifie maintenant.

## 2026-08-26 - le scheduler absorbait les commits de travail

**Constat** : apres avoir prepare le commit du tour precedent
(`git add -A`), `git commit` a repondu *nothing to commit, working tree
clean*. Les changements n'etaient pas perdus -- ils avaient ete **commites et
pousses par le scheduler** sous `a5725ba auto: resume connect`, avec le mauvais
message et l'auteur `rulesearch@local`.

**Cause reelle** : `scheduler.py` faisait

    git add -A summary.md found/ && git commit -m 'auto: resume <tag>'

Le `git add` est bien restreint a ses chemins, mais le **`git commit` ne l'est
pas** : sans pathspec, il valide **tout l'index**, donc aussi ce qu'une session
concurrente y avait mis en attente. Le scheduler tournant sur le meme arbre de
travail, tout `git add` d'une session agent devient sa propriete au bloc
suivant.

C'est la **meme classe de defaut** que les hashs orphelins corrigee plus haut :
le serveur opere sur un arbre de travail partage. Le gel de `engine/` reglait
la lecture du code ; celui-ci concerne l'index git.

**Correction** : pathspec ajoute en fin de commande --
`git commit ... -- summary.md found/`. Le scheduler ne peut plus valider que
ses propres fichiers, quoi qu'il y ait d'autre dans l'index.

**Verifie** :
- `ast.parse` sur `scheduler.py`.
- Le contenu du tour precedent est bien present dans `HEAD` et sur `origin`
  (test de permutation dans `summarize.py`, entrees `DECISIONS.md` et
  `WORKLOG.md`) : **rien n'a ete perdu**, seule l'attribution est fausse.

**Non verifie / suppose** :
- Le correctif n'a **pas encore tourne** : le scheduler garde l'ancien code en
  memoire jusqu'au prochain redemarrage. D'ici la, le comportement d'absorption
  persiste.
- Combien de commits anterieurs ont absorbe du travail de la sorte n'a pas ete
  recherche. `a5725ba` est le seul identifie.
- L'historique n'est pas reecrit : `a5725ba` garde son message trompeur. Le
  corriger demanderait une reecriture d'historique, non faite -- DECISIONS.md
  et ce journal portent l'information.

**Bloque sur** : `sudo` refuse. **Demande a Mrawdian : `sudo systemctl restart
rulesearch`** pour activer le correctif.

**Pour Claude chat** :
- Un commit `auto: resume <tag>` **peut contenir du travail qui n'est pas du
  scheduler**, pour les commits anterieurs au 26/08/2026. Ne pas se fier au
  message pour dater un changement : croiser avec `git log -- <fichier>`.
- Sur cet arbre partage, ne jamais laisser des fichiers en attente dans l'index
  entre deux operations : commiter immediatement apres `git add`.

## 2026-08-26 - T1 est SANS DOMAINE, test de significativite, gel verifie

**Demande** : confirmer la cause des 0 invocations de T1 avant de traiter le
symptome ; evaluer sans coder une technique intermediaire ; ajouter un test de
significativite a la mesure continue ; verifier le gel de `engine/` en cycle
reel.

**1. Cause confirmee, plus radicale que le diagnostic initial.**

    connect     n=4 d=3   0 systeme sur 600 avec region T1 eligible, 0 ALLDIFF
    static-ref  n=4 d=3   0 systeme sur 590,                          0 ALLDIFF
    baseline    n=4 d=4   126 sur 600 (21 %), 1308 ALLDIFF dont 322 de taille d

Sur les enregistrements : `connect` 0 %, `ref` 0 %, `baseline` 38,7 % citant
ALLDIFF.

Ce n'est pas "quasiment aucun" mais **exactement zero**, et pas seulement zero
region *eligible* : **zero contrainte ALLDIFF generee**, y compris par la
famille `static`. La raison est le principe des tiroirs et elle precede la
restriction de `t1_regions()` : a n=4, les regions structurelles ont 4 cases ;
avec d=3, un ALLDIFF sur 4 cases et 3 valeurs est infaisable, le generateur
n'en produit donc aucun. Et meme s'il en produisait, `t1_regions()` exige une
taille exactement d=3 que ces regions n'ont pas.

**T1 n'est ni fausse ni inerte : elle est SANS DOMAINE** dans l'espace que la
file explore. Elle redevient utile des que d egale la taille des regions --
cas de `baseline` a d=4. C'est le passage de la file a d=3 qui l'a eliminee.

**2. Technique proposee evaluee, NON codee : elle serait REDONDANTE.**

La proposition -- supposer v, saturer **T0 seul** au lieu de T0+T1, eliminer
sur contradiction -- part de l'idee que ce serait un T2 affaibli. Or
`apply_T1` parcourt `t1_regions(rs)` qui est **vide** : la boucle ne s'execute
jamais, la fonction rend `(False, False)`. Donc `saturate_low()` **est deja
exactement T0 seul** dans cet espace.

La technique proposee est donc **T2 a l'identique**, pas une version affaiblie.
Elle se declencherait aux memes endroits, sur les memes systemes. Inseree comme
palier intermediaire, elle reclasserait tous les T2 actuels et laisserait T2
vide : un renommage, pas un palier. Et **`canary6` la validerait** puisqu'elle
s'invoque bien -- piege plus retors que l'inertie, parce qu'elle aurait l'air
de marcher.

Piste proposee a la place, non codee : **contradiction a propagation bornee** --
supposer v, appliquer **une seule passe** de T0 au lieu d'iterer jusqu'au point
fixe. Strictement plus faible que T2 (les contradictions n'apparaissant qu'apres
plusieurs passes lui echappent), strictement plus forte que T0, et sans
dependance a une structure de region.

**Manque outillage** : `canary6` verifie qu'une technique se declenche, pas
qu'elle **discrimine**. Une technique redondante passe le canari. Il faudrait y
ajouter une comparaison de la distribution de `max_level` avant/apres.

**3. Test de significativite (test de permutation, stdlib seule).**

    615abe43d6bc  945 candidats  p = 0.0060  significatif
    89c65c03c4ad  213 candidats  p = 0.7586  NON SIGNIFICATIF
    0327bdc4c76a  107 candidats  p = 0.1569  NON SIGNIFICATIF
    12564867381b   75 candidats  p = 0.8296  NON SIGNIFICATIF
    12a0c0c5e34b   31 candidats  groupes trop petits, aucun test

**Une seule serie sur quatre est significative.** Mon "meme sens sur trois
series sur quatre" du tour precedent etait exactement la lecture que CLAUDE.md
interdit : une tendance jolie prise pour un resultat.

**Et la seule serie significative est `615abe43d6bc`, marquee NON
REPRODUCTIBLE.** Le seul resultat statistiquement solide provient du moteur
dont la source n'existe plus. Il n'est pas rejouable.

**Verifie** (execute et observe) :
- **Les six canaris passent depuis la racine ET depuis `engine/` : 12/12.**
- **Le gel a tourne en cycle reel** : `.engine-run/` cree a 23:18 au demarrage
  du cycle, et `RS_ENGINE=/home/rulesearch/rulesearch/.engine-run` lu
  directement dans `/proc/<pid>/environ` du `run.py` en cours.
- **Aucun nouveau hash orphelin** depuis le redemarrage : toujours six, pas de
  septieme. L'hemorragie est arretee.
- `89c65c03c4ad` est desormais **reproductible** (commit `d8f541a`) : c'est la
  serie de production courante, 1602 systemes et en croissance.
- Part non reproductible retombee de 83 % a **71 %**, par dilution.
- `summarize.py` : 0,52 s avec 2000 permutations par serie.

**Non verifie / suppose** :
- La mesure du domaine de T1 porte sur des systemes **regeneres** avec les
  memes familles et graine fixe, pas sur les systemes exactement journalises --
  les objets `RuleSystem` ne sont pas conserves dans les journaux. Le taux
  observe sur les etiquettes (0 % d'ALLDIFF cite) concorde.
- La redondance de la technique proposee est **demontree par lecture du code**
  (`t1_regions` vide donc `apply_T1` no-op), pas mesuree.
- La contradiction a propagation bornee est une **piste**, ni implementee ni
  testee. Rien ne garantit qu'elle cree un palier plutot qu'un renommage.
- Le test de permutation suppose l'echangeabilite sous H0. Les candidats d'une
  meme serie ne sont pas independants (memes graines, meme generateur) : le p
  est indicatif, pas une garantie formelle.
- Aucune correction pour tests multiples n'est appliquee : quatre series
  testees, un p a 0,006 -- une correction de Bonferroni le laisserait
  significatif, mais ce n'est pas calcule.

**Bloque sur** : rien. `sudo` reste refuse mais aucun redemarrage n'est requis
par ce tour -- `summarize.py` et la documentation sont relus a chaque bloc, et
`engine/` n'a pas change.

**Pour Claude chat** :
- **T1 est sans domaine, pas cassee.** Ne pas la "reparer" : elle fonctionne
  des que d egale la taille des regions. C'est la file a d=3 qui l'exclut.
- **`saturate_low()` = T0 seul** dans l'espace explore. Toute technique definie
  comme "T2 avec T0 seul" est identique a T2. Ne pas la proposer.
- Une technique peut passer `canary6` **en etant redondante** : se declencher
  n'est pas discriminer. Le canari ne couvre pas ce cas.
- **L'ecart de la mesure continue n'est significatif que sur une serie sur
  quatre**, et c'est la serie non reproductible. Ne pas le citer comme
  resultat acquis.
- Le gel de `engine/` est actif et verifie en production.

## 2026-08-26 - T3 retire, engine gele par cycle, metrique continue

**Demande** : retirer `apply_T3` ; marquer les series non reproductibles sans
les purger ; purger `__pycache__` au demarrage ; faire tourner le serveur sur
une copie figee de `engine/` ; sortir la distribution des niveaux.

**Cause reelle (series orphelines)** : `scheduler.py` relance `run.py` a chaque
bloc et `run.py` reimportait `engine/` **depuis le repertoire de travail**.
Toute edition en cours etait donc captee a mi-chemin par le bloc qui demarrait.
Six `dsl_hash` distincts en une journee, dont un -- `615abe43d6bc`, 7172
enregistrements, 80 % des donnees -- dont la source n'existe nulle part. Un
sixieme (`89c65c03c4ad`) est apparu **pendant la redaction de ce correctif**,
ce qui confirme le diagnostic.

**Correction** :
- `engine/deduction.py` : `apply_T3` **retire** (code mort). La docstring
  explique desormais pourquoi il n'y a pas de T3 et renvoie a DECISIONS.md.
  `uses` revient a {0,1,2}.
- `canary/canary3.py` : revient a T0/T1/T2.
- `run.py` : le moteur est charge depuis `RS_ENGINE` si defini, sinon
  `HERE/engine`. **`dsl_hash()` hache ce meme repertoire** -- le hash decrit
  donc le code reellement charge. Purge du `__pycache__` du moteur au
  demarrage. Canaris lances avec le meme `ENGINE`.
- `scheduler.py` : `geler_engine()` copie `engine/` vers `.engine-run/` au
  debut de chaque cycle (copie dans `.tmp` puis `os.rename`, bascule
  atomique) et passe `RS_ENGINE` au sous-processus.
- `.gitignore` : `.engine-run/`.
- `summarize.py` : marquage **NON REPRODUCTIBLE** de tout `dsl_hash` absent de
  l'historique git, avec total et pourcentage ; nouvelle section
  **profondeur en continu**.

**Verifie** (execute et observe) :
- **Les six canaris passent depuis la racine ET depuis `engine/` : 12/12.**
- `geler_engine()` produit bien `.engine-run/` avec les quatre modules.
- `RS_ENGINE` de bout en bout : `run.py` charge depuis la copie figee et rend
  le **meme hash** que depuis `engine/` quand les deux sont identiques
  (`89c65c03c4ad`).
- `summarize.py` marque 3 hashs sur 6 comme non reproductibles, soit 7483
  enregistrements (83 %). Duree : 0,16 s -- le calcul des hashs git ne
  ralentit pas le resume.
- Comportement sans `RS_ENGINE` inchange.

**AUCUN HASH NE MENT.** Test : un meme `dsl_hash` portant deux formes de
`level_uses` (`0,1,2` avant T3, `0,1,2,3` apres) prouverait qu'il couvre deux
versions de code. Chaque hash ne porte qu'**une seule** forme. L'invariant 2 a
tenu, et rien de ce qui a ete conclu aujourd'hui ne s'effondre. `uses[3] > 0`
sur **zero** enregistrement : T3 n'a jamais rien produit en production.

**DISTRIBUTION DES NIVEAUX -- il existe une sortie sans reecrire le moteur.**
Sur 1143 candidats, `max_level` vaut T2 pour **100 %**. Mais en continu :

    serie 615abe43d6bc, 945 candidats
      AVEC connectivite (397) : T0=12,99  T1=0,00  T2=2,95  pondere 5,90
      SANS connectivite (548) : T0=15,85  T1=0,00  T2=2,67  pondere 5,34

Plus de T2 et moins de T0 pour les systemes a connectivite : le sens predit par
l'hypothese. Ecart faible, **meme sens sur 3 series sur 4** (la 4e, n=53,
s'inverse). Une metrique continue discrimine donc la ou le seuil sature.

**T1 N'A JAMAIS ETE INVOQUEE** -- zero sur 8991 enregistrements, toutes series.
La hierarchie effective en production est **T0/T2**. Le niveau intermediaire
est vide, ce qui explique en partie la saturation. T1 n'est pas inerte au sens
de T3 (`canary6` la voit se declencher sur `cages+sum`) : elle est sans emploi
dans l'espace explore. Piste : combler le trou T0-T2 couterait bien moins cher
qu'une reecriture du moteur.

**Non verifie / suppose** :
- Le test "aucun hash ne ment" est **incomplet** : il ne detecte que les
  melanges observables dans les enregistrements. L'episode du `__pycache__`
  perime (`DEFAULT_MAX_LEVEL` 3 au lieu de 2) lui est structurellement
  invisible -- sans consequence toutefois, T3 n'ayant jamais ete invoque, le
  comportement execute etait identique a celui de la source etiquetee.
- **Le gel n'a pas encore tourne en production** : le scheduler garde l'ancien
  code en memoire. Verifie par appel direct de `geler_engine()`, pas par un
  cycle reel.
- L'ecart continu (5,90 contre 5,34) n'a fait l'objet d'**aucun test
  statistique**. Il est faible et pourrait etre du bruit.
- La metrique continue mesure l'**effort** de deduction, pas la profondeur au
  sens d'une hierarchie de techniques.
- Le cout du gel (copie de 4 fichiers par cycle) n'est pas chronometre.

**Bloque sur** : `sudo` refuse. **Demande a Mrawdian :
`sudo systemctl restart rulesearch`** -- c'est le redemarrage qui active le gel
et **arrete la creation de nouveaux hashs orphelins**. Tant qu'il n'a pas eu
lieu, toute edition d'`engine/` continue d'etre captee a mi-chemin.

**Pour Claude chat** :
- **Il n'y a pas de T3 et il ne faut pas en proposer un par elimination.** Deux
  l'ont ete, retirees. Seules les techniques qui POSENT une valeur marchent.
- **T1 est sans emploi en production.** Ne pas raisonner sur une hierarchie a
  trois niveaux : elle en a deux, T0 et T2.
- `max_level >= 2` **ne discrimine plus** (100 % partout). La mesure utilisable
  est la section **profondeur en continu** de `summary.md`.
- Un `dsl_hash` marque **NON REPRODUCTIBLE** designe une donnee valide mais non
  rejouable. Ne pas la citer comme reproductible ; ne pas la purger non plus.
- Le moteur tourne desormais depuis `.engine-run/`, copie figee. `RS_ENGINE`
  pointe le moteur reellement charge, et c'est lui que `dsl_hash` hache.

## 2026-08-26 - AVERTISSEMENT : 7172 enregistrements produits sous un code jamais commite

**Constat**, decouvert en verifiant l'etat de `runs/` apres le commit
`b152e57`. Cinq `dsl_hash` distincts coexistent :

    615abe43d6bc : 7172 enregistrements   <-- 84 % des donnees
    0327bdc4c76a :  853
    12a0c0c5e34b :  294
    12564867381b :  284   <-- etat commite actuel
    6680f7b47e6f :  124

**Cause reelle** : `engine/` a ete modifie **en place, sur un arbre de
production en marche**. `scheduler.py` relance `run.py` en sous-processus a
chaque bloc, et `run.py` reimporte `engine/` a chaque fois. Chaque etat
intermediaire de mes editions successives -- ajout de la paire nue, ajout de
`DEFAULT_MAX_LEVEL`, remplacement par la paire cachee, retouche de
commentaires -- a donc ete **capte et execute par la production**, produisant
une serie par etat.

`615abe43d6bc` correspond a un etat transitoire dont **la source n'existe plus
nulle part** : ni dans git, ni sur le disque. 7172 enregistrements, soit la
grande majorite des donnees accumulees, sont rattaches a un code irrecuperable.

**Ce qui n'est PAS casse** : `dsl_hash` a fait exactement son travail. Les
series sont separees, `summary.md` les liste et rappelle qu'elles ne sont pas
comparables. Aucune conclusion n'a melange deux hashs. L'invariant 2 a tenu.

**Ce qui est perdu** : le temps machine, et la reproductibilite de la plus
grosse serie. L'analyse de saturation rapportee plus haut (437 candidats avec
connectivite, 621 sans, 100 % de T2 des deux cotes) provient de cette serie.
La conclusion reste valide -- T3 n'ayant jamais ete invoque, le comportement
etait identique a `DEFAULT_MAX_LEVEL = 2` -- mais elle n'est pas rejouable a
l'identique.

**Erreur de methode, a moi** : editer `engine/` pendant que le service tourne.
Il aurait fallu arreter le service, editer, verifier, puis redemarrer. Le
`sudo` refuse rendait l'arret impossible, ce qui aurait du etre une raison de
**grouper les editions** au lieu de les enchainer.

**Non verifie / suppose** :
- L'attribution de chaque hash a un etat precis du code est **deduite de la
  chronologie**, pas verifiee : les sources intermediaires n'existent plus.
- Non verifie si des fichiers de `found/` portent un hash orphelin ; c'est
  probable, les noms sont prefixes par le hash.
- Non verifie si l'episode de `__pycache__` perime a produit des
  enregistrements sous un hash ne correspondant pas au code reellement
  execute. C'est possible, et ce serait plus grave que le reste : le hash
  mentirait au lieu de simplement pointer une source disparue.

**Decision en attente de l'utilisateur** : purger les series a hash orphelin,
ou les conserver. Elles sont inoffensives pour les conclusions puisque
separees, mais elles gonflent `summary.md` et le temps de `summarize.py`.

**Pour Claude chat** :
- **Ne jamais editer `engine/` pendant que le service tourne.** Chaque
  sauvegarde intermediaire devient une serie distincte executee en production.
- Un `dsl_hash` present dans `summary.md` ne garantit pas que la source
  correspondante existe encore. `615abe43d6bc` n'est retrouvable nulle part.
- La serie de reference actuelle est **`12564867381b`**, la seule qui
  corresponde a un commit.

## 2026-08-26 - T2 sature, T3 inerte deux fois, canary6, verdict neutralise

**Demande** : neutraliser le verdict quand l'indicateur sature ; implementer T3
(paire nue, puis paire cachee) ; en faire un canari de declenchement ;
consigner le motif.

**Trois causes reelles distinctes.**

**1. T2 a sature et le resume mentait.** Sur 8146 enregistrements, 437
candidats avec connectivite et 621 sans : la fraction atteignant T2 vaut
**100 % dans les deux groupes**. La regle `a < b + 0.05` etant satisfaite par
1,0 < 1,05, `summarize.py` imprimait **"l'hypothese ne tient pas"** -- une
refutation jamais etablie. Saturation n'est pas absence d'effet. Corrige :
INDICATEUR SATURE, et refus explicite de conclure dans les deux sens.

**2. T3 est inerte, DEUX FOIS, et la cause est un theoreme.** Paire nue puis
paire cachee : les deux implementees, restreintes a `t1_regions()` pour ne pas
refaire le bug T1, les deux verifiees correctes par `canary3` sur les cinq
familles -- et les deux a **0 invocation**.

Le moteur n'a aucune representation des candidats : `candidates()` les
recalcule depuis `feasible()`. Il n'existe nulle part ou inscrire une
elimination. Une technique d'elimination ne peut donc produire d'effet que si
elle reduit une cellule a une seule valeur, cas deja traite par T0. Pour la
paire cachee la demonstration est directe : si u et v n'ont que les cases
{i,j}, alors u et v sont candidats en i comme en j, donc l'elimination laisse
exactement deux candidats, jamais un ; et le cas a un seul est un hidden
single, deja capture par T1.

**Erreur de ma part, a consigner comme telle** : l'utilisateur avait identifie
cette cause pour la paire nue, et j'ai recommande une seconde technique
d'ELIMINATION. La distinction que j'avais faite -- "le hidden pair pose de
l'information sur les valeurs" -- etait verbale, pas structurelle. Sa
conclusion operationnelle reste une elimination.

**Regle qui en decoule** : seules les techniques qui POSENT une valeur ("la
case k vaut v") peuvent fonctionner sur ce moteur. T0, T1, T2 en sont.

**3. Bytecode perime.** La source portait `DEFAULT_MAX_LEVEL = 2`, `grep` le
confirmait, l'import rendait **3**. Un `engine/__pycache__` produit pendant un
test ou la constante valait 3 continuait d'etre servi -- taille de fichier
identique, seul le chiffre differant. `dsl_hash` ne hache que les `.py` : un
journal peut donc porter le hash d'une source qui n'a pas tourne. C'est
exactement ce que `dsl_hash` existe pour empecher.

**Correction** :
- `summarize.py` : INDICATEUR SATURE quand les deux groupes sont a 100 % ou a
  0 %.
- `engine/deduction.py` : `DEFAULT_MAX_LEVEL = 2` (constante nommee),
  `solve_graded` l'utilise par defaut. `apply_T3` = paire cachee, correcte,
  restreinte a `t1_regions()`, **desactivee**.
- `canary/canary6.py` (nouveau) : exige que toute technique de niveau <=
  `DEFAULT_MAX_LEVEL` s'invoque au moins une fois sur trois cas de reference.
  Les niveaux au-dela sont mesures a titre informatif sans faire echouer.
- `canary/canary3.py` : etendu a T3.
- `run.py` : `canary6.py` enregistre ; `uses_acc` etendu a T3.
- `CLAUDE.md` : invariants 6 et 7, section sur l'impossibilite des techniques
  d'elimination, section sur le risque asymetrique de l'option A, purge de
  `__pycache__` ajoutee a l'invariant 1.
- `DECISIONS.md` : quatre entrees.

**Verifie** (execute et observe) :
- **Les six canaris passent depuis la racine ET depuis `engine/` : 12/12.**
- `canary6` verifie **dans les deux sens** : il passe a
  `DEFAULT_MAX_LEVEL = 2`, et **echoue** (exit 1) si on le porte a 3 sans
  rendre T3 operante. L'invariant mord donc reellement.
- Invocations sur les cas de reference : T0 = 73, T1 = 2, T2 = 8, **T3 = 0**.
- `canary3` : DIVERGENCES=0 sur les cinq familles, avec la paire cachee active
  dans la boucle -- elle est correcte, elle est seulement inerte.
- Le resume imprime desormais INDICATEUR SATURE au lieu de la fausse
  refutation.
- Le `__pycache__` perime a ete reproduit puis purge ; apres purge l'import
  rend bien 2.

**dsl_hash : `0327bdc4c76a` -> `12564867381b`.** `engine/deduction.py` a
change, donc la serie repart. **A noter : le comportement a
`DEFAULT_MAX_LEVEL = 2` est INCHANGE** -- T3 est desactive. Les 8146
enregistrements deviennent donc incomparables aux suivants pour un changement
sans effet observable. `dsl_hash` hachant les fichiers entiers, un commentaire
suffit a rompre la comparabilite. Cout reel, non signale ailleurs.

**Non verifie / suppose** :
- Le repli (contradiction a profondeur 2) n'a **pas** ete code, sur consigne
  explicite. Son cout multiplicatif estime -- T2 imbrique dans T2, facteur
  anticipe 50 a 200 -- est un **raisonnement, pas une mesure**.
- La regle "seules les techniques de POSE fonctionnent" est demontree pour les
  deux techniques essayees ; elle est enoncee en general sans preuve generale.
- `canary6` repose sur trois cas de reference. T1 n'y est invoquee que 2 fois :
  deterministe (graines fixes) mais mince.
- La purge de `__pycache__` n'est **pas automatisee** : elle touche au chemin
  de production, non fait sans accord.
- Aucune conclusion sur l'hypothese centrale n'est possible tant que la mesure
  sature.

**Bloque sur** : `sudo` refuse ; redemarrage a demander a Mrawdian. Deux
questions en attente de l'utilisateur : retirer ou non `apply_T3` desormais
inerte, et automatiser ou non la purge de `__pycache__`.

**Pour Claude chat** :
- **Ne jamais proposer de technique de deduction par ELIMINATION.** Elle sera
  inerte, quelle que soit sa correction. Deux l'ont deja ete. Seules les
  techniques qui POSENT une valeur fonctionnent sur ce moteur.
- Un verdict "l'hypothese ne tient pas" produit alors que les deux groupes sont
  a 100 % est un **artefact de saturation**, pas un resultat. Le resume le dit
  desormais lui-meme.
- Apres toute modification de `engine/`, **purger `__pycache__`** avant de
  mesurer quoi que ce soit.
- `dsl_hash` = `12564867381b`. Les 8146 enregistrements precedents portent
  `0327bdc4c76a` et **ne se comparent pas** aux nouveaux.
- L'option A (etat de candidats explicite) est la seule voie connue vers une
  metrique non saturee, et elle est **differee, pas abandonnee**. Lire la
  section sur le risque asymetrique avant de la rouvrir.

## 2026-08-25 19:50 - ventilation intra-connect et censure de l'echantillon

**Demande** : ventiler les TROP-CHER a l'interieur du seul tag `connect`,
marquer la ligne globale comme confondue, et faire apparaitre dans le resume
que la borne de temps **censure l'echantillon dans le sens qui defavorise
l'hypothese**.

**Cause reelle (du besoin)** : la ligne "22 TROP-CHER, dont 22 avec CONNECTED,
0 sans" etait **confondue par construction**. `static-ref` ne tire que des
familles `static` : aucun de ses systemes ne peut contenir CONNECTED. Le ratio
melangeait donc l'effet de la connectivite et celui de la configuration, et
n'etablissait rien.

**Correction** (`summarize.py`) :
- ligne globale conservee mais **explicitement marquee CONFONDUE**, avec le
  motif et un renvoi vers la ventilation.
- **ventilation a configuration egale** : taux de TROP-CHER dans le seul tag
  `connect`, ou les deux types de systemes coexistent, avec et sans CONNECTED.
  Avertissement automatique si l'un des groupes compte moins de 20 systemes.
- nouvelle section **"censure de l'echantillon"** dans la partie hypothese :
  nombre et fraction des systemes CONNECTED abandonnes, puis le raisonnement
  en clair -- les abandonnes sont les plus couteux, donc vraisemblablement les
  plus profonds, donc ceux que l'hypothese predit comme atteignant T2 ;
  l'echantillon est tronque du cote que l'hypothese predit et la troncature
  joue **contre** elle ; tout ecart favorable observe est une **borne
  inferieure** ; **un ecart faible ou nul ne refute pas l'hypothese**.

`DECISIONS.md` : entree posant que la borne de 20 s n'est pas qu'une protection
de debit mais un **filtre qui biaise l'echantillon**, avec le critere de
reouverture demande -- au-dela de **20 % de systemes CONNECTED abandonnes**, la
borne detruit la mesure et devra etre remontee, ou ces systemes traites a part
dans une file a budget long plutot que jetes.

**Verifie** (execute et observe, sur 635 enregistrements) :
- ventilation a configuration egale, dans le seul tag `connect` :
  **avec CONNECTED 13,7 % sur 219 systemes, sans CONNECTED 0,0 % sur 47**.
  Le signal survit donc au controle de configuration -- c'est la premiere
  mesure non confondue sur cette question.
- censure : **30 systemes CONNECTED sur 276 (10,9 %) abandonnes**. Sous le
  seuil de reouverture de 20 %, mais du meme ordre de grandeur : a surveiller.
- cout : 30 TROP-CHER, soit 4,7 % des systemes pour **95 % du temps total**.
- part du temps sur les MORT tombee a **3 %** (contre 68 % avant le
  pre-filtre).
- `summarize.py` re-parse et tourne sans regression.

**Reserve importante sur le verdict affiche** : le resume imprime
"l'hypothese ne tient pas" alors que les deux groupes sont a **T2 100 %**
(31 candidats avec connectivite, 50 sans). Le test compare `a < b + 0.05` ;
avec a = b = 1,0 il conclut a l'absence d'ecart. Mais **100 % contre 100 %
n'est pas une absence d'effet : c'est une saturation de l'indicateur**.
`max_level >= 2` ne discrimine plus rien quand tous les candidats atteignent
T2. Ce verdict ne doit pas etre lu comme une refutation. Non corrige :
l'utilisateur a demande de laisser tourner sans rien changer. **A trancher
plus tard** -- il faudra un indicateur qui ne sature pas (T3, ou une mesure
continue de profondeur).

**Non verifie / suppose** :
- Les 13,7 % contre 0,0 % reposent sur 47 systemes seulement dans le groupe
  sans CONNECTED. L'ecart est net mais l'echantillon du groupe temoin est
  mince.
- Le lien "couteux donc profond" est une **hypothese de travail**, pas un fait
  mesure : rien ne prouve que les systemes abandonnes auraient atteint T2.
  C'est precisement pourquoi le resume parle de borne inferieure et non
  d'estimation.
- Aucun des 30 systemes abandonnes n'a ete evalue avec un budget long pour
  verifier ce qu'il aurait donne.

**Bloque sur** : rien de nouveau. `sudo` reste refuse ; un redemarrage reste
souhaitable pour que `run_canaries()` joue `canary5`, sans quoi rien n'est
casse.

**Pour Claude chat** :
- **Ne jamais lire la ligne globale "TROP-CHER dont N avec CONNECTED" comme un
  resultat.** Elle est confondue et marquee comme telle. La seule comparaison
  valide est la ventilation dans le tag `connect`.
- La section **"censure de l'echantillon"** doit etre lue avant tout verdict
  sur l'hypothese. Un ecart T2 faible ou nul **ne refute rien** tant que des
  systemes CONNECTED sont abandonnes : la borne de temps retire de
  l'echantillon precisement les cas favorables a l'hypothese.
- Surveiller la fraction de CONNECTED abandonnes. **Au-dela de 20 %**, la
  mesure n'est plus exploitable (critere inscrit dans `DECISIONS.md`).
  Actuellement 10,9 %.
- Le verdict automatique "l'hypothese ne tient pas" est **actuellement
  trompeur** : il se declenche aussi quand les deux groupes saturent a 100 %
  de T2, ce qui est le cas. Saturation n'est pas absence d'effet.
- Consigne de l'utilisateur : **laisser tourner sans rien changer** jusqu'a
  plusieurs centaines de systemes par groupe.

## 2026-08-25 19:35 - canary5, garde permanente de l'interruption par alarme

**Demande** : verser au depot le test du declenchement de l'alarme, avec en
plus une verification de faux positif ; l'enregistrer dans `run_canaries()` et
le documenter. Consigner par ailleurs comme question ouverte l'observation sur
`count_solutions`.

**Cause reelle** : le chemin d'interruption avait deja echoue **en silence**.
Une borne testee entre les appels ne pouvait pas interrompre un blocage
survenant dans un appel, et `summary.md` affichait `TROP-CHER : 0` -- lisible a
tort comme "aucun systeme trop cher". Un chemin de code sans canari peut
retomber dans cet etat sans que rien ne le signale.

**Correction** :
- `canary/canary5.py` (nouveau). Deux verifications symetriques :
  - **A, faux negatif** : `minimal_clues` remplace par une boucle de calcul
    pur, sans appel systeme ni test d'heure, que seul un signal peut
    interrompre. Exige un TROP-CHER en `phase == "minimal_clues"` avec
    `interrompu == True`, dans le budget imparti.
  - **B, faux positif** : avec le vrai `minimal_clues` et un budget large,
    aucun record ne doit porter TROP-CHER sans avoir reellement consomme son
    budget. Un systeme sain etiquete TROP-CHER disparaitrait des candidats
    sans laisser de trace -- exactement le mode de defaillance du pre-filtre
    surveille par `canary4`.
  - verifie en outre que l'alarme est **desarmee entre deux systemes** : si
    tous les systemes ressortaient TROP-CHER, `signal.alarm(0)` manquerait.
- `run.py` : `canary5.py` ajoute a la liste de `run_canaries()`.
- `README.md` : section Canaris listant les cinq, avec le role de chacun.
- `CLAUDE.md` : canary5 mentionne comme garde de l'interruption, et nouvelle
  section **Question ouverte : le budget de noeuds de count_solutions**.

**Isolation du canari** : `canary5` redirige `run.HERE` vers un repertoire
temporaire et y lie `engine/` symboliquement. Il n'ecrit donc ni dans `runs/`,
ni dans `found/`, ni dans `summary.md`. Verifie : aucun repertoire `canary5*`
dans `runs/` apres dix executions.

**Verifie** (execute et observe) :
- **Les cinq canaris passent depuis la racine ET depuis `engine/` : 10/10,
  exit 0.** `canary5` : `OK : aucun faux negatif, aucun faux positif.`
- `canary5` passe aussi sous **pypy3**, l'interpreteur de production.
- Detail d'une execution : partie A, 40 systemes, 16 TROP-CHER dont plusieurs
  en `phase=minimal_clues` a `elapsed_s=3.0`, et **24 systemes evalues
  normalement** apres interruption -- l'alarme est bien desarmee entre deux
  systemes. Partie B, 12 systemes, **0 TROP-CHER**.
- `dsl_hash` inchange : **`0327bdc4c76a`**. `canary5.py` est dans `canary/`,
  pas dans `engine/`.

**Question ouverte consignee, non tranchee** : en partie A, seul
`minimal_clues` avait ete truque, et pourtant des systemes ont ete interrompus
en `phase == "count_solutions"`. Si cette fonction peut consommer 3 s alors
qu'elle possede un budget de **noeuds**, ce budget ne borne pas ce qu'on croit
-- ce serait un **defaut du solveur**, pas une lenteur. `CLAUDE.md` le consigne
avec la consigne explicite de **ne pas toucher au solveur** avant d'avoir la
distribution du champ `phase` sur les vrais TROP-CHER de production.

**Non verifie / suppose** :
- L'observation sur `count_solutions` vient d'un **banc**, pas de donnees de
  production. Elle peut etre un artefact du cas artificiel. C'est une question,
  pas un resultat.
- `canary5` ajoute au demarrage un cout non mesure precisement, de l'ordre de
  la minute (la partie A accumule des attentes de 3 s). Les canaris ne tournent
  qu'une fois par vie du scheduler -- `--skip-canary` ensuite -- donc le cout
  est paye une fois par redemarrage, pas par bloc. Non chronometre.
- La partie B pourrait devenir lente si le generateur tombait sur un systeme
  reellement pathologique ; borne a 30 s par systeme, mais non observe.
- Aucun TROP-CHER de production n'a encore ete examine.

**Etat de la production, constate au passage** : le service a ete redemarre.
`runs/` contient desormais une quinzaine de repertoires horodates 19:28-19:31
alternant **`connect` et `static-ref`** -- la rotation fonctionne enfin, les
deux tags tournent, et les blocs s'achevent en quelques secondes au lieu de
geler. `found/` est passe a 38 fichiers. Non analyse en detail a ce stade.

**Bloque sur** : rien de nouveau. `sudo` reste refuse ; un redemarrage sera
necessaire pour que `run_canaries()` prenne `canary5` en compte, mais **rien
n'est casse sans lui** : le canari existe et passe, il n'est simplement pas
encore joue automatiquement au demarrage.

**Pour Claude chat** :
- Il y a maintenant **cinq** canaris. `canary5` garde le chemin
  d'interruption, dans les deux sens : ne pas le retirer, il couvre une panne
  qui s'est deja produite en silence.
- `canary5` est **lent** (de l'ordre de la minute) : c'est normal, il attend
  reellement des expirations de budget. Ne pas l'interpreter comme un blocage.
- Il s'execute dans un repertoire temporaire : s'il apparait un jour un tag
  `canary5a` ou `canary5b` dans `summary.md`, c'est que son isolation a casse.
- La question ouverte sur `count_solutions` **ne doit pas etre tranchee par
  raisonnement**. Elle attend une mesure : la distribution du champ `phase`
  sur les TROP-CHER de production.

## 2026-08-25 19:15 - interruption par SIGALRM, champ phase, seuil a 20 s

**Demande** : remplacer la borne de temps par une interruption SIGALRM,
ajouter un champ `phase`, abaisser le seuil a 20 s, et **verifier
explicitement que l'alarme se declenche**.

**Cause reelle** : la borne posee a l'intervention precedente etait
**structurellement incapable** d'interrompre le blocage. Elle testait
`time.time() - t0 > max_seconds` *entre* les appels couteux ; le processus se
bloquait *a l'interieur* d'un seul appel, qui ne rendait jamais la main. Aucun
test place entre deux appels ne peut interrompre cela, **quel que soit le
seuil**.

Preuve en production : le bloc `connect` n=4 d=3 avait bien `"max_seconds": 45`
dans son `config.json`. Il a evalue 11 systemes en **0,4 s cumulee**, puis est
reste **plus de 15 minutes a 98 % CPU sur le 12e** sans qu'aucun TROP-CHER ne
soit emis. Le compteur affichait 0, ce qui se lisait a tort comme "aucun
systeme trop cher".

**Correction** (`run.py` uniquement) :
- `signal.alarm(a.max_seconds)` arme avant `evaluate_system`, `signal.alarm(0)`
  dans un `finally`. Handler `_alarme` levant `SystemeTropLent`, rattrapee en
  TROP-CHER avec `elapsed_s`, `phase` et `interrompu: True`.
- `signal.signal(SIGALRM, _alarme)` installe une seule fois avant la boucle.
- variable module `PHASE`, mise a jour avant chaque etape : `prefilter`,
  `count_solutions`, `random_solution`, `minimal_clues`, `solve_graded`.
- **les gardes entre appels sont conservees**, comme demande : inutiles pour ce
  cas, gratuites, et elles etiquettent plus proprement quand elles suffisent.
  `interrompu` distingue les deux chemins -- present si l'arret vient du
  signal, absent si le depassement a ete constate entre deux appels.
- `MAX_SECONDS` 45 -> **20**.

Ni le solveur, ni `engine/`, ni les seuils existants (`MIN_GRIDS`,
`MAX_CLUE_FRAC`) ne sont touches.

**Verifie** (execute et observe) :
- **SIGALRM fonctionne sous pypy3.** C'etait la question ouverte, elle est
  tranchee par l'execution, pas par lecture.
- Test explicite : `minimal_clues` remplace par une boucle de calcul pur (aucun
  appel systeme, aucun test d'heure) que seul un signal peut interrompre, sur
  40 systemes avec `--max-seconds 3`.

      cpython : 40 systemes, 16 TROP-CHER, phase=minimal_clues,
                elapsed_s=3.0, interrompu=True, ms=3000
      pypy3   : 40 systemes, 15 TROP-CHER, phase=minimal_clues,
                elapsed_s=3.0, interrompu=True, ms=3000

  Interruption a exactement 3,0 s dans les deux cas, phase correcte, drapeau
  `interrompu` present. Le chemin de code est desormais **execute**, pas
  seulement ecrit.
- Observation de passage : certains systemes ont ete interrompus en
  `phase=count_solutions`, sans que cette fonction ait ete truquee. Des
  systemes bloquent donc reellement dans `count_solutions` malgre son budget
  de noeuds -- a confirmer sur des donnees de production.
- Les 4 canaris passent depuis la racine ET depuis `engine/` : 8/8, exit 0.
- `dsl_hash` inchange : **`0327bdc4c76a`** (`run.py` n'est pas dans `engine/`).
- Le repertoire de run du test et ses fichiers `found/` ont ete supprimes :
  `runs/` ne contient que les 6 runs legitimes, aucun tag `alarmtest` ne
  pollue `summary.md`.

**Non verifie / suppose** :
- **Aucun TROP-CHER n'a encore ete produit en conditions reelles.** Le
  mecanisme est prouve sur un cas artificiel ; la distribution reelle des
  phases sur de vrais systemes pathologiques est inconnue.
- Le seuil de 20 s n'est pas calibre par la mesure, il est choisi a priori.
- L'hypothese que la connectivite produise systematiquement des systemes trop
  chers reste **ouverte**. Deux blocages observes portaient sur des systemes
  `connect,relational`, ce qui ne constitue pas une mesure.
- Le script de test n'a **pas ete verse au depot** (il vivait dans `/tmp` et a
  ete supprime). Le chemin de code n'a donc pas de test de non-regression
  permanent -- candidat naturel a un `canary5.py`.
- `alarm()` a une resolution d'une seconde : le seuil n'est pas fin. Sans
  importance a 20 s.

**Bloque sur** : `sudo` toujours refuse. **Demande a Mrawdian :
`sudo systemctl restart rulesearch`.** Le bloc `connect` seed 84008 est gele
depuis 18:53 sur son 12e systeme, avec l'ancien `run.py` sans SIGALRM. Il ne
s'arretera pas seul et bloque toute la rotation.

**Pour Claude chat** :
- Une garde de temps placee **entre** deux appels ne borne rien si le blocage
  est **dans** un appel. C'est l'erreur commise ici, et elle a coute deux
  interventions. Seul un signal, ou un sous-processus, interrompt de
  l'exterieur.
- `TROP-CHER : 0` dans `summary.md` est **ambigu** : cela peut vouloir dire
  qu'aucun systeme n'est trop cher, ou que le mecanisme d'abandon ne se
  declenche pas. C'est arrive. Croiser avec la date du run et l'etat du
  processus avant de conclure.
- Le champ `phase` designe la fonction qui consommait le temps. `interrompu:
  True` signale une interruption par signal ; son absence signale un
  depassement constate entre deux appels.
- SIGALRM est **verifie fonctionnel sous pypy3**, qui est l'interpreteur de
  production. Ne pas re-ouvrir cette question sans nouvelle mesure.

## 2026-08-25 18:52 - borne de temps par systeme, verdict TROP-CHER

**Demande** : ajouter une borne de temps par systeme (`--max-seconds`, defaut
45), avec un verdict distinct **TROP-CHER**, et le documenter partout.

**Cause reelle** : le bloc `connect` a n=4 d=3 lance a 18:28 a tourne **16
minutes a 98,7 % CPU sans ecrire une seule ligne** -- 0 systeme evalue sur 15,
`results.jsonl` vide. Le processus n'etait pas bloque : il calculait un unique
systeme.

Defaut de conception, identifie par l'auteur : `count_solutions` a un budget de
**noeuds**, mais `random_solution` et `minimal_clues` n'avaient **aucun**
budget. Un systeme vivant et couteux pouvait donc consommer un bloc entier. Le
pre-filtre ne corrige pas cela : par conception il ne borne que les systemes
MORT, pas le cout des systemes vivants.

**Correction** (`run.py`) :
- constante `MAX_SECONDS = 45` et argument `--max-seconds`.
- `evaluate_system(rs, n_instances=6, max_seconds=MAX_SECONDS)` prend un
  `t0 = time.time()` en tete et teste le depassement **avant
  `count_solutions`** et **a chaque tour de la boucle sur les instances**.
- au depassement, retourne `{"verdict": "TROP-CHER", "elapsed_s": ...}` (plus
  `total_grids` quand il est connu), et **non** TIMEOUT.
- `--max-seconds` etant dans `vars(a)`, il est enregistre automatiquement dans
  le `config.json` de chaque run.

`summarize.py` : colonne TROP-CHER dans la table des verdicts, et dans la
section cout le nombre de systemes abandonnes, leur part des systemes et leur
part du temps total, **ventiles avec et sans CONNECTED**.

`README.md`, `CLAUDE.md`, `DECISIONS.md` : TROP-CHER documente, avec la
distinction explicite d'avec TIMEOUT.

**Ni le solveur ni les seuils existants (`MIN_GRIDS`, `MAX_CLUE_FRAC`) ne sont
touches.** Verifie sur le diff.

**Verifie** (execute et observe) :
- **Les quatre canaris passent depuis la racine ET depuis `engine/`** : 8
  executions, exit=0 partout. `canary3` : `OK : aucune divergence.`
  `canary4` : `OK : aucun faux positif.`
- `run.py --help` expose bien `--max-seconds MAX_SECONDS`.
- `summarize.py` tourne sans regression sur les 124 anciens enregistrements et
  emet la nouvelle ligne : `TROP-CHER : 0 systemes abandonnes (0.0% des
  systemes), 0% du temps total`.
- `ast.parse` passe sur `run.py` et `summarize.py`.
- **`dsl_hash` inchange : `0327bdc4c76a`.** `run.py` est a la racine, pas dans
  `engine/` : la borne de temps ne casse donc **pas** la comparabilite de la
  serie en cours. Seul `prefilter.py` avait change le hash.

**Non verifie / suppose** :
- **TROP-CHER n'a jamais ete declenche.** Le compteur est a 0 : le chemin de
  code est correct par lecture et par diff, pas par observation. Aucun systeme
  n'a encore ete abandonne pour depassement.
- Le seuil de 45 s n'est pas calibre par la mesure. Il est choisi a priori.
  S'il s'avere trop bas, des systemes evaluables seront abandonnes a tort ;
  trop haut, le goulot demeure.
- Le test de depassement place juste apres `is_dead()` est en pratique presque
  toujours faux (le pre-filtre coute 0,02 s). Il est conserve parce qu'il a ete
  demande explicitement, et il ne coute rien.
- L'hypothese que la connectivite produise systematiquement des systemes trop
  chers est **la question ouverte**, pas un resultat. Aucune donnee ne
  l'etaye encore.
- Le gain de debit du pre-filtre reste non mesure en production.

**Bloque sur** : `sudo` toujours refuse. **Demande a Mrawdian :
`sudo systemctl restart rulesearch`.** Necessaire ici pour deux raisons : le
bloc `connect` en cours tourne toujours avec l'ancien `run.py` **sans borne de
temps** (demarre a 18:28, plus de 20 min sur un seul systeme), et il ne
s'arretera pas de lui-meme. Sans redemarrage, la borne ne s'appliquera qu'au
bloc suivant -- qui n'arrivera pas tant que celui-ci n'a pas fini.

**Pour Claude chat** :
- **TIMEOUT et TROP-CHER ne sont pas synonymes.** TIMEOUT = budget de noeuds
  epuise dans `count_solutions` (systeme combinatoirement dur). TROP-CHER =
  budget de temps par systeme depasse, generation et minimisation incluses.
  Les confondre rend la mesure inexploitable.
- TROP-CHER est une **information de recherche**, pas un incident : un systeme
  trop cher a evaluer a n=4 est un fait sur le systeme. La ventilation
  avec/sans CONNECTED dans la section cout de `summary.md` est la mesure qui
  repond a cette question.
- Le `dsl_hash` reste **`0327bdc4c76a`**. Les runs de cette serie restent
  comparables entre eux malgre le changement de `run.py`.
- Un `summary.md` affichant `TROP-CHER : 0` peut vouloir dire deux choses
  opposees : aucun systeme trop cher, **ou** aucun bloc n'a encore tourne avec
  la borne. Verifier la date du run avant de conclure.

## 2026-08-25 18:25 - pre-filtre MORT (v3), correction canary4, file a domaine egal

**Demande** : integrer cinq fichiers livres (`prefilter.py`, `canary4.py`,
`run.py`, `CLAUDE.md`, `DECISIONS.md`), corriger la fragilite de chemin de
`canary4.py`, et remplacer la file par deux configs comparables.

**Cause reelle (echec de canary4)** : lance depuis la racine, `canary4.py`
sortait en `ModuleNotFoundError: No module named 'run'`. Il faisait

    sys.path.insert(0, "..")

soit un chemin **relatif au repertoire courant, pas au script**. Python ajoute
a `sys.path` le dossier **du script** (`canary/`), jamais le CWD : depuis la
racine, `".."` designait `/home/rulesearch`, le parent du depot, ou `run.py`
n existe pas. Le canari ne fonctionnait que lance depuis `engine/` -- ce que
fait `run_canaries()` (`cwd=HERE/engine`), d ou l illusion qu il etait correct.

C est **la meme classe de bug** que l aplatissement qui avait cause les 864
boucles : un chemin qui depend d ou l on se trouve plutot que d ou le code est.

`canary.py`, `canary2.py` et `canary3.py` ont ete verifies : ils **n ont pas**
cette fragilite (aucune manipulation de `sys.path`, ils n importent que des
modules d `engine/` via `PYTHONPATH`). Seul `canary4.py` etait touche.

**Correction** :
- `canary/canary4.py` : `sys.path.insert(0, "..")` remplace par
  `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`,
  et `os` ajoute aux imports. Le canari est desormais independant du CWD.
- `engine/prefilter.py` (nouveau), `canary/canary4.py` (nouveau), `run.py`,
  `CLAUDE.md`, `DECISIONS.md` transferes par scp **vers des chemins de
  destination explicites**, jamais vers un repertoire, pour eviter tout
  re-aplatissement. Arborescence verifiee avant toute autre action.
- `queue.json` (non versionne) : `block_systems` 60 -> 15 ; les 5 configs
  remplacees par exactement deux, `connect` et `static-ref`, toutes deux
  n=4 **d=3**.
- `DECISIONS.md` : entree datee sur la file a domaine egal.

**Verifie** (execute et observe) :
- **Les quatre canaris passent depuis la racine ET depuis `engine/`** : 8
  executions, `exit=0` partout. `canary3` finit sur `OK : aucune divergence.`,
  `canary4` sur `OK : aucun faux positif.`
- Surete du pre-filtre, sur 150 systemes : **16 declares MORT, 16 confirmes,
  0 FAUX POSITIF** ; 62 morts non attrapes (normal, le pre-filtre est
  incomplet par conception).
- Cout mesure : pre-filtre **0,02 s** contre solveur **36,1 s** sur le meme
  echantillon.
- Arborescence apres transfert : `engine/` contient deduction, dsl2,
  prefilter, rulesearch ; `canary/` contient canary, canary2, canary3,
  canary4 ; la racine ne contient que `run.py`, `scheduler.py`,
  `summarize.py`. Rien d aplati.
- `queue.json` relu : `block_systems=15`, tags `['connect', 'static-ref']`.

**dsl_hash : `6680f7b47e6f` -> `0327bdc4c76a`.** Le seul ajout de
`prefilter.py` dans `engine/` change le hash. **C est voulu.** Consequence
directe (invariant 2 de CLAUDE.md) : les runs posterieurs ne sont **pas
comparables** aux 124 systemes deja mesures. La serie repart de zero. Le hash
a change des le depot des fichiers sur disque, avant tout commit.

**Correction d une affirmation anterieure** : il avait ete ecrit qu un
redemarrage du service etait necessaire pour prendre le nouveau code.
**C est faux pour `run.py`.** `scheduler.py` relance `run.py` en
sous-processus a chaque bloc : le nouveau `run.py` et le pre-filtre entrent en
service au prochain bloc, sans redemarrage et independamment de tout commit.
Seul `scheduler.py`, charge une fois en memoire, exige un redemarrage -- et il
avait deja ete recharge. Le redemarrage demande ici a un **autre motif** :
interrompre le bloc en cours et faire relire `queue.json`.

**Non verifie / suppose** :
- Le pre-filtre n a **pas encore tourne en production** : aucun bloc ne s est
  execute avec le nouveau `run.py`. Le gain reel (annonce ~20 % dans
  DECISIONS.md, apres correction du ~30x errone) n est pas mesure en
  conditions reelles.
- Aucun resultat n existe encore pour `connect` ni `static-ref` a d=3. La
  question centrale reste ouverte.
- L absence de faux positifs est etablie sur 150 systemes a n=4/d=4, pas a
  d=3 ni au-dela.
- La duree d un bloc de 15 systemes n est pas mesuree.

**Bloque sur** : `sudo` toujours refuse (`rulesearch`). **Demande a Mrawdian :
`sudo systemctl restart rulesearch`** -- necessaire pour interrompre le bloc
`baseline` en cours (seed 80339, demarre a 17:52, toujours actif apres 30 min)
et faire relire la nouvelle `queue.json`. Sans cela, le scheduler termine son
bloc courant avant de reprendre la file.

**Pour Claude chat** :
- Ne jamais ecrire `sys.path.insert(0, "..")` ni aucun chemin relatif au CWD
  dans ce depot. Toujours ancrer sur `__file__`. Deux pannes distinctes en ont
  deja decoule.
- Un canari doit passer **depuis la racine et depuis `engine/`**. Passer dans
  un seul repertoire masque exactement ce type de bug.
- Le `dsl_hash` courant est **`0327bdc4c76a`**. Toute ligne de journal portant
  `6680f7b47e6f` appartient a la serie precedente et **ne se compare pas** aux
  nouvelles.
- `block_systems=15` et deux configs seulement : un `summary.md` sans
  `baseline`, `cages` ni `big` est **normal**, ce sont des retraits
  deliberes, pas des echecs.
- `queue.json` n est pas dans le depot (ignore, local au serveur) : son
  contenu n est pas lisible depuis GitHub.

## 2026-08-25 17:49 - regression .gitignore (summary.md) et garde sur sh()

**Demande** : retirer `summary.md` du `.gitignore`, puis journaliser en ERROR
les echecs de commandes git dans `scheduler.py`. Egalement : `block_systems`
de 400 a 60 dans `queue.json`.

**Cause reelle** : a l intervention precedente, `summary.md` a ete ajoute au
`.gitignore` au motif qu il est regenere a chaque bloc. C etait une erreur, et
elle venait de moi : je n avais pas lu `scheduler.py` avant de proposer
l ajout. Or le scheduler **versionne deliberement** ce fichier :

    sh("git add -A summary.md found/ && git ... commit ... --allow-empty")

Une fois `summary.md` ignore, `git add` sortait en code 1
(`The following paths are ignored by one of your .gitignore files`). A cause du
`&&`, le `commit` ne s executait plus **du tout** : ni `summary.md`, ni
`found/` n etaient plus pousses. La sortie qui compte cessait d arriver sur
GitHub.

**Pourquoi c est reste invisible** : `sh()` capturait stdout/stderr et
retournait `CompletedProcess` sans que l appelant ne teste `returncode`.
L echec etait donc totalement muet - le scheduler continuait sa boucle comme
si le push avait reussi. C est la cause racine de la regression : non pas
l erreur de `.gitignore` elle-meme, mais l absence de toute remontee d echec
qui l a laissee passer.

Precision sur l enonce de la demande : il n y avait **pas de WARNING generique**
a remplacer. `sh()` ne journalisait rien. La modification **ajoute** une
journalisation la ou il n y en avait aucune.

**Correction** :
- `.gitignore` : `summary.md` retire. Restent `__pycache__/`, `*.pyc`,
  `desktop.ini`, `scheduler.log`, `queue.json`, `runs/`.
- `scheduler.py` : `sh()` teste desormais `returncode` et journalise sur stderr
  `[sched][ERROR] commande en echec (rc=N) : <cmd>` suivi de stdout/stderr
  tronques a 2000 caracteres. Valeur de retour inchangee, aucun appelant
  modifie, **rien d autre touche** dans le scheduler.
- `queue.json` (non versionne, edite directement sur le serveur) :
  `block_systems` 400 -> 60. Les 5 configs sont intactes. Motif : le scheduler
  enchaine les configs sequentiellement et n avait produit que du `baseline` ;
  `connect` et `static-ref`, qui testent l hypothese centrale, n avaient jamais
  tourne. Des blocs courts accelerent la rotation complete.

**Verifie** (execute et observe) :
- `git add -A summary.md found/` sort desormais en **0** (sortait en 1 avant le
  correctif). La chaine `&&` du scheduler est donc retablie. Echec et
  retablissement tous deux constates directement sur le serveur.
- `scheduler.py` re-parse sans erreur (`ast.parse`).
- `block_systems` relu a 60 dans `queue.json`.
- Lecture de `scheduler.py` : la boucle externe fait `git pull --rebase
  --autostash` puis `load_queue()` **a chaque cycle**. `queue.json` est donc
  relu sans redemarrage - mais seulement **apres** la boucle interne sur les 5
  configs, donc pas avant la fin du cycle courant (celui a 400).
- `queue.json` etant non suivi et ignore, le `git pull` du scheduler ne
  l ecrase pas.

**Non verifie / suppose** :
- La journalisation ERROR n a **jamais ete declenchee en conditions reelles** :
  le correctif fait justement que la commande reussit. Le chemin d erreur est
  correct par lecture, pas par observation.
- Le service tourne encore avec l **ancien** `scheduler.py` charge en memoire
  et `block_systems=400`. Aucun effet des deux correctifs n a encore ete
  observe a l execution.
- Non verifie si des blocs ont echoue silencieusement entre l ajout de
  `summary.md` au `.gitignore` et son retrait ; le cas echeant, les `found/`
  correspondants ont ete rattrapes par le commit courant.
- L effet de `block_systems=60` sur la duree reelle d un cycle complet n est
  pas mesure.

**Bloque sur** : `sudo` toujours refuse pour l utilisateur `rulesearch`
(`sudo -n systemctl restart rulesearch` -> `sudo: interactive authentication is
required`). Egalement refuse pour `systemctl stop` et `journalctl -u
rulesearch`. Contournement non tente, conformement au protocole. **Le
redemarrage est pris en charge par Mrawdian.** Tant qu il n a pas eu lieu, les
correctifs de `scheduler.py` ne sont pas actifs.

En attente de sa confirmation avant de regenerer `summary.md` et de relever le
tableau : le faire avant ne montrerait que du `baseline` a 400, sans rapport
avec les changements.

**Pour Claude chat** :
- `summary.md` **est versionne et pousse par le scheduler** apres chaque bloc.
  C est le canal par lequel les resultats arrivent dans le depot. Ne jamais
  l ajouter au `.gitignore` : cela casse silencieusement aussi le push de
  `found/`. C est l erreur commise ici.
- Regle generale qui en decoule : avant d ignorer un fichier, verifier qu aucun
  script ne le committe explicitement. `grep` sur le nom du fichier dans
  `scheduler.py` et `nightly.sh` suffit.
- `queue.json` **n est pas dans le depot** (ignore, local au serveur). Son
  contenu ne peut pas etre lu depuis GitHub. Etat actuel : `block_systems=60`,
  5 configs `baseline`, `connect`, `cages`, `static-ref`, `big`.
- Un `summary.md` ne montrant que `baseline` ne signifie pas que les autres
  configs ont echoue : elles n ont simplement pas encore ete atteintes dans la
  rotation sequentielle.
- Les commits `auto: resume <tag>` sont produits par le scheduler lui-meme
  (identite `rulesearch@local`), pas par une intervention humaine.

## 2026-08-25 17:41 — restauration de l arborescence engine/ et canary/

**Demande** : le service systemd `rulesearch` ne demarrait pas (redemarrage en
boucle, exit 1) ; diagnostiquer la cause reelle, corriger, verifier.

**Cause reelle** : les fichiers Python avaient ete **aplatis a la racine** avant
le premier commit, alors que `run.py` attend une arborescence en sous-dossiers.
`dsl_hash()` (run.py:29) fait `os.listdir(HERE/"engine")` et `run_canaries()`
(run.py:39) cherche les canaris dans `HERE/canary`. Sans ces repertoires,
`dsl_hash()` levait `FileNotFoundError`, `run.py` sortait en erreur, le
scheduler journalisait `run en echec, arret` et sortait en code 1, et systemd
relancait — **864 cycles** enregistres dans `scheduler.log` (570 Ko).

Trois hypotheses de depart etaient **fausses** et sont ecartees :
- il n y avait aucun bug dans `scheduler.py`, ni prefligh/logging manquant ;
- les correctifs recherches etaient **deja presents** dans `run.py` (dsl_hash,
  PYTHONPATH des canaris, chemin `canary/`) ; c est le layout qui ne suivait pas ;
- `scheduler.log` n etait **pas vide** (570 Ko) : le crash ne precedait pas
  l ecriture, le scheduler journalisait correctement son echec.
- `journalctl -u rulesearch` vide s explique par l absence de droits, pas par
  une absence de log.

Le `exit 1` et l `activating (auto-restart)` etaient donc le comportement
**correct** du systeme signalant une vraie panne, pas un crash du service.

**Correction** :
- `git mv` : `rulesearch.py`, `deduction.py`, `dsl2.py` -> `engine/`
- `git mv` : `canary.py`, `canary2.py`, `canary3.py` -> `canary/`
- suppression de `desktop.ini` (etait versionne) et de `__pycache__`
- creation de `.gitignore` : `__pycache__/`, `*.pyc`, `desktop.ini`,
  `scheduler.log`, `queue.json`, `runs/`
- **aucun contenu Python modifie** : git enregistre des renommages purs (`R`)
- `engine/` et les seuils non touches, conformement a la consigne

**Verifie** (execute et observe sur le serveur) :
- les trois canaris passent, `exit 0` chacun :
  - `canary.py` : positif sudoku 4x4 10/10 deductibles ; contre-canari densite
    1.00 et aucune deduction (comportement attendu)
  - `canary2.py` : sudoku4 8/8 ; connected+nosquare+count 7/8
  - `canary3.py` : 5 familles, `DIVERGENCES=0` partout, finit sur
    `OK : aucune divergence.`
- `git status` confirme les renommages en `R` (contenu intact)
- commit `45e4957` pousse sur `main` (`3d917ec..45e4957`)
- le correctif fonctionne **en conditions reelles** : le service tournant
  toujours, les repertoires `found/` et `runs/` sont apparus pendant
  l intervention, avec 2 systemes retenus dans `found/`. Les runs aboutissent.

**Non verifie / supposition** :
- le service n a **jamais pu etre arrete ni relance proprement** (voir Bloque
  sur). Son bon fonctionnement est deduit de l apparition de `found/` et
  `runs/`, pas d un `systemctl status` observe apres correction.
- `rulesearch.service` n a pas ete relu ni valide ; rien n indique qu il pose
  probleme, mais ce n est pas verifie.
- les 2 entrees de `found/` n ont pas ete inspectees sur le fond.
- l historique git ne contient que 2 commits au total ; pourquoi le depot a ete
  initialise a plat n a pas ete elucide.

**Bloque sur** : `sudo` refuse pour l utilisateur `rulesearch`
(`sudo -n systemctl stop rulesearch` -> `sudo: interactive authentication is
required`). Le service n a donc pas pu etre arrete pendant l intervention, et
la boucle de redemarrage a continue. Conformement a la consigne, contournement
non tente. **Action restant a l operateur humain** : `sudo systemctl stop
rulesearch` puis redemarrage propre si souhaite. Meme limite pour
`journalctl -u rulesearch`.

**Pour Claude chat** :
- L arborescence attendue est desormais `engine/` (rulesearch, deduction, dsl2)
  et `canary/` (canary, canary2, canary3) ; tout le reste a la racine. Le code
  reference ces chemins en dur : **ne jamais reaplatir**.
- Les canaris se lancent avec `PYTHONPATH=engine python3 canary/canaryN.py`
  depuis la racine du depot.
- `dsl_hash` depend du **contenu de `engine/`** : deplacer ou modifier un
  fichier de `engine/` change le hash et rend les lignes incomparables
  (invariant 2 de CLAUDE.md). Le hash observe apres correction est `6680f7b47e6f`
  (visible dans les noms de fichiers de `found/`).
- `found/` est **versionne** (c est la sortie qui compte). `runs/`,
  `scheduler.log` et `queue.json` sont ignores : locaux au serveur, volumineux.
  Ne pas demander leur contenu en supposant qu il est dans le depot.
- `CLAUDE.md` demande de lire `summary.md` : **ce fichier n existe pas** dans le
  depot. Incoherence non corrigee, signalee ici.
- L identite git du depot a ete fixee localement (`Mrawdian` /
  `mrawdian@gmail.com`) : elle n etait pas configuree, ce qui bloquait le commit.
