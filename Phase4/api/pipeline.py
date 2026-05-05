"""
api/pipeline.py — Pipeline Runner
───────────────────────────────────
Runs each phase in a background thread and streams
progress events to WebSocket clients.

Progress event format (JSON):
{
  "phase":   1,
  "status":  "running",   # pending | running | done | error
  "message": "...",
  "percent": 40,
}
"""

import os
import sys
import asyncio
import threading
import subprocess
from pathlib import Path
from typing import Callable

# Force UTF-8 output in all subprocesses (fixes Windows cp1252 UnicodeEncodeError)
UTF8_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

# ── Absolute paths to each phase ─────────────────────────────────────────
PHASE1_DIR    = r"C:\Users\H.A.R\Desktop\Agentic_Ass_3"
PHASE1_PY     = r"C:\Users\H.A.R\Desktop\Agentic_Ass_3\venv\Scripts\python.exe"
PHASE1_SCRIPT = r"C:\Users\H.A.R\Desktop\Agentic_Ass_3\main.py"
PHASE1_OUTPUT = r"C:\Users\H.A.R\Desktop\Agentic_Ass_3\scene_manifest.json"

PHASE2_DIR    = r"C:\Users\H.A.R\Desktop\Agentic_Assignment_4"
PHASE2_PY     = r"C:\Users\H.A.R\Desktop\Agentic_Assignment_4\venv\Scripts\python.exe"
PHASE2_SCRIPT = r"C:\Users\H.A.R\Desktop\Agentic_Assignment_4\main.py"
PHASE2_OUTPUT = r"C:\Users\H.A.R\Desktop\Agentic_Assignment_4\raw_scenes"

PHASE3_DIR    = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3"
PHASE3_PY     = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3\venv\Scripts\python.exe"
PHASE3_SCRIPT = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3\phase3_main.py"
PHASE3_OUTPUT = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase3\final_output.mp4"

PHASE5_DIR    = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase5"
PHASE5_PY     = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase5\venv\Scripts\python.exe"
PHASE5_SCRIPT = r"C:\Users\H.A.R\Desktop\Agentic_Project_Phase5\phase5_main.py"


