from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


APP_NAME = "ytconverter"


def app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / APP_NAME


@dataclass(slots=True)
class AppConfig:
    create_zip: bool = False
    allow_alternatives: bool = True
    allow_playlists: bool = True
    quality: str = "Alta · 256 kbps"
    output_folder: str = str(Path.home() / "Downloads" / APP_NAME)


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_data_dir() / "config.json"

    def load(self) -> AppConfig:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            valid = {key: value for key, value in data.items() if key in AppConfig.__dataclass_fields__}
            return AppConfig(**valid)
        except (OSError, ValueError, TypeError):
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)
