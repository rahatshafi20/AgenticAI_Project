# LangGraph StateGraph — wires all agents together into a stateful workflow

from langgraph.graph import StateGraph, END

from state import GraphState
from agents.scriptwriter import scriptwriter_agent
from agents.validator import validator_agent
from agents.hitl import hitl_agent
from agents.character_designer import character_designer_agent
from agents.image_synthesizer import image_synthesizer_agent
from agents.memory_commit import memory_commit_agent


# ROUTING FUNCTIONS    (These decide which node to go to next based on the current state)

def route_by_mode(state: GraphState) -> str:        #Entry routing, decides whether to validate (manual) or generate (auto) based on input_mode.
    mode = state.get("input_mode", "auto")
    print(f"\n[Router] Input mode: '{mode}'")

    if mode == "manual":
        return "validator"
    else:
        return "scriptwriter"

def route_after_validation(state: GraphState) -> str:    # After validation — pass to HITL if valid, else end with errors.
    status = state.get("status", "")
    print(f"\n[Router] Validation status: '{status}'")

    if status == "validation_passed":
        return "hitl"
    else:
        print("[Router] Validation failed. Ending pipeline.")
        return END


def route_after_hitl(state: GraphState) -> str:     #After human review — proceed if approved, regenerate if rejected. Has a safety limit of 3 attempts to prevent infinite loops.
    approved = state.get("human_approved", False)
    attempts = state.get("script_generation_attempts", 0)
    print(f"\n[Router] Human approved: {approved} | Attempts so far: {attempts}")

    if approved:
        return "character_designer"
    elif attempts >= 3:
        print("[Router] Max regeneration attempts reached (3). Proceeding anyway.")
        return "character_designer"
    else:
        return "scriptwriter"


def route_after_scriptwriter(state: GraphState) -> str:         #After script generation — go to HITL for review, or end if there was an error.
    status = state.get("status", "")
    print(f"\n[Router] Scriptwriter status: '{status}'")

    if status == "script_generated":
        return "hitl"
    else:
        print("[Router] Script generation failed. Ending pipeline.")
        return END

# GRAPH BUILDER
def build_workflow():        #Constructs and compiles the full LangGraph StateGraph.
    graph = StateGraph(GraphState)

    #registering all nodes
    graph.add_node("mode_selector",      _mode_selector_node)
    graph.add_node("validator",          validator_agent)
    graph.add_node("scriptwriter",       scriptwriter_agent)
    graph.add_node("hitl",               hitl_agent)
    graph.add_node("character_designer", character_designer_agent)
    graph.add_node("image_synthesizer",  image_synthesizer_agent)
    graph.add_node("memory_commit",      memory_commit_agent)

    #set entry point
    graph.set_entry_point("mode_selector")

    #conditional edges
    graph.add_conditional_edges(
        "mode_selector",
        route_by_mode,
        {
            "validator":    "validator",
            "scriptwriter": "scriptwriter"
        }
    )

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "hitl": "hitl",
            END:    END
        }
    )

    graph.add_conditional_edges(
        "scriptwriter",
        route_after_scriptwriter,
        {
            "hitl": "hitl",
            END:    END
        }
    )

    graph.add_conditional_edges(
        "hitl",
        route_after_hitl,
        {
            "character_designer": "character_designer",
            "scriptwriter":       "scriptwriter"
        }
    )

    #Linear edges (no branching needed)
    graph.add_edge("character_designer", "image_synthesizer")
    graph.add_edge("image_synthesizer",  "memory_commit")
    graph.add_edge("memory_commit",       END)

    return graph.compile()


def _mode_selector_node(state: GraphState) -> GraphState:         #First node — just logs the mode and passes state through. Routing logic is handled by route_by_mode().
    print("\n" + "="*50)
    print("MODE SELECTOR — Starting pipeline")
    print("="*50)
    print(f"[ModeSelector] Mode: {state.get('input_mode', 'auto')}")
    print(f"[ModeSelector] Prompt: '{state.get('user_prompt', '')}'")
    state["status"] = "starting"
    return state