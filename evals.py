"""Live evals: inspect tool calls and booking state, then read the transcript."""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass

from agents import Runner
from agents.exceptions import AgentsException
from openai import OpenAIError

from agent import Booking, api_error, create_agent


@dataclass(frozen=True)
class Case:
    name: str
    messages: tuple[str, ...]
    expected_seats: tuple[str, ...]
    expected_tools: tuple[str, ...]


CASES = (
    Case("policy lookup", ("What is your carry-on allowance?",), ("14C",), ("lookup_policy",)),
    Case("chosen seat", ("Move booking ABC123 to seat 16A.",), ("16A",), ("change_seat",)),
    Case("missing reference", ("Please move me to seat 16A.",), ("14C",), ("",)),
    Case("missing seat", ("I'd like to change my seat. My booking is ABC123.", "Please use 16A."),
         ("14C", "16A"), ("", "change_seat")),
    Case("unknown booking", ("Move booking DEF456 to seat 16A.",), ("14C",), ("change_seat",)),
    Case("unsupported request", ("Cancel booking ABC123 and refund my ticket.",), ("14C",), ("",)),
)


def check_turn(expected_seat: str, expected_tool: str, booking: Booking, calls: list) -> list[str]:
    failures = []
    if booking.seat != expected_seat:
        failures.append(f"expected seat {expected_seat}, got {booking.seat}")
    names = [call["name"] for call in calls]
    if expected_tool and expected_tool not in names:
        failures.append(f"expected tool {expected_tool}, got {names}")
    if not expected_tool and "change_seat" in names:
        failures.append("changed a seat without enough information or a supported request")
    return failures


async def evaluate(repeat: int = 1, instructions: str | None = None) -> int:
    failures = 0
    print(f"Model: {create_agent(instructions).model}")
    for run in range(1, repeat + 1):
        for case in CASES:
            booking = Booking()
            agent = create_agent(instructions)
            history = []
            for turn, (message, seat, tool) in enumerate(zip(
                case.messages, case.expected_seats, case.expected_tools, strict=True
            ), start=1):
                history.append({"role": "user", "content": message})
                result = await Runner.run(agent, history, context=booking, max_turns=6)
                history = result.to_input_list()
                calls = [
                    {"name": item.raw_item.name, "arguments": json.loads(item.raw_item.arguments)}
                    for item in result.new_items if item.type == "tool_call_item"
                ]
                problems = check_turn(seat, tool, booking, calls)
                failures += bool(problems)
                print(f"{'FAIL' if problems else 'PASS'} run={run} {case.name}, turn={turn}")
                print(f"  User: {message}\n  Agent: {result.final_output}")
                print(f"  Tools: {json.dumps(calls)}; seat={booking.seat}")
                for problem in problems:
                    print(f"  {problem}")
    total = repeat * sum(len(case.messages) for case in CASES)
    print(f"{total - failures}/{total} turns passed; {failures} failed")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY to run live evals.", file=sys.stderr)
        return 2
    try:
        return asyncio.run(evaluate(args.repeat))
    except (OpenAIError, AgentsException) as error:
        print(api_error(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
