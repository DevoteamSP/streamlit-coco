"""Build / regenerate prompts for CoCo."""

from __future__ import annotations

from engine.brief import APP_FILE, BRIEF_MD, SKETCH_DIR
from engine.catalog import AppType
from engine.skills import SHARED_SKILL_ID, skill_md_files_for, skill_md_path


def build_prompt(app_type: AppType, *, regenerate: bool) -> str:
    action = (
        f"Overwrite `{APP_FILE}` from the filled brief (regenerate)."
        if regenerate
        else f"Create `{APP_FILE}` from the filled brief."
    )
    skill = app_type.guidelines_skill or SHARED_SKILL_ID
    skill_files = skill_md_files_for(skill)
    if not skill_files:
        skill_files = [skill_md_path(SHARED_SKILL_ID)]
    read_skills = "\n".join(f"   - `{path}`" for path in skill_files)
    return f"""You are generating a Streamlit app of type **{app_type.name}**.
The app name and owner brief are in `{BRIEF_MD}`.

Working directory is this app folder. {action}

Do this:
1. Read `{BRIEF_MD}` in full (context, allows, does not, owner's brief, answers).
   Honor **What the owner wants** for this instance. Never violate the type's
   **What this does not do**.
2. Read any files under `{SKETCH_DIR}/` if present.
   Treat them as the owner's layout intent.
3. You MUST Read these guidelines skill files in full (they are outside cwd;
   use the exact paths; they are also mounted via add_dirs):
{read_skills}
4. Write `{APP_FILE}` here. Optional: `requirements` comments at the top if needed.
5. If answers use the demo pack / fixture, read `data.csv` in this folder
   (already copied). Do not invent tables or warehouses.
6. Do **not** `CREATE SEMANTIC VIEW`, do not migrate BI,
   do not write outside this folder.

Honor "What this does not do". Prefer Streamlit 1.57+ APIs
(`width="stretch"`, no `use_container_width`).
If a required answer is missing, AskUser — do not guess grounding
(views, tables, files).

After writing `{APP_FILE}`:
7. If `CHECKLIST.md` exists in the `{skill}` guidelines skill directory,
   read it (and `reference/streamlit_app.py` if present and unread).
   Verify the file you wrote against every checklist item. If something
   fails, Edit once. If there is no checklist, skip this step — do not
   mention the missing file.
8. If `.preview.log` in this folder shows a traceback, make **one**
   corrective Edit (same idea as Fix-with-CoCo / `default_fix_prompt`),
   then stop — do not loop.
"""
