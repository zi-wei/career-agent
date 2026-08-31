import pytest

from career_agent.generation.contracts import (
    FeedbackAdviceInput,
    MaterialGenerationInput,
    PlanGenerationInput,
    PracticeEvaluationInput,
    ProfileFactContext,
    RequirementContext,
)
from career_agent.generation.demo import DemoProvider
from career_agent.generation.openai_compatible import ProviderNotConfigured
from career_agent.generation.provider import build_provider
from career_agent.settings import Settings


def test_demo_provider_extracts_requirements_with_jd_evidence() -> None:
    analysis = DemoProvider().analyze_job(
        "负责 Linux 系统维护, 使用 Docker 和 Nginx, 编写 Shell 脚本."
    )

    assert [item.label for item in analysis.requirements] == [
        "Linux",
        "Docker",
        "Nginx",
        "Shell",
    ]
    assert all(item.evidence_text for item in analysis.requirements)


def test_demo_provider_uses_core_duty_when_no_catalog_keyword_matches() -> None:
    analysis = DemoProvider().analyze_job("协助完成内部系统的日常支持与问题跟进.")

    assert len(analysis.requirements) == 1
    assert analysis.requirements[0].label == "岗位核心职责"
    assert analysis.requirements[0].evidence_text == "协助完成内部系统的日常支持与问题跟进."


def test_demo_provider_generates_materials_from_supplied_facts() -> None:
    draft = DemoProvider().generate_materials(
        MaterialGenerationInput(
            job_title="Linux运维实习生",
            company="示例科技",
            job_description="使用 Docker部署服务.",
            target_role="Linux运维实习生",
            profile_facts=[
                ProfileFactContext(
                    id="fact-1",
                    kind="project",
                    title="个人服务器",
                    content="使用 Docker部署 Nginx服务.",
                )
            ],
            requirements=[
                RequirementContext(
                    id="req-1",
                    label="Docker",
                    category="container",
                    evidence_text="使用 Docker部署服务.",
                )
            ],
        )
    )

    assert draft.sections[0].bullets[0].source_refs == ["profile_fact:fact-1"]
    assert draft.questions[0].requirement_id == "req-1"


def test_demo_provider_generates_fourteen_day_plan_for_selected_requirements() -> None:
    draft = DemoProvider().generate_plan(
        PlanGenerationInput(
            job_title="Linux运维实习生",
            selected_requirements=[
                RequirementContext(
                    id="req-1",
                    label="Docker",
                    category="container",
                    evidence_text="使用 Docker部署服务.",
                )
            ],
        )
    )

    assert [day.day_number for day in draft.days] == list(range(1, 15))
    assert {
        task.requirement_id for day in draft.days for task in day.tasks
    } == {"req-1"}


def test_demo_plan_contains_complete_knowledge_and_project_guidance() -> None:
    draft = DemoProvider().generate_plan(
        PlanGenerationInput(
            job_title="Linux运维实习生",
            selected_requirements=[
                RequirementContext(
                    id="req-1",
                    label="Docker",
                    category="container",
                    evidence_text="使用 Docker部署服务.",
                )
            ],
        )
    )

    knowledge = next(
        task for day in draft.days for task in day.tasks if task.kind == "knowledge_drill"
    )
    project = next(
        task for day in draft.days for task in day.tasks if task.kind == "guided_project"
    )
    assert knowledge.guidance.explanation
    assert knowledge.guidance.key_concepts
    assert knowledge.guidance.scenario_question
    assert knowledge.guidance.answer_framework
    assert knowledge.guidance.self_checks
    assert project.guidance.business_context
    assert project.guidance.milestones
    assert project.guidance.acceptance_criteria
    assert project.guidance.deliverables
    assert project.guidance.reflection_questions


def test_provider_factory_selects_demo() -> None:
    assert isinstance(build_provider(Settings(provider="demo")), DemoProvider)


def test_provider_factory_requires_openai_compatible_configuration() -> None:
    with pytest.raises(ProviderNotConfigured):
        build_provider(Settings(provider="openai-compatible"))


def test_provider_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="unsupported_provider"):
        build_provider(Settings(provider="unknown"))


def test_demo_provider_evaluates_submission_as_advisory() -> None:
    draft = DemoProvider().evaluate_submission(
        PracticeEvaluationInput(
            task_title="Docker排查",
            objective="完成容器网络排查",
            acceptance_criteria=["记录步骤"],
            content="检查端口映射和容器日志.",
            artifact_refs=[],
            report_summary="排查完成.",
        )
    )

    assert draft.advisory is True
    assert draft.summary


def test_demo_provider_feedback_advice_preserves_source_facts() -> None:
    draft = DemoProvider().analyze_feedback(
        FeedbackAdviceInput(
            application_status="rejected",
            source_facts=["岗位暂停招聘"],
        )
    )

    assert draft.source_facts == ["岗位暂停招聘"]
    assert "能力不足" not in draft.summary
