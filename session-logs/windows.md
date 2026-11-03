# Windows: how to submit logs

This file was rewritten on 16.08. It used to say that automatic export for
Windows does not exist and the path is manual only. That is no longer so: on August 12 a
build of the export tool for native Windows came out, and you follow the same path as
everyone else. If you read the earlier version and set yourself up to export every
session by hand, reread it, it got easier.

Honestly about how much is verified. The Claude Code mechanics — that sessions are written
to disk on their own, exactly where they are stored and how to bring up an old one — I checked on live
sessions and on the source code, this part is reliable. The Windows build of the export tool
I did not run, I do not have a Windows machine: it exists, I made sure of this
on the releases page, but you will be the first to run it. **If anything at all does not add up at any
step — write to me, we will sort it out together, and I will fix the instructions for everyone else.**

## Read this first, even if you read nothing further

Your conversation with the agent **does not go anywhere** when you close the IDE or the terminal.
Claude Code writes the transcript to disk continuously, throughout the session, not at the moment of exit.
The `/export` command does not save anything: it takes the file already on disk and
turns it into a readable form. So forgetting to export is impossible in principle,
everything is restored after the fact.

It is stored in `%USERPROFILE%\.claude\projects\`, in a separate folder for each project
and a separate `.jsonl` file for each session.

There is exactly one real risk, and it is about the time limit.

## Step 0. Stop the deletion timer. This is more important than everything else

By default Claude Code keeps transcripts for **thirty days** and then deletes them.
The course lasts longer than a month, so the logs of the first modules will physically not survive
until the end if you do nothing. Moreover, deletion happens **at the moment Claude Code
launches**, not on a calendar: the program starts, looks at what is older than the limit,
and cleans up. That is, the danger is not "sometime later", but your next launch.

Open the file `%USERPROFILE%\.claude\settings.json` in any editor and add
this line to it:

```json
{
  "cleanupPeriodDays": 3650
}
```

If the file already exists and has something in it, just add this pair to the existing
object, not forgetting the comma. If there is no file, create it with exactly this content.
You cannot set zero, the minimum value is one, so we take a deliberately large
number: ten years.

Do this **before the next launch** of Claude Code. Editing the file does not launch
anything by itself, so the order is safe.

## Step 1. Make sure the sessions are in place

Open PowerShell and look at what is in the storage:

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\projects" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

You should get a list of folders, one per project, the freshest on top. The folder name
is the path to your project with all characters other than letters and digits replaced
with a hyphen: `C:\Users\alex\proj` becomes `C--Users-alex-proj`. Inside are
`.jsonl` files, one per session.

Empty after real work means one of two things. Either you work inside WSL:
then `.claude` is inside the distribution, not in the Windows profile, and you need to look
from inside WSL with the command `ls ~/.claude/projects/`. These are two independent storages
on one machine, and you must restore from the environment you worked in. Or
something non-standard, and then write to me.

## Step 2. Install the export tool

Download the file `SpecStoryCLI_Windows_x86_64.zip` from the releases page (for ARM machines
`SpecStoryCLI_Windows_arm64.zip`):

<https://github.com/specstoryai/getspecstory/releases>

Unpack it, put `specstory.exe` in any permanent folder and add that folder to `PATH`.
Check:

```powershell
specstory version
```

On first launch Windows will show a warning that the application is unknown:
the build is not signed yet, this is expected and not a sign of a problem.

## Step 3. Turn off the tool's network

Right after installation, with one command in PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.specstory\cli" | Out-Null
@'
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
'@ | Set-Content -Encoding utf8 "$env:USERPROFILE\.specstory\cli\config.toml"
```

By default the tool checks for updates, sends anonymous analytics, and when you log in
to an account it syncs sessions to its cloud. The config turns off all of this at once.
Do not log in to an account and do not run `specstory login`. On a work laptop this is a
mandatory condition, not an option.

## Step 4. Export the sessions

From your repository folder:

