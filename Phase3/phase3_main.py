"""
phase3_main.py — Phase 3: Video Generation & Composition
──────────────────────────────────────────────────────────
Entry point for the Visual Layer.

Run:
    python phase3_main.py

Input  : scene_manifest.json  (Phase 1 output)
         raw_scenes/scene_XX.mp4 (Phase 2 output — characters + lip sync)
Output : final_output.mp4     (complete animated short film)
         scene_visuals/        (AI-generated background images)
         composed_scenes/      (per-scene composed videos)
"""

import json
import os
import sys
import time


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          PROJECT MONTAGE — PHASE 3: THE VISUAL LAYER         ║
║          Video Generation & Composition                       ║
║          CS-4015 Agentic AI                                   ║
╚══════════════════════════════════════════════════════════════╝
""")


def load_manifest(path: str = "scene_manifest.json") -> dict:
    if not os.path.exists(path):
        print(f"[ERROR] '{path}' not found. Run Phase 1 first.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def print_report(result: dict):
    print("\n" + "═" * 62)
    print("  PHASE 3 COMPLETE — FINAL REPORT")
    print("═" * 62)

    final = result.get("final_output", "")
    if final and os.path.exists(final):
        size = os.path.getsize(final) / (1024 * 1024)
        print(f"\n  ✓ Final video     : {final}  ({size:.1f} MB)")
    else:
        print(f"\n  ✗ Final video not found: {final}")

    composed = result.get("composed_scenes", [])
    print(f"\n  ✓ Composed scenes : {len(composed)}")
    for p in composed:
        sz = os.path.getsize(p) / 1024 if os.path.exists(p) else 0
        print(f"    → {p}  ({sz:.0f} KB)")

    images = result.get("scene_images", [])
    print(f"\n  ✓ Scene images    : {len(images)}")
    for p in images:
        print(f"    → {p}")

    errors = result.get("errors", [])
    if errors:
        print(f"\n  ⚠ Errors ({len(errors)}):")
        for e in errors:
            print(f"    ! {e}")
    else:
        print(f"\n  ✓ No errors.")

    print("\n" + "═" * 62)


def main():
    print_banner()

    manifest = load_manifest()
    scenes   = manifest.get("scenes", [])
    title    = manifest.get("title", "Untitled")

    print(f"  [MAIN] Title  : {title}")
    print(f"  [MAIN] Scenes : {len(scenes)}")

    # Create output directories
    for d in ["scene_visuals", "composed_scenes", "logs"]:
        os.makedirs(d, exist_ok=True)

    # Check Phase 2 outputs exist
    missing = []
    for scene in scenes:
        sid  = scene["scene_id"]
        path = f"raw_scenes/scene_{sid:02d}.mp4"
        if not os.path.exists(path):
            missing.append(path)

    if missing:
        print(f"\n  [WARN] Missing Phase 2 outputs:")
        for m in missing:
            print(f"    ! {m}")
        print("  [INFO] Phase 3 will generate visuals for missing scenes anyway.\n")
    else:
        print(f"  [MAIN] All Phase 2 outputs found ✓\n")

    # Run composition agent
    from agents.video_composer import compose_video

    start = time.time()
    print("  [MAIN] Starting video composition...\n")

    result = compose_video(scenes, title)

    elapsed = time.time() - start
    print(f"\n  [MAIN] Completed in {elapsed:.1f}s")
    print_report(result)


if __name__ == "__main__":
    main()
