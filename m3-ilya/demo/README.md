# M3 lecture demos

Two small stands for the M3 lecture, a preparation script and step files for the third demo (it runs on `Smart-Technical-Support/agent_v2`), and `present.py`, which runs any step file one command per Enter.

| Folder | Slide | What it shows | Needs |
|---|---|---|---|
| [01-bare-loop](01-bare-loop/loop.py) | 10 | A bare agent loop on the OpenAI API: the model asks, the code runs tools and stops on a budget | `OPENAI_API_KEY` from `Smart-Technical-Support/.env` (paid, under a cent per run) |
| [02-crash-double-effect](02-crash-double-effect/crash.py) | 25 | A file `SqliteSaver` resumes the graph after a crash, and the effect runs twice; an idempotency key fixes it | nothing: no model |
| [03-agent-v2](03-agent-v2/steps.txt) | 36 | The homework scenario on the Operator: pause, approve once, reject, an empty thread | `03-agent-v2/prepare.sh` within the hour before the lecture (paid, a few cents) |

All three use the venv of `agent_v2` (`openai`, `langgraph` 1.2.15, `langgraph-checkpoint-sqlite` 3.1.2). `present.py` finds it on its own when `Smart-Technical-Support` sits next to this repository; otherwise set `STS` or `PY`:

```bash
export PY=~/Desktop/projects/ai-learning/Smart-Technical-Support/agent_v2/.venv/bin/python
```

On stage, from this folder:

```bash
python3 present.py 01-bare-loop/steps.txt
python3 present.py 02-crash-double-effect/steps.txt
python3 present.py 03-agent-v2/steps.txt      # after 03-agent-v2/prepare.sh
```

Enter runs the shown command, `s` skips it, `q` quits.

`outbox.txt` and `checkpoints.sqlite*` in `02-crash-double-effect/` are run artifacts: `$PY crash.py reset` removes them. `03-agent-v2/demo3.env` is written by `prepare.sh` and points at a temporary workspace.
