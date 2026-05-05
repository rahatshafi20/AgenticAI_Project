"""
state_manager.py — State Versioning & Undo System
───────────────────────────────────────────────────
Rubric: State snapshot system, undo/revert functionality (Phase 5)

Implements:
  StateManager.snapshot(description, state_json, asset_paths) → version int
  StateManager.revert(version)  → restores assets + state
  StateManager.history()        → list of all versions with diff summary
  StateManager.current()        → latest version number

Storage: SQLite (append-only log — no version is ever permanently lost)
Assets : copied into versions/ directory per snapshot
"""

import os
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH       = "versions/state_history.db"
VERSIONS_DIR  = "versions"


class StateManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(VERSIONS_DIR, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    version     INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   TEXT    NOT NULL,
                    description TEXT    NOT NULL,
                    state_json  TEXT    NOT NULL,
                    asset_dir   TEXT    NOT NULL,
                    edit_intent TEXT    DEFAULT '',
                    edit_params TEXT    DEFAULT '{}'
                )
            """)
            conn.commit()

    # ──────────────────────────────────────────────────────────────
    # snapshot() — save current pipeline state + assets
    # ──────────────────────────────────────────────────────────────
    def snapshot(
        self,
        description:  str,
        state_json:   dict,
        asset_paths:  list = None,
        edit_intent:  str  = "",
        edit_params:  dict = None,
    ) -> int:
        """
        Save a versioned snapshot of the current pipeline state.

        Args:
            description : human-readable summary (e.g. "After voice tone change")
            state_json  : full pipeline state dict to serialize
            asset_paths : list of file paths to copy into the snapshot
            edit_intent : what edit was applied (e.g. "change_voice_tone")
            edit_params : parameters of the edit

        Returns:
            version number (integer, auto-incremented)
        """
        timestamp = datetime.now().isoformat()

        # Insert snapshot record first to get the version number
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO snapshots
                   (timestamp, description, state_json, asset_dir, edit_intent, edit_params)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    timestamp,
                    description,
                    json.dumps(state_json, indent=2),
                    "",   # placeholder — updated after we know the version
                    edit_intent,
                    json.dumps(edit_params or {}),
                )
            )
            version = cursor.lastrowid
            conn.commit()

        # Create asset directory for this version
        asset_dir = os.path.join(VERSIONS_DIR, f"v{version:04d}")
        os.makedirs(asset_dir, exist_ok=True)

        # Copy assets into the version directory
        if asset_paths:
            for src in asset_paths:
                if src and os.path.exists(src):
                    dst = os.path.join(asset_dir, os.path.basename(src))
                    shutil.copy2(src, dst)

        # Update the asset_dir in the database
        with self._connect() as conn:
            conn.execute(
                "UPDATE snapshots SET asset_dir = ? WHERE version = ?",
                (asset_dir, version)
            )
            conn.commit()

        print(f"  [STATE] Snapshot v{version} saved: '{description}' → {asset_dir}/")
        return version

    # ──────────────────────────────────────────────────────────────
    # revert() — restore a previous version
    # ──────────────────────────────────────────────────────────────
    def revert(self, version: int) -> dict:
        """
        Restore pipeline state and assets to a previous version.

        Returns the restored state_json dict, or {} on failure.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state_json, asset_dir, description FROM snapshots WHERE version = ?",
                (version,)
            ).fetchone()

        if not row:
            print(f"  [STATE] ERROR: Version {version} not found")
            return {}

        state_json_str, asset_dir, description = row
        state = json.loads(state_json_str)

        # Restore asset files to their original locations
        if asset_dir and os.path.isdir(asset_dir):
            restored = 0
            for fname in os.listdir(asset_dir):
                src = os.path.join(asset_dir, fname)

                # Determine restore destination based on file type
                if fname.endswith(".mp4"):
                    if fname.startswith("scene_"):
                        # Per-scene raw video → raw_scenes/
                        dst = os.path.join("raw_scenes", fname)
                    elif fname == "final_output.mp4":
                        dst = "final_output.mp4"
                    else:
                        dst = os.path.join("composed_scenes", fname)
                elif fname.endswith(".wav") or fname.endswith(".mp3"):
                    dst = os.path.join("audio", fname)
                elif fname.endswith(".json"):
                    dst = fname   # root level JSON files
                elif fname.endswith((".jpg", ".jpeg", ".png")):
                    dst = os.path.join("scene_visuals", fname)
                else:
                    dst = fname

                os.makedirs(os.path.dirname(dst) if os.path.dirname(dst) else ".", exist_ok=True)
                shutil.copy2(src, dst)
                restored += 1

            print(f"  [STATE] Reverted to v{version}: '{description}' ({restored} assets restored)")
        else:
            print(f"  [STATE] Reverted to v{version}: '{description}' (state only — no assets)")

        # Save a new snapshot recording that we reverted
        self.snapshot(
            description=f"Reverted to v{version}: {description}",
            state_json=state,
            edit_intent="revert",
            edit_params={"reverted_to": version},
        )

        return state

    # ──────────────────────────────────────────────────────────────
    # history() — list all versions
    # ──────────────────────────────────────────────────────────────
    def history(self) -> list:
        """
        Return list of all versions with metadata.

        Returns:
            [ {version, timestamp, description, edit_intent, edit_params}, ... ]
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT version, timestamp, description, edit_intent, edit_params, asset_dir
                   FROM snapshots ORDER BY version DESC"""
            ).fetchall()

        result = []
        for row in rows:
            version, timestamp, description, edit_intent, edit_params_str, asset_dir = row

            # Count assets in this version
            asset_count = len(os.listdir(asset_dir)) if asset_dir and os.path.isdir(asset_dir) else 0

            result.append({
                "version":     version,
                "timestamp":   timestamp,
                "description": description,
                "edit_intent": edit_intent or "initial",
                "edit_params": json.loads(edit_params_str or "{}"),
                "asset_count": asset_count,
                "asset_dir":   asset_dir,
            })

        return result

    # ──────────────────────────────────────────────────────────────
    # current() — latest version number
    # ──────────────────────────────────────────────────────────────
    def current(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(version) FROM snapshots"
            ).fetchone()
        return row[0] or 0

    # ──────────────────────────────────────────────────────────────
    # get_state() — retrieve state_json for a specific version
    # ──────────────────────────────────────────────────────────────
    def get_state(self, version: int) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state_json FROM snapshots WHERE version = ?", (version,)
            ).fetchone()
        return json.loads(row[0]) if row else {}


# Singleton
state_manager = StateManager()
