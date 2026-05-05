# Entry point — runs the full Writers Room pipeline

import json
from state import GraphState
from workflow.graph import build_workflow


def get_initial_state(mode: str, prompt: str = "", raw_script: dict = None) -> GraphState:        #Builds the clean initial state for a pipeline run.
    return GraphState( input_mode=mode, user_prompt=prompt, raw_script=raw_script, script=None, validation_errors=[], human_approved=False, human_feedback="", characters=[], images=[], memory_committed=False, status="starting", error_message="", script_generation_attempts=0)

def print_final_summary(final_state: GraphState):      #prints a clean summary of what was produced.
    print("\n" + "="*50)
    print("PIPELINE COMPLETE — FINAL SUMMARY")
    print("="*50)
    print(f"Status          : {final_state.get('status')}")
    print(f"Title           : {final_state.get('script', {}).get('title', 'N/A')}")
    print(f"Scenes          : {len(final_state.get('script', {}).get('scenes', []))}")
    print(f"Characters      : {len(final_state.get('characters', []))}")
    print(f"Images generated: {len(final_state.get('images', []))}")
    print(f"Memory committed: {final_state.get('memory_committed', False)}")
    print("\nOutput files:")
    print("  → outputs/scene_manifest.json")
    print("  → outputs/character_db.json")
    for img in final_state.get("images", []):
        print(f"  → {img['file_path']}")


def run_auto_mode():        #run in autonomous script generation mode.
    print("\n" + "="*50)
    print("  THE WRITER'S ROOM — AUTO MODE")
    print("="*50)

    prompt = input("\nEnter your story idea: ").strip()
    if not prompt:
        prompt = "A young hacker discovers a government conspiracy and must expose the truth before being silenced"
        print(f"[Main] No prompt entered. Using default: '{prompt}'")

    initial_state = get_initial_state(mode="auto", prompt=prompt)

    print("\n[Main] Building LangGraph workflow...")
    workflow = build_workflow()

    print("[Main] Launching pipeline...\n")
    final_state = workflow.invoke(initial_state)

    print_final_summary(final_state)
    return final_state


def run_manual_mode():      #run in manual script injection mode.
    print("\n" + "="*50)
    print("  THE WRITER'S ROOM — MANUAL MODE")
    print("="*50)

    # Sample script for testing manual mode
    sample_script = {
        "title": "The Last Signal",
        "genre": "Sci-Fi Thriller",
        "scenes": [
            {
                "scene_id": 1,
                "location": "Abandoned radio tower, desert",
                "time_of_day": "NIGHT",
                "characters": ["Maya", "Dr. Chen"],
                "action": "Maya and Dr. Chen set up equipment to intercept an alien transmission.",
                "dialogue": [
                    {
                        "speaker": "Maya",
                        "line": "The signal is coming from sector seven. We need to act now.",
                        "visual_cue": "Close-up on Maya's tense face, red warning lights flashing"
                    },
                    {
                        "speaker": "Dr. Chen",
                        "line": "If we broadcast back, we reveal our location to everyone.",
                        "visual_cue": "Wide shot, Dr. Chen steps back from the console"
                    }
                ]
            },
            {
                "scene_id": 2,
                "location": "Underground bunker",
                "time_of_day": "DAY",
                "characters": ["Maya", "Dr. Chen", "Commander Ross"],
                "action": "The team analyzes the decoded alien message which contains a warning.",
                "dialogue": [
                    {
                        "speaker": "Commander Ross",
                        "line": "This changes everything we thought we knew.",
                        "visual_cue": "Extreme close-up on the decoded message on screen"
                    },
                    {
                        "speaker": "Maya",
                        "line": "We have 48 hours before they arrive. What do we do?",
                        "visual_cue": "Pull back to reveal the whole team looking at Maya"
                    }
                ]
            }
        ]
    }

    print("\n[Main] Using sample script for manual mode demonstration.")
    initial_state = get_initial_state(
        mode="manual",
        prompt="Manual script submission",
        raw_script=sample_script
    )

    print("[Main] Building LangGraph workflow...")
    workflow = build_workflow()

    print("[Main] Launching pipeline...\n")
    final_state = workflow.invoke(initial_state)

    print_final_summary(final_state)
    return final_state


if __name__ == "__main__":
    print("\n" + "="*50)
    print("   THE WRITER'S ROOM")
    print("   Autonomous Story & Image Generation")
    print("="*50)

    print("\nSelect mode:")
    print("  1 → Auto mode   (AI generates script from your prompt)")
    print("  2 → Manual mode (validate a pre-written script)")

    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        if choice == "1":
            run_auto_mode()
            break
        elif choice == "2":
            run_manual_mode()
            break
        else:
            print("Please enter 1 or 2.")