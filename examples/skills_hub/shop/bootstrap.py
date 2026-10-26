"""Start of the service: publish the skills baked into the image to the application's stage.

Idempotent: a version that is on the stage is left alone (published versions never change), so a
restart publishes nothing and a new image adds only its new skills or versions. It uses the same
gate and the same store as `make publish-skill`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from shop.skill import validate_folder
from shop.stores import PublishError

HERE = Path(__file__).resolve().parent.parent


def publish_bundled(store, samples: Path) -> list[str]:
    """Publish every skill folder of `samples` that the store does not have; the ids and versions
    published. A folder that fails validation is an error, not skipped."""
    have = {(s.id, s.version) for s in store.index()}
    published = []
    for folder in sorted(p for p in samples.iterdir() if p.is_dir()):
        report = validate_folder(folder)
        if not report.ok:
            raise PublishError(f"{folder.name}: {'; '.join(report.errors)}")
        if (report.skill.id, report.skill.version) in have:
            continue
        store.publish(folder, report)
        published.append(f"{report.skill.id} {report.skill.version}")
    return published


def main() -> int:
    from shop import native

    options, store = native.connect()
    try:
        done = publish_bundled(store, HERE / "samples")
    finally:
        options.connection.close()
    print("published: " + (", ".join(done) if done else "nothing new"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
