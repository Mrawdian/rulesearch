#!/usr/bin/env python3
"""
Runner de production. Tourne en boucle jusqu'a arret.

  python3 run.py --n 4 --d 4 --tag baseline
  python3 run.py --n 5 --d 3 --tag connect --families connect,cages

Refuse de demarrer si les canaris ne passent pas.
Journal append-only en JSONL. Un fichier par candidat retenu dans found/.
"""
import argparse, hashlib, json, os, random, subprocess, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))

from rulesearch import (UNASSIGNED, RuleSystem, rows, cols, diags, blocks,
                        Count, AllDiff, SumRange, NeqAdj, NoTriple, Mono,
                        count_solutions, random_solution, minimal_clues)
from dsl2 import (random_cages, adj_pairs, knight_pairs,
                  PairDiff, PairRatio, Connected, NoSquare)
from deduction import solve_graded
from prefilter import is_dead


# ---------- identite du DSL ----------

def dsl_hash():
    h = hashlib.sha256()
    for fn in sorted(os.listdir(os.path.join(HERE, "engine"))):
        if fn.endswith(".py"):
            with open(os.path.join(HERE, "engine", fn), "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:12]


def run_canaries():
    ok = True
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(HERE, "engine") + os.pathsep + env.get("PYTHONPATH", "")
    for c in ("canary.py", "canary2.py", "canary3.py", "canary4.py"):
        p = os.path.join(HERE, "canary", c)
        if not os.path.exists(p):
            continue
        r = subprocess.run([sys.executable, p], cwd=os.path.join(HERE, "engine"),
                           env=env, capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            print("CANARI ECHOUE :", c, file=sys.stderr)
            print(r.stdout[-2000:], file=sys.stderr)
            print(r.stderr[-2000:], file=sys.stderr)
            ok = False
    return ok


# ---------- generation de systemes ----------

FAMILIES = ["static", "cages", "relational", "connect"]


def gen_system(n, d, rng, families):
    cons, parts = [], []
    k = rng.randint(2, 3)
    for _ in range(k):
        fam = rng.choice(families)

        if fam == "static":
            regs_name = rng.choice(["rows", "cols", "diags", "blocks"])
            regions = {"rows": rows, "cols": cols, "diags": diags, "blocks": blocks}[regs_name](n)
            if not regions:
                continue
            t = rng.choice(["ALLDIFF", "COUNT", "SUM", "NEQADJ", "NOTRIPLE", "MONO"])
            if t == "ALLDIFF":
                if d < min(len(R) for R in regions):
                    continue
                cons += [AllDiff(R) for R in regions]
                parts.append(f"ALLDIFF@{regs_name}")
            elif t == "COUNT":
                v = rng.randrange(d); lo = rng.randint(0, max(0, n // 2)); hi = lo + rng.randint(0, 1)
                cons += [Count(R, v, lo, min(hi, len(R))) for R in regions]
                parts.append(f"COUNT(v{v},{lo}-{hi})@{regs_name}")
            elif t == "SUM":
                tgt = rng.randint(0, (d - 1) * n); sl = rng.randint(0, 1)
                cons += [SumRange(R, max(0, tgt - sl), tgt + sl, d) for R in regions]
                parts.append(f"SUM({tgt}+-{sl})@{regs_name}")
            elif t == "NEQADJ":
                cons += [NeqAdj(R) for R in regions]; parts.append(f"NEQADJ@{regs_name}")
            elif t == "NOTRIPLE":
                cons += [NoTriple(R) for R in regions]; parts.append(f"NOTRIPLE@{regs_name}")
            else:
                cons += [Mono(R) for R in regions]; parts.append(f"MONO@{regs_name}")

        elif fam == "cages":
            lo_s = rng.randint(2, 3); hi_s = lo_s + rng.randint(0, 2)
            cages = random_cages(n, rng, lo_s, hi_s)
            t = rng.choice(["SUM", "ALLDIFF"])
            if t == "ALLDIFF":
                cages = [C for C in cages if len(C) <= d]
                if not cages:
                    continue
                cons += [AllDiff(C) for C in cages]
                parts.append(f"ALLDIFF@cages({lo_s}-{hi_s})")
            else:
                sl = rng.randint(0, 1)
                for C in cages:
                    tgt = rng.randint(0, (d - 1) * len(C))
                    cons.append(SumRange(C, max(0, tgt - sl), tgt + sl, d))
                parts.append(f"SUM@cages({lo_s}-{hi_s})")

        elif fam == "relational":
            pr_name = rng.choice(["adj", "knight"])
            pairs = adj_pairs(n) if pr_name == "adj" else knight_pairs(n)
            if rng.random() < 0.5:
                kk = rng.randint(1, max(1, d // 2))
                cons.append(PairDiff(pairs, kk, n)); parts.append(f"PAIRDIFF(>={kk})@{pr_name}")
            else:
                dd = rng.randint(1, max(1, d - 1))
                cons.append(PairRatio(pairs, dd)); parts.append(f"PAIRSTEP({dd})@{pr_name}")

        elif fam == "connect":
            v = rng.randrange(d)
            cons.append(Connected(n, v)); parts.append(f"CONNECTED(v{v})")
            if rng.random() < 0.6:
                cons.append(NoSquare(n, v)); parts.append(f"NOSQUARE(v{v})")
            lo = rng.randint(1, n * n // 2); hi = min(n * n, lo + rng.randint(1, n))
            cons.append(Count(list(range(n * n)), v, lo, hi))
            parts.append(f"COUNT(v{v},{lo}-{hi})@grid")

    if not cons:
        return None
    return RuleSystem(n, d, cons, " + ".join(parts))


# ---------- evaluation ----------

MIN_GRIDS = 12
MAX_CLUE_FRAC = 0.55
# budget de temps par systeme. count_solutions a un budget de noeuds,
# random_solution et minimal_clues n'en avaient aucun : un systeme vivant
# et couteux pouvait bloquer un bloc entier.
MAX_SECONDS = 45


def evaluate_system(rs, n_instances=6, max_seconds=MAX_SECONDS):
    n = rs.n; cells = n * n
    t0 = time.time()
    # pre-filtre : propagation seule, sans backtracking. Ne peut produire
    # que des vrais positifs (voir engine/prefilter.py et canary/canary4.py).
    if is_dead(rs):
        return {"verdict": "MORT", "total_grids": 0, "prefiltered": True}
    if time.time() - t0 > max_seconds:
        return {"verdict": "TROP-CHER", "elapsed_s": round(time.time() - t0, 1)}
    total = count_solutions(rs, [UNASSIGNED] * cells, cap=MIN_GRIDS + 1)
    if total is None:
        return {"verdict": "TIMEOUT"}
    if total == 0:
        return {"verdict": "MORT", "total_grids": 0}
    if total <= MIN_GRIDS:
        return {"verdict": "SUR-CONTRAINT", "total_grids": total}

    fracs, levels, uses_acc = [], [], {0: 0, 1: 0, 2: 0}
    solved = 0
    for _ in range(n_instances):
        if time.time() - t0 > max_seconds:
            return {"verdict": "TROP-CHER",
                    "elapsed_s": round(time.time() - t0, 1),
                    "total_grids": total}
        sol = random_solution(rs)
        if sol is None:
            return {"verdict": "MORT", "total_grids": total}
        puz = minimal_clues(rs, sol)
        fracs.append(sum(1 for x in puz if x != UNASSIGNED) / cells)
        r = solve_graded(rs, puz)
        if r["solved"]:
            solved += 1
            levels.append(r["max_level"])
            for k in uses_acc:
                uses_acc[k] += r["uses"][k]
    if not fracs:
        return {"verdict": "MORT", "total_grids": total}

    cf = sum(fracs) / len(fracs)
    out = {"total_grids": total, "clue_frac": round(cf, 3),
           "solved_frac": round(solved / n_instances, 3),
           "level_uses": uses_acc,
           "max_level": max(levels) if levels else -1}
    if cf > MAX_CLUE_FRAC:
        out["verdict"] = "LIBRE"
    elif solved < n_instances:
        out["verdict"] = "DEVINETTE"
    elif out["max_level"] <= 0:
        out["verdict"] = "PLAT"
    else:
        out["verdict"] = "CANDIDAT"
    return out


# ---------- boucle ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--d", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--families", default="static,cages,relational,connect")
    ap.add_argument("--instances", type=int, default=6)
    ap.add_argument("--max-systems", type=int, default=0)
    ap.add_argument("--max-seconds", type=int, default=MAX_SECONDS)
    ap.add_argument("--skip-canary", action="store_true")
    a = ap.parse_args()

    if not a.skip_canary and not run_canaries():
        sys.exit("canaris en echec : run refuse")

    dh = dsl_hash()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rundir = os.path.join(HERE, "runs", f"{stamp}-{dh}-{a.tag}")
    os.makedirs(rundir, exist_ok=True)
    os.makedirs(os.path.join(HERE, "found"), exist_ok=True)
    with open(os.path.join(rundir, "config.json"), "w") as f:
        json.dump({**vars(a), "dsl_hash": dh}, f, indent=2)

    families = a.families.split(",")
    rng = random.Random(a.seed)
    random.seed(a.seed)
    jl = open(os.path.join(rundir, "results.jsonl"), "a", buffering=1)

    i = 0
    seen = set()
    while True:
        if a.max_systems and i >= a.max_systems:
            break
        rs = gen_system(a.n, a.d, rng, families)
        i += 1
        if rs is None or rs.label in seen:
            continue
        seen.add(rs.label)
        t0 = time.time()
        try:
            res = evaluate_system(rs, a.instances, a.max_seconds)
        except Exception as e:
            res = {"verdict": "ERREUR", "err": repr(e)[:200]}
        rec = {"ts": time.time(), "dsl_hash": dh, "seed": a.seed, "idx": i,
               "n": a.n, "d": a.d, "sys": rs.label,
               "ms": int(1000 * (time.time() - t0)), **res}
        jl.write(json.dumps(rec) + "\n")
        if res.get("verdict") == "CANDIDAT":
            name = f"{dh}-s{a.seed}-i{i}.json"
            with open(os.path.join(HERE, "found", name), "w") as f:
                json.dump(rec, f, indent=2)


if __name__ == "__main__":
    main()
