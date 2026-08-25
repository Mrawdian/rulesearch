# WORKLOG — rulesearch

Journal des interventions faites **sur le serveur** (`rulesearch@77.42.21.130`,
depot `/home/rulesearch/rulesearch`).

Ce fichier existe parce que Claude en chat n a **aucun acces** au serveur ni au
depot : c est son seul canal d information. Chaque entree doit donc se lire
seule, sans contexte exterieur.

Entree la plus recente **en haut**.

---

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
