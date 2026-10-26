"""`make publish-skill`: validate a skill folder and put it on the shop's stage (or a local folder).

    make publish-skill SKILL=examples/skills_hub/samples/csv-profile \\
        ARGS="--stage DB.SCHEMA.STAGE --profile snowflake --role MY_ROLE"
    make publish-skill SKILL=... ARGS="--local /tmp/shop"             # no Snowflake
    make publish-skill SKILL=... ARGS="--dry-run"                      # validate only

A published version never changes: publishing it again is refused (`--force` replaces it, for a
fix made by the developer who published it). The role of the connection must be able to write to the
stage; give the shop's users read only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shop.skill import validate_folder
from shop.stores import LocalFolderStore, PublishError, StageStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="publish-skill", description=__doc__.split("\n\n")[0])
    parser.add_argument("folder", help="the skill folder (SKILL.md at its top)")
    where = parser.add_mutually_exclusive_group()
    where.add_argument("--stage", help="DATABASE.SCHEMA.STAGE to publish to")
    where.add_argument("--local", help="a folder on this computer to publish to")
    parser.add_argument("--profile", help="a profile of ~/.snowflake (with --stage)")
    parser.add_argument("--role", help="the role of the session (default: the profile's own)")
    parser.add_argument("--force", action="store_true", help="replace a published version")
    parser.add_argument("--dry-run", action="store_true", help="validate, publish nothing")
    return parser


def main(argv: list[str] | None = None, *, connect=None) -> int:
    """`connect(profile, role)` -> a connector connection; given by tests, else the library's."""
    args = build_parser().parse_args(argv)
    folder = Path(args.folder).expanduser().resolve()
    report = validate_folder(folder)
    for warning in report.warnings:
        print(f"warning: {warning}")
    if not report.ok:
        for error in report.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    skill = report.skill
    print(f"{skill.id} {skill.version}: {len(skill.files)} files, sha256 {skill.sha256[:12]}")
    if args.dry_run:
        print("dry run: nothing published.")
        return 0
    if args.local:
        store = LocalFolderStore(args.local)
    elif args.stage:
        if not args.profile:
            print("error: --stage needs --profile.", file=sys.stderr)
            return 2
        if connect is None:
            from streamlit_coco import options_from_connection

            def connect(profile, role):
                return options_from_connection(profile, role=role).connection

        connection = connect(args.profile, args.role)
        try:
            store = StageStore(connection, args.stage)
            return _publish(store, folder, report, args.force)
        finally:
            connection.close()
    else:
        print("error: give --stage or --local (or --dry-run).", file=sys.stderr)
        return 2
    return _publish(store, folder, report, args.force)


def _publish(store, folder: Path, report, force: bool) -> int:
    try:
        published = store.publish(folder, report, force=force)
    except PublishError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"published {published.id} {published.version} to {store.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
