# Airline support agent

A small Python agent exercise for a Forward Deployed / Solutions Engineer
interview. Use AI coding tools freely; be ready to explain your decisions and
show what you verified.

## Customer brief

Northstar Air is a fictional airline. Its support team wants an assistant that
answers policy questions and helps passengers change seats. Staff care about
short, useful conversations and accurate actions. The assistant should use the
published policies, collect missing information, and only change a seat when
the passenger has supplied a booking reference and chosen a specific seat.
It must not invent passenger preferences or claim an action succeeded when it
didn't. Unsupported requests should go to a human.

This is a local simulation. Every new chat starts with booking `ABC123` in seat
`14C`. Seat changes only affect memory for that chat. There is no real airline,
seat-availability service, authentication, or persistent database.

## Setup

Use Python 3.12 or newer. There is no build step. The only direct runtime
dependency is OpenAI's Agents SDK; pip installs its dependencies too.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The interviewer provides an API key separately. Set `OPENAI_API_KEY` in your
shell without putting it in a source file or commit. The app reads environment
variables directly; it does not load `.env` files. Live chats and evals make
billable API calls. The default model is `gpt-6.1-sol` with low reasoning effort;
`OPENAI_MODEL` overrides it with a compatible reasoning model. Use the same
model before and after your change. SDK tracing is disabled.

```bash
python agent.py                  # chat; /booking shows local state; /quit exits
python -m unittest -v            # offline tests; no API key needed
python evals.py                  # live behavior checks; API key required
python evals.py --repeat 3       # check consistency across fresh sessions
```

API/configuration errors print `ERROR` and exit 2. Behavior failures print
`FAIL` and exit 1. A successful eval run exits 0. Live behavior can vary between
runs. Evals inspect tool use and booking state, not an exact
wording; they do not fully judge response quality. Read the conversations too.

## Files

- `agent.py`: booking state, policy/seat tools, agent setup, terminal chat.
- `prompt.md`: editable agent instructions.
- `evals.py`: live scenarios and behavior checks.
- `test_agent.py`: offline checks for the local booking behavior and eval checks.

## Source

Adapted from OpenAI's MIT-licensed
[customer-service example](https://github.com/openai/openai-agents-python/blob/64fbde5d02b42ae5f9db668eb0184cdb3fc9d775/examples/customer_service/main.py).
This exercise reduces the example to one agent, uses a fixed local booking,
and adds interview-specific instructions, checks, and documentation. The
upstream license is retained in `LICENSE`.
