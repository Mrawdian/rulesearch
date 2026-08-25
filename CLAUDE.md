# CLAUDE.md — rulesearch

Lis ce fichier en entier avant toute action. Puis `summary.md`. Puis
`DECISIONS.md`. Ne touche pas au code avant ces trois lectures.

## Protocole de session

A appliquer a chaque intervention, sans exception.

1. **Lire avant d agir** : `CLAUDE.md`, puis `DECISIONS.md`, puis `WORKLOG.md`.
   Aucune modification du depot avant ces trois lectures. `WORKLOG.md` donne
   l etat reel du serveur et ce qui a deja ete tente.
2. **Ecrire l entree `WORKLOG.md` avant le commit final**, pas apres. Entree la
   plus recente en haut, au format defini dans le fichier. Le commit qui corrige
   et l entree qui le documente vont ensemble.
3. **Toujours distinguer verifie de suppose.** Ce qui a ete execute et observe
   va dans **Verifie** ; tout le reste va dans **Non verifie / suppose**, meme
   si c est probable. Ne jamais presenter une deduction comme une observation.
4. **Commande refusee : consigner et s arreter.** Si un `sudo`, un acces
   journal ou une dependance manque, l ecrire dans **Bloque sur**, le signaler
   a l operateur humain, et s arreter sur ce point. **Ne pas contourner.**
   Le reste de la tache, qui n en depend pas, doit etre mene a terme.

## Ce qu'on cherche

L'espace des **systemes de regles** de puzzles, pas l'espace des instances.
Generer un sudoku est resolu ; chercher quelles familles de regles produisent
des puzzles bien poses ne l'est pas.

Un systeme est retenu (CANDIDAT) s'il produit des instances a solution
unique, resolubles par deduction pure sans devinette, avec peu d'indices
et un niveau de technique superieur au plus faible.

## Ce que l'oracle ne couvre pas

La structure est calculable. L'interet de jouer ne l'est pas. Ce moteur est
un **filtre d'elimination**, jamais un juge. Ne jamais ecrire qu'un systeme
est "bon" ou "amusant" : il est bien pose, c'est tout.

## Invariants durs — ne jamais violer

1. Les canaris tournent avant tout run. `--skip-canary` est reserve au debug.
   Un banc casse produit du bruit indistinguable de vrais resultats.
2. Ne jamais comparer des lignes de `dsl_hash` differents. Le hash change des
   qu'un fichier de `engine/` change.
3. Toute nouvelle technique de deduction exige un canari de CORRECTION avant
   d'etre utilisee : la deduction doit retrouver EXACTEMENT la solution
   d'origine, pas seulement remplir la grille.
4. Ne conclure sur aucune hypothese sous 20 candidats par groupe compare.
5. La tache nocturne headless n'ecrit que des analyses. Elle ne modifie pas
   `engine/`, ne change pas les seuils, ne supprime aucun journal.

## Erreurs deja payees — ne pas les refaire

- **T1 faux (corrige).** "hidden single" n'est valide que sur un ALLDIFF de
  taille exactement d. Applique a toute region, il force des valeurs a tort.
  Invisible sur le sudoku, qui satisfait la condition partout. C'est ce qui a
  motive l'invariant 3.
- **DSL v1 trop pauvre.** Regions statiques seules (lignes, colonnes, blocs,
  diagonales) : l'espace ne pouvait produire que des variantes de sudoku. Ce
  n'etait pas un probleme de solveur mais de langage.
- **Mesure de profondeur vide.** Compter les passes d'une technique unique
  sature vers 2-3 pour tout, sudoku compris. La profondeur ne veut dire
  quelque chose que relativement a une hierarchie de techniques.

## Hypothese en cours

La ligne de fracture entre systemes plats et systemes profonds n'est pas
"quelles contraintes" mais **decomposable localement ou non**. La
connectivite (`Connected`) est le seul type non decomposable en contraintes
locales.

Test : parmi les CANDIDATS, ceux contenant CONNECTED atteignent-ils T2
nettement plus souvent que les autres, a taux de candidats comparable ?
`summarize.py` calcule cet ecart et refuse de conclure sous 20 par groupe.

Sur 49 systemes (echantillon sans valeur statistique) : config `connect`
12,5 % de candidats tous a T2, config statique 0 %. Va dans le sens de
l'hypothese, ne la prouve pas.

Si l'hypothese tombe, le DSL v2 n'est qu'un v1 elargi et il faut chercher la
fracture ailleurs.

## Prochaine tache, par priorite

1. **Pre-filtre des systemes MORT.** 97 % du temps machine part a decouvrir
   par solveur complet qu'un systeme n'a aucune solution. Facteur ~30 sur le
   debit. Piste : propagation d'arc a cout borne avant d'appeler le solveur.
2. Etendre a n=5 et n=6 une fois le pre-filtre en place.
3. Ajouter T3 (paires/triplets nus) si et seulement si T2 sature.

## Ce qu'il ne faut pas faire

- Elargir le DSL sans ajouter le canari correspondant.
- Reecrire le solveur "au propre". Il marche et il est verifie.
- Ajouter des dependances. Stdlib seule, c'est un choix : le moteur doit
  tourner sur pypy3 sans installation.
- Conclure sur des echantillons faibles parce que la tendance est jolie.
