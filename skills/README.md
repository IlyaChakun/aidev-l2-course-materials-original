# Skills

## ai-agent-builder

A skill for designing AI agents and assistants: it assembles a full set of artifacts, not
just the prompt text.

The output: a system prompt with XML structure, chain of reasoning, constraints
and examples; an input specification; an output JSON schema; a model recommendation with an estimate of tokens
and cost; a log of open decisions. It works both for agents with tools and without them,
and also for individual pipeline steps, classifiers and extractors.

When it is useful in the course: the third part of the homework is a chain of agents, and each one needs
a system prompt with explicit boundaries. The skill makes you spell out the boundaries and the output format
before you start debugging them in a node.

### How to install

```
cp -r ai-agent-builder ~/.claude/skills/
```

To check: `/skills` in Claude Code. It is invoked by name or by phrases like "создай агента" (create an agent),
"напиши системный промпт" (write a system prompt), "оптимизируй промпт" (optimize a prompt).
