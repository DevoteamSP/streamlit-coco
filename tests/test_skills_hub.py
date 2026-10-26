"""The skills shop example: validation, the stores, the service and the publish command.

No Snowflake: the stage is a fake connection over a temporary folder that answers the three
statements the shop uses (list, get, put) and keeps every statement it was sent.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

APP = Path(__file__).resolve().parents[1] / "examples" / "skills_hub"
sys.path.insert(0, str(APP))

from shop import cli  # noqa: E402
from shop.demo import build_demo_store  # noqa: E402
from shop.service import Shop  # noqa: E402
from shop.skill import (  # noqa: E402
    folder_hash,
    parse_front_matter,
    semver_key,
    validate_folder,
)
from shop.stores import (  # noqa: E402
    CachedStore,
    LocalFolderStore,
    NotOnAStage,
    PublishError,
    StageStore,
)

from streamlit_coco.managed import ManagedOptions  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)
STAMP = "2026-10-26T12:00:00Z"
STAGE = "DB.SKILLS.SHOP_STAGE"


def write_skill(root: Path, name="demo-skill", version="1.0.0", extra=None, body="Do the thing.\n"):
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\nversion: {version}\ndescription: A demo skill.\npack: demo\n"
        f"---\n{body}",
        encoding="utf-8",
    )
    for rel, content in (extra or {}).items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(content, encoding="utf-8")
    return folder


@pytest.fixture
def tmp(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------- front matter, hash


def test_front_matter_is_read_and_the_body_is_left():
    meta, body = parse_front_matter(
        '---\nname: x\n# a comment\ndescription: one\n  two\nicon: ":material/a:"\n---\nBody\n'
    )
    assert meta == {"name": "x", "description": "one two", "icon": ":material/a:"}
    assert body == "Body\n"
    assert parse_front_matter("no front matter") == ({}, "no front matter")


def test_semver_orders_numbers_not_text():
    assert sorted(["1.10.0", "1.2.0", "1.9.9"], key=semver_key) == ["1.2.0", "1.9.9", "1.10.0"]


def test_the_hash_follows_the_content_and_the_names_not_the_place(tmp):
    a = write_skill(tmp / "a", extra={"references/n.txt": "one"})
    b = write_skill(tmp / "b", extra={"references/n.txt": "one"})
    files = ["SKILL.md", "references/n.txt"]
    assert folder_hash(a, files) == folder_hash(b, files)
    (b / "references" / "n.txt").write_text("two")
    assert folder_hash(a, files) != folder_hash(b, files)


# ---------------------------------------------------------------------------- validation


def test_a_good_folder_passes_and_describes_itself(tmp):
    folder = write_skill(tmp, extra={"references/notes.md": "notes", "assets/a.svg": "<svg/>"})
    report = validate_folder(folder)
    assert report.ok and not report.warnings
    skill = report.skill
    assert (skill.id, skill.version, skill.pack, skill.title) == (
        "demo-skill",
        "1.0.0",
        "demo",
        "demo-skill",
    )
    assert skill.files == ("SKILL.md", "assets/a.svg", "references/notes.md")
    assert not skill.has_scripts and len(skill.sha256) == 64


def test_scripts_are_listed_for_the_reviewer(tmp):
    report = validate_folder(write_skill(tmp, extra={"scripts/run.py": "print(1)"}))
    assert report.ok and report.skill.has_scripts
    assert "scripts/run.py" in report.warnings[0]


def _deep(folder: Path) -> None:
    deep = folder / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (deep / "e.md").write_text("x")


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda f: (f / "SKILL.md").unlink(), "SKILL.md is missing"),
        (lambda f: (f / "x.exe").write_text("x"), "not allowed"),
        (lambda f: (f / "bad name.md").write_text("x"), "the name must be"),
        (lambda f: _deep(f), "levels deep"),
        (lambda f: (f / "k.txt").write_text("-----BEGIN RSA PRIVATE KEY-----"), "private key"),
        (lambda f: (f / "k.txt").write_text("password = abcdefghijklmnop1234"), "credential"),
        (lambda f: (f / "big.txt").write_text("x" * 1_000_001), "at most"),
    ],
)
def test_what_may_not_be_published(tmp, mutate, expected):
    folder = write_skill(tmp)
    mutate(folder)
    report = validate_folder(folder)
    assert not report.ok and any(expected in e for e in report.errors), report.errors


def test_a_link_is_refused_even_to_a_harmless_file(tmp):
    folder = write_skill(tmp)
    (tmp / "outside.md").write_text("x")
    os.symlink(tmp / "outside.md", folder / "link.md")
    assert any("link" in e for e in validate_folder(folder).errors)


@pytest.mark.parametrize(
    "front, expected",
    [
        ("name: Bad_Name\nversion: 1.0.0\ndescription: d", "`name`"),
        ("name: ok\nversion: 1.0\ndescription: d", "`version`"),
        ("name: ok\nversion: 1.0.0", "`description`"),
        ("name: ok\nversion: 1.0.0\ndescription: " + "x" * 401, "at most 400"),
    ],
)
def test_the_front_matter_is_checked(tmp, front, expected):
    folder = tmp / "f"
    folder.mkdir()
    (folder / "SKILL.md").write_text(f"---\n{front}\n---\nbody")
    assert any(expected in e for e in validate_folder(folder).errors)


def test_the_samples_of_the_shop_pass_their_own_gate():
    for folder in sorted((APP / "samples").iterdir()):
        report = validate_folder(folder)
        assert report.ok, (folder.name, report.errors)
        assert report.skill.run_prompt, folder.name


# ---------------------------------------------------------------------------- the local store


def test_publish_then_read_back(tmp):
    store = LocalFolderStore(tmp / "shop", now=NOW)
    folder = write_skill(tmp, extra={"references/n.md": "n"})
    skill = store.publish(folder, validate_folder(folder))
    assert skill.published_at == STAMP
    assert store.index() == [skill]
    assert "Do the thing." in store.read_skill_md(skill)
    assert (tmp / "shop" / "skills" / "demo-skill" / "1.0.0" / "references" / "n.md").is_file()


def test_a_published_version_is_not_replaced(tmp):
    store = LocalFolderStore(tmp / "shop", now=NOW)
    folder = write_skill(tmp)
    store.publish(folder, validate_folder(folder))
    with pytest.raises(PublishError, match="bump the version"):
        store.publish(folder, validate_folder(folder))
    (folder / "SKILL.md").write_text(
        "---\nname: demo-skill\nversion: 1.0.0\ndescription: Fixed.\n---\nbody"
    )
    again = store.publish(folder, validate_folder(folder), force=True)
    assert [s.description for s in store.index()] == [again.description] == ["Fixed."]


def test_a_report_with_errors_publishes_nothing(tmp):
    store = LocalFolderStore(tmp / "shop")
    folder = tmp / "empty"
    folder.mkdir()
    with pytest.raises(PublishError):
        store.publish(folder, validate_folder(folder))
    assert not (tmp / "shop").exists()


def test_a_local_store_cannot_feed_the_managed_agent(tmp):
    store = LocalFolderStore(tmp / "shop", now=NOW)
    folder = write_skill(tmp)
    skill = store.publish(folder, validate_folder(folder))
    with pytest.raises(NotOnAStage):
        store.skill_path(skill)


# ---------------------------------------------------------------------------- the stage store


class FakeCursor:
    def __init__(self, conn):
        self.conn, self.rows = conn, []

    def execute(self, sql):
        self.conn.statements.append(sql)
        verb = sql.split()[0].lower()
        getattr(self, f"_{verb}")(sql)

    def _list(self, sql):
        prefix = sql.split(f"@{STAGE}/", 1)[1]
        self.rows = [
            (f"shop_stage/{p.relative_to(self.conn.root).as_posix()}", p.stat().st_size, "", "")
            for p in sorted(self.conn.root.rglob("*"))
            if p.is_file() and p.relative_to(self.conn.root).as_posix().startswith(prefix)
        ]

    def _get(self, sql):
        remote = sql.split(f"@{STAGE}/", 1)[1].split(" '", 1)[0]
        dest = Path(sql.split("'file://", 1)[1].rstrip("'"))
        source = self.conn.root / remote
        if not source.is_file():
            raise RuntimeError(f"no such file on the stage: {remote}")
        shutil.copyfile(source, dest / source.name)
        self.rows = [(source.name, "DOWNLOADED")]

    def _put(self, sql):
        local = Path(sql.split("'file://", 1)[1].split("'", 1)[0])
        remote = sql.split(f"@{STAGE}/", 1)[1].split(" ", 1)[0]
        target = self.conn.root / remote / local.name
        if target.exists() and "overwrite=false" in sql:
            self.rows = [(local.name, "SKIPPED")]
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local, target)
        self.rows = [(local.name, "UPLOADED")]

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, root: Path):
        self.root, self.statements, self.closed = root, [], False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


@pytest.fixture
def stage(tmp):
    conn = FakeConnection(tmp / "stage")
    (tmp / "stage").mkdir()
    return conn, StageStore(conn, STAGE, now=NOW)


def test_an_empty_stage_is_an_empty_shop(stage):
    assert stage[1].index() == []


def test_publish_to_a_stage_and_read_it_back(tmp, stage):
    conn, store = stage
    folder = write_skill(tmp, extra={"references/n.md": "n", "scripts/a.py": "print(1)"})
    skill = store.publish(folder, validate_folder(folder))
    assert store.index() == [skill]
    on_stage = sorted(
        p.relative_to(conn.root).as_posix() for p in conn.root.rglob("*") if p.is_file()
    )
    assert on_stage == [
        "skills/demo-skill/1.0.0/SKILL.md",
        "skills/demo-skill/1.0.0/references/n.md",
        "skills/demo-skill/1.0.0/scripts/a.py",
        "skills/index.json",
    ]
    assert store.skill_path(skill) == f"@{STAGE}/skills/demo-skill/1.0.0"
    assert "Do the thing." in store.read_skill_md(skill)
    assert json.loads((conn.root / "skills/index.json").read_text())["schema"] == 1


def test_a_second_publish_of_a_version_is_refused_before_anything_is_sent(tmp, stage):
    conn, store = stage
    folder = write_skill(tmp)
    store.publish(folder, validate_folder(folder))
    sent = len(conn.statements)
    with pytest.raises(PublishError, match="bump the version"):
        store.publish(folder, validate_folder(folder))
    assert all(s.split()[0].lower() == "list" for s in conn.statements[sent:])


def test_the_index_keeps_every_version_in_order(tmp, stage):
    _, store = stage
    for version in ("1.10.0", "1.2.0"):
        folder = write_skill(tmp / version, version=version)
        store.publish(folder, validate_folder(folder))
    assert [s.version for s in store.index()] == ["1.2.0", "1.10.0"]


def test_only_checked_names_reach_a_statement(tmp):
    for bad in ("one.two", "a.b.c; drop table x", "a.b.c d", "a.'b'.c", ""):
        with pytest.raises(ValueError):
            StageStore(FakeConnection(tmp), bad)
    assert StageStore(FakeConnection(tmp), "@db.s.st").stage == "db.s.st"
    with pytest.raises(ValueError):
        StageStore._url("/tmp/it's")


def test_the_store_does_not_close_the_connection_it_was_given(stage):
    conn, store = stage
    store.index()
    assert not conn.closed


def test_the_cache_serves_the_index_until_it_is_old_or_refreshed(tmp, stage):
    conn, store = stage
    clock = iter(range(0, 1000, 10))
    cached = CachedStore(store, ttl=25, clock=lambda: next(clock))
    cached.index()
    seen = len(conn.statements)
    cached.index()
    assert len(conn.statements) == seen  # the second read came from memory
    cached.refresh()
    cached.index()
    assert len(conn.statements) > seen
    folder = write_skill(tmp)
    cached.publish(folder, validate_folder(folder))
    assert [s.id for s in cached.index()] == ["demo-skill"]


# ---------------------------------------------------------------------------- the service


@pytest.fixture
def shop(tmp):
    store = LocalFolderStore(tmp / "shop", now=NOW)
    for name, version, pack in (
        ("alpha", "1.0.0", "x"),
        ("alpha", "1.2.0", "x"),
        ("beta", "0.1.0", "y"),
    ):
        folder = tmp / f"{name}-{version}" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(
            f"---\nname: {name}\nversion: {version}\ndescription: The {name} skill for sql.\n"
            f"pack: {pack}\n---\n# {name}\nBody of {name} {version}.\n"
        )
        store.publish(folder, validate_folder(folder))
    return Shop(store)


def test_the_shop_lists_the_latest_version_of_each_skill(shop):
    assert [(s.id, s.version) for s in shop.skills()] == [("alpha", "1.2.0"), ("beta", "0.1.0")]
    assert shop.packs() == ["x", "y"]
    assert [s.version for s in shop.versions("alpha")] == ["1.2.0", "1.0.0"]


def test_search_and_pack_filter(shop):
    assert [s.id for s in shop.skills(query="BETA")] == ["beta"]
    assert [s.id for s in shop.skills(query="skill sql", pack="y")] == ["beta"]
    assert shop.skills(query="nothing like this") == []


def test_get_and_about(shop):
    assert shop.get("alpha").version == "1.2.0"
    assert shop.get("alpha", "1.0.0").version == "1.0.0"
    with pytest.raises(KeyError):
        shop.get("alpha", "9.9.9")
    assert shop.about(shop.get("alpha")) == "# alpha\nBody of alpha 1.2.0."


def test_verify_accepts_what_was_published_and_catches_a_change(shop, tmp):
    skill = shop.get("alpha")
    assert shop.verify(skill).ok
    (tmp / "shop" / skill.folder / "SKILL.md").write_text("changed")
    verdict = shop.verify(skill)
    assert not verdict.ok and "changed" in verdict.problems[0]


def test_verify_catches_a_file_added_to_the_folder(shop, tmp):
    skill = shop.get("alpha")
    (tmp / "shop" / skill.folder / "scripts").mkdir()
    (tmp / "shop" / skill.folder / "scripts" / "evil.py").write_text("print(1)")
    verdict = shop.verify(skill)
    assert not verdict.ok and "added: scripts/evil.py" in verdict.problems[0]


def test_verify_catches_a_file_taken_away(shop, tmp):
    skill = shop.get("alpha")
    (tmp / "shop" / skill.folder / "SKILL.md").unlink()
    verdict = shop.verify(skill)
    assert not verdict.ok and "missing: SKILL.md" in verdict.problems[0]


def test_verify_on_a_stage_sees_an_added_file_too(tmp, stage):
    conn, store = stage
    folder = write_skill(tmp, extra={"references/n.md": "n"})
    skill = store.publish(folder, validate_folder(folder))
    shop = Shop(store)
    assert shop.verify(skill).ok
    (conn.root / skill.folder / "references" / "extra.md").write_text("sneaked in")
    verdict = shop.verify(skill)
    assert not verdict.ok and "added: references/extra.md" in verdict.problems[0]


def test_verify_says_so_when_the_folder_is_gone(shop, tmp):
    skill = shop.get("alpha")
    shutil.rmtree(tmp / "shop" / skill.folder)
    verdict = shop.verify(skill)
    assert not verdict.ok and "missing: SKILL.md" in verdict.problems[0]


def test_a_chat_has_one_skill_and_does_not_own_the_connection(tmp, stage):
    conn, store = stage
    folder = write_skill(tmp)
    store.publish(folder, validate_folder(folder))
    shop = Shop(store)
    base = ManagedOptions(
        account="a", token="t", stage_skills=[{"name": "old", "path": "@x"}], connection=conn
    )
    options = shop.chat_options(base, shop.get("demo-skill"))
    assert options.stage_skills == [
        {"name": "demo-skill", "path": f"@{STAGE}/skills/demo-skill/1.0.0"}
    ]
    assert options.connection is None and base.connection is conn
    assert options.spec()["stage_skills"] == options.stage_skills
    assert options.spec()["permission_policy"] == "always_ask"


# ------------------------------------------------------------ the demo and the command


def test_the_demo_shop_is_built_through_the_gate():
    shop = Shop(build_demo_store())
    assert {s.id for s in shop.skills()} == {
        "release-notes-writer",
        "sql-style-review",
        "csv-profile",
    }
    assert shop.get("csv-profile").has_scripts
    assert shop.verify(shop.get("csv-profile")).ok


def test_the_command_validates_and_publishes_locally(tmp, capsys):
    folder = write_skill(tmp)
    assert cli.main([str(folder), "--dry-run"]) == 0
    assert not (tmp / "shop").exists()
    assert cli.main([str(folder), "--local", str(tmp / "shop")]) == 0
    assert cli.main([str(folder), "--local", str(tmp / "shop")]) == 1  # the version exists
    assert "bump the version" in capsys.readouterr().err
    assert cli.main([str(folder), "--local", str(tmp / "shop"), "--force"]) == 0


def test_the_command_refuses_a_bad_folder_and_a_missing_target(tmp, capsys):
    (tmp / "empty").mkdir()
    assert cli.main([str(tmp / "empty"), "--dry-run"]) == 1
    assert "SKILL.md is missing" in capsys.readouterr().err
    folder = write_skill(tmp)
    assert cli.main([str(folder)]) == 2
    assert cli.main([str(folder), "--stage", STAGE]) == 2  # --stage needs --profile


def test_the_command_publishes_to_a_stage_and_closes_its_connection(tmp):
    conn = FakeConnection(tmp / "stage")
    (tmp / "stage").mkdir()
    seen = {}

    def connect(profile, role):
        seen.update(profile=profile, role=role)
        return conn

    folder = write_skill(tmp)
    code = cli.main(
        [str(folder), "--stage", STAGE, "--profile", "p", "--role", "R"], connect=connect
    )
    assert code == 0 and seen == {"profile": "p", "role": "R"} and conn.closed
    assert (tmp / "stage" / "skills" / "index.json").is_file()


# ------------------------------------------------------------------------------ the page


def _page(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("STREAMLIT_COCO_AGENT", "mock")
    return AppTest.from_file(str(APP / "app.py"), default_timeout=30).run()


def test_the_page_lists_the_sample_skills(monkeypatch):
    app = _page(monkeypatch)
    assert not app.exception
    text = " ".join(m.value for m in app.markdown)
    for title in ("Release notes writer", "SQL style review", "CSV profile"):
        assert title in text
    assert any(b.label == "Open" for b in app.button)


def test_opening_a_skill_shows_it_and_a_warning_for_code(monkeypatch):
    app = _page(monkeypatch)
    next(b for b in app.button if b.key == "open-csv-profile").click().run()
    assert not app.exception
    assert any("carries code" in w.value for w in app.warning)
    assert any(b.label == "Chat with this skill" for b in app.button)
    next(b for b in app.button if b.label == "Back to the shop").click().run()
    assert any(b.key == "open-sql-style-review" for b in app.button)


def test_search_narrows_the_shop(monkeypatch):
    app = _page(monkeypatch)
    app.text_input[0].set_value("csv").run()
    keys = [b.key for b in app.button if b.key and b.key.startswith("open-")]
    assert keys == ["open-csv-profile"]


# ------------------------------------------------------------------ inside the Native App


def test_the_service_says_it_is_a_native_app_only_by_its_spec():
    from shop import native

    assert native.in_native_app({"SKILLS_HUB_NATIVE": "1"})
    assert not native.in_native_app({})
    assert not native.in_native_app({"SKILLS_HUB_NATIVE": "0"})


def test_the_stage_is_the_applications_own():
    from shop import native

    assert native.stage_name({"SNOWFLAKE_DATABASE": "SHOP_APP"}) == "SHOP_APP.DATA.SKILLS_STAGE"
    env = {"SNOWFLAKE_DATABASE": "D", "SKILLS_STAGE_SCHEMA": "S", "SKILLS_STAGE": "T"}
    assert native.stage_name(env) == "D.S.T"
    with pytest.raises(RuntimeError, match="SNOWFLAKE_DATABASE"):
        native.stage_name({})


def test_the_connection_uses_the_service_token_read_when_it_opens(tmp):
    from shop import native

    token = tmp / "token"
    token.write_text("T-OLD\n")
    seen = []
    env = {"SNOWFLAKE_HOST": "h.internal", "SNOWFLAKE_ACCOUNT": "ACC", "SNOWFLAKE_DATABASE": "APP"}
    native.open_connection(env, token, connect=lambda **kw: seen.append(kw) or object())
    token.write_text("T-NEW\n")
    native.open_connection(env, token, connect=lambda **kw: seen.append(kw) or object())
    assert [kw["token"] for kw in seen] == ["T-OLD", "T-NEW"]
    assert seen[0] == {
        "host": "h.internal",
        "account": "ACC",
        "authenticator": "oauth",
        "token": "T-OLD",
        "database": "APP",
    }


def test_a_missing_service_variable_is_named(tmp):
    from shop import native

    with pytest.raises(RuntimeError, match="SNOWFLAKE_HOST"):
        native.open_connection({"SNOWFLAKE_ACCOUNT": "A"}, tmp / "t", connect=lambda **kw: None)


def test_the_managed_options_follow_the_session_token_of_the_connection():
    from shop import native

    conn = SimpleNamespace(host="h.internal", rest=SimpleNamespace(token="S1"))
    options = native.managed_options(conn)
    assert options.base_url == "https://h.internal" and options.connection is conn
    assert options.auth.get_token() == "S1"
    conn.rest.token = "S2"
    assert options.auth.get_token() == "S2"
    assert "S2" not in repr(options.auth)


def test_bootstrap_publishes_the_bundled_skills_once(tmp, stage):
    from shop.bootstrap import publish_bundled

    _, store = stage
    first = publish_bundled(store, APP / "samples")
    assert sorted(first) == [
        "csv-profile 1.0.0",
        "release-notes-writer 1.0.0",
        "sql-style-review 1.0.0",
    ]
    assert publish_bundled(store, APP / "samples") == []  # a restart publishes nothing
    assert len(store.index()) == 3


def test_bootstrap_adds_only_what_is_new(tmp, stage):
    from shop.bootstrap import publish_bundled

    _, store = stage
    bundled = tmp / "bundled"
    write_skill(bundled, "one", "1.0.0")
    assert publish_bundled(store, bundled) == ["one 1.0.0"]
    write_skill(bundled, "one", "1.1.0")
    write_skill(bundled, "two", "1.0.0")
    shutil.rmtree(bundled / "one")
    write_skill(bundled, "one", "1.1.0")
    assert sorted(publish_bundled(store, bundled)) == ["one 1.1.0", "two 1.0.0"]


def test_bootstrap_refuses_a_bundled_folder_that_fails_the_gate(tmp, stage):
    from shop.bootstrap import publish_bundled

    _, store = stage
    bundled = tmp / "bundled"
    (bundled / "broken").mkdir(parents=True)
    with pytest.raises(PublishError, match="broken"):
        publish_bundled(store, bundled)
