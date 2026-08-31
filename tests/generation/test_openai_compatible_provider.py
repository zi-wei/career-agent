from __future__ import annotations

import json
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

import httpx
import pytest

from career_agent.generation.contracts import (
    MaterialGenerationInput,
    PlanGenerationInput,
    ProfileFactContext,
    RequirementContext,
)
from career_agent.generation.openai_compatible import (
    OpenAICompatibleProvider,
    ProviderNotConfigured,
)
from career_agent.settings import Settings


class ModelHandler(BaseHTTPRequestHandler):
    responses: ClassVar[deque[tuple[int, str]]] = deque()
    requests: ClassVar[list[dict[str, object]]] = []

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        type(self).requests.append(json.loads(self.rfile.read(length)))
        status, content = type(self).responses.popleft()
        payload = {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def model_server():
    ModelHandler.responses = deque()
    ModelHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def settings_for(server: ThreadingHTTPServer) -> Settings:
    return Settings(
        provider="openai-compatible",
        model_base_url=f"http://127.0.0.1:{server.server_port}/v1",
        model_api_key="test-model-secret",
        model_name="test-model",
        model_timeout_seconds=2,
    )


def valid_analysis() -> str:
    return json.dumps(
        {
            "requirements": [
                {
                    "label": "Docker",
                    "category": "container",
                    "evidence_text": "使用 Docker部署服务.",
                }
            ]
        },
        ensure_ascii=False,
    )


def test_provider_validates_structured_job_analysis(model_server) -> None:
    ModelHandler.responses.append((200, valid_analysis()))
    provider = OpenAICompatibleProvider(settings_for(model_server))

    result = provider.analyze_job("负责 Linux维护, 使用 Docker部署服务.")

    assert result.requirements[0].label == "Docker"
    assert ModelHandler.requests[0]["model"] == "test-model"
    assert "test-model-secret" not in json.dumps(ModelHandler.requests)


def test_provider_retries_transient_server_error(model_server) -> None:
    ModelHandler.responses.extend([(500, "{}"), (200, valid_analysis())])
    provider = OpenAICompatibleProvider(settings_for(model_server))

    result = provider.analyze_job("使用 Docker部署服务.")

    assert result.requirements[0].label == "Docker"
    assert len(ModelHandler.requests) == 2


def test_provider_retries_when_server_disconnects_before_response(
    model_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleProvider(settings_for(model_server))
    responses: deque[httpx.Response | Exception] = deque([
        httpx.RemoteProtocolError("server disconnected"),
        httpx.Response(
            200,
            json={"choices": [{"message": {"content": valid_analysis()}}]},
            request=httpx.Request("POST", "http://model.test/chat/completions"),
        ),
    ])

    def post(*args: object, **kwargs: object) -> httpx.Response:
        response = responses.popleft()
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(provider.client, "post", post)

    result = provider.analyze_job("使用 Docker部署服务.")

    assert result.requirements[0].label == "Docker"
    assert not responses


def test_provider_requests_one_structured_repair(model_server) -> None:
    ModelHandler.responses.extend([(200, "not-json"), (200, valid_analysis())])
    provider = OpenAICompatibleProvider(settings_for(model_server))

    result = provider.analyze_job("使用 Docker部署服务.")

    assert result.requirements[0].label == "Docker"
    assert len(ModelHandler.requests) == 2
    repair_messages = ModelHandler.requests[1]["messages"]
    assert "修复" in repair_messages[-1]["content"]


def test_provider_requires_server_side_configuration() -> None:
    settings = Settings(
        provider="openai-compatible",
        model_base_url="https://api.example.com/v1",
        model_api_key="",
        model_name="test-model",
    )

    with pytest.raises(ProviderNotConfigured) as error:
        OpenAICompatibleProvider(settings)

    assert error.value.code == "provider_not_configured"


def test_provider_generates_materials_with_allowed_source_refs(model_server) -> None:
    ModelHandler.responses.append(
        (
            200,
            json.dumps(
                {
                    "target_title": "Linux运维实习生",
                    "summary": "具备个人服务器部署经验.",
                    "sections": [
                        {
                            "kind": "project",
                            "title": "个人服务器",
                            "bullets": [
                                {
                                    "text": "使用 Docker部署 Nginx服务.",
                                    "source_refs": ["profile_fact:fact-1"],
                                }
                            ],
                        }
                    ],
                    "interview_title": "Linux运维实习生面试题",
                    "questions": [
                        {
                            "question": "如何排查 Docker容器无法访问?",
                            "category": "container",
                            "requirement_id": "req-1",
                            "evidence_text": "使用 Docker部署服务.",
                            "answer_guide": "按网络、端口和日志逐层排查.",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )
    )
    provider = OpenAICompatibleProvider(settings_for(model_server))
    request = MaterialGenerationInput(
        job_title="Linux运维实习生",
        company="示例科技",
        job_description="负责 Linux维护, 使用 Docker部署服务.",
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

    result = provider.generate_materials(request)

    assert result.sections[0].bullets[0].source_refs == ["profile_fact:fact-1"]
    assert result.questions[0].requirement_id == "req-1"
    system_prompt = ModelHandler.requests[0]["messages"][0]["content"]
    assert ModelHandler.requests[0]["reasoning_effort"] == "low"
    assert ModelHandler.requests[0]["max_tokens"] == 4096
    assert "专业中文针对性简历" in system_prompt
    assert "岗位关键词" in system_prompt
    assert "行动、技术和结果" in system_prompt
    assert "1到5个 section" in system_prompt
    assert "sections不得重复自我评价" in system_prompt
    assert "5到8道" in system_prompt
    assert "所有顶层字段" in system_prompt
    assert "不要输出 HTML" in system_prompt


def test_provider_normalizes_known_raw_fact_ids_in_material_source_refs(model_server) -> None:
    raw_materials = json.dumps(
        {
            "target_title": "Linux运维实习生",
            "summary": "具备个人服务器部署经验.",
            "sections": [
                {
                    "kind": "project",
                    "title": "个人服务器",
                    "bullets": [
                        {
                            "text": "使用 Docker部署 Nginx服务.",
                            "source_refs": ["fact-1"],
                        }
                    ],
                }
            ],
            "interview_title": "Linux运维实习生面试题",
            "questions": [
                {
                    "question": "如何排查 Docker容器无法访问?",
                    "category": "container",
                    "requirement_id": "req-1",
                    "evidence_text": "使用 Docker部署服务.",
                    "answer_guide": "按网络、端口和日志逐层排查.",
                }
            ],
        },
        ensure_ascii=False,
    )
    ModelHandler.responses.extend([(200, raw_materials), (200, raw_materials)])
    provider = OpenAICompatibleProvider(settings_for(model_server))
    request = MaterialGenerationInput(
        job_title="Linux运维实习生",
        company="示例科技",
        job_description="负责 Linux维护, 使用 Docker部署服务.",
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

    result = provider.generate_materials(request)

    assert result.sections[0].bullets[0].source_refs == ["profile_fact:fact-1"]
    assert len(ModelHandler.requests) == 1


def test_provider_repairs_materials_that_duplicate_summary_as_a_section(model_server) -> None:
    def materials(section_kind: str, section_title: str) -> str:
        return json.dumps(
            {
                "target_title": "Linux运维实习生",
                "summary": "具备个人服务器部署经验.",
                "sections": [
                    {
                        "kind": section_kind,
                        "title": section_title,
                        "bullets": [
                            {
                                "text": "使用 Docker部署 Nginx服务.",
                                "source_refs": ["profile_fact:fact-1"],
                            }
                        ],
                    }
                ],
                "interview_title": "Linux运维实习生面试题",
                "questions": [
                    {
                        "question": "如何排查 Docker容器无法访问?",
                        "category": "container",
                        "requirement_id": "req-1",
                        "evidence_text": "使用 Docker部署服务.",
                        "answer_guide": "按网络、端口和日志逐层排查.",
                    }
                ],
            },
            ensure_ascii=False,
        )

    ModelHandler.responses.extend([
        (200, materials("summary", "自我评价")),
        (200, materials("project", "项目经历")),
    ])
    provider = OpenAICompatibleProvider(settings_for(model_server))
    request = MaterialGenerationInput(
        job_title="Linux运维实习生",
        company="示例科技",
        job_description="负责 Linux维护, 使用 Docker部署服务.",
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

    result = provider.generate_materials(request)

    assert result.sections[0].kind == "project"
    assert len(ModelHandler.requests) == 2


def test_provider_plan_contains_only_selected_requirements(model_server) -> None:
    days = [
        {
            "day_number": index,
            "tasks": [
                {
                    "kind": "knowledge_drill",
                    "title": "Docker场景训练",
                    "objective": "完成容器网络故障分析.",
                    "estimated_minutes": 45,
                    "completion_condition": "提交排查步骤和复盘.",
                    "evidence_requirement": "一份排查记录.",
                    "requirement_id": "req-docker",
                    "guidance": {
                        "explanation": "Docker容器网络排查需要从现象和网络路径开始.",
                        "key_concepts": [
                            {"name": "端口映射", "explanation": "连接宿主机与容器端口."},
                            {"name": "容器网络", "explanation": "管理容器间和外部通信."},
                        ],
                        "scenario_question": "容器服务无法访问时如何排查?",
                        "answer_framework": ["确认现象", "检查配置和日志"],
                        "self_checks": ["能否解释端口映射?", "能否说明验证依据?"],
                    },
                }
            ],
        }
        for index in range(1, 15)
    ]
    ModelHandler.responses.append((200, json.dumps({"days": days}, ensure_ascii=False)))
    provider = OpenAICompatibleProvider(settings_for(model_server))
    request = PlanGenerationInput(
        job_title="Linux运维实习生",
        selected_requirements=[
            RequirementContext(
                id="req-docker",
                label="Docker",
                category="container",
                evidence_text="使用 Docker部署服务.",
            )
        ],
    )

    result = provider.generate_plan(request)

    assert len(result.days) == 14
    assert {
        task.requirement_id for day in result.days for task in day.tasks
    } == {"req-docker"}
