# Tool implementations registered into the MCP Registry
# Agents never import these directly — they discover them via mcp_registry.discover()

import os
import json
import requests
from groq import Groq
from dotenv import load_dotenv
import chromadb

from mcp.registry import mcp_registry

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("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"))
MODEL = "llama-3.3-70b-versatile"

# Initialize ChromaDB
chroma_client = chromadb.Client()
memory_collection = chroma_client.get_or_create_collection("writers_room_memory")



# TOOL 1: generate_script_segment, (used by: Scriptwriter Agent)

def _generate_script_segment(prompt: str, num_scenes: int = 3) -> dict:     #calls the LLM to generate a structured multi-scene screenplay. returns a parsed JSON dict.
   
    system_prompt = """You are an expert Hollywood screenwriter.
Your job is to write structured screenplays in valid JSON format only.
Never return anything outside the JSON. No explanation, no markdown, no backticks.
Always return raw JSON that can be parsed directly."""

    user_prompt = f"""Write a {num_scenes}-scene screenplay based on this idea: "{prompt}"

Return ONLY this JSON structure with no extra text:
{{
  "title": "Story Title Here",
  "genre": "genre here",
  "scenes": [
    {{
      "scene_id": 1,
      "location": "specific location description",
      "time_of_day": "DAY or NIGHT",
      "characters": ["Character Name 1", "Character Name 2"],
      "action": "Brief description of what physically happens in this scene",
      "dialogue": [
        {{
          "speaker": "Character Name 1",
          "line": "What the character says",
          "visual_cue": "Camera or visual direction e.g. Close-up, tense expression"
        }},
        {{
          "speaker": "Character Name 2",
          "line": "Their response",
          "visual_cue": "Wide shot, character steps forward"
        }}
      ]
    }}
  ]
}}

Make sure:
- Each scene has at least 2 dialogue exchanges
- Visual cues are cinematic and specific
- Characters are consistent across scenes
- The story has a clear beginning, middle, and end"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=3000
    )

    raw = response.choices[0].message.content.strip()

    # Clean up common LLM formatting mistakes
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw output:\n{raw}")


mcp_registry.register(
    name="generate_script_segment",
    description="Generates a structured multi-scene screenplay from a user prompt using LLM",
    schema={"prompt": "str", "num_scenes": "int (default 3)"},
    handler=_generate_script_segment
)



# TOOL 2: validate_script_structure  (used by: Validator Agent)

def _validate_script_structure(script: dict) -> dict:    #validates that a script has all required fields. returns {"valid": bool, "errors": [list of error strings]}
  
    errors = []

    if "scenes" not in script:
        errors.append("Missing top-level 'scenes' key")
        return {"valid": False, "errors": errors}

    if not isinstance(script["scenes"], list) or len(script["scenes"]) == 0:
        errors.append("'scenes' must be a non-empty list")
        return {"valid": False, "errors": errors}

    for i, scene in enumerate(script["scenes"]):
        prefix = f"Scene {i+1}"

        if "scene_id" not in scene:
            errors.append(f"{prefix}: Missing 'scene_id'")
        if "location" not in scene or not scene["location"]:
            errors.append(f"{prefix}: Missing or empty 'location'")
        if "characters" not in scene or len(scene.get("characters", [])) == 0:
            errors.append(f"{prefix}: Missing or empty 'characters' list")
        if "action" not in scene or not scene["action"]:
            errors.append(f"{prefix}: Missing 'action' description")
        if "dialogue" not in scene or len(scene.get("dialogue", [])) == 0:
            errors.append(f"{prefix}: Missing or empty 'dialogue'")
        else:
            for j, line in enumerate(scene["dialogue"]):
                if "speaker" not in line:
                    errors.append(f"{prefix}, Dialogue {j+1}: Missing 'speaker'")
                if "line" not in line:
                    errors.append(f"{prefix}, Dialogue {j+1}: Missing 'line'")
                if "visual_cue" not in line:
                    errors.append(f"{prefix}, Dialogue {j+1}: Missing 'visual_cue'")

    return {"valid": len(errors) == 0, "errors": errors}


mcp_registry.register(
    name="validate_script_structure",
    description="Validates that a script JSON has all required structural fields",
    schema={"script": "dict"},
    handler=_validate_script_structure
)

# TOOL 3: extract_characters    (used by: Character Designer Agent)

def _extract_characters(script: dict) -> list:   #Uses LLM to extract and build rich character profiles from the script. Returns a list of character profile dicts.
   
    # Collect unique character names from all scenes
    names = set()
    for scene in script.get("scenes", []):
        for char in scene.get("characters", []):
            names.add(char)

    characters = []
    for idx, name in enumerate(names):
        prompt = f"""You are a character designer for a film production.
