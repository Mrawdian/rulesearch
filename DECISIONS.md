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

## 2026-08-26 - sixieme metrique confondue, et le confondant etait dans la colonne d'a cote
La "resistance a T0" avait d'abord ete mesuree comme **fraction de la grille
entiere** remplie par T0 seul :

    connect    d=3   74,2 %
    static-ref d=3   98,0 %

24 points d'ecart, presente comme le meilleur discriminant trouve. **C'etait
un artefact de la densite d'indices.** `connect` recoit 6,0 indices en moyenne
et `static` 9,5 : `static` part de 59 % de grille deja remplie contre 37 %. En
points AJOUTES par T0, les deux sont identiques -- 36,7 contre 38,6.

Le confondant, `clue_frac`, etait **journalise depuis le debut et affiche dans
la colonne voisine du meme tableau**. Il n'a pas ete regarde.

C'est la **sixieme** metrique du projet a mesurer autre chose que ce qu'elle
annonce : T1 faux, profondeur v1 saturante, T2 sature, T3 inerte, effort
confondu avec profondeur, et maintenant resistance confondue avec densite.

**Regle qui en decoule, et qui devient un invariant** : toute nouvelle metrique
doit etre **testee contre les variables deja journalisees** avant d'etre
adoptee -- `clue_frac` en premier, puis `total_grids`, `n`, `d`. Le confondant
n'est presque jamais exotique ; il est dans le journal, a cote.

**Correction** : normalisation sur les cases INCONNUES et non sur la grille.

    resistance = cases restantes apres saturation T0 seule
                 / cases inconnues du puzzle initial

Le signal survit et se renforce. Recalcul sur les **systemes des journaux**
(rejeu exact par `seed` + `idx`, instances fraiches a graine fixe), candidats
uniquement :

    d=3 : connect 39,2 %  contre static 18,1 %   facteur 2,2   p = 0,0005
    d=4 : connect 40,4 %  contre static 23,2 %   facteur 1,7   p = 0,0005

Significatif aux deux domaines, ce qui repond en meme temps a la question de
robustesse : le resultat ne depend pas d'un domaine particulier.

