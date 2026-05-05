# Character Designer Agent — extracts and builds character profiles from the script

from state import GraphState
from mcp.tools import mcp_registry

def character_designer_agent(state: GraphState) -> GraphState:    #reads the approved script and builds a rich identity profile for each character. Profiles are used by Image Synthesizer and stored in character_db.json.
    print("\n" + "="*50)
    print("CHARACTER DESIGNER AGENT — Starting")
    print("="*50)

    script = state.get("script", {})

    if not script:
        print("[CharacterDesigner] ERROR: No script found in state.")
        state["status"] = "error"
        state["error_message"] = "Character Designer received empty script."
        return state

    try:
        # Discover and invoke via MCP
        extract_tool = mcp_registry.discover("extract_characters")
        characters = extract_tool(script=script)

        state["characters"] = characters
        state["status"] = "characters_extracted"

        print(f"[CharacterDesigner] Extracted {len(characters)} character profile(s):")
        for char in characters:
            print(f"   - {char.get('name')} ({char.get('role', 'unknown role')})")
            print(f"     Appearance: {char.get('appearance', '')[:80]}...")

        # Also commit each character to memory via MCP
        commit_tool = mcp_registry.discover("commit_memory")
        for char in characters:
            commit_tool(
                key=f"character_{char.get('id', char.get('name'))}",
                data=char
            )

    except Exception as e:
        print(f"[CharacterDesigner] ERROR: {e}")
        state["status"] = "error"
        state["error_message"] = str(e)

    return state