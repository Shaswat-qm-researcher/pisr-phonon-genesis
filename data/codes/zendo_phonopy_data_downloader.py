"""
Download ALL materials from the Materials Project Phonon database v1.1
(Zenodo record 20196565) and save ONE CSV with every field found in each
06_harmonic_phonons/summary.json.gz (mp_id, formula, elements, composition,
symmetry, volume, density, e_above_hull, min/max frequency, stability class,
debye_temperature, ...).

Usage:
    pip install requests
    python extract_all_debye.py                          # asks where to save, then downloads everything
    python extract_all_debye.py --out my_folder          # skip the question, use this folder
    python extract_all_debye.py --workers 4              # parallel downloads (keep <= 6)
    python extract_all_debye.py --test                   # only the smallest tar (quick check)
    python extract_all_debye.py --tars mp_0960001-0980000 mp_2420001-2440000   # specific tars

Works on a normal PC (Windows/macOS/Linux) and on HPC clusters:
  - Interactive terminal: asks for the save folder. Batch job / no terminal: uses --out,
    else $DEBYE_OUT, else ./debye_all (never blocks waiting for input).
  - ~ and environment variables in the path are expanded (e.g. --out $SCRATCH/debye).
  - SIGTERM/SIGUSR1/SIGHUP/Ctrl+C -> checkpoints saved, clean exit; resubmit to continue.
  - Needs internet: run it on a login/transfer node, or a compute node that has outbound
    access. Proxies are honoured via the usual HTTPS_PROXY / HTTP_PROXY variables.
  - Only dependency: requests (pip install --user requests).
  See run_debye_slurm.sh for a ready-made SLURM job script.

Robustness (the full dataset is >100 GB of streaming):
  - Mid-tar resume with HTTP Range after IncompleteRead / ProtocolError etc.
  - Checkpoint per tar every 30 s; Ctrl+C or a crash -> re-run to continue.
  - Finished tars are stored as small .jsonl files and skipped on re-run.
  - Retry budget counts only consecutive attempts with NO progress.

Output (inside <your chosen location>/zendo_phonopy_data/, created if it does not exist):
    all_debye.csv        one row per material, all fields (nested ones as JSON text,
                         'symmetry' is expanded into symmetry_* columns), plus source_tar
    parts/               per-tar .jsonl results + .state.json checkpoints (resume data)
    run_<timestamp>.log  log of this run
"""
import argparse
import csv
import gzip
import json
import logging
import os
import random
import re
import signal
import sys
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

RECORD = "20196565"
BASE = os.environ.get("ZENODO_BASE", f"https://zenodo.org/records/{RECORD}/files")
SUMMARY_RE = re.compile(r"(mp-\d+)/06_harmonic_phonons/summary\.json\.gz$")
MAX_STALLS = 30
CHECKPOINT_EVERY = 30
HEARTBEAT = 600
# preferred leading column order; any other keys found are appended automatically
PREFERRED = ["mp_id", "formula_pretty", "chemsys", "nelements", "elements", "nsites",
             "debye_temperature", "phonon_stability_class", "predicted_phonon_stable",
             "has_imaginary_modes", "min_frequency", "max_frequency", "e_above_hull",
             "volume", "density"]

STOP = threading.Event()

