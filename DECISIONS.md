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
