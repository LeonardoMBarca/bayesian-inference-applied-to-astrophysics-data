"""Build/check the current TCC evidence in the campaign's locked WSL environment."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def launch():
    runtime = json.loads((ROOT / "configs/publication/tcc_numerical_complement_v4.json").read_text())["runtime"]
    interpreter = runtime["scientific_python"]
    if os.name == "nt":
        raise SystemExit(subprocess.call(["wsl.exe", "--cd", str(ROOT), "-d", runtime["wsl_distribution"],
                                          "--", interpreter, "scripts/close_tcc_evidence.py", *sys.argv[1:]], cwd=ROOT))
    if Path(sys.executable).resolve() != Path(interpreter).resolve():
        os.execv(interpreter, [interpreter, str(Path(__file__).resolve()), *sys.argv[1:]])
    from publication.tcc_closure import main
    main()


if __name__ == "__main__":
    launch()
