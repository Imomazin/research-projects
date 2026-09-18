"""Reproducibility / provenance capture."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _git_sha(cwd: Optional[str] = None) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cwd, stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return None


def _pkg_versions() -> Dict[str, str]:
    versions: Dict[str, str] = {}
    for name in ("numpy", "scipy", "sklearn", "pandas"):
        try:
            mod = __import__(name)
            versions[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            versions[name] = "not-installed"
    return versions


def config_hash(config: Dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class Provenance:
    experiment_id: str
    config: Dict[str, Any]
    date_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_sha: Optional[str] = field(default_factory=_git_sha)
    python_version: str = field(default_factory=platform.python_version)
    platform: str = field(default_factory=platform.platform)
    package_versions: Dict[str, str] = field(default_factory=_pkg_versions)

    @property
    def config_hash(self) -> str:
        return config_hash(self.config)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["config_hash"] = self.config_hash
        return d
