# Ask CoCo: live run checklist

Needs the Cortex Code program and a Snowflake connection; costs credits. **Nothing below was run live for 0.2.0**:
the window, the conversation, the gate and the policy are verified on the scripted agent
(`STREAMLIT_COCO_AGENT=mock`). Run in a scratch folder, never in a customer repository.

Program version read when the adapter was written: Cortex Code 1.1.104, SDK 1.0.7. Note the versions you run.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | `make chat`, open the launcher, Connect | "Connecting", then the first screen; no tool list error | |
| 2 | Ask "List the files here" | Steps appear without a request (reads inside the folder are free); the answer streams once, not twice | |
| 3 | Ask for a file outside the folder | A request that says it is outside, with the exact path; Decline: the step says "Declined" | |
| 4 | Ask to create a file | A change request; "Show change" holds the full content; Allow: the file exists, the page reruns once | |
| 5 | Ask to run a shell command (policy without commands) | A change request with the whole input; after Allow it runs; the step is not "completed" if the program refuses it itself | |
| 6 | `make approval` (policy with `git_readonly`, a command, `sql=True`): "what changed?" | A read request under the command's plain name; the exact line behind "Show command" | |
| 7 | Same app: ask a SELECT, then a CREATE TABLE in a scratch schema | First shown as a query, second as a statement that cannot be undone; the program accepts `sql_execute` after Allow | |
| 8 | Same app with `standing=True`: tick "stop asking" on a query | The next query runs with "Not asked"; the menu lists it; "Ask again" takes it back | |
| 9 | Ask something that makes CoCo ask a question | The question block; Send answer; CoCo goes on with the answer | |
| 10 | Switch "Plan first" on, ask for a change | The planning strip; a plan to approve; after Approve each change still asks | |
| 11 | Ask for a long file (over the program's output limit) | CoCo reads it back from the session's long-output folder without a request | |
| 12 | Stop during a run; close the browser tab during a run | "Stopped"; the Cortex program's process ends in both cases | |
| 13 | `make structured` | The answer is a data block; the page receives the result | |
| 14 | `make cwd-upload`: attach a file, ask about it | The file is saved in the working folder and read | |
| 15 | With `options.mcp_servers` set | Each MCP call asks, as a change | |
| 16 | Disconnect the network during a run | "Connection lost", Reconnect; what was typed is kept | |
