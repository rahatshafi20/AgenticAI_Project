"""
agents/voice_synth.py — Voice Synthesis Agent
──────────────────────────────────────────────
Role    : Generates gender-aware, emotion-aware speech per dialogue line
MCP     : voice_cloning_synthesizer, commit_memory

CHANGES v2:
  - Gender-aware voices: male → David voice, female → Zira voice (via pyttsx3)
  - Stores per-line manifest in memory so lip_sync animates the correct speaker
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory_store import commit_memory, is_completed
from mcp_tools import mcp


# ── Emotion map ────────────────────────────────────────────────────────────
EMOTION_MAP = {
    "urgent":     "urgent",
    "tense":      "urgent",
    "sad":        "sad",
    "reflective": "reflective",
    "emotional":  "sad",
    "happy":      "happy",
    "whisper":    "whisper",
    "angry":      "urgent",
    "hopeful":    "happy",
}

# ── Gender map — add your characters here ─────────────────────────────────
# Any character NOT listed is auto-detected by first name, then defaults male.
GENDER_MAP = {
    "Alex":        "male",
    "Ryan":        "male",
    "Professor":   "male",
    "Interviewer": "male",
    "Narrator":    "male",
}

# Common female first names for auto-detection fallback
FEMALE_NAMES = {
    "sarah", "emma", "emily", "sophia", "olivia", "ava", "isabella",
    "mia", "amelia", "harper", "evelyn", "abigail", "ella", "scarlett",
    "grace", "chloe", "victoria", "lily", "zoe", "nora", "luna",
    "layla", "hannah", "samantha", "leah", "zoey", "aria", "fatima",
    "ayesha", "zainab", "hira", "sana", "maria", "aisha",
}


def get_gender(character: str) -> str:
    if character in GENDER_MAP:
        return GENDER_MAP[character]
    first_name = character.split()[0].lower()
    return "female" if first_name in FEMALE_NAMES else "male"


def extract_emotion(visual_cue: str) -> str:
    cue_lower = visual_cue.lower()
    for keyword, emotion in EMOTION_MAP.items():
        if keyword in cue_lower:
            return emotion
    return "neutral"


def voice_synth_node(state: dict) -> dict:
    scene = state["scene"]
    sid   = scene["scene_id"]

    print(f"\n  ┌─ AGENT 2 · VOICE SYNTH  [Scene {sid}]")

    mem_key = f"voice_synth_scene_{sid}"
    if is_completed(mem_key):
        combined_path = f"audio/scene_{sid}_combined.wav"
        print(f"  │  [MEMORY] Already done → {combined_path}")
        return {"completed_audio": [combined_path], "errors": []}

    dialogues  = scene.get("dialogue", [])
    characters = scene.get("characters", [])
    wav_paths  = []
    line_manifest = []

    for i, line in enumerate(dialogues):
        speaker    = line.get("speaker", characters[0] if characters else "Narrator")
        text       = line.get("line", "")
        visual_cue = line.get("visual_cue", "")
        emotion    = extract_emotion(visual_cue)
        gender     = get_gender(speaker)
        output_path = f"audio/scene_{sid}_{speaker}_{i}.wav"

        print(f"  │  Line {i}: [{speaker}] gender={gender} emotion={emotion}")
        print(f"  │           \"{text[:50]}\"")

        wav = mcp.call("voice_cloning_synthesizer", {
            "text":        text,
            "scene_id":    sid,
            "speaker":     speaker,
            "emotion":     emotion,
            "gender":      gender,
            "output_path": output_path,
        })

        if wav and os.path.exists(wav):
            wav_paths.append(wav)
            line_manifest.append({
                "line_index": i,
                "speaker":    speaker,
                "audio_path": wav,
                "gender":     gender,
                "emotion":    emotion,
            })

    combined_path = _concatenate_audio(wav_paths, sid)

    # Store per-line manifest — lip_sync uses this to animate correct speaker
    mcp.call("commit_memory", {"key": mem_key,                       "value": "completed"})
    mcp.call("commit_memory", {"key": f"audio_path_scene_{sid}",     "value": combined_path})
    mcp.call("commit_memory", {"key": f"line_manifest_scene_{sid}",  "value": json.dumps(line_manifest)})

    print(f"  └─ [VOICE SYNTH] Scene {sid} → {len(line_manifest)} lines | combined: {combined_path}")
    return {"completed_audio": [combined_path], "errors": []}


def _concatenate_audio(wav_paths: list, scene_id: int) -> str:
    from moviepy.editor import AudioFileClip, concatenate_audioclips
    import shutil

    combined_path = f"audio/scene_{scene_id}_combined.wav"
    valid_paths   = [p for p in wav_paths if p and os.path.exists(p)]
    if not valid_paths:
        return ""
    if len(valid_paths) == 1:
        shutil.copy(valid_paths[0], combined_path)
        return combined_path

    clips    = [AudioFileClip(p) for p in valid_paths]
    combined = concatenate_audioclips(clips)
    combined.write_audiofile(combined_path, verbose=False, logger=None)
    for c in clips:
        c.close()
    combined.close()
    return combined_path