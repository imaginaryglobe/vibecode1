# author jaden fang jason lyu
from __future__ import annotations

import hashlib
from pathlib import Path


def spec_hash(spec_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(spec_dir.glob("*.md")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
