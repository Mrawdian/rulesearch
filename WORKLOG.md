# WORKLOG — rulesearch

Journal des interventions faites **sur le serveur** (`rulesearch@77.42.21.130`,
depot `/home/rulesearch/rulesearch`).

Ce fichier existe parce que Claude en chat n a **aucun acces** au serveur ni au
depot : c est son seul canal d information. Chaque entree doit donc se lire
seule, sans contexte exterieur.

Entree la plus recente **en haut**.

---

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
