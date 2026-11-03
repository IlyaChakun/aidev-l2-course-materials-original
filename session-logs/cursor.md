# Cursor with the built-in agent

Collection was checked by hand on real Cursor sessions, scrubbing and redaction on planted
secrets on 05.08. Your case differs from the others the most, so read
carefully: you are the only one whose logs are not in files.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then all the commands below work as written,
with no path substitution. You will create the export tool's config with one command
from the "Turn off the network" step — no separate file is needed.

## Where your logs are written

Not into files. Cursor keeps the conversation with the agent in an internal database inside its support
directory, as separate records for every dialog and every message. This is not text you
can simply copy, so ordinary log collectors built for session files
find nothing on your machine and create a false impression that there are no logs.

The SpecStory tool reads this database and unpacks it into ordinary markdown. I checked it
on my own Cursor sessions: it found and parsed them correctly, tool calls
included.

Separately: if you use not the panel inside Cursor but the console `cursor-agent`,
everything is written to files, and that is supported by the same tool, only in the export
command write `cursor` instead of `cursoride`.

## Step 1. Install the export tool

Once, before you start work on the homework.

```bash
brew tap specstoryai/tap
brew install specstory
specstory version
```

If `brew install` complains about Command Line Tools, which happens on fresh macOS,
take a ready-made binary:

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

For an Intel processor replace `arm64` with `x86_64` in the file name, for Linux take
`SpecStoryCLI_Linux_arm64.tar.gz` or `SpecStoryCLI_Linux_x86_64.tar.gz` from the same
release. For Windows take `SpecStoryCLI_Windows_x86_64.zip` (or `_arm64`) from the same release and then go to the neighboring file `windows.md`: the whole path is laid out there for Windows in full. If something does not work, write to me and we will sort it out together.

## Step 2. Turn off the tool's network

Right after installation put the attached config in place:

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
and do not run `specstory login`: your sessions must not go anywhere except your
own repository.

## Step 3. Check before you start the homework

Go to your project folder and run:

```bash
cd path/to/your/repository
specstory sync cursoride
ls -lt .specstory/history/ | head -5
```

Markdown files should appear. If they did, everything is fine and you are ready to submit.
If the folder is empty, it means you have not yet worked with the Cursor agent in this project: work
for five minutes and repeat.

The tool cuts secrets of known formats (API keys, tokens) itself, and `[REDACTED:…]`
will be in their place. This is not enough, so the next step is mandatory.

## Step 4. Scrub the extras

The built-in redaction catches secret formats but misses email, phone numbers, surnames,
addresses, database connection strings and passwords that look like human words. And one more
non-obvious thing: the export **file name** is built from your first message to the agent,
before any redaction, so a secret or a client name from the prompt goes straight into the name.
The attached script closes both: it scrubs the content and renames the files
to a clean date-time.

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith" --dry-run
```

First with `--dry-run`, to see what it found without changing anything. In `--names`
list your own company names and surnames: proper names are not caught by a regular expression,
this is the one thing that cannot be closed automatically. Once you are sure the list is reasonable,
run it without `--dry-run`:

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith"
```

The script will rewrite the files and put the originals next to them with the `.orig` suffix. You should not
commit the originals, add the line `*.orig` to `.gitignore`.

The script will also try to build `context-report.md` next to them — a summary of
context window fill. For your agent's sessions the script has no such data yet, so
the absence of the report is normal, not an error. If in this same project you also worked
with Claude Code or Codex, the report will be built from their sessions.

Self-check before the first submission: put a known string in the prompt to the agent,
`TEST_EMAIL = "a@b.co"`, go through steps 3 and 4 and make sure the export has
`[EMAIL]` in its place. If the string itself is there, it means the script did not work, write to me.

## Step 5. Look with your own eyes

```bash
grep -rn "REDACTED\|SECRET_ASSIGNMENT\|API_KEY\|EMAIL\|PHONE" .specstory/history | head
```

This way you will see exactly what was replaced. Then open one file in full and scroll through it with your own eyes:
the automatic check catches formats, but a client name or surname in free text
only you will see. Remember that the export includes the contents of files the agent read,
that is, your code. The repository must be private.

## Step 6. Submit

For you it is simple: these are ordinary files, and they go with an ordinary commit.

```bash
echo "*.orig" >> .gitignore
git add .specstory/history .gitignore
git commit -m "session logs"
git push origin
```

Open your repository on GitHub and check that the `.specstory/history` folder is there
and the files in it are readable. While at it, take a last look to see that nothing extra is left in them:
after publishing it is harder to fix.

If you work with the agent more after submitting, repeat steps 3, 4 and 6: the export does not
update itself, and new files arrive unscrubbed until you run the script.

## If something does not add up

The command ran but there are no files. Check that you are in the folder of the project that is open
in Cursor: the tool ties sessions to the working folder, and from another folder it will not see your
dialogs.

There turned out to be very many files, including old dialogs. Leave in the commit only those
that relate to the homework, delete the rest from the folder before committing.

Files with strange long names are normal until you run the script from the fourth
step, it will rename them.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
