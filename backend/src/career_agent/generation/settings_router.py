from typing import Never, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from career_agent.generation.model_settings import (
    ModelSettingsError,
    list_available_models,
    save_model_settings,
    test_model_connection,
)
from career_agent.settings import Settings

router = APIRouter(prefix="/api/model-settings", tags=["model-settings"])


class ModelConnectionInput(BaseModel):
    base_url: str
    api_key: str | None = None


class ModelSettingsInput(ModelConnectionInput):
    model: str


class ModelSettingsView(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key_configured: bool


class ModelListView(BaseModel):
    items: list[str]


class ModelTestView(BaseModel):
    status: str
    model: str
    latency_ms: int


def _settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def _view(settings: Settings) -> ModelSettingsView:
    return ModelSettingsView(
        provider=settings.provider,
        base_url=settings.model_base_url,
        model=settings.model_name,
        api_key_configured=bool(settings.model_api_key),
    )


def _raise_http(error: ModelSettingsError) -> Never:
    status_by_code = {
        "invalid_model_base_url": 422,
        "model_api_key_required": 422,
        "model_name_required": 422,
        "model_service_auth_failed": 401,
        "model_service_request_failed": 502,
        "invalid_model_response": 502,
        "model_service_unavailable": 503,
        "model_service_unreachable": 503,
        "model_settings_write_failed": 500,
    }
    raise HTTPException(
        status_code=status_by_code.get(error.code, 500),
        detail={"code": error.code},
    ) from error


@router.get("", response_model=ModelSettingsView)
def read_model_settings(request: Request) -> ModelSettingsView:
    return _view(_settings(request))


@router.put("", response_model=ModelSettingsView)
def update_model_settings(payload: ModelSettingsInput, request: Request) -> ModelSettingsView:
    settings = _settings(request)
    try:
        save_model_settings(settings, payload.base_url, payload.api_key, payload.model)
    except ModelSettingsError as error:
        _raise_http(error)
    return _view(settings)


@router.post("/models", response_model=ModelListView)
def read_available_models(payload: ModelConnectionInput, request: Request) -> ModelListView:
    try:
        return ModelListView(items=list_available_models(
            _settings(request), payload.base_url, payload.api_key
        ))
    except ModelSettingsError as error:
        _raise_http(error)


@router.post("/test", response_model=ModelTestView)
def test_selected_model(payload: ModelSettingsInput, request: Request) -> ModelTestView:
    try:
        result = test_model_connection(
            _settings(request),
            payload.base_url,
            payload.api_key,
            payload.model,
        )
    except ModelSettingsError as error:
        _raise_http(error)
    return ModelTestView.model_validate(result)
