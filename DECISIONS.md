# Journal des decisions

Append-only. Une entree par decision structurante, avec sa raison et son
critere de reouverture. Ne jamais reecrire l'historique : une decision
revisee s'ajoute, elle n'efface pas la precedente.

## 2026-08-24 — choix du terrain
Filtre a trois branches pour choisir un terrain de recherche automatisee :
verite calculable, espace trop grand pour un humain seul, peu d'yeux dessus.
VELAX passait les deux premieres et echouait sur la troisieme (mobilite
individuelle = domaine sature). Terrain retenu : espace des systemes de
regles de puzzles.

## 2026-08-24 — stdlib seule, pas de solveur SAT
Un solveur SAT externe enfermerait le DSL dans son modele de contraintes au
moment precis ou on a besoin d'exprimer ce qu'il ne sait pas dire — la
connectivite en premier. Reouverture : si le pre-filtre ne suffit pas et que
le debit reste le goulot apres n=6.

## 2026-08-24 — pypy3 plutot que python3
Backtracking pur Python, gain de 5 a 20x sans changer une ligne.

## 2026-08-24 — dsl_hash dans chaque ligne de journal
Sans lui, un journal de plusieurs semaines devient un tas de lignes dont on
ne sait plus lesquelles se comparent. C'est le seul garde-fou contre
l'accumulation silencieuse de resultats incoherents.

## 2026-08-24 — la tache nocturne n'ecrit que des analyses
Un agent qui modifie le moteur sans surveillance corrompt les journaux d'une
maniere qu'on ne saura pas dater apres coup. Les changements de code passent
par une session interactive.

## 2026-08-25 — pre-filtre MORT par propagation seule (T0)
Retenu apres mesure : 15-30 % des morts attrapes, cout negligeable, zero
faux positif sur 150 systemes. La variante T0+T2 attrape 52 % mais consomme
un tiers de ce qu'elle economise — ecartee.
Reouverture : si le profil du temps change avec n=5/n=6.

## 2026-08-25 — reordonnancement du solveur ecarte
MRV dynamique reduit les noeuds de 35 % et double le temps. Ordre statique
par degre : 5 %, dans le bruit. Le cout par noeud domine le nombre de
noeuds. Les trois variantes rendent des comptes de solutions identiques,
la mesure est donc fiable.
Reouverture : seulement si `feasible` devient incrementiel, ce qui change
le rapport cout-par-noeud / nombre-de-noeuds.

## 2026-08-25 — le facteur ~30 annonce pour le pre-filtre etait faux
Ecrit dans CLAUDE.md sans mesure. Le gain reel est de l'ordre de 20 %.
Corrige sur place. Aucune autre estimation de gain ne doit figurer dans
CLAUDE.md sans le banc qui la produit.

## 2026-08-25 - file reduite a connect / static-ref, a domaine egal
La file faisait tourner `connect` a d=2 et `static-ref` a d=4. Deux
configurations a domaines differents ne sont pas comparables : la mesure
censee trancher l'hypothese centrale (fracture locale / non-locale) etait
**biaisee par construction**, puisque l'ecart de profondeur observe pouvait
venir de la taille du domaine et non de la presence de CONNECTED.

Nouvelle file : `connect` et `static-ref` tous deux a n=4, d=3, meme
`block_systems`. Seule la presence de CONNECTED varie -- c'est la variable
dont on veut mesurer l'effet.

`baseline`, `cages` et `big` sont retires : ils consomment du temps machine
sans contribuer a la question. `baseline` melange toutes les familles et ne
peut donc trancher sur aucune ; `big` (n=5) change le domaine, donc n'est pas
comparable non plus.

Reouverture : une fois l'hypothese tranchee a d=3, verifier qu'elle tient a
un autre domaine (d=2 et d=4, chaque fois **les deux tags ensemble**). Un
resultat obtenu a un seul domaine ne se generalise pas.

