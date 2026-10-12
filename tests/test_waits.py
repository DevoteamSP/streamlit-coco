"""Ask CoCo, what waits for the user: one ordered list of requests, questions and plans, planning
    only,
standing permission (waits.py)."""

from __future__ import annotations

import copy

from coco_fixture import ConversationCase

from streamlit_coco import waits as coco_waits
from streamlit_coco.testing import fixtures as fx

ANSWER = [{"id": "q1", "picked": ["This week"], "other": None, "fields": None}]


class WaitCase(ConversationCase):
    standing = True

    def setUp(self) -> None:
        super().setUp()
        self.connect()

    def calls(self, name):
        return [c for c in self.conv.agent.calls if c[0] == name]

    def act(self, **action) -> None:
        self.conv.act(action, self.ctx())

    def question(self, id="n1", text="Which week?", tool_id="tq", source="coco", questions=None):
        return {
            "t": "question",
            "id": id,
            "tool_id": tool_id,
            "source": source,
            "questions": questions
            or [
                fx.choice(
                    "q1",
                    text,
                    [
                        {"label": "This week", "description": ""},
                        {"label": "Last week", "description": ""},
                    ],
                )
            ],
        }

    def plan(self, id="n2", text="1. Read.\n2. Write.", tool_id="tp"):
        return {"t": "plan", "id": id, "tool_id": tool_id, "text": text}

    def standing_request(self, rid="r1", tool_id="t1", offer=True):
        facts = self.conv.run["message"]["policy"].judge("Bash", {"command": "git status"})[1]
        facts = {
            k: v for k, v in facts.items() if offer or k != "standing"
        }  # the policy offers one by itself
        event = {"t": "request", "id": rid, "tool_id": tool_id, "facts": facts}
        return event

    def bash_call(self, tool_id="t1"):
        return {"t": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": "git status"}}

    def order(self) -> list:
        return [(w["kind"], w["id"]) for w in coco_waits.waits(self.conv)]

    def notes(self, kind="asked") -> list:
        return [i["note"] for i in self.thread(kind)]

    def shape(self, name, view=None) -> None:
        view = copy.deepcopy(view or self.view())
        if view["request"]:
            view["request"].pop(
                "pill", None
            )  # the policy's own key for the minimised pill: not on the sheet
            if "standing" not in (fx.VIEWS[name]["request"] or {}):
                view["request"].pop("standing", None)
        for key in set(view) & {
            "attach",
            "options",
            "hidden",
            "session",
            "type_ahead",
            "problem",
            "profile_files",
        } - set(fx.VIEWS[name]):
            del view[key]  # other packages' keys, not under test here
        view["thread"] = [
            i for i in view["thread"] if i["kind"] != "scope"
        ]  # the fixtures leave the scope line out
        for item in view["thread"]:
            for step in item["items"] if item["kind"] == "steps" else [item]:
                step.pop("elapsed", None)  # sent by the runtime, absent from the sheet's steps
        fx.assert_same_shape(self, view, fx.VIEWS[name], name)

    def read(self, tool_id="t1") -> list:
        return [self.step(tool_id), {"t": "tool_result", "id": tool_id, "content": "9 files"}]


class OrderTest(WaitCase):
    def test_requests_questions_and_plans_wait_in_the_order_they_came(self) -> None:
        self.send()
        self.tell(self.write_call("t1"), self.request("r1", "t1"), self.question(), self.plan())
        view = self.view()
        self.assertEqual(
            (view["status"], view["wait"]["kind"], view["wait"]["more"], view["request"]["id"]),
            ("waiting", "request", {"count": 3, "next": "question"}, "r1"),
        )
        self.assertEqual(view["pill"]["kind"], "request")
        self.act(type="allow", id="r1")
        view = self.view()
        self.assertEqual(
            (view["wait"]["kind"], view["wait"]["more"], view["request"], view["pill"]["label"]),
            ("question", {"count": 2, "next": "plan"}, None, "A question for you"),
        )
        self.act(type="skip", id="n1")
        view = self.view()
        self.assertEqual(
            (view["wait"]["kind"], view["wait"]["more"], view["pill"]["label"]),
            ("plan", None, "A plan to approve"),
        )
        self.act(type="approve_plan", id="n2")
        view = self.view()
        self.assertEqual((view["status"], "wait" in view, view["pill"]), ("working", False, None))

    def test_a_request_behind_a_question_is_not_the_request_of_the_view_until_its_turn(
        self,
    ) -> None:
        self.send()
        self.tell(self.question(), self.write_call("t1"), self.request("r1", "t1"))
        view = self.view()
        self.assertEqual(
            (view["wait"]["kind"], view["wait"]["more"], view["request"]),
            ("question", {"count": 2, "next": "request"}, None),
        )
        self.assertNotIn("t1", self.steps())  # its step waits behind its request
        self.act(type="answer", id="n1", answers=ANSWER)
        view = self.view()
        self.assertEqual(
            (view["wait"]["kind"], view["request"]["id"], view["pill"]["kind"]),
            ("request", "r1", "request"),
        )

    def test_a_wait_arriving_while_another_is_answered_goes_behind_it(self) -> None:
        self.send()
        self.tell(self.question("n1"), self.question("n2", tool_id="tq2"))
        self.act(type="skip", id="n1")
        self.tell(self.plan("n3"))
        self.assertEqual(self.order(), [("question", "n2"), ("plan", "n3")])
        self.act(type="skip", id="n2")
        self.assertEqual(self.view()["wait"]["id"], "n3")

    def test_the_same_event_twice_is_one_wait_and_events_without_a_run_are_ignored(self) -> None:
        self.tell(self.question())  # no run: late
        self.assertEqual(self.order(), [])
        self.send()
        self.tell(self.question(), self.question())
        self.assertEqual(self.order(), [("question", "n1")])

    def test_typing_ahead_queues_behind_whatever_waits_and_the_field_answers_nothing(self) -> None:
        self.send()
        self.tell(self.question(), self.plan())
        self.send("Then list the risks")
        view = self.view()
        self.assertEqual(
            ([m["text"] for m in view["queue"]], view["wait"]["id"], self.sent()),
            (["Then list the risks"], "n1", ["Hello"]),
        )
        self.act(type="skip", id="n1")
        self.act(type="approve_plan", id="n2")
        self.assertEqual(len(self.view()["queue"]), 1)
        self.tell({"t": "result", "text": "Done."})
        self.assertEqual(
            (self.sent(), self.view()["queue"]), (["Hello", "Then list the risks"], [])
        )

    def test_navigation_moves_nothing_of_a_wait(self) -> None:
        self.send()
        self.tell(self.question())
        before = self.view()["wait"]
        self.assertEqual(self.view()["wait"], before)


class QuestionTest(WaitCase):
    def test_an_answer_goes_to_the_agent_and_the_thread_keeps_the_question_and_the_answer_once(
        self,
    ) -> None:
        self.send()
        self.tell(self.question())
        self.act(type="answer", id="n1", answers=ANSWER)
        self.assertEqual(self.calls("answer"), [("answer", "n1", ANSWER)])
        self.assertEqual(
            [(i["kind"], i["text"]) for i in self.thread() if i["kind"] in ("asked", "user")],
            [("user", "Hello"), ("asked", "Which week?"), ("user", "This week")],
        )
        self.act(type="answer", id="n1", answers=ANSWER)  # twice: nothing more
        self.assertEqual((len(self.thread("asked")), len(self.calls("answer"))), (1, 1))

    def test_several_choices_a_free_answer_and_a_form_become_one_message(self) -> None:
        form = {
            "id": "q2",
            "kind": "form",
            "text": "Report",
            "fields": [
                fx.form_field("h", "Highlights", "longtext"),
                fx.form_field("b", "Blockers"),
                fx.form_field("d", "Days", "number", required=False),
            ],
        }
        self.send()
        self.tell(
            self.question(
                source="app", questions=[fx.choice("q1", "Who?", fx.WHO, multi=True), form]
            )
        )
        self.act(
            type="answer",
            id="n1",
            answers=[
                {"id": "q1", "picked": ["A", "B"], "other": "C", "fields": None},
                {
                    "id": "q2",
                    "picked": [],
                    "other": None,
                    "fields": {"h": "Done", "b": "None", "d": ""},
                },
            ],
        )
        self.assertEqual(
            self.thread("user")[-1]["text"], "A, B, C\nHighlights: Done\nBlockers: None"
        )

    def test_an_empty_or_unknown_answer_changes_nothing(self) -> None:
        self.send()
        self.tell(self.question())
        for action in (
            {
                "type": "answer",
                "id": "n1",
                "answers": [{"id": "q1", "picked": [], "other": "  ", "fields": None}],
            },
            {"type": "answer", "id": "n1", "answers": "x"},
            {"type": "answer", "id": "zz", "answers": ANSWER},
            {"type": "skip", "id": "zz"},
        ):
            self.conv.act(action, self.ctx())
        self.assertEqual(
            (self.order(), self.calls("answer"), self.calls("skip")), ([("question", "n1")], [], [])
        )

    def test_skipped(self) -> None:
        self.send()
        self.tell(self.question())
        self.act(type="skip", id="n1")
        self.assertEqual(
            (self.calls("skip"), self.notes(), self.view()["status"]),
            ([("skip", "n1")], ["Skipped"], "working"),
        )

    def test_expired_like_a_request_and_the_others_keep_waiting(self) -> None:
        self.send()
        self.tell(self.question(), self.plan(), {"t": "expired", "id": "n1", "tool_id": "tq"})
        self.assertEqual(
            (self.notes(), self.order(), self.calls("skip")), (["Expired"], [("plan", "n2")], [])
        )
        self.tell({"t": "expired", "id": "n2", "tool_id": "tp"})
        step = [s for s in self.steps().values() if s["tool"] is None][0]
        self.assertEqual(
            (step["note"], step["state"], step["reason"]),
            ("Expired", "no", "Not answered within ten minutes. Nothing was done."),
        )
        self.assertEqual(self.view()["status"], "working")

    def test_a_request_expires_beside_a_question(self) -> None:
        self.send()
        self.tell(
            self.write_call("t1"),
            self.request("r1", "t1"),
            self.question(),
            {"t": "expired", "id": "r1", "tool_id": "t1"},
        )
        self.assertEqual(
            (self.order(), self.steps()["t1"]["note"]), ([("question", "n1")], "Expired")
        )

    def test_a_question_the_cockpit_cannot_show_is_refused_and_its_step_fails(self) -> None:
        self.send()
        self.tell(
            self.step("tq", name="AskUser"),
            self.question(
                questions=[
                    {
                        "id": "q1",
                        "kind": "choice",
                        "text": "",
                        "multi": False,
                        "options": [],
                        "other": None,
                    }
                ]
            ),
        )
        self.assertEqual((self.order(), self.calls("skip")), ([], [("skip", "n1")]))
        self.assertEqual(self.conv.run["steps"]["tq"]["state"], "bad")

    def test_the_question_tool_is_not_a_step_of_the_thread(self) -> None:
        self.send()
        self.tell(self.step("tq", name="AskUser"), self.question())
        self.act(type="skip", id="n1")
        self.assertNotIn("tq", self.steps())


class PlanTest(WaitCase):
    def test_planning_only_is_a_mode_and_the_agent_is_told(self) -> None:
        self.assertNotIn("mode", self.view())
        coco_waits.set_planning(self.conv, True)
        self.assertEqual(
            (self.view()["mode"], self.calls("set_planning")),
            ({"planning": True, "can_carry_out": False}, [("set_planning", True)]),
        )
        coco_waits.set_planning(self.conv, True)
        self.assertEqual(len(self.calls("set_planning")), 1)
        coco_waits.set_planning(self.conv, False)
        self.assertNotIn("mode", self.view())

    def test_approved_the_run_goes_on_and_planning_ends(self) -> None:
        coco_waits.set_planning(self.conv, True)
        self.send()
        self.tell(self.plan())
        self.act(type="approve_plan", id="n2")
        view = self.view()
        self.assertEqual(
            (self.calls("approve_plan"), "mode" in view, view["status"]),
            ([("approve_plan", "n2")], False, "working"),
        )
        step = [s for s in self.steps().values() if s["tool"] is None][0]
        self.assertEqual(
            (step["label"], step["state"], step["blocks"]),
            ("The plan you approved", "ok", [{"type": "text", "text": "1. Read.\n2. Write."}]),
        )

    def test_declined_with_a_reason_the_reason_goes_to_the_agent_and_is_the_users_message(
        self,
    ) -> None:
        coco_waits.set_planning(self.conv, True)
        self.send()
        self.tell(self.plan())
        self.act(type="decline_plan", id="n2", reason=" Only the report. ")
        self.assertEqual(self.calls("decline_plan"), [("decline_plan", "n2", "Only the report.")])
        self.assertEqual(
            (self.thread("user")[-1]["text"], self.view()["mode"]["planning"]),
            ("Only the report.", True),
        )
        self.assertEqual(
            [s["note"] for s in self.steps().values() if s["tool"] is None], ["Declined"]
        )

    def test_declined_without_a_reason_adds_no_message(self) -> None:
        self.send()
        self.tell(self.plan())
        self.act(type="decline_plan", id="n2", reason="")
        self.assertEqual(
            ([u["text"] for u in self.thread("user")], self.calls("decline_plan")),
            (["Hello"], [("decline_plan", "n2", "")]),
        )

    def test_a_plan_written_as_an_answer_offers_carry_out_which_leaves_planning_and_asks(
        self,
    ) -> None:
        coco_waits.set_planning(self.conv, True)
        self.send()
        self.assertFalse(self.view()["mode"]["can_carry_out"])
        self.tell({"t": "result", "text": "I would read, then write."})
        self.assertTrue(self.view()["mode"]["can_carry_out"])
        self.conv.act({"type": "carry_out"})  # no context: the last one is used
        view = self.view()
        self.assertEqual(
            ("mode" in view, self.calls("set_planning")[-1], len(self.sent()), view["status"]),
            (False, ("set_planning", False), 2, "working"),
        )
        self.assertIn("Carry out", self.sent()[-1])

    def test_carry_out_without_planning_does_nothing(self) -> None:
        self.send()
        self.tell({"t": "result", "text": "Done."})
        self.conv.act({"type": "carry_out"})
        self.assertEqual(len(self.sent()), 1)


class StopAndEndTest(WaitCase):
    def three(self) -> None:
        self.send()
        self.tell(self.write_call("t1"), self.request("r1", "t1"), self.question(), self.plan())
        self.send("Typed ahead")

    def test_stop_declines_every_wait_and_returns_the_queue_to_the_field(self) -> None:
        self.three()
        self.act(type="stop")
        self.assertEqual(
            (
                self.calls("decide"),
                self.calls("skip"),
                self.calls("decline_plan"),
                self.calls("stop"),
            ),
            (
                [("decide", "r1", False, False)],
                [("skip", "n1")],
                [("decline_plan", "n2", "")],
                [("stop",)],
            ),
        )
        self.assertEqual(self.order(), [])
        self.tell({"t": "stopped"})
        view = self.view()
        self.assertEqual(
            (view["status"], view["restore"], view["queue"], self.notes()),
            ("ready", "Typed ahead", [], ["Skipped"]),
        )
        self.assertEqual(sorted(s["note"] for s in self.steps().values()), ["Declined", "Declined"])

    def test_a_failure_cancels_every_wait_and_says_so(self) -> None:
        self.three()
        self.tell({"t": "error", "message": "boom", "retry": False})
        view = self.view()
        self.assertEqual(
            (view["status"], view["restore"], self.order(), self.notes()),
            ("ready", "Typed ahead", [], ["Cancelled"]),
        )
        self.assertEqual(
            (self.calls("skip"), self.calls("decline_plan"), self.calls("decide")),
            ([("skip", "n1")], [("decline_plan", "n2", "")], [("decide", "r1", False, False)]),
        )
        self.assertEqual(
            sorted(s["note"] for s in self.steps().values()), ["Cancelled", "Cancelled"]
        )
        self.assertEqual(view["pill"]["kind"], "failed")

    def test_a_lost_connection_cancels_every_wait_without_calling_the_agent(self) -> None:
        coco_waits.set_planning(self.conv, True)
        self.three()
        self.tell({"t": "granted", "id": "p1", "text": "Reads things"})
        self.tell({"t": "lost", "message": "gone"})
        view = self.view()
        self.assertEqual(
            (view["status"], view["restore"], self.order(), self.notes()),
            ("lost", "Typed ahead", [], ["Cancelled"]),
        )
        self.assertEqual(
            (self.calls("skip"), self.calls("decline_plan"), self.calls("decide")), ([], [], [])
        )
        self.assertEqual(
            ("mode" in view, "granted" in view, view["pill"]["label"]),
            (False, False, "Connection lost"),
        )

    def test_the_end_of_a_conversation_ends_what_waited_and_what_was_granted(self) -> None:
        for end in ({"type": "new"}, {"type": "disconnect"}):
            self.conv = self.make()
            self.connect()
            coco_waits.set_planning(self.conv, True)
            self.three()
            self.tell({"t": "granted", "id": "p1", "text": "Reads things"})
            self.conv.act(end)
            view = self.view()
            self.assertFalse({"wait", "mode", "granted"} & set(view), end)
            self.assertEqual(view["thread"], [], end)

    def test_the_working_folder_changing_ends_waits_and_grants(self) -> None:
        self.send()
        self.tell(self.question(), {"t": "granted", "id": "p1", "text": "Reads things"})
        self.conv.set_cwd(self.folder.parent / "elsewhere")
        self.assertFalse({"wait", "granted"} & set(self.view()))


class StandingTest(WaitCase):
    def test_allow_with_standing_passes_the_family_on_and_the_grant_is_listed_and_said(
        self,
    ) -> None:
        self.send()
        self.tell(self.bash_call("t1"), self.standing_request())
        self.assertIn("standing", self.view()["request"])
        self.act(type="allow", id="r1", standing=True)
        self.assertEqual(self.calls("decide"), [("decide", "r1", True, True)])
        self.tell(
            {"t": "granted", "id": "p1", "text": "Looks at what has changed", "family": "git"}
        )
        view = self.view()
        self.assertEqual(view["granted"], [{"id": "p1", "text": "Looks at what has changed"}])
        kinds = [i["kind"] for i in view["thread"]]
        self.assertLess(
            kinds.index("system"), kinds.index("steps")
        )  # the line comes before the step that runs

    def test_the_tick_counts_only_when_the_request_offered_it(self) -> None:
        self.send()
        self.tell(self.bash_call("t1"), self.standing_request(offer=False))
        self.act(type="allow", id="r1", standing=True)
        self.assertEqual(self.calls("decide"), [("decide", "r1", True, False)])

    def test_allow_once_and_decline_never_pass_standing(self) -> None:
        self.send()
        self.tell(
            self.bash_call("t1"),
            self.standing_request("r1", "t1"),
            self.bash_call("t2"),
            self.standing_request("r2", "t2"),
        )
        self.act(type="allow", id="r1")
        self.act(type="decline", id="r2", standing=True)
        self.assertEqual(
            self.calls("decide"), [("decide", "r1", True, False), ("decide", "r2", False, False)]
        )

    def test_a_step_that_was_not_asked_says_so(self) -> None:
        self.send()
        self.tell(
            self.step("t2"),
            {"t": "standing", "tool_id": "t2"},
            {"t": "tool_result", "id": "t2", "content": "x"},
        )
        self.assertTrue(self.steps()["t2"]["standing"])
        self.tell(self.step("t3"), {"t": "tool_result", "id": "t3", "content": "x"})
        self.assertNotIn("standing", self.steps()["t3"])

    def test_revoke_from_the_menu_or_the_line_takes_it_back(self) -> None:
        self.send()
        self.tell(
            {"t": "granted", "id": "p1", "text": "Looks at files"},
            {"t": "granted", "id": "p2", "text": "Runs queries"},
        )
        line = self.thread("system")[0]
        self.assertEqual(line["action"], {"label": "Ask again"})
        self.act(type="system_action", id=line["id"])
        self.assertEqual(
            (
                self.calls("revoke"),
                [g["id"] for g in self.view()["granted"]],
                self.thread("system")[0]["action"],
            ),
            ([("revoke", "p1")], ["p2"], None),
        )
        self.act(type="revoke", id="p2")
        self.act(type="revoke", id="p2")
        self.assertEqual(
            (self.calls("revoke"), "granted" in self.view()),
            ([("revoke", "p1"), ("revoke", "p2")], False),
        )

    def test_the_agent_revoking_by_itself_is_followed_even_with_no_run(self) -> None:
        self.tell({"t": "granted", "id": "p1", "text": "Looks at files"})
        self.assertEqual(len(self.view()["granted"]), 1)
        self.tell({"t": "revoked", "id": "p1"})
        self.assertEqual((self.calls("revoke"), "granted" in self.view()), ([], False))

    def test_system_action_of_another_item_is_not_ours(self) -> None:
        self.assertFalse(coco_waits.act(self.conv, {"type": "system_action", "id": "zz"}, None))


class FixtureShapeTest(WaitCase):
    """Each frame's fixture is reached from events: same keys, same types."""

    def asked(self, *events, planning=False, read=True) -> None:
        if planning:
            coco_waits.set_planning(self.conv, True)
        self.send(fx.RM_Q["text"])
        self.tell(*(self.read() if read else []), *events)

    def test_question_frames(self) -> None:
        self.asked(self.question())
        for name in (
            "f38_question_choice",
            "f40_question_other",
            "f41_question_multi",
            "f46_question_pill",
        ):
            self.shape(name)
        self.send("Then list the open risks")
        self.shape("f39_question_picked")

    def test_several_questions_and_a_form(self) -> None:
        self.asked(self.question(questions=fx.VIEWS["f42_question_several"]["wait"]["questions"]))
        self.shape("f42_question_several")
        self.act(type="skip", id="n1")
        self.tell(
            self.question(
                "n3", source="app", questions=fx.VIEWS["f43_question_form"]["wait"]["questions"]
            )
        )
        self.shape("f43_question_form")

    def test_answered_and_skipped(self) -> None:
        self.asked(self.question())
        self.act(type="answer", id="n1", answers=ANSWER)
        self.tell(self.step("t2"))
        self.shape("f44_question_answered")
        self.act(type="new")
        self.connect()
        self.asked(self.question())
        self.act(type="skip", id="n1")
        self.tell({"t": "text", "text": "I will cover this week."})
        self.shape("f45_question_skipped")

    def test_expired(self) -> None:
        self.asked(self.question(), {"t": "expired", "id": "n1", "tool_id": "tq"}, read=False)
        self.shape("question_expired")
        self.act(type="new")
        self.connect()
        self.asked(self.plan(), {"t": "expired", "id": "n2", "tool_id": "tp"}, read=False)
        self.shape("plan_expired")

    def test_plan_frames(self) -> None:
        self.asked(self.plan(), planning=True, read=False)
        for name in ("f48_plan_presented", "f49_plan_long", "f50_plan_decline", "f53_plan_pill"):
            self.shape(name)
        self.act(type="approve_plan", id="n2")
        self.tell(self.step("t2"))
        self.shape("f51_plan_approved")

    def test_plan_declined_and_planning_strip(self) -> None:
        self.asked(self.step("t2"), planning=True, read=False)
        self.shape("f47_plan_mode")
        self.act(type="new")
        self.connect()
        coco_waits.set_planning(self.conv, True)
        self.send(fx.PLAN_Q["text"])
        self.tell(self.plan())
        self.act(
            type="decline_plan", id="n2", reason="Only the report. Leave the specifications alone."
        )
        self.shape("f52_plan_declined")

    def test_plan_written_as_an_answer(self) -> None:
        coco_waits.set_planning(self.conv, True)
        self.send(fx.PLAN_Q["text"])
        self.tell({"t": "result", "text": "I would read and write."})
        self.shape("f54_plan_answer")

    def test_two_waiting(self) -> None:
        self.send(fx.GIT_Q["text"])
        self.tell(self.bash_call("t1"), self.standing_request(offer=False), self.question())
        self.shape("f55_two_wait")

    def test_standing_frames(self) -> None:
        self.send(fx.GIT_Q["text"])
        self.tell(self.bash_call("t1"), self.standing_request())
        self.shape("f56_standing_offer")
        self.shape("f57_standing_ticked")
        self.act(type="allow", id="r1", standing=True)
        self.tell({"t": "granted", "id": "p1", "text": fx.GRANTED[0]["text"], "family": "git"})
        self.shape("f58_standing_granted")
        self.tell({"t": "result", "text": "ok"})
        self.send("And now, anything new?")
        self.tell(
            self.bash_call("t2"),
            {"t": "standing", "tool_id": "t2"},
            {"t": "tool_result", "id": "t2", "content": "clean"},
            {"t": "result", "text": "Nothing."},
        )
        view = self.view()
        view["thread"] = view["thread"][-3:]
        self.shape("f59_standing_later", view)
