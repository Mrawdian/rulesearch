#!/usr/bin/env python3
"""
Ordonnanceur. Lit queue.json, enchaine les configurations indefiniment,
agrege apres chaque bloc et pousse le resume.

Aucune intervention humaine apres le premier demarrage.
Modifier queue.json et pousser suffit a changer ce que le serveur cherche :
l'ordonnanceur relit le fichier a chaque cycle et fait un git pull avant.
"""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue.json")
# Copie figee du moteur, prise au debut de chaque cycle. Le serveur ne doit
# pas tourner sur un arbre de travail : sans ce gel, une edition en cours
# est captee a mi-chemin par le bloc qui demarre, et produit une serie sous
# un dsl_hash dont la source ne sera jamais commitee. Arrive le 26/08/2026 :
# 7172 enregistrements sous un code irrecuperable.
SNAPSHOT = os.path.join(HERE, ".engine-run")
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
    r = subprocess.run(cmd, shell=True, cwd=HERE, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("[sched][ERROR] commande en echec (rc=%d) : %s" % (r.returncode, cmd),
              file=sys.stderr, flush=True)
        for name, out in (("stdout", r.stdout), ("stderr", r.stderr)):
            txt = (out or "").strip()
            if txt:
                print("[sched][ERROR] %s: %s" % (name, txt[-2000:]),
                      file=sys.stderr, flush=True)
    return r


def geler_engine():
    """Fige engine/ pour la duree du cycle. Rend le chemin de la copie."""
    src = os.path.join(HERE, "engine")
    tmp = SNAPSHOT + ".tmp"
    for d in (tmp, SNAPSHOT):
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(src, tmp, ignore=shutil.ignore_patterns("__pycache__"))
    os.rename(tmp, SNAPSHOT)          # bascule atomique
    return SNAPSHOT


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
        engine = geler_engine()
        env = dict(os.environ)
        env["RS_ENGINE"] = engine
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
            r = subprocess.run(args, cwd=HERE, env=env)
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
