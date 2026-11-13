"""A terminal airline assistant. All booking actions are local simulations."""

import asyncio
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agents import Agent, ModelSettings, RunContextWrapper, Runner, function_tool
from agents import set_tracing_disabled
from agents.exceptions import AgentsException
from openai import OpenAIError
from openai.types.shared import Reasoning

set_tracing_disabled(True)
PROMPT_PATH = Path(__file__).with_name("prompt.md")
POLICIES = {
    "baggage": "One carry-on, at most 22 x 14 x 9 inches and 50 pounds, is included.",
    "wifi": "Wi-Fi is free. Join the Airline-Wifi network.",
    "seating": "Seats are rows 1–30, letters A–F. Seat changes are free in this demo.",
}


@dataclass
class Booking:
    confirmation: str = "ABC123"
    seat: str = "14C"

    def move(self, confirmation: str, seat: str) -> str:
        if confirmation.strip().upper() != self.confirmation:
            raise ValueError("Booking not found. Ask the passenger to check the reference.")
        seat = seat.strip().upper()
        if not re.fullmatch(r"([1-9]|[12][0-9]|30)[A-F]", seat):
            raise ValueError("Invalid seat. Choose a row from 1 to 30 and letter A to F.")
        self.seat = seat
        return f"Seat changed to {seat} for booking {self.confirmation}."


@function_tool
def lookup_policy(topic: Literal["baggage", "wifi", "seating"]) -> str:
    """Read the airline's published policy for the requested topic."""
    return POLICIES[topic]


@function_tool
def change_seat(
    context: RunContextWrapper[Booking], confirmation: str, seat: str
) -> str:
    """Change a local booking's seat using its reference and a specific seat."""
    try:
        return context.context.move(confirmation, seat)
    except ValueError as error:
        return str(error)


def create_agent(instructions: str | None = None) -> Agent[Booking]:
    return Agent[Booking](
        name="Northstar Air support",
        instructions=PROMPT_PATH.read_text() if instructions is None else instructions,
        model=os.environ.get("OPENAI_MODEL", "gpt-6.1-sol"),
        model_settings=ModelSettings(reasoning=Reasoning(effort="low"), max_tokens=4096),
        tools=[lookup_policy, change_seat],
    )


def api_error(error: Exception) -> str:
    # Don't print SDK error bodies, which can include credential fragments.
    status = getattr(error, "status_code", None)
    return f"ERROR: {type(error).__name__}" + (f" (HTTP {status})" if status else "")


async def main() -> int:
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY before starting a chat.", file=sys.stderr)
        return 2
    booking = Booking()
    agent = create_agent()
    history = []
    print("Northstar Air demo. /booking shows state; /quit exits.")
    while True:
        try:
            message = input("You: ").strip()
        except EOFError:
            break
        if message == "/quit":
            break
        if message == "/booking":
            print(f"Booking {booking.confirmation}: seat {booking.seat}")
            continue
        if not message:
            continue
        history.append({"role": "user", "content": message})
        result = await Runner.run(agent, history, context=booking, max_turns=6)
        history = result.to_input_list()
        print(f"Agent: {result.final_output}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print()
    except (OpenAIError, AgentsException) as error:
        print(api_error(error), file=sys.stderr)
        sys.exit(2)
