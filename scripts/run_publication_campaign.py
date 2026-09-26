"""Run, resume, stop or audit a predeclared publication campaign."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.campaign import main  # noqa: E402


def launch():
    """Use the configured locked Linux environment from Windows or Linux Play."""
    root = Path(__file__).resolve().parents[1]
    arguments = sys.argv[1:]
    config = "configs/publication/tcc_final_campaign.json"
    if "--config" in arguments:
        config = arguments[arguments.index("--config") + 1]
    runtime = json.loads((root / config).read_text(encoding="utf-8")).get("runtime", {})
    interpreter = runtime.get("scientific_python", "/home/leonardo_barca/mc3/bin/python3.14")
    if os.name == "nt":
        command = ["wsl.exe", "--cd", str(root), "-d", runtime.get("wsl_distribution", "Ubuntu-24.04"),
                   "--", interpreter, "scripts/run_publication_campaign.py", *arguments]
        raise SystemExit(subprocess.call(command, cwd=root))
    if runtime.get("scientific_python") and Path(sys.executable).resolve() != Path(interpreter).resolve():
        os.execv(interpreter, [interpreter, str(Path(__file__).resolve()), *arguments])
    main()


if __name__ == "__main__":
    launch()
