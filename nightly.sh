#!/usr/bin/env bash
# Analyse nocturne headless. N'ECRIT QUE DES ANALYSES.
# crontab -e :  0 5 * * *  /home/rulesearch/rulesearch/nightly.sh
set -uo pipefail
cd "$(dirname "$0")" || exit 1

git pull --rebase --autostash >/dev/null 2>&1
python3 summarize.py >/dev/null 2>&1

DATE=$(date -u +%Y-%m-%d)
OUT="analyses/ANALYSE-${DATE}.md"
mkdir -p analyses

PROMPT=$(cat <<'P'
Lis CLAUDE.md, DECISIONS.md et summary.md, puis les journaux les plus
recents sous runs/.

Ecris une analyse dans analyses/ANALYSE-<date>.md qui repond a ces
questions et a aucune autre :

1. L'hypothese locale/non-locale : ou en est l'ecart T2 avec/sans
   CONNECTED ? Y a-t-il assez de candidats par groupe pour conclure ?
   Si non, dis-le et ne conclus pas.
2. Quels systemes CANDIDAT sont apparus depuis la derniere analyse, et
   lesquels ne ressemblent a aucun puzzle connu ?
3. Quelque chose contredit-il ce qui est ecrit dans CLAUDE.md ?
4. Ou part le temps machine, et le pre-filtre MORT est-il toujours le
   premier goulot ?

Contraintes strictes :
- ne modifie AUCUN fichier hors de analyses/
- ne touche pas a engine/, run.py, scheduler.py, summarize.py, queue.json
- ne supprime aucun journal
- si les donnees ne permettent pas de repondre, ecris-le au lieu d'extrapoler
P
)

claude -p "$PROMPT" \
  --allowedTools "Read,Grep,Glob,Write,Bash(git log:*),Bash(git diff:*)" \
  --max-turns 40 \
  --output-format text \
  > "analyses/.raw-${DATE}.txt" 2> "analyses/.err-${DATE}.txt"

RC=$?
if [ $RC -ne 0 ]; then
  echo "$(date -u) analyse headless en echec (rc=$RC)" >> nightly.log
  exit $RC
fi

git add -A analyses/ summary.md found/
git -c user.email=rulesearch@local -c user.name=rulesearch \
    commit -m "auto: analyse ${DATE}" --allow-empty >/dev/null 2>&1
git push origin HEAD >/dev/null 2>&1
echo "$(date -u) analyse ${DATE} poussee" >> nightly.log
