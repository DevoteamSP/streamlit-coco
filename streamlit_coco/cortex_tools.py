"""Ask CoCo, the tool names of a Cortex Code session.

The one place that names tools for the Cortex adapter (cortex.py) and the rights (policy.py,
gate.py). Pure Python.

The session is started with NO tool list: the program offers every built-in tool and every call
goes through the pre-tool hook. A list given to `--allowed-tools` makes the program refuse
everything else outright, before any hook or callback (seen live: "not matched by any
--allowed-tools pattern").
"""

# The tools the policy knows by name. For SQL the program's permission name is "sql"; hooks are
# given the tool's name, "sql_execute".
TOOLS = ("Read", "Glob", "Grep", "direct_tool_calling", "Edit", "Write", "Bash", "sql")

# The tools whose whole point is a question to the user: the program asks the host itself
# (control request "can_use_tool" with this name), so the hook lets them through and the adapter
# turns them into a question or a plan to answer.
QUESTION, PLAN, PLANNING = "askuserquestion", "exitplanmode", "enterplanmode"


def normal(name) -> str:
    """Lower case, letters and digits only: "ask_user_question" is "AskUserQuestion"."""
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())


def is_sql(name) -> bool:
    return normal(name).startswith("sql")