Based on this screenplay, create a detailed profile for the character "{name}".

Screenplay:
{json.dumps(script, indent=2)}

Return ONLY this JSON with no extra text:
{{
  "id": "char_{idx+1:03d}",
  "name": "{name}",
  "role": "protagonist or antagonist or supporting",
  "personality_traits": ["trait1", "trait2", "trait3"],
  "appearance": "detailed physical description for image generation: age, height, hair, eyes, skin, distinguishing features",
  "clothing": "specific clothing and style description",
  "image_generation_prompt": "a detailed, comma-separated prompt suitable for AI image generation of this character, photorealistic, portrait style"
}}"""

        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            profile = json.loads(raw)
            characters.append(profile)
        except json.JSONDecodeError:
            # Fallback profile if LLM misbehaves
            characters.append({
                "id": f"char_{idx+1:03d}",
                "name": name,
                "role": "unknown",
                "personality_traits": [],
                "appearance": f"a character named {name}",
                "clothing": "casual attire",
                "image_generation_prompt": f"portrait of {name}, cinematic, detailed, photorealistic"
            })

    return characters


mcp_registry.register(
    name="extract_characters",
    description="Extracts and builds rich character profiles from a screenplay using LLM",
    schema={"script": "dict"},
    handler=_extract_characters
)


# TOOL 4: generate_character_image, (Used by: Image Synthesizer Agent)


def _generate_character_image(character_name: str, image_prompt: str, character_id: str) -> str:    #Generates a character image using Pollinations.ai (free, no API key). Saves to outputs/images/ and returns the file path.
    
    os.makedirs("outputs/images", exist_ok=True)

    # Clean filename
    safe_name = character_name.lower().replace(" ", "_").replace("'", "")
    file_path = f"outputs/images/{safe_name}.jpg"

    # Pollinations.ai — free image generation via URL
    full_prompt = f"{image_prompt}, photorealistic, cinematic portrait, high quality, 8k"
    encoded_prompt = requests.utils.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&seed=42"

    try:
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=90)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"[Image] Generated: {file_path}")
                    return file_path
            except requests.exceptions.Timeout:
                print(f"[Image] Timeout on attempt {attempt+1}/3 for {character_name}. Retrying...")
            except Exception as e:
                print(f"[Image] Error: {e}")
                break

        print(f"[Image] Failed after 3 attempts for {character_name}")
        return ""
    except Exception as e:
        print(f"[Image] Outer error for {character_name}: {e}")
        return ""


mcp_registry.register(
    name="generate_character_image",
    description="Generates a character portrait image using Pollinations.ai and saves it locally",
    schema={"character_name": "str", "image_prompt": "str", "character_id": "str"},
    handler=_generate_character_image
)


# TOOL 5: commit_memory (Used by: Memory Commit Agent)


def _commit_memory(key: str, data: dict) -> bool:  #Saves data to ChromaDB vector store for persistent agent memory, returns true on success.
    
    try:
        text_repr = json.dumps(data)
        memory_collection.upsert(
            documents=[text_repr],
            ids=[key]
        )
        print(f"[Memory] Committed to ChromaDB: key='{key}'")
        return True
    except Exception as e:
        print(f"[Memory] Failed to commit '{key}': {e}")
        return False


mcp_registry.register(
    name="commit_memory",
    description="Persists data to ChromaDB vector store for agent memory continuity",
    schema={"key": "str", "data": "dict"},
    handler=_commit_memory
)

# TOOL 6: query_memory,  (Used by: Any agent that needs to recall past data)


def _query_memory(query: str, n_results: int = 3) -> list:    #Queries ChromaDB for relevant stored memories. returns a list of matching documents.
    try:
        results = memory_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results.get("documents", [[]])[0]
    except Exception as e:
        print(f"[Memory] Query failed: {e}")
        return []


mcp_registry.register(
    name="query_memory",
    description="Queries ChromaDB vector store to retrieve relevant past agent memories",
    schema={"query": "str", "n_results": "int (default 3)"},
    handler=_query_memory
)

print(f"\n[MCP] Registry initialized with {len(mcp_registry.list_tools())} tools.")
print(f"[MCP] Available tools: {mcp_registry.list_tools()}\n")