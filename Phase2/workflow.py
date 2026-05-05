"""
workflow.py — LangGraph Stateful Workflow (Phase 2)
────────────────────────────────────────────────────
Implements the parallel multi-agent execution architecture using:
  - StateGraph (shared state across all nodes)
  - Send() API  (true parallel fan-out to audio + video pipelines)

Graph topology:
  scene_parser_node
       │
       ├──(Send)──► voice_synth_node ──────────────────────────┐
       │                                                        ▼
       └──(Send)──► video_gen_node ──► face_swap_node ──► lip_sync_node ──► END
"""

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from state import GraphState
from agents.scene_parser import scene_parser_node, route_to_parallel
from agents.voice_synth   import voice_synth_node
from agents.video_gen     import video_gen_node
from agents.face_swap     import face_swap_node
from agents.lip_sync      import lip_sync_node


# ─────────────────────────────────────────────────────────────────────────────
# Wrapper nodes for parallel Send() targets
# LangGraph's Send() passes a custom dict to each node, not the full GraphState.
# These wrappers handle both Send()-style input and normal state input.
# ─────────────────────────────────────────────────────────────────────────────

def _voice_synth_wrapper(state: dict) -> dict:
    """Runs Voice Synth Agent; merges output into GraphState via Annotated[List, operator.add]."""
    result = voice_synth_node(state)
    return {
        "completed_audio": result.get("completed_audio", []),
        "errors":          result.get("errors", []),
    }


def _video_gen_wrapper(state: dict) -> dict:
    """Runs Video Gen Agent, then immediately chains to Face Swap Agent."""
    video_result = video_gen_node(state)
    face_input   = video_result.get("_face_swap_input", {})

    face_result  = face_swap_node(face_input if face_input else state)
    return {
        "completed_video": face_result.get("completed_video", []),
        "errors":          video_result.get("errors", []) + face_result.get("errors", []),
    }


def _lip_sync_aggregator(state: GraphState) -> dict:
    """
    Fusion Layer — called once all parallel tasks are done.
    Runs lip_sync for every scene using memory-stored paths.
    """
    from memory_store import get_memory

    scenes      = state.get("scenes", [])
    all_outputs = []
    all_errors  = []

    for scene in scenes:
        sid    = scene["scene_id"]
        result = lip_sync_node({
            "scene":           scene,
            "completed_audio": state.get("completed_audio", []),
            "completed_video": state.get("completed_video", []),
        })
        all_outputs.extend(result.get("final_outputs", []))
        all_errors.extend(result.get("errors", []))

    return {"final_outputs": all_outputs, "errors": all_errors}


# ─────────────────────────────────────────────────────────────────────────────
# Build the LangGraph StateGraph
# ─────────────────────────────────────────────────────────────────────────────

def build_workflow():
    builder = StateGraph(GraphState)

    # ── Add all nodes ──────────────────────────────────────────────────────
    builder.add_node("scene_parser_node", scene_parser_node)
    builder.add_node("voice_synth_node",  _voice_synth_wrapper)   # Audio Pipeline
    builder.add_node("video_gen_node",    _video_gen_wrapper)      # Video Pipeline (gen + swap)
    builder.add_node("lip_sync_node",     _lip_sync_aggregator)    # Fusion Layer

    # ── Entry point ────────────────────────────────────────────────────────
    builder.set_entry_point("scene_parser_node")

    # ── scene_parser → parallel fan-out via Send() API ────────────────────
    # route_to_parallel() returns [Send("voice_synth_node", ...), Send("video_gen_node", ...)]
    # for every scene — this is what makes it truly parallel
    builder.add_conditional_edges(
        "scene_parser_node",
        route_to_parallel,
        ["voice_synth_node", "video_gen_node"]  # allowed target nodes
    )

    # ── Both pipelines converge at lip_sync_node ───────────────────────────
    builder.add_edge("voice_synth_node", "lip_sync_node")
    builder.add_edge("video_gen_node",   "lip_sync_node")

    # ── lip_sync_node → END ────────────────────────────────────────────────
    builder.add_edge("lip_sync_node", END)

    return builder.compile()


# Compiled graph — imported by main.py
graph = build_workflow()
