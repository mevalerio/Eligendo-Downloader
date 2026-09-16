from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    request_interval_seconds: float
    request_timeout_seconds: float
    catalogue_ttl_seconds: int
    max_archive_bytes: int
    max_uncompressed_bytes: int

    @classmethod
    def from_environment(cls) -> "Settings":
        data_dir = Path(os.getenv("ELIGENDO_DATA_DIR", "data")).resolve()
        database_path = Path(
            os.getenv("ELIGENDO_DATABASE_PATH", str(data_dir / "eligendo.sqlite3"))
        ).resolve()
        return cls(
            data_dir=data_dir,
            database_path=database_path,
            request_interval_seconds=float(
                os.getenv("ELIGENDO_REQUEST_INTERVAL_SECONDS", "0.8")
            ),
            request_timeout_seconds=float(
                os.getenv("ELIGENDO_REQUEST_TIMEOUT_SECONDS", "30")
            ),
            catalogue_ttl_seconds=int(
                os.getenv("ELIGENDO_CATALOGUE_TTL_SECONDS", "3600")
            ),
            max_archive_bytes=int(
                os.getenv("ELIGENDO_MAX_ARCHIVE_BYTES", str(250 * 1024 * 1024))
            ),
            max_uncompressed_bytes=int(
                os.getenv("ELIGENDO_MAX_UNCOMPRESSED_BYTES", str(2 * 1024**3))
            ),
        )


settings = Settings.from_environment()
