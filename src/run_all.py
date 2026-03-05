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
    py = sys.executable
    run([py, "src/run_pipeline.py"])
    run([py, "src/viz_report.py"])
    print("\n✅ Pipeline + visuals complete.")

if __name__ == "__main__":
    main()