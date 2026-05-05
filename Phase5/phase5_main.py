"""
phase5_main.py — Phase 5: Intelligent Edit & Undo System
──────────────────────────────────────────────────────────
CLI for testing the edit agent and state versioning system.

Usage:
    python phase5_main.py
    python phase5_main.py --test        # run all 10+ test queries
    python phase5_main.py --history     # show version history
    python phase5_main.py --revert 2   # revert to version 2
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.edit_agent import run_edit, classify_intent_local
from state_manager import state_manager


# 10+ test queries covering all intent types (rubric requirement)
TEST_QUERIES = [
    "Change the voice tone to whispered for scene 1",
    "Add background music to all scenes",
    "Make scene 2 darker",
    "Make scene 3 brighter by 40%",
    "Apply a sepia filter to scene 1",
    "Apply grayscale filter to all scenes",
    "Remove the subtitle from the video",
    "Speed up scene 2 by 1.5x",
    "Slow down scene 3",
    "Add fade in and fade out to the final video",
    "Change the character design for Alex",
    "Change the voice emotion to happy for scene 4",
    "Regenerate the script with a different story",
    "Add warm filter to scene 1",
]


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          PROJECT MONTAGE — PHASE 5: EDIT & UNDO AGENT        ║
║          Intelligent Edit System + State Versioning           ║
║          CS-4015 Agentic AI                                   ║
╚══════════════════════════════════════════════════════════════╝
""")


def run_tests():
    """Run all 10+ test queries and show classification results."""
    print("\n  RUNNING INTENT CLASSIFICATION TESTS")
    print("  " + "─" * 55)

    passed = 0
    for i, query in enumerate(TEST_QUERIES, 1):
        intent = classify_intent_local(query)
        status = "✓" if intent["intent"] != "unknown" else "?"
        if intent["intent"] != "unknown":
            passed += 1
        print(f"  {status} [{i:2d}] {query[:50]:<50}")
        print(f"        → intent={intent['intent']} | target={intent['target']} | scope={intent['scope']}")
        print()

    print(f"  Results: {passed}/{len(TEST_QUERIES)} queries classified")
    print()


def show_history():
    """Display full version history."""
    history = state_manager.history()
    if not history:
        print("  No versions saved yet. Run the pipeline first.")
        return

    print(f"\n  VERSION HISTORY ({len(history)} versions)")
    print("  " + "─" * 55)
    for v in history:
        print(f"  v{v['version']:03d}  [{v['timestamp'][:19]}]  {v['description']}")
        print(f"        intent={v['edit_intent']}  assets={v['asset_count']}")
        print()


def interactive_mode():
    """Interactive edit prompt."""
    print("  INTERACTIVE EDIT MODE")
    print("  Type edit commands in plain English.")
    print("  Commands: 'history' | 'revert <N>' | 'quit'\n")

    while True:
        try:
            query = input("  edit> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting.")
            break

        if not query:
            continue
        if query.lower() in ["quit", "exit", "q"]:
            break
        if query.lower() == "history":
            show_history()
            continue
        if query.lower().startswith("revert "):
            try:
                version = int(query.split()[1])
                state   = state_manager.revert(version)
                print(f"  ✓ Reverted to version {version}")
                print(f"  State: {json.dumps(state, indent=4)[:200]}...")
            except Exception as e:
                print(f"  Error: {e}")
            continue

        # Run the edit
        print()
        result = run_edit(query)
        if result.get("error"):
            print(f"  ✗ Error: {result['error']}")
        else:
            print(f"  ✓ Done: {result.get('result', '')}")
            print(f"  ✓ Saved as version v{result.get('version', '?')}")
        print()


def main():
    print_banner()

    parser = argparse.ArgumentParser()
    parser.add_argument("--test",    action="store_true", help="Run all test queries")
    parser.add_argument("--history", action="store_true", help="Show version history")
    parser.add_argument("--revert",  type=int,            help="Revert to version N")
    parser.add_argument("--edit",    type=str,            help="Run a single edit query")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.history:
        show_history()
    elif args.revert:
        state = state_manager.revert(args.revert)
        print(f"  ✓ Reverted to version {args.revert}")
    elif args.edit:
        result = run_edit(args.edit)
        print(f"  Result : {result.get('result', '')}")
        print(f"  Version: v{result.get('version', '?')}")
        if result.get("error"):
            print(f"  Error  : {result['error']}")
    else:
        # Default: interactive mode
        # First take a baseline snapshot
        if state_manager.current() == 0:
            state_manager.snapshot(
                description="Initial pipeline state (before any edits)",
                state_json={"phase": "initial"},
                asset_paths=_collect_current_assets(),
            )
            print("  [STATE] Baseline snapshot saved as v1\n")
        interactive_mode()


def _collect_current_assets():
    import os
    assets = []
    for folder, ext in [("raw_scenes", ".mp4"), ("audio", ".wav"),
                         ("composed_scenes", ".mp4"), ("scene_visuals", ".jpg")]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.endswith(ext):
                    assets.append(f"{folder}/{f}")
    if os.path.exists("final_output.mp4"):
        assets.append("final_output.mp4")
    return assets


if __name__ == "__main__":
    main()
