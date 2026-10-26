"""Every sentence Ask CoCo writes, in one table: key -> English text.

Key naming (one dict, two families):

    window.<area>.<name>   written by the browser side (static/coco/*.js), read there as
                           L('<area>.<name>').
    agent.<name>           written by the conversation, in Python (streamlit_coco.conversation
                           reports its own keys here).
    Any other prefix is free for a host's own sentences; nothing reads it but the host.

Rules of the table:

- ``{name}`` is a slot the writer fills; ``_one`` / ``_other`` suffixes (``rows_one``,
  ``rows_other``) are the singular and the plural, because a translation may not form a plural
  by adding an "s".
- A value may start or end with a space or a colon where the sentence is read aloud after a
  prefix ("You: ").
- ``ask_coco(labels={key: text})`` overrides any key; a key the table does not know is passed
  through untouched, so a host can keep its own sentences next to the package's. Texts written by
  a policy (a request's question, a command's plain name) are not here: they are the policy's own.
- The defaults name no host: a host that wants its own words (the Cockpit's "Cockpit" and
  "make cockpit") passes them through ``labels=``.
"""

from __future__ import annotations

DEFAULT: dict[str, str] = {
    # ---- the shell: launcher, header, field
    "window.launcher.label": "Ask CoCo",
    "window.launcher.working": "CoCo is answering. Open Ask CoCo",
    "window.launcher.pill_named": "{label} ({name})",
    "window.dialog.label": "CoCo",
    "window.header.title": "CoCo",
    "window.header.minimise": "Minimise CoCo",
    "window.header.rail": "Restore",
    "window.header.dock_left": "Attach to the left",
    "window.header.dock_right": "Attach to the right",
    "window.header.full": "Full page",
    "window.header.float": "Floating window",
    "window.header.menu": "CoCo menu",
    "window.thread.label": "Conversation",
    "window.offline": "No answer from the application yet. Trying again.",
    "window.field.label": "Ask CoCo",
    "window.field.placeholder": "Ask CoCo",
    "window.field.ahead_working": "Type ahead. It is sent when CoCo is done",
    "window.field.ahead_waiting": "Type ahead. It is sent after your answer",
    "window.field.held": "Wait for CoCo to finish, then send",
    "window.field.send": "Send",
    "window.field.stop": "Stop",
    # ---- words used in several places
    "window.common.try_again": "Try again",
    "window.common.show_details": "Show details",
    "window.common.copied": "Copied",
    "window.common.optional": "(optional)",
    "window.common.back": "Back",
    "window.common.close": "Close",
    "window.time.seconds": "{s} s",
    "window.time.minutes": "{m} min {s} s",
    # ---- the thread
    "window.thread.you": "You: ",
    "window.thread.coco": "CoCo: ",
    "window.thread.steps": "{n} steps",
    "window.thread.copy_answer": "Copy answer",
    "window.thread.copy_draft": "Copy draft",
    "window.thread.draft_to": "to ",
    "window.thread.working": "CoCo is working",
    "window.queue.queued": "Queued",
    "window.queue.take_back": "Take back",
    "window.queue.take_back_for": "Take back: {text}",
    # ---- a step
    "window.step.running": "running",
    "window.step.completed": "completed",
    "window.step.failed": "failed",
    "window.step.not_run": "not run",
    "window.step.so_far": "{time} so far",
    "window.step.result": "Result",
    "window.step.allowed_by_you": "Allowed by you",
    # ---- a request for agreement
    "window.request.show_change": "Show change",
    "window.request.show_command": "Show command",
    "window.request.group": "CoCo needs your agreement: {question}",
    "window.request.where": "Where",
    "window.request.reads": "Reads",
    "window.request.changes": "Changes",
    "window.request.how_much": "How much",
    "window.request.allow": "Allow",
    "window.request.decline": "Decline",
    "window.wait.first_of": "First of {count} waiting for you. Next: {next}.",
    "window.wait.word_request": "a request",
    "window.wait.word_question": "a question",
    "window.wait.word_plan": "a plan",
    "window.wait.word_other": "something else",
    "window.announce.asks": "CoCo asks: {question} {where}",
    "window.announce.waiting": "CoCo is waiting for your answer",
    # ---- the first screen and the footer
    "window.first.title": "What can CoCo do for you?",
    "window.first.sub": (
        "It reads your project files. It asks before it runs a command or changes a file."
    ),
    "window.first.not_installed": "CoCo is not set up on this computer",
    "window.first.not_installed_sub": "Ask whoever installs this application for you to enable it.",
    "window.first.connecting": "Connecting to {profile}",
    "window.first.your_account": "your Snowflake account",
    "window.first.lost": "The connection was lost",
    "window.first.could_not_connect": "Could not connect",
    "window.first.could_not_connect_to": "Could not connect to {profile}",
    "window.first.choose_or_retry": "Choose another profile or try again.",
    "window.first.retry": "Try again.",
    "window.first.no_connection": "No Snowflake connection is set up on this computer",
    "window.first.where": "Where do connections live?",
    "window.first.where_answer": (
        "Snowflake keeps them in connections.toml, in the .snowflake folder of your user folder."
    ),
    "window.first.choose": "Choose an account",
    "window.first.connect": "Connect CoCo",
    "window.first.works_with": "CoCo works with your Snowflake account.",
    "window.footer.missing": "What is missing and how to fix it",
    "window.footer.package_missing": (
        "The assistant's package is not installed. This command installs it:"
    ),
    "window.footer.profile": "Snowflake profile",
    "window.footer.connect": "Connect",
    "window.footer.connect_to": "Connect {profile}",
    "window.footer.reconnect": "Reconnect",
    # ---- the menu and its confirmation
    "window.menu.new": "New conversation",
    "window.menu.disconnect": "Disconnect",
    "window.confirm.stops": "It stops what it is doing now.",
    "window.confirm.request": "The request waiting for you is cancelled.",
    "window.confirm.queued_one": "{n} queued message is discarded.",
    "window.confirm.queued_other": "{n} queued messages are discarded.",
    "window.confirm.changed": "What it already changed in your files stays.",
    "window.confirm.your_account": "your account",
    "window.confirm.disconnect_title": "Disconnect from {profile}?",
    "window.confirm.new_title": "Start a new conversation?",
    "window.confirm.forgets_disconnect": (
        "CoCo forgets this conversation, and you will have to connect again."
    ),
    "window.confirm.forgets_new": "CoCo forgets this conversation.",
    "window.confirm.disconnect_do": "Disconnect",
    "window.confirm.disconnect_keep": "Stay connected",
    "window.confirm.new_do": "Start new conversation",
    "window.confirm.new_keep": "Keep this one",
    # ---- questions
    "window.question.other": "Something else",
    "window.question.your_answer": "Your answer",
    "window.question.send": "Send answer",
    "window.question.send_all": "Send answers",
    "window.question.next": "Next",
    "window.question.skip": "Skip",
    "window.question.skip_all": "Skip all",
    "window.question.group_app": "The application asks you a question",
    "window.question.group_coco": "CoCo asks you a question",
    "window.question.n_of": "Question {i} of {n}",
    "window.question.asks_app": "The application asks: {text}",
    "window.question.asks_coco": "CoCo asks: {text}",
    # ---- plans
    "window.plan.approve_note": (
        "If you approve, CoCo starts. It still asks before each command or change."
    ),
    "window.plan.region": "The plan",
    "window.plan.group": "CoCo proposes a plan",
    "window.plan.title": "Go ahead with this plan?",
    "window.plan.reason": "What should CoCo change?",
    "window.plan.approve": "Approve plan",
    "window.plan.decline": "Decline",
    "window.plan.decline_do": "Decline plan",
    "window.plan.announce": "CoCo proposes a plan. Go ahead with this plan?",
    "window.plan.mode": "Planning only. Nothing is changed yet.",
    "window.plan.carry_out": "Carry out the plan",
    # ---- standing permissions
    "window.standing.covers": "Covers",
    "window.standing.until": "Until",
    "window.standing.allow": "Allow and stop asking",
    "window.standing.not_asked": "Not asked: you allowed it for this conversation",
    "window.standing.menu": "Without asking",
    "window.standing.menu_one": "1 thing CoCo no longer asks for",
    "window.standing.menu_other": "{n} things CoCo no longer asks for",
    "window.standing.panel_title": "CoCo no longer asks before it:",
    "window.standing.ask_again": "Ask again",
    "window.standing.ask_again_for": "Ask again: {text}",
    "window.standing.ends_one": "It ends with this conversation.",
    "window.standing.ends_many": "Both end with this conversation.",
    "window.standing.confirm": "What it let you do without asking ends with this conversation.",
    # ---- data
    "window.data.table": "Table",
    "window.data.rows_one": "{n} row",
    "window.data.rows_other": "{n} rows",
    "window.data.of": "{shown} of {total}",
    "window.data.first_of": "The first {shown} of {total}",
    "window.data.larger": "Open larger",
    "window.data.back": "Conversation",
    "window.data.copy_table": "Copy table",
    "window.data.csv": "Download CSV",
    "window.data.csv_done": "CSV downloaded",
    "window.data.file": "table",
    "window.data.show_json": "Show as JSON",
    "window.data.hide_json": "Hide JSON",
    "window.data.sql": "SQL",
    "window.data.code": "Code",
    "window.data.copy_code": "Copy code",
    # ---- files
    "window.files.attach": "Attach files",
    "window.files.drop": "Drop the files here to attach them",
    "window.files.mb": "{n} MB",
    "window.files.kb": "{n} KB",
    "window.files.too_big": "Not attached: {size}, the limit is {max} MB",
    "window.files.type": "Not attached: this type of file is not accepted",
    "window.files.dup": "Not attached: already attached",
    "window.files.replaces": "Replaces the earlier file",
    "window.files.dismiss": "Dismiss {name}",
    "window.files.remove": "Remove {name}",
    "window.files.sending_one": "Sending {n} file",
    "window.files.sending_other": "Sending {n} files",
    # ---- a request of the page
    "window.page.show_full": "Show full request",
    "window.page.hide_full": "Hide full request",
    # ---- session
    "window.session.details": "Session details",
    "window.session.copy": "Copy details",
    "window.session.earlier_one": "Show {n} earlier message",
    "window.session.earlier_other": "Show {n} earlier messages",
    "window.session.show_all": "Show all",
    "window.session.show_less": "Show less",
    "window.session.request": "Request",
    "window.session.considered": "What CoCo considered",
    "window.session.show_message": "Show the message",
    "window.session.hide_message": "Hide the message",
    # ---- the conversation's sentences (Python side), read there as t('<name>')
    # notes of a step, a question, a plan
    "agent.note_allowed": "Allowed by you",
    "agent.note_declined": "Declined",
    "agent.note_not_allowed": "Not allowed",
    "agent.note_expired": "Expired",
    "agent.note_cancelled": "Cancelled",
    "agent.note_skipped": "Skipped",
    "agent.note_stopped": "Stopped",
    "agent.note_interrupted": "Interrupted",
    "agent.reason_expired": "Not answered within ten minutes. Nothing was done.",
    "agent.reason_cli_refused": "Cortex Code refused this tool for the session.",
    # the thread's own lines
    "agent.scope_about": "About {name}",
    "agent.scope_none": "About the whole working folder",
    "agent.folder_changed": "The working folder changed, so this conversation ended.",
    "agent.lost_text": "The connection to CoCo was lost. Reconnect to go on.",
    "agent.failed_text": "CoCo could not finish this request.",
    "agent.plan_approved": "The plan you approved",
    "agent.plan_proposed": "The plan CoCo proposed",
    "agent.carry_out_prompt": "Carry out the plan you described.",
    "agent.granted_line": "CoCo no longer asks before it {what}.",
    "agent.granted_ask_again": "Ask again",
    "agent.revoked_line": "CoCo asks again before it {what}.",
    # pills
    "agent.pill_answer": "Answer ready",
    "agent.pill_lost": "Connection lost",
    "agent.pill_failed": "Could not finish",
    "agent.pill_read": "Allow a command?",
    "agent.pill_change": "Allow a file change?",
    "agent.pill_question": "A question for you",
    "agent.pill_plan": "A plan to approve",
    # menu switches
    "agent.opt_plan": "Plan first",
    "agent.opt_plan_sub": "CoCo proposes before it acts",
    "agent.opt_latest": "Latest exchange only",
    "agent.opt_latest_sub": "Earlier messages one click away",
    "agent.opt_shorten": "Shorten long messages",
    "agent.opt_shorten_sub": "",
    "agent.opt_raw": "Raw technical details",
    "agent.opt_raw_sub": "",
    # data
    "agent.rows_none": "No rows",
    "agent.rows_one": "{n} row",
    "agent.rows": "{n} rows",
    # attached files
    "agent.attach_prompt": "I attached files.",
    "agent.attach_intro": "Files saved for you (read them with your tools):",
    "agent.attach_refused": "Not attached: {files}.",
    "agent.attach_type": "this type is not accepted",
    "agent.attach_wait": "wait until CoCo is connected",
    "agent.attach_size": "{mb} MB, the limit is {max} MB",
    "agent.attach_unreadable": "the file could not be read",
    "agent.attach_duplicate": "already attached",
    "agent.attach_sandbox_none": "this agent has no place for files (the host gives it a stage)",
    "agent.attach_sandbox_started": "files go in before the first message: start a new one",
    "agent.attach_sandbox_failed": "the upload to Snowflake failed: {why}",
    # connection
    "agent.problem_signin": "Snowflake refused the sign-in. Try again, or choose another account.",
    "agent.problem_network": "CoCo could not reach Snowflake. Check your network, then try again.",
    "agent.problem_other": "CoCo could not connect. Try again, or choose another account.",
    "agent.queue_note": "Sent when you connect",
    # the command shown when the SDK is missing: empty, the agent's own; a host that installs it
    # another way (the Cockpit: `make cockpit`) says so here
    "agent.setup_package": "",
}


def table(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """DEFAULT with a host's overrides on top (an unknown key is kept: a host's own sentence)."""
    return {**DEFAULT, **{str(key): str(text) for key, text in (overrides or {}).items()}}
