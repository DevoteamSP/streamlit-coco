"""Catalog + filled brief helpers for App Builder (no Streamlit)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "app_builder"))

from engine.brief import (  # noqa: E402
    answers_complete,
    delete_filled,
    partition_questions,
    render_brief_md,
    save_filled,
    slugify,
    unique_slug,
)
from engine.catalog import (  # noqa: E402
    delete_type,
    filter_by_topics,
    get_type,
    load_catalog,
    new_type_template,
    save_type_raw,
)
from engine.generate import build_prompt  # noqa: E402
from engine.paths import TYPES_DIR  # noqa: E402
from engine.skills import (  # noqa: E402
    SHARED_SKILL_ID,
    skill_dirs_for,
    skill_md_files_for,
    write_skill_md,
)


def test_shared_generation_skill_exists() -> None:
    skill = TYPES_DIR / "shared" / "SKILL.md"
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert "any" in text.lower()
    assert "BRIEF.md" in text
    assert not (TYPES_DIR / "shared" / "type.json").exists()


def test_catalog_skips_shared_skill_folder() -> None:
    ids = {item.id for item in load_catalog()}
    assert SHARED_SKILL_ID not in ids


def test_skill_dirs_always_include_shared_then_type() -> None:
    dirs = skill_dirs_for("csv-explorer")
    assert dirs[0] == str((TYPES_DIR / SHARED_SKILL_ID).resolve())
    assert dirs[1] == str((TYPES_DIR / "csv-explorer").resolve())
    files = skill_md_files_for("csv-explorer")
    assert files[0].name == "SKILL.md"
    assert files[0].parent.name == SHARED_SKILL_ID
    assert files[1].parent.name == "csv-explorer"


def test_build_prompt_names_shared_and_type_skill_paths() -> None:
    app_type = get_type("csv-explorer")
    assert app_type is not None
    prompt = build_prompt(app_type, regenerate=False)
    shared = str((TYPES_DIR / SHARED_SKILL_ID / "SKILL.md").resolve())
    typed = str((TYPES_DIR / "csv-explorer" / "SKILL.md").resolve())
    assert shared in prompt
    assert typed in prompt
    assert "You MUST Read these guidelines skill files" in prompt


def test_write_skill_md_roundtrip(tmp_path: Path, monkeypatch) -> None:
    import engine.skills as skills_mod

    monkeypatch.setattr(skills_mod, "TYPES_DIR", tmp_path)
    dest = write_skill_md("demo-skill", "# Hello")
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == "# Hello\n"
    try:
        write_skill_md("Not Valid", "# no")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_each_type_has_at_least_four_questions() -> None:
    for app in load_catalog():
        assert len(app.questions) >= 4, app.id


def test_catalog_loads_live_and_coming_soon() -> None:
    types = {item.id: item for item in load_catalog()}
    assert "semantic-kpis" in types
    assert "data-quality" in types
    assert "csv-explorer" in types
    assert "meeting-recap" in types
    assert "prompt-library" in types
    assert types["call-transcription"].coming_soon is False
    assert types["call-transcription"].needs_snowflake is False
    assert types["csv-explorer"].needs_snowflake is False
    assert types["semantic-kpis"].needs_snowflake is True
    assert types["semantic-kpis"].grounding_kind == "semantic_view"
    assert types["semantic-kpis"].grounding_label == "Semantic view"
    assert types["semantic-kpis"].ships_copilot is False
    assert types["data-quality"].grounding_kind == "tabular"
    assert types["csv-explorer"].grounding_kind == "tabular"
    assert types["call-transcription"].grounding_kind == "documents"
    assert "Local" in types["csv-explorer"].topics


def test_filter_by_topics() -> None:
    types = load_catalog()
    local = filter_by_topics(types, ["Local"])
    assert local
    assert all(not item.needs_snowflake for item in local)
    snow = filter_by_topics(types, ["Snowflake"])
    assert all(item.needs_snowflake for item in snow)
    assert filter_by_topics(types, None) == types


def test_required_answers() -> None:
    app_type = get_type("semantic-kpis")
    assert app_type is not None
    assert answers_complete(app_type, {}) == [
        "semantic_view",
        "metrics",
        "grain",
        "audience_note",
        "comparison",
    ]
    filled = {
        "semantic_view": "DEMO:sales_sv",
        "metrics": ["Revenue", "Orders"],
        "grain": "month",
        "audience_note": "Sales ops lead — checks overnight bookings.",
        "comparison": "none",
    }
    assert answers_complete(app_type, filled) == []


def test_render_and_save_brief(tmp_path: Path) -> None:
    app_type = get_type("semantic-kpis")
    assert app_type is not None
    answers = {
        "semantic_view": "DEMO:sales_sv",
        "metrics": ["Revenue"],
        "grain": "month",
        "user_brief": "Three KPIs only. No export. Sales ops, every morning.",
    }
    md = render_brief_md(app_type, answers)
    assert "KPI presentation" in md
    assert "What this does not do" in md
    assert "What the owner wants" in md
    assert "Three KPIs only" in md
    assert "DEMO:sales_sv" in md
    dest = save_filled(
        "northwind-kpis",
        app_type,
        answers,
        app_name="Northwind KPIs",
        out_dir=tmp_path,
    )
    assert (dest / "brief.json").is_file()
    assert (dest / "BRIEF.md").is_file()
    assert (dest / "sketches").is_dir()
    payload = (dest / "brief.json").read_text(encoding="utf-8")
    assert "Northwind KPIs" in payload
    assert "Northwind KPIs" in (dest / "BRIEF.md").read_text(encoding="utf-8")


def test_save_filled_rewrites_brief_md(tmp_path: Path) -> None:
    app_type = get_type("prompt-library")
    assert app_type is not None
    save_filled(
        "pack",
        app_type,
        {"user_brief": "first draft", "source": "demo pack"},
        app_name="Pack",
        out_dir=tmp_path,
    )
    dest = save_filled(
        "pack",
        app_type,
        {
            "user_brief": "cards first, easy to copy",
            "source": "I will add markdown files",
            "layout": "list",
        },
        app_name="Pack",
        out_dir=tmp_path,
    )
    md = (dest / "BRIEF.md").read_text(encoding="utf-8")
    assert "cards first, easy to copy" in md
    assert "I will add markdown files" in md
    assert "list" in md
    assert "first draft" not in md


def test_slugify_and_unique_slug(tmp_path: Path) -> None:
    assert slugify("Q3 Call Recap!") == "q3-call-recap"
    assert slugify("  ") == "app"
    assert unique_slug("demo", out_dir=tmp_path) == "demo"
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "brief.json").write_text("{}\n", encoding="utf-8")
    assert unique_slug("demo", out_dir=tmp_path) == "demo-2"


def test_delete_filled(tmp_path: Path) -> None:
    app_type = get_type("csv-explorer")
    assert app_type is not None
    dest = save_filled("throwaway", app_type, {}, app_name="Throwaway", out_dir=tmp_path)
    assert dest.is_dir()
    delete_filled("throwaway", out_dir=tmp_path)
    assert not dest.exists()
    try:
        delete_filled("..", out_dir=tmp_path)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_partition_questions_by_type() -> None:
    call = get_type("call-transcription")
    assert call is not None
    data, found, asked = partition_questions(call.questions)
    assert [q.id for q in data] == ["source"]
    assert found == []
    assert [q.id for q in asked] == ["focus", "audience", "tone"]

    recap = get_type("meeting-recap")
    assert recap is not None
    data, found, asked = partition_questions(recap.questions)
    assert [q.id for q in data] == ["source"]
    assert found == []
    assert [q.id for q in asked] == ["audience", "include", "length"]

    kpi = get_type("semantic-kpis")
    assert kpi is not None
    data, found, asked = partition_questions(kpi.questions)
    assert [q.id for q in data] == ["semantic_view"]
    assert [q.id for q in found] == ["metrics", "grain", "filters"]
    assert [q.id for q in asked] == [
        "audience_note",
        "must_not",
        "comparison",
        "hero_metric",
    ]


def test_semantic_kpis_infer_and_never_inferred() -> None:
    app_type = get_type("semantic-kpis")
    assert app_type is not None
    by_id = {q.id: q for q in app_type.questions}
    assert by_id["metrics"].infer == "metrics"
    assert by_id["grain"].infer == "grain"
    assert by_id["filters"].infer == "filters"
    assert by_id["audience_note"].required is True
    assert by_id["audience_note"].infer is None
    assert by_id["must_not"].required is False
    assert by_id["must_not"].infer is None
    assert by_id["semantic_view"].infer is None


def test_save_and_delete_type(tmp_path: Path) -> None:
    payload = new_type_template("demo-admin")
    payload["name"] = "Admin demo"
    dest = save_type_raw(payload, types_dir=tmp_path)
    assert dest.is_file()
    loaded = {item.id: item for item in load_catalog(tmp_path)}
    assert loaded["demo-admin"].name == "Admin demo"
    delete_type("demo-admin", types_dir=tmp_path)
    assert not (tmp_path / "demo-admin").exists()


def test_save_type_rejects_bad_id(tmp_path: Path) -> None:
    payload = new_type_template("ok")
    payload["id"] = "Not Valid"
    try:
        save_type_raw(payload, types_dir=tmp_path)
    except ValueError as exc:
        assert "lowercase" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")


def test_save_and_delete_type_reject_shared(tmp_path: Path) -> None:
    payload = new_type_template(SHARED_SKILL_ID)
    try:
        save_type_raw(payload, types_dir=tmp_path)
    except ValueError as exc:
        assert SHARED_SKILL_ID in str(exc)
    else:
        raise AssertionError("expected ValueError")
    try:
        delete_type(SHARED_SKILL_ID, types_dir=tmp_path)
    except ValueError as exc:
        assert SHARED_SKILL_ID in str(exc)
    else:
        raise AssertionError("expected ValueError")
