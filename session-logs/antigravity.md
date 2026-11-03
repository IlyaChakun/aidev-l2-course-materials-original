# Antigravity

First the main point: **automatic export works only for the console version of
Antigravity (`agy` in the terminal)**. If you work in the Antigravity IDE app,
the export tool will not see your sessions — this was checked on 05.08 on live IDE data:
it honestly looks for the CLI version's directory and does not find it. For the IDE go straight to the section
"Fallback path" at the bottom: manual export + script.

Next is the path for the CLI version. I did not run all of it: I do not use the agent myself.
The mechanism — export, redaction and scrubbing — I ran by hand on 05.08 on another agent.
You will be the first to check this setup; if something does not add up, write to me right away and I will fix it
for everyone else.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then all the commands below work as written,
with no path substitution. You will create the export tool's config with one command
from the "Turn off the network" step — no separate file is needed.

## Step 1. Install the export tool

```bash
brew tap specstoryai/tap
brew install specstory
specstory version
```

If `brew install` complains about Command Line Tools, take a ready-made binary:

```bash
curl -fsSL -o specstory.tar.gz \
  https://github.com/specstoryai/getspecstory/releases/download/v2.9.0/SpecStoryCLI_Darwin_arm64.tar.gz
tar -xzf specstory.tar.gz && chmod +x specstory
mkdir -p ~/.local/bin && mv specstory ~/.local/bin/
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
specstory version
```

The last lines put the binary in a permanent place and add it to PATH — after
this `specstory` is available from any terminal, as with a brew install.

For Intel replace `arm64` with `x86_64`, for Linux take `SpecStoryCLI_Linux_arm64.tar.gz`
or `SpecStoryCLI_Linux_x86_64.tar.gz` from the same release. For Windows take `SpecStoryCLI_Windows_x86_64.zip` (or `_arm64`) from the same release and then go to the neighboring file `windows.md`: the whole path is laid out there for Windows in full. If something does not work, write to me and we will sort it out together.

## Step 2. Turn off the tool's network

```bash
mkdir -p ~/.specstory/cli
cat > ~/.specstory/cli/config.toml <<'EOF'
# SpecStory config for the course: no network. Do not log in to an account, do not run specstory login.

[cloud_sync]
enabled = false

[analytics]
enabled = false

[version_check]
enabled = false

[telemetry]
prompts = false

[redaction]
enabled = true
EOF
```

By default the tool checks for updates on every launch and sends anonymous
analytics, and when you log in to an account it syncs sessions to its cloud. The config turns off
all of this at once: I checked, and with it there are no network calls at all. Do not log in to an account
and do not run `specstory login`.

## Step 3. Check before you start the homework

```bash
cd path/to/your/repository
specstory sync antigravity
ls -lt .specstory/history/ | head -5
```

Markdown files with dates should appear. If they did, you are ready to submit. If it is empty,
work with the agent for five minutes and repeat. If it is still empty, write to me, attaching the full output
of the `specstory sync antigravity` command.

The tool cuts secrets of known formats itself, and `[REDACTED:…]` will be in their place.
This is not enough, the next step is mandatory.

## Step 4. Scrub the extras

The built-in redaction catches secret formats but misses email, phone numbers, surnames,
addresses, database connection strings and passwords that look like human words. And one more thing:
the export **file name** is built from the first message of the session before any redaction,
so a secret or a client name from the prompt goes straight into the name. The attached script
scrubs the content and renames the files to a clean date-time.

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith" --dry-run
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith"
```

First with `--dry-run`, to see what was found without changing anything. In `--names`
list your own company names and surnames: proper names are not caught by a regular expression.
The script will put the originals next to them with the `.orig` suffix; you should not commit them.

The script will also try to build `context-report.md` next to them — a summary of
context window fill. For your agent's sessions the script has no such data yet, so
the absence of the report is normal, not an error. If in this same project you also worked
with Claude Code or Codex, the report will be built from their sessions.

Self-check before the first submission: put a known string in the prompt to the agent,
`TEST_EMAIL = "a@b.co"`, go through steps 3 and 4 and make sure the export has `[EMAIL]`.
If the string itself is there, the script did not work, write to me.

## Step 5. Look with your own eyes and submit

```bash
grep -rn "REDACTED\|SECRET_ASSIGNMENT\|API_KEY\|EMAIL\|PHONE" .specstory/history | head
```

Then open one file in full and scroll through it: automation catches formats, but a client name
in free text only you will see. The export includes the contents of files the
agent read, that is, your code. The repository must be private.

Then an ordinary commit, for you these are just files:

```bash
echo "*.orig" >> .gitignore
git add .specstory/history .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub and check that the `.specstory/history` folder is there and the files
are readable. If you work with the agent more after submitting, repeat steps 3, 4 and the submission.

## Fallback path: Antigravity IDE and everything that did not work

For the Antigravity IDE app this is the main path, not a fallback: export the conversation
with the agent from the interface by hand, save it to a `.md` file inside the homework folder
(for example `ai-logs/session-2026-08-05.md`), run it through `sanitize-log.py`
and commit. This is no worse than the automatic export, just slower.

If you followed the CLI path and something did not work — write to me what exactly, and I will fix
the instructions for everyone else.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
