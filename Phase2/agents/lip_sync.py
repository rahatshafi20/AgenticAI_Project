"""
agents/lip_sync.py — Lip Sync Agent (Fusion Layer)
────────────────────────────────────────────────────
Role    : For each dialogue line, animates ONLY the speaking character's face.
          Concatenates per-line clips into the final scene MP4.

CHANGES v2:
  - Reads per-line manifest from memory (set by voice_synth)
  - Runs Wav2Lip per line on the correct speaker's face image
  - Concatenates all per-line clips → final scene video
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory_store import commit_memory, get_memory, is_completed
from mcp_tools import mcp


def find_character_image(character: str) -> str:
    """Find character face image in image_assets/."""
    for name in [character, character.lower(), character.upper(), character.capitalize()]:
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
            path = f"image_assets/{name}{ext}"
            if os.path.exists(path):
                return path
    return ""


def _find_frames_for_scene(sid: int, state: dict) -> str:
    """Find the swapped frames directory for a scene."""
    # 1. Memory store (set by face_swap agent)
    path = get_memory(f"swapped_dir_scene_{sid}")
    if path and os.path.isdir(path):
        return path
    # 2. Filesystem check
    swapped = f"frames/scene_{sid}_swapped"
    if os.path.isdir(swapped) and len(os.listdir(swapped)) > 0:
        return swapped
    # 3. Original frames fallback
    original = f"frames/scene_{sid}"
    if os.path.isdir(original):
        print(f"  │  [WARN] Using unswapped frames for scene {sid}")
        return original
    return ""


def lip_sync_node(state: dict) -> dict:
    """
    Agent 5 — Lip Sync (Fusion Layer)
    Processes each dialogue line separately:
      speaker face image + line audio → Wav2Lip clip
    Then concatenates all clips → final scene MP4.
    """
    scene = state.get("scene", {})
    sid   = scene.get("scene_id", 0)

    # Fallback scene_id detection
    if not sid:
        for p in state.get("completed_audio", []) + state.get("completed_video", []):
            try:
                sid = int(p.split("scene_")[1].split("_")[0].split("/")[0])
                break
            except Exception:
                continue
    if not sid:
        sid = 1

    print(f"\n  ┌─ AGENT 5 · LIP SYNC     [Scene {sid}]")

    output_path = f"raw_scenes/scene_{sid:02d}.mp4"
    mem_key     = f"lip_sync_scene_{sid}"

    if is_completed(mem_key) and os.path.exists(output_path):
        print(f"  │  [MEMORY] Already done → {output_path}")
        return {"final_outputs": [output_path], "errors": []}

    # ── Get per-line manifest from memory (written by voice_synth) ─────
    manifest_json = get_memory(f"line_manifest_scene_{sid}")
    if manifest_json:
        try:
            line_manifest = json.loads(manifest_json)
        except Exception:
            line_manifest = []
    else:
        line_manifest = []

    # Fallback: build manifest from combined audio if per-line not available
    if not line_manifest:
        print(f"  │  [WARN] No per-line manifest for scene {sid} — using combined audio")
        combined_audio = get_memory(f"audio_path_scene_{sid}") or ""
        characters     = scene.get("characters", [])
        speaker        = characters[0] if characters else "Unknown"
        line_manifest  = [{"line_index": 0, "speaker": speaker, "audio_path": combined_audio}]

    # ── Get swapped frames dir (background + all character faces) ───────
    frames_dir = _find_frames_for_scene(sid, state)
    print(f"  │  Frames dir : {frames_dir or '[NOT FOUND]'}")
    print(f"  │  Lines      : {len(line_manifest)}")

    if not frames_dir:
        err = f"Lip Sync scene {sid}: no frames directory found"
        print(f"  └─ [ERROR] {err}")
        return {"final_outputs": [], "errors": [err]}

    # ── Build character image map ────────────────────────────────────────
    all_speakers = list({entry["speaker"] for entry in line_manifest})
    char_images  = {}
    for speaker in all_speakers:
        img = find_character_image(speaker)
        char_images[speaker] = img
        print(f"  │  {speaker}: {img or '[no image — placeholder]'}")

    # ── Run Wav2Lip per dialogue line ────────────────────────────────────
    final_mp4 = mcp.call("lip_sync_aligner", {
        "line_manifest":  line_manifest,   # [{speaker, audio_path, line_index}, ...]
        "char_images":    char_images,     # {speaker: image_path}
        "frames_dir":     frames_dir,      # background frames
        "scene_id":       sid,
        "fps":            24,
        "output_path":    output_path,
    })

    if not final_mp4:
        err = f"Lip Sync scene {sid}: lip_sync_aligner returned empty path"
        print(f"  └─ [ERROR] {err}")
        return {"final_outputs": [], "errors": [err]}

    mcp.call("commit_memory", {"key": mem_key,                  "value": "completed"})
    mcp.call("commit_memory", {"key": f"final_mp4_scene_{sid}", "value": final_mp4})

    print(f"  └─ [LIP SYNC] ✓ Scene {sid} → {final_mp4}")
    return {"final_outputs": [final_mp4], "errors": []}