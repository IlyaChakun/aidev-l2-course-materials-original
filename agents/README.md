# Agents for working with n8n

Two Claude Code subagents that cover the path from "I have an automation idea" to a finished
workflow. They work as a pair: the first extracts requirements, the second builds the JSON from them.

| File | What it does |
|---|---|
| `n8n-requirements-orchestrator.md` | Runs a dialogue and turns a vague idea into a structured specification: triggers, steps, data, error handling. Checks feasibility before anything is built |
| `n8n-workflow-builder.md` | Takes a finished specification and generates workflow JSON ready for import, together with implementation documentation |

## How to install

Put the files into the Claude Code agents folder:

```
cp *.md ~/.claude/agents/
```

After that, Claude Code sees them as subagents and calls them by name or by the meaning of the task.
To check that they were picked up: `/agents` in Claude Code.

## How to use

The usual order is this: first the requirements orchestrator, which asks questions and produces a
specification as output. You hand that to the builder, which builds the workflow. The split is deliberate: mixing
requirements gathering and generation in one pass works worse, because the model starts
making up the missing requirements itself instead of asking.

You can also call the builder without the orchestrator if you have already written the specification by hand.