# (tar name, size in MB)
TARS = [
    ("mp_0000001-0020000", 14500), ("mp_0020001-0040000", 7100), ("mp_0040001-0060000", 153.0),
    ("mp_0500001-0520000", 512.4), ("mp_0520001-0540000", 18.7), ("mp_0540001-0560000", 5300),
    ("mp_0560001-0580000", 2900), ("mp_0580001-0600000", 135.3), ("mp_0600001-0620000", 345.7),
    ("mp_0620001-0640000", 814.5), ("mp_0640001-0660000", 723.8), ("mp_0660001-0680000", 739.6),
    ("mp_0680001-0700000", 635.8), ("mp_0700001-0720000", 94.8), ("mp_0720001-0740000", 185.3),
    ("mp_0740001-0760000", 3700), ("mp_0760001-0780000", 3300), ("mp_0780001-0800000", 105.3),
    ("mp_0800001-0820000", 6.4), ("mp_0840001-0860000", 153.9), ("mp_0860001-0880000", 1800),
    ("mp_0880001-0900000", 22.1), ("mp_0920001-0940000", 7.7), ("mp_0940001-0960000", 6.2),
    ("mp_0960001-0980000", 1100), ("mp_0980001-1000000", 1200), ("mp_1000001-1020000", 1100),
    ("mp_1020001-1040000", 2400), ("mp_1040001-1060000", 993.5), ("mp_1060001-1080000", 860.8),
    ("mp_1080001-1100000", 1100), ("mp_1100001-1120000", 4300), ("mp_1120001-1140000", 82.1),
    ("mp_1140001-1160000", 153.2), ("mp_1160001-1180000", 630.7), ("mp_1180001-1200000", 6900),
    ("mp_1200001-1220000", 8000), ("mp_1220001-1240000", 6300), ("mp_1240001-1260000", 1300),
    ("mp_1260001-1280000", 13.3), ("mp_1300001-1320000", 19.2), ("mp_1320001-1340000", 43.6),
    ("mp_1340001-1360000", 230.3), ("mp_1360001-1380000", 272.2), ("mp_1380001-1400000", 178.2),
    ("mp_1400001-1420000", 135.6), ("mp_1420001-1440000", 18.0), ("mp_1440001-1460000", 28.9),
    ("mp_1500001-1520000", 1700), ("mp_1520001-1540000", 1700), ("mp_1540001-1560000", 43.5),
    ("mp_1940001-1960000", 6.9), ("mp_1960001-1980000", 21.8), ("mp_1980001-2000000", 8.5),
    ("mp_2000001-2020000", 26.7), ("mp_2020001-2040000", 25.2), ("mp_2040001-2060000", 25.3),
    ("mp_2200001-2220000", 173.7), ("mp_2220001-2240000", 216.6), ("mp_2240001-2260000", 17.3),
    ("mp_2260001-2280000", 1.3), ("mp_2340001-2360000", 2.3), ("mp_2360001-2380000", 23.2),
    ("mp_2380001-2400000", 8.0), ("mp_2400001-2420000", 1.5), ("mp_2420001-2440000", 1.0),
    ("mp_2440001-2460000", 7.3), ("mp_2460001-2480000", 6.4), ("mp_2480001-2500000", 4.3),
    ("mp_2500001-2520000", 9.3), ("mp_2520001-2540000", 4.8), ("mp_2580001-2600000", 13.0),
    ("mp_2620001-2640000", 3.0), ("mp_2640001-2660000", 58.0), ("mp_2660001-2680000", 5.0),
    ("mp_2680001-2700000", 3.7), ("mp_2700001-2720000", 24.1), ("mp_2720001-2740000", 24.4),
    ("mp_2740001-2760000", 60.0), ("mp_2760001-2780000", 110.6), ("mp_2800001-2820000", 2.3),
    ("mp_2820001-2840000", 1.4), ("mp_2860001-2880000", 1.2), ("mp_2900001-2920000", 54.9),
    ("mp_2920001-2940000", 5.4), ("mp_3200001-3220000", 20.1), ("mp_3340001-3360000", 86.5),
]


def list_tars(log):
    """Try the Zenodo API for the current tar list; fall back to the built-in list."""
    try:
        r = requests.get(f"https://zenodo.org/api/records/{RECORD}/files", timeout=60)
        r.raise_for_status()
        out = [(e["key"][:-4], e.get("size", 0) / 1e6)
               for e in r.json()["entries"] if e["key"].endswith(".tar")]
        if out:
            log.info(f"Tar list from Zenodo API: {len(out)} tars")
            return out
    except Exception as e:
        log.warning(f"Zenodo API listing failed ({e!r}); using built-in list")
    log.info(f"Using built-in tar list: {len(TARS)} tars")
    return list(TARS)


