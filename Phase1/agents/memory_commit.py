# agents/memory_commit.py
# Memory Commit Agent — saves all outputs to ChromaDB and writes final JSON files

import json
import os
from state import GraphState
from mcp.tools import mcp_registry


def memory_commit_agent(state: GraphState) -> GraphState:  #Final agent in the pipeline.1. Saves script and character data to ChromaDB via MCP 2. Writes scene_manifest.json to outputs/ 3. Writes character_db.json to outputs/
    print("\n" + "="*50)
    print("MEMORY COMMIT AGENT — Starting")
    print("="*50)

    os.makedirs("outputs", exist_ok=True)
    commit_tool = mcp_registry.discover("commit_memory")

    # 1. Commit full script to memory
    script = state.get("script", {})
    if script:
        commit_tool(key="scene_manifest", data=script)

        # Write scene_manifest.json
        manifest_path = "outputs/scene_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        print(f"[MemoryCommit] scene_manifest.json saved.")

    # 2. Commit characters to memory
    characters = state.get("characters", [])
    images = state.get("images", [])

    # Build character_db — merge character profiles with their image paths
    character_db = []
    for char in characters:
        char_record = dict(char)
        # Find matching image
        for img in images:
            if img["character_id"] == char.get("id"):
                char_record["image_path"] = img["file_path"]
                char_record["image_prompt"] = img["prompt_used"]
                break
        character_db.append(char_record)

    if character_db:
        commit_tool(key="character_db", data={"characters": character_db})

        # Write character_db.json
        char_db_path = "outputs/character_db.json"
        with open(char_db_path, "w", encoding="utf-8") as f:
            json.dump({"characters": character_db}, f, indent=2, ensure_ascii=False)
        print(f"[MemoryCommit] character_db.json saved.")

    state["memory_committed"] = True
    state["status"] = "completed"

    print(f"\n[MemoryCommit] All outputs committed.")
    print(f"   → outputs/scene_manifest.json")
    print(f"   → outputs/character_db.json")
    print(f"   → outputs/images/ ({len(images)} image(s))")

    return state