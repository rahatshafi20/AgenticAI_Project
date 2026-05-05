"""
mcp_tools.py - MCP Tool Registry and Implementations

CHANGES v3:
  [1] voice_cloning_synthesizer: uses pyttsx3 for gender-aware voices
      (male → David, female → Zira on Windows)
  [2] lip_sync_aligner: processes each dialogue line individually
      - animates ONLY the speaking character's face per line
      - concatenates all per-line clips into final scene MP4
  [3] All Wav2Lip paths are absolute (fixes "not a valid path" error)
  [4] _lip_sync_aligner and _av_merge_fallback correctly inside class
  [5] face_swapper erases slot before drawing (no ghost characters)
  [6] query_stock_footage has no pre-drawn placeholder body
"""

import os
import json
from pathlib import Path
from typing import Any
import threading
_pyttsx3_lock = threading.Lock()
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})
# Path to wav2lip_env Python 3.10 — CHANGE THIS if project is elsewhere
WAV2LIP_PYTHON = str(
    Path(__file__).parent / "wav2lip_env" / "Scripts" / "python.exe"
)


class MCPClient:

    def __init__(self):
        self._registry = {
            "get_task_graph":            self._get_task_graph,
            "commit_memory":             self._commit_memory_tool,
            "voice_cloning_synthesizer": self._voice_cloning_synthesizer,
            "query_stock_footage":       self._query_stock_footage,
            "identity_validator":        self._identity_validator,
            "face_swapper":              self._face_swapper,
            "lip_sync_aligner":          self._lip_sync_aligner,
            "generate_scene_image":      self._generate_scene_image,
            "compose_scene":             self._compose_scene,
            "concat_with_transitions":   self._concat_with_transitions,

        }

    def call(self, tool_name: str, params: dict) -> Any:
        if tool_name not in self._registry:
            raise ValueError(f"[MCP] Tool '{tool_name}' not found. "
                             f"Available: {list(self._registry.keys())}")
        print(f"  [MCP] → {tool_name}({', '.join(params.keys())})")
        return self._registry[tool_name](params)

    # ─────────────────────────────────────────────
    # TOOL 1: get_task_graph
    # ─────────────────────────────────────────────
    def _get_task_graph(self, params: dict) -> dict:
        scenes = params.get("scenes", [])
        task_graph = {
            "total_scenes":   len(scenes),
            "execution_mode": "parallel",
            "parallel_tasks": [
                {
                    "scene_id":    s["scene_id"],
                    "audio_task":  f"voice_synth_scene_{s['scene_id']}",
                    "video_task":  f"video_gen_scene_{s['scene_id']}",
                    "face_task":   f"face_swap_scene_{s['scene_id']}",
                    "fusion_task": f"lip_sync_scene_{s['scene_id']}",
                    "dependencies": {
                        "lip_sync": [
                            f"voice_synth_scene_{s['scene_id']}",
                            f"face_swap_scene_{s['scene_id']}",
                        ]
                    },
                }
                for s in scenes
            ],
        }
        os.makedirs("logs", exist_ok=True)
        with open("logs/task_graph.json", "w") as f:
            json.dump(task_graph, f, indent=2)
        print("  [MCP] Task graph saved → logs/task_graph.json")
        return task_graph

    # ─────────────────────────────────────────────
    # TOOL 2: commit_memory
    # ─────────────────────────────────────────────
    def _commit_memory_tool(self, params: dict) -> bool:
        from memory_store import commit_memory
        return commit_memory(params["key"], params["value"])

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 3: voice_cloning_synthesizer
    # CHANGE v3: Uses pyttsx3 for gender-aware voices.
    #   - male   → Windows "David"  voice (or first available male)
    #   - female → Windows "Zira"   voice (or first available female)
    #   Falls back to gTTS if pyttsx3 is not installed.
    # ─────────────────────────────────────────────────────────────────────────
    def _voice_cloning_synthesizer(self, params: dict) -> str:
        text        = params.get("text", "")
        scene_id    = params.get("scene_id", 0)
        speaker     = params.get("speaker", "character")
        emotion     = params.get("emotion", "neutral")
        gender      = params.get("gender", "male")      # NEW param
        output_path = params.get("output_path", f"audio/scene_{scene_id}_{speaker}.wav")

        os.makedirs("audio", exist_ok=True)

        # Try pyttsx3 first (gender-aware, offline)
        try:
            success = self._synthesize_pyttsx3(text, gender, emotion, output_path)
            if success and os.path.exists(output_path):
                print(f"  [MCP] Audio (pyttsx3/{gender}) → {output_path}")
                return output_path
        except Exception as e:
            print(f"  [MCP] pyttsx3 failed ({e}), falling back to gTTS")

        # Fallback: gTTS (no gender, but works everywhere)
        return self._synthesize_gtts(text, emotion, output_path)

    def _synthesize_pyttsx3(self, text: str, gender: str, emotion: str, output_path: str) -> bool:
        """Use pyttsx3 to generate gender-specific voice audio."""
        import pyttsx3
        with _pyttsx3_lock:          # ← only one thread at a time
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")

            if not voices:
                return False

            # Find best matching voice for the requested gender
            target_gender_str = "female" if gender == "female" else "male"
            selected_voice    = None

            for v in voices:
                v_name = (v.name or "").lower()
                v_id   = (v.id   or "").lower()
                is_female = any(n in v_name or n in v_id
                                for n in ["zira", "female", "woman", "girl", "eva", "hazel", "susan"])
                is_male   = any(n in v_name or n in v_id
                                for n in ["david", "male", "man", "george", "mark", "james"])

                if target_gender_str == "female" and is_female:
                    selected_voice = v.id
                    break
                if target_gender_str == "male" and is_male:
                    selected_voice = v.id
                    break

            # If no gender match found, use first voice (better than crashing)
            if not selected_voice:
                selected_voice = voices[0].id
                print(f"  [MCP] WARN: No {gender} voice found, using default")

            engine.setProperty("voice", selected_voice)

            # Emotion → speech rate & volume
            rate_map   = {"urgent": 185, "happy": 170, "sad": 130, "whisper": 120, "neutral": 150}
            volume_map = {"whisper": 0.6, "urgent": 1.0}
            engine.setProperty("rate",   rate_map.get(emotion, 150))
            engine.setProperty("volume", volume_map.get(emotion, 0.9))

            engine.save_to_file(text, output_path)
            engine.runAndWait()
            engine.stop()
        return True

    def _synthesize_gtts(self, text: str, emotion: str, output_path: str) -> str:
        """gTTS fallback — no gender support but works without pyttsx3."""
        from gtts import gTTS
        from moviepy.editor import AudioFileClip

        slow    = emotion.lower() in ["sad", "whisper", "reflective"]
        tts     = gTTS(text=text, lang="en", slow=slow)
        mp3_path = output_path.replace(".wav", ".mp3")
        tts.save(mp3_path)

        clip = AudioFileClip(mp3_path)
        clip.write_audiofile(output_path, verbose=False, logger=None)
        clip.close()
        os.remove(mp3_path)
        print(f"  [MCP] Audio (gTTS fallback) → {output_path}")
        return output_path

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 4: query_stock_footage
    # No placeholder body drawn here — face_swapper handles character drawing.
    # ─────────────────────────────────────────────────────────────────────────
    def _query_stock_footage(self, params: dict) -> dict:
        import cv2
        import numpy as np

        scene_id   = params.get("scene_id", 0)
        location   = params.get("location", "Unknown")
        visual_cue = params.get("visual_cue", "")
        duration   = params.get("duration", 4)
        fps        = params.get("fps", 24)

        frames_dir = f"frames/scene_{scene_id}"
        os.makedirs(frames_dir, exist_ok=True)

        palette = {
            "library":    ([60,  90,  140], [30,  60,  100]),
            "auditorium": ([80,  60,  120], [50,  30,  90]),
            "university": ([70,  100, 150], [40,  70,  110]),
            "interview":  ([50,  80,  60],  [30,  55,  40]),
            "office":     ([50,  120, 80],  [20,  80,  50]),
            "park":       ([34,  139, 34],  [20,  90,  20]),
            "street":     ([100, 100, 110], [60,  60,  70]),
            "home":       ([200, 140, 80],  [150, 100, 50]),
            "city":       ([70,  130, 180], [30,  80,  130]),
        }
        bg1, bg2 = [80, 80, 160], [40, 40, 100]
        for key, colors in palette.items():
            if key in location.lower():
                bg1, bg2 = colors
                break

        total_frames = duration * fps
        for i in range(total_frames):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for y in range(480):
                a = y / 480
                frame[y, :] = [
                    int(bg1[2] * (1-a) + bg2[2] * a),
                    int(bg1[1] * (1-a) + bg2[1] * a),
                    int(bg1[0] * (1-a) + bg2[0] * a),
                ]
            cv2.rectangle(frame, (0, 0), (640, 55), (0, 0, 0), -1)
            cv2.putText(frame, f"SCENE {scene_id}  |  {location[:50]}",
                        (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, visual_cue[:70],
                        (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
            cv2.putText(frame, f"frame {i+1:04d}/{total_frames}",
                        (540, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)
            cv2.imwrite(f"{frames_dir}/frame_{i:04d}.png", frame)

        print(f"  [MCP] {total_frames} frames → {frames_dir}/")
        return {"frames_dir": frames_dir, "frame_count": total_frames, "fps": fps}

    # ─────────────────────────────────────────────
    # TOOL 5: identity_validator
    # ─────────────────────────────────────────────
    def _identity_validator(self, params: dict) -> bool:
        character      = params.get("character", "")
        reference_path = params.get("reference_path", "")
        if reference_path and os.path.exists(reference_path):
            print(f"  [MCP] Identity VALIDATED: {character}")
            return True
        print(f"  [MCP] Identity WARNING: {character} — no reference, placeholder used")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 6: face_swapper
    # Erases slot before drawing — prevents ghost characters.
    # ─────────────────────────────────────────────────────────────────────────
    def _face_swapper(self, params: dict) -> str:
        import cv2
        import numpy as np

        frames_dir     = params.get("frames_dir", "")
        character      = params.get("character", "Unknown")
        reference_path = params.get("reference_path", "")
        scene_id       = params.get("scene_id", 0)
        all_characters = params.get("all_characters", [character])
        char_index     = params.get("char_index", 0)

        output_dir = f"frames/scene_{scene_id}_swapped"
        os.makedirs(output_dir, exist_ok=True)

        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(".png")])
        if not frame_files:
            print(f"  [MCP] WARN: No frames in {frames_dir}")
            return output_dir

        ref_img = None
        if reference_path and os.path.exists(reference_path):
            ref_img = cv2.imread(reference_path)
            if ref_img is None:
                try:
                    from PIL import Image
                    pil_img = Image.open(reference_path).convert("RGB")
                    ref_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    print(f"  [WARN] Cannot load {reference_path}: {e}")
            if ref_img is not None:
                ref_img = cv2.resize(ref_img, (110, 130))

        n_chars = max(len(all_characters), 1)
        slot_w  = 640 // n_chars
        cx      = slot_w * char_index + slot_w // 2
        cy      = 260
        slot_x1 = slot_w * char_index
        slot_x2 = slot_x1 + slot_w

        for fname in frame_files:
            existing = os.path.join(output_dir, fname)
            src_path = existing if os.path.exists(existing) else os.path.join(frames_dir, fname)
            frame    = cv2.imread(src_path)
            if frame is None:
                continue

            # Clear slot to avoid ghost characters
            frame[60:480, slot_x1:slot_x2] = [25, 25, 25]

            if ref_img is not None:
                x1 = max(cx - 55, 0)
                y1 = max(cy - 65, 0)
                x2 = min(x1 + 110, 640)
                y2 = min(y1 + 130, 480)
                frame[y1:y2, x1:x2] = ref_img[:y2-y1, :x2-x1]
            else:
                cv2.ellipse(frame, (cx, cy-30), (50, 60), 0, 0, 360, (210, 180, 140), -1)
                cv2.ellipse(frame, (cx, cy+65), (70, 40), 0, 0, 180, (170, 140, 110), -1)
                cv2.circle(frame, (cx-16, cy-38), 7, (50, 50, 50), -1)
                cv2.circle(frame, (cx+16, cy-38), 7, (50, 50, 50), -1)

            cv2.rectangle(frame, (cx-55, cy+70), (cx+55, cy+90), (0, 0, 0), -1)
            cv2.putText(frame, character, (max(cx-50, 0), cy+87),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 200), 1)
            cv2.imwrite(os.path.join(output_dir, fname), frame)

        print(f"  [MCP] Face swap → {output_dir}/ | {character} ({char_index+1}/{n_chars})")
        return output_dir

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 7: lip_sync_aligner  (MAJOR CHANGE v3)
    #
    # OLD behaviour: one combined audio + all frames → one Wav2Lip call
    # NEW behaviour: per dialogue line:
    #   1. Take ONLY the speaking character's face image
    #   2. Run Wav2Lip(face_image, line_audio) → short clip
    #   3. Concatenate all clips → final scene MP4
    #
    # This means:
    #   - Mouth movement matches the right speaker for every line
    #   - Each speaker has their own lip animation
    # ─────────────────────────────────────────────────────────────────────────
    def _lip_sync_aligner(self, params: dict) -> str:
        import subprocess
        import shutil
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        line_manifest = params.get("line_manifest", [])
        char_images   = params.get("char_images", {})
        frames_dir    = params.get("frames_dir", "")
        scene_id      = params.get("scene_id", 0)
        fps           = params.get("fps", 24)
        output_path   = params.get("output_path", f"raw_scenes/scene_{scene_id:02d}.mp4")

        os.makedirs("raw_scenes", exist_ok=True)
        os.makedirs(f"raw_scenes/tmp_scene_{scene_id}", exist_ok=True)

        # Locate Wav2Lip
        wav2lip_dir = Path(__file__).parent / "Wav2Lip"
        checkpoint  = wav2lip_dir / "checkpoints" / "wav2lip_gan.pth"
        if not checkpoint.exists():
            checkpoint = wav2lip_dir / "checkpoints" / "wav2lip.pth"

        wav2lip_available = wav2lip_dir.exists() and checkpoint.exists()

        wav2lip_python = WAV2LIP_PYTHON
        if not Path(wav2lip_python).exists():
            print(f"  [MCP] WARN: wav2lip_env not at expected path, using system python")
            wav2lip_python = "python"

        # ── Process each dialogue line ────────────────────────────────────
        clip_paths = []

        for entry in line_manifest:
            line_idx   = entry.get("line_index", 0)
            speaker    = entry.get("speaker", "Unknown")
            audio_path = entry.get("audio_path", "")

            if not audio_path or not os.path.exists(audio_path):
                print(f"  │  [SKIP] Line {line_idx}: no audio for {speaker}")
                continue

            face_image = char_images.get(speaker, "")
            clip_out   = f"raw_scenes/tmp_scene_{scene_id}/line_{line_idx:03d}.mp4"

            print(f"  │  Line {line_idx}: [{speaker}] face={face_image or 'placeholder'}")

            # ── Case A: Have face image → run Wav2Lip ─────────────────────
            if wav2lip_available and face_image and os.path.exists(face_image):
                abs_face      = str(Path(face_image).resolve())
                abs_audio     = str(Path(audio_path).resolve())
                abs_clip_out  = str(Path(clip_out).resolve())
                abs_checkpoint= str(checkpoint.resolve())

                cmd = [
                    wav2lip_python,
                    str(wav2lip_dir / "inference.py"),
                    "--checkpoint_path", abs_checkpoint,
                    "--face",            abs_face,       # single face image
                    "--audio",           abs_audio,
                    "--outfile",         abs_clip_out,
                    "--nosmooth",
                    "--resize_factor",   "1",
                ]

                result = subprocess.run(
                    cmd, cwd=str(wav2lip_dir),
                    capture_output=True, text=True
                )

                if result.returncode == 0 and os.path.exists(clip_out):
                    print(f"  │    ✓ Wav2Lip clip → {clip_out}")
                    clip_paths.append(clip_out)
                    continue
                else:
                    print(f"  │    Wav2Lip failed for line {line_idx}: {result.stderr[-200:]}")
                    # Fall through to plain A/V merge below

            # ── Case B: No face image or Wav2Lip failed ───────────────────
            # Build a static frame video for this speaker and merge with audio
            print(f"  │    Using A/V merge (no lip animation) for line {line_idx}")
            fallback = self._build_static_clip(
                speaker, face_image, frames_dir, audio_path, clip_out, fps
            )
            if fallback:
                clip_paths.append(fallback)

        if not clip_paths:
            print(f"  [MCP] ERROR: No clips generated for scene {scene_id}")
            return ""

        # ── Concatenate all per-line clips → final scene MP4 ─────────────
        print(f"  [MCP] Concatenating {len(clip_paths)} clips → {output_path}")
        try:
            clips    = [VideoFileClip(p) for p in clip_paths]
            combined = concatenate_videoclips(clips, method="compose")
            combined.write_videofile(output_path, fps=fps, verbose=False, logger=None)
            for c in clips:
                c.close()
            combined.close()
        except Exception as e:
            print(f"  [MCP] Concatenation error: {e}")
            # Last resort: just copy the first clip
            if clip_paths:
                shutil.copy(clip_paths[0], output_path)

        # Cleanup temp clips
        for p in clip_paths:
            try:
                os.remove(p)
            except Exception:
                pass

        print(f"  [MCP] ✓ Scene {scene_id} complete → {output_path}")
        return output_path

    def _build_static_clip(self, speaker: str, face_image: str, frames_dir: str,
                            audio_path: str, output_path: str, fps: int) -> str:
        """
        Build a short video clip by looping a static face frame for the
        duration of the audio — used as fallback when Wav2Lip is not available.
        """
        import cv2
        import numpy as np
        from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips

        # Try to load the speaker's face image
        frame = None
        if face_image and os.path.exists(face_image):
            frame = cv2.imread(face_image)
            if frame is None:
                try:
                    from PIL import Image
                    pil_img = Image.open(face_image).convert("RGB")
                    frame   = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception:
                    pass
            if frame is not None:
                frame = cv2.resize(frame, (640, 480))

        # Fall back to a plain gradient with name label
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = [40, 40, 80]
            cv2.putText(frame, f"[{speaker} speaking]",
                        (160, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        # Determine clip duration from audio
        try:
            audio_clip = AudioFileClip(audio_path)
            duration   = audio_clip.duration
            audio_clip.close()
        except Exception:
            duration = 3.0

        total_frames = max(int(duration * fps), 1)
        frames_list  = [frame] * total_frames       # same frame repeated

        # Save frame images to temp dir
        tmp_dir = os.path.dirname(output_path)
        os.makedirs(tmp_dir, exist_ok=True)

        frame_paths = []
        for i, f in enumerate(frames_list):
            p = os.path.join(tmp_dir, f"_static_{os.path.basename(output_path)}_{i:04d}.png")
            cv2.imwrite(p, f)
            frame_paths.append(p)

        video_clip = ImageSequenceClip(frame_paths, fps=fps)
        audio_clip = AudioFileClip(audio_path)
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile(output_path, fps=fps, verbose=False, logger=None)
        video_clip.close()
        audio_clip.close()

        # Clean up temp frames
        for p in frame_paths:
            try:
                os.remove(p)
            except Exception:
                pass

        return output_path

    def _av_merge_fallback(self, video_path: str, audio_path: str,
                            output_path: str, fps: int) -> str:
        from moviepy.editor import VideoFileClip, AudioFileClip
        if not os.path.exists(video_path):
            return ""
        clip = VideoFileClip(video_path)
        if audio_path and os.path.exists(audio_path):
            clip = clip.set_audio(AudioFileClip(audio_path))
        clip.write_videofile(output_path, fps=fps, verbose=False, logger=None)
        clip.close()
        return output_path


    #n------------------------new tools for phase 3---------------------------------------
    
    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 8: generate_scene_image
    # Uses Pollinations.ai — completely free, no API key required.
    # Just sends an HTTP GET with the prompt encoded in the URL.
    # ─────────────────────────────────────────────────────────────────────────
    def _generate_scene_image(self, params: dict) -> str:
        import requests
        import urllib.parse

        prompt      = params.get("prompt", "cinematic scene")
        scene_id    = params.get("scene_id", 0)
        output_path = params.get("output_path", f"scene_visuals/scene_{scene_id:02d}_bg.jpg")

        os.makedirs("scene_visuals", exist_ok=True)

        # Pollinations.ai free image generation
        # Format: https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720
        encoded = urllib.parse.quote(prompt)
        url     = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1280&height=720&nologo=true&seed={scene_id * 42}"
        )

        print(f"  [MCP] Generating image for scene {scene_id}...")
        print(f"  [MCP] Prompt: {prompt[:80]}...")

        try:
            response = requests.get(url, timeout=60)   # can be slow first time
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                size = os.path.getsize(output_path) / 1024
                print(f"  [MCP] Image saved → {output_path} ({size:.0f} KB)")
                return output_path
            else:
                print(f"  [MCP] Pollinations returned {response.status_code}")
                return ""
        except Exception as e:
            print(f"  [MCP] Image generation error: {e}")
            return ""

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 9: compose_scene
    # Takes:
    #   - bg_image    : AI-generated background (1280×720 JPEG)
    #   - phase2_video: raw_scenes/scene_XX.mp4 (characters + lip sync)
    # Does:
    #   1. Apply Ken Burns (zoom/pan) to background
    #   2. Composite Phase 2 characters on top (chroma-key style: replace
    #      the dark background color with the AI image)
    #   3. Burn subtitle text for each dialogue line
    #   4. Keep original audio from Phase 2 video
    # ─────────────────────────────────────────────────────────────────────────
    def _compose_scene(self, params: dict) -> str:
        import numpy as np
        import cv2
        from moviepy.editor import (
            VideoFileClip, ImageClip, CompositeVideoClip,
            TextClip, AudioFileClip
        )

        scene        = params.get("scene", {})
        bg_image     = params.get("bg_image", "")
        phase2_video = params.get("phase2_video", "")
        output_path  = params.get("output_path", "composed_scenes/scene_00.mp4")
        fps          = params.get("fps", 24)

        sid       = scene.get("scene_id", 0)
        dialogues = scene.get("dialogue", [])
        location  = scene.get("location", "")

        os.makedirs("composed_scenes", exist_ok=True)

        # ── Load Phase 2 video (has characters + audio) ───────────────────
        if phase2_video and os.path.exists(phase2_video):
            char_clip = VideoFileClip(phase2_video)
            duration  = char_clip.duration
            audio     = char_clip.audio
        else:
            print(f"  [MCP] No Phase 2 video for scene {sid} — generating placeholder")
            char_clip = None
            duration  = 10.0
            audio     = None

        # ── Build Ken Burns background ─────────────────────────────────────
        bg_clip = self._make_ken_burns_clip(bg_image, duration, fps, sid)

        # ── Subtitle clips ─────────────────────────────────────────────────
        subtitle_clips = self._make_subtitle_clips(dialogues, duration, fps)

        # ── Composite: background → characters → subtitles ─────────────────
        layers = [bg_clip]

        if char_clip is not None:
            # Resize character video to match background dimensions (1280×720)
            char_resized = char_clip.resize((1280, 720))
            # Blend: make the dark character background semi-transparent
            # so AI background shows through
            char_resized = char_resized.set_opacity(0.92)
            layers.append(char_resized)

        layers.extend(subtitle_clips)

        composite = CompositeVideoClip(layers, size=(1280, 720))
        composite = composite.set_duration(duration)

        # Re-attach original audio from Phase 2
        if audio:
            composite = composite.set_audio(audio)

        composite.write_videofile(
            output_path, fps=fps,
            codec="libx264", audio_codec="aac",
            verbose=False, logger=None
        )

        # Clean up
        if char_clip:
            char_clip.close()
        composite.close()
        bg_clip.close()

        return output_path

    def _make_ken_burns_clip(self, bg_image: str, duration: float,
                               fps: int, scene_id: int):
        """
        Apply Ken Burns effect (slow zoom + pan) to a background image.
        Alternates between zoom-in and zoom-out per scene for variety.
        """
        import numpy as np
        import cv2
        from moviepy.editor import VideoClip

        W, H = 1280, 720

        # Load background image
        if bg_image and os.path.exists(bg_image):
            bg = cv2.imread(bg_image)
            if bg is None:
                try:
                    from PIL import Image
                    pil_img = Image.open(bg_image).convert("RGB")
                    bg = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception:
                    bg = None
        else:
            bg = None

        # Fallback: gradient background
        if bg is None:
            bg = np.zeros((H, W, 3), dtype=np.uint8)
            colors = [(60,90,140), (80,60,120), (50,80,60), (50,120,80)]
            c = colors[scene_id % len(colors)]
            for y in range(H):
                a = y / H
                bg[y, :] = [int(c[2]*(1-a) + 20*a),
                             int(c[1]*(1-a) + 20*a),
                             int(c[0]*(1-a) + 20*a)]

        # Resize larger than frame for zoom headroom
        bg_h, bg_w = bg.shape[:2]
        scale = max(W / bg_w, H / bg_h) * 1.15   # 15% extra for zoom
        bg_big = cv2.resize(bg, (int(bg_w * scale), int(bg_h * scale)))
        bh, bw = bg_big.shape[:2]

        # Alternate zoom direction per scene
        zoom_in = (scene_id % 2 == 0)

        def make_frame(t):
            progress = t / max(duration, 0.001)

            if zoom_in:
                # Start slightly zoomed in, slowly pull back → zoom in effect
                zoom = 1.0 + 0.08 * progress
            else:
                # Start wide, slowly zoom in
                zoom = 1.08 - 0.08 * progress

            # Pan: slow horizontal drift
            pan_x = int(0.03 * bw * progress * (1 if scene_id % 4 < 2 else -1))

            # Compute crop window
            crop_w = int(W / zoom)
            crop_h = int(H / zoom)
            cx     = (bw - crop_w) // 2 + pan_x
            cy     = (bh - crop_h) // 2

            # Clamp to image bounds
            cx = max(0, min(cx, bw - crop_w))
            cy = max(0, min(cy, bh - crop_h))

            cropped = bg_big[cy:cy+crop_h, cx:cx+crop_w]
            resized = cv2.resize(cropped, (W, H))
            return cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        from moviepy.editor import VideoClip
        return VideoClip(make_frame, duration=duration).set_fps(fps)

    def _make_subtitle_clips(self, dialogues: list, total_duration: float, fps: int) -> list:
        """
        Create subtitle TextClip for each dialogue line.
        Evenly distributes line display time across the scene duration.
        """
        from moviepy.editor import TextClip

        if not dialogues:
            return []

        clips      = []
        line_dur   = total_duration / len(dialogues)

        for i, line in enumerate(dialogues):
            speaker = line.get("speaker", "")
            text    = line.get("line", "")
            if not text:
                continue

            # Truncate long lines for readability
            display_text = f"{speaker}: {text}"
            if len(display_text) > 80:
                display_text = display_text[:77] + "..."

            start_t = i * line_dur
            end_t   = min((i + 1) * line_dur, total_duration)

            try:
                txt_clip = (
                    TextClip(
                        display_text,
                        fontsize=28,
                        color="white",
                        stroke_color="black",
                        stroke_width=1.5,
                        method="caption",
                        size=(1200, None),
                        font="Arial",
                    )
                    .set_position(("center", 660))   # near bottom
                    .set_start(start_t)
                    .set_end(end_t)
                )
                clips.append(txt_clip)
            except Exception as e:
                print(f"  [MCP] Subtitle error line {i}: {e}")

        return clips

    # ─────────────────────────────────────────────────────────────────────────
    # TOOL 10: concat_with_transitions
    # Concatenates all composed scene videos with:
    #   - Crossfade between scenes (fade out → fade in)
    #   - Title card at the beginning
    #   - Final fade to black at the end
    # ─────────────────────────────────────────────────────────────────────────
    def _concat_with_transitions(self, params: dict) -> str:
        from moviepy.editor import (
            VideoFileClip, concatenate_videoclips,
            TextClip, CompositeVideoClip, ColorClip
        )

        scene_paths   = params.get("scene_paths", [])
        output_path   = params.get("output_path", "final_output.mp4")
        title         = params.get("title", "")
        fps           = params.get("fps", 24)
        fade_duration = params.get("fade_duration", 0.5)

        if not scene_paths:
            print("  [MCP] No scene paths to concatenate")
            return ""

        print(f"  [MCP] Loading {len(scene_paths)} scene clips...")
        clips = []
        for path in scene_paths:
            if os.path.exists(path):
                clip = VideoFileClip(path)
                # Apply fade in/out to each clip for smooth transitions
                clip = clip.fadein(fade_duration).fadeout(fade_duration)
                clips.append(clip)
            else:
                print(f"  [MCP] WARN: {path} not found, skipping")

        if not clips:
            return ""

        # ── Title card (3 seconds at start) ────────────────────────────────
        if title:
            try:
                W, H = clips[0].size
                title_bg = ColorClip(size=(W, H), color=(0, 0, 0), duration=3.0)
                title_txt = (
                    TextClip(title, fontsize=52, color="white",
                             font="Arial-Bold", method="caption", size=(W - 100, None))
                    .set_position("center")
                    .set_duration(3.0)
                )
                title_card = (
                    CompositeVideoClip([title_bg, title_txt])
                    .fadein(0.5)
                    .fadeout(0.5)
                )
                clips.insert(0, title_card)
                print(f"  [MCP] Title card added: '{title}'")
            except Exception as e:
                print(f"  [MCP] Title card error: {e}")

        # ── Concatenate with crossfade ─────────────────────────────────────
        print(f"  [MCP] Concatenating with crossfade transitions...")
        try:
            final = concatenate_videoclips(clips, method="compose", padding=-fade_duration)
        except Exception:
            # Fallback: simple concatenation without padding
            final = concatenate_videoclips(clips, method="compose")

        # Final fade to black
        final = final.fadeout(1.0)

        print(f"  [MCP] Writing final_output.mp4 (duration: {final.duration:.1f}s)...")
        final.write_videofile(
            output_path, fps=fps,
            codec="libx264", audio_codec="aac",
            verbose=False, logger=None
        )

        for c in clips:
            c.close()
        final.close()

        size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  [MCP] ✓ final_output.mp4 → {size:.1f} MB")
        return output_path




# Global singleton
mcp = MCPClient()