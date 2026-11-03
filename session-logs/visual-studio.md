# Visual Studio (.NET)

Honest from the start: I do not have Visual Studio, and I did not run this setup.
Automatic log collectors do not work with Visual Studio itself: they are all built
for terminal agents and for editors of the VS Code family, while Visual Studio is arranged
differently.

But this does not mean you will have to do everything by hand. If your agent is a terminal one
and not built into Visual Studio itself, then the export works: the tool's Windows build
came out on August 12, before that it did not exist. The whole path is laid out in the neighboring file
**`windows.md`** — open it and go step by step. The scrubbing script and the context window
report are there too: it is ordinary Python, and it works fully on Windows.

Two clarifications specifically for your case.

First. If your agent works as a panel inside Visual Studio and has no export
command — copy the conversation from the panel by hand into the file `ai-logs\session-date.md`,
then everything follows `windows.md` unchanged.

Second. A better working option: you can launch the agent not from the IDE panel
but from an ordinary terminal opened in the project folder — for example Claude Code
in PowerShell. You keep writing code in Visual Studio, the only thing that changes is where the agent
starts from. Then raw sessions are written automatically, Claude Code has
`/export`, and the context window report will be built in full.

If you do not plan to submit logs, you do not need to do any of this: submission
is voluntary and does not affect your grade. The file is kept in case you change your mind.

If something does not add up at any step — write to me, we will sort it out together,
and I will fix the instructions for everyone else.