Ecart avec l'estimation faite a la main sur l'echantillon regenere (facteur 8) :
le rejeu porte sur les seuls **CANDIDATS** journalises, sous-ensemble filtre
(bien poses, peu d'indices), alors que la mesure initiale prenait toute
instance resoluble. Les candidats `static` resistent plus que les systemes
`static` en general. Le facteur reel est ~2, pas ~8.

**Adoptee comme metrique principale**, pour trois raisons cumulees :
1. elle ne sature pas, contrairement a `max_level` (100 % partout) ;
2. elle est significative aux deux domaines ;
3. **elle ne depend d'aucune technique dont la disponibilite varie entre les
   groupes compares.** C'est decisif : `max_level` est confondu a d=4 parce que
   `static-d4` dispose de T1 (34,4 % de regions eligibles) et `connect-d4`
   jamais (0,0 %, les familles connect/relational ne produisent aucun ALLDIFF).
   Comparer la profondeur de deux groupes dont l'un a trois niveaux et l'autre
   deux n'a pas de sens. La resistance a T0 n'a pas ce defaut : T0 est
   disponible partout.

Le biais de disponibilite de T1 a d=4 devient donc **secondaire** : il reste
reel, mais il n'affecte plus la mesure qui fait foi.

**Journalisation** : ce sont les **deux bruts** qui sont enregistres --
`t0_unknown` et `t0_left` -- et non le ratio. Un ratio journalise ne se
recalcule pas si la normalisation change ; deux bruts, si. La lecon vient
directement de cette entree : la premiere normalisation etait fausse, et
n'aurait pas ete rattrapable si seul le ratio avait ete ecrit.

`max_level` est conserve dans `summary.md`, explicitement marque **SATURE**.

Reouverture : si la resistance sature a son tour (tout proche de 0 ou de 1),
ou si un confondant non teste apparait, reprendre la liste des variables
journalisees et tester contre chacune.


## 2026-08-26 - canary7 : la metrique principale doit separer ses deux bornes
Une metrique principale qui ne distinguerait pas ses cas extremes ne mesurerait
rien, et l'historique du projet montre que ca passe inapercu.

`canary7` verifie aux deux bornes :
- **resistance nulle** sur une instance que T0 resout integralement ;
- **resistance strictement positive** sur une instance qu'il ne resout pas.

Il echoue aussi s'il n'arrive pas a **exhiber** l'un des deux cas : ne pas
trouver d'instance resistante signifierait que la mesure est constante, donc
sans pouvoir discriminant. C'est la meme exigence que le controle B de
`canary6` -- se declencher, ou ici se calculer, ne suffit pas : il faut
separer.

## 2026-08-26 - resistance a T0 : ACQUISE, avec le detail de ce qui n'a pas pu etre teste
Invariant 7bis applique a la metrique elle-meme. Aucun des quatre controles ne
la tue. Elle est adoptee, mais deux d'entre eux sont partiels et c'est dit ici
plutot que passe sous silence.

**1. Circularite -- ECARTEE, et c'etait le risque le plus serieux.**
L'inquietude etait fondee : un systeme que T0 resout instantanement tombe en
PLAT, donc est exclu des candidats. Le filtre de candidature selectionne bien
de la resistance, la mesure le confirme :

    PLAT           0,9 %      LIBRE          7,2 %
    SUR-CONTRAINT 34,0 %      CANDIDAT      36,1 %      DEVINETTE 56,2 %

Mais l'ecart connect/static **ne vient pas de la** : il survit hors du filtre,
et il y est **plus grand** :

    CANDIDATS seuls   connect 44,4 % (n= 50)  static 26,8 % (n= 45)  p=0,0030
    NON candidats     connect 19,8 % (n=210)  static  5,1 % (n=215)  p=0,0005
    TOUS evaluables   connect 24,5 % (n=260)  static  8,9 % (n=260)  p=0,0005

Controle plus severe, **a verdict egal**, qui neutralise entierement la
selection :

    LIBRE     connect 14,3 % (n=59)  static  4,5 % (n=154)  p=0,0010
    CANDIDAT  connect 50,6 % (n=55)  static 24,6 % (n= 49)  p=0,0005
    PLAT      connect  1,3 % (n=59)  static  2,1 % (n= 54)  p=0,5077
    SUR-CONTRAINT : static n=3, non testable

L'absence d'ecart sur PLAT n'est pas un echec : PLAT designe precisement les
systemes que T0 resout, la mesure y est au plancher dans les deux familles
(1,3 % et 2,1 %). C'est meme une verification de coherence.

**2. total_grids -- PASSE sur la strate dominante, non testable sur l'autre.**
Premiere tentative **invalide** : terciles effondres, parce que `total_grids`
est **censure a droite** par `cap = MIN_GRIDS + 1 = 13`. Distribution reelle :
`{1:2, 2:39, 3:13, 4:24, 13:442}`. Refait sur la seule coupure que la donnee
autorise :

    au plafond (>=13)   connect 23,7 % (n=185)  static 7,8 % (n=257)  p=0,0005
    sous le plafond     connect 33,8 % (n= 75)  static 33,3 % (n=  3)  static n=3

La strate au plafond represente **85 % des donnees** et l'ecart y survit. Sous
le plafond, `static` n'a que 3 systemes : **non testable**. A noter, sans y
lire quoi que ce soit, que les deux estimations ponctuelles y sont quasi egales
(33,8 contre 33,3).

Le confondant est fortement desequilibre -- `connect` est au plafond a 71 %,
`static` a 99 % -- ce qui rendait ce controle indispensable.

**3. d -- PASSE aux deux domaines, avec une stabilite frappante.**

    d=3  connect 24,4 % (n=130)  static 8,6 % (n=130)  p=0,0005
    d=4  connect 24,7 % (n=130)  static 9,1 % (n=130)  p=0,0005

**4. n -- NON TESTABLE.** `n` vaut 4 dans toutes les configurations de la file :
aucune variance, aucun test possible. **Marque non teste, pas reussi.** A
refaire si n=5 est ajoute.

**Controle supplementaire, clue_frac stratifie** (la normalisation suffit-elle,
ou reste-t-il un effet residuel ?) :

    tercile faible  connect 30,3 % (n=94)  static 17,0 % (n= 57)  p=0,0120
    tercile moyen   connect 23,0 % (n=60)  static  9,1 % (n= 90)  p=0,0005
    tercile eleve   connect  5,4 % (n=31)  static  2,1 % (n=110)  p=0,1454

Survit dans deux terciles sur trois. Le troisieme n'est pas significatif mais
va dans le meme sens (facteur 2,6) avec seulement 31 systemes `connect` :
manque de puissance, pas contradiction. Il subsiste une correlation residuelle
entre resistance et densite d'indices **a l'interieur de chaque famille**
(r = -0,29 pour connect, -0,31 pour static) : plus d'indices, moins de
resistance. Elle joue dans les deux familles de la meme facon, donc ne
fabrique pas l'ecart.

**Verdict : metrique ACQUISE.** Aucun controle ne la tue, l'ecart survit a la
candidature, au verdict, au domaine, au nombre de grilles et a la densite
d'indices. Limites a rappeler a chaque usage :
- `n` n'est pas teste et ne peut pas l'etre a n=4 seul ;
- la strate `total_grids` sous le plafond n'est pas testee (static n=3) ;
- le tercile de forte densite d'indices n'est pas significatif ;
- tous les p viennent de tests de permutation sans correction pour tests
  multiples, sur des candidats non independants (memes graines, meme
  generateur).

Reouverture : si n=5 est ajoute, refaire le controle 4. Si la censure de
`total_grids` est levee (cap plus haut), refaire le controle 2 en terciles.


## 2026-08-26 - graine d'instance journalisee
Defaut de reproductibilite constate en rejouant les journaux : `gen_system`
etant deterministe a partir de `random.Random(seed)`, les **systemes** se
rejouent exactement, mais pas les **instances** -- `random_solution` et
`minimal_clues` consomment le `random` global, dont l'etat depend de tout ce
qui a ete evalue avant dans le bloc.

Correction : `inst_seed = seed * 1000 + idx`, applique par `random.seed()`
avant chaque systeme, et journalise dans le record. Rejouer une evaluation
devient : `gen_system` x `idx`, puis `random.seed(inst_seed)`.

Ecart avec la formulation initiale de la demande, assume : un
`random.Random(...)` **local** passe aux fonctions d'instance aurait ete plus
propre, mais `random_solution` et `minimal_clues` vivent dans `engine/` et
consomment le module global -- leur passer un generateur demanderait de
changer leur signature, donc de toucher au moteur. Le resemage du global
atteint le meme resultat sans y toucher.

Effet de bord : le flux aleatoire des instances change. Chaque systeme part
desormais d'un etat frais au lieu de continuer le flux du bloc. Sans
consequence sur la validite -- les systemes generes sont inchanges,
`gen_system` utilisant son propre generateur -- mais les instances des blocs a
venir ne sont pas celles qu'on aurait eues sans ce changement.

`dsl_hash` inchange : `run.py` n'est pas dans `engine/`.

## 2026-08-26 - A est OUVERT. Decision d'architecture : feasible() est CONSERVEE
Le chantier A (etat de candidats explicite) est ouvert. Sa condition
d'ouverture n'est pas le gain de debit mais le fait que **la propagation sur
domaines est strictement plus forte que le forward-checking actuel**, donc
qu'elle detruirait la metrique acquise si rien n'etait fait.

### Decision : la propagation s'AJOUTE, elle ne remplace pas

Chaque contrainte gardera `feasible(g)` **inchangee** et recevra
`propagate(dom)` **a cote**. Trois raisons, dans l'ordre de force :

1. **Un oracle independant est impose par le risque asymetrique.** Un
   propagateur qui retire un candidat de trop **ne plante pas** : il rend une
   solution FAUSSE. Cela ne se detecte que si quelque chose de **non contamine**
   sait ce qui est vrai. Si propagation et verite partagent leur code, plus rien
   ne peut attraper l'erreur.
2. **Le solveur exhaustif utilise `feasible()`**, et c'est lui qui produit la
   verite contre laquelle `canary3` valide les propagateurs. Un code partage
   rendrait `canary3` aveugle -- il comparerait une erreur a elle-meme.
3. **Le corpus fige de `canary8` en depend.** `t0_legacy` appelle `feasible()` :
   si sa semantique bouge, le verrou bouge. Un verrou qui bouge n'est pas un
   verrou.

**Cout assume : duplication de la logique de chaque contrainte**, une fois en
`feasible` et une fois en `propagate`. C'est le prix de l'independance de
l'oracle, et il est paye volontairement.

### Ordre impose du chantier

1. **Gel de T0-historique** (fait) : `engine/t0_legacy.py` + `canary8`.
2. `canary3` etendu **AVANT** chaque propagateur, jamais apres.
3. Les sept faciles d'abord (AllDiff en premier, gabarit des autres), les deux
   moyens ensuite, **Connected en dernier** -- et seulement avec le retrait par
   inaccessibilite et le forcage par point d'articulation, la detection de
   contradiction actuelle etant conservee telle quelle.
4. **Un seul propagateur par commit.** Jamais deux. C'est le terrain exact du
   risque asymetrique.
5. **Ne pas redefinir la hierarchie pour l'instant.** La propagation absorbera
   T0 et une partie de T1 : c'est attendu. La nouvelle hierarchie se decidera
   quand elle tournera, pas avant.

### Sur l'affirmation Steiner

Le filtrage complet de la connexite est **suppose** NP-difficile (probleme de
type Steiner). Cette affirmation est **non verifiee dans ce projet** et **ne
sert pas d'argument** : on ne vise pas le filtrage complet, seulement des
regles saines et incompletes. Marquee comme telle dans `PERIMETRE-A.md`.


## 2026-08-26 - gel de T0-historique : pourquoi le module ne suffisait pas
`engine/t0_legacy.py` fige le propagateur de reference de la metrique acquise.

**Raison du gel, et elle est structurelle** : la resistance a T0 mesure la
non-localite **relativement a un propagateur donne**. Renforcer le propagateur
deplace la frontiere qu'on mesure -- un T0 plus fort resoudrait davantage de
systemes a connectivite, donc mesurerait **moins bien exactement ce qu'il doit
mesurer**. Le propagateur de reference est fige **par nature**, pas par
commodite d'archivage.

**Le gel du fichier ne suffisait pas.** `t0_legacy` appelle
`rs.feasible(g, changed=i)`, dont le comportement vit dans les classes de
contraintes que A va toucher. Une modification de `feasible()` changerait les
valeurs produites **sans que le fichier gele ait bouge d'une ligne**.

D'ou `canary8`, qui ne compare pas a du code courant -- lequel va changer par
construction -- mais a des **nombres figes** : `canary/t0_reference.json`, 60
entrees du 26/08/2026. Chaque entree fige la recette du systeme, son label, **le
puzzle lui-meme**, et les deux valeurs attendues.

Le puzzle est stocke tel quel plutot que regenere : `random_solution` et
`minimal_clues` vivent dans `engine/` et peuvent legitimement changer sous A.
Les regenerer rendrait le canari sensible a des evolutions permises.

**Equilibre du corpus** : le tirage naturel donnait 47 entrees a resistance
nulle contre 13 positives. Or ce sont les **positives** qui detectent un
propagateur RENFORCE -- un T0 plus fort laisse moins de cases. Les nulles sont
au plancher et detectent l'affaiblissement. A rendant le propagateur plus fort,
la proportion a ete inversee : **40 positives, 20 nulles**, les deux sens
restant couverts.

Consequence : `dsl_hash` change (ajout dans `engine/`). La serie pre-A est
close de toute facon.

Reouverture : aucune. Ce module ne doit jamais etre modifie. Si une divergence
apparait, c'est le reste du moteur qu'il faut corriger.

## 2026-08-26 - la force du propagateur Connected est un CHOIX DE CONCEPTION, pas un parametre a maximiser
Note ecrite a l'ouverture de A, six propagateurs avant d'en avoir besoin,
precisement parce qu'on l'aura oubliee d'ici la.

**La force du propagateur `Connected` n'est pas un parametre a maximiser. Elle
definit la frontiere entre ce que le moteur traite comme local et ce qu'il ne
peut pas decomposer. Un `Connected` trop bien propage rendrait le moteur
incapable d'observer la non-localite qu'il etudie.**

C'est le meme piege que le T0 renforce, a un autre etage. La resistance a T0
mesure la non-localite **relativement a un propagateur** ; si le propagateur de
la seule contrainte non decomposable devient assez fort pour la decomposer en
pratique, l'objet d'etude disparait dans l'instrument.

### La dissymetrie qui rend la chose vivable

Les **sept propagateurs faciles** peuvent etre aussi forts qu'on veut. Ils
portent des contraintes **decomposables par nature** : les renforcer ne detruit
rien, cela ne fait qu'ameliorer le traitement de ce qui est deja local.

C'est le **contraste** entre eux et `Connected` qui produit le signal.
Renforcer les locaux **augmente** meme ce contraste. La contrainte de retenue
ne porte donc que sur un propagateur sur dix.

### Consequence pratique, A DECIDER A L'ETAPE 5 ET PAS AVANT

Le propagateur `Connected` devra **probablement rester deliberement faible** --
retrait par inaccessibilite et forcage par points d'articulation, rien de plus
-- **non par difficulte d'implementation mais par choix de conception**. La
difficulte technique (filtrage complet hors de portee) et le choix de
conception coincident ici, ce qui pourrait faire croire que le second n'est
qu'une justification du premier. Ce n'est pas le cas : meme si le filtrage
complet devenait accessible, il ne faudrait pas l'adopter sans mesure.

**Et il faudra mesurer l'effet de son ajout sur la resistance a T0 avant de
l'adopter, exactement comme pour une metrique.** Le protocole existe deja :
`canary8` compare a un corpus fige, l'invariant 7bis impose de tester toute
mesure contre les variables journalisees. Ici la question est symetrique --
non pas "cette mesure est-elle confondue ?" mais "ce propagateur detruit-il la
mesure ?".

**Critere de decision pour l'etape 5, FERME le 26/08/2026** : si l'ajout du
propagateur `Connected` rapproche `connect` de `static` sur la resistance, le
propagateur a mange le signal.

**Reponse par defaut dans ce cas** : garder `t0_legacy` comme **reference
unique de la metrique**, et laisser le propagateur faire son travail de debit
sans toucher a la mesure. C'est exactement ce que le gel permet, et cela separe
proprement **l'instrument** de **l'accelerateur** -- deux roles qu'il n'y a
aucune raison de faire porter au meme code.

Reouverture : cette note ne se tranche pas, elle se rappelle. Elle est a relire
integralement au moment d'ecrire le propagateur `Connected`.

## 2026-08-26 - deux regles de canari, tirees de deux echecs distincts

### Les cas limites se construisent a la main

Un canari qui attend ses cas du generateur **ne teste que ce que le generateur
produit**. Deja paye deux fois :

- **T1** : code correct, restriction correcte, **zero invocation sur 8991
  systemes**. L'espace genere ne contient aucun ALLDIFF de taille d, donc le
  cas ou T1 s'applique n'apparaissait jamais. Aucun canari ne l'a signale
  parce qu'aucun ne construisait ce cas.
- **Le propagateur AllDiff a venir** : le generateur ne produit `AllDiff` que
  si `d >= n`, sur des regions de taille `n`. Les regions de taille `!= d` --
  precisement la ou T1 s'etait trompee -- n'apparaissent qu'avec `d > n` ou via
  les cages. Un canari qui les attendrait du generateur ne testerait rien.

**Regle** (invariant 8) : le generateur couvre le cas ordinaire, les bords se
construisent a la main.

### Un canari doit avoir ete vu echouer

Le test negatif devient la norme : on construit deliberement le defaut que le
canari doit attraper, et on verifie qu'il l'attrape. Un canari jamais vu rouge
est une decoration.

Fait pour `canary5` (alarme), `canary6` (renommage), `canary7` (bornes),
`canary8` (propagateur renforce).

**Anecdote qui justifie la regle a elle seule** : la premiere version du test
negatif de `canary8` renforcait T0 avec **T1**. Zero divergence detectee -- non
parce que le canari est aveugle, mais parce que **T1 est un no-op dans cet
espace**, fait etabli le matin meme et oublie l'apres-midi. Le test ne prouvait
rien tout en ayant l'air de conclure. Refait avec T2, qui se declenche
reellement.

La lecon depasse le cas : **un test negatif doit lui-meme etre verifie comme
tel**. Construire un defaut qui n'en est pas un donne une fausse assurance,
exactement du meme genre que celle qu'on cherche a eviter.


## 2026-08-26 - propagateur AllDiff : filtrage minimal, Regin ECARTE
Le propagateur `AllDiff` se limite au retrait de la valeur assignee chez les
autres cellules de la region. C'est la seule regle dont la validite ne depend
d'aucune hypothese sur la taille de la region.

**Le filtrage par couplage (Regin) est ECARTE -- et il n'est pas faux.** Il
donne la coherence de domaine complete pour `AllDifferent` et c'est de
l'etat de l'art. Il est ecarte parce qu'il **n'est pas necessaire au gabarit** :
`AllDiff` sert de modele aux six autres propagateurs faciles, et chaque regle
supplementaire est une occasion de retirer un candidat de trop.

Principe general applique ici, valable pour les dix propagateurs : **ne rien
conclure quand on ne peut pas conclure**. En cas de doute sur une regle de
filtrage, elle ne rentre pas. Un propagateur incomplet est **correct** ; un
propagateur trop zele produit des **solutions fausses** -- et ne plante pas,
c'est tout le probleme.

**Note pour qui relira** : ce propagateur est deliberement plus faible que
l'etat de l'art. Ce n'est pas un oubli. Sa reouverture demande **une mesure**
-- montrer que le filtrage supplementaire change quelque chose de mesurable au
debit ou a la profondeur -- et non une intuition du type "on pourrait faire
mieux".

Attention particuliere pour `AllDiff` : la region peut avoir une taille
**differente de d**. Si `|R| > d`, la contrainte est infaisable (principe des
tiroirs) ; si `|R| < d`, elle est satisfaisable mais **aucun raisonnement du
type "chaque valeur doit apparaitre" n'y est valide**. C'est exactement la
configuration ou T1 s'etait trompee. Le canari construit ces cas a la main.

## 2026-08-26 - la duplication deliberee est un invariant, pas une dette
Note ecrite sans qu'elle soit demandee, le risque etant actif des maintenant.

Le gel de T0-historique cree une situation qu'un lecteur ultérieur lira
naturellement comme un defaut : `engine/t0_legacy.py` contient des copies
quasi identiques de `candidates` et `apply_T0`, qui vivent aussi dans
`deduction.py`. Le reflexe d'un developpeur competent est de factoriser.

**Factoriser detruirait le gel**, et surtout : **rien ne planterait**. Le
moteur continuerait de tourner, les journaux continueraient de se remplir, et
la metrique de resistance suivrait silencieusement le propagateur en cours
d'evolution au lieu de la reference figee. Seul `canary8` crierait -- et la
tentation immediate serait de regenerer son corpus pour le faire taire, ce qui
achèverait la destruction.

C'est exactement la forme de defaillance que le projet paie depuis le debut :
correct au sens du code, sans prise sur ce qu'il pretend garantir.

**Le meme piege se reproduira a chaque propagateur.** La decision d'architecture
de A impose que chaque contrainte porte `feasible()` **et** `propagate(dom)`,
soit la meme logique deux fois. Ce n'est pas une dette technique a resorber :
c'est le **prix de l'independance de l'oracle**, paye volontairement, sans
lequel `canary3` compare une erreur a elle-meme.

**Regle** (invariant 10) : une duplication documentee comme deliberee est un
invariant. Avant de factoriser deux fonctions semblables dans `engine/`,
verifier qu'aucune n'est declaree gelee.

Signal a surveiller : si `canary8` echoue apres un commit dont le message parle
de "nettoyage", "simplification", "factorisation" ou "DRY", c'est
vraisemblablement ce piege. Regarder le diff avant de toucher au corpus.

## 2026-08-26 - AllDiff : premier propagateur de A, et la forme des neuf suivants

**Une seule regle de filtrage** : une cellule dont le domaine est reduit a
`{v}` interdit `v` aux autres cellules de la region. Valide pour **toute**
taille de region, parce qu'elle ne suppose jamais que chaque valeur doive
apparaitre -- exactement l'hypothese sur laquelle T1 s'etait trompe.

**Ecarte deliberement** : tout raisonnement de comptage, et le filtrage par
couplage maximal de Regin (voir l'entree dediee). Le propagateur ne doit rien
conclure quand il ne peut pas conclure ; **un propagateur incomplet est
correct, un propagateur trop zele produit des solutions fausses**.

**Ce qui rend la regle plus forte que l'existant** : elle porte sur les
domaines **singletons**, pas sur les cellules **assignees**. Une cellule peut
etre reduite a une seule valeur sans avoir ete assignee -- c'est tout l'ecart
entre forward-checking et propagation.

### Le module est separe, et c'est la garantie, pas une commodite
`engine/propagate.py` est un module a part : `rulesearch.py` et `dsl2.py` ne
bougent pas d'une ligne. La conservation de `feasible()` -- condition de
l'independance de l'oracle -- devient ainsi **verifiable par diff**. Une revue
humaine peut se tromper ; un diff vide, non.

### Question 2 tranchee par la MESURE, pas a priori
Sur `|R| > d` (infaisable par principe des tiroirs), le retrait simple
**n'atteint pas** la contradiction sur grille vide -- aucun domaine n'est
singleton, la regle ne s'amorce pas. Il l'atteint **des qu'un seul indice est
pose**. Les deux cas sont journalises par `canary3`.

**Aucune regle n'a ete ajoutee pour combler ce trou.** `feasible()` detecte
deja l'infaisabilite et reste l'oracle. Un propagateur qui laisse passer une
infaisabilite est **incomplet, pas faux** : c'est la moitie correcte du
compromis.

### Le test negatif, et ou il mord
`canary3` injecte un AllDiff **trop zele** : le hidden single non conditionne,
c'est-a-dire le bug T1 reecrit dans le langage des domaines. Resultat :
**0 violation sur `|R| == d`** (ou la regle est effectivement valide) et
**46 sur `|R| < d`**. Le canari discrimine donc au bon endroit, et pas par
accident de couverture.

**Consequence** : `dsl_hash` change (nouveau fichier dans `engine/`) alors
meme que **le comportement de production est inchange** -- `propagate.py`
n'est pas branche sur la hierarchie de deduction. Une serie se clot pour un
module inerte. C'est le prix de hacher le repertoire plutot que le chemin
d'execution, et c'est preferable a l'inverse.

## 2026-08-26 - engine_active : attenuer les ruptures de serie SANS toucher au hash

**Constat** : `dsl_hash` porte sur tout `engine/`. Pendant A, chaque
propagateur ajoute rompt la serie **alors qu'il ne tourne pas**. Neuf ruptures
pour des modules inertes.

**Decision : la regle du hash ne change pas.** L'asymetrie est ecrasante -- un
hash qui **rate** un changement est catastrophique, un hash qui en **signale un
inoffensif** coute une rupture de serie. Neuf ruptures est un prix acceptable.

**Attenuation, a cote et non a la place** : le record porte desormais
`engine_active` (liste des modules reellement sur le chemin d'execution) et
`engine_active_hash` (hash de leur **contenu**). `summarize.py` peut alors
proposer un regroupement de series a `dsl_hash` differents, **en le disant
explicitement**. Le hash reste l'invariant dur ; le regroupement est une
**lecture**, documentee comme telle.

**Le regroupement se fait sur le hash du CONTENU, jamais sur la liste de
noms.** Deux series peuvent declarer les memes modules actifs avec du code
different : regrouper sur les noms fusionnerait des series incomparables --
exactement le mode de defaillance que `dsl_hash` existe pour empecher,
reintroduit un etage plus bas. C'est le motif du projet applique au dispositif
cense l'attenuer, et il fallait le voir avant de l'ecrire.

**`ENGINE_ACTIVE` est une liste TENUE A LA MAIN**, et ne peut pas etre autre
chose : aucune detection automatique ne distingue un module **importe** d'un
module **actif**. `propagate.py` doit y etre absent tant qu'il n'est pas
branche. `run.py` journalise aussi `engine_inertes` dans `config.json` pour que
l'omission soit visible plutot que silencieuse.

**Benefice retrospectif, qui est la vraie raison** : sans ce champ, on ne
saurait plus, une fois le chantier fini, quelle serie a tourne avec quels
propagateurs branches.

**Enregistrements anterieurs** : ils n'ont pas le champ. Ils forment un groupe
"inconnu" a part et ne sont **jamais** fusionnes avec les autres.


## 2026-08-26 - le risque d'interaction a n grand ne se couvre pas par canary3

**Point ferme maintenant plutot qu'au sixieme propagateur.**

Les cas limites de `canary3` sont a n=2 et n=3, parce que **l'enumeration
exhaustive des solutions est non negociable** comme verite de reference : la
valider contre `feasible()` seule ferait comparer le propagateur a lui-meme.
Les cas limites **resteront donc petits**, et c'est acquis, pas une dette.

Le risque qu'un bug d'interaction n'apparaisse qu'a n plus grand est reel et
**ne se couvre pas la**. Il se couvre par le **solveur exhaustif lui-meme** :

    au moment du branchement des propagateurs sur la hierarchie, un systeme
    resolu par propagation doit avoir la MEME solution unique que celle
    comptee par `count_solutions`.

**A ajouter au moment du branchement, PAS avant** : tant qu'aucun propagateur
n'est sur le chemin d'execution, ce controle n'aurait rien a comparer.

## 2026-08-26 - Count : deux sens dans le meme commit, et la condition qui l'autorise

`Count(region, val, lo, hi)` porte deux bornes, donc deux regles :
- **INTERDICTION** : si le minimum atteignable vaut deja `hi`, aucune autre
  cellule ne peut prendre `val` ;
- **FORCAGE** : si le maximum atteignable vaut `lo`, toutes les cellules qui
  peuvent encore prendre `val` doivent la prendre.

Minimum atteignable = cellules deja reduites au singleton `{val}`. Maximum
atteignable = cellules dont le domaine contient encore `val`. Comme pour
AllDiff, la lecture se fait sur les **domaines**, pas sur les assignations.

**Condition posee pour les mettre dans le meme commit** : que `canary3` les
rejette **separement** dans son test negatif. Elle est remplie, et le bug
injecte est le meme des deux cotes -- **confondre `lo` et `hi`**, l'erreur
naturelle sur une contrainte a deux bornes, fausse exactement quand `lo < hi`.

    INTERDICTION zelee : 0 violation sur lo == hi, 20 sur lo < hi, 21 sur lo == 0
    FORCAGE zele       : 0 violation sur lo == hi, 19 sur lo < hi,  9 sur lo == 0

Chaque variante ne remplace **qu'un** sens, l'autre restant correct : une
violation est donc imputable au sens injecte. Et les deux donnent **zero**
violation sur `lo == hi`, ou la confusion est effectivement sans effet -- le
canari discrimine, il ne signale pas au hasard.

**Cas limites, construits a la main** : `lo == hi` (comptage exact),
`lo < hi` (intervalle lache), et `lo == 0` -- **le piege**, analogue de
`|R| < d` pour AllDiff : la contrainte autorise **zero** occurrence, donc
aucun raisonnement « une cellule doit valoir `val` » n'y est valide.

**Verification supplementaire, ajoutee sans qu'elle soit demandee** : chaque
sens doit etre **invoque au moins une fois**. Deux techniques de deduction ont
deja ete ecrites, verifiees correctes, puis retirees pour n'avoir jamais
tourne. Un propagateur inerte est le motif du projet, et il se constate a
l'ecriture ou jamais. Mesure : interdiction 10 declenchements, forcage 5.
Le forcage ne se declenche **jamais** sur `lo == 0` -- normal, il faudrait que
plus aucune cellule ne puisse valoir `val` -- mais il se declenche sur les deux
autres formes.

**Ce qui n'est deliberement pas fait** : aucune detection de contradiction par
comptage (`|sur| > hi`, `|poss| < lo`). Elle serait correcte, mais
`feasible()` la fait deja et reste l'oracle. Seul un domaine **vide** est
signale, comme pour AllDiff.

**A verifier au commit suivant** : `dsl_hash` passe de `e40600351a72` a
`06fe04a859f1` tandis que `engine_active_hash` reste `0caa9267db60`. C'est le
**premier test reel** de la section de regroupement de `summarize.py`, qui
n'avait jamais eu l'occasion de s'afficher.

## 2026-08-26 - croisements de propagateurs, et le bug d'interaction qui N'EXISTE PAS

Trois systemes construits a la main pour la paire AllDiff x Count, tous a
n=2 / d=3 pour que l'enumeration soit **exhaustive** -- toutes les solutions
croisees avec **tous** les sous-ensembles d'indices. Un echantillon aleatoire
raterait precisement la configuration rare qui declenche l'interaction.

    X1  AllDiff |R| < d  x  Count lo == 0   regions partageant une cellule
    X2  AllDiff |R| < d  x  Count lo == 1   regions partageant une cellule
    X3  meme paire que X2, regions DISJOINTES   -- TEMOIN

### Le candidat naturel est structurellement inerte, et c'est un resultat
Le bug d'interaction suggere etait le **cache perime** : un propagateur lit le
domaine d'une cellule et ne le relit pas apres qu'un autre l'ait reduite. Il ne
peut **pas** etre injecte ici, pour une raison de fond :

> les domaines ne font que **retrecir**, et les deux declencheurs de Count sont
> des egalites sur des quantites **monotones** (`|sur|` croit, `|poss|`
> decroit). Une lecture perimee donne donc toujours un `sur` plus PETIT et un
> `poss` plus GRAND que la realite -- c'est-a-dire un propagateur plus
> **faible**, jamais plus zele.

Un cache perime produirait ici une **deduction manquee**, pas une solution
fausse. La classe n'est pas vide, mais **ce candidat-la** en est exclu par
monotonie. Consigne parce qu'un resultat negatif vaut mieux qu'une case vide,
et parce que la meme monotonie protegera les huit propagateurs suivants.

### Le bug d'interaction reel a cette frontiere
L'hypothese implicite qu'un domaine est **plein ou singleton** -- vraie dans le
monde du forward-checking d'ou l'on vient, **fausse** des qu'un autre
propagateur a rogne **partiellement** une cellule partagee. C'est le piege
conceptuel propre a l'introduction des domaines, et il **exige** le
chevauchement.

    bug sur X2 (chevauche)  : 24 violations
    bug sur X3 (DISJOINT)   :  0 violation

Le temoin disjoint reste muet : le chevauchement est bien le mecanisme.

### Ce que X1 ne peut PAS tester, et il fallait le dire
Le croisement nomme -- `|R| < d` x `lo == 0` -- donne **0 violation meme avec
le bug**. Avec `lo == 0` le sens FORCAGE ne se declenche jamais, et c'est le
forcage qui porte l'unsoundness. X1 exerce donc la **surete**, pas
l'interaction. X2 a ete ajoute pour cela. **Une configuration limite n'est pas
automatiquement une configuration ou l'interaction est observable.**

## 2026-08-26 - SumRange : coherence aux bornes, et deux croisements de plus

Meme famille de bornes que `Count`, donc **le meme gabarit a deux sens**, et la
comparaison est instructive : la ou `Count` compte des cellules, `SumRange`
borne une somme, mais les deux se declenchent sur un **extremum atteignable**.

    PLAFOND  (borne hi) : impossible si, meme en donnant aux autres cellules
                          leur MINIMUM, la somme depasse hi.
    PLANCHER (borne lo) : impossible si, meme en donnant aux autres cellules
                          leur MAXIMUM, la somme n'atteint pas lo.

Les min/max se lisent sur les **domaines**, ce qui rend la regle plus forte que
`feasible()`, qui borne toute cellule inconnue par `d-1` sans regarder ce
qu'elle peut valoir.

**Ecarte deliberement** : toute recherche de sous-ensembles realisables
(« quelles combinaisons somment exactement a `lo` »). Correcte mais
exponentielle, et surtout elle **resoudrait localement** des configurations
dont la difficulte est ce que le projet mesure. Meme motif que le rejet de
Regin.

**Deux sens dans le meme commit** : condition remplie, `canary3` les rejette
separement. Bug injecte : intervertir min et max dans le calcul du reste,
l'erreur classique de la coherence aux bornes.

    PLAFOND zele  : 86 violations sur lo == hi, 191 sur lo < hi, 0 sur vacuous
    PLANCHER zele : 87 violations sur lo == hi, 188 sur lo < hi, 0 sur vacuous

**Zero sur le cas vacuous** (`[0, |R|*(d-1)]`, toujours satisfait) : la, aucun
retrait n'est jamais justifie et aucune confusion min/max ne change rien. Le
canari discrimine.

### Le croisement Count x SumRange a d'abord ECHOUE, et c'est le resultat
Premiere version : `Count(lo=1, hi=2)` sur une region de **2** cellules. Le bug
d'interaction ne mordait pas. Cause : avec `hi == |R|`, le sens INTERDICTION ne
peut **rien retirer a l'interieur de sa propre region** -- il ne se declenche
que lorsque toutes les cellules valent deja `val`. Count ne pouvait donc pas
fabriquer le domaine **partiellement rogne** dont le bug a besoin.

Corrige en `hi = 1`. **La lecon est la meme que pour X1** : une paire de
configurations limites n'est pas automatiquement une paire ou l'interaction est
**observable**. Il faut verifier que l'un des deux propagateurs peut
effectivement **ROGNER** une cellule partagee -- pas seulement la partager.

    AllDiff x SumRange       : chevauchant 48, temoin disjoint 0
    Count(lo=hi=1) x SumRange: chevauchant 24, temoin disjoint 0

### Cout des croisements, mesure
`canary3` complet : **0,20 s** avec trois paires. La croissance quadratique
annoncee est, a ce stade, sans effet pratique. A remesurer, pas a supposer.

## 2026-08-26 - QUESTION OUVERTE : l'invariant 14 tient-il pour Connected ?

**A trancher au moment de Connected (etape 10), pas avant. Mais a savoir AVANT
d'y arriver, pas pendant.**

L'invariant 14 dit que l'unsoundness par interaction ne peut venir que d'une
inference sur la **forme** d'un domaine plutot que sur son contenu, la
monotonie rendant toute lecture perimee inerte. Il a tenu pour les quatre
premiers propagateurs. **Il y a une raison serieuse de penser qu'il ne couvre
pas Connected.**

**Ce qui est conforme** : `Connected` raisonne sur l'accessibilite dans un
graphe dont les sommets passables sont ceux dont le domaine **contient** `val`.
C'est une inference sur l'**appartenance**, donc couverte par 14 -- et la
regle de retrait par inaccessibilite l'est aussi.

**Ce qui ne l'est peut-etre pas** : le **forcage par point d'articulation**
infere depuis la **structure du graphe induit**, laquelle depend de **quels
domaines ont ete rognes**. C'est une propriete de forme **collective**, pas
individuelle -- et l'invariant 14, tel qu'il est enonce, ne parle que de la
forme d'**un** domaine.

Autrement dit : 14 pourrait etre correct et **incomplet**. Un propagateur peut
ne faire que des lectures d'appartenance, cellule par cellule, et neanmoins
tirer une conclusion d'une propriete **globale** du graphe que ces
appartenances induisent. La monotonie protege chaque lecture ; elle ne dit rien
sur la monotonie de la propriete collective.

**Ce qu'il faudra etablir a l'etape 10** :
- la structure induite evolue-t-elle **monotonement** quand les domaines
  retrecissent ? (un sommet passable ne peut que le rester ou cesser de
  l'etre -- donc le graphe ne fait que **perdre** des sommets, ce qui est
  monotone ; mais l'ensemble des **points d'articulation** n'est PAS monotone
  sous suppression de sommets, et c'est la que le doute porte) ;
- si la reponse est non, l'invariant 14 doit etre **etendu** a la forme
  collective, et le test negatif de tous les croisements impliquant Connected
  doit etre construit sur cette classe-la, pas sur celle de la forme
  individuelle.

**Ne pas traiter maintenant.** Consigne pour que l'etape 10 commence par cette
question au lieu de la decouvrir.


## 2026-08-26 - NeqAdj : le piege de T1 sous un troisieme habit

Une seule regle : une cellule reduite a `{v}` interdit `v` a ses **voisines
immediates** dans l'ordre de la region. Une seule lecture de forme,
`len(dom) == 1`, la forme admise.

**LE PIEGE** : `NeqAdj` n'est **pas** un `AllDiff`. Sur une region de trois
cellules ou plus, les **extremites peuvent etre egales**. Un propagateur qui
retirerait `v` de toute la region serait faux des que `|region| >= 3`.

C'est **le meme piege que T1**, sous un troisieme habit : appliquer a toute une
region un raisonnement qui n'est valide que localement. Le test negatif le
verifie :

    NeqAdj traite comme un AllDiff :
      0 violation sur |R| = 2 (ou les deux coincident effectivement)
      58 sur |R| = 3
      14 sur |R| = 3, d = 2

Zero sur `|R| = 2`, ou la confusion est sans effet : le canari discrimine.

**Trois croisements ajoutes** (contre AllDiff, Count, SumRange), meme gabarit,
bug d'interaction de la classe de l'invariant 14 :

    AllDiff x NeqAdj  : chevauchant 42, temoin disjoint 0
    Count   x NeqAdj  : chevauchant 12, temoin disjoint 0
    SumRange x NeqAdj : chevauchant 18, temoin disjoint 0

## 2026-08-26 - Mono : le premier propagateur SUR PAR CONSTRUCTION

Deux sens, tous deux de la coherence aux bornes :

    AVANT   : `dom[b]` ne peut contenir de valeur < min(dom[a])
    ARRIERE : `dom[a]` ne peut contenir de valeur > max(dom[b])

**AUDIT DE FORME : ce propagateur n'en fait AUCUNE.** Il ne lit que
`min(dom[i])`, `max(dom[i])` et l'appartenance. Par l'invariant 14 il est donc
**sur par construction vis-a-vis des interactions**, et c'est verifiable **par
simple relecture**, avant tout test. C'est le premier du chantier dans ce cas,
et cela montre que le critere de relecture n'est pas qu'un garde-fou : il
**classe** les propagateurs.

Confirmation par l'autre bout : pour fabriquer une interaction unsound sur
Mono, il a fallu **introduire deliberement une lecture de forme** dans le bug
injecte. On ne pouvait pas faire autrement -- ce qui est exactement ce que
l'invariant 14 predit.

**`feasible()` ne verifie que les paires assignees** ; sur une grille complete
cela revient a la monotonie de toute la suite, et c'est contre les grilles
completes que la propagation doit etre sure. Une seule passe ne suffit pas des
`|R| >= 3` : la contrainte se propage de proche en proche, et c'est le point
fixe de `propager()` qui fait le travail.

**Deux sens dans le meme commit** : condition remplie.

    AVANT zele   : 76 / 75 / 10 violations  (|R|=2 / |R|=3 / |R|=4,d=2)
    ARRIERE zele : 50 / 41 /  7

### Les quatre croisements, et la troisieme occurrence de la meme lecon
Deux d'entre eux ont **echoue** avant correction. Le bug injecte porte sur le
sens ARRIERE, qui lit `dom[b]` -- la cellule la plus loin dans l'ordre de la
region. Avec `Mono([1, 2])` et l'autre contrainte sur `[0, 1]`, l'autre
propagateur rognait le `a` : le bug ne voyait **jamais** de domaine partiel.
Corrige en inversant l'ordre de la region (`Mono([2, 1])`).

**La lecon se precise, et c'est sa troisieme forme** : il ne suffit pas que
l'un des deux propagateurs puisse **rogner** une cellule partagee -- il faut
qu'il rogne **LA cellule que l'inference injectee LIT**.

    AllDiff  x Mono : chevauchant  6, temoin disjoint 0
    Count    x Mono : chevauchant 12, temoin disjoint 0
    SumRange x Mono : chevauchant  6, temoin disjoint 0
    NeqAdj   x Mono : chevauchant  6, temoin disjoint 0

### Cout de canary3, remesure
    3 paires  : 0,20 s
    6 paires  : 0,21 s
    10 paires : 0,27 s
La croissance est visible mais reste sans effet pratique. A remesurer apres
PairRatio, et surtout apres NoSquare et Connected dont les regions sont bien
plus grandes.

## 2026-08-26 - 14bis : generalisation candidate, NON TRANCHEE

Formulation a ecrire maintenant, a trancher a l'etape 10 :

> **14** couvre les inferences dont l'entree est **l'appartenance d'une valeur
> a un domaine**. Il ne couvre **pas** les inferences dont l'entree est une
> **propriete d'un objet construit a partir de plusieurs domaines et non
> monotone sous retrecissement**. Pour celles-la, la surete doit etre prouvee
> separement -- ou l'inference ecartee.

### Le critere operatoire qui en decoule
Formule ainsi, 14bis se teste en une question par propagateur :

> **l'objet sur lequel porte l'inference est-il FIXE par la contrainte, ou
> INDUIT par les domaines courants ?**

Un objet **fixe** -- une region, une fenetre geometrique, une liste de paires --
ne bouge pas quand les domaines retrecissent. Les lectures faites dessus sont
des appartenances cellule par cellule, et 14 s'applique tel quel.

Un objet **induit** -- le graphe des cases passables de `Connected` -- change
avec les domaines, et **une propriete de cet objet peut ne pas etre monotone**
meme si chaque domaine ne fait que retrecir. C'est precisement le cas des
points d'articulation : le graphe ne fait que **perdre** des sommets, mais
l'ensemble de ses points d'articulation peut **grossir**.

### Consequence agreable, a VERIFIER et non a supposer
Sur les six propagateurs ecrits (`AllDiff`, `Count`, `SumRange`, `NeqAdj`,
`Mono`, `PairDiff`), l'objet est toujours **fixe** : la region ou la liste de
paires, donnees a la construction. 14bis ne change donc rien pour eux.

**A verifier a l'ecriture, pas maintenant** : `NoTriple` et `NoSquare`
raisonnent sur des **fenetres**, donc sur des objets multi-cellules. Lecture
preliminaire, **non verifiee dans le code** : leurs fenetres sont
**geometriques et statiques** -- les triplets consecutifs d'une region, les
carres 2x2 d'une grille -- donc **fixes**, et 14 devrait suffire. Si l'un des
deux fait une inference sur une fenetre **induite** par les domaines, la
question Connected arrive a l'etape 8 ou 9 au lieu de 10, et il vaut mieux le
savoir la.


## 2026-08-26 - PairDiff : coherence d'arc, et un helper partage assume

Regle unique, la **coherence d'arc** : une valeur `v` survit dans `dom[a]` s'il
existe un **support** `w` dans `dom[b]` avec `|v - w| >= k`.

**AUDIT DE FORME : aucune.** Le support se teste par appartenance, valeur par
valeur. `PairDiff` est donc, comme `Mono`, **sur par construction**, et le bug
d'interaction des croisements a du -- la encore -- introduire deliberement une
lecture de forme.

**La regle s'applique aux deux bouts de chaque paire, mais ce ne sont PAS
« deux sens »** au sens de `Count` ou `SumRange` : c'est une seule regle
appliquee symetriquement. La condition de commit separe ne s'applique pas.

**Helper partage, et pourquoi c'est assume** : `_arc_consistance` sera reutilise
par `PairRatio` ; seule la relation differe. Il **ne tombe pas** sous
l'invariant 10, qui protege la separation entre `feasible()` et la propagation,
pas l'ecriture deux fois d'un meme parcours de paires. Le risque -- un bug du
helper touche les deux propagateurs a la fois -- est couvert par les
croisements, qui les testeront l'un contre l'autre.

### Test negatif : la valeur absolue oubliee
    dirige P (k=1)   : 270 violations
    dirige Q (k=d-1) :  90
    dirige R (k=0)   :  90
    dirige S (chaine): 180

**Le cas vacuous ne donne PAS zero ici, contrairement aux autres propagateurs,
et c'est normal** : le bug ne confond pas une borne, il **change la relation**.
Avec `k = 0` la relation correcte est universellement vraie tandis que
`v - w >= 0` ne l'est pas. Le signal de discrimination n'est donc pas au meme
endroit -- il faut le lire, pas l'attendre.

### Cinq croisements de plus : quinze paires
    AllDiff  x PairDiff : 42 / 0      NeqAdj x PairDiff : 42 / 0
    Count    x PairDiff : 12 / 0      Mono   x PairDiff : 12 / 0
    SumRange x PairDiff : 18 / 0      (chevauchant / temoin disjoint)

## 2026-08-26 - PairRatio : ce qui est exact pour le voisin y est FAUX

Meme coherence d'arc que `PairDiff`, meme helper, autre relation. Et c'est la
que le partage se paie -- de la bonne facon, parce qu'on l'a teste.

**La difference de fond** : la relation de `PairDiff` (`|v - w| >= k`) est
**monotone en `w`** -- le meilleur support est toujours `min(dom[b])` ou
`max(dom[b])` -- donc un test **aux bornes** y serait exact. Celle de
`PairRatio` (`|v - w| in {0, delta}`) ne l'est **pas** : le seul support d'une
valeur peut etre une valeur **interieure** du domaine.

Recopier le test aux bornes d'un propagateur a l'autre est donc **exact pour
l'un et faux pour l'autre**, alors que les deux se ressemblent au point de
partager leur helper. C'est precisement l'erreur que le partage invite, et
`canary3` l'injecte :

    support cherche aux bornes :
      0 violation sur delta = 1     (la ou les bornes suffisent effectivement)
     28 sur delta = d-1
     24 sur delta >= d
      0 sur la chaine

**Zero sur `delta = 1`** : avec `d = 3`, tout minimum supporte toute valeur, et
le test aux bornes coincide avec le test exact. Le canari discrimine donc bien
sur la **structure de la relation**, pas au hasard.

### Le croisement PairDiff x PairRatio
C'est celui qui couvre le risque assume au commit precedent -- un bug du helper
partage toucherait les deux propagateurs a la fois. Il mord : 30 violations sur
le chevauchant, 0 sur le temoin disjoint.

### Quatrieme forme de la meme lecon
`Mono x PairRatio` a **echoue** d'abord. La cellule partagee etait bien rognee,
mais **du mauvais cote** : `Mono([0, 1])` ne peut que **relever le plancher** de
`dom[1]`, qui vaut alors `{1, 2}` ; son minimum, 1, supporte toutes les valeurs
a `delta = 1`, donc l'inference injectee ne se trompait jamais. Il fallait
`Mono([1, 0])`, qui **abaisse le plafond** et produit `dom[1] = {0, 1}` -- dont
le minimum 0 ne supporte plus la valeur 2.

**Enonce complet, apres quatre echecs** : il faut que l'autre propagateur
puisse produire **le domaine partiel PARTICULIER que l'inference injectee lit
de travers**. Pas seulement rogner ; pas seulement rogner la bonne cellule ;
la rogner **du bon cote**.

### Cout, remesure
    3 paires : 0,20 s      15 paires : 0,32 s
    6 paires : 0,21 s      21 paires : 0,42 s
   10 paires : 0,27 s
Croissance reelle, toujours sans consequence. Rien n'est prevu, tout est
remesure.

## 2026-08-26 - LA MESURE QUE LE GEL REND POSSIBLE : le gain de propagation

Ce que ni la resistance a T0 ni la resistance a la propagation ne donnent
seule :

    gain_propagation = (resistance_T0 - resistance_prop) / resistance_T0

C'est **ce que le renforcement des propagateurs LOCAUX recupere**.

**C'est un test plus direct de l'hypothese que la resistance brute.** Un
systeme localement decomposable devrait voir sa resistance **largement
recuperee** par des propagateurs locaux plus forts. Un systeme non
decomposable, **non -- par definition**. L'hypothese predit donc :

    gain FAIBLE pour `connect`,  gain FORT pour `static`.

Et c'est exactement ce que le gel de `t0_legacy` rend possible : **deux
instruments dont l'un ne bouge jamais**, et c'est l'ecart entre eux qui devient
le signal. Sans le gel, les deux mesures deriveraient ensemble et l'ecart ne
voudrait rien dire.

### Ce que le commit de branchement devra contenir
- un **second champ** dans le record : les deux resistances journalisees en
  **brut** (`unknown` / `left` pour chacune), **jamais le ratio** -- meme regle
  qu'a la premiere metrique, pour la meme raison ;
- un **canari de non-redondance** : si les deux mesures **coincident toujours**,
  l'une des deux ne sert a rien et il faut le savoir. Un instrument qui suit
  exactement un autre n'ajoute pas d'information, il ajoute de la confiance
  injustifiee ;
- le **controle croise** deja ferme : un systeme resolu par propagation doit
  avoir la meme solution unique que celle comptee par `count_solutions`.

**Priorite au branchement : le COUT par systeme**, pas la qualite de deduction.
Voir l'en-tete de PERIMETRE-A.md.


## 2026-08-26 - Connected : le point d'articulation est ECARTE, pas reporte

`Connected` gardera **l'inaccessibilite** et la **detection de contradiction
actuelle**. Rien de plus. Le **forcage par point d'articulation est ecarte**.

**Deux motifs, et aucun n'est la difficulte** :
1. **Force du propagateur** : un `Connected` trop fort **dissoudrait localement**
   la difficulte que le projet mesure. La force de ce propagateur n'est pas un
   parametre a maximiser -- c'est deja ecrit, ceci en est l'application.
2. **14bis** : l'articulation est **la seule** inference du chantier qui porte
   sur un objet **induit** par les domaines et **non monotone** sous
   retrecissement. L'ecarter regle 14bis **sans avoir a le trancher**.

**CE N'EST PAS UN REPORT PAR DIFFICULTE.** Meme si l'articulation etait triviale
a ecrire, elle ne serait **pas adoptee sans mesure**. C'est une decision de
perimetre, pas un aveu de cout.

**Critere de reouverture, mesurable et unique** : si a n=5 le debit reste
insuffisant **avec l'inaccessibilite seule**, et seulement dans ce cas. Et il
faudra alors **prouver 14bis AVANT** d'ecrire la regle, pas apres.


## 2026-08-26 - NoSquare : dsl2.py reste intact, le propagateur construit ses fenetres

`NoSquare(n, val)` a pour region la **grille entiere** alors que la contrainte
porte sur `(n-1)^2` fenetres 2x2. **On ne corrige pas la contrainte.**

**Motif** : une region trop large rend `touch[i]` **sur-inclusif** -- donc c'est
une **inefficacite, pas une incorrection**. Et le **diff vide** sur `dsl2.py`
est la **preuve mecanique** que `feasible()` est conservee pendant tout A. Une
preuve mecanique vaut plus qu'une optimisation.

Le propagateur construit donc ses fenetres 2x2 lui-meme, a partir de `n`. Le
commit preparatoire de decomposition qui etait prevu **n'a plus lieu d'etre**.

## 2026-08-26 - NoTriple : 14bis verifie, et un huitieme cas du motif

### Le propagateur
Regle unique : dans une fenetre de trois cellules consecutives, si **deux**
sont reduites au meme singleton `{v}`, la troisieme ne peut pas valoir `v`.
Les trois positions sont symetriques -- une seule regle, trois choix de cible.

**LE PIEGE** : `NoTriple` n'est **pas** un `NeqAdj`. **Deux** valeurs
identiques consecutives sont licites. C'est le meme piege que `NeqAdj` traite
comme un `AllDiff`, d'un cran plus fin : la regle appliquee a la mauvaise
granularite.

    traite comme un NeqAdj : 80 / 109 / 32 violations
                             (|R|=3 / |R|=4 / d=2)

### 14BIS : VERIFIE, PAS SUPPOSE
Les fenetres sont les **triplets consecutifs de la region** -- un objet **FIXE
par la contrainte**. Il ne depend pas des domaines et **ne bouge pas** quand ils
retrecissent ; l'inference porte cellule par cellule sur un index fixe.
**14 suffit ; 14bis n'est pas engage.** La lecture preliminaire est confirmee
pour `NoTriple` ; reste `NoSquare`.

### HUITIEME CAS DU MOTIF, ET IL EST DANS LE CANARI LUI-MEME
Les sept croisements de `NoTriple` ont d'abord rendu **zero violation** sous un
bug reel. Ce n'etait pas un bug inerte : **l'echantillon ne couvrait rien.**

`NoTriple` exige une region de quatre cellules pour avoir deux fenetres, et le
temoin disjoint doit loger ailleurs -- il a donc fallu passer les croisements a
n=3, donc a un **echantillon** au lieu de l'enumeration exhaustive. Et
l'echantillon etait `sols[:30]` sur une enumeration **lexicographique** :
toutes les grilles retenues partagent les memes petites valeurs en tete de
grille. **Un coin de l'espace, pas l'espace.**

    sols[:30]                      : 0 violation
    tirage aleatoire, meme taille  : des centaines

**C'est le motif du projet a l'etage de l'echantillonnage du canari, et il a
ete introduit dans le commit meme qui ajoutait la couverture qu'il annulait.**
Ce qui l'a fait voir : refuser de conclure « bug inerte » sur sept echecs
simultanes -- sept croisements independants ne deviennent pas tous inertes en
meme temps.

**Correction** : `echantillon()`, tirage aleatoire a graine fixe, applique
**partout** ou un prefixe etait pris (`cas_surete`, `croisement_surete`, les
compteurs de declenchement). Invariant 15.

**Regle generale qui en sort** : quand une couverture est reduite, verifier que
la reduction est **independante de l'ordre dans lequel les cas ont ete
produits**. Une troncature suit toujours l'ordre du generateur, et l'ordre du
generateur est structure.

**Et : quand un croisement rend zero, distinguer « bug inerte » de « couverture
aveugle » AVANT de conclure.** Les deux impriment exactement la meme ligne.

### Le regime d'echantillonnage est IMPRIME
`croisement_surete` affiche desormais `exhaustif` ou `ECHANTILLON<=k` a chaque
ligne. Un croisement echantillonne ne doit pas etre lu comme exhaustif.

    AllDiff  x NoTriple :  48 / 0      Mono      x NoTriple : 290 / 0
    Count    x NoTriple :  60 / 0      PairDiff  x NoTriple :  48 / 0
    SumRange x NoTriple :  72 / 0      PairRatio x NoTriple : 513 / 0
    NeqAdj   x NoTriple :  48 / 0      (chevauchant / temoin disjoint)

### Cout, remesure
    21 paires : 0,42 s        28 paires : 3,39 s
Le saut vient des croisements a n=3, pas du nombre de paires : chacun fait
15 600 essais contre ~600 a n=2. **La croissance n'est pas quadratique en
paires, elle est dominee par la taille de grille.** A surveiller a `NoSquare`,
qui exigera au moins n=3 lui aussi.

## 2026-08-26 - correction d'attribution du cout de canary3

L'hypothese posee en ouvrant les croisements etait que le cout croitrait
**quadratiquement avec le nombre de paires**. La mesure dit autre chose :

    3 paires : 0,20 s     15 paires : 0,32 s
    6 paires : 0,21 s     21 paires : 0,42 s
   10 paires : 0,27 s     28 paires : 3,39 s

Le saut d'un facteur huit entre 21 et 28 paires ne vient **pas** des sept
paires ajoutees : il vient de ce qu'elles sont les premieres a **n=3**.
Chacune fait 15 600 essais la ou une paire a n=2 en fait ~600.

**Le terme dominant est `n`, pas le nombre de paires.** L'espace des grilles
croit exponentiellement en `n^2` tandis que les paires croissent en `k^2` ;
a `k = 45` et `n = 2`, les paires ne coutent rien. C'est donc le passage a
des contraintes exigeant de plus grandes regions -- `NoSquare`, `Connected` --
qu'il faut surveiller, pas l'arrivee du dixieme propagateur.

Consigne parce que la mauvaise attribution etait ecrite, et qu'une prevision
de cout fausse conduit a optimiser le mauvais terme.

## 2026-08-26 - NoSquare : 14bis verifie mecaniquement sur les NEUF propagateurs

### Le propagateur
Dans une fenetre 2x2, si **trois** cellules sont reduites au singleton `{val}`,
la quatrieme ne peut pas valoir `val`. Les fenetres sont construites **dans le
propagateur**, a partir de `cn.n` : `dsl2.py` n'est pas touche, conformement a
la decision prise. Son diff vide reste la preuve mecanique que `feasible()` est
conservee pendant tout A.

Test negatif, le bug de granularite une fois de plus : declencher a **deux**
singletons au lieu de trois, c'est-a-dire interdire une paire monochrome alors
que seule la fenetre **complete** est interdite.

### 14BIS : VERIFIE, ET MECANIQUEMENT
Plutot que d'argumenter que les fenetres sont geometriques, chaque propagateur
**declare** dans `objet_inference()` l'objet qu'il parcourt, et `canary3`
verifie que cet objet est **identique avant et apres des rognages arbitraires**
des domaines.

    AllDiff FIXE   Count FIXE   SumRange FIXE   NeqAdj FIXE   Mono FIXE
    PairDiff FIXE  PairRatio FIXE   NoTriple FIXE   NoSquare FIXE

**Les neuf objets sont fixes : 14 suffit, 14bis n'est pas engage.** La
presomption est remplacee par une verification qui tourne a chaque canari.

**Et le test est ecrit pour ECHOUER sur `Connected`** -- dont le graphe des
cases passables depend des domaines. C'est ainsi qu'on saura que 14bis est
engage, au lieu de le decouvrir apres coup. Un propagateur qui ne declare aucun
objet fait echouer le canari : **on ne peut pas ne pas repondre a la question**.

### Le temoin disjoint devient IMPOSSIBLE, et le controle s'ameliore
Les fenetres de `NoSquare` couvrent **toute la grille** : aucune contrainte ne
peut lui etre disjointe. Le temoin geometrique utilise pour les huit
propagateurs precedents ne peut pas etre construit -- **et `Connected` aura
exactement la meme propriete.**

Remplace par un controle **strictement plus fort** : le meme systeme, avec le
propagateur de l'autre contrainte **desactive**. Les deux mondes ont alors
**exactement le meme ensemble de solutions** ; seule change la capacite de
l'autre propagateur a rogner. C'est mieux que le controle geometrique, qui
faisait varier le systeme en meme temps que le chevauchement.

### CINQUIEME FORME DE LA MEME LECON, et elle se lit sans tatonner
Trois croisements ont echoue. Le bug lit `min(dom) == val` avec `val = 1` : il
lui faut donc un domaine partiel **egal a `{1, 2}`**, c'est-a-dire dont la
valeur 0 a ete retiree.

- `Count([0,1], val=1, ...)` ne retire **jamais que la valeur 1 elle-meme** : il
  produit `{0, 2}`, jamais `{1, 2}`. **Structurellement incapable.**
- `SumRange([0,1], lo=0, ...)` n'a que son **plafond** actif -- `lo = 0` rend le
  plancher inerte -- donc il ne retire que les **grandes** valeurs. Idem.
- `NoTriple x NoSquare` : la chaine a besoin de **quatre** cellules posees pour
  s'amorcer -- deux pour que NoTriple retire une valeur, deux de plus pour
  completer la fenetre 2x2. A `max_taille = 3` c'etait une **couverture
  aveugle**, pas un bug inerte (invariant 15).

Corriges en `Count(val=0)`, `SumRange(lo=3)` et `NS_TAILLE = 4`. **Les trois ont
ete constates en faisant echouer le croisement, pas devines.**

    AllDiff   x NoSquare :  15 / 0     Mono      x NoSquare :  96 / 0
    Count     x NoSquare :  15 / 0     PairDiff  x NoSquare :  15 / 0
    SumRange  x NoSquare : 531 / 0     PairRatio x NoSquare :  15 / 0
    NeqAdj    x NoSquare :  15 / 0     NoTriple  x NoSquare :   3 / 0
                        (avec l'autre propagateur / sans lui)

### Cout
    28 paires : 3,39 s      36 paires : 8,23 s
Conforme a l'attribution corrigee : la hausse vient des huit paires a **n=3**
et du passage a `max_taille = 4` (30 720 essais par execution contre 15 600),
pas du nombre de paires.

## 2026-08-26 - 14ter : la preuve tient, mais le critere propose n'est pas le bon

**Demande** : prouver ou refuter la surete du retrait par inaccessibilite sur
un objet induit, AVANT toute ligne de propagateur `Connected`.

### La conclusion demandee est VRAIE
Le retrait par inaccessibilite est **sur**. Preuve, avec `P` l'ensemble des
cellules passables (`val` dans `dom[i]`) et `F` celles dont le domaine est
reduit a `{val}` :

    Soit sigma une solution compatible avec les domaines courants, et
    S = {i : sigma[i] = val}. Par soundness des domaines, S est inclus dans P.
    `Connected` impose que S soit connexe. Si s appartient a F, alors s
    appartient a S, donc tout i de S est relie a s par un chemin DANS S, donc
    par un chemin dans P. Contraposee : si i n'est pas accessible depuis s
    dans P, alors sigma[i] != val. Le retrait est valide.

**Condition d'amorcage** : il faut `|F| >= 1`. Sans ancre, aucun retrait n'est
justifie -- la composante peut etre n'importe ou, ou vide.

### MAIS LA PREMISSE SUR L'ARTICULATION EST FAUSSE
La formulation proposee -- « une inference sur objet induit est sure si la
propriete inferee est monotone » -- est **suffisante mais pas necessaire**, et
surtout elle **ne discrimine pas** : le forcage par point d'articulation la
satisfait aussi.

**Il est sur.** Meme decor : tout chemin de `a` a `b` dans `S` est un chemin
dans `P` ; si `x` separe `a` et `b` dans `P`, ce chemin passe par `x`, donc
`sigma[x] = val`.

**Et il est monotone.** L'intuition « les points d'articulation ne sont pas
monotones sous suppression de sommets » est vraie **pour l'ensemble des points
d'articulation d'un graphe quelconque**, mais l'objet ici n'est pas celui-la :
c'est **l'ensemble des sommets par lesquels passe TOUT chemin `a`-`b`**.
Supprimer des sommets ne **cree** jamais de chemin, donc cet ensemble ne peut
que **croitre**. (Cas degenere : si `a` et `b` cessent d'etre relies, le
systeme est infaisable et c'est une contradiction, pas un forcage.)

**Verifie empiriquement** avant d'etre ecrit : 1675 tirages de graphes-grilles
4x4 avec suppressions aleatoires de sommets, comparaison des ensembles avant et
apres. **Zero contre-exemple** pour l'inaccessibilite comme pour l'articulation.

### LE BON CRITERE (invariant 14ter)
> Une inference est sure si elle n'utilise les domaines **que comme
> sur-approximation des valeurs possibles** -- si elle est valide dans la
> relaxation « chaque cellule peut prendre n'importe quelle valeur de son
> domaine ».

**14 en est le cas particulier** : lire la FORME d'un domaine, c'est affirmer
sur son contenu quelque chose de plus fort que `sigma[i] dans dom[i]`.

**Etre induit n'est pas etre dangereux.** Un objet induit **construit par
appartenance** herite de la sur-approximation. La monotonie sert a la
**confluence** -- unicite du point fixe, donc metrique bien definie
independamment de l'ordre de propagation -- **pas a la surete**. Les deux
regles de `Connected` etant monotones, la confluence est acquise aussi.

### CONSEQUENCE SUR L'EXCLUSION DE L'ARTICULATION
Elle avait **deux motifs**. Le second -- 14bis -- **s'evapore** : l'articulation
est sure et monotone. Le premier tient entier et **suffit** : un `Connected`
trop fort **dissoudrait localement** la difficulte que le projet mesure, et la
force de ce propagateur n'est pas un parametre a maximiser.

**L'exclusion est donc maintenue, mais elle repose desormais sur un seul
motif, et c'est un motif de conception d'experience, pas de correction.** Le
critere de reouverture reste celui fixe : insuffisance de debit a n=5 avec
l'inaccessibilite seule. **Il n'y aura plus de preuve a produire avant** -- elle
est faite.

### CE QUE « INDUIT » COUTE REELLEMENT
Ni la surete ni la confluence. Il coute **l'incrementalite** : l'objet doit
etre reconstruit a chaque changement de domaine, la ou une region fixe se
parcourt sans recalcul. **Pour un chantier de debit, c'est le seul cout qui
compte**, et c'est celui-la qu'il faudra mesurer.

## 2026-08-26 - OU LE BUDGET PART REELLEMENT A n=5, ET CE QUE CA IMPOSE A L'ETAPE 10

### Le chiffre
Ventilation a n=5, `connect,relational`, 30 systemes, borne 20 s, moteur
actuel **seul** :

    systemes terminees : 25  ->    3,56 s
    systemes coupes    :  5  ->  100,00 s, TOUS dans solve_graded

    BUDGET REEL          solve_graded     100,202 s   96,8 %
                         random_solution    2,410 s    2,3 %
                         minimal_clues      0,704 s    0,7 %
                         count_solutions    0,209 s    0,2 %

**`solve_graded` porte 97 % du budget. A vise donc le bon endroit**, et c'est
la seule phase que la propagation accelere.

### La lecture inverse, et pourquoi elle etait fausse
Sur les systemes **terminees seuls**, `random_solution` pese 67,7 % et
`solve_graded` 5,7 %. C'est la population qui ne coute rien -- mediane 125 ms
par systeme. **Le banc a d'abord imprime cette lecture-la en conclusion**, donc
l'inverse de la verite. Recurrence du neuvieme cas, dans l'outil ecrit pour
l'eviter. Corrige : le budget est calcule interrompus inclus, et c'est ce
chiffre-la qui est mis en avant.

### CE QUE LES DEUX MESURES POINTENT, ET C'EST LE MEME ENDROIT
- Les **5 systemes** qui brulent le budget sont **tous des `CONNECTED`**.
- Les **3 systemes** que le prototype « debloque » (base coupee a 20 s,
  prototype instantane) sont **tous des `CONNECTED`** aussi -- debloques parce
  qu'il **ne voit pas** la contrainte.
- Sur la population **COUVERTE** (toutes contraintes propagees), le prototype
  est **plus lent** : x0,43, et il ne perd aucune deduction.

**`Connected` n'est donc pas le dernier propagateur du chantier : c'est le seul
qui puisse valider A.** Les neuf autres ne produisent aucun gain de debit
mesurable -- ils sont la **condition d'existence** d'un propagateur qui, lui,
agit sur la population qui decide.

### Correction d'une formulation trop favorable
Il avait ete ferme que « tout gain mesure sur `connect` est un MINORANT ».
C'est trop favorable. Un minorant supposerait un prototype **equivalent** plus
rapide ; celui-ci est **strictement plus faible** -- il ne voit pas `Connected`
du tout. Une part du temps economise est du **travail non fait** : le rapport
n'est pas conservateur, il est **CONFONDU**.

Preuve dans les chiffres : 27 instances sur 63 ou la base resout et pas le
prototype, et 2 `max_level` **plus hauts** -- le prototype, plus faible au
niveau bas, doit monter au niveau 2 la ou T0 suffisait.

Le banc separe desormais les deux populations a chaque execution.

### Ce qui n'est PAS etabli
Que la propagation `Connected` fasse passer ces cinq systemes sous 20 s. Rien
ne le garantit : `apply_T2` sature `T0+T1` sur chaque hypothese, et le gain
depend de la **force** du propagateur `Connected` -- dont la regle la plus
forte a ete deliberement ecartee. **C'est la premiere mesure a refaire apres
l'etape 10, et c'est elle qui decide du sort de A.**

## 2026-08-26 - l'argument de surete avance contre l'articulation etait FAUX

Rectification d'une entree anterieure de ce fichier, et de la decision qu'elle
motivait a moitie.

L'exclusion du forcage par point d'articulation avait ete posee sur **deux**
motifs. Le second etait : « l'articulation infere depuis une propriete non
monotone d'un objet induit ». **Cet argument est faux.**

Il reposait sur le choix du mauvais objet. L'ensemble des **points
d'articulation d'un graphe quelconque** n'est effectivement pas monotone sous
suppression de sommets. Mais l'objet pertinent ici est l'ensemble des **sommets
separateurs de `a` et `b`** -- ceux par lesquels passe TOUT chemin de `a` a `b`.
Supprimer des sommets ne **cree** jamais de chemin : cet ensemble ne peut donc
que **croitre**. Verifie sur 1675 tirages, zero contre-exemple
(`preuves/monotonie_connected.py`).

Et par 14ter, la monotonie n'etait de toute facon pas le critere : l'inference
est sure parce qu'elle est valide dans la **relaxation**, ce que l'articulation
satisfait aussi.

**L'ARTICULATION RESTE ECARTEE, POUR UN SEUL MOTIF, ET IL SUFFIT** : un
`Connected` trop fort **dissoudrait localement** la difficulte que le projet
mesure. C'est un motif de **conception d'experience**, pas de correction. Il
n'y a **plus aucun argument de surete** dans cette decision, et si le critere
de reouverture se declenche, **rien ne reste a prouver avant** de l'ecrire.

## 2026-08-26 - Connected, dixieme propagateur, et le VERDICT DE A

### Le propagateur
Deux regles, et rien d'autre : **retrait par inaccessibilite** depuis une
cellule certainement `val`, et **detection de contradiction** quand deux
cellules certainement `val` ne sont plus reliables dans `P`. La preuve est
ecrite dans `engine/propagate.py`, **avant le code**, dans les termes de
14ter -- validite dans la relaxation.

**LE PIEGE EST LA CONDITION D'AMORCAGE** : il faut `|F| >= 1`. Sans ancre
CERTAINE, la composante peut etre n'importe ou, ou vide -- `feasible()`
acceptant zero ou une cellule `val`. Le test negatif prend pour ancre une
cellule seulement POSSIBLE : 2 / 5 / 8 violations sur les trois cas.

**Objet INDUIT**, declare comme tel, avec les deux regles ecrites et **elles
seules** : `statut_objet` rend `INDUIT-PROUVE`.

### Les neuf croisements, et deux formes nouvelles de la meme lecon
- **Sixieme forme** : `Mono x Connected` ne mordait pas parce que
  `certaines[0]` retient le PLUS PETIT INDICE, et la fausse ancre etait
  toujours precedee par la VRAIE ancre qui l'avait causee. Il ne suffit donc
  pas que le domaine partiel voulu soit produit, du bon cote, sur la bonne
  cellule : il faut encore que cette cellule soit **choisie** par
  l'implementation. Corrige par `Mono([4, 0])`.
- **UNE PAIRE PEUT N'ETRE DECLENCHABLE QUE DANS UN SEUL SENS** :
  `NoSquare x Connected` -- les deux propagateurs ne font que RETIRER `val`,
  donc aucun ne produit le domaine partiel CONTENANT `val` dont le bug d'ancre
  a besoin. Le sens inverse marche : `Connected` retire `val=1` et laisse
  `{0, 2}`, dont le minimum vaut 0, le `val` de `NoSquare`. Le bug a donc
  change de cote.

`canary3` : 45 paires, **15,4 s**.

### LE VERDICT
Prototype **equivalent en deduction** (invariant 21) :

    125 instances comparables : x0,99
    decile le plus couteux    : x0,90
    systemes rendus mesurables: 1 sur 132
    aucune ne finit           : 6
    solutions fausses         : 0

**A ne remplit pas son critere de succes.** Pas de gain de debit.

Le x3,99 mesure auparavant venait d'un prototype qui **remplacait** la
saturation : 18 deductions perdues. En filtre : 0 perdue, et le gain
disparait. **Presque tout le gain apparent etait du travail non fait.**

### Ce que A a produit et qui n'est pas nul
Le prototype **deduit plus a cout egal** : 11 instances resolues par lui seul,
63 `max_level` abaisses, 0 deduction perdue. C'est une amelioration de la
QUALITE de deduction, pas du debit -- donc pas ce que A visait.

### Residu non explique
**1 divergence de `max_level` PLUS HAUTE** sur 132, population entierement
couverte. Le montage en filtre garantit « egal ou plus fort » sur les
retraits, mais la propagation initiale assigne des cellules et change donc
l'ORDRE dans lequel T2 examine les cases : le niveau atteint peut differer
sans qu'aucune deduction soit perdue (0 perdue, 0 solution fausse). A verifier
si le chiffre grossit.

### Le critere de reouverture de l'articulation est ATTEINT
Fixe a l'avance : « si a n=5 le debit reste insuffisant avec l'inaccessibilite
seule ». La mesure le declenche. La preuve de surete est faite : **rien ne
reste a etablir avant de l'ecrire.** La decision n'est pas prise ici.

## 2026-08-26 - VERDICT : A A ECHOUE SUR CE QU'IL VISAIT

**La propagation sur domaines ne produit aucun gain de debit. n=5 ne passe pas
sous la borne de 20 s. Le chantier a echoue sur son critere de succes.**

Enonce sans attenuation, parce que le volume de travail accompli -- dix
propagateurs, 45 croisements, onze invariants -- rend la nuance trop facile.

    125 instances comparables : x0,99      decile le plus couteux : x0,90
    systemes rendus mesurables: 1 sur 132  aucune ne finit        : 6

### Le dixieme cas du motif, et pourquoi il est le plus important
La mesure fausse **allait dans le sens espere**, sur le **critere de succes du
chantier**, au moment ou on l'attendait. Les neuf autres contredisaient une
attente ou etaient neutres.

    UN RESULTAT FAVORABLE MERITE LE MEME CONTROLE QU'UN RESULTAT
    DEFAVORABLE, ET IL LE RECOIT MOINS SOUVENT.

C'est le regime ou un instrument n'est jamais reverifie. Le x3,99 aurait ete
rapporte comme le resultat du chantier si l'utilisateur n'avait pas impose
d'afficher le SENS des divergences et de separer la population couverte.

### L'articulation ne sera pas ouverte, et le critere etait mal concu
Atteint formellement, il ne sera pas suivi. Il devait **constater** un debit
insuffisant ; il ne devait pas **ouvrir une piste** que les mesures rendent
invraisemblable. Aucun facteur n'est recuperable nulle part -- ni sur la
population couverte, ni sur le decile le plus couteux, ni sur les instances qui
atteignent la borne.

**Un critere de reouverture doit dire a quelle condition une piste redevient
PLAUSIBLE, pas seulement a quelle condition on est mecontent du resultat. Un
seuil d'insatisfaction n'est pas une hypothese.**

### Ce qui est garde, mesure, et NON branche
A cout egal, la propagation deduit davantage : 11 instances resolues par elle
seule, 63 `max_level` abaisses, 0 perdue, 0 solution fausse. Second instrument
du `gain_propagation`, axe QUALITE.

**Ne pas le brancher** : il deplacerait la frontiere mesuree, ce contre quoi le
gel de `t0_legacy` a ete construit. Disponible si la question de qualite
redevient centrale.

### Residu ouvert, non explique et laisse tel quel
**1 divergence de `max_level` plus haute** sur 132, population entierement
couverte. 0 deduction perdue, 0 solution fausse : ce n'est pas une
unsoundness. **Non explique, et volontairement non explique ce soir.**

### Ce qui suit n'est pas technique
Si A ne debloque pas n=5, la voie vers la profondeur mesurable n'existe plus
dans sa forme actuelle. **C'est une question de recherche, pas d'ingenierie.**

## 2026-08-26 - gain_propagation : PREDICTION ECRITE AVANT LA MESURE

**Ce paragraphe est ecrit et pousse AVANT que la mesure ne tourne. C'est la
moitie du garde : une prediction posee apres coup n'en est pas une.**

### Pourquoi cette mesure existe, et pourquoi elle n'a pas besoin de n=5
L'hypothese centrale n'a jamais exige n=5 -- c'est la **profondeur** qui
l'exigeait. La **decomposabilite locale** se teste autrement :

> des propagateurs locaux plus forts **recuperent** la resistance d'un systeme
> localement decomposable, et **pas** celle d'un systeme qui ne l'est pas.
> Par definition.

A a livre cet instrument **sans le viser** : le chantier a echoue sur le debit
et produit une mesure de qualite.

### LA PREDICTION
    gain_propagation = (resistance_T0 - resistance_prop) / resistance_T0

    gain FORT   sur `static-ref`
    gain FAIBLE sur `connect`

La faiblesse relative de `Connected` -- deux regles seulement, l'articulation
ecartee -- n'est pas un defaut ici : **c'est le signal attendu**. Un systeme
non decomposable ne doit pas voir sa resistance recuperee par des propagateurs
locaux, si forts soient-ils.

### LES TROIS GARDES, tires de la journee
1. **Canari de non-redondance D'ABORD.** Si les deux resistances coincident
   partout, le gain ne mesure rien et **on s'arrete la**. Et s'il sature -- 0 %
   ou 100 % des deux cotes -- c'est le troisieme cas du motif qui recommence.
2. **La prediction ci-dessus est directionnelle et ecrite.** Si le resultat la
   confirme, il merite **EXACTEMENT le controle qu'aurait recu son contraire**.
   C'est le regime du dixieme cas : un resultat favorable est moins reverifie.
3. **Aucun branchement en production.** La mesure tourne a part ; `t0_legacy`
   reste la reference de la serie, `engine_active_hash` ne bouge pas.

### Ce qui se decidera apres, et pas avant
Si le gain **discrimine**, une file lente a n=5 devient justifiee -- borne
300 s, quelques centaines de systemes, en parallele de la production n=4,
objectif **vingt candidats par groupe et non un debit**.

**S'il ne discrimine pas, l'hypothese a un probleme plus profond que le debit**,
et la file lente mesurerait cher une question mal posee. Elle n'est pas lancee.

## 2026-08-27 - RESULTAT : la fracture est portee par Connected, et la mesure le montre

### La prediction, ecrite et poussee avant la mesure, est confirmee
    static-ref   n= 9258  inconnues=434704  T0=113438  prop= 50197   gain 0,557 / 0,699
    connect      n=12015  inconnues=639201  T0=380544  prop=281769   gain 0,260 / 0,237
    ECART : 0,699 vs 0,237   p = 0,0005

Recalcule a la main depuis les bruts, sans passer par l'agrege :
`63241/113438 = 0,5575` et `98775/380544 = 0,2596`.

### LE CONTROLE DECISIF : a l'interieur du tag `connect`
    connect SANS Connected   inst=28539  T0=47760   prop=0       gain 1,000
    connect AVEC Connected   inst=60947  T0=299562  prop=250801  gain 0,158
    p = 0,0005

**Meme tag, meme generateur, memes familles.** La composition du tag ne peut pas
expliquer cet ecart. Les systemes sans `Connected` sont **relationnels purs** --
verifie, et non suppose : `PAIRDIFF`/`PAIRSTEP` seuls, aucun `NoSquare`, aucun
`Count`.

**La propagation locale recupere INTEGRALEMENT la resistance des systemes
relationnels purs, et 16 % de celle des systemes a connectivite.** C'est
l'enonce de l'hypothese centrale, mesure.

### LE PLAFOND, ET IL EST VERIFIE
`gain = 1,000` exactement sur 28539 instances est un **indicateur sature** --
troisieme cas du motif. Verifie que ce n'est pas un bug : sur 200 instances,
**200 grilles pleines, 0 fausse**. Le plafond est reel.

**Consequence sur la lecture** : la comparaison `static 0,669` vs
`connect-sans-Connected 1,000` est une comparaison **AU PLAFOND** et ne peut pas
etayer un « ils se ressemblent ». J'avais annonce cette lecture avant la
mesure ; elle est **invalide dans sa forme**, meme si sa direction est
favorable. Le contraste qui tient est celui **a l'interieur du tag**, ou le
groupe avec `Connected` (0,158, resistance 0,526) est loin de tout plafond
comme de tout plancher.

### CONFONDANT 1 : la densite d'indices n'explique pas l'ecart
    static-ref            bas 0,641   median 0,714   haut 0,831
    connect sans Connected bas 1,000   median 1,000   haut  (plus rien a recuperer)
    connect avec Connected bas 0,196   median 0,062   haut  0,268
**Dans chaque strate**, le groupe a `Connected` reste tres en dessous des deux
autres. L'ecart survit a la stratification.

**Non explique** : la non-monotonie du groupe a `Connected` -- 0,196 / 0,062 /
0,268. Le tercile median tombe a 6 %. Consigne comme residu, pas explique.

### LA RESERVE QUI COMPTE, ET ELLE N'A PAS ETE DEMANDEE
**Ce resultat est partiellement circulaire, et il faut le dire.**

Le propagateur `Connected` est **deliberement faible** : l'articulation a ete
ecartee, et le motif de cette exclusion etait qu'un `Connected` trop fort
**dissoudrait localement la difficulte que le projet mesure**.

    On a donc ecarte la regle forte PARCE QU'ON S'ATTENDAIT A CE QU'ELLE
    dissolve la difficulte, et on mesure ensuite que la difficulte n'est pas
    dissoute par les regles faibles.

Le controle intra-tag ecarte la composition comme confondant. Il n'ecarte
**pas** la force du propagateur. L'enonce que la mesure autorise est donc :

> `Connected` resiste aux propagateurs locaux **que nous avons choisi
> d'ecrire**, et ce choix a ete informe par l'attente qu'il resiste.

**Le controle qui leverait la circularite existe et il est a portee** : le
forcage par point d'articulation est **prouve sur (relaxation + monotonie)**,
il ne reste rien a etablir avant de l'ecrire. Mesurer le gain AVEC lui
repondrait a la question : si `Connected` reste non recuperable meme avec la
regle la plus forte, la circularite tombe. S'il devient recuperable, alors ce
qu'on mesurait etait la faiblesse du propagateur.

**Ce n'est pas une decision d'ingenierie et elle n'est pas prise ici.**

## 2026-08-27 - L'ARTICULATION EST OUVERTE, et c'est une decision de RECHERCHE

**Renversement assume d'une decision prise deux fois (26/08, matin et soir).**
Elle avait ete fermee, puis re-fermee avec le motif que son critere de
reouverture etait mal concu. Ce qui a change n'est pas le critere : **c'est la
question**.

### Le motif qui l'ecartait s'est INVERSE avec le changement de question

    QUESTION D'HIER  : quelle est la resistance a T0 ?
                       -> un `Connected` fort DISSOUT ce qu'on mesure.
                          L'ecarter PROTEGE l'instrument.

    QUESTION D'AUJOURD'HUI : cette resistance est-elle recuperable par
                       propagation LOCALE ?
                       -> la regle la plus forte n'est plus une menace,
                          elle est LE CONTROLE.

**Un instrument se protege de ce qui le fausse, pas de ce qui le teste.**
La meme regle etait un confondant sous la premiere question et devient le
controle decisif sous la seconde. Le critere de reouverture de PERIMETRE-A.md
-- « si a n=5 le debit reste insuffisant » -- n'est PAS ce qui declenche :
il portait sur le debit, et le debit n'est plus la question.

### Ce que la mesure d'hier autorisait, et pourquoi ca ne suffit pas
L'enonce etroit, qui reste ecrit tel quel :

> `Connected` resiste aux propagateurs locaux **que nous avons choisi
> d'ecrire**, et ce choix a ete informe par l'attente qu'il resiste.

Le controle intra-tag ecarte la **composition** comme confondant. Il n'ecarte
pas la **force du propagateur**. Tant que la regle la plus forte disponible
n'est pas mesuree, le resultat est partiellement circulaire.

### LES DEUX ISSUES SONT ECRITES AVANT LA MESURE, ET LES DEUX SONT DES RESULTATS

- **`Connected` reste non recuperable avec l'articulation** : la circularite
  tombe. La resistance est une propriete de LA CONTRAINTE, pas de notre
  implementation. C'est **le premier resultat de fond du projet**, et il est
  etabli contre le controle le plus fort disponible.
- **`Connected` devient recuperable** : ce qu'on mesurait etait la faiblesse de
  notre propagateur. L'hypothese centrale perd son meilleur soutien, et **il
  faudra le dire aussi nettement que l'echec de A**.

Aucune des deux n'est l'issue esperee. C'est la condition pour que la mesure
ait un sens.

### CONDITIONS, identiques a tout le chantier
- **La preuve de surete est faite (relaxation + monotonie), et ne dispense PAS
  du test.** `canary3` etendu, cas limites construits A LA MAIN, test negatif
  vu mordre, croisements contre les dix propagateurs existants. La journee du
  26 a montre dix fois qu'une conviction n'est pas une verification.
- **Aucun branchement.** La mesure tourne a part, `t0_legacy` reste la
  reference de la serie, `engine_active_hash` ne doit pas bouger. La regle est
  derriere un drapeau **par defaut a False** : le propagateur par defaut reste
  BYTE POUR BYTE celui qui a produit la mesure d'hier, ce qui rend les deux
  bras comparables sans argument.
- **`gain_propagation` relance a l'identique**, avec l'articulation en plus, et
  **les MEMES gardes** -- y compris le tirage aleatoire (invariant 15) dont
  l'absence a ete payee hier dans le dispositif meme charge de l'appliquer.

### Non poursuivi
Le residu de **non-monotonie du gain selon `clue_frac`** (0,196 / 0,062 /
0,268) reste **ouvert et non poursuivi**.

### La file lente a n=5 est RECONDITIONNEE
Elle ne depend plus du gain seul, mais du resultat de ce controle. Si la
circularite tombe, elle se lance. Sinon, **ce qu'elle mesurerait serait notre
propre choix de propagateur, et elle n'a pas d'objet**.

## 2026-08-27 - VERDICT DU CONTROLE DE CIRCULARITE : la circularite tombe

Journaux bruts : commit `1c67fade`, fichiers `bench/ctrl_canary3.log`,
`bench/ctrl_localisation.log`, `bench/ctrl_gain.log`, `bench/ctrl_strates.log`.
Regle mesuree : commit `958fa8c8`. `engine_active_hash` = `0caa9267db60`,
inchange : la mesure a tourne A PART, `t0_legacy` reste la reference de la
serie, rien n'a ete branche en production.

### L'ENONCE ETABLI, ET SA BORNE

> La resistance de `Connected` a la recuperation par propagation locale
> survit a la regle locale la plus forte CALCULABLE -- le forcage par sommet
> separateur, dit articulation -- qui n'en recupere que **r = 0,034**, soit
> **un sixieme de ce que les neuf propagateurs ordinaires recuperent
> ensemble**.

**LA BORNE EST COMPUTATIONNELLE, PAS LOGIQUE, ET LA DISTINCTION EST LE
RESULTAT AUTANT QUE LE CHIFFRE.**

    CE QUI EST ETABLI    : aucune regle locale CALCULABLE ne recupere cette
                           resistance.
    CE QUI N'EST PAS     : aucune regle locale ne la recupere.

La regle suivante en puissance est le filtrage type Steiner, ecarte a
l'ouverture de A **pour complexite** et non pour surete. Elle n'a donc pas ete
mesuree et ne peut pas l'etre. Tout enonce de la forme « `Connected` n'est pas
localement decomposable », sans le qualificatif *calculable*, SURESTIME ce
qui a ete mesure.

### CE QUE LE RESULTAT N'ETABLIT PAS : L'HYPOTHESE CENTRALE A DEUX MOITIES

L'hypothese centrale porte sur la **PROFONDEUR** : la fracture entre systemes
plats et systemes profonds tiendrait a la decomposabilite locale. Ce qui vient
d'etre mesure est la **NON-LOCALITE**. Ce n'est pas l'hypothese, c'est **sa
moitie testable**.

    NON-LOCALITE  : mesuree, etablie contre le controle le plus fort
                    disponible. C'est ce verdict.
    PROFONDEUR    : HORS D'ATTEINTE A n=4, ou T0 sature. A visait a la rendre
                    mesurable a n=5 et A A ECHOUE (verdict du 26/08).

**UN LECTEUR FUTUR NE DOIT PAS LIRE CE VERDICT COMME « L'HYPOTHESE EST
CONFIRMEE ». ELLE NE L'EST PAS.** Sa moitie non-locale l'est ; sa moitie
profondeur n'a jamais ete mesuree et aucune voie vers elle n'est ouverte.

### LES CHIFFRES

    connect_avec_CONNECTED   T0 = 411 839   prop = 345 609   ART = 333 786
    r = (345 609 - 333 786) / 345 609 = 11 823 / 345 609 = 0,034

    ECART ENTRE TAGS   static-ref 0,700  vs  connect 0,262   p = 0,0005
    CONTROLE INTRA-TAG sans CONNECTED 1,000 vs avec 0,183    p = 0,0005

Contre-verification sur la moyenne par systeme : 0,155 -> 0,183, soit
0,028 / 0,845 = **0,033**. Meme bande, ecart de 0,001.

### LA CHAINE DE CONTROLE, ET C'EST ELLE QUI REND LE CHIFFRE CROYABLE

**Sans cette chaine, `r = 0,034` est un nombre. Avec elle, c'est un
resultat.**

1. **Seuil PRE-INSCRIT avant la mesure**, et derive de valeurs DEJA PUBLIEES
   (26/08) : bande basse `r < 0,194` = parite avec les neuf autres
   propagateurs ; bande haute `r >= 0,471` = alignement sur le gain total de
   `static-ref`. **Aucune constante ronde, donc aucun degre de liberte a
   regler apres coup.**
2. **La borne de parite est STABLE** : recalculee sur la population
   d'aujourd'hui, `66 230 / 345 609 = 0,192` contre `0,194` hier -- **0,002
   d'ecart alors que la population a quasi double**. Le seuil n'etait pas
   porte par le tirage du 26/08.
3. **Quatre controles BLOQUANTS passes**, lus AVANT `r` et dans cet ordre :
   zero solution fausse (`canary3` complet, sortie 0) ; localisation du
   forcage (277 cellules, 100 % sur le sous-groupe ou `r` se lit, 145 appels
   y forcant -- le risque reel etait un forcage NUL, il est ecarte) ; aucune
   inversion `T0 >= prop >= ART` ; sens des divergences toutes conformes.
4. **`p = 0,0005` sur les DEUX comparaisons** -- entre tags et a l'interieur
   du tag `connect`. La seconde tient la composition du tag hors de cause.
5. **Confondant `clue_frac` ecarte** : dans chacune des trois strates, le
   groupe a `Connected` reste tres en dessous des deux autres.

Controle lateral qui vaut d'etre note : sur `static-ref` et
`connect_sans_CONNECTED`, `ART` vaut `prop` **au chiffre pres** (72 993 =
72 993 ; 0 = 0). L'articulation est exactement inerte la ou aucun `Connected`
n'existe -- la seule valeur admissible, et elle n'a pas ete supposee.

### LE RENVERSEMENT DE DECISION QUI A RENDU CE VERDICT POSSIBLE
L'articulation avait ete fermee deux fois. Ce qui a change n'est pas son
critere de reouverture -- il portait sur le DEBIT -- mais **la question** :
sous « quelle est la resistance a T0 ? » une regle forte DISSOUT ce qu'on
mesure et l'ecarter protege l'instrument ; sous « cette resistance est-elle
recuperable localement ? » elle EST le controle. **Un instrument se protege de
ce qui le fausse, pas de ce qui le teste.**

### RESTENT OUVERTS, ET RIEN N'EST ENGAGE
- **File lente a n=5** : debloquee par ce verdict, mais son objet a change --
  elle devait rendre le controle menable, il l'etait a n=4. Non lancee.
- **Non-monotonie du gain selon `clue_frac`** (0,247 / 0,079 / 0,240) : a
  survecu a un changement de propagateur ET a un doublement de population.
  L'hypothese « bruit » est plus faible qu'hier. Non poursuivie.
- **1 divergence `max_level` plus haute sur 132** : inchangee, non expliquee,
  sans consequence de surete.