```powershell
cd C:\path\to\your\repository
specstory sync claude
Get-ChildItem .specstory\history | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

Markdown files will appear in `.specstory\history\`, one per session. The command
works **after the fact**: it will lay out sessions you closed long ago too,
not only today's. The tool takes the sessions of this project only, the rest,
work ones included, it will not touch.

You need to run it from the root of each project separately, the command does not take all projects at once.

## Step 5. Fallback path, if you do not want to install anything

All the same can be obtained with Claude Code's standard tools, just one session
at a time. Go to the project folder and type:

```powershell
claude --resume
```

Choose the session you need from the list, and when it opens, type inside it:

```
/export session-2026-08-16.md
```

If Claude Code is already running, the list of sessions is opened by the `/resume` command right inside
a session, no need to exit.

Specify the file name in `/export` **explicitly**. Without a name the command offers an option via the
clipboard, and in the clipboard Cyrillic arrives unreadable on Windows: this is a known
and not yet closed problem. With an explicit file name it does not occur.

Put such files in the `ai-logs\` folder inside the repository, one session — one file.

## Step 6. Scrub the extras

The `sanitize-log.py` script sits in this same `session-logs` folder: download it and put it
in the root of your course repository, and commit it together with the project. Get Python
from python.org or from the Microsoft Store, during installation check "Add python to PATH",
check with `python --version`.

Then from the project root, first with `--dry-run`, to see what was found
without changing anything:

```powershell
python sanitize-log.py .specstory\history --names "Acme Ltd" "Smith" --dry-run
python sanitize-log.py .specstory\history --names "Acme Ltd" "Smith"
```

If you took the fallback path from the fifth step, substitute your `ai-logs` folder
for `.specstory\history`.

In `--names` list your own company names and surnames: proper names are not caught by a regular
expression. The tool's built-in redaction cuts secrets of known
formats, but misses email, phone numbers, surnames, addresses, database connection
strings and passwords that look like human words. And one more non-obvious thing:
the export **file name** is built from your first message to the agent, before any
redaction, so a secret or a client name from the prompt goes straight into the name.
The script closes both: it scrubs the content and renames the files
to a clean date-time.

It will put the originals next to them with the `.orig` suffix, you should not commit them.

Besides scrubbing, the script will build `context-report.md` next to them: a summary of how you
worked with the context window, how many turns in each session, the peak and final window fill,
manual and automatic compactions. The report has only numbers, not a line of conversation,
so it is safe under any NDA. For it to be built, run the script from the root of the
project the agent worked in.

## Step 7. Look with your own eyes

```powershell
Select-String -Path .specstory\history\* -Pattern "REDACTED|SECRET_ASSIGNMENT|API_KEY|EMAIL|PHONE" | Select-Object -First 10
```

Then open one file in full and scroll through it. Automation catches formats, but a client name
in free text only you will see. The log includes the contents of files
the agent read, that is, your code: **the repository must be private**.

## Step 8. Submit

```powershell
Add-Content .gitignore "*.orig"
git add .specstory/history .gitignore
git commit -m "session logs"
git push origin
```

Open the repository on GitHub and check that the folder is there, the files are readable
and there is nothing extra in them.

If you work with the agent more after submitting, repeat steps 4, 6 and 8: the export does not
update itself, and new files arrive unscrubbed until you run the script.

## If something does not add up

**In the VS Code extension panel, opening an old session shows "NO MODELS
AVAILABLE" and does not let you type anything.** This is an open bug of the extension, it shows up
on Windows when the model is connected through a third-party address rather than directly. The session
is intact. Bring it up **from the terminal** with the `claude --resume` command, from there
everything works.

**`/export` fails with an error about `EEXIST` and `mkdir`.** This happens when the project
folder is in OneDrive: it sets a "read-only" attribute on its folders, and the runtime
the Windows Claude Code binary is built on stumbles on it. Fixed with the
`attrib -R .` command in the project folder or by exporting to a folder outside OneDrive.

**`specstory sync claude` says there are no sessions.** Check that you are in the folder of the same
repository in which you worked with the agent, and that step 1 shows a non-empty storage.

**The session list in `claude --resume` is empty although the files are in place.** It is known that this
happens on network drives, on drives attached via `subst`, and on paths like
`\\server\folder`. In that case the session still opens by identifier:
take the `.jsonl` file name without the extension from step 1 and pass it with the command
`claude --resume <identifier>`.

**Files with strange long names in `.specstory\history\`** are normal
until you run the script from the sixth step, it will rename them.

**`python` says it cannot open the file `sanitize-log.py`.** Python is fine,
the script is not in the current folder. Download it from `session-logs` and put it in the root of your
repository, next to `.git`.

And once more: if anything at all does not add up at any step — write, and we will sort it out together.
