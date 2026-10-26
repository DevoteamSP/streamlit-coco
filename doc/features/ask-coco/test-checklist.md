# Ask CoCo: live run checklist

Rows 1 to 20 need the Cortex Code program and a Snowflake connection; rows 21 to 33 need a Snowflake account with the Cortex Agent API (the managed agent). They cost credits. Run in a scratch folder, never in a customer repository. Run the examples **without** `STREAMLIT_COCO_AGENT=mock`: with it the agent is scripted. Each example below is a `make` target of this repository's Makefile.

Program version read when the adapter was written: Cortex Code 1.1.104. **Run for 0.3.0 (2026-10-26):** Cortex Code 1.2.18, `snowflake-cortex-agent-sdk` 0.0.3, a Snowflake test account. The Result column says what was run and how; a row left blank was **not** run for 0.3.0 (0.2.0 and 0.2.2 were not run live either; they were verified on the scripted agent). "Conversation" below means the window's own `Conversation` driven by a script on the real agent: everything the window shows, but no browser; "browser" means the scripted harness in Playwright.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | `make chat`, press **Ask CoCo** (bottom right), pick the profile, **Connect** | "Connecting", then the first screen; no tool list error | Not run (script run instead: connect, ready) |
| 2 | Ask "List the files here" | Steps appear without a request (reads inside the folder are free); the answer streams once, not twice | Conversation, CLI 1.2.18: listing the folder ran with no request, one answer |
| 3 | Ask for a file outside the folder | A request that says it is outside, with the exact path; Decline: the step says "Declined" | Conversation, CLI: the request said "outside the working folder" with the exact path; Decline: step "Declined", the agent said it was declined |
| 4 | Ask to create a file | A change request; "Show change" holds the full content; Allow: the file exists, the page reruns once | Conversation, CLI: "create a file" asked as a change; Allow: the file exists |
| 5 | `make chat` (Bash is among the tools that ask): ask to run a shell command | A change request with the whole input; after Allow it runs; the step is not "completed" if the program refuses it itself | Conversation, CLI: `echo live-check` asked as a change ("on this computer"); after Allow its output came back |
| 6 | `make approval` (a listed command, `git_readonly`, `changes="*.md"`, `sql=True`, `standing=True`): "what changed?" | A read request under the command's plain name ("Look at what has changed"); the exact line behind **Show command**; any other command asks as a change | |
| 7 | Same app: ask a SELECT, then a CREATE TABLE in a scratch schema | First shown as a query, second as a statement that cannot be undone; the program accepts `sql_execute` after Allow | |
| 8 | Same app (it has `standing=True`): tick "Do not ask again for queries that only read" on a query, then press **Allow and stop asking** | The next query runs and its step says "Not asked: you allowed it for this conversation"; the menu (**Without asking**) lists it; **Ask again** takes it back | |
| 9 | Ask something that makes CoCo ask a question | The question block; Send answer; CoCo goes on with the answer | |
| 10 | Switch "Plan first" on, ask for a change | The planning strip; a plan to approve; after Approve each change still asks | |
| 11 | Ask for a long file (over the program's output limit) | CoCo reads it back from the session's long-output folder without a request | |
| 12 | Stop during a run; close the browser tab during a run | "Stopped"; the Cortex program's process ends in both cases | |
| 13 | `make structured`, press **Ask for the package facts** | The answer is a data block; the page shows the package name, version and number of dependencies from `coco.result` | |
| 14 | `make cwd-upload`: attach a file in the field, ask about it | The file is saved in `cwd_upload_workspace/_coco_uploads/<id>/` and read without a request; the sidebar uploader writes to `cwd_upload_workspace/_uploads/` | |
| 15 | With `options.mcp_servers` set | Each MCP call asks, as a change | |
| 16 | Disconnect the network during a run | "Connection lost", Reconnect; what was typed is kept | |
| 17 | `make modern-chat`, **Ask CoCo**, sidebar **Split**: open the window, connect, press the attach-right icon in the title bar | The window takes the full height at the right; the page (sidebar included) shrinks to the rest of the screen; the sidebar says `right`; the cards stack | |
| 18 | Same page: attach left, then **Full page**, then press the pressed icon, then Minimize | Left: the page moves right. Full page: the window covers the page, the conversation keeps a readable width. The pressed icon returns to floating. Minimize: the page gets its screen back (`closed`) | |
| 19 | Same page, a real run: ask something that makes CoCo ask a question while docked, and leave it waiting 30 s | The window does not blink and nothing of the page draws over it; Streamlit's header and menu bar are under the title bar | |
| 20 | `make app-builder`: on each screen open the window | The suggested questions follow the screen; Build this app (Brief) is sent to the window and asks before it writes; Fix with CoCo in the preview is sent to the window | |

### The managed agent (0.3.0, experimental)

Run `make managed` (profile + role, then the window) for rows 21 to 26 and 29 in a browser, or the script of the same steps (on 2026-10-26 rows 21 to 24 were also done by hand in a browser on a real account: the new first screen, the request with "Where: The Snowflake sandbox", **Show command**, Allow, the answer; no console error); use the least role that works (`PUBLIC` was enough on a Snowflake test account).

| # | Do | Expect | Result |
|---|---|---|---|
| 21 | `make managed`, open **Ask CoCo**, connect with a profile and a role | The first screen says it works in a Snowflake sandbox, not on this computer; no "project files"; session details name the account, the agent and the thread, no secret | Conversation: connected with the session token of a profile, role `PUBLIC`; the first-screen words are the agent's (`ManagedAgent.labels`). Browser (scripted stream): first screen and its screenshot, `tests/e2e/test_managed_window.py` |
| 22 | Ask "What is 17 times 23? Answer with the number only." | An answer, no request | Conversation: `391`, no request |
| 23 | Ask it to create `/tmp/coco_probe.txt` with a shell command; **Decline** | A request that says "in the Snowflake sandbox", **Where: The Snowflake sandbox**, the exact command behind **Show command**; the step says "Declined" and the agent says it was not run | Conversation: the command `echo probe > /tmp/coco_probe.txt && cat ...` asked, where "The Snowflake sandbox"; declined; the agent said so. Browser (scripted): same card, no local folder name |
| 24 | The same, **Allow** | The command runs; the step says "Allowed by you"; the agent says done | Conversation: allowed, done. The service sent the one-call option only (unit-tested: never "Allow all bash for this session") |
| 25 | With `FolderPolicy(standing=True)`: Allow and tick "Do not ask again for commands", then ask for a second write | The second write runs without a request; the thread says what is no longer asked | Conversation: the second write had **0 requests**; the audit log shows `standing`. (Found: the line ended with two full stops: fixed.) |
| 26 | Attach a CSV **before** the first message (`ManagedOptions(upload_stage=...)`, role that writes the stage), ask for a sum of a column | The file is on the stage in this conversation's folder, the agent reads it at `/uploads/<id>/...`, **no copy** in the working folder; the agent is told the sandbox path | Conversation on a scratch stage: the sum was right (7), the file was on the stage under one folder, nothing in `_coco_uploads/`. Browser (scripted): the path reaches the agent, the local folder does not |
| 27 | Attach another file **after** the first message | Refused: "files go in before the first message: start a new one" | Conversation: refused with that sentence, the file was not uploaded |
| 28 | New conversation or Disconnect after row 26 | The upload folder is gone from the stage | Conversation: `LIST` of the folder after the close was empty |
| 29 | Stop while a request waits | "Stopped"; the run ends; the next message works; no warning in the server log | Conversation: stopped, the next question was answered. Found: cancelling a run the service had already ended raised a `ConflictError` warning (now a debug line) |
| 30 | `AuditLog` on rows 23 to 25, and on a Cortex Code run (rows 3 to 5) | One line per decision: declined, allowed, allowed with `standing_granted`, `standing`; the exact command; the agent's class name | Conversation: managed: `declined`, `allowed`, `allowed` + `standing_granted: commands`, `standing` x2; CLI: `declined` (Read), `allowed` (Write), `allowed` (Bash) |
| 31 | `check_environment(managed=True)` with no `cortex` on the `PATH` | `ready` is true; the default probe says not ready | Run: `ready: True, cli_path: None` and, by default, `ready: False` |
| 32 | `make skills-hub` on a stage: **Chat with this skill** | The skill loads; a script of the skill asks before it runs | Run on 2026-10-26 (P1): three skills, `csv-profile` stopped at an approval card and ran after Allow |
| 33 | The Native App (`examples/skills_hub_native/DEPLOY.md`), open the ingress URL logged in | The shop lists the skills, a chat answers as the application | Service and probe run (a skill answered through the Agent API from inside the service); **the page behind the ingress was not opened** (needs a login) |

Not run: rows 6 to 20 (not repeated for 0.3.0: no change to what they test, except the gate's new audit hook, covered by rows 30 and the unit tests), a conversation of many hours (token renewal), sandbox SQL under caller's rights, two skills in one conversation.
