# VS Code plus Claude Code

I ran collection, scrubbing and submission by hand on 05.08 on real Claude Code session files,
including a check of the redaction on planted secrets. The separate question of whether the VS Code
extension writes to disk at all was closed back on 02.08: it does.

You need one file — the `sanitize-log.py` script. It sits in this same `session-logs`
folder: download it and put it in the root of your course repository,
and commit it together with the project. Then all the commands below work as written,
with no path substitution. You will create the export tool's config with one command
from the "Turn off the network" step — no separate file is needed.

## Where your logs are written

The vendor documentation contradicts itself on this: one page says the extension
and the terminal CLI share one history, another says the panel has its own. I took the
extension apart and checked: inside it is the very same CLI binary of the same version, the extension
simply launches it. So there is one history, and sessions from the panel land in the same place as
from the terminal: `~/.claude/projects/<your-project-path>/`, one `.jsonl` file per session.

## Step 1. Check before you start the homework

Open the terminal inside VS Code, go to the project folder and run:

```bash
ls -lt ~/.claude/projects/$(pwd | sed 's/[^A-Za-z0-9]/-/g')/*.jsonl | head -3
```

You should get a list of files, the freshest on top. If the project is new, work
with the agent for five minutes and repeat. Empty after real work means you have
something non-standard, write to me.

The form of the command matters: it replaces with a hyphen every character other than letters and digits, not only
slashes. Simpler variants on paths with spaces show an empty result even though sessions exist.

## Step 2. Install the export tool

Once, before you start the homework. The tool is called SpecStory, it unpacks sessions
into ordinary markdown files.

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

## Step 3. Turn off the tool's network

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
and do not run `specstory login`.

## Step 4. Export the sessions

Before submitting the homework run this in the project folder:

```bash
cd path/to/your/repository
specstory sync claude
ls -lt .specstory/history/ | head -5
```

Markdown files will appear in `.specstory/history/`, one per session. The tool takes
only the sessions of this project: it will not touch your others, work ones included, I checked this
on a live machine with hundreds of other sessions alongside.

It cuts secrets of known formats itself, and `[REDACTED:…]` will be in their place.
But this is not enough, so the next step is mandatory.

Now about the time limit, and this is worth doing once right now. Claude Code keeps
transcripts for **thirty days** and then deletes them itself. The course lasts longer than a month,
so the logs of the first modules will not survive until the end if you do nothing. Moreover,
deletion happens **at the moment Claude Code launches**, not on a calendar: the program
starts, looks at what is older than the limit, and cleans up. The danger is not "sometime later",
but your next launch.

Fixed with one line. Open `~/.claude/settings.json` and add this there:

```json
{
  "cleanupPeriodDays": 3650
}
```

If the file already exists and is not empty, add this pair to the existing object. You cannot set zero,
the minimum value is one, so we take a deliberately large number. After
this you can export calmly, not in the same weekend.

And one more thing that removes needless worry: **you cannot forget to export a session**. The raw
files are written to disk continuously, throughout the session, not at the moment of exit, and
`specstory sync claude` parses them after the fact, long-closed ones included. A closed
IDE, a reboot or a forgotten export lose nothing.

## Step 5. Scrub the extras

The built-in redaction catches secret formats but misses email, phone numbers, surnames,
addresses, database connection strings and passwords that look like human words. And one more
non-obvious thing: the export **file name** is built from your first message to the agent,
before any redaction, so a secret or a client name from the prompt goes straight into the name.
The attached script closes both: it scrubs the content and renames the files
to a clean date-time.

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith" --dry-run
```

First with `--dry-run`, to see what was found without changing anything. In `--names`
list your own company names and surnames: proper names are not caught by a regular expression.
Then without the flag:

```bash
python3 sanitize-log.py .specstory/history --names "Acme Ltd" "Smith"
```

The script will put the originals next to them with the `.orig` suffix, you should not commit them.

Besides scrubbing, the script will build `context-report.md` next to them — a summary of how you worked
with the context window: how many turns in each session, the peak and final window fill
in tokens and percent, manual and automatic compactions. The report has only numbers,
not a line of conversation, and it goes into the commit together with the logs. For it to be built,
run the script from the root of the project the agent worked in.

Self-check before the first submission: put a known string in the prompt to the agent,
`TEST_EMAIL = "a@b.co"`, go through steps 4 and 5 and make sure the export has
`[EMAIL]` in its place. If the string itself is there, it means the script did not work, write to me.

## Step 6. Look with your own eyes

```bash
grep -rn "REDACTED\|SECRET_ASSIGNMENT\|API_KEY\|EMAIL\|PHONE" .specstory/history | head
```

Then open one file in full and scroll through it: automation catches formats, but a client name
in free text only you will see. The log includes the contents of files the agent
read, that is, your code. The repository must be private.

## Step 7. Submit

```bash
echo "*.orig" >> .gitignore
git add .specstory/history .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub and check that the `.specstory/history` folder is there and the files
are readable. While at it, take a last look to see that nothing extra is left.

If you work with the agent more after submitting, repeat steps 4, 5 and 7: the export does not
update itself, and new files arrive unscrubbed until you run the script.

## If something does not add up

The check from the first step is empty although you worked in the panel. Open the built-in terminal
of VS Code, launch the agent with the `claude` command from there and repeat the check. If it is still empty,
write to me.

`specstory sync claude` says there are no sessions. Check that you are in the folder of the same
repository in which you worked with the agent.

Files with strange long names in `.specstory/history/` are normal until you run the
script from the fifth step, it will rename them.

`python3` says can't open file 'sanitize-log.py'. Python is fine — the script is not
in the current folder. Go back to the start of the file: download `sanitize-log.py` from `session-logs`
and put it in the root of your repository, next to `.git`, then repeat the command.
