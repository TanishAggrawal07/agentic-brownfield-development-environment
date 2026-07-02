"""
Agent Router (Phase 5) — Development Agent endpoints.

  POST /api/agent/develop          generate a proposed-change bundle
  GET  /api/agent/result/{plan_id} re-fetch a previously generated bundle
  GET  /api/agent/providers        list LLM providers and which is active

The agent only PROPOSES changes; nothing here writes to project files.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.services.agent_service import agent_service
from backend.routers.filesystem import get_project_root

logger = logging.getLogger(__name__)
router = APIRouter()


class DevelopRequest(BaseModel):
    request: str = Field(..., min_length=1, description="Natural-language dev request")


@router.post("/develop", summary="Generate a proposed change set for a dev request")
async def develop(body: DevelopRequest, project_root: str = Depends(get_project_root)):
    """
    Understand the request, select context, plan changes, generate code,
    produce diffs, and validate — without modifying any source files.
    """
    try:
        return agent_service.develop(body.request, project_root)
    except Exception as exc:
        logger.error(f"Agent develop failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/result/{plan_id}", summary="Fetch a previously generated change set")
async def get_result(plan_id: str):
    bundle = agent_service.get_result(plan_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"No result for plan_id: {plan_id}")
    return bundle


@router.get("/providers", summary="List available LLM providers")
async def providers():
    return {"providers": agent_service.providers()}
