# Elite Agent Prompt Framework

## Purpose

A meta-prompt for creating high-quality system prompts for AI agents. Use it when you need to create a prompt for:
- AI agents with tools (n8n AI Agent, Claude with tools, OpenAI Assistants)
- AI assistants without tools (chatbots, specialized helpers)
- Any LLM-based solutions with a system prompt

## When to use

Apply this framework when the user asks to:
- Create/write a prompt for an agent
- Optimize an existing system prompt
- Build an AI assistant for a specific task
- Configure an AI Agent node in n8n
- Create a chatbot with a specific specialization

## How to use (instructions for the LLM)

### Step 1: Load the framework
Use the full text of the meta-prompt from `elite-agent-prompt.txt` (including all XML tags) as the basis for creating the prompt.

### Step 2: Gather information
Per the framework, you MUST ask the user 3-5 critical questions:
- Specific goals and expected outcomes
- Target audience and its level of expertise
- Specific constraints or requirements
- Required level of detail
- Edge cases that need to be handled

If the information is already available in the context (e.g., from an n8n workflow JSON or documentation), use it.

### Step 3: Create the prompt
Based on the answers, create a prompt with the following structure:
1. **Title/Description** — position the agent as an expert in the domain
2. **Instructions** — clear step-by-step instructions
3. **Chain of Thoughts** — a logical chain of reasoning
4. **What Not To Do** — prohibitions and anti-patterns
5. **Few-Shot Examples** — examples of desired and undesired behavior

### Step 4: Create the mandatory artifacts

When creating a prompt for an assistant, ALWAYS create the following files in the project folder.

#### File naming rule

You MUST prefix all files with the agent name:

```
{agent-name}-agent-prompts.txt
{agent-name}-agent-input-spec.md
{agent-name}-agent-json-schema.json
{agent-name}-agent-model-recommendations.md
{agent-name}-agent-tbd-items.md
```

**Examples:**
- For the chapters agent: `chapters-agent-prompts.txt`
- For the summary agent: `summary-agent-json-schema.json`
- For the keywords agent: `keywords-agent-model-recommendations.md`

This makes it possible to tell apart files of different agents in the same folder or when moving them.

#### 1. `{agent}-agent-prompts.txt` — Prompts (User + System)

The file contains two sections. **User message ON TOP** (more convenient for the n8n interface):

```
================================================================================
USER MESSAGE
================================================================================

{{ $json.variableName }}


================================================================================
SYSTEM MESSAGE
================================================================================

<prompt>
...full system prompt in XML structure...
</prompt>
```

**Important:**
- User message on top — only the variable, no descriptions
- System message below — all logic, instructions, examples

#### 2. `{agent}-agent-input-spec.md` — Input data specification
A description of what arrives in the user message:
- Variable name
- Data format (JSON, text, SRT)
- Structure and examples
- Constraints (min/max length, encoding)
- Data source

#### 3. `{agent}-agent-tbd-items.md` — Questions for discussion
A document with open questions that require discussion with the team:
- Undefined requirements
- Alternative approaches
- Edge cases requiring a decision
- History of decisions made

#### 4. `{agent}-agent-model-recommendations.md` — Model recommendations
A document with analysis and recommendations:
- Token estimate for typical input data
- Model comparison table (context, price, quality)
- Cost per request estimate
- Recommended temperature for different scenarios
- Final recommendations (MVP/Production/Premium)

#### 5. `{agent}-agent-json-schema.json` — JSON Schema
A formal schema of the assistant's response structure:
- All required and optional fields
- Data types and constraints
- Status and error codes
- Examples of successful and error responses

## Key principles of the framework

1. **Communication language** — ALWAYS respond in the user's language
2. **Questions are mandatory** — never skip the information-gathering stage
3. **Model adaptation** — simpler language for small models, more complex for large ones
4. **Chain of Thoughts** — always include step-by-step reasoning
5. **Negative examples** — always show what NOT to do
6. **Safety** — integrate ethical constraints

## Prompt structure (output template)

```xml
<prompt>
<title># [AGENT ROLE NAME]</title>

<description>
YOU ARE [EXPERT POSITIONING]...
</description>

<instructions>
## INSTRUCTIONS
1. [Instruction 1]
2. [Instruction 2]
...
</instructions>

<output_format>
<!-- Optional but recommended for Claude models when agent returns structured data.
     Define the JSON schema or output pattern here. Include a minimal example. -->
## OUTPUT FORMAT
[JSON schema or output pattern description]
</output_format>

<chain_of_thoughts>
## CHAIN OF THOUGHTS
1. [Step 1]
   1.1. [Sub-step]
...
</chain_of_thoughts>

<restrictions>
## WHAT NOT TO DO
- NEVER [restriction 1]
- NEVER [restriction 2]
...
</restrictions>

<examples>
## FEW-SHOT EXAMPLES

Desired Example:
[Input] → [Output]

Undesired Example:
[Input] → [Wrong Output]
</examples>
</prompt>
```

**Tag notes:**
- `<output_format>` — an optional tag; add it for agents with JSON/structured output
- `<examples>` — plural (not `<example>`), since the section contains multiple examples
- Inside `<instructions>` for complex agents you can use section headings: `## INSTRUCTION 1: INPUT VALIDATION`, `## INSTRUCTION 2: ...` — this improves Claude's navigation through long prompts

## Files

- `elite-agent-prompt.txt` — full text of the meta-prompt (DO NOT EDIT)
- `readme.md` — these instructions
