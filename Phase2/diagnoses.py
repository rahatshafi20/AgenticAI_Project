"""
diagnose.py — Run this to find the image naming mismatch
Usage: python diagnose.py
"""

import os
import json

print("\n" + "="*60)
print("  DIAGNOSTIC: IMAGE ASSETS vs SCENE MANIFEST")
print("="*60)

# ── Step 1: What files are actually in image_assets/ ──────────
print("\n[1] Files found in image_assets/:")
if not os.path.exists("image_assets"):
    print("    ERROR: image_assets/ folder does not exist!")
else:
    files = os.listdir("image_assets")
    if not files:
        print("    ERROR: image_assets/ folder is EMPTY!")
    for f in files:
        full = os.path.join("image_assets", f)
        size = os.path.getsize(full)
        print(f"    → '{f}'  ({size} bytes)")

# ── Step 2: What character names are in scene_manifest.json ───
print("\n[2] Character names in scene_manifest.json:")
if not os.path.exists("scene_manifest.json"):
    print("    ERROR: scene_manifest.json not found!")
else:
    with open("scene_manifest.json") as f:
        manifest = json.load(f)

    all_chars = set()

    # From top-level characters array
    for c in manifest.get("characters", []):
        name = c.get("name", c) if isinstance(c, dict) else c
        all_chars.add(name)

    # From scene-level characters lists
    for scene in manifest.get("scenes", []):
        for c in scene.get("characters", []):
            all_chars.add(c)

    for name in sorted(all_chars):
        print(f"    → '{name}'")

# ── Step 3: Cross-check — which ones match ────────────────────
print("\n[3] Cross-check (does each character have an image?):")
if os.path.exists("image_assets") and os.path.exists("scene_manifest.json"):
    image_files = os.listdir("image_assets")
    image_names = [os.path.splitext(f)[0] for f in image_files]  # strip extension

    for name in sorted(all_chars):
        # Exact match
        exact_png = f"{name}.png"
        exact_jpg = f"{name}.jpg"
        lower_png = f"{name.lower()}.png"
        lower_jpg = f"{name.lower()}.jpg"

        matched = None
        for fname in image_files:
            if fname in [exact_png, exact_jpg, lower_png, lower_jpg]:
                matched = fname
                break

        if matched:
            print(f"    ✓ '{name}' → image_assets/{matched}")
        else:
            print(f"    ✗ '{name}' → NO MATCH FOUND")
            print(f"      (looking for: {exact_png} or {exact_jpg})")
            # Show closest filename if any
            for fname in image_files:
                if name.lower() in fname.lower() or fname.lower() in name.lower():
                    print(f"      Closest file found: '{fname}'")

# ── Step 4: Show exact fix ────────────────────────────────────
print("\n[4] SOLUTION:")
print("    Rename your image files to EXACTLY match character names above.")
print("    Example: if character is 'Alex' → file must be 'Alex.png'")
print("    Then run: python main.py --fresh")
print("="*60 + "\n")