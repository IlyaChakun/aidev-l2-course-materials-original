# Anthropic Best Practices — XML Tags & Context Engineering

> Source: Anthropic official docs (docs.claude.com, anthropic.com/engineering)

## XML Tag Patterns for Claude

Claude is specifically trained to recognize XML tags for structuring prompts. Use them to create clear boundaries.

### Recommended tags

```xml
<role>Agent identity and expertise</role>
<context>Background information, domain knowledge</context>
<instructions>Step-by-step behavioral rules</instructions>
<constraints>Limitations, boundaries, what NOT to do</constraints>
<examples>Few-shot demonstrations</examples>
<output_format>Expected response structure</output_format>
<input>User-provided data (wrapped in tags)</input>
```

### Tag nesting
Tags can be nested for hierarchical organization:
```xml
<instructions>
  <step1>Validate input</step1>
  <step2>Process data</step2>
  <step3>Format output</step3>
</instructions>
```

### Variable injection
Wrap dynamic data in descriptive tags:
```xml
<user_query>{{query}}</user_query>
<existing_data>{{data}}</existing_data>
```

## Context Engineering for Agents

### The 4 Strategies (from Anthropic's engineering blog)

1. **Write clearly and directly** — Be specific about what you want. "Extract the company name" not "Find relevant information"

2. **Provide examples** — Few-shot examples are the most reliable way to steer behavior. 3+ examples recommended for complex tasks.

3. **Use XML structure** — Claude understands XML better than most models. Use it for:
   - Separating instructions from data
   - Marking few-shot example boundaries
   - Structuring output format

4. **Let Claude think** — For complex reasoning, use chain-of-thought. `<thinking>` tags for internal reasoning before the final answer.

### Prompt Length Guidelines

- System prompts can be very long (10K+ tokens) — Claude handles them well
- Front-load the most important instructions
- Use XML sections to help Claude navigate long prompts
- If a section is >500 words, consider making it a separate XML block

### JSON Output with Claude

- Use `<output_format>` tag with explicit JSON schema
- Provide both the schema AND an example
- For complex schemas: describe field-by-field, then show complete example
- Claude respects `response_format: { type: "json_object" }` in API calls

## How to Apply in EAP Framework

The EAP XML structure (`<prompt><title>...<description>...<instructions>...`) aligns perfectly with Claude's training. Additional tips:

1. Wrap user input explicitly: `{{ $json.data }}` → `<input>{{ $json.data }}</input>`
2. For complex inputs, use nested tags: `<input><transcript>...</transcript><speakers>...</speakers></input>`
3. Add `<thinking>` guidance in chain_of_thoughts for Claude models
4. JSON output: include schema in both `<output_format>` tag AND in API structured output parameter (belt and suspenders)
5. Add `<output_format>` as a dedicated EAP section between `<instructions>` and `<chain_of_thoughts>` — this keeps output contract separate from processing logic

### Structuring Complex Instructions with XML

For agents with many instruction steps (5+), use named section headers or nested tags to help Claude navigate:

```xml
<instructions>

## INSTRUCTION 1: INPUT VALIDATION
1.1. Check required fields...
1.2. If invalid → return error JSON...

## INSTRUCTION 2: CORE PROCESSING
2.1. Analyze the input...
2.2. Apply business logic...

## INSTRUCTION 3: OUTPUT ASSEMBLY
3.1. Build JSON structure...
3.2. Validate before returning...

</instructions>
```

This pattern (used in production by MediAgile cold-call and resource-info agents) significantly improves instruction adherence on long prompts.

### Defining Enumerable Sections with XML

When an agent must produce a variable set of output sections (e.g., insight categories), use `<main_sections>` with named `<section>` children to define them declaratively:

```xml
<main_sections>

<section name="Key Findings">
- Extract main findings from the input
- requires_action: true for urgent findings
</section>

<section name="Recommendations">
- Specific actionable recommendations
- requires_action: true for all items
</section>

</main_sections>
```

This approach is cleaner than listing sections as prose and allows Claude to parse section names and rules independently.
