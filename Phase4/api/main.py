"""
api/main.py — FastAPI Backend (Phase 4)
────────────────────────────────────────
Endpoints:
  GET  /                        → serves React frontend
  POST /api/run/all             → run phases 1→2→3 sequentially
  POST /api/run/{phase}         → start a single phase
  POST /api/prompt              → set user prompt
  GET  /api/state               → current pipeline state
  GET  /api/video               → download final_output.mp4
  GET  /api/video/stream        → stream video for browser preview
  WS   /ws                      → real-time progress stream

Run:
  uvicorn api.main:app --reload --port 8000
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Project root
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from api.pipeline import runner

app = FastAPI(title="Project Montage API", version="1.0")

# Allow React dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket connection manager ──────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


async def progress_callback(event: dict):
    await manager.broadcast(event)


# ── Capture the event loop once at startup and give it to the runner ──────
@app.on_event("startup")
async def startup():
    loop = asyncio.get_running_loop()
    runner._loop = loop
    runner.set_progress_callback(progress_callback)


# ── WebSocket endpoint ────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_text(json.dumps({
            "type":  "init",
            "state": runner.get_state(),
        }))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── REST endpoints ────────────────────────────────────────────────────────

class PromptRequest(BaseModel):
    prompt: str


@app.post("/api/prompt")
async def set_prompt(body: PromptRequest):
    runner.prompt = body.prompt
    return {"ok": True, "prompt": body.prompt}


# IMPORTANT: /api/run/all must be defined BEFORE /api/run/{phase}
# otherwise FastAPI matches "all" as the phase integer and throws 422
@app.post("/api/run/all")
async def run_all():
    """Run phases 1 → 2 → 3 sequentially."""
    if runner.running_phase is not None:
        raise HTTPException(409, "A phase is already running")

    async def _run_sequential():
        for phase in [1, 2, 3]:
            runner.run_phase(phase, runner.prompt)
            while runner.running_phase == phase:
                await asyncio.sleep(1)

    asyncio.create_task(_run_sequential())
    return {"ok": True, "message": "Full pipeline started"}


@app.post("/api/run/{phase}")
async def run_phase(phase: int):
    """Trigger a single pipeline phase (1-5)."""
    if phase not in range(1, 6):
        raise HTTPException(400, "Phase must be 1-5")
    if runner.running_phase is not None:
        raise HTTPException(409, f"Phase {runner.running_phase} is currently running")

    runner.run_phase(phase, runner.prompt)
    return {"ok": True, "phase": phase, "message": f"Phase {phase} started"}


@app.get("/api/state")
async def get_state():
    return runner.get_state()


@app.get("/api/video")
async def download_video():
    path = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3\final_output.mp4"
    if not os.path.exists(path):
        raise HTTPException(404, "final_output.mp4 not found. Run Phase 3 first.")
    return FileResponse(path, media_type="video/mp4", filename="final_output.mp4")


@app.get("/api/video/stream")
async def stream_video():
    path = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3\final_output.mp4"
    if not os.path.exists(path):
        raise HTTPException(404, "Video not found")
    return FileResponse(path, media_type="video/mp4")


@app.get("/api/scenes")
async def list_scenes():
    composed_dir = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3\composed_scenes"
    if not os.path.exists(composed_dir):
        return {"scenes": []}
    scenes = sorted([f for f in os.listdir(composed_dir) if f.endswith(".mp4")])
    return {"scenes": scenes}


@app.get("/api/health")
async def health():
    return {"status": "ok", "running_phase": runner.running_phase}


# ── Serve React build (production) ───────────────────────────────────────
frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")))

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dist, "index.html"))