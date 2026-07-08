"""
Pydantic models for diagnosis output.

These describe the JSON shape that /diagnose will return and that the LLM will receive in the final project.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["high", "medium"]
Status = Literal["ok", "warning", "critical"]


class Issue(BaseModel):
    type: str
    severity: Severity
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ProcessSummary(BaseModel):
    name: str
    memory_mb: float


class DiagnosisResult(BaseModel):
    status: Status
    issues: list[Issue] = Field(default_factory=list)
    top_processes: list[ProcessSummary] = Field(default_factory=list)