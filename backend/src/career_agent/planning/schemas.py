from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SelectionState = Literal["strengthen", "skip", "already_have", "unselected"]


class SelectionInput(BaseModel):
    requirement_id: str
    state: SelectionState


class SelectionUpdate(BaseModel):
    selections: list[SelectionInput] = Field(min_length=1)


class SelectionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: str
    state: SelectionState


class SelectionListView(BaseModel):
    items: list[SelectionView]


class PlanTaskView(BaseModel):
    id: str
    kind: str
    title: str
    objective: str
    completion_condition: str
    requirement_id: str | None
    status: str


class PlanDayView(BaseModel):
    day_number: int
    date: date
    tasks: list[PlanTaskView]


class RollingPlanView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_version_id: str
    revision: int
    status: str
    timezone: str
    starts_on: date
    days: list[PlanDayView]
