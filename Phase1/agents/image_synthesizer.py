# Image Synthesizer Agent — generates visual portraits for each character

from state import GraphState
from mcp.tools import mcp_registry


def image_synthesizer_agent(state: GraphState) -> GraphState:    #takes character profiles and generates an AI portrait image for each. Uses Pollinations.ai via MCP ( no hardcoded image API calls). Saves images to outputs/images/ directory.
    print("\n" + "="*50)
    print("IMAGE SYNTHESIZER AGENT — Starting")
    print("="*50)

    characters = state.get("characters", [])

    if not characters:
        print("[ImageSynthesizer] ERROR: No characters found in state.")
        state["status"] = "error"
        state["error_message"] = "Image Synthesizer received empty character list."
        return state

    images = []

    # Discover image generation tool via MCP once
    image_tool = mcp_registry.discover("generate_character_image")

    for char in characters:
        name = char.get("name", "Unknown")
        char_id = char.get("id", "char_000")
        image_prompt = char.get(
            "image_generation_prompt",
            f"portrait of {name}, cinematic, detailed, photorealistic"
        )

        print(f"\n[ImageSynthesizer] Generating image for: {name}")
        print(f"   Prompt: {image_prompt[:80]}...")

        # Invoke via MCP — never call Pollinations directly
        file_path = image_tool(
            character_name=name,
            image_prompt=image_prompt,
            character_id=char_id
        )

        if file_path:
            record = {
                "character_id": char_id,
                "character_name": name,
                "prompt_used": image_prompt,
                "file_path": file_path
            }
            images.append(record)
            print(f"Saved to: {file_path}")
        else:
            print(f"Image generation failed for {name}")

    state["images"] = images
    state["status"] = "images_generated"

    print(f"\n[ImageSynthesizer] Generated {len(images)}/{len(characters)} images successfully.")

    return state