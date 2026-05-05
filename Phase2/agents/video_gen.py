"""
agents/video_gen.py — Video Generation Agent
─────────────────────────────────────────────
Role    : Generates visual frames for each scene from location + visual cues
MCP     : query_stock_footage, commit_memory
Rubric  : Video Quality / Visual Coherence (20 marks)
Note    : Runs in PARALLEL with voice_synth_node
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import GraphState
from memory_store import is_completed
from mcp_tools import mcp


def video_gen_node(state: dict) -> dict:
    """
    Agent 3 — Video Generation (runs in parallel with voice_synth_node)
    Generates frame sequences for the scene.
    Passes the frames_dir forward to face_swap_node.
    """
    scene = state["scene"]
    sid   = scene["scene_id"]

    print(f"\n  ┌─ AGENT 3 · VIDEO GEN    [Scene {sid}]")

    # ── Resumability check ──────────────────────────────────────
    mem_key = f"video_gen_scene_{sid}"
    if is_completed(mem_key):
        print(f"  │  [MEMORY] Already done — skipping scene {sid}")
        return {
            "errors": [],
            "_face_swap_input": {"scene": scene, "frames_dir": f"frames/scene_{sid}"}
        }

    location   = scene.get("location", "Unknown")
    characters = scene.get("characters", [])
    dialogues  = scene.get("dialogue", [])

    # Build a combined visual cue for the scene
    all_cues = " | ".join([d.get("visual_cue", "") for d in dialogues])

    # Estimate scene duration from dialogue count (2 seconds per line minimum)
    duration = max(len(dialogues) * 3, 4)

    print(f"  │  Location: {location}")
    print(f"  │  Duration: {duration}s at 24fps = {duration * 24} frames")

    # ── MCP Tool: query_stock_footage ──────────────────────────
    result = mcp.call("query_stock_footage", {
        "scene_id":   sid,
        "location":   location,
        "visual_cue": all_cues,
        "duration":   duration,
        "fps":        24,
    })

    frames_dir = result["frames_dir"]

    # ── MCP Tool: commit_memory ─────────────────────────────────
    mcp.call("commit_memory", {"key": mem_key,                         "value": "completed"})
    mcp.call("commit_memory", {"key": f"frames_dir_scene_{sid}",       "value": frames_dir})
    mcp.call("commit_memory", {"key": f"scene_duration_{sid}",         "value": duration})

    print(f"  └─ [VIDEO GEN] Scene {sid} frames → {frames_dir}/")

    # Pass scene + frames_dir to the face_swap_node
    return {
        "errors": [],
        "_face_swap_input": {"scene": scene, "frames_dir": frames_dir}
    }
