"""
api/edit_routes.py — Edit & Undo API Routes (Phase 5)
──────────────────────────────────────────────────────
Mount these routes in api/main.py with:
    from api.edit_routes import edit_router
    app.include_router(edit_router)

Endpoints:
  POST /api/edit              → run an edit command
  GET  /api/history           → version history list
  POST /api/revert/{version}  → revert to a version
  GET  /api/history/{version} → get state for a specific version
  POST /api/snapshot          → manually save a snapshot
"""

import sys
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import state_manager

edit_router = APIRouter()


class EditRequest(BaseModel):
    query: str


class SnapshotRequest(BaseModel):
    description: str
    state_json:  dict = {}


@edit_router.post("/api/edit")
async def run_edit_command(body: EditRequest, background_tasks: BackgroundTasks):
    """
    Run a free-text edit command through the edit agent.
    Runs in background so UI doesn't block.
    """
    if not body.query.strip():
        raise HTTPException(400, "Edit query cannot be empty")

    # Import here to avoid circular imports
    from agents.edit_agent import run_edit

    # Run edit in background thread (it can be slow)
    import asyncio
    import concurrent.futures

    loop     = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor()

    try:
        result = await loop.run_in_executor(executor, run_edit, body.query)
        return {
            "ok":      not bool(result.get("error")),
            "intent":  result.get("intent", {}),
            "result":  result.get("result", ""),
            "version": result.get("version", 0),
            "error":   result.get("error", ""),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@edit_router.get("/api/history")
async def get_history():
    """Return full version history for the version history UI panel."""
    return {"history": state_manager.history()}


@edit_router.post("/api/revert/{version}")
async def revert_to_version(version: int):
    """Revert pipeline state and assets to a previous version."""
    if version < 1:
        raise HTTPException(400, "Version must be >= 1")
    if version > state_manager.current():
        raise HTTPException(404, f"Version {version} does not exist")

    state = state_manager.revert(version)
    if not state:
        raise HTTPException(500, f"Revert to version {version} failed")

    return {
        "ok":      True,
        "version": version,
        "state":   state,
        "message": f"Reverted to version {version}",
    }


@edit_router.get("/api/history/{version}")
async def get_version_state(version: int):
    """Get state JSON for a specific version."""
    state = state_manager.get_state(version)
    if not state:
        raise HTTPException(404, f"Version {version} not found")
    return {"version": version, "state": state}


@edit_router.post("/api/snapshot")
async def manual_snapshot(body: SnapshotRequest):
    """Manually save a state snapshot."""
    version = state_manager.snapshot(
        description=body.description,
        state_json=body.state_json,
    )
    return {"ok": True, "version": version}
