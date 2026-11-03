# VS Code plus Codex

I ran the export and scrubbing mechanics by hand on 05.08 on Claude Code; for Codex the tool
works the same way, and I separately checked that it does not pick up other projects' sessions from the shared directory.
That the VS Code extension writes to the same directory as the console Codex is visible
right in the session files: they record the surface the session was launched from.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then all the commands below work as written,
with no path substitution. You will create the export tool's config with one command
from the "Turn off the network" step — no separate file is needed.

## Where your logs are written

Into your home directory, into `~/.codex/sessions/YEAR/MONTH/DAY/rollout-*.jsonl`, one file
per session, laid out by date. The console Codex and the VS Code extension write to the same place.

## Step 1. Check before you start the homework

```bash
ls -lt ~/.codex/sessions/$(date +%Y/%m/%d)/ | head -5
```

There should be files for today. If you have not worked with the agent today yet, look at the general list:

```bash
ls -lt ~/.codex/sessions/*/*/*/ | head -5
```

Empty after real work with the agent means you have a non-standard build,
write to me.

## Step 2. Install the export tool

Once, before you start the homework. The tool is called SpecStory.

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

For Intel replace `arm64` with `x86_64`, for Linux take the Linux archive from the same release.
For Windows take `SpecStoryCLI_Windows_x86_64.zip` (or `_arm64`) from the same release and then go to the neighboring file `windows.md`: the whole path is laid out there for Windows in full. If something does not work, write to me and we will sort it out together.

## Step 3. Turn off the tool's network

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

By default the tool checks for updates and sends anonymous analytics, and when you
log in to an account it syncs sessions to the cloud. The config turns off all of this at once,
I checked: with it there are no network calls. Do not log in to an account, do not run `specstory login`.

## Step 4. Export the sessions

```bash
cd path/to/your/repository
specstory sync codex
ls -lt .specstory/history/ | head -5
```

Markdown files will appear in `.specstory/history/`. The tool takes only the sessions of this
project: I checked on a machine with hundreds of work rollouts alongside — in another project it
finds nothing and asks you to open Codex right here.

It cuts secrets of known formats itself, and `[REDACTED:…]` will be in their place.
This is not enough, the next step is mandatory.

## Step 5. Scrub the extras

The built-in redaction catches secret formats but misses email, phone numbers, surnames,
addresses, database connection strings and passwords that look like human words. And one more thing:
the export **file name** is built from the first message of the session before any redaction.
The attached script scrubs the content and renames the files to a clean date-time.

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith" --dry-run
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith"
```

First with `--dry-run`, to see what was found. In `--names` list your own company names
and surnames: proper names are not caught by a regular expression. The script will put the originals
next to them with the `.orig` suffix, you should not commit them.

Besides scrubbing, the script will build `context-report.md` next to them — a summary of how you worked
with the context window: how many turns in each session, the peak and final window fill
in tokens and percent, manual and automatic compactions. The report has only numbers,
not a line of conversation, and it goes into the commit together with the logs. For it to be built,
run the script from the root of the project the agent worked in.

Self-check before the first submission: put a known string in the prompt to the agent,
`TEST_EMAIL = "a@b.co"`, go through steps 4 and 5 and make sure the export has
`[EMAIL]` in its place. If the string itself is there, the script did not work, write to me.

## Step 6. Look with your own eyes

```bash
grep -rn "REDACTED\|SECRET_ASSIGNMENT\|API_KEY\|EMAIL\|PHONE" .specstory/history | head
```

Then open one file and scroll through it. The log includes the contents of files the agent read,
that is, your code. The repository must be private.

An honest limitation of Codex: the log contains the conversation, but not every agent step — the log
shows what you asked and what the agent answered, but not all of its actions.

## Step 7. Submit

```bash
echo "*.orig" >> .gitignore
git add .specstory/history .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub, check that the `.specstory/history` folder is there and the files
are readable, and take a last look to see that nothing extra is left.

If you work with the agent more after submitting, repeat steps 4, 5 and 7: new files
arrive unscrubbed until you run the script.

## If something does not add up

`specstory sync codex` says "no sessions" and advises opening Codex in this project.
It means you have not yet worked with Codex in this particular repository: sessions are tied
to the working folder.

Files with strange long names in `.specstory/history/` are normal until you run the
script from the fifth step, it will rename them.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
