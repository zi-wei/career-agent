from pydantic import BaseModel, ConfigDict, Field


class ResumeBullet(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source_refs: list[str] = Field(min_length=1)


class ResumeSection(BaseModel):
    kind: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    bullets: list[ResumeBullet]


class ResumeRevisionInput(BaseModel):
    summary: str = Field(max_length=5000)
    sections: list[ResumeSection]


class ResumeView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    root_id: str
    previous_revision_id: str | None
    job_version_id: str
    revision: int
    status: str
    target_title: str
    summary: str
    sections: list[ResumeSection]


class InterviewQuestion(BaseModel):
    question: str
    category: str
    requirement_id: str
    evidence_text: str
    answer_guide: str


class InterviewPackView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_version_id: str
    revision: int
    status: str
    title: str
    questions: list[InterviewQuestion]


class MaterialBundleView(BaseModel):
    job_id: str
    resume: ResumeView
    interview_pack: InterviewPackView