def save_state(path, resume_at, rows, last_save_info=None):
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"resume_at": resume_at, "rows": rows}, f)
    os.replace(tmp, path)


def scan_tar(name, parts_dir, log):
    """Stream one tar and keep every summary.json.gz as a dict. Resumes mid-tar on errors."""
    part = parts_dir / f"{name}.jsonl"
    state_path = parts_dir / f"{name}.state.json"
    if part.exists():
        log.info(f"[{name}] already done in an earlier run - skipped")
        return name, "resumed", 0
    url = f"{BASE}/{name}.tar?download=1"

    rows, seen = [], set()
    resume_at = 0
    if state_path.exists():
        try:
            s = json.loads(state_path.read_text(encoding="utf-8"))
            resume_at, rows = int(s["resume_at"]), s["rows"]
            seen = {r["mp_id"] for r in rows if r.get("mp_id")}
            log.info(f"[{name}] checkpoint loaded: byte {resume_at:,}, {len(rows)} materials so far")
        except Exception as e:
            log.warning(f"[{name}] unreadable checkpoint ({e!r}) - restarting this tar")
            rows, seen, resume_at = [], set(), 0

    start_offset = resume_at
    done = interrupted = False
    fails = attempt = 0
    last_err = None
    t0 = last_save = last_beat = time.time()

    while not done:
        if STOP.is_set():
            interrupted = True
            break
        attempt += 1
        mark = resume_at
        try:
            headers = {"Accept-Encoding": "identity"}
            if resume_at:
                headers["Range"] = f"bytes={resume_at}-"
            log.info(f"[{name}] attempt {attempt} from byte {resume_at:,} ({len(rows)} materials so far)")
            with requests.get(url, stream=True, timeout=(30, 300), headers=headers) as r:
                if resume_at and r.status_code == 416:
                    log.info(f"[{name}] offset past end of file - tar already complete")
                    done = True
                    break
                if resume_at and r.status_code != 206:
                    log.warning(f"[{name}] Range not honoured (HTTP {r.status_code}); restarting from 0")
                    rows, seen, resume_at = [], set(), 0
                    state_path.unlink(missing_ok=True)
                    raise RuntimeError("server ignored Range header")
                r.raise_for_status()
                base = resume_at
                with tarfile.open(fileobj=r.raw, mode="r|", bufsize=1 << 20) as tar:
                    for m in tar:
                        resume_at = base + m.offset
                        if STOP.is_set():
                            interrupted = True
                            break
                        now = time.time()
                        if now - last_save > CHECKPOINT_EVERY:
                            save_state(state_path, resume_at, rows)
                            last_save = now
                        if now - last_beat > HEARTBEAT:
                            mb = (resume_at - start_offset) / 1e6
                            log.info(f"[{name}] still running: byte {resume_at:,} "
                                     f"({mb / max(now - t0, 1e-9):.1f} MB/s), {len(rows)} materials")
                            last_beat = now
                        if not m.isfile():
                            continue
                        mt = SUMMARY_RE.search(m.name)
                        if not mt:
                            continue
                        mid = mt.group(1)
                        if mid in seen:
                            continue
                        try:
                            d = json.load(gzip.open(tar.extractfile(m), "rt"))
                        except (EOFError, OSError, ValueError) as e:
                            # a truncated stream raises here too -> let outer handler retry
                            if isinstance(e, (EOFError, OSError)) and not isinstance(e, gzip.BadGzipFile):
                                raise
                            log.warning(f"[{name}] could not parse {m.name}: {e!r}")
                            continue
                        if not d.get("mp_id"):
                            d["mp_id"] = mid
                        d["source_tar"] = name
                        rows.append(d)
                        seen.add(mid)
            if interrupted:
                break
            done = True
        except Exception as e:
            last_err = e
            code = e.response.status_code if isinstance(e, requests.HTTPError) and e.response is not None else None
            if code in (403, 404):
                log.error(f"[{name}] HTTP {code} - retrying will not help")
                break
            fails = 0 if resume_at > mark else fails + 1
            log.warning(f"[{name}] attempt {attempt} failed at byte {resume_at:,} "
                        f"({len(rows)} materials, {fails}/{MAX_STALLS} stalls): {e!r}")
            try:
                save_state(state_path, resume_at, rows)
                last_save = time.time()
            except Exception as se:
                log.warning(f"[{name}] could not save checkpoint: {se!r}")
            if fails >= MAX_STALLS:
                break
            wait = min(10 * max(fails, 1), 300) + random.uniform(0, 5)
            log.info(f"[{name}] resuming in {wait:.0f}s")
            if STOP.wait(wait):
                interrupted = True
                break

    if interrupted:
        try:
            save_state(state_path, resume_at, rows)
        except Exception:
            pass
        log.info(f"[{name}] stopped; checkpoint saved at byte {resume_at:,} ({len(rows)} materials)")
        return name, "interrupted", 0
    if not done:
        log.error(f"[{name}] FAILED: {last_err!r} (checkpoint kept - re-run to continue)")
        return name, "failed", 0

    tmp = part.with_suffix(".jsonl.part")
    with open(tmp, "w", encoding="utf-8") as f:
        for d in rows:
            f.write(json.dumps(d) + "\n")
    os.replace(tmp, part)
    state_path.unlink(missing_ok=True)
    secs = time.time() - t0
    log.info(f"[{name}] done: {len(rows)} materials in {secs:.0f}s")
    return name, "ok", len(rows)


