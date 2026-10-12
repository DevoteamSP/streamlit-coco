"""Testing Ask CoCo without a login and without a server.

    VIEWS           one view per frame of the design sheet (streamlit_coco.testing.fixtures)
    harness         one HTML file that mounts the real window on any view
                    (python -m streamlit_coco.testing.harness)
    domdiff         the window before and after, or against the Cockpit's own
                    (python -m streamlit_coco.testing.domdiff)
    ScriptedAgent   the scripted agent, through the real policy and the real gate
                    (streamlit_coco.testing.scripted)

`ScriptedAgent` is read on first use, so importing this package needs neither Streamlit nor the
conversation.
"""

from __future__ import annotations

from streamlit_coco.testing.fixtures import VIEWS

__all__ = ["VIEWS"]


def __getattr__(name: str):
    if name == "ScriptedAgent":
        from streamlit_coco.testing.scripted import ScriptedAgent

        return ScriptedAgent
    raise AttributeError(name)
