import re
from typing import Literal

from career_agent.generation.contracts import (
    FeedbackAdviceDraft,
    FeedbackAdviceInput,
    InterviewQuestionDraft,
    JobAnalysisDraft,
    JobRequirementDraft,
    KeyConceptDraft,
    KnowledgeGuidanceDraft,
    MaterialDraft,
    MaterialGenerationInput,
    PlanDayDraft,
    PlanGenerationInput,
    PlanTaskDraft,
    PracticeEvaluationDraft,
    PracticeEvaluationInput,
    ProjectGuidanceDraft,
    ProjectMilestoneDraft,
    ResumeBulletDraft,
    ResumeSectionDraft,
    RollingPlanDraft,
)

CATALOG: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Linux", "system", ("linux",)),
    ("Docker", "container", ("docker",)),
    ("Nginx", "web", ("nginx",)),
    ("Shell", "automation", ("shell", "bash")),
    ("Python", "automation", ("python",)),
    ("MySQL", "database", ("mysql",)),
    ("PostgreSQL", "database", ("postgresql", "postgres")),
    ("Redis", "database", ("redis",)),
    ("Kubernetes", "container", ("kubernetes", "k8s")),
    ("监控告警", "observability", ("监控", "告警", "prometheus", "grafana")),
    ("网络基础", "network", ("tcp/ip", "网络", "dns", "http")),
)


def split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[。！？.!?])\s*", text) if sentence.strip()]


