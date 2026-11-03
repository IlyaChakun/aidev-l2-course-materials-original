# OpenCode

Honest from the start: I do not have OpenCode installed, and I did not run this setup.
There is no automatic collector for it: the tool the rest of the cohort uses
does not support OpenCode. But OpenCode stores history in ordinary files, so the path is
manual: find, copy, scrub, commit.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then the commands below work with no path substitution.

## Step 1. Find where your sessions are stored

Run:

```bash
ls -lt ~/.local/share/opencode/ 2>/dev/null
find ~ -maxdepth 5 -type d -iname "*opencode*" 2>/dev/null | grep -v Trash | head
```

Look inside for a folder with sessions or history, usually `storage`, `sessions` or `history`
with one file per session. Do this **before you start the homework**: if
your build is arranged differently, better to find out in advance. If you found nothing, write to me with the output of both commands.

## Step 2. Check that history is being written

Work with the agent for five minutes in the study project folder and repeat the commands from the first
step, looking at the file modification time. A fresh timestamp means history is
being written and you have something to submit.

## Step 3. Copy what you need into the repository

```bash
cd path/to/your/repository
mkdir -p ai-logs
ls -lt <found-sessions-directory> | head -5
cp <found-sessions-directory>/<needed-files> ai-logs/
```

Copy only the sessions that relate to the homework. The shared directory also holds your working
conversations, and those should not go anywhere.

## Step 4. Scrub the extras

Mandatory: there is no built-in scrubbing with manual copying.

```bash
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith" --dry-run
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith"
```

First with `--dry-run`, to see what was found. In `--names` list your own company names
and surnames: proper names are not caught by a regular expression. The script puts the originals
next to them with the `.orig` suffix, you should not commit them.

The script will also try to build `context-report.md` next to them — a summary of
context window fill. For your agent's sessions the script has no such data yet, so
the absence of the report is normal, not an error. If in this same project you also worked
with Claude Code or Codex, the report will be built from their sessions.

The log includes the contents of files the agent read, that is, your code. The repository
must be private.

## Step 5. Submit and check

```bash
echo "*.orig" >> .gitignore
git add ai-logs .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub, make sure the folder is there and the files are readable, and take a last
look with your own eyes to see that nothing extra is left.

## If something does not add up

Write to me with the output of the commands from the first step. I do not have the tool, so these
instructions were assembled from the general principle, not from a run. We will sort it out together,
and I will fix them.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
