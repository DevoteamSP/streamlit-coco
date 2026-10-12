"""Ask CoCo, the tools of the Cortex Code session (feature file section 12.1).

The one place that names tools for the Cortex adapter (utils/coco_agent.py) and the rights (utils/coco_policy.py,
utils/coco_gate.py), so that they are different files. Pure Python. utils/coco_policy.py re-exports TOOLS under the name it
always had.

Since section 12 the session is started with NO tool list: the program offers every built-in tool and every call goes through
the pre-tool hook (a list given to `--allowed-tools` makes the program refuse everything else outright, before any hook or
callback; seen live: "not matched by any --allowed-tools pattern").
"""

# Not sent to the program any more: the tools that the policy knows by name (for SQL the CLI's permission name is "sql", hooks
# are given the tool's name, "sql_execute").
TOOLS = ("Read", "Glob", "Grep", "direct_tool_calling", "Edit", "Write", "Bash", "sql")

# The tools whose whole point is a question to the user: the program asks the host itself (control request "can_use_tool"
# with this name), so the hook lets them through and the adapter turns them into a question or a plan to answer.
QUESTION, PLAN, PLANNING = "askuserquestion", "exitplanmode", "enterplanmode"


def normal(name) -> str:
    """A tool name compared the way streamlit-coco does: lower case, letters and digits only ("ask_user_question" is "AskUserQuestion")."""
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())


def is_sql(name) -> bool:
    return normal(name).startswith("sql")