def flatten(d):
    """One CSV row: scalars as-is, 'symmetry' expanded, other nested values as JSON text."""
    out = {}
    for k, v in d.items():
        if k == "symmetry" and isinstance(v, dict):
            for kk, vv in v.items():
                out[f"symmetry_{kk}"] = json.dumps(vv) if isinstance(vv, (dict, list)) else vv
        elif isinstance(v, (dict, list)):
            out[k] = json.dumps(v, separators=(",", ":"))
        else:
            out[k] = v
    return out


def merge(names, parts_dir, out_csv, log):
    rows, keys = [], {}
    for name in names:
        part = parts_dir / f"{name}.jsonl"
        if not part.exists():
            continue
        with open(part, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    flat = flatten(json.loads(line))
                    rows.append(flat)
                    for k in flat:
                        keys.setdefault(k, None)
    uniq = {}
    for r in rows:
        uniq[r.get("mp_id")] = r          # de-duplicate by mp_id
    rows = sorted(uniq.values(), key=lambda r: int(re.sub(r"\D", "", str(r.get("mp_id"))) or 0))
    cols = [c for c in PREFERRED if c in keys]
    cols += [c for c in keys if c not in cols and c != "source_tar"]
    if "source_tar" in keys:
        cols.append("source_tar")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    n_deb = sum(1 for r in rows if r.get("debye_temperature") not in (None, "", "None"))
    log.info("=" * 60)
    log.info(f"Materials written        : {len(rows)}")
    log.info(f"  with Debye temperature : {n_deb}")
    log.info(f"  Debye temperature empty: {len(rows) - n_deb}")
    log.info(f"Columns                  : {len(cols)}")
    log.info(f"Saved -> {out_csv}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="output folder (if omitted, you are asked)")
    ap.add_argument("--workers", type=int, default=4, help="parallel downloads (default 4, keep <= 6)")
    ap.add_argument("--test", action="store_true", help="only process the smallest tar")
    ap.add_argument("--tars", nargs="+", help="only these tars (names with or without .tar)")
    args, _unknown = ap.parse_known_args()      # ignores extra args such as Jupyter's "-f kernel.json"
    STOP.clear()                                # allows re-running main() in the same Jupyter kernel
    in_jupyter = "ipykernel" in sys.modules

    # Output folder: --out, else $DEBYE_OUT, else ask (interactive PC), else ./debye_all (batch/HPC)
    out = args.out or os.environ.get("DEBYE_OUT")
    defaulted = False
    if not out:
        if in_jupyter or (sys.stdin is not None and sys.stdin.isatty()):
            out = input("Folder to save results in (created if it does not exist): ").strip().strip('"').strip("'")
            if not out:
                raise SystemExit("No save folder given.")
        else:
            out, defaulted = "debye_all", True
    # supports ~ and $SCRATCH etc.; everything goes into an extra "zendo_phonopy_data" subfolder
    out_dir = Path(os.path.expandvars(os.path.expanduser(out))) / "zendo_phonopy_data"
    out_dir.mkdir(parents=True, exist_ok=True)      # create the folder if missing
    parts_dir = out_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    log = logging.getLogger("extract_all")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    log_path = out_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    for h in (logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")):
        h.setFormatter(fmt)
        log.addHandler(h)

    if defaulted:
        log.warning("No terminal and no --out/$DEBYE_OUT given: saving to ./debye_all")

    # Graceful stop on Ctrl+C and on scheduler signals (SLURM/PBS/LSF send SIGTERM/SIGUSR1 before killing)
    def _on_signal(signum, _frame):
        log.warning(f"Signal {signum} received - saving checkpoints and stopping...")
        STOP.set()
    # (skipped in Jupyter: the kernel's own interrupt button raises KeyboardInterrupt, handled below)
    for sig in ([] if in_jupyter else ("SIGINT", "SIGTERM", "SIGUSR1", "SIGHUP")):
        if hasattr(signal, sig):
            try:
                signal.signal(getattr(signal, sig), _on_signal)
            except (ValueError, OSError):
                pass

    tars = list_tars(log)
    if args.tars:
        wanted = {t[:-4] if t.endswith(".tar") else t for t in args.tars}
        tars = [t for t in tars if t[0] in wanted]
        missing = wanted - {t[0] for t in tars}
        if missing:
            log.warning(f"Unknown tar names ignored: {sorted(missing)}")
    if args.test:
        tars = [min(tars, key=lambda t: t[1] or 1e18)]
        log.info(f"TEST mode: {tars[0][0]}")
    if not tars:
        raise SystemExit("No tars to process.")

    plan = [n for n, _ in sorted(tars, key=lambda t: -(t[1] or 0))]   # biggest first
    log.info(f"Run started: {len(plan)} tars, ~{sum(s for _, s in tars) / 1000:.1f} GB, "
             f"{args.workers} workers, output {out_dir.resolve()}")

    t_all = time.time()
    status = {}
    ex = ThreadPoolExecutor(args.workers)
    try:
        futs = [ex.submit(scan_tar, n, parts_dir, log) for n in plan]
        for i, fut in enumerate(as_completed(futs), 1):
            name, st, n = fut.result()
            status[name] = st
            log.info(f"--- progress: {i}/{len(plan)} tars finished ({time.time() - t_all:.0f}s) ---")
    except KeyboardInterrupt:
        STOP.set()
        ex.shutdown(wait=True, cancel_futures=True)
    ex.shutdown(wait=True)

    if STOP.is_set():
        log.info("Stopped cleanly. Re-run the same command (same folder) to continue.")
        return

    merge(plan, parts_dir, out_dir / "all_debye.csv", log)
    bad = sorted(t for t, s in status.items() if s == "failed")
    if bad:
        log.warning(f"Failed tars (re-run to retry): {bad}")
    log.info(f"Total time: {time.time() - t_all:.0f}s")
    log.info("Run finished" + (" WITH FAILURES" if bad else " OK"))


if __name__ == "__main__":
    main()