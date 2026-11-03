# Agent work logs: find your setup

Logs are submitted voluntarily and do not affect your grade. They give me an extra review:
the finished code does not show how you framed the task, where you stopped the agent and what
you decided to check by hand, but the session log does.

Find your setup in the table and open your file. It has everything for you alone: what to check
before you start, what to install, what to configure, how to make sure anything extra is scrubbed,
and how to submit. The files do not refer to each other, so you only need to read one.

If you use two tools, take the file for the one you write code with the agent in
more often. If you did not find your setup, write to me and I will add it.


| Your environment                                  | Agent                   | How it is collected                                                                                                                                                                                                    | Verification                                                                                            | File                                               |
| ------------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| IntelliJ IDEA, WebStorm, PyCharm, any JetBrains   | Claude Code             | automatic: `specstory sync claude` — the plugin writes to the same place as the CLI                                                                                                                                  | verified: run by hand end to end, 05.08                                                                        | [intellij-claude-code.md](intellij-claude-code.md) |
| IntelliJ IDEA, WebStorm, PyCharm, any JetBrains   | Codex                   | automatic, but first move the sessions to the shared directory: the JetBrains plugin writes to an IDE service directory that the export does not see. Fixed by running `codex` from the built-in terminal         | partial: the export itself was run; the plugin quirk is from JetBrains documentation, not from a run                 | [intellij-codex.md](intellij-codex.md)             |
| IntelliJ IDEA, WebStorm, PyCharm, any JetBrains   | GitHub Copilot          | no automatic export — manual export from the panel + scrub script                                                                                                                                                    | not verified: I do not have this setup, the path is generic                                                                         | [intellij-copilot.md](intellij-copilot.md)         |
| IntelliJ IDEA, WebStorm, PyCharm, any JetBrains   | Cline                   | no automatic export — Cline tasks are stored as files, copy + script                                                                                                                                                 | partial: the file locations are from documentation, not from a run                                                   | [intellij-cline.md](intellij-cline.md)             |
| VS Code                                           | Claude Code             | automatic: `specstory sync claude` — the extension writes to the same place as the CLI                                                                                                                               | verified: run by hand end to end, 05.08                                                                        | [vscode-claude-code.md](vscode-claude-code.md)     |
| VS Code                                           | Codex                   | automatic: `specstory sync codex`                                                                                                                                                                                    | partial: the mechanics were run on another agent; that the extension writes to the shared directory is visible from the session files | [vscode-codex.md](vscode-codex.md)                 |
| Cursor                                            | built-in Cursor agent   | automatic: `specstory sync cursoride`. Caveat: Cursor keeps chats not in files but in an internal SQLite database — our tool is the only one that reads it; all other collectors will show "no sessions" while the history is alive | verified: collection was run on real Cursor sessions 02.08, redaction and scrubbing 05.08                             | [cursor.md](cursor.md)                             |
| Antigravity **CLI** (`agy` in the terminal)       | built-in agent          | automatic: `specstory sync antigravity` — reads only CLI sessions                                                                                                                                                  | partial: the mode is claimed by the vendor, not run — you will be the first to check it                                         | [antigravity.md](antigravity.md)                   |
| Antigravity **IDE** (the app)                     | built-in agent          | no automatic export: the export sees only CLI sessions, while the IDE keeps its own elsewhere. Checked 05.08 on live IDE data — the tool does not find them. Manual export + script                             | verified: the negative result was confirmed by a run                                                            | [antigravity.md](antigravity.md)                   |
| Terminal                                          | OpenCode                | no automatic export — copy the history files + script                                                                                                                                                                | partial: the file locations are from documentation, not from a run                                                   | [opencode.md](opencode.md)                         |
| Terminal                                          | crush                   | no automatic export — manual export + script                                                                                                                                                                         | not verified: I do not have the tool, the path is generic                                                                    | [crush.md](crush.md)                               |
| Visual Studio                                     | any                     | collectors do not work with it — manual path via `windows.md` (Visual Studio is always Windows)                                                                                                                      | not verified                                                                                        | [visual-studio.md](visual-studio.md)               |
| Have not chosen a tool yet                        | any                     | recommendation: Claude Code — the path is verified end to end                                                                                                                                                        | —                                                                                                       | [ne-vybral.md](ne-vybral.md)                       |
| **Windows** (any environment)                     | any                     | automatic: `specstory sync claude` — the Windows build came out on 12.08, before that it did not exist                                                                                          | partial: the build exists, checked on the releases page; the Claude Code mechanics were run end to end, but you will be the first to check the export itself on Windows | [windows.md](windows.md)                           |


