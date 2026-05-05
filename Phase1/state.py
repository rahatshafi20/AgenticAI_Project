# Shared state definition for the Writers Room multi-agent system
# All agents read from and write to this single state object

from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    #The central shared state passed between all agents in the LangGraph workflow. Every field here is accessible by every agent.
    # --- Input ---
    input_mode: str    # "auto": user gave a prompt, Scriptwriter Agent generates the script, "manual": user provided their own script, Validator Agent checks it

    user_prompt: str    # The raw story idea from the user

    raw_script: Optional[Dict[str, Any]] #only used in manual mode — the user's uploaded script before validation

    # --- Script ---
    script: Optional[Dict[str, Any]]
    # The fully structured scene_manifest
    # Format:
    # {
    #   "title": "...",
    #   "scenes": [
    #     {
    #       "scene_id": 1,
    #       "location": "...",
    #       "characters": ["A", "B"],
    #       "action": "...",
    #       "dialogue": [
    #         {
    #           "speaker": "A",
    #           "line": "...",
    #           "visual_cue": "..."
    #         }
    #       ]
    #     }
    #   ]
    # }

    # --- Validation ---
    validation_errors: List[str]     # List of errors found by the Validator Agent. Empty list means validation passed

    # --- Human-in-the-Loop ---
    human_approved: bool     #true: human reviewed and approved the script, False: human rejected, system will regenerate

    human_feedback: str      # Optional feedback from human reviewer

    # --- Characters ---
    characters: List[Dict[str, Any]]
    # List of character profiles extracted by Character Designer Agent
    # Format per character:
    # {
    #   "id": "char_001",
    #   "name": "Elena",
    #   "personality_traits": ["brave", "stubborn", "loyal"],
    #   "appearance": "tall woman, red hair, early 30s, scar on left cheek",
    #   "style": "military uniform, worn boots",
    #   "role": "protagonist"
    # }

    # --- Images ---
    images: List[Dict[str, str]]
    # List of generated image records
    # Format per image:
    # {
    #   "character_id": "char_001",
    #   "character_name": "Elena",
    #   "prompt_used": "tall woman, red hair...",
    #   "file_path": "outputs/images/elena.jpg"
    # }

    # --- Memory ---
    memory_committed: bool     #true once Memory Commit Agent has saved everything to ChromaDB...

    # --- System Status ---
    status: str
    # Tracks current pipeline status for routing decisions
    # Possible values: starting, script_generated, validation_passed, validation_failed, awaiting_human_review, human_approved, human_rejected, characters_extracted, images_generated, completed, error

    error_message: str    #stores error details if something goes wrong

    # --- Retry Tracking ---
    script_generation_attempts: int    #counts how many times Scriptwriter has run. Prevents infinite loops if human keeps rejecting