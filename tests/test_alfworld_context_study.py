"""CPU contracts for the matched experience/history-window study."""
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/agent_frontier_portfolio_20261029/alfworld_context_study.py"
spec = importlib.util.spec_from_file_location("alfworld_context_study_contract", SCRIPT)
r = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = r
spec.loader.exec_module(r)

PUBLIC_KEYS = ("observation", "score", "done", "won", "action_count", "admissible_commands")
RECOVERY_ARMS = ("keep_full", "keep_recent", "drop_full", "drop_recent")
ARMS = ("collect", "collect_none", "goal_recent", "ordinary_reset") + RECOVERY_ARMS
EXPERIENCE = '\n  SOURCE_EXPERIENCE_BEGIN\n`tool` "quoted" 中文\nSOURCE_EXPERIENCE_END\n\n'


def public_state(count, observation):
    return {"observation": observation, "score": 0.0, "done": False, "won": False,
            "action_count": count, "admissible_commands": ["look", "inventory"]}


def prompt_inputs():
    reset = public_state(0, "Your task is to: heat some egg and put it in diningtable. RESET_PUBLIC_GOAL")
    reset["expert_plan"] = "NEVER_RENDER_RESET_EXPERT_PLAN"
    steps = []
    for index in range(1, 7):
        state = public_state(index, "HISTORY_OBSERVATION_%02d" % index)
        state["hidden_pddl"] = "NEVER_RENDER_HISTORY_HIDDEN_%02d" % index
        steps.append({"event": "step", "action": "go to historical_location_%02d" % index,
                      "state": state, "private_metadata": "NEVER_RENDER_STEP_PRIVATE_METADATA"})
    current = public_state(6, "COMPLETE_CURRENT_PUBLIC_OBSERVATION")
    current["admissible_commands"] = ["take egg 1 from diningtable 1", "inventory", "look",
                                       "examine COMPLETE_CURRENT_ADMISSIBLE_TAIL"]
    current["hidden_goal"] = "NEVER_RENDER_CURRENT_HIDDEN_GOAL"
    return reset, steps, current


def json_objects(text):
    """Find embedded JSON independently of presentation headings."""
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            yield value


def history_range(text):
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "[":
            continue
        try:
            value, length = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, list) and value and all(
                isinstance(row, dict) and "action" in row and "state" in row for row in value):
            return index, index + length
    raise AssertionError("accepted target history is not represented as JSON records")


def render(reset, steps, current, keep, window):
    return r.render_prompt(reset, steps, current, EXPERIENCE, keep, window)


