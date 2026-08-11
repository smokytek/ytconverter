"""Ricerca dell'eseguibile FFmpeg usato da ytconverter."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_ffmpeg() -> Path | None:
    candidates = [
        application_dir() / "dependencies" / "ffmpeg.exe",
        application_dir() / "ffmpeg.exe",
    ]
    system = shutil.which("ffmpeg")
    if system:
        candidates.append(Path(system))
    return next((path for path in candidates if path.is_file()), None)
