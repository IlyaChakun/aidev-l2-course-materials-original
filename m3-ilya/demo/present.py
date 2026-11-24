"""Step-by-step demo runner: shows the next command, waits for Enter, runs it.

    python3 present.py 01-bare-loop/steps.txt

Enter runs the shown command, s skips it, q quits. A steps file holds blocks separated by blank
lines: lines starting with "# " are the note shown above the command, the other line is the command.
Header lines: "@cwd PATH" sets the working directory, "@env FILE" loads KEY=VALUE lines.
$PY and $STS are set when missing: the Smart-Technical-Support checkout next to this repository
and the Python of its agent_v2 venv.
"""
import os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("STS", str(HERE.parents[2] / "Smart-Technical-Support"))
os.environ.setdefault("PY", os.path.join(os.environ["STS"], "agent_v2/.venv/bin/python"))
DIM, BOLD, CYAN, OFF = "\033[2m", "\033[1m", "\033[36m", "\033[0m"


def blocks(path: Path):
    cwd, notes = path.parent, []
    for line in path.read_text().splitlines() + [""]:
        if line.startswith("@cwd "):
            cwd = Path(os.path.expandvars(line[5:].strip())).expanduser()
        elif line.startswith("@env "):
            env_file = Path(os.path.expandvars(line[5:].strip())).expanduser()
            if not env_file.is_absolute():
                env_file = path.parent / env_file
            for kv in env_file.read_text().splitlines():
                k, _, v = kv.partition("=")
                if k.strip() and not k.startswith("#"):
                    os.environ[k.strip()] = v.strip()
        elif line.startswith("# "):
            notes.append(line[2:])
        elif line.strip():
            yield cwd, notes, line
            notes = []


def main(path: str):
    steps = list(blocks(Path(path).resolve()))
    for i, (cwd, notes, cmd) in enumerate(steps, 1):
        for note in notes:
            print(f"{DIM}{note}{OFF}")
        print(f"{CYAN}[{i}/{len(steps)}]{OFF} {BOLD}$ {cmd}{OFF}", end="  ")
        key = input(f"{DIM}Enter = run, s = skip, q = quit{OFF} ").strip().lower()
        if key == "q":
            break
        if key == "s":
            continue
        subprocess.run(cmd, shell=True, cwd=cwd)
        print()


if __name__ == "__main__":
    main(sys.argv[1])
