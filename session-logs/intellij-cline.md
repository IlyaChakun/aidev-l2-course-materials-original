# IntelliJ IDEA (or another JetBrains IDE) plus Cline

Honest from the start: I do not have this setup, and I did not run it. None of the collectors
I checked supports Cline. But Cline, unlike many, stores its
tasks in ordinary files on disk, and that settles the question.

## Step 1. Find where your tasks are stored

Cline puts each task in a separate folder with the message history. Run:

```bash
find ~ -maxdepth 6 -type d \( -name "tasks" -path "*cline*" -o -name "tasks" -path "*claude-dev*" \) 2>/dev/null | head
```

If nothing was found, search wider:

```bash
find ~ -maxdepth 6 -type d -iname "*cline*" 2>/dev/null | grep -v Trash | head
```

Inside the folder you found there should be numbered subfolders and files like
`api_conversation_history.json` and `ui_messages.json`. These are your logs.

Do this check **before you start the homework**, not after: if it turns out that
your build is arranged differently, better to find out in advance. If you found nothing,
write to me, attaching the output of both commands.

## Step 2. Create a folder for logs in the homework repository

```bash
cd path/to/your/repository
mkdir -p ai-logs
```

## Step 3. After the work, copy the needed tasks

Tasks are listed by modification time, so the fresh ones are visible right away:

```bash
ls -lt <found-path-to-tasks> | head -5
```

Copy into the repository the task folders that relate to the homework:

```bash
cp -r <found-path-to-tasks>/<task-number> ai-logs/
```

Copy specifically the homework tasks, not everything: the shared folder also holds your working
tasks, and we do not need them and they should not go anywhere.

## Step 4. Scrub the extras

Mandatory, there is no built-in scrubbing here at all, the files lie as they are:

```bash
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith" --dry-run
```

First with `--dry-run`, to see what was found without changing anything. In `--names`
list your own company names, surnames and internal systems: proper names are not caught by a regular
expression. Then run without the flag:

```bash
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith"
```

The script will rewrite the files and put the originals next to them with the `.orig` suffix. You should not
commit the originals.

The script will also try to build `context-report.md` next to them — a summary of
context window fill. For your agent's sessions the script has no such data yet, so
the absence of the report is normal, not an error. If in this same project you also worked
with Claude Code or Codex, the report will be built from their sessions.

Separately, look at at least one file with your own eyes. Cline's history includes the contents of files
the agent read, that is, your code, and since this is a work machine, there may be
something extra in it. The repository must be private.

## Step 5. Submit

```bash
echo "*.orig" >> .gitignore
git add ai-logs .gitignore
git commit -m "session logs"
git push origin
```

## Step 6. Make sure it arrived

Open the repository on GitHub and check that the `ai-logs` folder is there and the files in it
are readable. While at it, take a last look to see that nothing extra is left: after publishing
it is harder to fix.

## If something does not add up

These instructions were assembled from how the tool is built, not from my run. If the tasks
folder was not found, or what is inside is not what is described, write to me and attach the output of the
commands from the first step. We will sort it out together, and I will fix it for everyone else.

A fallback path that always works: copy the conversation from the Cline panel by hand,
save it to `ai-logs/session-date.md`, run it through the script and commit.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
