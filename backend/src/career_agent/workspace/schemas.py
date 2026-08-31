from pydantic import BaseModel, ConfigDict, Field


class ProfileFactInput(BaseModel):
    kind: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)


class WorkspaceProfileUpdate(BaseModel):
    target_role: str = Field(max_length=200)
    cities: list[str] = Field(max_length=20)
    availability: str = Field(max_length=500)
    raw_resume: str = Field(max_length=50000)
    facts: list[ProfileFactInput] = Field(max_length=100)


class ProfileFactView(ProfileFactInput):
    model_config = ConfigDict(from_attributes=True)

    id: str


class WorkspaceProfileView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_role: str
    cities: list[str]
    availability: str
    raw_resume: str
    facts: list[ProfileFactView]
