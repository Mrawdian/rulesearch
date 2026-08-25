#!/usr/bin/env python3
"""
Ordonnanceur. Lit queue.json, enchaine les configurations indefiniment,
agrege apres chaque bloc et pousse le resume.

Aucune intervention humaine apres le premier demarrage.
Modifier queue.json et pousser suffit a changer ce que le serveur cherche :
l'ordonnanceur relit le fichier a chaque cycle et fait un git pull avant.
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue.json")
PY = os.environ.get("RS_PYTHON", "pypy3")

DEFAULT_QUEUE = {
    "block_systems": 400,
    "configs": [
        {"tag": "baseline",  "n": 4, "d": 4, "families": "static,cages,relational,connect"},
        {"tag": "connect",   "n": 4, "d": 2, "families": "connect,relational"},
        {"tag": "cages",     "n": 4, "d": 4, "families": "cages,static"},
        {"tag": "static-ref","n": 4, "d": 4, "families": "static"},
        {"tag": "big",       "n": 5, "d": 3, "families": "static,cages,relational,connect"}
    ]
}


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, cwd=HERE, capture_output=True, text=True, **kw)


def load_queue():
    if not os.path.exists(QUEUE):
        with open(QUEUE, "w") as f:
            json.dump(DEFAULT_QUEUE, f, indent=2)
    with open(QUEUE) as f:
        return json.load(f)


def main():
    seed = int(time.time()) % 100000
    canary_done = False
    while True:
        sh("git pull --rebase --autostash")
        q = load_queue()
        for cfg in q["configs"]:
            seed += 1
            args = [PY, os.path.join(HERE, "run.py"),
                    "--n", str(cfg["n"]), "--d", str(cfg["d"]),
                    "--tag", cfg["tag"], "--families", cfg["families"],
                    "--seed", str(seed),
                    "--max-systems", str(q.get("block_systems", 400))]
            if canary_done:
                args.append("--skip-canary")
            print("[sched]", " ".join(args), flush=True)
            r = subprocess.run(args, cwd=HERE)
            if r.returncode != 0:
                print("[sched] run en echec, arret", file=sys.stderr, flush=True)
                return 1
            canary_done = True

            subprocess.run([sys.executable, os.path.join(HERE, "summarize.py")], cwd=HERE)
            sh("git add -A summary.md found/ && "
               "git -c user.email=rulesearch@local -c user.name=rulesearch "
               "commit -m 'auto: resume %s' --allow-empty" % cfg["tag"])
            sh("git push origin HEAD")


if __name__ == "__main__":
    sys.exit(main())
