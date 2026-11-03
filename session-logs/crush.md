# crush

Honest from the start: I do not have crush installed, and I did not run this setup. None
of the collectors I checked supports it. But crush stores session history
locally in ordinary files, and that is enough.

## Step 1. Find where your sessions are stored

Do this **before you start the homework**, not after.

```bash
ls -lt ~/.local/share/crush/ 2>/dev/null
ls -lt ~/.config/crush/ 2>/dev/null
find ~ -maxdepth 5 -type d -iname "*crush*" 2>/dev/null | grep -v Trash | head
```

Look inside for a database or a folder with sessions: crush history usually sits either in a single database
file for everything, or in a folder with sessions per project. If there is a local
`.crush` folder inside the project, look in it too:

```bash
cd path/to/your/repository && ls -la .crush 2>/dev/null
```

If nothing is found, write to me with the output of all the commands and we will sort it out.

## Step 2. Check that history is being written at all

Work with the agent for five minutes in the study project folder and repeat the commands from the first step,
looking at the file modification time. A fresh timestamp means history is being written
and you have something to submit. That is the check before the homework.

## Step 3. Copy what you need into the repository

```bash
cd path/to/your/repository
mkdir -p ai-logs
cp <found-session-files> ai-logs/
```

Copy only what relates to the homework. The shared directory also holds your working
conversations, and those should not go anywhere.

If crush keeps history in one shared database for all projects, do not copy the whole database.
Instead export the needed session through crush's own interface, if it can do that,
or copy the conversation manually into the file `ai-logs/session-date.md`. A shared database for all
projects must not end up in the course repository.

## Step 4. Scrub the extras

Mandatory, there is no built-in scrubbing here:

```bash
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith" --dry-run
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith"
```

First with `--dry-run`, to see what was found without changing anything. In `--names`
list your own company names, surnames and internal systems: proper names are not caught by a regular
expression. The script will put the originals next to them with the `.orig` suffix; you should not commit
them.

The script will also try to build `context-report.md` next to them — a summary of
context window fill. For your agent's sessions the script has no such data yet, so
the absence of the report is normal, not an error. If in this same project you also worked
with Claude Code or Codex, the report will be built from their sessions.

Then open one file and scroll through it with your own eyes. The history includes the contents of files the
agent read, that is, your code. The repository must be private.

## Step 5. Submit and check

```bash
echo "*.orig" >> .gitignore
git add ai-logs .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub, make sure the folder is there and the files are readable, and take a last
look to see that nothing extra is left.

## If something does not add up

Write to me with the output of the commands from the first step. I do not have the tool, so these instructions
were assembled from the general principle, not from a run. We will sort it out together, and I will fix them
for everyone else.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
