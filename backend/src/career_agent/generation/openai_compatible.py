from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

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


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ProviderNotConfigured(ProviderError):
    def __init__(self) -> None:
        super().__init__("provider_not_configured", "真实模型 Provider配置不完整")


ContractT = TypeVar("ContractT", bound=BaseModel)


class OpenAICompatibleProvider:
    name = "openai-compatible"
    prompt_version = "job-analysis-v1"

    def __init__(self, settings: Settings) -> None:
        if not settings.model_base_url or not settings.model_api_key or not settings.model_name:
            raise ProviderNotConfigured()
        self.base_url = settings.model_base_url.rstrip("/")
        self.api_key = settings.model_api_key
        self.model = settings.model_name
        self.client = httpx.Client(timeout=settings.model_timeout_seconds)

    def analyze_job(self, description: str) -> JobAnalysisDraft:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "你是招聘岗位分析器. 只输出 JSON对象, 不输出 Markdown. "
                    "提取可独立训练和面试验证的岗位要求. evidence_text必须逐字引用 JD原文. "
                    "输出格式: {\"requirements\":[{\"label\":string,"
                    "\"category\":string,\"evidence_text\":string}]}"
                ),
            },
            {"role": "user", "content": f"JD原文:\n{description}"},
        ]
        def validate(draft: JobAnalysisDraft) -> None:
            for requirement in draft.requirements:
                if requirement.evidence_text not in description:
                    raise ValueError(f"JD引用不在原文中: {requirement.label}")

        return self._structured(messages, JobAnalysisDraft, validate)

    def generate_materials(self, request: MaterialGenerationInput) -> MaterialDraft:
        allowed_refs = {
            *(f"profile_fact:{fact.id}" for fact in request.profile_facts),
            *(f"job_requirement:{item.id}" for item in request.requirements),
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "你是专业中文针对性简历生成器. 根据目标岗位JD和用户真实经历, "
                    "生成现代、简洁、适合招聘者快速扫描的中文简历内容与面试题. "
                    "简历必须突出与JD直接相关的岗位关键词, 简介控制在2到4句, "
                    "每条经历使用清晰的行动、技术和结果结构; 没有真实量化结果时不得补造数字. "
                    "按岗位匹配度组织1到5个 section, 只保留有真实事实支撑的模块, "
                    "每个 section包含1到4条简洁 bullet. summary已经用于自我评价, "
                    "sections不得重复自我评价; 优先组织教育背景、项目或工作经历和技能特长. "
                    "面试题生成5到8道, 优先覆盖JD核心要求并给出可复述的回答框架. "
                    "但不得创建输入事实中不存在的学校、公司、荣誉、职责、联系方式或时间. "
                    "必须包含所有顶层字段, 只输出完整 JSON对象, "
                    "不要输出 HTML、CSS、Markdown或解释文字. "
                    "每条简历 bullet必须包含 source_refs, 且每个引用只能逐字选自: "
                    f"{json.dumps(sorted(allowed_refs), ensure_ascii=False)}. "
                    f"输出必须符合 JSON Schema: {json.dumps(MaterialDraft.model_json_schema(), ensure_ascii=False)}"
                ),
            },
            {"role": "user", "content": request.model_dump_json()},
        ]
        raw_ref_aliases: dict[str, str | None] = {}
        for raw_id, canonical_ref in [
            *((fact.id, f"profile_fact:{fact.id}") for fact in request.profile_facts),
            *((item.id, f"job_requirement:{item.id}") for item in request.requirements),
        ]:
            raw_ref_aliases[raw_id] = (
                canonical_ref if raw_id not in raw_ref_aliases else None
            )
        requirement_ids = {item.id for item in request.requirements}
        evidence_by_id = {item.id: item.evidence_text for item in request.requirements}

        def validate(draft: MaterialDraft) -> None:
            for section in draft.sections:
                normalized_kind = section.kind.strip().lower().replace("-", "_")
                if (
                    normalized_kind in {"summary", "profile", "self_evaluation", "self_assessment"}
                    or section.title.strip() in {"自我评价", "个人评价", "个人总结", "个人简介"}
                ):
                    raise ValueError("sections不得重复summary中的自我评价")
                for bullet in section.bullets:
                    bullet.source_refs = [
                        raw_ref_aliases.get(source_ref) or source_ref
                        for source_ref in bullet.source_refs
                    ]
                    if not set(bullet.source_refs).issubset(allowed_refs):
                        raise ValueError("简历引用超出允许的事实集合")
            for question in draft.questions:
                if question.requirement_id not in requirement_ids:
                    raise ValueError("面试题引用了未知岗位要求")
                if question.evidence_text != evidence_by_id[question.requirement_id]:
                    raise ValueError("面试题 JD引用与已保存要求不一致")

        return self._structured(messages, MaterialDraft, validate, max_tokens=4096)

    def generate_plan(self, request: PlanGenerationInput) -> RollingPlanDraft:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是14天求职训练计划生成器. 只输出 JSON对象. 计划必须恰好14天, "
                    "知识和项目任务只能引用输入中用户明确选择的 requirement_id. "
                    f"输出必须符合 JSON Schema: {json.dumps(RollingPlanDraft.model_json_schema(), ensure_ascii=False)}"
                ),
            },
            {"role": "user", "content": request.model_dump_json()},
        ]
        selected_ids = {item.id for item in request.selected_requirements}

        def validate(draft: RollingPlanDraft) -> None:
            if {day.day_number for day in draft.days} != set(range(1, 15)):
                raise ValueError("计划日期必须完整覆盖1到14")
            for day in draft.days:
                for task in day.tasks:
                    if task.kind in {"knowledge_drill", "guided_project"}:
                        if task.requirement_id not in selected_ids:
                            raise ValueError("计划任务引用了未选择的岗位要求")
                    elif task.requirement_id is not None and task.requirement_id not in selected_ids:
                        raise ValueError("计划附加任务引用了未知岗位要求")

        return self._structured(messages, RollingPlanDraft, validate)

    def evaluate_submission(
        self, request: PracticeEvaluationInput
    ) -> PracticeEvaluationDraft:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是岗位实训评价器. 只输出JSON对象. 只评价用户提供的内容, "
                    "不得声称已执行命令或验证外部链接. advisory必须为true. "
                    f"输出必须符合JSON Schema: {json.dumps(PracticeEvaluationDraft.model_json_schema(), ensure_ascii=False)}"
                ),
            },
            {"role": "user", "content": request.model_dump_json()},
        ]

        def validate(draft: PracticeEvaluationDraft) -> None:
            if draft.advisory is not True:
                raise ValueError("实训评价必须标记为建议性")

        return self._structured(messages, PracticeEvaluationDraft, validate)

    def analyze_feedback(self, request: FeedbackAdviceInput) -> FeedbackAdviceDraft:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是求职反馈分析器. 只输出JSON对象. 只能引用输入中的source_facts, "
                    "不得把拒绝自动归因于能力不足. "
                    f"输出必须符合JSON Schema: {json.dumps(FeedbackAdviceDraft.model_json_schema(), ensure_ascii=False)}"
                ),
            },
            {"role": "user", "content": request.model_dump_json()},
        ]
        allowed = set(request.source_facts)

        def validate(draft: FeedbackAdviceDraft) -> None:
            if not set(draft.source_facts).issubset(allowed):
                raise ValueError("反馈建议引用了未记录事实")

        return self._structured(messages, FeedbackAdviceDraft, validate)

    def _structured(
        self,
        messages: list[dict[str, str]],
        schema: type[ContractT],
        validator: Callable[[ContractT], None],
        *,
        max_tokens: int | None = None,
    ) -> ContractT:
        raw = self._request(messages, max_tokens=max_tokens)
        try:
            draft = schema.model_validate(json.loads(raw))
            validator(draft)
            return draft
        except (json.JSONDecodeError, ValidationError, ValueError) as error:
            repair_messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        "上一次输出无法通过结构校验. 请修复并只输出完整 JSON对象. "
                        f"校验错误: {error}"
                    ),
                },
            ]
            repaired = self._request(repair_messages, max_tokens=max_tokens)
            try:
                draft = schema.model_validate(json.loads(repaired))
                validator(draft)
                return draft
            except (json.JSONDecodeError, ValidationError, ValueError) as repair_error:
                raise ProviderError(
                    "invalid_model_output",
                    "模型输出经过一次修复后仍不符合结构合同",
                ) from repair_error

    def _request(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "reasoning_effort": "low",
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    raise ProviderError(
                        "model_temporarily_unavailable",
                        f"模型服务返回 HTTP {response.status_code}",
                        retryable=True,
                    )
                response.raise_for_status()
                body = response.json()
                content = body["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ProviderError("invalid_model_response", "模型响应缺少文本内容")
                return content.strip()
            except (httpx.TransportError, ProviderError) as error:
                last_error = error
                retryable = not isinstance(error, ProviderError) or error.retryable
                if not retryable or attempt == 2:
                    break
                time.sleep(0.05 * (attempt + 1))
            except (httpx.HTTPStatusError, KeyError, IndexError, TypeError, ValueError) as error:
                raise ProviderError("invalid_model_response", "模型服务返回无效响应") from error
        if isinstance(last_error, ProviderError):
            raise last_error
        raise ProviderError(
            "model_temporarily_unavailable",
            "模型服务暂时不可用",
            retryable=True,
        ) from last_error