## 2026-08-25 - borne de temps par systeme, verdict TROP-CHER
Defaut de conception : `count_solutions` avait un budget de noeuds, mais
`random_solution` et `minimal_clues` n'en avaient aucun. Un systeme vivant et
couteux pouvait donc consommer un bloc entier. Constate en production : le
premier bloc `connect` a n=4 d=3 a tourne **16 minutes a 98 % CPU sans emettre
une seule ligne** -- zero systeme evalue sur 15.

Ajout de `--max-seconds` (defaut 45), verifie avant `count_solutions` et a
chaque tour de la boucle sur les instances.

Verdict distinct **TROP-CHER**, et non TIMEOUT : les deux abandons n'ont pas
le meme sens. TIMEOUT = budget de noeuds epuise, le systeme est
combinatoirement dur. TROP-CHER = budget de temps depasse, ce qui inclut le
cout de generation et de minimisation. Les confondre rendrait la mesure
inexploitable.

Ce verdict est une **information de recherche**, pas seulement une rustine :
un systeme trop cher a evaluer a n=4 est un fait sur le systeme. Si la
connectivite en produit systematiquement, c'est un resultat sur la fracture
locale / non-locale, pas un incident d'exploitation. `summarize.py` ventile
donc les TROP-CHER avec et sans CONNECTED.

Ni le solveur ni les seuils existants (MIN_GRIDS, MAX_CLUE_FRAC) ne sont
touches.

Reouverture : si une part importante des systemes tombe en TROP-CHER a 45 s,
le seuil est mal calibre ou le cout de `minimal_clues` doit etre attaque
directement. A surveiller des le premier bloc complet.

## 2026-08-25 - interruption par SIGALRM, champ phase, seuil a 20 s
La borne de temps decidee plus haut etait **structurellement incapable
d'interrompre le blocage**. Elle testait le depassement *entre* les appels
couteux ; or le processus se bloquait *a l'interieur* d'un seul appel, qui ne
rendait jamais la main. Aucun test place entre deux appels ne peut interrompre
cela, quel que soit le seuil.

Constate en production : bloc `connect` n=4 d=3 avec `max_seconds=45` bien
actif dans son `config.json`, 11 systemes evalues en 0,4 s cumulee, puis **15
minutes a 98 % CPU sur le 12e sans que TROP-CHER se declenche**.

Correction : `signal.alarm(max_seconds)` autour de `evaluate_system`, handler
levant `SystemeTropLent`, rattrape en TROP-CHER avec `elapsed_s`. Le signal
interrompt le code ou qu'il en soit. Les gardes entre appels sont conservees :
inutiles pour ce cas, gratuites, et elles etiquettent plus proprement quand
elles suffisent -- le champ `interrompu` distingue les deux chemins.

Champ **`phase`** : variable mise a jour avant chaque etape (`prefilter`,
`count_solutions`, `random_solution`, `minimal_clues`, `solve_graded`). Savoir
qu'un systeme est pathologique ne dit pas quelle fonction l'est ; sans ce
champ, la mesure ne designe pas de coupable.

Seuil abaisse de 45 s a **20 s** : a 45 s on paie tres cher des systemes de
toute facon inexploitables.

