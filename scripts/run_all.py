"""Executa todo o pipeline em ordem (download → tratamento → Partes I, II e III).

Uso (a partir da raiz do projeto):
    python scripts/run_all.py            # completo (~25 min)
    python scripts/run_all.py --quick    # benchmark e robustez reduzidos (~12 min)
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import src  # noqa: E402,F401  (configura a saída em UTF-8 no Windows)

STEPS = [
    ["scripts/download_data.py"],
    ["-m", "src.treatment"],
    ["-m", "src.prepare_data"],
    ["-m", "src.metrics"],
    ["-m", "src.distances"],
    ["-m", "src.clustering"],
    ["-m", "src.visualize"],
    ["-m", "src.part1_summary"],
    ["-m", "src.benchmark"],
    ["-m", "src.smallworld"],
    ["-m", "src.powerlaw"],
    ["-m", "src.centrality"],
    ["-m", "src.robustness"],
    ["-m", "src.hubs"],
    ["-m", "src.models"],
    ["-m", "src.report_tables"],
]
QUICK_CAPABLE = {"src.benchmark", "src.robustness"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    start = time.perf_counter()
    for step in STEPS:
        cmd = [sys.executable, *step]
        if args.quick and step[-1] in QUICK_CAPABLE:
            cmd.append("--quick")
        print(f"\n=== {' '.join(cmd[1:])} ===", flush=True)
        t0 = time.perf_counter()
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)
        print(f"--- concluído em {time.perf_counter() - t0:.1f}s", flush=True)
    print(f"\nPipeline completo em {(time.perf_counter() - start) / 60:.1f} min.")


if __name__ == "__main__":
    main()
