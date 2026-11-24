# M3 · One agent in code: lecture materials

The slides and the live demos from the M3 lecture session. The homework text is in [`../M3/`](../M3/README.md); start the homework from [`../M3/homework.md`](../M3/homework.md).

## What is here

| Path | What it is |
|---|---|
| [`slides/m3-lecture.html`](slides/m3-lecture.html) | **M3 lecture** deck: workflow or agent, the agent loop, frameworks, state and checkpoints, the pause for approval, memory. Opens in a browser with a double click |
| [`demo/01-bare-loop/`](demo/01-bare-loop/loop.py) | **Demo 1** (slide 10): a bare agent loop on the OpenAI API, the code runs the tools and stops on a budget |
| [`demo/02-crash-double-effect/`](demo/02-crash-double-effect/crash.py) | **Demo 2** (slide 25): a checkpoint resumes the graph after a crash, the effect runs twice; an idempotency key fixes it |
| [`demo/03-agent-v2/`](demo/03-agent-v2/steps.txt) | **Demo 3** (slide 36): the homework scenario on `Smart-Technical-Support/agent_v2`: pause, approve once, reject, an empty thread |
| [`demo/present.py`](demo/present.py) | Runs a step file one command per Enter |

## Running the demos

See [`demo/README.md`](demo/README.md). The demos use the venv of `Smart-Technical-Support/agent_v2`; `present.py` finds it when `Smart-Technical-Support` sits next to this repository, otherwise set `STS` or `PY`. From the repository root:

```bash
cd m3-ilya/demo
python3 present.py 01-bare-loop/steps.txt
```

Keys go into `.env` files only. They are in `.gitignore`: never commit them and never paste them into a chat.
