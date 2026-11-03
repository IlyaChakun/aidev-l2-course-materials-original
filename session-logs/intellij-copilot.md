# IntelliJ IDEA (or another JetBrains IDE) plus GitHub Copilot

Honest from the start: I do not have this setup, and I did not run it. The Copilot plugin inside
JetBrains does not put chat history in ordinary files, and there is currently no automatic collector for
it: the tool the rest of the cohort uses is only developing Copilot support. As soon as
it comes out and I check it, I will send an update to these instructions.
For now there is one path — manual, and it works, it just requires discipline.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then the commands below work with no path substitution.

## Step 1. Create a folder for logs

```bash
cd path/to/your/repository
mkdir -p ai-logs
```

Do this in advance so you do not gather everything on the last evening.

## Step 2. After each notable session, save the conversation

Finished work on a task — select the conversation with the agent in the panel, copy it and save it
to a file inside the homework folder, for example `ai-logs/session-2026-08-05.md`. One session — one
file, with the date in the name.

Copy the conversation for the homework, not everything: working dialogs should not go anywhere.

## Step 3. Scrub the extras

Mandatory: with manual copying there is no built-in scrubbing at all.

```bash
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith" --dry-run
python3 sanitize-log.py ai-logs --names "Acme Ltd" "Smith"
```

First with `--dry-run`, to see what was found without changing anything. In `--names` list
your own company names and surnames: the name of your company, colleagues, internal systems. Proper names
are not caught by a regular expression, this is the one thing that cannot be closed automatically.
The script puts the originals next to them with the `.orig` suffix, you should not commit them.

The script will also try to build `context-report.md` next to them — a summary of
context window fill. For your agent's sessions the script has no such data yet, so
the absence of the report is normal, not an error. If in this same project you also worked
with Claude Code or Codex, the report will be built from their sessions.

Then open one file and scroll through it with your own eyes: automation catches formats, but a client name
in free text only you will see. The conversation includes the contents of files the
agent read, that is, your code. The repository must be private.

## Step 4. Submit

```bash
echo "*.orig" >> .gitignore
git add ai-logs .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub and check that the `ai-logs` folder is there and the files are readable.
While at it, take a last look to see that nothing extra is left: after publishing it is harder
to fix.

## If something does not add up

I cannot check this setup on my machine. If something goes differently for you — the panel
does not let you select the whole conversation, history is written somewhere in files, anything — write to
me, we will sort it out together, and I will fix the instructions for everyone else.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
