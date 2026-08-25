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
