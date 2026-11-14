"""FastAPI application implementing api/openapi.yaml. Stateless."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from analog_compass import kb, service
from analog_compass.api import geojson, serialize
from analog_compass.settings import get_settings


class CompareRequest(BaseModel):
    target_id: str
    test_id: str
    site_ids: list[str] | None = None
    n_draws: int | None = Field(default=None, ge=1)


class Constraint(BaseModel):
    characteristic: str
    op: str  # "min" | "max"
    value: float
    required: bool = True
    weight: float | None = None


class DiscoverRequest(BaseModel):
    target_id: str
    test_id: str
    region_bbox: list[float] | None = None
    k: int = Field(default=10, ge=1)
    include_curated: bool = False
    n_draws: int | None = Field(default=None, ge=1)
    constraints: list[Constraint] | None = None


class SuitabilityRequest(BaseModel):
    site_id: str
    target_id: str | None = None
    n_draws: int | None = Field(default=None, ge=1)


class DataContributionRequest(BaseModel):
    name: str
    source_link: str
    measures: str
    characteristics: list[str] | None = None
    coverage: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


def create_app() -> FastAPI:
    app = FastAPI(title="Analog Compass API", version="0.1.0")
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        # Any localhost port is allowed in dev (Vite/Next use varied ports).
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return service.health()

    @app.get("/targets")
    def targets() -> list[dict[str, Any]]:
        return kb.list_targets()

    @app.get("/tests")
    def tests() -> list[dict[str, Any]]:
        return kb.list_tests()

    @app.get("/sites")
    def sites() -> list[dict[str, Any]]:
        return kb.list_sites()

    @app.post("/compare")
    def compare(req: CompareRequest) -> dict[str, Any]:
        try:
            result = service.run_compare(req.target_id, req.test_id, req.site_ids, req.n_draws)
        except KeyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return serialize.result_to_dict(result)

    @app.post("/discover")
    def discover(req: DiscoverRequest) -> dict[str, Any]:
        try:
            result = service.run_discover(
                req.target_id, req.test_id, req.region_bbox, req.k,
                req.include_curated, req.n_draws,
                constraints=[c.model_dump() for c in req.constraints] if req.constraints else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return serialize.result_to_dict(result)

    @app.post("/suitability")
    def suitability(req: SuitabilityRequest) -> dict[str, Any]:
        try:
            return service.run_suitability(req.site_id, req.target_id, req.n_draws)
        except KeyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/layers")
    def layers() -> dict[str, Any]:
        return kb.data_catalog()

    @app.get("/site_profile")
    def site_profile(site_id: str | None = None, grid_id: str | None = None) -> dict[str, Any]:
        try:
            return service.site_profile(site_id=site_id, grid_id=grid_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/data/contributions")
    def submit_contribution(req: DataContributionRequest) -> dict[str, Any]:
        return kb.review_contribution(req.model_dump())

    @app.get("/site_operations")
    def site_operations(site_id: str | None = None, grid_id: str | None = None,
                        target_id: str | None = None) -> dict[str, Any]:
        try:
            return service.site_operations(site_id=site_id, grid_id=grid_id, target_id=target_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/map.geojson")
    def map_geojson(req: CompareRequest) -> JSONResponse:
        try:
            result = service.run_compare(req.target_id, req.test_id, req.site_ids, req.n_draws)
        except KeyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return JSONResponse(content=geojson.to_feature_collection(result),
                            media_type="application/geo+json")

    @app.post("/agent/chat")
    async def agent_chat(req: ChatRequest):  # type: ignore[no-untyped-def]
        if not get_settings().anthropic_api_key:
            raise HTTPException(status_code=503, detail="Agent not configured (ANTHROPIC_API_KEY).")
        from sse_starlette.sse import EventSourceResponse

        from analog_compass.agent.runtime import stream_chat

        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        return EventSourceResponse(stream_chat(messages))

    return app


app = create_app()
