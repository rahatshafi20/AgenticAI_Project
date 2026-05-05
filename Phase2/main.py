"""
main.py — Phase 2: The Studio Floor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry point for the Video and Audio Synthesis Layer.

Run:
    python main.py              # Normal run
    python main.py --fresh      # Clear memory and start from scratch
    python main.py --resume     # Resume from last checkpoint (default)

Input  : scene_manifest.json   (from Phase 1)
Outputs: raw_scenes/scene_01.mp4, scene_02.mp4, ...
         audio/scene_*.wav
         frames/scene_*/
         logs/task_graph.json
"""

import json
import os
import sys
import time


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          PROJECT MONTAGE — PHASE 2: THE STUDIO FLOOR         ║
║          Video and Audio Synthesis Layer                      ║
║          CS-4015 Agentic AI                                   ║
╚══════════════════════════════════════════════════════════════╝
""")


def load_scene_manifest(path: str = "scene_manifest.json") -> dict:
    if not os.path.exists(path):
        print(f"[ERROR] '{path}' not found. Make sure Phase 1 output is present.")
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)


def print_final_report(final_state: dict):
    outputs = final_state.get("final_outputs", [])
    errors  = final_state.get("errors", [])

    print("\n" + "═" * 60)
    print("  PHASE 2 COMPLETE — FINAL REPORT")
    print("═" * 60)

    print(f"\n  ✓ Scenes Rendered : {len(outputs)}")
    for path in outputs:
        size = os.path.getsize(path) if os.path.exists(path) else 0
        print(f"    → {path}  ({size/1024:.1f} KB)")

    audio_files = [f for f in os.listdir("audio") if f.endswith(".wav")] if os.path.exists("audio") else []
    print(f"\n  ✓ Audio Files     : {len(audio_files)}")
    for af in sorted(audio_files):
        print(f"    → audio/{af}")

    print(f"\n  ✓ Task Graph Log  : logs/task_graph.json")
    print(f"  ✓ Memory Store    : memory_store.json")

    if errors:
        print(f"\n  ⚠ Errors ({len(errors)}):")
        for e in errors:
            print(f"    ! {e}")
    else:
        print(f"\n  ✓ No errors — all scenes processed successfully.")

    print("\n" + "═" * 60)


def main():
    print_banner()

    # ── CLI flags ──────────────────────────────────────────────
    fresh  = "--fresh"  in sys.argv
    resume = "--resume" in sys.argv or not fresh

    if fresh:
        from memory_store import clear_memory
        clear_memory()
        print("  [MAIN] Fresh run — memory cleared.\n")
    else:
        print("  [MAIN] Resumable run — will skip completed stages.\n")

    # ── Load Phase 1 output ────────────────────────────────────
    manifest = load_scene_manifest("scene_manifest.json")
    scenes   = manifest.get("scenes", [])
    print(f"  [MAIN] Loaded {len(scenes)} scenes from scene_manifest.json")

    # ── Create output directories ──────────────────────────────
    for d in ["audio", "frames", "raw_scenes", "logs", "image_assets"]:
        os.makedirs(d, exist_ok=True)

    # ── Build initial GraphState ───────────────────────────────
    initial_state = {
        "scenes":          scenes,
        "task_graph":      None,
        "completed_audio": [],
        "completed_video": [],
        "final_outputs":   [],
        "errors":          [],
    }

    # ── Import and run LangGraph workflow ─────────────────────
    from workflow import graph

    print("\n  [MAIN] Starting LangGraph workflow...\n")
    start_time = time.time()

    final_state = graph.invoke(initial_state)

    elapsed = time.time() - start_time
    print(f"\n  [MAIN] Workflow completed in {elapsed:.1f}s")

    # ── Final report ───────────────────────────────────────────
    print_final_report(final_state)


if __name__ == "__main__":
    main()
