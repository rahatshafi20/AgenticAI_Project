# Script Validator Agent — validates manually uploaded scripts

from state import GraphState
from mcp.tools import mcp_registry


def validator_agent(state: GraphState) -> GraphState:        #Validates a manually provided script for correct structure., Used only in manual input mode. Rejects scripts that are missing required fields.

    print("\n" + "="*50)
    print("VALIDATOR AGENT — Starting")
    print("="*50)

    script = state.get("raw_script") or state.get("script")

    if not script:
        print("[Validator] ERROR: No script found to validate.")
        state["status"] = "validation_failed"
        state["validation_errors"] = ["No script provided for validation."]
        return state

    try:
        # Discover and invoke via MCP
        validate_tool = mcp_registry.discover("validate_script_structure")
        result = validate_tool(script=script)

        if result["valid"]:
            print("[Validator] Script passed all validation checks.")
            state["script"] = script
            state["validation_errors"] = []
            state["status"] = "validation_passed"
        else:
            print(f"[Validator] Script failed validation with {len(result['errors'])} error(s):")
            for err in result["errors"]:
                print(f"   - {err}")
            state["validation_errors"] = result["errors"]
            state["status"] = "validation_failed"

    except Exception as e:
        print(f"[Validator] ERROR: {e}")
        state["status"] = "error"
        state["error_message"] = str(e)

    return state