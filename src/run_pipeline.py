import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print(f"\n➡️ Running: {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=ROOT, text=True)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

def main():
    py = sys.executable  # ensures it uses your .venv python

    run([py, "src/pull_demand_hourly.py"])
    run([py, "src/pull_caiso_lmp_dam_hourly.py"])
    run([py, "src/build_energy_signal.py"])
    run([py, "src/ingest_compute_telemetry.py"])
    run([py, "src/build_dispatch_signal.py"])

    print("\n✅ Pipeline complete.")

if __name__ == "__main__":
    main()