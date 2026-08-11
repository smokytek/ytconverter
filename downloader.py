"""Servizio di download e conversione per ytconverter."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Callable

import yt_dlp


class DownloadResult(Enum):
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()


class DownloadCancelled(Exception):
    pass


@dataclass(slots=True)
class DownloadEvent:
    kind: str
    message: str = ""
    percent: float | None = None
    title: str = ""
    speed: str = ""
    eta: str = ""


QUALITY_BITRATES = {
    "Bassa · 96 kbps": "96",
    "Media · 160 kbps": "160",
    "Alta · 256 kbps": "256",
    "Massima · 320 kbps": "320",
}


def _percent(value: str) -> float | None:
    match = re.search(r"([\d.,]+)%", value)
    if not match:
        return None
    try:
        return max(0.0, min(100.0, float(match.group(1).replace(",", "."))))
    except ValueError:
        return None


class AudioDownloader:
    def __init__(self, ffmpeg_path: Path, emit: Callable[[DownloadEvent], None]) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.emit = emit

    def download(
        self,
        source: str,
        output_folder: Path,
        quality: str,
        cancel: threading.Event,
        allow_alternative: bool,
    ) -> DownloadResult:
        output_folder.mkdir(parents=True, exist_ok=True)
        result, title = self._attempt(source, output_folder, quality, cancel)
        if result is not DownloadResult.FAILED or not allow_alternative or not title:
            return result

        self.emit(DownloadEvent("log", f"Cerco una possibile alternativa per “{title}”…"))
        alternative = self._find_alternative(title, cancel)
        if not alternative or alternative == source:
            return DownloadResult.FAILED
        self.emit(DownloadEvent("log", "Trovata un’alternativa: eseguo un solo nuovo tentativo."))
        return self._attempt(alternative, output_folder, quality, cancel)[0]

    def _attempt(
        self, source: str, output_folder: Path, quality: str, cancel: threading.Event
    ) -> tuple[DownloadResult, str]:
        title = ""

        def hook(data: dict) -> None:
            nonlocal title
            if cancel.is_set():
                raise DownloadCancelled()
            info = data.get("info_dict") or {}
            title = str(info.get("title") or title)
            status = data.get("status")
            if status == "downloading":
                self.emit(
                    DownloadEvent(
                        "progress",
                        percent=_percent(str(data.get("_percent_str", ""))),
                        title=title,
                        speed=str(data.get("_speed_str", "")),
                        eta=str(data.get("_eta_str", "")),
                    )
                )
            elif status == "finished":
                self.emit(DownloadEvent("phase", "Conversione in MP3…", title=title))

        options = {
            "format": "bestaudio/best",
            "outtmpl": str(output_folder / "%(title).180B [%(id)s].%(ext)s"),
            "ffmpeg_location": str(self.ffmpeg_path),
            "noplaylist": True,
            "windowsfilenames": True,
            "overwrites": False,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": QUALITY_BITRATES.get(quality, "256"),
            }],
        }
        try:
            self.emit(DownloadEvent("phase", "Preparazione del download…"))
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(source, download=True)
                title = str((info or {}).get("title") or title)
            return DownloadResult.SUCCESS, title
        except DownloadCancelled:
            return DownloadResult.CANCELLED, title
        except Exception as exc:
            if cancel.is_set():
                return DownloadResult.CANCELLED, title
            self.emit(DownloadEvent("log", f"Download non riuscito: {exc}"))
            return DownloadResult.FAILED, title

    def _find_alternative(self, title: str, cancel: threading.Event) -> str | None:
        if cancel.is_set():
            return None
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
                result = ydl.extract_info(f"ytsearch1:{title}", download=False)
            entries = (result or {}).get("entries") or []
            return str(entries[0].get("webpage_url")) if entries else None
        except Exception:
            return None
