# Human-in-the-Loop Agent — checkpoint for human review before proceeding
import json
from state import GraphState

def hitl_agent(state: GraphState) -> GraphState:    #Pauses the pipeline and presents the generated script to the human. Waits for explicit approval or rejection before continuing.This prevents hallucinated or misaligned scripts from proceeding.
    print("\n" + "="*50)
    print("HUMAN-IN-THE-LOOP AGENT — Review Required")
    print("="*50)

    script = state.get("script", {})

    if not script:
        print("[HITL] No script to review. Skipping.")
        state["human_approved"] = False
        state["status"] = "error"
        state["error_message"] = "HITL received empty script."
        return state

    # Display the script to the human for review
    print("\n GENERATED SCRIPT FOR YOUR REVIEW:")
    print("-" * 40)
    print(f"Title  : {script.get('title', 'Untitled')}")
    print(f"Genre  : {script.get('genre', 'Unknown')}")
    print(f"Scenes : {len(script.get('scenes', []))}")
    print("-" * 40)

    for scene in script.get("scenes", []):
        print(f"\n Scene {scene.get('scene_id')} — {scene.get('location')} ({scene.get('time_of_day', '')})")
        print(f"   Characters : {', '.join(scene.get('characters', []))}")
        print(f"   Action     : {scene.get('action', '')}")
        print(f"   Dialogue:")
        for line in scene.get("dialogue", []):
            print(f"     [{line.get('speaker')}]: {line.get('line')}")
            print(f"      Visual cue: {line.get('visual_cue')}")

    print("\n" + "-" * 40)

    # Human review prompt
    while True:
        decision = input("\n Approve this script? (yes/no): ").strip().lower()

        if decision in ["yes", "y"]:
            state["human_approved"] = True
            state["human_feedback"] = ""
            state["status"] = "human_approved"
            print("[HITL] Script approved. Proceeding to character design.")
            break

        elif decision in ["no", "n"]:
            feedback = input("💬 Enter feedback for improvement (or press Enter to skip): ").strip()
            state["human_approved"] = False
            state["human_feedback"] = feedback
            state["status"] = "human_rejected"
            print(f"[HITL] Script rejected. Sending back to Scriptwriter.")
            if feedback:
                print(f"[HITL] Feedback recorded: '{feedback}'")
            break

        else:
            print("   Please type 'yes' or 'no'.")

    return state