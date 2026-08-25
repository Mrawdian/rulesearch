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
    canary5.py  surete de l'interruption par alarme, dans les deux sens :
                faux negatif (l'alarme ne se declenche pas, un systeme
                pathologique gele un bloc -- c'est arrive) et faux positif
                (un systeme sain etiquete TROP-CHER disparaitrait des
                candidats, comme un faux positif du pre-filtre).
                Tourne dans un repertoire temporaire : ne touche ni
                `runs/`, ni `found/`, ni `summary.md`.

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
