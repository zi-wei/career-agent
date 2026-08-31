from typing import Literal

from pydantic import BaseModel, Field, model_validator


class JobRequirementDraft(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    evidence_text: str = Field(min_length=1, max_length=2000)


class JobAnalysisDraft(BaseModel):
    requirements: list[JobRequirementDraft] = Field(min_length=1)


class ProfileFactContext(BaseModel):
    id: str
    kind: str
    title: str
    content: str


class RequirementContext(BaseModel):
    id: str
    label: str
    category: str
    evidence_text: str


class MaterialGenerationInput(BaseModel):
    job_title: str
    company: str
    job_description: str
    target_role: str
    profile_facts: list[ProfileFactContext]
    requirements: list[RequirementContext]


class ResumeBulletDraft(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    source_refs: list[str] = Field(min_length=1)


class ResumeSectionDraft(BaseModel):
    kind: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    bullets: list[ResumeBulletDraft] = Field(min_length=1)


class InterviewQuestionDraft(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    category: str = Field(min_length=1, max_length=100)
    requirement_id: str
    evidence_text: str = Field(min_length=1, max_length=2000)
    answer_guide: str = Field(min_length=1, max_length=4000)


class MaterialDraft(BaseModel):
    target_title: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=4000)
    sections: list[ResumeSectionDraft] = Field(min_length=1)
    interview_title: str = Field(min_length=1, max_length=300)
    questions: list[InterviewQuestionDraft] = Field(min_length=1)


class PlanGenerationInput(BaseModel):
    job_title: str
    selected_requirements: list[RequirementContext] = Field(min_length=1)


class KeyConceptDraft(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=2000)


class KnowledgeGuidanceDraft(BaseModel):
    explanation: str = Field(min_length=1, max_length=6000)
    key_concepts: list[KeyConceptDraft] = Field(min_length=2)
    scenario_question: str = Field(min_length=1, max_length=3000)
    answer_framework: list[str] = Field(min_length=2)
    self_checks: list[str] = Field(min_length=2)


class ProjectMilestoneDraft(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    actions: list[str] = Field(min_length=1)
    expected_output: str = Field(min_length=1, max_length=2000)


class ProjectGuidanceDraft(BaseModel):
    business_context: str = Field(min_length=1, max_length=4000)
    milestones: list[ProjectMilestoneDraft] = Field(min_length=2)
    acceptance_criteria: list[str] = Field(min_length=2)
    deliverables: list[str] = Field(min_length=1)
    reflection_questions: list[str] = Field(min_length=2)


class GeneralGuidanceDraft(BaseModel):
    instructions: str = Field(min_length=1, max_length=4000)
    checklist: list[str] = Field(min_length=1)


class PlanTaskDraft(BaseModel):
    kind: Literal["knowledge_drill", "guided_project", "material_review", "application"]
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1, max_length=4000)
    estimated_minutes: int = Field(ge=10, le=480)
    completion_condition: str = Field(min_length=1, max_length=4000)
    evidence_requirement: str = Field(min_length=1, max_length=4000)
    requirement_id: str | None = None
    guidance: KnowledgeGuidanceDraft | ProjectGuidanceDraft | GeneralGuidanceDraft

    @model_validator(mode="after")
    def validate_guidance_for_kind(self) -> "PlanTaskDraft":
        if self.kind == "knowledge_drill" and not isinstance(
            self.guidance, KnowledgeGuidanceDraft
        ):
            raise ValueError("knowledge_drill必须包含知识讲解结构")
        if self.kind == "guided_project" and not isinstance(
            self.guidance, ProjectGuidanceDraft
        ):
            raise ValueError("guided_project必须包含项目实训结构")
        if self.kind in {"material_review", "application"} and not isinstance(
            self.guidance, GeneralGuidanceDraft
        ):
            raise ValueError("通用任务必须包含操作清单")
        return self


class PlanDayDraft(BaseModel):
    day_number: int = Field(ge=1, le=14)
    tasks: list[PlanTaskDraft] = Field(min_length=1)


class RollingPlanDraft(BaseModel):
    days: list[PlanDayDraft] = Field(min_length=14, max_length=14)


class PracticeEvaluationInput(BaseModel):
    task_title: str
    objective: str
    acceptance_criteria: list[str]
    content: str
    artifact_refs: list[str]
    report_summary: str


class PracticeEvaluationDraft(BaseModel):
    advisory: Literal[True] = True
    summary: str = Field(min_length=1, max_length=4000)
    strengths: list[str]
    improvements: list[str]


class FeedbackAdviceInput(BaseModel):
    application_status: str
    source_facts: list[str] = Field(min_length=1)


class FeedbackAdviceDraft(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)
    source_facts: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)