Limites connues : SIGALRM n'existe que sous Unix et ne se declenche que sur le
thread principal. `run.py` tourne bien dans le thread principal, et le
declenchement a ete verifie explicitement sous **python3 et sous pypy3** (un
chemin de code jamais execute n'est pas un chemin de code). La resolution
d'`alarm()` est la seconde, donc le seuil n'est pas fin -- sans importance ici.

Reouverture : si un blocage survient dans du code qui masque les signaux, ou
si le portage sort d'Unix, il faudra passer par un sous-processus avec timeout.

## 2026-08-25 - la borne de 20 s est un filtre qui biaise l'echantillon
La borne de temps par systeme n'est pas seulement une protection de debit.
C'est un **critere de selection applique a l'echantillon**, et il n'est pas
neutre : il exclut preferentiellement les systemes couteux a evaluer.

Premiere mesure : 22 TROP-CHER sur 395 systemes (4,2 %), consommant **94 % du
temps total**, et **tous** contenant CONNECTED. Phase unique : `solve_graded`.

Consequence pour l'hypothese centrale. Si la connectivite cause les abandons,
alors les systemes a connectivite les plus couteux sont exclus de la mesure.
Ce sont vraisemblablement les plus profonds -- exactement ceux que l'hypothese
predit comme atteignant T2. **L'echantillon est donc tronque du cote que
l'hypothese predit, et la troncature joue CONTRE elle.**

Il en decoule une regle de lecture, portee dans `summary.md` pour qu'on ne
puisse pas l'oublier : tout ecart T2 favorable observe est une **borne
inferieure**, jamais une estimation. Et surtout, **un ecart faible ou nul ne
refute pas l'hypothese** -- il peut n'etre qu'un effet de la borne de temps.
Sans cet avertissement, on lirait une non-difference comme une refutation.

Le ratio global "TROP-CHER avec / sans CONNECTED" est **confondu** : seul le
tag `connect` peut produire des systemes contenant CONNECTED, `static-ref`
n'en produit aucun par construction. La comparaison valide est le taux de
TROP-CHER **a l'interieur du seul tag `connect`**, ou les deux types de
systemes coexistent. `summarize.py` publie desormais les deux, la ligne
globale explicitement marquee comme confondue.

Reouverture : **si la fraction de systemes CONNECTED abandonnes depasse 20 %
des systemes CONNECTED**, la borne ne protege plus le debit, elle detruit la
mesure. Il faudra alors la remonter, ou traiter ces systemes a part dans une
file dediee a budget long, plutot que de les jeter. Le chiffre est publie a
chaque resume dans la section "censure de l'echantillon".

## 2026-08-26 - T2 a sature, T3 est inerte, et le motif se repete
Deux constats distincts, une meme racine.

**T2 a sature.** Sur 8146 enregistrements, 437 candidats avec connectivite et
621 sans, la fraction atteignant T2 vaut **100 % dans les deux groupes**.
L'indicateur ne discrimine plus. Pire, le verdict automatique de
`summarize.py` imprimait alors "l'hypothese ne tient pas" : la regle
`a < b + 0.05` est satisfaite par 1,0 < 1,05. Le resume **affirmait une
refutation qu'il n'avait pas etablie**. Corrige : il imprime desormais
INDICATEUR SATURE et refuse explicitement de conclure, dans les deux sens.
Un resume muet vaut mieux qu'un resume qui ment.

**T3 est correct et inerte.** La paire nue a ete implementee, restreinte a
`t1_regions()` pour ne pas refaire le bug T1, et verifiee par `canary3` sur les
cinq familles : aucune divergence. Elle ne s'est jamais declenchee -- 0
invocation sur 30 instances de reference, puis 0 sur les cas de `canary6`.

La cause est **structurelle, pas un bug** : T3 est une technique d'ELIMINATION
de candidats, et le moteur n'a aucune representation des candidats.
`candidates()` les recalcule a chaque appel. Une elimination ne peut donc se
materialiser que si elle reduit une cellule a une seule valeur -- cas que T0
traite deja. Aucun reglage ne peut la rendre operante.

**C'est le quatrieme cas d'une metrique qui ne mesure pas ce qu'elle
annonce** (T1 faux ; profondeur v1 saturante ; T2 sature ; T3 inerte), et le
**deuxieme ou une metrique a ete livree sans avoir ete testee dans son regime
d'usage** -- survenu immediatement apres que cette regle ait ete ecrite dans
CLAUDE.md. Ecrire la regle n'a pas suffi.

Elle devient donc un **invariant dur** (CLAUDE.md 6 et 7) et surtout un
**canari** : `canary6` exige que toute technique de niveau <=
`DEFAULT_MAX_LEVEL` s'invoque au moins une fois sur les cas de reference.
Verifie dans les deux sens : le canari passe a `DEFAULT_MAX_LEVEL = 2`, et
**echoue** si on le porte a 3 sans rendre T3 operante. Une regle n'est acquise
que lorsqu'un canari echoue quand elle cesse d'etre respectee.

`DEFAULT_MAX_LEVEL` reste a **2**. T3 reste dans le code, correct et desactive.

Reouverture : le choix entre donner au moteur un etat de candidats explicite
(A) et remplacer T3 par une technique qui pose des valeurs (B) n'est pas
tranche. Tant qu'il ne l'est pas, la mesure de profondeur est saturee et
**aucune conclusion sur l'hypothese centrale n'est possible** -- ni pour, ni
contre.

## 2026-08-26 - aucune technique d'ELIMINATION ne peut fonctionner sur ce moteur
Deux tentatives, deux echecs identiques, et la cause n'est pas le choix de la
technique.

**Paire nue** : deux cellules d'une region ALLDIFF de taille d ayant exactement
les deux memes candidats se reservent ces deux valeurs, qui sont eliminees des
autres cellules. Implementee, restreinte a `t1_regions()`, verifiee correcte
par `canary3` sur les cinq familles. **0 invocation.**

**Paire cachee** : deux valeurs n'ayant chacune que les deux memes cases
possibles se reservent ces cases, dont toute autre valeur est eliminee.
Implementee, meme restriction, meme verification. **0 invocation.**

La cause est **structurelle et demontrable**. Le moteur n'a aucune
representation des candidats : `candidates()` les recalcule depuis
`feasible()`. Il n'existe nulle part ou inscrire une elimination. Une technique
d'elimination ne peut donc produire d'effet que si elle reduit une cellule a
une seule valeur -- et ce cas est deja traite par T0.

Pour la paire cachee la demonstration est directe : si les valeurs u et v n'ont
que les cases {i,j}, alors u et v sont candidats en i comme en j ; l'elimination
laisse donc exactement deux candidats dans chacune, jamais un. Et le cas ou il
n'en resterait qu'un est precisement un hidden single, deja capture par T1.

**Regle qui en decoule** : seules les techniques qui POSENT une valeur ("la
case k vaut v") peuvent fonctionner sur ce moteur. T0, T1 et T2 en sont. Cette
propriete doit etre verifiee AVANT d'implementer, pas apres -- `canary6` la
verifie apres, ce qui est un filet, pas une methode.

`DEFAULT_MAX_LEVEL` reste a **2**. La mesure de profondeur reste saturee, donc
**aucune conclusion sur l'hypothese centrale n'est possible**, ni pour ni
contre.

Reouverture : elle passe par l'option A ci-dessous, ou par une technique de
POSE moins couteuse que la contradiction a profondeur 2. Aucune n'est connue a
ce jour.


## 2026-08-26 - etat de candidats explicite : bonne architecture, mauvais moment
Donner au moteur un domaine par cellule, propage et reduit, est ce que fait
tout solveur de contraintes serieux. C'est ce qui rendrait operante toute la
classe des techniques d'elimination -- paires nues et cachees, triplets,
X-Wing -- au lieu de les laisser inertes. C'est la bonne architecture.

**Differee.** Deux raisons.

D'abord le perimetre : `feasible()` est aujourd'hui l'unique oracle. Passer a
des domaines propages veut dire ecrire une propagation par type de contrainte,
`Connected` compris -- celle qui n'est pas decomposable localement, donc la
plus difficile. C'est reecrire le coeur du moteur pour debloquer une metrique.

Ensuite, et surtout, le **risque asymetrique** : un bug de propagation ne
plante pas. Il retire un candidat de trop, la deduction remplit quand meme la
grille, et rend une solution FAUSSE. C'est le mode de defaillance du bug T1
deja paye, mais reparti sur tout le moteur au lieu d'une fonction. `canary3`
l'attraperait -- c'est sa raison d'etre -- au prix d'une mise au point longue
pendant laquelle la recherche est a l'arret.

**Critere de reouverture** : quand le **debit**, et non la metrique, sera le
probleme -- typiquement a n=5 ou n=6, ou le recalcul integral de
`candidates()` a chaque appel deviendra le goulot. A ce moment le chantier se
justifie par lui-meme et ne sera plus un detour.

Condition prealable non negociable : etendre `canary3` avant d'ecrire la
premiere ligne de propagation, pas apres.


## 2026-08-26 - bytecode perime : le code execute peut differer de la source
Constate en verifiant `canary6` : la source portait `DEFAULT_MAX_LEVEL = 2`,
`grep` le confirmait, et l'import rendait **3**. Un `engine/__pycache__`
perime, produit lors d'un test ou la constante valait 3, continuait d'etre
servi -- la taille du fichier etant inchangee, seul le chiffre differant.

C'est une atteinte directe a l'integrite des mesures : `dsl_hash` hache les
fichiers `.py`, donc un journal peut porter le hash d'une source qui n'est pas
celle qui a tourne. Exactement ce que `dsl_hash` est cense empecher.

Ajoute a l'invariant 1 : purger `__pycache__` apres toute modification de
`engine/`. Non automatise a ce stade -- candidat a une purge systematique au
demarrage de `run.py`, non fait car cela touche au chemin de production.

## 2026-08-26 - reformulation de l'option A : ce n'est plus une question de calendrier
L'entree precedente presentait l'etat de candidats explicite comme "bonne
architecture, mauvais moment". Cette formulation est trop douce, et l'auteur
l'a corrigee.

Puisque **toute technique d'ELIMINATION est inerte sur ce moteur** et que la
seule famille de POSE connue au-dela de T2 -- la contradiction a profondeur 2
-- a un cout multiplicatif qui detruirait la mesure qu'elle permet, A n'est
plus une option parmi deux. C'est **la seule voie connue** vers une metrique de
profondeur non saturee.

La question n'est donc pas "quand reecrire le moteur" mais :

    **accepte-t-on de ne jamais mesurer la profondeur au-dela de T2 ?**

Repondre oui est un choix legitime -- le projet peut se contenter de T0/T2 et
chercher ailleurs sa ligne de fracture. Mais c'est un choix, pas un report, et
il doit etre pris comme tel.

Reouverture inchangee sur le fond : le chantier se justifie de lui-meme quand
le debit deviendra le probleme (n=5, n=6). Ce qui change est qu'en attendant,
**aucune mesure de profondeur plus fine que T2 n'existe** -- sauf par la voie
continue ci-dessous.


## 2026-08-26 - une metrique CONTINUE discrimine la ou le seuil sature
Mesure demandee avant de trancher A, et elle change la situation.

Distribution sur 1143 candidats, toutes series : `max_level` vaut T2 pour
**100 %** d'entre eux. Le seuil est donc bien sature. Mais les invocations par
niveau, elles, varient :

    serie 615abe43d6bc, 945 candidats
      AVEC connectivite (397) : T0=12,99  T2=2,95  pondere 5,90
      SANS connectivite (548) : T0=15,85  T2=2,67  pondere 5,34

Le sens est celui que l'hypothese predit : les systemes a connectivite
demandent **plus de T2 et moins de T0**. L'ecart est faible mais il va dans le
meme sens sur trois des quatre series (la quatrieme, n=53, s'inverse).

**Consequence pratique : il existe une sortie sans reecrire le moteur.** Une
metrique continue -- nombre d'invocations pondere par le niveau -- discrimine
la ou `max_level >= 2` ne dit plus rien. Elle est publiee a chaque resume.

Elle ne remplace pas A : elle mesure l'EFFORT de deduction, pas la PROFONDEUR
au sens d'une hierarchie de techniques. Un systeme qui demande 3 fois T2 n'est
pas "plus profond" qu'un systeme qui en demande 2, il est plus laborieux. La
distinction compte pour l'interpretation, pas pour le pouvoir discriminant.

**Decouverte annexe, et elle est importante : T1 n'a JAMAIS ete invoquee.**
Zero sur l'ensemble des enregistrements, toutes series confondues. La
hierarchie effective en production est **T0/T2**, pas T0/T1/T2 -- le niveau
intermediaire est vide. Cela explique en partie la saturation : il n'y a pas
trois niveaux mais deux, et tout candidat qui depasse T0 tombe directement a
T2. `canary6` montre pourtant que T1 se declenche sur un cas de reference
(cages+sum), donc la technique n'est pas inerte au sens de T3 -- elle est
simplement sans emploi dans l'espace reellement explore.

A creuser avant tout chantier sur A : si le vrai probleme est un trou entre T0
et T2, une technique intermediaire operante vaudrait mieux qu'une reecriture.

Reouverture : si l'ecart continu reste sous le bruit une fois plusieurs
centaines de candidats accumules par groupe, la question de A redevient
frontale.


## 2026-08-26 - les series non reproductibles sont marquees, pas purgees
Cinq `dsl_hash` cohabitent, dont plusieurs designent un moteur dont la source
n'existe plus -- 83 % des enregistrements a la date de cette entree.

Choix : **conserver et etiqueter**, ne pas purger. Une serie non reproductible
reste une donnee ; ce qui est dangereux n'est pas de la garder, c'est de la
croire reproductible. `summarize.py` calcule desormais le `dsl_hash` de chaque
version de `engine/` presente dans l'historique git et marque **NON
REPRODUCTIBLE** tout hash absent de cet ensemble, avec le total et le
pourcentage concernes.

Si git est indisponible, le marquage est omis plutot que devine -- une absence
de marque ne vaut donc pas certificat.


## 2026-08-26 - le serveur ne tourne plus sur un arbre de travail
Cause racine des series orphelines : `scheduler.py` relance `run.py` a chaque
bloc, et `run.py` reimportait `engine/` depuis le repertoire de travail. Toute
edition en cours etait donc captee a mi-chemin par le bloc qui demarrait.
Constate quatre fois en une journee, dont une serie de 7172 enregistrements.

Correction structurelle, qui supprime la cause au lieu d'exiger de la
discipline :
- `scheduler.py` fige `engine/` dans `.engine-run/` au debut de chaque cycle
  (copie, puis bascule atomique par `os.rename`) et passe `RS_ENGINE` a
  `run.py`.
- `run.py` charge le moteur depuis `RS_ENGINE` s'il est defini, et **calcule
  `dsl_hash` sur ce meme repertoire** -- le hash decrit donc le code
  reellement charge, pas l'etat du disque au moment du calcul.
- `run.py` purge le `__pycache__` du moteur au demarrage : un bytecode perime
  ferait tourner un code different de la source que `dsl_hash` a hachee.

Sans `RS_ENGINE`, le comportement est inchange : les executions manuelles et
les canaris continuent de fonctionner depuis `engine/`.

Verification faite sur les journaux : aucun `dsl_hash` ne porte deux formes de
`level_uses`, donc rien n'indique qu'un hash ait jamais designe un code autre
que le sien. L'invariant 2 a tenu. Le test est toutefois **incomplet** : il ne
detecte que les melanges observables dans les enregistrements.

## 2026-08-26 - T1 est sans domaine, et la technique de repli serait redondante
Mesure demandee avant de traiter le symptome. `t1_regions()` n'accepte qu'un
ALLDIFF de taille exactement d. Dans l'espace reellement explore :

    connect     n=4 d=3   0 systeme sur 600 eligible, 0 ALLDIFF generee
    static-ref  n=4 d=3   0 systeme sur 590,          0 ALLDIFF generee
    baseline    n=4 d=4   126 sur 600 (21 %), 322 ALLDIFF de taille d

Zero, pas "quasiment zero" -- et zero ALLDIFF **tout court**, y compris pour la
famille `static`. La cause precede la restriction de `t1_regions()` : a n=4 les
regions structurelles ont 4 cases, et un ALLDIFF sur 4 cases avec d=3 valeurs
est infaisable par principe des tiroirs. Le generateur n'en produit donc aucune.

**T1 n'est ni fausse ni inerte : elle est SANS DOMAINE.** Elle redevient utile
des que d egale la taille des regions -- `baseline` a d=4. C'est le passage de
la file a d=3 qui l'a eliminee, pas un defaut de la technique.

**Consequence a ne pas manquer** : `apply_T1` parcourant une liste vide rend
`(False, False)`, donc `saturate_low()` -- censee saturer T0+T1 -- **est
exactement T0 seul** dans cet espace.

La technique de repli envisagee -- supposer v, saturer T0 seul au lieu de
T0+T1, eliminer sur contradiction -- serait donc **T2 a l'identique**, pas un
T2 affaibli. Inseree comme palier intermediaire elle reclasserait tous les T2
existants et laisserait T2 vide : un renommage, aucun pouvoir discriminant
supplementaire. Ecartee sans etre codee.

Piste retenue a la place, non implementee : **contradiction a propagation
bornee** -- supposer v, appliquer une seule passe de T0 au lieu d'iterer
jusqu'au point fixe. Strictement entre T0 et T2, sans dependance a une
structure de region.

**Lacune d'outillage identifiee** : `canary6` verifie qu'une technique se
DECLENCHE, pas qu'elle DISCRIMINE. Une technique redondante le passe sans
broncher. Avant d'implementer la piste ci-dessus, y ajouter une comparaison de
la distribution de `max_level` avant/apres.


## 2026-08-26 - la mesure continue exige un test, et il change la lecture
La mesure continue est conservee mais n'est plus interpretable sans test.
`summarize.py` applique un test de permutation bilateral (2000 melanges,
stdlib seule -- l'invariant "pas de dependances" tient) et refuse de conclure
sous 20 candidats par groupe ou au-dessus de p = 0,05.

    615abe43d6bc  945 candidats  p = 0.0060  significatif
    89c65c03c4ad  213 candidats  p = 0.7586  non significatif
    0327bdc4c76a  107 candidats  p = 0.1569  non significatif
    12564867381b   75 candidats  p = 0.8296  non significatif

**Une seule serie sur quatre est significative**, et c'est
**`615abe43d6bc`, marquee NON REPRODUCTIBLE** : le seul resultat solide vient
du moteur dont la source n'existe plus, et il n'est pas rejouable.

Le "meme sens sur trois series sur quatre" avance au tour precedent etait une
tendance jolie prise pour un resultat -- precisement ce que CLAUDE.md
interdit. Le test etait la bonne exigence.

Reserve permanente, portee dans CLAUDE.md et dans `summary.md` a cote du
chiffre : cette mesure evalue l'**EFFORT** de deduction, pas la **PROFONDEUR**.
Un systeme qui demande trois T2 est plus laborieux, pas plus profond. Les
confondre serait la cinquieme metrique du projet a mesurer autre chose que ce
qu'elle annonce.

Reouverture : reevaluer quand `89c65c03c4ad`, seule serie reproductible en
croissance, aura plusieurs centaines de candidats par groupe.

## 2026-08-26 - le scheduler ne commite plus que ses propres chemins
Deuxieme manifestation du meme defaut : le serveur opere sur un arbre de
travail partage. Le gel de `engine/` reglait la lecture du code ; celle-ci
concerne l'index git.

`git add -A summary.md found/ && git commit -m 'auto: resume <tag>'` : le
`git add` est restreint, le `git commit` ne l'est pas. Sans pathspec, il valide
**tout l'index**, y compris ce qu'une session concurrente y a mis en attente.
Un commit de travail a ainsi ete absorbe dans `a5725ba auto: resume connect`,
avec le mauvais message et l'auteur `rulesearch@local`.

Correction : `git commit ... -- summary.md found/`. Le scheduler ne peut plus
valider que ses propres fichiers.

L'historique n'est pas reecrit -- `a5725ba` garde son message trompeur, et
c'est ici qu'on le note. Consequence pour la lecture de l'historique : un
commit `auto: resume` anterieur au 26/08/2026 peut contenir autre chose que ce
que son message annonce.

Reouverture : si d'autres interferences apparaissent (index, stash, branche),
la vraie reponse est que le scheduler travaille sur un clone dedie plutot que
sur l'arbre de developpement.

## 2026-08-26 - corriger un biais en a cree un autre, invisible plusieurs heures
La file avait ete ramenee a `connect` et `static-ref` **tous deux a d=3** pour
supprimer un biais reel : comparer d=2 a d=4 rendait la mesure inexploitable,
l'ecart pouvant venir du domaine et non de la connectivite. La correction etait
juste.

Elle a eu une consequence que personne n'a vue : **imposer d=3 a supprime un
niveau entier de la hierarchie de deduction.** A n=4, les regions structurelles
ont 4 cases ; un ALLDIFF sur 4 cases avec 3 valeurs est infaisable par principe
des tiroirs. Le generateur n'en produit donc aucun, `t1_regions()` est vide, et
T1 -- correcte, testee, non modifiee -- n'a plus **aucun domaine
d'application**. La hierarchie annoncee a trois niveaux n'en avait plus que
deux, T0 et T2.

Le symptome (T1 a 0 invocation) est reste invisible plusieurs heures, jusqu'a
ce que la mesure de `level_uses` le fasse apparaitre. Rien ne l'a signale :
aucun canari ne verifiait qu'une technique conserve un domaine dans l'espace
reellement explore, et le resume n'affichait que `max_level`, ou l'absence de
T1 ne se distingue pas d'un T1 simplement rare.

**Ce qu'il faut en retenir, et qui depasse ce cas** : corriger un biais est une
modification de l'espace explore, donc un changement de ce qu'on mesure. Une
correction de comparabilite peut detruire une mesure ailleurs. Verifier apres
coup que les techniques et les metriques ont toujours un domaine.

Correction : la file passe a **quatre** configurations -- `connect` et
`static-ref` a d=3, plus `connect-d4` et `static-d4` a d=4. A d=4 les ALLDIFF
sur regions de 4 cases redeviennent faisables, T1 retrouve un domaine et la
hierarchie ses trois niveaux. On obtient de surcroit la comparaison
connect/static **aux deux domaines**, ce qui repond a la question de robustesse
laissee ouverte : un resultat obtenu a un seul domaine ne se generalise pas.

Reouverture : si T1 reste a 0 invocation sur les tags `-d4`, la cause n'est pas
le domaine et il faut la chercher ailleurs.


## 2026-08-26 - canary6 : se declencher ne suffit pas, il faut reclasser
Ajout d'un second controle, ne apres qu'une technique redondante ait failli
etre codee. Le premier controle (declenchement) ne l'aurait pas arretee.

Le cas concret : `t1_regions()` etant vide dans l'espace explore,
`saturate_low()` vaut T0 seul ; une technique definie comme "contradiction
saturant T0 seul" y est donc **identique a T2**. Elle se serait invoquee
normalement, aurait passe le canari, et n'aurait rien mesure de neuf --
reclassant simplement les T2 existants sous une nouvelle etiquette.

`canary6` compare desormais la distribution de `max_level` **avec et sans** la
technique du niveau le plus eleve. Si elle est identique, la technique est un
**renommage** et le canari echoue.

Verifie dans les deux sens : le controle passe sur T2 (8 systemes reclasses,
{0:27, 1:2} -> {0:21, 2:8}) et detecte bien l'egalite quand on compare un
niveau a lui-meme, cas qui simule une technique redondante.

Invariant qui en decoule : **une technique de deduction doit creer un palier,
pas deplacer une etiquette.** Se declencher est necessaire, pas suffisant.


## 2026-08-26 - le resume traite l'absence de resultat reproductible comme telle
Le test de permutation ne donnait un p significatif que sur `615abe43d6bc`,
serie **NON REPRODUCTIBLE** ; les trois series reproductibles ne concluaient
pas. Afficher ce p en tete revenait a mettre en avant un resultat non
rejouable, issu d'un moteur dont la source n'existe plus.

`summarize.py` distingue desormais les deux cas. Un p significatif sur une
serie non reproductible est affiche **A NE PAS RETENIR**, et une section de
synthese indique explicitement quand **aucune serie reproductible n'etablit
l'ecart** -- en precisant qu'il s'agit d'une **absence de resultat** et non
d'une refutation : les echantillons rejouables sont encore trop petits.

C'est la contrepartie de la decision de conserver les series orphelines : on
les garde comme donnees, mais elles ne peuvent pas porter une conclusion.
