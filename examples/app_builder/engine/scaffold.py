"""Disconnected demo scaffold when CoCo is not used (UC6)."""

from __future__ import annotations

import shutil
from pathlib import Path

from engine.brief import APP_FILE, slug_dir
from engine.catalog import AppType
from engine.paths import FIXTURES_DIR

_KPI_APP = '''\
"""KPI presentation — demo scaffold (disconnected). Generated locally, not by CoCo."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data.csv"

st.set_page_config(page_title="KPI presentation", layout="wide")
st.title("KPI presentation")
st.caption("Demo fixture · disconnected — no warehouse")

if not DATA.is_file():
    st.error("Missing `data.csv` next to this app.")
    st.stop()

df = pd.read_csv(DATA)
revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0.0
orders = int(df["orders"].sum()) if "orders" in df.columns else 0
margin = float(df["margin"].mean()) if "margin" in df.columns else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Revenue", f"${revenue:,.0f}")
c2.metric("Orders", f"{orders:,}")
c3.metric("Avg margin", f"{margin:.1%}" if margin <= 1 else f"{margin:.1f}")

grain = st.session_state.get("grain") or "month"
if "month" in df.columns:
    st.line_chart(df.set_index("month")[["revenue"]] if "revenue" in df.columns else df)
st.dataframe(df, width="stretch")
'''

_DQ_APP = '''\
"""Data quality — demo scaffold (disconnected). Generated locally, not by CoCo."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data.csv"

st.set_page_config(page_title="Data quality", layout="wide")
st.title("Data quality")
st.caption("Demo fixture · disconnected — no warehouse")

if not DATA.is_file():
    st.error("Missing `data.csv` next to this app.")
    st.stop()

df = pd.read_csv(DATA)
rows = len(df)
nulls = int(df.isna().sum().sum())
dupes = int(df.duplicated().sum())

c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{rows:,}")
c2.metric("Null cells", f"{nulls:,}")
c3.metric("Duplicate rows", f"{dupes:,}")
st.dataframe(df, width="stretch")
st.subheader("Nulls by column")
st.bar_chart(df.isna().sum())
'''

_CALL_APP = '''\
"""Call transcription — demo scaffold. Local file, no Snowflake."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "transcript.txt"

st.set_page_config(page_title="Call transcription", layout="wide")
st.title("Call transcription")
st.caption("Local transcript · no Snowflake")

if not DATA.is_file():
    st.error("Missing `transcript.txt` next to this app.")
    st.stop()

text = DATA.read_text(encoding="utf-8")
query = st.text_input("Search")
st.text_area("Transcript", value=text, height=240)
if query:
    hits = [line for line in text.splitlines() if query.lower() in line.lower()]
    st.caption(f"{len(hits)} line(s) match")
    for line in hits:
        st.markdown(f"- {line}")
st.subheader("Focus")
st.markdown("- Action items\\n- Risks\\n- Next meeting")
'''

_CSV_APP = '''\
"""CSV explorer — demo scaffold. Local file, no Snowflake."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data.csv"

st.set_page_config(page_title="CSV explorer", layout="wide")
st.title("CSV explorer")
st.caption("Local CSV · no Snowflake")

if not DATA.is_file():
    st.error("Missing `data.csv` next to this app.")
    st.stop()

df = pd.read_csv(DATA)
if "region" in df.columns:
    regions = ["All", *sorted(df["region"].dropna().unique())]
    picked = st.selectbox("region", regions)
    if picked != "All":
        df = df[df["region"] == picked]
st.bar_chart(df.select_dtypes("number"))
st.dataframe(df, width="stretch")
'''

_RECAP_APP = '''\
"""Meeting recap — demo scaffold. Local file, no Snowflake."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "notes.md"

st.set_page_config(page_title="Meeting recap", layout="wide")
st.title("Meeting recap")
st.caption("Local notes · no Snowflake")

if not DATA.is_file():
    st.error("Missing `notes.md` next to this app.")
    st.stop()

st.markdown(DATA.read_text(encoding="utf-8"))
'''

_PROMPTS_APP = '''\
"""Prompt library — demo scaffold. Local file, no Snowflake."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "prompts.md"

st.set_page_config(page_title="Prompt library", layout="wide")
st.title("Prompt library")
st.caption("Local pack · no Snowflake")

if not DATA.is_file():
    st.error("Missing `prompts.md` next to this app.")
    st.stop()

st.markdown(DATA.read_text(encoding="utf-8"))
'''

_SCAFFOLDS = {
    "semantic-kpis": (_KPI_APP, "data.csv"),
    "data-quality": (_DQ_APP, "data.csv"),
    "csv-explorer": (_CSV_APP, "data.csv"),
    "call-transcription": (_CALL_APP, "transcript.txt"),
    "meeting-recap": (_RECAP_APP, "notes.md"),
    "prompt-library": (_PROMPTS_APP, "prompts.md"),
}

_FIXTURE_DEST = {
    "semantic-kpis": "data.csv",
    "data-quality": "data.csv",
    "csv-explorer": "data.csv",
    "call-transcription": "transcript.txt",
    "meeting-recap": "notes.md",
    "prompt-library": "prompts.md",
}


def _find_fixture(name: str) -> Path | None:
    exact = FIXTURES_DIR / name
    if exact.is_file():
        return exact
    matches = sorted(FIXTURES_DIR.glob(f"{name}.*"))
    return matches[0] if matches else None


def copy_fixture(app_type: AppType, dest: Path) -> Path | None:
    name = app_type.demo_fixture
    if not name:
        return None
    src = _find_fixture(name)
    if src is None:
        return None
    dest.mkdir(parents=True, exist_ok=True)
    target_name = _FIXTURE_DEST.get(app_type.id) or src.name
    target = dest / target_name
    shutil.copy2(src, target)
    return target


def write_demo_scaffold(app_type: AppType, slug: str) -> Path:
    dest = slug_dir(slug)
    dest.mkdir(parents=True, exist_ok=True)
    copy_fixture(app_type, dest)
    source, _fixture = _SCAFFOLDS.get(app_type.id, (_KPI_APP, ""))
    path = dest / APP_FILE
    path.write_text(source, encoding="utf-8")
    return path
