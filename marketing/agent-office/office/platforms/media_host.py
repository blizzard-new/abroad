"""Public URLs for rendered media. Instagram and Threads fetch images and videos from a URL, they do not take uploads.

- supabase: uploads to a public Supabase Storage bucket (the project already uses Supabase).
- static:   the office server itself serves var/media/ at OFFICE_PUBLIC_BASE_URL/media/ (for example behind a tunnel).
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from ..config import Settings
from .base import Client, PlatformError


class MediaHost(Client):
    name = "Media host"

    def __init__(self, settings: Settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings

    def public_url(self, path: Path) -> str:
        relative = path.resolve().relative_to(self.settings.media_dir.resolve()).as_posix()
        mode = self.settings.media_host
        if mode == "static":
            if not self.settings.public_base_url:
                raise PlatformError("OFFICE_MEDIA_HOST=static 需要設定 OFFICE_PUBLIC_BASE_URL")
            return f"{self.settings.public_base_url}/media/{relative}"
        if mode == "supabase":
            base, bucket = self.settings.supabase_url, self.settings.supabase_bucket
            if not (base and self.settings.supabase_service_key) and not self.dry_run:
                raise PlatformError("OFFICE_MEDIA_HOST=supabase 需要 SUPABASE_URL 與 SUPABASE_SERVICE_ROLE_KEY")
            key = self.settings.supabase_service_key
            self.request(
                "POST",
                f"{base}/storage/v1/object/{bucket}/{relative}",
                content=b"" if self.dry_run else path.read_bytes(),
                headers={
                    "Authorization": f"Bearer {key}",
                    "apikey": key,
                    "x-upsert": "true",
                    "Content-Type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                },
            )
            return f"{base}/storage/v1/object/public/{bucket}/{relative}"
        if self.dry_run:
            return f"(本機檔案) {relative}"
        raise PlatformError("Instagram／Threads 需要公開網址：請設定 OFFICE_MEDIA_HOST（supabase 或 static）")