class ContextPromptTests(unittest.TestCase):
    def test_ordinary_reset_is_the_exact_empty_history_public_recovery_contract(self):
        reset, steps, current = prompt_inputs()
        expected = r.render_prompt(reset, [], reset, "", False, "recent")
        assignment = {"carrier": "ordinary_public_history"}
        actual = r.initial_prompt(reset, "ordinary_reset", assignment, EXPERIENCE)
        self.assertEqual(actual.encode(), expected.encode())
        self.assertEqual(actual, r.initial_prompt(reset, "ordinary_reset", assignment, "OTHER_SOURCE"))
        for absent in ("SOURCE_EXPERIENCE_BEGIN", "HISTORY_OBSERVATION_", current["observation"], "NEVER_RENDER"):
            self.assertNotIn(absent, actual)
        self.assertIn({key: reset[key] for key in PUBLIC_KEYS}, list(json_objects(actual)))

    def test_restatement_adds_only_the_existing_public_goal_to_drop_recent(self):
        reset, steps, current = prompt_inputs()
        baseline = render(reset, steps, current, False, "recent")
        restated = r.recovery_prompt(reset, steps, current, EXPERIENCE, "goal_recent")
        goal = reset["observation"].split("Your task is to:", 1)[1].strip()
        self.assertEqual(restated, baseline +
            "\nCurrent task to finish (restated from the public reset): " + goal + "\n")
        self.assertNotIn("SOURCE_EXPERIENCE_BEGIN", restated)
        self.assertNotIn("NEVER_RENDER", restated)
        for stage in RECOVERY_ARMS:
            with self.subTest(stage=stage):
                self.assertEqual(r.recovery_prompt(reset, steps, current, EXPERIENCE, stage),
                    render(reset, steps, current, stage.startswith("keep_"), stage.split("_")[1]))
        for observation in ("No explicit public goal.", "Your task is to:",
                            "Your task is to: heat egg.\nUnrelated extra text.",
                            "Your task is to: heat egg. Your task is to: clean egg."):
            with self.subTest(observation=observation), self.assertRaises(ValueError):
                r.recovery_prompt(dict(reset, observation=observation), steps, current, EXPERIENCE, "goal_recent")

    def test_no_experience_collection_uses_same_task_without_any_carrier(self):
        def frozen_task(state, condition="none", experience=None):
            prompt = "FROZEN_TASK:" + state["observation"]
            return prompt if condition == "none" else prompt + "\n" + experience

        core = SimpleNamespace(condition_prompt=mock.Mock(side_effect=frozen_task))
        rec = SimpleNamespace(actor=lambda: core)
        reset, _, _ = prompt_inputs()
        assignment = {"carrier": "ordinary_public_history"}
        with mock.patch.object(r, "recovery", return_value=rec):
            ordinary = r.collection_prompt(reset, "collect", assignment, EXPERIENCE)
            plain = r.collection_prompt(reset, "collect_none", assignment, EXPERIENCE)
            alternate = r.collection_prompt(reset, "collect_none", assignment, "OTHER_SOURCE")
            self.assertEqual(r.initial_prompt(reset, "collect", assignment, EXPERIENCE), ordinary)
            self.assertEqual(r.initial_prompt(reset, "collect_none", assignment, EXPERIENCE), plain)
            with self.assertRaises(ValueError):
                r.collection_prompt(reset, "drop_recent", assignment, EXPERIENCE)
        self.assertEqual(ordinary, plain + "\n" + EXPERIENCE)
        self.assertEqual(plain, alternate)
        self.assertIn(reset["observation"], plain)
        self.assertNotIn("SOURCE_EXPERIENCE_BEGIN", plain)
        self.assertEqual(core.condition_prompt.call_args_list[1], mock.call(reset, "none"))

    def test_four_arms_preserve_full_goal_current_state_and_shared_tool_contract(self):
        reset, steps, current = prompt_inputs()
        before = copy.deepcopy((reset, steps, current))
        expected_current = {key: current[key] for key in PUBLIC_KEYS}
        for keep in (True, False):
            for window in ("full", "recent"):
                with self.subTest(keep=keep, window=window):
                    text = render(reset, steps, current, keep, window)
                    self.assertIn(reset["observation"], text)
                    self.assertIn(expected_current, list(json_objects(text)))
                    self.assertIn("/runtime/bin/python -B /world/client.py step --socket /world/s --action", text)
                    self.assertIn("done", text)
                    self.assertIn("won", text)
                    for command in current["admissible_commands"]:
                        self.assertIn(command, text)
                    self.assertNotIn("NEVER_RENDER", text)
        self.assertEqual((reset, steps, current), before)

    def test_keep_preserves_exact_experience_bytes_while_drop_is_experience_independent(self):
        reset, steps, current = prompt_inputs()
        for window in ("full", "recent"):
            with self.subTest(window=window):
                kept = render(reset, steps, current, True, window)
                dropped = render(reset, steps, current, False, window)
                self.assertEqual(kept.count(EXPERIENCE), 1)
                self.assertNotIn("SOURCE_EXPERIENCE_BEGIN", dropped)
                self.assertEqual(kept.replace(EXPERIENCE, "", 1), dropped)
                other = r.render_prompt(reset, steps, current, "DIFFERENT_FROZEN_SOURCE_BYTES", False, window)
                self.assertEqual(dropped, other)

    def test_recent_means_last_three_accepted_target_observations_in_order(self):
        reset, steps, current = prompt_inputs()
        self.assertEqual(r.RECENT_STEPS, 3)
        for keep in (True, False):
            with self.subTest(keep=keep):
                full = render(reset, steps, current, keep, "full")
                recent = render(reset, steps, current, keep, "recent")
                positions = []
                for index in range(1, 7):
                    observation = "HISTORY_OBSERVATION_%02d" % index
                    action = "go to historical_location_%02d" % index
                    self.assertIn(observation, full)
                    self.assertIn(action, full)
                    if index <= 3:
                        self.assertNotIn(observation, recent)
                        self.assertNotIn(action, recent)
                    else:
                        self.assertIn(observation, recent)
                        self.assertIn(action, recent)
                        positions.append(recent.index(observation))
                self.assertEqual(positions, sorted(positions))
                full_start, full_end = history_range(full)
                recent_start, recent_end = history_range(recent)
                self.assertEqual(full[:full_start] + full[full_end:],
                                 recent[:recent_start] + recent[recent_end:])

    def test_short_history_does_not_add_an_arm_hint_or_change_common_prompt(self):
        reset, steps, current = prompt_inputs()
        for count in (0, 1, 3):
            for keep in (True, False):
                with self.subTest(count=count, keep=keep):
                    self.assertEqual(render(reset, steps[:count], current, keep, "full"),
                                     render(reset, steps[:count], current, keep, "recent"))
        with self.assertRaises(ValueError):
            render(reset, steps, current, True, "unknown_window")


