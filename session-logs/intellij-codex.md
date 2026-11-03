# IntelliJ IDEA (or another JetBrains IDE) plus Codex

Your setup is the only one where nothing is collected by default. Read the first section
to the end, it is short and settles everything.

I ran the export and scrubbing mechanics by hand on 05.08. The JetBrains setup itself I checked
against the official JetBrains knowledge base and their issue tracker, because a live check
requires logging in to an account inside the IDE. If something does not add up for you, write to me right away.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then all the commands below work as written,
with no path substitution. You will create the export tool's config with one command
from the "Turn off the network" step — no separate file is needed.

## What is special about your setup

Codex inside JetBrains is not the same Codex as in the terminal. The plugin keeps **its own**
authorization, config and sessions in a separate IDE service directory, not in the shared `~/.codex`.
It cannot be switched with a standard setting, the vendor has this capability only
in feature requests so far. The practical consequence: the export tool looks in the shared directory
and will find nothing on your machine even though you worked.

Fixed by one of two solutions, pick either.

**First, the simple one.** Run `codex` from the IDE's built-in terminal, not from the plugin panel.
Then it behaves like an ordinary console Codex, writes to the shared directory, and from there everything is
the same as for everyone else. You keep working in IDEA as usual, the only thing that changes is where the agent
starts from. I recommend this path.

**Second.** Keep the plugin panel, but launch the IDE with the environment variable
`CODEX_HOME=~/.codex`, and then the plugin will use the shared directory. This works, but requires
launching the IDE in a special way, and it is easy to forget.

## Step 1. Check before you start the homework

Look at where your sessions are stored at all. Run both commands, one of them will show something:

```bash
ls -lt ~/.codex/sessions/*/*/*/ | head -5
ls -d ~/Library/Caches/JetBrains/*/aia/codex/sessions 2>/dev/null
```

On Linux the second command looks like this:

```bash
ls -d ~/.cache/JetBrains/*/aia/codex/sessions 2>/dev/null
```

If files were found at the first path, you are already working through the shared directory, nothing needs
changing. If the first is empty and the directory was found at the second, it means you are working through
the plugin panel, and you need to apply one of the two solutions above.

After applying it, work with the agent for five minutes and repeat the first command.
Files should appear. Do not skip this check: it takes a minute and separates
the situation "everything is set up" from the situation "I submitted nothing".

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
project, it will not touch the work ones. If it says "no sessions", go back to the first step:
almost certainly the sessions are still going to the plugin directory, not the shared one.

It cuts secrets of known formats itself (`[REDACTED:…]` in their place), but this is
not enough, the next step is mandatory.

## Step 5. Scrub the extras

The built-in redaction misses email, phone numbers, surnames, addresses, connection strings
and passwords that look like human words. And one more thing: the export **file name** is built
from the first message of the session before any redaction. The attached script scrubs the content
and renames the files to a clean date-time.

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith" --dry-run
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith"
```

First with `--dry-run`, to see what was found. In `--names` list your own company names,
surnames and internal systems. The script will put the originals next to them with the `.orig` suffix,
you should not commit them.

Besides scrubbing, the script will build `context-report.md` next to them — a summary of how you worked
with the context window: how many turns in each session, the peak and final window fill
in tokens and percent, manual and automatic compactions. The report has only numbers,
not a line of conversation, and it goes into the commit together with the logs. For it to be built,
run the script from the root of the project the agent worked in.

Self-check before the first submission: put a known string in the prompt to the agent,
`TEST_EMAIL = "a@b.co"`, go through steps 4 and 5 and make sure the export has `[EMAIL]`.

## Step 6. Look with your own eyes and submit

```bash
grep -rn "REDACTED\|SECRET_ASSIGNMENT\|API_KEY\|EMAIL\|PHONE" .specstory/history | head
```

Then open one file and scroll through it. The log includes the contents of files the agent read,
that is, your code. The repository must be private.

An honest limitation of Codex: the log contains the conversation, but not every agent step.

```bash
echo "*.orig" >> .gitignore
git add .specstory/history .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub, check that the folder is there and the files are readable. If you work
with the agent more after submitting, repeat steps 4, 5 and the submission.

## If something does not add up

This is a setup I could not run in full on my machine. If after the first step
you found neither of the two directories, or found the second one, and after switching
to the built-in terminal sessions still do not appear, write to me right away and attach the output of
both commands from the first step. We will sort it out together, and I will fix these instructions for everyone else.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