class PipelineRunner:
    def __init__(self):
        self.phases = {
            1: {"name": "Story & Script",   "status": "pending", "percent": 0,   "message": ""},
            2: {"name": "Audio Generation", "status": "pending", "percent": 0,   "message": ""},
            3: {"name": "Video Composition","status": "pending", "percent": 0,   "message": ""},
            4: {"name": "Web Interface",    "status": "done",    "percent": 100, "message": "Running"},
            5: {"name": "Edit & Undo Agent","status": "pending", "percent": 0,   "message": ""},
        }
        self.prompt        = ""
        self.final_video   = ""
        self.running_phase = None
        self._lock         = threading.Lock()
        self._progress_cb  = None
        self._loop         = None   # set by main.py on startup

    def set_progress_callback(self, cb: Callable):
        self._progress_cb = cb

    def _emit(self, phase: int, status: str, message: str, percent: int):
        with self._lock:
            self.phases[phase]["status"]  = status
            self.phases[phase]["message"] = message
            self.phases[phase]["percent"] = percent

        event = {"phase": phase, "status": status, "message": message, "percent": percent}

        if self._progress_cb and self._loop:
            try:
                asyncio.run_coroutine_threadsafe(self._progress_cb(event), self._loop)
            except Exception:
                pass

    # ── Public ───────────────────────────────────────────────────────────
    def run_phase(self, phase_num: int, prompt: str = ""):
        if self.running_phase == phase_num:
            return
        if prompt:
            self.prompt = prompt

        thread = threading.Thread(
            target=self._execute_phase,
            args=(phase_num,),
            daemon=True,
        )
        thread.start()

    def _execute_phase(self, phase_num: int):
        self.running_phase = phase_num
        try:
            {
                1: self._run_phase1,
                2: self._run_phase2,
                3: self._run_phase3,
                5: self._run_phase5,
            }.get(phase_num, lambda: None)()
        finally:
            self.running_phase = None

    # ── Phase 1 — Story & Script ─────────────────────────────────────────
    def _run_phase1(self):
        self._emit(1, "running", "Generating story and script...", 10)
        try:
            # Write prompt so Phase 1 can read it
            prompt_file = os.path.join(PHASE1_DIR, "user_prompt.txt")
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(self.prompt)

            self._emit(1, "running", "LLM generating scenes...", 40)

            result = subprocess.run(
                [PHASE1_PY, PHASE1_SCRIPT],
                cwd=PHASE1_DIR,
                capture_output=True, text=True, timeout=None,
                encoding="utf-8", env=UTF8_ENV
            )

            if result.returncode == 0 and os.path.exists(PHASE1_OUTPUT):
                self._emit(1, "done", "Script generated ✓", 100)
            else:
                err = result.stderr[-400:] if result.stderr else "Unknown error"
                self._emit(1, "error", f"Failed: {err}", 0)

        except Exception as e:
            self._emit(1, "error", str(e), 0)

    # ── Phase 2 — Audio Generation ───────────────────────────────────────
    def _run_phase2(self):
        self._emit(2, "running", "Starting audio generation...", 5)
        try:
            if not os.path.exists(PHASE1_OUTPUT):
                self._emit(2, "error", "scene_manifest.json not found. Run Phase 1 first.", 0)
                return

            self._emit(2, "running", "Synthesizing voices and lip sync...", 20)

            result = subprocess.run(
                [PHASE2_PY, PHASE2_SCRIPT, "--fresh"],
                cwd=PHASE2_DIR,
                capture_output=True, text=True, timeout=600,
                encoding="utf-8", env=UTF8_ENV
            )

            raw_scenes_exist = (
                os.path.exists(PHASE2_OUTPUT) and
                any(f.endswith(".mp4") for f in os.listdir(PHASE2_OUTPUT))
            )

            if result.returncode == 0 and raw_scenes_exist:
                count = len([f for f in os.listdir(PHASE2_OUTPUT) if f.endswith(".mp4")])
                self._emit(2, "done", f"Audio & video done ✓ ({count} scenes)", 100)
            else:
                err = result.stderr[-400:] if result.stderr else "No output files produced"
                self._emit(2, "error", f"Failed: {err}", 0)

        except Exception as e:
            self._emit(2, "error", str(e), 0)

    # ── Phase 3 — Video Composition ──────────────────────────────────────
    def _run_phase3(self):
        self._emit(3, "running", "Generating AI scene backgrounds...", 5)
        try:
            if not os.path.exists(PHASE1_OUTPUT):
                self._emit(3, "error", "scene_manifest.json not found. Run Phase 1 first.", 0)
                return

            self._emit(3, "running", "Compositing scenes with transitions...", 30)

            result = subprocess.run(
                [PHASE3_PY, PHASE3_SCRIPT],
                cwd=PHASE3_DIR,
                capture_output=True, text=True, timeout=900,
                encoding="utf-8", env=UTF8_ENV
            )

            if result.returncode == 0 and os.path.exists(PHASE3_OUTPUT):
                size = os.path.getsize(PHASE3_OUTPUT) / (1024 * 1024)
                self.final_video = PHASE3_OUTPUT
                self._emit(3, "done", f"Video ready ✓ ({size:.1f} MB)", 100)
            else:
                err = result.stderr[-400:] if result.stderr else "No output file produced"
                self._emit(3, "error", f"Failed: {err}", 0)

        except Exception as e:
            self._emit(3, "error", str(e), 0)

    # ── Phase 5 — Edit & Undo Agent ──────────────────────────────────────
    def _run_phase5(self):
        self._emit(5, "running", "Edit agent processing...", 20)
        try:
            result = subprocess.run(
                [PHASE5_PY, PHASE5_SCRIPT],
                cwd=PHASE5_DIR,
                capture_output=True, text=True, timeout=300,
                encoding="utf-8", env=UTF8_ENV
            )
            if result.returncode == 0:
                self._emit(5, "done", "Edit applied ✓", 100)
            else:
                err = result.stderr[-300:] if result.stderr else "Unknown error"
                self._emit(5, "error", f"Failed: {err}", 0)

        except Exception as e:
            self._emit(5, "error", str(e), 0)

    def get_state(self) -> dict:
        return {
            "prompt":        self.prompt,
            "final_video":   self.final_video,
            "running_phase": self.running_phase,
            "phases":        self.phases,
        }


# Singleton used by FastAPI
runner = PipelineRunner()