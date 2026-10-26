"""The demo shop: the sample skills, published (through the same gate) into a temporary folder."""

from __future__ import annotations

import tempfile
from pathlib import Path

from shop.skill import validate_folder
from shop.stores import LocalFolderStore

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def build_demo_store(samples: Path = SAMPLES) -> LocalFolderStore:
    store = LocalFolderStore(tempfile.mkdtemp(prefix="skills-shop-demo-"))
    for folder in sorted(p for p in samples.iterdir() if p.is_dir()):
        store.publish(folder, validate_folder(folder))
    store.label = "the sample skills (a temporary folder)"
    return store
