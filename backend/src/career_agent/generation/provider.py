from typing import Protocol

from career_agent.generation.contracts import (
    FeedbackAdviceDraft,
    FeedbackAdviceInput,
    JobAnalysisDraft,
    MaterialDraft,
    MaterialGenerationInput,
    PlanGenerationInput,
    PracticeEvaluationDraft,
    PracticeEvaluationInput,
    RollingPlanDraft,
)
from career_agent.settings import Settings


class GenerationProvider(Protocol):
    name: str
    model: str
    prompt_version: str

    def analyze_job(self, description: str) -> JobAnalysisDraft: ...

    def generate_materials(self, request: MaterialGenerationInput) -> MaterialDraft: ...

    def generate_plan(self, request: PlanGenerationInput) -> RollingPlanDraft: ...

    def evaluate_submission(
        self, request: PracticeEvaluationInput
    ) -> PracticeEvaluationDraft: ...

    def analyze_feedback(self, request: FeedbackAdviceInput) -> FeedbackAdviceDraft: ...


def build_provider(settings: Settings) -> GenerationProvider:
    if settings.provider == "demo":
        from career_agent.generation.demo import DemoProvider

        return DemoProvider()
    if settings.provider == "openai-compatible":
        from career_agent.generation.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider(settings)
    raise ValueError("unsupported_provider")