class DemoProvider:
    name = "demo"
    model = "deterministic-demo"
    prompt_version = "demo-v1"

    def analyze_job(self, description: str) -> JobAnalysisDraft:
        sentences = split_sentences(description)
        lower_description = description.lower()
        requirements: list[JobRequirementDraft] = []
        for label, category, aliases in CATALOG:
            matched_alias = next((alias for alias in aliases if alias in lower_description), None)
            if matched_alias is None:
                continue
            evidence = next(
                (sentence for sentence in sentences if matched_alias in sentence.lower()),
                description.strip(),
            )
            requirements.append(
                JobRequirementDraft(label=label, category=category, evidence_text=evidence)
            )
        if not requirements:
            evidence = sentences[0] if sentences else description.strip()
            requirements.append(
                JobRequirementDraft(
                    label="岗位核心职责",
                    category="general",
                    evidence_text=evidence,
                )
            )
        return JobAnalysisDraft(requirements=requirements)

    def generate_materials(self, request: MaterialGenerationInput) -> MaterialDraft:
        sections = [
            ResumeSectionDraft(
                kind=fact.kind,
                title=fact.title,
                bullets=[
                    ResumeBulletDraft(
                        text=fact.content,
                        source_refs=[f"profile_fact:{fact.id}"],
                    )
                ],
            )
            for fact in request.profile_facts
        ]
        if not sections:
            sections = [
                ResumeSectionDraft(
                    kind="profile",
                    title="个人信息",
                    bullets=[
                        ResumeBulletDraft(
                            text=f"目标岗位: {request.target_role or request.job_title}",
                            source_refs=[f"job_requirement:{request.requirements[0].id}"],
                        )
                    ],
                )
            ]
        questions = [
            InterviewQuestionDraft(
                question=f"请结合实际经历说明你如何使用或理解 {item.label}?",
                category=item.category,
                requirement_id=item.id,
                evidence_text=item.evidence_text,
                answer_guide="说明背景、具体行动、验证方法和结果, 没有相关经历时如实说明准备思路.",
            )
            for item in request.requirements
        ]
        return MaterialDraft(
            target_title=request.target_role or request.job_title,
            summary=f"目标岗位: {request.job_title}. 现有材料仅使用用户已提供经历生成.",
            sections=sections,
            interview_title=f"{request.job_title}面试题",
            questions=questions,
        )

    def generate_plan(self, request: PlanGenerationInput) -> RollingPlanDraft:
        days = []
        for index in range(14):
            requirement = request.selected_requirements[index % len(request.selected_requirements)]
            kind: Literal["knowledge_drill", "guided_project"]
            guidance: KnowledgeGuidanceDraft | ProjectGuidanceDraft
            if index in {5, 12}:
                kind = "guided_project"
                guidance = ProjectGuidanceDraft(
                    business_context=(
                        f"模拟{request.job_title}接手一项与{requirement.label}相关的线上服务任务, "
                        "需要在不影响现有业务的前提下完成部署、验证和交接."
                    ),
                    milestones=[
                        ProjectMilestoneDraft(
                            title="设计与准备",
                            actions=[
                                f"梳理JD中{requirement.label}的原文要求.",
                                "写出环境、依赖、风险和回滚方案.",
                            ],
                            expected_output="一份实施清单和验证方案.",
                        ),
                        ProjectMilestoneDraft(
                            title="实施与验证",
                            actions=[
                                "按清单完成实训并记录关键步骤.",
                                "执行自定义验证, 保存现象、结果和异常处理过程.",
                            ],
                            expected_output="包含过程、结果和问题处理的实训记录.",
                        ),
                    ],
                    acceptance_criteria=[
                        "提交内容能让他人复现主要步骤.",
                        "明确写出预期结果、实际结果和验证依据.",
                    ],
                    deliverables=["实施记录", "验证结果摘要", "复盘说明"],
                    reflection_questions=[
                        "本次方案最可能在哪个环节失败, 如何提前发现?",
                        "面试中如何用背景、行动、验证和结果讲清这个项目?",
                    ],
                )
            else:
                kind = "knowledge_drill"
                guidance = KnowledgeGuidanceDraft(
                    explanation=(
                        f"{requirement.label}在{request.job_title}中用于支撑JD原文中的实际职责. "
                        "学习时先理解它解决的问题, 再掌握常见操作、验证方法和故障边界."
                    ),
                    key_concepts=[
                        KeyConceptDraft(
                            name="核心机制",
                            explanation=f"说明{requirement.label}如何工作, 以及关键组件之间的关系.",
                        ),
                        KeyConceptDraft(
                            name="验证与排障",
                            explanation="从现象、配置、运行状态、日志和依赖逐层定位, 每一步都保留证据.",
                        ),
                    ],
                    scenario_question=(
                        f"你负责的服务在使用{requirement.label}时出现异常, "
                        "请给出从确认影响范围到定位根因的排查顺序."
                    ),
                    answer_framework=[
                        "先复述现象、影响范围和已知条件.",
                        "按配置、状态、日志、网络或依赖逐层验证.",
                        "说明修复、回滚、复测和后续预防措施.",
                    ],
                    self_checks=[
                        f"能否不用术语堆砌解释{requirement.label}解决什么问题?",
                        "能否为每个排查步骤说明观察对象和判断依据?",
                    ],
                )
            days.append(
                PlanDayDraft(
                    day_number=index + 1,
                    tasks=[
                        PlanTaskDraft(
                            kind=kind,
                            title=f"{requirement.label}{'岗位实训' if kind == 'guided_project' else '知识训练'}",
                            objective=f"围绕岗位要求完成 {requirement.label} 的学习和可复述练习.",
                            estimated_minutes=60,
                            completion_condition="提交学习记录、场景分析和复盘.",
                            evidence_requirement="一份包含过程与结果的学习或实训记录.",
                            requirement_id=requirement.id,
                            guidance=guidance,
                        )
                    ],
                )
            )
        return RollingPlanDraft(days=days)

    def evaluate_submission(
        self, request: PracticeEvaluationInput
    ) -> PracticeEvaluationDraft:
        return PracticeEvaluationDraft(
            advisory=True,
            summary="已收到提交. 评价基于用户提供的文本和产物引用, 不代表系统执行验证.",
            strengths=["提交包含可复盘的过程记录."],
            improvements=["继续补充可复现步骤、预期结果和实际结果."],
        )

    def analyze_feedback(self, request: FeedbackAdviceInput) -> FeedbackAdviceDraft:
        return FeedbackAdviceDraft(
            summary="根据已记录反馈整理下一轮行动, 不对未记录原因作推断.",
            source_facts=request.source_facts,
            next_actions=["复核本次使用的材料版本.", "将明确出现的问题加入下一轮面试训练."],
        )
