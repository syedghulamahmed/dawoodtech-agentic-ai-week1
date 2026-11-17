"""Pydantic models for tool arguments and final structured output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class WeatherArgs(StrictToolArgs):
    city: str = Field(min_length=1, max_length=100, description="City name, optionally with country.")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius", description="Temperature unit for the returned weather."
    )


class CalculatorArgs(StrictToolArgs):
    expression: str = Field(
        min_length=1,
        max_length=200,
        description="A basic arithmetic expression, for example '(18 * 7) + 4'.",
    )


class SaveNoteArgs(StrictToolArgs):
    title: str = Field(min_length=1, max_length=120, description="Short title for the note.")
    content: str = Field(min_length=1, max_length=4000, description="Text to store in the note.")


class SearchNotesArgs(StrictToolArgs):
    query: str = Field(min_length=1, max_length=200, description="Words to search for in saved notes.")


class AnswerSummary(BaseModel):
    """The only accepted final response shape returned by the assistant."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, description="A clear answer to the user's request.")
    tools_used: list[str] = Field(default_factory=list, description="Names of tools actually executed.")
    confidence: float = Field(ge=0.0, le=1.0, description="Self-assessed confidence between 0 and 1.")