Legend for the "Verification" column. "verified" — I went through the path on my machine, including redaction
on planted secrets, and the commands in the file are copied from a terminal that worked.
"partial" — not run, but the vendor documentation says it works this way; if it
differs, trust what you see and write to me. "not verified" — I physically do not have the setup, the path is assembled
from the generic mechanism, which always works, just takes longer.

## Heads-up: Windows

**Updated 16.08: Windows is no longer a separate manual path.** This page used to
say that no export tool for Windows existed, and that was true: the build appeared
only on August 12. Now the same `specstory sync claude` command works on Windows as
for everyone else. If you read the earlier version and set yourself up to
export every session by hand, open **[windows.md](windows.md)** again.

It also covers three things that occur only on Windows: the VS Code extension panel,
which refuses to open an old session on third-party models, the `/export` crash
in OneDrive folders, and the fork between a native install and WSL. If something
does not work, write to me and we will sort it out together.

## Three things that matter for everyone

First. Do the check from the first section of your file **before you start the homework**,
not after. A tool that found no sessions and a tool that found an empty result
look the same, but are fixed differently. The check takes ten seconds.

Second. The log contains not only your conversation with the agent, but also the contents of the files
the agent read, that is, your code. That is why the repository everything goes into
must be private, and why every file has a scrubbing step. The export tool's built-in redaction
cuts secrets of known formats, and this is verified, but it
does not touch email, phone numbers, surnames, addresses, database connection strings, passwords that look
like human words, and the name of the export file itself. Our script finishes that job, and its step
must not be skipped.

Third, and it is about the time limit. Agents do not keep history forever. For Claude Code it is **thirty
days**, after which it deletes the transcripts itself, and does so **at the moment of the next
launch**, not on a calendar. The course lasts longer than a month, so the logs of the first modules
will not survive until the end of the cohort if you do nothing. Fixed once and for all: add
to `~/.claude/settings.json` (on Windows it is `%USERPROFILE%\.claude\settings.json`)
the line `"cleanupPeriodDays": 3650`. You cannot set zero there, the minimum is one, so
we take a deliberately large number. Do this before the next agent launch.

I have not verified the same for the other tools, so the general rule is simple:
export logs at least once every couple of weeks, and then the retention period will not catch up with anyone.

And separately, because this question has already been asked: **you cannot forget to export a session**.
For Claude Code the raw files are written to disk continuously, throughout the session, not at the moment of exit,
and the export parses them after the fact. A closed IDE, a reboot or a forgotten `/export`
do not lose the conversation.

## Shared script and config

Path substitutions in the commands are reduced to one: the `sanitize-log.py` script sits next to
these instructions — download it once and put it in the root of your course
repository, and commit it together with the project. After that all the commands in the setup files
work exactly as written. The export tool's config is not handed out as a separate file: it is created with one command right from the "Turn off the network" step of your
file. The config turns off cloud sync, analytics and update checks —
with it the tool makes no network calls at all, I verified this, and on a work
laptop this is a mandatory condition, not an option.

`**sanitize-log.py**` — the scrubbing and metadata script. One run does three things.
First: it passes any export, markdown or HTML, through one set of rules
and replaces what it finds with labels — secrets, passwords, email, phone numbers, OS
usernames in paths. Second: it renames the export files to a clean
date-time — the original name holds a piece of your first prompt, and secrets end up there.
Third: it builds `context-report.md` next to the export — a summary of
context window management from the raw session files of your project: how many turns
in each session, the peak and final context window fill in tokens and percent, the cache hit share,
compactions (manual and automatic, how many tokens before and after). The report has only
numbers, not a line of code or conversation, so it is safe under any NDA — and it
goes into the commit together with the logs. For the report to be built, run the script from the root of the
project the agent worked in.

You can pass it your own names that a regular expression cannot catch:

```bash
python3 sanitize-log.py <file-or-folder> --names "Acme Ltd" "Smith" --dry-run
```

With `--dry-run` it changes nothing and only shows what it found. Without it, it rewrites
the file and puts the original next to it with the `.orig` suffix, and that one you should not commit.
