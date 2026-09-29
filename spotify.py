"""Client Spotify (solo stdlib) per leggere playlist, album e tracce."""

from __future__ import annotations

import base64
import json
import re
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

API_BASE = "https://api.spotify.com/v1"
EMBED_TOKEN_URL = "https://open.spotify.com/get_access_token?reason=transport&productType=embed"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

_PLAYLIST_RE = re.compile(r"playlist/([A-Za-z0-9]+)")
_ALBUM_RE = re.compile(r"album/([A-Za-z0-9]+)")
_TRACK_RE = re.compile(r"track/([A-Za-z0-9]+)")
_URI_RE = re.compile(r"spotify:(playlist|album|track):([A-Za-z0-9]{22})")


class SpotifyError(Exception):
    pass


@dataclass(slots=True)
class SpotifyTrack:
    name: str
    artists: str
    album: str
    duration_ms: int
    query: str


class SpotifyClient:
    """Ottiene i metadati senza login: prima prova il token anonimo dell'embed
    pubblico, poi (se configurate) le credenziali Client Credentials."""

    def __init__(
        self,
        emit=None,
        client_id: str = "",
        client_secret: str = "",
        cancel: threading.Event | None = None,
    ) -> None:
        self.emit = emit or (lambda message: None)
        self.client_id = client_id
        self.client_secret = client_secret
        self.cancel = cancel

    # ------------------------------------------------------------------ auth
    def _token(self) -> str:
        if self.client_id and self.client_secret:
            try:
                return self._client_credentials_token()
            except SpotifyError:
                self.emit("Credenziali Spotify non valide: provo il token anonimo…")
        return self._anonymous_token()

    def _anonymous_token(self) -> str:
        request = urllib.request.Request(
            EMBED_TOKEN_URL, headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SpotifyError(
                "Impossibile ottenere il token Spotify. Configura client_id e "
                "client_secret (https://developer.spotify.com/dashboard) in "
                "%LOCALAPPDATA%\\ytconverter\\config.json."
            ) from exc
        token = str(data.get("accessToken") or "")
        if not token:
            raise SpotifyError("Risposta Spotify senza token di accesso.")
        return token

    def _client_credentials_token(self) -> str:
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        request = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SpotifyError(f"Autenticazione Spotify non riuscita: {exc}") from exc
        token = str(data.get("access_token") or "")
        if not token:
            raise SpotifyError("Risposta Spotify senza token di accesso.")
        return token

    # ----------------------------------------------------------------- fetch
    def _get(self, url: str, token: str) -> dict:
        if self.cancel is not None and self.cancel.is_set():
            raise SpotifyError("Operazione annullata.")
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SpotifyError(f"Chiamata API Spotify non riuscita: {exc}") from exc

    @staticmethod
    def _resource_id(source: str) -> tuple[str, str] | None:
        text = urllib.parse.unquote(source.strip())
        uri = _URI_RE.search(text)
        if uri:
            return uri.group(1), uri.group(2)
        for kind, pattern in (
            ("playlist", _PLAYLIST_RE),
            ("album", _ALBUM_RE),
            ("track", _TRACK_RE),
        ):
            match = pattern.search(text)
            if match:
                return kind, match.group(1)
        if re.fullmatch(r"[A-Za-z0-9]{22}", text):
            return "playlist", text
        return None

    def fetch_tracks(self, source: str) -> tuple[str, list[SpotifyTrack]]:
        """Restituisce (titolo della raccolta, tracce)."""
        resolved = self._resource_id(source)
        if not resolved:
            raise SpotifyError(
                "Link Spotify non riconosciuto: serve un URL di playlist, album o traccia."
            )
        kind, resource_id = resolved
        token = self._token()

        if kind == "track":
            data = self._get(f"{API_BASE}/tracks/{resource_id}", token)
            return data.get("album", {}).get("name", ""), [self._track_from(data)]

        if kind == "album":
            data = self._get(f"{API_BASE}/albums/{resource_id}", token)
            title = str(data.get("name") or "Album Spotify")
            tracks = self._paginate(f"{API_BASE}/albums/{resource_id}/tracks", token)
            return title, [self._track_from(item, album_override=title) for item in tracks]

        data = self._get(f"{API_BASE}/playlists/{resource_id}?fields=name", token)
        title = str(data.get("name") or "Playlist Spotify")
        tracks = self._paginate(
            f"{API_BASE}/playlists/{resource_id}/tracks", token
        )
        return title, [self._track_from(item.get("track") or {}) for item in tracks]

    def _paginate(self, url: str, token: str) -> list[dict]:
        items: list[dict] = []
        next_url: str | None = url
        total = None
        while next_url:
            if self.cancel is not None and self.cancel.is_set():
                raise SpotifyError("Operazione annullata.")
            data = self._get(next_url, token)
            page = data.get("items") or []
            items.extend(item for item in page if item)
            total = data.get("total") if total is None else total
            self.emit(f"Lette {len(items)} tracce…" + (f" (su {total})" if total else ""))
            next_url = data.get("next")
        return items

    def _track_from(self, data: dict, album_override: str = "") -> SpotifyTrack:
        name = str(data.get("name") or "").strip()
        artists = ", ".join(
            str(artist.get("name") or "")
            for artist in (data.get("artists") or [])
            if artist.get("name")
        )
        album = album_override or str(data.get("album") or "")
        return SpotifyTrack(
            name=name,
            artists=artists,
            album=album,
            duration_ms=int(data.get("duration_ms") or 0),
            query=f"{artists} - {name}".strip(" -") if artists else name,
        )


def load_spotify_credentials(config_path: Path) -> tuple[str, str]:
    """Legge spotify_client_id / spotify_client_secret dal config.json."""
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    return (
        str(data.get("spotify_client_id") or ""),
        str(data.get("spotify_client_secret") or ""),
    )