class ContextAccountingTests(unittest.TestCase):
    def setUp(self):
        self.total = {"posts": 20, "seconds": 60, "world_actions": 30, "model_payload_bytes_combined": 10000}
        self.receipt = {"model_posts": 5, "elapsed_seconds": 11.25, "world_actions": 7,
                        "model_request_payload_bytes": 1000, "model_response_wire_bytes": 2000,
                        "provider_usage": {"prompt_tokens": 999, "completion_tokens": 22,
                                           "prompt_tokens_details": {"cached_tokens": 800}},
                        "raw_step_tokens_separate_not_added": [{"total": 1021, "cache": {"read": 800}}]}

    def test_remaining_caps_use_physical_costs_once_and_preserve_inputs(self):
        before = copy.deepcopy((self.total, self.receipt))
        remaining = r.remaining_caps(self.total, self.receipt)
        self.assertEqual(set(remaining), set(self.total))
        self.assertEqual(remaining["posts"], 15)
        self.assertEqual(remaining["world_actions"], 23)
        self.assertEqual(remaining["model_payload_bytes_combined"], 7000)
        exact_seconds = self.total["seconds"] - self.receipt["elapsed_seconds"]
        self.assertLessEqual(remaining["seconds"], exact_seconds)
        self.assertGreater(remaining["seconds"], exact_seconds - 1)
        changed_cache = copy.deepcopy(self.receipt)
        changed_cache["provider_usage"] = None
        changed_cache["raw_step_tokens_separate_not_added"] = [{"total": 999999999, "cache": {"read": 999999999}}]
        self.assertEqual(r.remaining_caps(self.total, changed_cache), remaining)
        self.assertEqual((self.total, self.receipt), before)

    def test_negative_nonfinite_and_overrun_costs_fail_closed(self):
        invalid = [(key, -1) for key in ("model_posts", "elapsed_seconds", "world_actions",
                                       "model_request_payload_bytes", "model_response_wire_bytes")]
        invalid += [("elapsed_seconds", float("nan")), ("elapsed_seconds", float("inf")),
                    ("model_posts", 21), ("elapsed_seconds", 61), ("world_actions", 31),
                    ("model_request_payload_bytes", 10001), ("model_response_wire_bytes", 10001)]
        for key, value in invalid:
            with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                r.remaining_caps(self.total, dict(self.receipt, **{key: value}))

    def test_exact_exhaustion_cannot_create_an_executable_followup_budget(self):
        for exhausted in ({"model_posts": 20}, {"elapsed_seconds": 60}, {"world_actions": 30},
                          {"model_request_payload_bytes": 8000},
                          {"model_posts": 20, "elapsed_seconds": 60, "world_actions": 30,
                           "model_request_payload_bytes": 4000, "model_response_wire_bytes": 6000}):
            with self.subTest(exhausted=exhausted), self.assertRaises(ValueError):
                r.remaining_caps(self.total, dict(self.receipt, **exhausted))


