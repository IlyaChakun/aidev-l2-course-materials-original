"""Demo 1: a bare agent loop on the raw OpenAI API, two toy Operator tools, no framework."""
import json, os, sys
from pathlib import Path
from openai import OpenAI

TICKETS = {2: "Teammate invitation link: I invited a new teammate last week and she says "
              "the link does not work any more. How long is an invitation link valid?"}
ARTICLE = ("team-and-roles.md: The person receives an email with an invitation link. "
           "The link is valid for 7 days. Re-send it once the 7 days have passed.")

def get_ticket(id: int) -> str:
    return TICKETS[int(id)]                       # unknown id -> KeyError -> an observation

def search_knowledge_base(query: str) -> str:
    return ARTICLE

DISPATCH = {"get_ticket": get_ticket, "search_knowledge_base": search_knowledge_base}
TOOLS = [
    {"type": "function", "function": {"name": "get_ticket", "description": "Read a support ticket by id.",
     "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}}},
    {"type": "function", "function": {"name": "search_knowledge_base", "description": "Search help articles.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
]

def load_env():
    env = Path(os.getenv("STS_ENV", Path(__file__).resolve().parents[6] / "Smart-Technical-Support/.env"))
    for line in env.read_text().splitlines() if env.exists() else []:
        k, _, v = line.partition("=")
        if k in ("OPENAI_API_KEY", "OPENAI_MODEL") and v.strip():
            os.environ.setdefault(k, v.strip())

load_env()
client, MODEL = OpenAI(), os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_STEPS = int(os.getenv("MAX_STEPS", "10"))
SYSTEM = "You are a first-line support operator. Use the tools; do not answer from memory."
messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": sys.argv[1]}]

for step in range(1, MAX_STEPS + 1):
    r = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS,
                                       parallel_tool_calls=False, temperature=0)
    choice, used = r.choices[0], r.usage.prompt_tokens
    messages.append(choice.message.model_dump(exclude_none=True))
    if choice.finish_reason in ("length", "content_filter"):
        raise RuntimeError(f"no answer: {choice.finish_reason}")
    if choice.finish_reason != "tool_calls":
        print(f"iter {step} · finish_reason={choice.finish_reason} · input_tokens={used}")
        print("ANSWER:", choice.message.content)
        break
    for call in choice.message.tool_calls:
        args = json.loads(call.function.arguments)
        try:
            out, err = str(DISPATCH[call.function.name](**args)), False
        except Exception as e:
            out, err = f"Error: {type(e).__name__}: {e}. Check the arguments and try again.", True
        print(f"iter {step} · finish_reason=tool_calls · {call.function.name}({json.dumps(args)})"
              f" · input_tokens={used}" + (" · ERROR" if err else ""))
        messages.append({"role": "tool", "tool_call_id": call.id, "content": out})
else:
    sys.exit(f"RuntimeError: iteration budget exhausted after {MAX_STEPS} steps")
