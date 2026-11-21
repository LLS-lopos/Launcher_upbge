from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

CONFIG = Path.home() / ".LanceurUpBGE" / "config_launcher.json"

GAME_KEYWORDS = (
    "RUNX2",
    "RUNX3",
    "RUNX4",
    "RUNX5",
    "RUNXRANGE",
    "RUNXCUSTOM",
)

INTERACTIVE_CODE = (
    "import bpy\n"
    "try:\n"
    "    import bge\n"
    "except Exception as exc:\n"
    "    print('bge indisponible:', exc)\n"
    "import code\n"
    "code.interact(local=globals())\n"
)


def load_config():
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def available():
    data = load_config()
    section = "windows" if os.name == "nt" else "linux"
    engines = []
    for name, path in data.get(section, {}).get("executable", {}).items():
        if name.startswith("game-") or not path:
            continue
        candidate = Path(path)
        if candidate.exists():
            engines.append((name, str(candidate)))
    custom_key = "C_Wblend" if os.name == "nt" else "C_Lblend"
    path = data.get("custom", {}).get(custom_key)
    if path and Path(path).exists():
        engines.append((custom_key, path))
    if not engines:
        for name in ("RangeEngine", "blender", "bforartists"):
            found = shutil.which(name)
            if found:
                engines.append((name, found))
    return engines


def labels():
    return [name for name, _ in available()]


def preferred():
    engines = available()
    if not engines:
        return None
    for name, path in engines:
        if "range" in name.lower():
            return path
    return engines[-1][1]


def game_commands():
    data = load_config()
    section = "windows" if os.name == "nt" else "linux"
    executables = data.get(section, {}).get("executable", {})
    custom = data.get("custom", {})
    range_key = "game-W-Range" if os.name == "nt" else "game-L-Range"
    custom_key = "C_Wgame" if os.name == "nt" else "C_Lgame"
    mapping = {
        "RUNX2": executables.get("game-2x"),
        "RUNX3": executables.get("game-3x"),
        "RUNX4": executables.get("game-4x"),
        "RUNX5": executables.get("game-5x"),
        "RUNXRANGE": executables.get(range_key),
        "RUNXCUSTOM": custom.get(custom_key),
    }
    result = {}
    for keyword, path in mapping.items():
        if path and Path(path).exists():
            result[keyword] = str(path)
    return result


def interactive_command(executable):
    return [str(executable), "--background", "--python-expr", INTERACTIVE_CODE]


def script_command(executable, script):
    return [str(executable), "--background", "--python", str(script)]
