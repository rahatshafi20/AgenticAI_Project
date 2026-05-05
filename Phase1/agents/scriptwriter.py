#scriptwriter Agent — transforms user prompts into structured screenplays

from state import GraphState
from mcp.tools import mcp_registry


def scriptwriter_agent(state: GraphState) -> GraphState:       #Takes the user's raw prompt and generates a full structured screenplay. Communicates only through shared state. Invokes tools only through MCP registry — no direct API calls.
   
    print("\n" + "="*50)
    print("SCRIPTWRITER AGENT — Starting")
    print("="*50)

    # Track how many times we've attempted generation
    attempts = state.get("script_generation_attempts", 0) + 1
    state["script_generation_attempts"] = attempts

    prompt = state.get("user_prompt", "")
    feedback = state.get("human_feedback", "")

    # If human rejected and gave feedback, incorporate it
    if feedback and attempts > 1:
        enriched_prompt = f"{prompt}. Additional direction: {feedback}"
        print(f"[Scriptwriter] Attempt #{attempts} — incorporating feedback: '{feedback}'")
    else:
        enriched_prompt = prompt
        print(f"[Scriptwriter] Attempt #{attempts} — generating from prompt: '{prompt}'")

    try:
        # Discover and invoke tool via MCP — never call directly
        generate_tool = mcp_registry.discover("generate_script_segment")
        script = generate_tool(prompt=enriched_prompt, num_scenes=3)

        state["script"] = script
        state["status"] = "script_generated"
        state["error_message"] = ""

        print(f"[Scriptwriter] Script generated successfully!")
        print(f"[Scriptwriter] Title: '{script.get('title', 'Untitled')}'")
        print(f"[Scriptwriter] Scenes: {len(script.get('scenes', []))}")

    except Exception as e:
        print(f"[Scriptwriter] ERROR: {e}")
        state["status"] = "error"
        state["error_message"] = str(e)

    return state