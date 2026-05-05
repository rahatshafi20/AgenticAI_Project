"""
agents/face_swap.py — Face Swap Agent
Positions ALL characters in a scene side by side in each frame.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory_store import is_completed
from mcp_tools import mcp


def find_character_image(character: str) -> str:
    """Search image_assets/ for any supported extension, any case."""
    for name in [character, character.lower(), character.upper()]:
        for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
            path = f"image_assets/{name}{ext}"
            if os.path.exists(path):
                print(f"  │  [IMAGE] Found: {path}")
                return path
    print(f"  │  [IMAGE] No image found for '{character}' — will use placeholder")
    return ""


def face_swap_node(state: dict) -> dict:
    face_input = state.get("_face_swap_input", {})
    scene      = face_input.get("scene", state.get("scene", {}))
    frames_dir = face_input.get("frames_dir", state.get("frames_dir", ""))
    sid        = scene.get("scene_id", 0)

    print(f"\n  ┌─ AGENT 4 · FACE SWAP    [Scene {sid}]")

    if not frames_dir or not os.path.isdir(frames_dir):
        err = f"Face Swap scene {sid}: frames_dir missing or empty"
        print(f"  └─ [ERROR] {err}")
        return {"completed_video": [], "errors": [err]}

    mem_key = f"face_swap_scene_{sid}"
    if is_completed(mem_key):
        print(f"  │  [MEMORY] Already done — skipping scene {sid}")
        return {"completed_video": [f"frames/scene_{sid}_swapped"], "errors": []}

    characters  = scene.get("characters", [])
    swapped_dir = frames_dir

    print(f"  │  Characters in scene: {characters}")

    # Process EACH character — pass index so they render side by side
    for idx, character in enumerate(characters):
        ref_path = find_character_image(character)

        print(f"  │  [{idx+1}/{len(characters)}] {character} → {ref_path or 'placeholder'}")

        # ── CRITICAL: identity_validator BEFORE face_swapper ────
        is_valid = mcp.call("identity_validator", {
            "character":      character,
            "reference_path": ref_path,
        })
        if not is_valid:
            print(f"  │  [SKIP] Validation failed for {character}")
            continue

        # ── face_swapper — now receives position info ────────────
        swapped_dir = mcp.call("face_swapper", {
            "frames_dir":     frames_dir,
            "character":      character,
            "reference_path": ref_path,
            "scene_id":       sid,
            "all_characters": characters,   # so tool knows total count
            "char_index":     idx,          # so tool knows this one's position
        })

    mcp.call("commit_memory", {"key": mem_key,                    "value": "completed"})
    mcp.call("commit_memory", {"key": f"swapped_dir_scene_{sid}", "value": swapped_dir})

    print(f"  └─ [FACE SWAP] Scene {sid} complete → {swapped_dir}/")
    return {"completed_video": [swapped_dir], "errors": []}