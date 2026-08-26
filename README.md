# rulesearch

Recherche automatisee dans l'espace des SYSTEMES DE REGLES de puzzles.
L'oracle est un solveur : unicite, resolubilite par deduction pure,
niveau de technique necessaire, densite d'indices.

## Environnement
Python 3.11+, stdlib seule. Aucune dependance.
PyPy3 fortement recommande pour les runs longs.

## Lancer
    python3 run.py --n 4 --d 4 --tag baseline
    python3 run.py --n 4 --d 2 --tag connect --families connect,relational

Les canaris tournent automatiquement au demarrage ; le run REFUSE de
partir s'ils echouent. `--skip-canary` existe pour le debug, jamais pour
un run reel.

## Structure
    engine/     rulesearch.py  regions statiques, contraintes de base, solveur
                dsl2.py        cages, relationnel, connectivite
                deduction.py   hierarchie T0/T1/T2
    canary/     canary.py   sensibilite (sudoku reconnu / systeme vide rejete)
                canary2.py  separation (la hierarchie distingue des difficultes)
    runs/       <date>-<dsl_hash>-<tag>/ config.json + results.jsonl
    found/      un json par systeme retenu

## dsl_hash
sha256 des fichiers de engine/. Deux runs de dsl_hash differents ne sont
PAS comparables. Sans ce champ, un journal de plusieurs semaines devient
un tas de lignes dont on ne sait plus lesquelles se comparent.

## Verdicts
    MORT           aucune grille ne satisfait le systeme
    SUR-CONTRAINT  trop peu de grilles valides : toujours le meme puzzle
    LIBRE          contraintes trop faibles : il faut donner la grille
    DEVINETTE      unicite oui, deduction pure non
    PLAT           deductible mais la technique la plus faible suffit
    CANDIDAT       bien pose, deductible, peu d'indices, niveau >= T1
    TROP-CHER      budget de temps par systeme depasse (--max-seconds,
                   20 s par defaut). A distinguer de TIMEOUT, qui est un
                   budget de NOEUDS epuise dans count_solutions. TROP-CHER
                   est une information de recherche : un systeme trop cher
                   a evaluer a n=4 est un fait sur le systeme.

## Resistance a T0 -- metrique principale
    t0_unknown   cases inconnues du puzzle initial, cumulees sur les instances
    t0_left      cases restantes apres saturation de T0 SEULE, cumulees
    resistance = t0_left / t0_unknown

Fraction du travail de deduction que la technique la PLUS FAIBLE ne fait pas.
Ne sature pas (contrairement a `max_level`, a 100 % partout) et ne depend
d'aucune technique dont la disponibilite varie selon les familles -- T1 par
exemple n'existe que sur les systemes portant un ALLDIFF de taille d.

Calculee par `engine/t0_legacy.py`, **module gele** : la resistance mesure
la non-localite RELATIVEMENT a un propagateur donne, donc le propagateur de
reference doit etre fige par nature. Voir DECISIONS.md.

Les deux BRUTS sont journalises, pas le ratio : une normalisation peut changer,
et un ratio journalise ne se recalcule pas. La premiere version normalisait sur
la grille entiere et etait **confondue par la densite d'indices** -- `connect`
recoit 6,0 indices et `static` 9,5, donc `static` partait de bien plus haut.

## Champ phase
Present sur les records TROP-CHER. Indique l'etape en cours quand le
budget a ete depasse, parmi :
    prefilter        is_dead() dans engine/prefilter.py
    count_solutions  comptage des grilles valides
    random_solution  tirage d'une solution
    minimal_clues    minimisation des indices
    solve_graded     resolution graduee par techniques
Sans ce champ on sait que le systeme est pathologique, pas quelle
fonction l'est. L'interruption se fait par SIGALRM : un test place ENTRE
les appels ne peut rien interrompre quand le blocage est DANS un appel.
Le champ `interrompu` distingue une interruption par signal d'un
depassement constate entre deux appels.