class ContextStageDispatchTests(unittest.TestCase):
    def setUp(self):
        self.study = {
            "total_caps": {"posts": 128, "seconds": 1800, "world_actions": 100,
                           "model_payload_bytes_combined": 64000000},
            "collection_caps": {"posts": 32, "seconds": 600, "world_actions": 100,
                                "model_payload_bytes_combined": 64000000}}
        self.prefix = {"receipt": {"model_posts": 8, "elapsed_seconds": 90.25, "world_actions": 10,
                                   "model_request_payload_bytes": 1000, "model_response_wire_bytes": 2000}}

    def test_reset_uses_total_caps_and_all_old_stage_caps_are_unchanged(self):
        before = copy.deepcopy((self.study, self.prefix))
        self.assertIs(r.stage_caps("ordinary_reset", self.study, None), self.study["total_caps"])
        for stage in ("collect", "collect_none"):
            self.assertIs(r.stage_caps(stage, self.study, None), self.study["collection_caps"])
        for stage in RECOVERY_ARMS + ("goal_recent",):
            with self.subTest(stage=stage):
                self.assertEqual(r.stage_caps(stage, self.study, self.prefix),
                                 r.remaining_caps(self.study["total_caps"], self.prefix["receipt"]))
        self.assertEqual((self.study, self.prefix), before)

    def test_prepare_verify_both_backends_keep_reset_progress_and_total_caps(self):
        validator = r.recovery().bridge().validate_response

        def write_new(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as out:
                json.dump(value, out)

        with tempfile.TemporaryDirectory() as tmp:
            qual = Path(tmp).resolve()
            binary = qual / "mock-binary"
            binary.write_bytes(b"OFFLINE_ONLY")
            reset = public_state(0, "Your task is to: heat some egg and put it in diningtable.")
            study = dict(self.study, world_seed=17, pool_path="D-only-pool", pool_sha256="mock-pool-sha")
            assignment = {"carrier": "ordinary_public_history", "source_id": "D-only-source"}
            game, binding = {"game_path": "D-only-game"}, {"sha256": "mock-game-sha"}
            profile = {"model_id": "mock-model"}
            core = SimpleNamespace(load_profile=mock.Mock(return_value=profile), write_new=write_new,
                config=lambda p, seed: {"model": p["model_id"], "seed": seed},
                model_payload=lambda *args: {"mock_sampling": True},
                PROFILE_PINS={backend: ("mock-profile", "mock-profile-sha") for backend in ("student8b", "teacher27b")},
                dependencies=SimpleNamespace(verify_projection=mock.Mock()),
                RUNTIME_ROOT=qual / "mock-runtime", RUNTIME_SHA="mock-runtime-sha",
                BINARY=binary, BINARY_SHA=r.sha(binary), IMAGE="mock-image", stop_world=mock.Mock())
            rec = SimpleNamespace(actor=lambda: core, bridge=lambda: SimpleNamespace(validate_response=validator),
                                  token_qualifier=mock.Mock(return_value=({"tokenizer": "offline"}, mock.Mock())))
            pool = SimpleNamespace(start_world=mock.Mock(return_value=((object(), qual / "mock-world"), reset, game)))
            with mock.patch.object(r, "QUAL", qual), mock.patch.object(r, "recovery", return_value=rec), \
                    mock.patch.object(r, "protocol", return_value=study), \
                    mock.patch.object(r, "read_case", return_value=(game, binding, assignment, EXPERIENCE)), \
                    mock.patch.object(r, "components", return_value={"offline_test": "fixed"}), \
                    mock.patch.object(r, "task_pool", return_value=pool), \
                    mock.patch.object(r, "load_prefix", side_effect=AssertionError("ordinary has no source")), \
                    mock.patch.object(r, "cohort_binding", side_effect=AssertionError("ordinary has no cohort")), \
                    mock.patch.object(r.os, "getuid", return_value=1000, create=True), \
                    mock.patch.object(r.os, "getgid", return_value=1000, create=True), \
                    mock.patch.object(r.subprocess, "check_output", return_value="mock-image-id\n"), \
                    mock.patch("socket.create_connection", side_effect=AssertionError("no network")):
                for backend in ("student8b", "teacher27b"):
                    with self.subTest(backend=backend):
                        root = qual / ("context_study_v1/cases/heat_2/ordinary_reset/" + backend + "/attempt_v1")
                        manifest = r.prepare(root, qual / "mock-protocol.json", "a" * 64)
                        verified = r.verify(root, r.sha(root / "manifest.json"))
                        self.assertIsNone(verified[3])
                        self.assertEqual(manifest["caps"], self.study["total_caps"])
                        for key in ("source_root", "source_binding", "cohort_binding"):
                            self.assertIsNone(manifest[key])
                        self.assertEqual((root / "task.txt").read_bytes(),
                                         r.render_prompt(reset, [], reset, "", False, "recent").encode())
                        self.assertEqual(pool.start_world.call_args.args[4]["world_actions"], 100)
                        self.assertFalse((root.parents[2] / "RECOVERY_COHORT.json").exists())
                        # Even a rehashed manifest cannot disguise a recovery handoff as a reset.
                        (root / "handoff_public.json").write_text(json.dumps(public_state(1, "Existing progress")), encoding="utf-8")
                        manifest["inputs_sha256"]["handoff_public.json"] = r.sha(root / "handoff_public.json")
                        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                        with self.assertRaisesRegex(ValueError, "cannot contain recovery progress"):
                            r.verify(root, r.sha(root / "manifest.json"))

    def test_only_actual_recovery_stages_accept_a_source_prefix(self):
        invalid = [(stage, self.prefix) for stage in ("collect", "collect_none", "ordinary_reset")]
        invalid += [(stage, None) for stage in RECOVERY_ARMS + ("goal_recent",)]
        invalid += [("invented", None), ("invented", self.prefix)]
        for stage, prefix in invalid:
            with self.subTest(stage=stage, prefix=prefix), self.assertRaises(ValueError):
                r.stage_caps(stage, self.study, prefix)

    def test_verify_rejects_forged_reset_recovery_switches_before_cohort_or_actor(self):
        invalid = [(stage, "mock-source", None) for stage in ("collect", "collect_none", "ordinary_reset")]
        invalid += [(stage, None, None) for stage in RECOVERY_ARMS + ("goal_recent",)]
        invalid.append(("ordinary_reset", None, {"path": "forged-recovery-cohort"}))
        with tempfile.TemporaryDirectory() as tmp:
            qual = Path(tmp).resolve()
            for index, (stage, source_root, cohort) in enumerate(invalid, 1):
                root = qual / ("context_study_v1/cases/heat_2/" + stage + "/student8b/attempt_v" + str(index))
                root.mkdir(parents=True)
                manifest = {"case_id": "heat_2", "stage": stage, "backend": "student8b", "components": {},
                            "protocol_path": "mock-protocol", "protocol_sha256": "a" * 64,
                            "source_root": source_root, "cohort_binding": cohort}
                (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.subTest(stage=stage, source_root=source_root, cohort=cohort), \
                        mock.patch.object(r, "QUAL", qual), mock.patch.object(r, "components", return_value={}), \
                        mock.patch.object(r, "protocol", return_value=self.study), \
                        mock.patch.object(r, "read_case", return_value=({}, {}, {}, "D_ONLY_SOURCE")), \
                        mock.patch.object(r, "load_prefix", return_value=self.prefix) as load, \
                        mock.patch.object(r, "cohort_binding", side_effect=AssertionError("no cohort mutation")), \
                        mock.patch.object(r, "recovery", side_effect=AssertionError("no actor access")):
                    with self.assertRaises(ValueError):
                        r.verify(root, r.sha(root / "manifest.json"))
                    self.assertEqual(load.call_count, int(source_root is not None))

    def test_ordinary_timeout_is_an_episode_timeout_without_any_actor_or_model(self):
        def write_new(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as out:
                json.dump(value, out)

        with tempfile.TemporaryDirectory() as tmp:
            qual = Path(tmp).resolve()
            root = qual / "context_study_v1/cases/heat_2/ordinary_reset/teacher27b/attempt_v1"
            root.mkdir(parents=True)
            manifest = {"case_id": "heat_2", "stage": "ordinary_reset", "backend": "teacher27b",
                        "world_seed": 17, "caps": self.study["total_caps"], "source_binding": None}
            study = {"pool_path": "mock-not-read", "pool_sha256": "mock-sha"}
            core = SimpleNamespace(write_new=write_new, ModelRelay=type("UnusedRelay", (), {}))
            pool = SimpleNamespace(start_world=mock.Mock(side_effect=subprocess.TimeoutExpired("mock-world", 1)))
            with mock.patch.object(r, "QUAL", qual), \
                    mock.patch.object(r, "verify", return_value=(manifest, study, {}, None, None)), \
                    mock.patch.object(r, "recovery", return_value=SimpleNamespace(actor=lambda: core)), \
                    mock.patch.object(r, "task_pool", return_value=pool), \
                    mock.patch.object(r.subprocess, "run", side_effect=AssertionError("no actor process")), \
                    mock.patch("socket.create_connection", side_effect=AssertionError("no network")):
                receipt = r.run_episode(root, "mock-manifest-sha")
            self.assertEqual(receipt["status"], "EPISODE_TIMEOUT")
            self.assertEqual(receipt["errors"], [])
            self.assertEqual(receipt["real_model_calls"], 0)
            self.assertIsNone(receipt["source_binding_charge_once"])


class ContextContinuationTests(unittest.TestCase):
    def test_only_normal_exit_unfinished_known_world_and_real_remaining_budget_qualify(self):
        healthy = {"first_exit": 0, "final": public_state(8, "actual unfinished state"),
                   "posts": 5, "max_posts": 20, "elapsed": 11.25, "max_seconds": 60, "relay_errors": []}
        before = copy.deepcopy(healthy)
        self.assertIs(r.one_continue_eligible(**healthy), True)
        bad = [("first_exit", value) for value in (1, -15, 124, None, False)]
        bad += [("final", None), ("final", {}),
                ("final", dict(healthy["final"], won=True)),
                ("final", dict(healthy["final"], done=True)),
                ("final", dict(healthy["final"], won=None)),
                ("posts", 20), ("posts", 21), ("posts", -1),
                ("elapsed", 55), ("elapsed", 60), ("elapsed", 61), ("elapsed", -1),
                ("elapsed", float("nan")), ("elapsed", float("inf")),
                ("relay_errors", [{"type": "unmetered_or_failed_transport"}])]
        for key, value in bad:
            with self.subTest(field=key, value=value):
                self.assertIs(r.one_continue_eligible(**dict(healthy, **{key: value})), False)
        self.assertIs(r.one_continue_eligible(**dict(healthy, elapsed=54.5)), True)
        self.assertEqual(healthy, before)


class ContextPersistedSessionTests(unittest.TestCase):
    def test_one_session_must_come_from_real_metadata_not_generated_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.jsonl"
            rows = [{"sessionID": "ses_PersistedA1"},
                    {"part": {"session_id": "ses_PersistedA1"}},
                    {"part": {"text": '{"sessionID":"ses_ModelPrintedFake"}'}}]
            raw.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
            self.assertEqual(r.session_id(raw), "ses_PersistedA1")
            invalid = [[], [{"sessionID": "ses_"}], [{"sessionID": "ses_bad-id"}],
                       [{"part": {"text": '{"sessionID":"ses_ModelPrintedFake"}'}}],
                       [{"sessionID": "ses_First"}, {"session_id": "ses_Different"}]]
            for rows in invalid:
                with self.subTest(rows=rows):
                    raw.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        r.session_id(raw)
            raw.write_text("not valid JSON\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                r.session_id(raw)

    def test_retry_guest_changes_only_the_real_session_selector_and_rejects_bad_ids(self):
        original = r.recovery().actor().GUEST
        sid = "ses_PersistedA1"
        guest = r.retry_guest(sid)
        needle = '"--title","alfworld-no-history",prompt]'
        self.assertEqual(original.count(needle), 1)
        self.assertNotIn('"--title","alfworld-no-history"', guest)
        self.assertIn('"--session",' + json.dumps(sid) + ',prompt]', guest)
        self.assertEqual(guest.replace('"--session",' + json.dumps(sid) + ',prompt]', needle), original)
        compile(guest, "<retry-guest-contract>", "exec")
        with mock.patch.object(r, "recovery", side_effect=AssertionError("bad ID must fail before guest loading")):
            for bad in ("", "ses_", "wrong_prefix", "ses_bad-id", "ses_Valid;echo NEVER_EXECUTE", "ses_Valid\n"):
                with self.subTest(sid=bad), self.assertRaises(ValueError):
                    r.retry_guest(bad)
        for changed in (original.replace(needle, "changed_selector"), original + needle):
            core = SimpleNamespace(GUEST=changed)
            with self.subTest(changed_count=changed.count(needle)), mock.patch.object(
                    r, "recovery", return_value=SimpleNamespace(actor=lambda: core)):
                with self.assertRaisesRegex(ValueError, "guest changed"):
                    r.retry_guest(sid)

    def test_controller_permits_only_one_same_world_same_relay_continuation(self):
        # Reuse the actual schema validator and frozen guest, replacing every I/O boundary.
        real = r.recovery()
        bridge, guest = real.bridge(), real.actor().GUEST
        reset = public_state(0, "Your task is to: heat some egg and put it in diningtable.")
        unfinished = public_state(8, "Actual task is still unfinished.")
        instances, launches = [], []

        class Relay:
            def __init__(self, *args, **kwargs):
                self.budget = SimpleNamespace(posts=0, request_bytes=0, response_bytes=0)
                self.forwarded, self.errors, self.delivery, self.closed = 0, [], None, False
                instances.append(self)

            def begin_close(self):
                pass

            def close(self):
                self.closed = True

        def write_new(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                json.dump(value, handle)

        with tempfile.TemporaryDirectory() as tmp:
            qual = Path(tmp).resolve()
            root = qual / "context_study_v1/cases/heat_2/collect/student8b/attempt_v1"
            root.mkdir(parents=True)
            frozen_task = "FROZEN_CURRENT_GOAL_AND_CONTEXT"
            for name, value in (("initial_reset.json", reset), ("handoff_public.json", reset),
                                ("opencode_config.json", {})):
                write_new(root / name, value)
            (root / "task.txt").write_text(frozen_task, encoding="utf-8")
            caps = {"posts": 20, "seconds": 120, "world_actions": 100, "model_payload_bytes_combined": 10000}
            manifest = {"case_id": "heat_2", "stage": "collect", "backend": "student8b",
                        "world_seed": 17, "model_seed": 17, "caps": caps, "sampling": {}, "source_binding": None}
            study = {"context_margin_tokens": 512, "pool_path": "mock-not-read", "pool_sha256": "mock-pool"}
            profile = {"host": "mock-not-connected", "port": 1, "context": 32768, "output": 8192}
            core = SimpleNamespace(GUEST=guest, ModelRelay=Relay, write_new=write_new,
                socket_directory=mock.Mock(return_value=qual / "mock-model-sockets"),
                docker_command=mock.Mock(return_value=["mock-context-actor"]),
                stop_world=mock.Mock(), cleanup_directory=mock.Mock())
            pool = SimpleNamespace(start_world=mock.Mock(return_value=((object(), qual / "mock-world-sockets"), reset, {})))
            rec = SimpleNamespace(actor=lambda: core, bridge=lambda: bridge)

            def process(argv, **kwargs):
                if argv == ["mock-context-actor"]:
                    work = root / "workspace"
                    launches.append({"task": (work / "task.txt").read_text(),
                                     "guest": (work / "guest.py").read_text(), "timeout": kwargs["timeout"]})
                    if len(launches) > 2:
                        raise AssertionError("a third actor round is forbidden")
                    kwargs["stdout"].write((json.dumps({"type": "step_finish", "sessionID": "ses_PersistedA1"}) + "\n").encode())
                elif argv[:3] != ["docker", "rm", "-f"]:
                    raise AssertionError("unexpected external process: " + repr(argv))
                return subprocess.CompletedProcess(argv, 0)

            with mock.patch.object(r, "QUAL", qual), mock.patch.object(r, "recovery", return_value=rec), \
                    mock.patch.object(r, "task_pool", return_value=pool), \
                    mock.patch.object(r, "verify", return_value=(manifest, study, profile, None, mock.Mock())), \
                    mock.patch.object(r, "final_state", return_value=unfinished), \
                    mock.patch.object(r.subprocess, "run", side_effect=process), \
                    mock.patch("socket.create_connection", side_effect=AssertionError("no network")):
                receipt = r.run_episode(root, "mock-frozen-digest", fake_endpoint=("mock-not-connected", 1))
            self.assertEqual(receipt["status"], "RETURNED")
            self.assertEqual(receipt["errors"], [])
            self.assertEqual(len(launches), 2)
            self.assertEqual(receipt["ordinary_continuations"], 1)
            self.assertEqual(receipt["real_model_calls"], 0)
            self.assertEqual(launches[0]["task"], frozen_task)
            self.assertEqual(launches[1]["task"], r.CONTINUE)
            self.assertEqual(launches[0]["guest"], guest)
            self.assertIn('"--session","ses_PersistedA1",prompt]', launches[1]["guest"])
            self.assertLessEqual(launches[1]["timeout"], launches[0]["timeout"])
            self.assertEqual(pool.start_world.call_count, 1)
            self.assertEqual(len(instances), 1)
            self.assertTrue(instances[0].closed)
            self.assertFalse(json.loads((root / "ordinary_continuation.json").read_text())["world_reset"])
            self.assertIsNone(receipt["provider_cached_input_tokens"])


class ContextNamespaceTests(unittest.TestCase):
    def test_only_canonical_case_arm_backend_attempt_names_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(r, "QUAL", Path(tmp).resolve()):
            cases = r.QUAL / "context_study_v1/cases"
            for arm in ARMS:
                for backend in ("teacher27b", "student8b"):
                    path = cases / "heat_2" / arm / backend / "attempt_v1"
                    with self.subTest(arm=arm, backend=backend):
                        r.check_root(path)
                        self.assertFalse(path.exists())
            invalid = [r.QUAL / "outside/heat_2/keep_full/student8b/attempt_v1",
                       cases / "heat_2/not_an_arm/student8b/attempt_v1",
                       cases / "heat_2/keep_full/attempt_v1",
                       cases / "heat_2/keep_full/student8b/attempt_v0",
                       cases / "heat_2/keep_full/student8b/attempt_v01",
                       cases / "heat_2/keep_full/student8b/attempt_v-1",
                       cases / "heat_2/keep_full/student8b/attempt_v1/extra"]
            for path in invalid:
                with self.subTest(path=str(path)), self.assertRaises(ValueError):
                    r.check_root(path)

    def test_direct_and_parent_symlink_aliases_cannot_enter_the_canonical_namespace(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(r, "QUAL", Path(tmp).resolve()):
            root = r.QUAL / "context_study_v1/cases/heat_2/keep_full/student8b/attempt_v1"
            root.mkdir(parents=True)
            direct, parent = r.QUAL / "outside_alias", r.QUAL / "parent_alias"
            case_alias = root.parents[2].with_name("alias_case")
            try:
                direct.symlink_to(root, target_is_directory=True)
                parent.symlink_to(root.parent, target_is_directory=True)
                case_alias.symlink_to(root.parents[2], target_is_directory=True)
            except OSError as exc:
                self.skipTest("symlinks unavailable: " + str(exc))
            for path in (direct, parent / root.name,
                         case_alias / "keep_full/student8b/attempt_v1"):
                with self.subTest(path=str(path)), self.assertRaises(ValueError):
                    r.check_root(path)


@contextmanager
def collector_fixture():
    """Synthetic archived case; no real profile, source or model is accessed."""
    validator = r.recovery().bridge().validate_response
    with tempfile.TemporaryDirectory() as tmp:
        qual = Path(tmp).resolve()
        root = qual / "context_study_v1/cases/heat_2/collect/student8b/attempt_v1"
        root.mkdir(parents=True)
        protocol_sha = "a" * 64
        manifest = {"protocol_sha256": protocol_sha, "case_id": "heat_2", "stage": "collect", "backend": "student8b"}
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        digest = r.sha(root / "manifest.json")
        reset = public_state(0, "Public reset goal.")
        final = public_state(1, "Actual unfinished public observation.")
        events = [{"event": "reset", "state": reset}, {"event": "step", "action": "look", "state": final}]
        (root / "execute_world.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
        receipt = {"label": "MULTITASK_CONTEXT_DEVELOPMENT", "status": "RETURNED",
                   "manifest_sha256": digest, "real_model_calls": 1, "forwarded_model_posts": 1,
                   "model_posts": 1, "won": False, "unknown_usage_model_posts": 0,
                   "final_world_state": final, "world_actions": 1}
        reservation = {"mode": "REAL_DEVELOPMENT", "manifest_sha256": digest}
        for name, value in (("receipt.json", receipt), ("reservation.json", reservation)):
            (root / name).write_text(json.dumps(value), encoding="utf-8")

        def exclusive_write(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                json.dump(value, handle)

        writer = mock.Mock(side_effect=exclusive_write)
        rec = SimpleNamespace(actor=lambda: SimpleNamespace(write_new=writer),
                              bridge=lambda: SimpleNamespace(validate_response=validator))
        with mock.patch.object(r, "QUAL", qual), mock.patch.object(r, "recovery", return_value=rec):
            yield SimpleNamespace(qual=qual, root=root, receipt=receipt, reservation=reservation,
                                  protocol_sha=protocol_sha, writer=writer)


class ContextCollectorBindingTests(unittest.TestCase):
    def test_relabeling_an_ordinary_manifest_cannot_create_a_real_collector(self):
        with collector_fixture() as f:
            path = f.root / "manifest.json"
            original = json.loads(path.read_text())
            for change in ({"stage": "ordinary_reset"}, {"stage": "collect_none"},
                           {"backend": "teacher27b"}, {"case_id": "other_case"}):
                with self.subTest(change=change):
                    path.write_text(json.dumps(dict(original, **change)), encoding="utf-8")
                    digest = r.sha(path)
                    for name, value in (("receipt.json", f.receipt), ("reservation.json", f.reservation)):
                        (f.root / name).write_text(json.dumps(dict(value, manifest_sha256=digest)), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "student collection"):
                        r.load_prefix(f.root, "heat_2")

    def test_plain_reset_and_other_noncollector_paths_cannot_seed_real_recovery(self):
        with collector_fixture() as f:
            for stage, backend in (("ordinary_reset", "student8b"), ("ordinary_reset", "teacher27b"),
                                   ("collect_none", "student8b"), ("collect", "teacher27b")):
                root = f.root.parents[2] / stage / backend / "attempt_v1"
                with self.subTest(stage=stage, backend=backend), self.assertRaisesRegex(ValueError, "student collection"):
                    r.load_prefix(root, "heat_2")

    def test_only_real_positive_call_collection_and_real_reservation_can_seed_recovery(self):
        with collector_fixture() as f:
            prefix = r.load_prefix(f.root, "heat_2")
            self.assertEqual(len(prefix["steps"]), 1)
            self.assertEqual(prefix["binding"], {str(f.root / name): r.sha(f.root / name)
                             for name in ("manifest.json", "receipt.json", "execute_world.jsonl")})
            invalid = [({"label": "OWNED_FAKE_NOT_SCIENTIFIC"}, {}),
                       ({"real_model_calls": 0, "forwarded_model_posts": 0}, {}),
                       ({"real_model_calls": -1}, {}), ({"real_model_calls": True}, {}),
                       ({"forwarded_model_posts": 0}, {}),
                       ({}, {"mode": "OWNED_FAKE"}), ({}, {"mode": None}),
                       ({}, {"manifest_sha256": "different-frozen-attempt"})]
            for receipt_change, reservation_change in invalid:
                with self.subTest(receipt=receipt_change, reservation=reservation_change):
                    (f.root / "receipt.json").write_text(json.dumps(dict(f.receipt, **receipt_change)), encoding="utf-8")
                    (f.root / "reservation.json").write_text(
                        json.dumps(dict(f.reservation, **reservation_change)), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "actual model collection"):
                        r.load_prefix(f.root, "heat_2")

    def test_four_arms_share_one_exclusively_frozen_collector_and_protocol(self):
        with collector_fixture() as f:
            prefix = r.load_prefix(f.root, "heat_2")
            pointer = f.root.parents[2] / "RECOVERY_COHORT.json"
            self.assertFalse(pointer.exists())
            frozen_bytes, binding = None, None
            for arm in RECOVERY_ARMS:
                episode = f.root.parents[2] / arm / "student8b/attempt_v1"
                current = r.cohort_binding(episode, prefix, f.protocol_sha)
                self.assertEqual(Path(current["path"]), pointer)
                if frozen_bytes is None:
                    frozen_bytes, binding = pointer.read_bytes(), current
                self.assertEqual(pointer.read_bytes(), frozen_bytes)
                self.assertEqual(current, binding)
            self.assertEqual(f.writer.call_count, 4)
            self.assertTrue(all(call.args[0] == pointer for call in f.writer.call_args_list))
            episode = f.root.parents[2] / "keep_full/student8b/attempt_v2"
            changed_root = dict(prefix, root=f.root.with_name("attempt_v2"))
            changed_hash = dict(prefix, binding={**prefix["binding"], str(f.root / "receipt.json"): "b" * 64})
            for changed in (changed_root, changed_hash):
                with self.subTest(change="source root" if changed is changed_root else "source hash"):
                    with self.assertRaisesRegex(ValueError, "same frozen collector"):
                        r.cohort_binding(episode, changed, f.protocol_sha)
                    self.assertEqual(pointer.read_bytes(), frozen_bytes)
            writes_before = f.writer.call_count
            with self.assertRaisesRegex(ValueError, "different frozen study"):
                r.cohort_binding(episode, prefix, "c" * 64)
            self.assertEqual(f.writer.call_count, writes_before)
            changed_protocol = dict(prefix, manifest={**prefix["manifest"], "protocol_sha256": "c" * 64})
            with self.assertRaisesRegex(ValueError, "same frozen collector"):
                r.cohort_binding(episode, changed_protocol, "c" * 64)
            self.assertEqual(pointer.read_bytes(), frozen_bytes)


def test_replay_metadata_adapter_keeps_immutable_source_binding():
    prefix = {'binding': {'receipt.json': 'original-file-hash'},
              'public_prefix_sha256': 'canonical-public-prefix-hash', 'steps': []}
    before = copy.deepcopy(prefix)
    replay = mock.Mock(return_value=('current', 'cost'))
    with mock.patch.object(r, 'recovery', return_value=SimpleNamespace(replay=replay)):
        assert r.replay_prefix(prefix, 'reset', 'step', 'log') == ('current', 'cost')
    assert prefix == before
    assert replay.call_args.args[0]['binding'] == {'public_prefix_sha256': 'canonical-public-prefix-hash'}
    assert replay.call_args.args[1:] == ('reset', 'step', 'log')


if __name__ == "__main__":
    unittest.main()