## Canaris
Tous tournent avant chaque run ; `--skip-canary` est reserve au debug.
Ils doivent passer depuis la racine ET depuis `engine/`.
    canary.py   positif sudoku 4x4, plus un contre-canari sans contrainte
    canary2.py  niveaux de technique requis par famille
    canary3.py  correction de T1 : aucune divergence avec la solution
    canary4.py  surete du pre-filtre : aucun faux positif
    canary8.py  gel de T0-historique : engine/t0_legacy.py doit rendre
                exactement les valeurs de canary/t0_reference.json, 60
                entrees figees le 26/08/2026. Verrouille aussi la
                semantique de feasible(), dont t0_legacy depend. Une
                divergence est un SIGNAL : ne jamais regenerer le corpus
                pour faire passer le canari.
    canary7.py  surete de la resistance a T0 : elle doit valoir 0 sur un
                systeme que T0 resout integralement, et etre strictement
                positive sur un systeme qu'il ne resout pas. Une metrique
                qui ne separe pas ces deux cas ne mesure rien.
    canary6.py  declenchement : toute technique de deduction ACTIVEE
                (niveau <= DEFAULT_MAX_LEVEL) doit s'invoquer au moins
                une fois sur les cas de reference. Une technique correcte
                mais inerte fait croire que la hierarchie discrimine sur
                un niveau qui n'existe pas en pratique. Relever
                DEFAULT_MAX_LEVEL sans rendre la technique operante fait
                echouer ce canari, donc bloque le run.
    canary5.py  surete de l'interruption par alarme, dans les deux sens :
                faux negatif (l'alarme ne se declenche pas, un systeme
                pathologique gele un bloc -- c'est arrive) et faux positif
                (un systeme sain etiquete TROP-CHER disparaitrait des
                candidats, comme un faux positif du pre-filtre).
                Tourne dans un repertoire temporaire : ne touche ni
                `runs/`, ni `found/`, ni `summary.md`.

## Niveaux de deduction
    T0  naked single   une seule valeur reste possible pour une cellule
    T1  hidden single  dans une region, une valeur n'a qu'une case possible
    T2  contradiction a profondeur 1
    T3  paire nue      PRESENT MAIS INERTE, non activee. Correct (canary3)
                       et jamais declenche : technique d'ELIMINATION alors
                       que le moteur n'a pas d'etat de candidats.
`DEFAULT_MAX_LEVEL` dans engine/deduction.py fixe le niveau en service.

## Etat 24/08/2026
- T1 (hidden single) corrige : n'est valide que sur un ALLDIFF de taille d.
  Applique a toute region il forcait des valeurs a tort -- invisible sur le
  sudoku, faux ailleurs.
- canari de correction ajoute : la deduction doit retrouver EXACTEMENT la
  solution d'origine, pas seulement remplir la grille.
- passage v1 -> v2 : le taux de MORT monte de 30% a 60%, les candidats
  tombent de 8% a 5%, et surtout ils cessent d'etre des variantes de sudoku.
- goulot actuel : on paie le solveur complet pour decouvrir qu'un systeme
  est MORT. Un pre-filtre bon marche recupererait la majorite du temps.

## Fonctionnement autonome

    sudo cp rulesearch.service /etc/systemd/system/
    sudo systemctl enable --now rulesearch

Le service lance `scheduler.py`, qui enchaine indefiniment les
configurations de `queue.json`, agrege apres chaque bloc, commit et pousse
`summary.md`. Redemarre seul apres crash ou reboot.

Changer ce que le serveur cherche = editer `queue.json` et pousser.
L'ordonnanceur fait un `git pull` a chaque cycle et prend la nouvelle file
sans qu'on touche au serveur.

### Repartition reelle des roles
- automatique : execution, rotation des configs, agregation, commit, push,
  redemarrage
- humain, une fois : installation
- humain, a chaque changement de code : `git push` (Claude ne peut pas
  ecrire dans le depot)
- non automatisable : l'analyse. Claude n'existe pas entre les sessions.
  Le moteur tourne sans lui ; lui ne tourne pas sans session.

### Canaris
- `canary.py`  sensibilite : sudoku reconnu bien pose, systeme vide rejete
- `canary2.py` separation : la hierarchie distingue des difficultes connues
- `canary3.py` correction : la deduction retrouve EXACTEMENT la solution
  d'origine. Sortie non nulle = le moteur ment. C'est celui qui aurait
  attrape le bug T1.
