"""CPU contracts for the matched experience/history-window study."""
import copy
from contextlib import contextmanager
import importlib.util
import json
import hashlib
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
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

    def test_student_checkpoint_arms_share_exactly_one_goal_suffix_and_only_history_differs(self):
        reset, steps, current = prompt_inputs()
        prefix = dict(steps=steps, visible_steps=steps, checkpoint_reference={"CPU_SYNTHETIC": True},
                      checkpoint_source_kind="REAL_CLOSED_STUDENT8B_FAILURE")
        before = copy.deepcopy((reset, prefix, current))
        suffix = "\nCurrent task to finish (restated from the public reset): " + reset["observation"].split("Your task is to:", 1)[1].strip() + "\n"
        self.assertEqual(r.public_goal_restatement(reset), suffix)
        full = r.prefix_prompt(reset, prefix, current, EXPERIENCE, "drop_full")
        recent = r.prefix_prompt(reset, prefix, current, EXPERIENCE, "goal_recent")
        self.assertEqual(full, render(reset, steps, current, False, "full") + suffix)
        self.assertEqual(recent, render(reset, steps, current, False, "recent") + suffix)
        for text in (full, recent):
            self.assertTrue(text.endswith(suffix))
            self.assertEqual(text.count(suffix), 1)
            self.assertIn(reset["observation"], text)
            self.assertIn({key: current[key] for key in PUBLIC_KEYS}, list(json_objects(text)))
            for absent in ("REAL_CLOSED_STUDENT8B_FAILURE", "SOURCE_EXPERIENCE_BEGIN", "NEVER_RENDER"):
                self.assertNotIn(absent, text)
        fa, fb = history_range(full); ra, rb = history_range(recent)
        self.assertEqual(len(json.loads(full[fa:fb])), 6)
        self.assertEqual(len(json.loads(recent[ra:rb])), 3)
        self.assertEqual(full[:fa] + full[fb:], recent[:ra] + recent[rb:])
        self.assertEqual((reset, prefix, current), before)

    def test_other_checkpoint_full_prompts_and_legacy_goal_recent_are_byte_identical(self):
        reset, steps, current = prompt_inputs()
        suffix = "\nCurrent task to finish (restated from the public reset): " + reset["observation"].split("Your task is to:", 1)[1].strip() + "\n"
        for kind in (None, "REAL_CLOSED_ACTOR_FAILURE", "D_CONSTRUCTED_MATCHED_CONTROL"):
            prefix = dict(steps=steps, visible_steps=steps, checkpoint_reference={"CPU_SYNTHETIC": True})
            if kind is not None: prefix["checkpoint_source_kind"] = kind
            with self.subTest(kind=kind):
                self.assertEqual(r.prefix_prompt(reset, prefix, current, "", "drop_full").encode(),
                                 render(reset, steps, current, False, "full").encode())
                self.assertEqual(r.prefix_prompt(reset, prefix, current, "", "goal_recent").encode(),
                                 (render(reset, steps, current, False, "recent") + suffix).encode())
        legacy = dict(steps=steps)
        self.assertEqual(r.prefix_prompt(reset, legacy, current, "", "drop_full"),
                         render(reset, steps, current, False, "full"))

    def test_student_full_restatement_uses_only_an_unambiguous_public_reset_goal(self):
        reset, steps, current = prompt_inputs()
        prefix = dict(steps=steps, visible_steps=steps, checkpoint_reference={"CPU_SYNTHETIC": True},
                      checkpoint_source_kind="REAL_CLOSED_STUDENT8B_FAILURE")
        for observation in ("No explicit public goal.", "Your task is to:",
                            "Your task is to: clean an object.\nExtra instruction.",
                            "Your task is to: clean an object. Your task is to: heat another."):
            state = dict(reset, observation=observation)
            with self.subTest(observation=observation), self.assertRaises(ValueError):
                r.prefix_prompt(state, prefix, current, "", "drop_full")
            # The older full-history contract never acquired this new validation requirement.
            old = dict(prefix, checkpoint_source_kind="REAL_CLOSED_ACTOR_FAILURE")
            self.assertEqual(r.prefix_prompt(state, old, current, "", "drop_full"),
                             r.render_prompt(state, steps, current, "", False, "full"))

    def test_student_checkpoint_prepare_verify_render_the_same_suffix_in_both_policies(self):
        # Existing fixture replaces only external world/model/runtime surfaces; real rendering/verify run.
        fixture = r.module(ROOT / "tests/test_alfworld_checkpoint_source.py", "student_goal_checkpoint_fixture")
        with fixture.v2_fixture("REAL_CLOSED_STUDENT8B_FAILURE", 8, 8, 1, checkpoint_attempts={"a": 3}) as f:
            texts = {}; manifests = {}
            for stage in ("drop_full", "goal_recent"):
                root = f.root(stage, "a"); manifests[stage] = fixture.prepare(f, stage, "a")
                _, _, _, prefix, _ = r.verify(root, r.sha(root / "manifest.json"))
                texts[stage] = (root / "task.txt").read_text()
            goal = prefix["reset"]["observation"].split("Your task is to:", 1)[1].strip()
            suffix = "\nCurrent task to finish (restated from the public reset): " + goal + "\n"
            for text in texts.values():
                self.assertTrue(text.endswith(suffix)); self.assertEqual(text.count(suffix), 1)
                self.assertIn(prefix["reset"]["observation"], text)
                self.assertIn(prefix["current"]["observation"], text)
            fa, fb = history_range(texts["drop_full"]); ra, rb = history_range(texts["goal_recent"])
            self.assertEqual(len(json.loads(texts["drop_full"][fa:fb])), 8)
            self.assertEqual(len(json.loads(texts["goal_recent"][ra:rb])), 3)
            self.assertEqual(texts["drop_full"][:fa] + texts["drop_full"][fb:],
                             texts["goal_recent"][:ra] + texts["goal_recent"][rb:])
            root = f.root("drop_full", "a"); (root / "task.txt").write_text(texts["drop_full"][:-len(suffix)])
            rebound = copy.deepcopy(manifests["drop_full"]); rebound["inputs_sha256"]["task.txt"] = r.sha(root / "task.txt")
            fixture.write(root / "manifest.json", rebound)
            with self.assertRaisesRegex(ValueError, "prompt or source carrier changed"):
                r.verify(root, r.sha(root / "manifest.json"))

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
                choices = [None, {'native_terminal_stop':True,'recent_tool_rounds':None},
                           {'native_terminal_stop':True,'recent_tool_rounds':3}]
                for index,(backend,controls) in enumerate([(b,c) for b in ("student8b", "teacher27b") for c in choices],1):
                    with self.subTest(backend=backend,controls=controls):
                        study.pop('runtime_controls',None)
                        if controls is not None:study['runtime_controls']=controls
                        root = qual / ("context_study_v1/cases/heat_2/ordinary_reset/" + backend + "/attempt_v"+str(index))
                        manifest = r.prepare(root, qual / "mock-protocol.json", "a" * 64)
                        verified = r.verify(root, r.sha(root / "manifest.json"))
                        if controls is None:self.assertNotIn('runtime_controls',manifest)
                        else:self.assertEqual(manifest['runtime_controls'],controls)
                        forged = copy.deepcopy(manifest)
                        if controls is None:forged['runtime_controls']=choices[-1]
                        else:forged.pop('runtime_controls')
                        (root/'manifest.json').write_text(json.dumps(forged),encoding='utf8')
                        with self.assertRaisesRegex(ValueError,'runtime_controls'):
                            r.verify(root,r.sha(root/'manifest.json'))
                        (root/'manifest.json').write_text(json.dumps(manifest),encoding='utf8')
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
            self.assertNotIn('runtime_controls',receipt)
            self.assertNotIn('controller_stop',receipt)


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
                self.controller_stops, self.terminal_witness = [], None
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
            controls={'native_terminal_stop':True,'recent_tool_rounds':3}
            manifest['runtime_controls']=study['runtime_controls']=controls
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
            self.assertEqual(receipt['runtime_controls'],controls)
            self.assertIsNone(receipt['controller_stop'])
            self.assertEqual(receipt['controller_stops'],[])
            self.assertEqual(json.loads((root/'reservation.json').read_text())['runtime_controls'],controls)


    def test_top_level_raw_errors_block_retry_but_tool_feedback_does_not(self):
        """Mock every execution surface; exercise the actual two-round controller."""
        actual=r.recovery();guest=actual.actor().GUEST;bridge=actual.bridge()
        sid='ses_ValidOriginal1'
        normal=[{'type':'step_finish','sessionID':sid}]
        tool_error=[{'type':'tool_use','sessionID':sid,'part':{'state':{'status':'error','error':'ordinary failed tool feedback'}}}]+normal
        unknown=normal+[{'type':'error','sessionID':sid,'error':{'name':'UnknownError','data':{'message':'CPU opaque error'}}}]
        api=normal+[{'type':'error','sessionID':sid,'error':{'name':'APIError','data':{'statusCode':403,'message':'Forbidden'}}}]
        scenarios=[(unknown,0,False,1),(normal,0,False,2),(tool_error,0,False,2),
                   (normal,0,True,1),(normal,1,False,1),(normal,137,False,1),(api,0,False,1)]
        class Relay:
            def __init__(self,*a,**k):
                self.budget=SimpleNamespace(posts=0,request_bytes=0,response_bytes=0)
                self.forwarded=0;self.errors=[];self.delivery=None;self.controller_stops=[];self.terminal_witness=None
            def begin_close(self):pass
            def close(self):pass
        def write(path,value):
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x') as f:json.dump(value,f)
        for rows,code,terminal,expected in scenarios:
            with self.subTest(raw_type=rows[-1]['type'],exit=code,terminal=terminal),tempfile.TemporaryDirectory() as tmp:
                qual=Path(tmp).resolve();root=qual/'context_study_v1/cases/CPU_CASE/collect_none/student8b/attempt_v1';root.mkdir(parents=True)
                reset=public_state(0,'Your task is to: clean an object.');final=dict(public_state(1,'CPU public progress'),done=terminal)
                write(root/'initial_reset.json',reset);write(root/'handoff_public.json',reset);write(root/'opencode_config.json',{})
                (root/'task.txt').write_text('CPU frozen task');launches=[]
                m=dict(case_id='CPU_CASE',stage='collect_none',backend='student8b',world_seed=17,model_seed=17,
                    caps=dict(posts=20,seconds=120,world_actions=100,model_payload_bytes_combined=10000),sampling={},source_binding=None)
                study=dict(pool_path='CPU_POOL',pool_sha256='CPU_SHA');profile=dict(host='CPU_NOT_CONNECTED',port=1)
                core=SimpleNamespace(GUEST=guest,ModelRelay=Relay,write_new=write,socket_directory=lambda *_:qual/'CPU_MODEL',
                    docker_command=lambda *_:['CPU_ACTOR'],stop_world=mock.Mock(),cleanup_directory=mock.Mock())
                pool=SimpleNamespace(start_world=mock.Mock(return_value=((object(),qual/'CPU_WORLD'),reset,{})))
                def process(argv,**kw):
                    if argv==['CPU_ACTOR']:
                        launches.append(argv);kw['stdout'].write((''.join(json.dumps(z)+'\n' for z in rows)).encode())
                        return subprocess.CompletedProcess(argv,code)
                    self.assertEqual(argv[:3],['docker','rm','-f']);return subprocess.CompletedProcess(argv,0)
                with mock.patch.object(r,'QUAL',qual),mock.patch.object(r,'recovery',return_value=SimpleNamespace(actor=lambda:core,bridge=lambda:bridge)), \
                        mock.patch.object(r,'task_pool',return_value=pool),mock.patch.object(r,'verify',return_value=(m,study,profile,None,mock.Mock())), \
                        mock.patch.object(r,'final_state',return_value=final),mock.patch.object(r.subprocess,'run',side_effect=process), \
                        mock.patch('socket.create_connection',side_effect=AssertionError('no endpoint')):
                    result=r.run_episode(root,'CPU_FROZEN_SHA',fake_endpoint=('CPU_NOT_CONNECTED',1))
                self.assertEqual(len(launches),expected)
                self.assertEqual((root/'ordinary_continuation.json').exists(),expected==2)
                self.assertEqual(r.session_id(root/'raw_1.jsonl'),sid)
                if rows[-1]['type']=='error':
                    self.assertEqual(result['rounds'][0]['raw_top_level_error_count'],1)
                    self.assertEqual((root/'raw_1.jsonl').read_text(),''.join(json.dumps(z)+'\n' for z in rows))
                else:self.assertNotIn('raw_top_level_error_count',result['rounds'][0])


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



class AdditionalRecoveryStudyTests(unittest.TestCase):
    """Synthetic closed sources plus fake preflight; no world, model or Docker."""
    def setUp(self):
        fixture = r.module(ROOT/'tests/test_alfworld_recovery_source.py', 'study_additional_source_fixture')
        self.helper = fixture.m
        self.f = fixture.SourceTests('runTest'); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.f.root = self.f.base/'context_study_v1/cases'/self.f.case/'ordinary_reset/student8b/attempt_v2'
        self.f.root.mkdir(parents=True)
        self.f.receipt.update(elapsed_seconds=1800, model_request_payload_bytes=64000000, model_response_wire_bytes=0)
        for event in self.f.events:
            if 'state' in event: event['state']['private_pddl'] = 'NEVER_RENDER_PRIVATE_SOURCE'
        self.f.save()
        self.study = dict(total_caps=self.f.manifest['caps'].copy(),
            collection_caps=dict(posts=32, seconds=600, world_actions=100, model_payload_bytes_combined=64000000),
            intended_stage='preserved_recovery', world_seed=17, case_ids=[self.f.case],
            pool_path='CPU_ONLY_POOL', pool_sha256='CPU_ONLY_POOL_SHA', recent_steps=3,
            ordinary_continuations=1, context_margin_tokens=512,
            additional_recovery_source=dict(path=str(self.f.new), sha256=r.sha(self.f.new)))
        self.enterContext(mock.patch.object(r, 'QUAL', self.f.base))

    def source_refreshed(self):
        self.f.save(); self.study['additional_recovery_source']['sha256'] = r.sha(self.f.new)

    def tagged_prefix(self):
        return dict(self.f.load(), additional_recovery_source=self.study['additional_recovery_source'].copy(),
            source_loader_sha256=r.sha(r.HERE/'alfworld_recovery_source.py'))

    @contextmanager
    def loader(self):
        with mock.patch.object(r, 'additional_source_helper', return_value=self.helper): yield

    @contextmanager
    def prepared(self):
        validator = r.recovery().bridge().validate_response
        binary = self.f.base/'CPU_BINARY'; binary.write_bytes(b'FAKE_NOT_EXECUTABLE')
        def write_new(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x') as f: json.dump(value, f)
        profile = {'model_id': 'CPU_MODEL'}
        core = SimpleNamespace(write_new=write_new, config=lambda *a: {'CPU_CONFIG': True},
            model_payload=lambda *a: {'CPU_SAMPLING': True}, PROFILE_PINS={'student8b': ('CPU_PROFILE','CPU_SHA')},
            dependencies=SimpleNamespace(verify_projection=mock.Mock()), RUNTIME_ROOT='CPU_RUNTIME', RUNTIME_SHA='CPU_RUNTIME_SHA',
            BINARY=binary, BINARY_SHA=r.sha(binary), IMAGE='CPU_IMAGE', stop_world=mock.Mock())
        rec = SimpleNamespace(actor=lambda: core, bridge=lambda: SimpleNamespace(validate_response=validator))
        pool = SimpleNamespace(start_world=mock.Mock(return_value=((object(), self.f.base/'CPU_WORLD'), self.f.state(0), {})))
        from contextlib import ExitStack
        with ExitStack() as stack:
            for patcher in (mock.patch.object(r,'additional_source_helper',return_value=self.helper),
                mock.patch.object(r,'recovery',return_value=rec), mock.patch.object(r,'protocol',return_value=self.study),
                mock.patch.object(r,'load_study_profile',return_value=(profile,None)),
                mock.patch.object(r,'read_case',return_value=({}, {}, {}, 'NEVER_INJECT_ASSIGNED_CARRIER')),
                mock.patch.object(r,'components',return_value={'CPU_STUDY':'fixed','CPU_SOURCE_HELPER':r.sha(r.HERE/'alfworld_recovery_source.py')}),
                mock.patch.object(r,'study_token_qualifier',return_value=({'CPU_TOKENIZER':'fixed'},mock.Mock())),
                mock.patch.object(r,'task_pool',return_value=pool), mock.patch.object(r,'replay_prefix',return_value=(self.f.state(2),{})),
                mock.patch.object(r.subprocess,'check_output',return_value='CPU_IMAGE_ID\n'),
                mock.patch.object(r.subprocess,'run',side_effect=AssertionError('CPU test cannot run a container'))):
                stack.enter_context(patcher)
            yield pool

    def root(self, stage='drop_full', attempt=1, backend='student8b'):
        return self.f.root.parents[2]/stage/backend/('attempt_v'+str(attempt))

    def test_exhausted_old_total_still_has_only_the_independent_new_phase(self):
        prefix = self.tagged_prefix(); before = copy.deepcopy(prefix)
        with self.assertRaises(ValueError): r.remaining_caps(self.study['total_caps'], prefix['receipt'])
        self.assertEqual(r.stage_caps('drop_full', self.study, prefix), dict(posts=32,seconds=600,
            world_actions=98,model_payload_bytes_combined=64000000))
        self.assertEqual(prefix, before)
        for stage in ('ordinary_reset','collect','drop_recent','keep_recent','goal_recent'):
            with self.subTest(stage=stage), self.assertRaises(ValueError): r.stage_caps(stage,self.study,prefix)
        for key,value in [('budget_semantics','OLD_REMAINING'),('additional_caps',dict(prefix['additional_caps'],posts=31))]:
            with self.subTest(key=key), self.assertRaises(ValueError): r.stage_caps('drop_full',self.study,dict(prefix,**{key:value}))

    def test_explicit_source_dispatch_preserves_helper_identity_and_rejects_wrong_root_case_or_license(self):
        with self.loader():
            prefix = r.load_source_prefix(self.study,self.f.case,self.f.root)
            self.assertEqual(prefix['manifest']['stage'],'ordinary_reset')
            self.assertEqual(prefix['receipt']['model_posts'],128)
            self.assertEqual(prefix['root'],self.f.root)
            self.assertEqual(prefix['additional_recovery_source'],self.study['additional_recovery_source'])
            for case,root in [(self.f.case,self.f.root.with_name('attempt_v3')),('other_case',self.f.root)]:
                with self.subTest(case=case,root=root), self.assertRaises(ValueError): r.load_source_prefix(self.study,case,root)
            missing = dict(self.study); missing.pop('additional_recovery_source')
            with self.assertRaises(ValueError): r.load_source_prefix(missing,self.f.case,self.f.root)
            for ref in [None,{},dict(self.study['additional_recovery_source'],sha256='0'*64),dict(self.study['additional_recovery_source'],extra=True)]:
                with self.subTest(ref=ref), self.assertRaises(ValueError):
                    r.load_source_prefix(dict(self.study,additional_recovery_source=ref),self.f.case,self.f.root)
            for change in [{'won':True},{'label':'OWNED_FAKE_NOT_SCIENTIFIC'},{'real_model_calls':0}]:
                saved=self.f.receipt.copy(); self.f.receipt.update(change); self.source_refreshed()
                with self.subTest(change=change),self.assertRaises(ValueError):r.load_source_prefix(self.study,self.f.case,self.f.root)
                self.f.receipt=saved
            self.source_refreshed(); self.f.protocol['allow_frozen_ordinary_reset_sources']=False; self.source_refreshed()
            with self.assertRaises(ValueError):r.load_source_prefix(self.study,self.f.case,self.f.root)

    def test_legacy_loader_and_cohort_are_not_relaxed_and_helper_bytes_are_bound(self):
        with mock.patch.object(r,'load_prefix',return_value='LEGACY') as legacy:
            self.assertEqual(r.load_source_prefix({},self.f.case,self.f.root),'LEGACY')
            legacy.assert_called_once_with(self.f.root,self.f.case)
        self.assertIn(str(r.HERE/'alfworld_recovery_source.py'),r.components())
        with mock.patch.object(r,'ADDITIONAL_SOURCE_SHA','0'*64),self.assertRaises(ValueError):r.additional_source_helper()
        with collector_fixture() as f:
            prefix=r.load_prefix(f.root,'heat_2')
            with self.assertRaisesRegex(ValueError,'different frozen study'):r.cohort_binding(f.root,prefix,'b'*64)

    def test_new_cohort_is_isolated_and_rejects_changed_prefix_or_new_protocol(self):
        prefix=self.tagged_prefix(); legacy=self.root().parents[2]/'RECOVERY_COHORT.json';legacy.write_bytes(b'KEEP_LEGACY_BYTES')
        validator=r.recovery().bridge().validate_response
        def write_new(path,value):
            with path.open('x') as f:json.dump(value,f)
        rec=SimpleNamespace(actor=lambda:SimpleNamespace(write_new=write_new),bridge=lambda:SimpleNamespace(validate_response=validator))
        with mock.patch.object(r,'recovery',return_value=rec):
            first=r.cohort_binding(self.root(),prefix,'a'*64,study=self.study)
            self.assertEqual(Path(first['path']).name,'ADDITIONAL_RECOVERY_COHORT.json')
            self.assertEqual(r.cohort_binding(self.root('keep_full'),prefix,'a'*64,study=self.study),first)
            raw=Path(first['path']).read_bytes()
            for changed,digest in [(dict(prefix,public_prefix_sha256='b'*64),'a'*64),
                (dict(prefix,root=self.f.root.with_name('attempt_v3')),'a'*64),(prefix,'b'*64)]:
                with self.subTest(digest=digest),self.assertRaises(ValueError):r.cohort_binding(self.root(),changed,digest,study=self.study)
                self.assertEqual(Path(first['path']).read_bytes(),raw)
        self.assertEqual(legacy.read_bytes(),b'KEEP_LEGACY_BYTES')

    def test_prepare_verify_full_prefix_reference_budget_and_rehashed_mutations(self):
        ref=self.f.base/'all7.txt';ref.write_bytes(b'CPU_SYNTHETIC_ALL7_PUBLIC_HISTORY\n')
        with self.prepared() as pool:
            drop=self.root();d=r.prepare(drop,'CPU_PROTOCOL','a'*64,source_root=self.f.root)
            keep=self.root('keep_full');k=r.prepare(keep,'CPU_PROTOCOL','a'*64,source_root=self.f.root,
                reference_context=ref,reference_context_sha=r.sha(ref))
            for root,m in [(drop,d),(keep,k)]:
                checked=r.verify(root,r.sha(root/'manifest.json'));self.assertEqual(checked[3]['root'],self.f.root)
                self.assertEqual(m['caps']['posts'],32);self.assertEqual(m['caps']['seconds'],600);self.assertEqual(m['caps']['world_actions'],98)
                self.assertEqual(m['additional_recovery_metadata']['budget_semantics'],'ADDITIONAL_PHASE_NOT_OLD_REMAINING_POSTS')
                self.assertEqual(m['additional_recovery_source'],self.study['additional_recovery_source'])
                text=(root/'task.txt').read_text();self.assertNotIn('NEVER_',text)
                lo,hi=history_range(text);history=json.loads(text[lo:hi]);self.assertEqual([x['state']['action_count'] for x in history],[1,2])
            self.assertEqual(d['cohort_binding'],k['cohort_binding'])
            self.assertEqual(pool.start_world.call_args.args[4]['world_actions'],100)
            self.assertEqual((keep/'task.txt').read_bytes(),r.render_prompt(self.f.state(0),self.f.load()['steps'],self.f.state(2),ref.read_text(),True,'full').encode())
            self.assertNotIn(ref.read_text(),(drop/'task.txt').read_text())
            for edit in ['caps','metadata','source_ref','cohort','reference']:
                bad=copy.deepcopy(k)
                if edit=='caps':bad['caps']['posts']=31
                elif edit=='metadata':bad['additional_recovery_metadata']['budget_semantics']='OLD_REMAINING'
                elif edit=='source_ref':bad['additional_recovery_source']['sha256']='0'*64
                elif edit=='cohort':bad['cohort_binding']['sha256']='0'*64
                else:bad['reference_context']['text_sha256']='0'*64
                (keep/'manifest.json').write_text(json.dumps(bad))
                with self.subTest(edit=edit),self.assertRaises(ValueError):r.verify(keep,r.sha(keep/'manifest.json'))
            (keep/'manifest.json').write_text(json.dumps(k))
            cohort=Path(k['cohort_binding']['path']);original_cohort=cohort.read_bytes()
            cohort.write_bytes(original_cohort+b'\n')
            with self.assertRaises(ValueError):r.verify(keep,r.sha(keep/'manifest.json'))
            cohort.unlink()
            with self.assertRaises(ValueError):r.verify(keep,r.sha(keep/'manifest.json'))
            self.assertFalse(cohort.exists());cohort.write_bytes(original_cohort)
            original_reference=ref.read_bytes();ref.write_bytes(original_reference+b'CHANGED_REFERENCE')
            with self.assertRaises(ValueError):r.verify(keep,r.sha(keep/'manifest.json'))
            ref.write_bytes(original_reference)
            current=dict(self.f.state(2),observation='FORGED_CURRENT');(keep/'handoff_public.json').write_text(json.dumps(current))
            (keep/'task.txt').write_text(r.render_prompt(self.f.state(0),self.f.load()['steps'],current,ref.read_text(),True,'full'))
            forged=copy.deepcopy(k)
            for name in ('handoff_public.json','task.txt'):forged['inputs_sha256'][name]=r.sha(keep/name)
            (keep/'manifest.json').write_text(json.dumps(forged))
            with self.assertRaises(ValueError):r.verify(keep,r.sha(keep/'manifest.json'))
            with self.assertRaises(ValueError):r.prepare(self.root('keep_full',2),'CPU_PROTOCOL','a'*64,source_root=self.f.root)
            with self.assertRaises(ValueError):r.prepare(self.root('drop_full',2),'CPU_PROTOCOL','a'*64,source_root=self.f.root,reference_context=ref,reference_context_sha=r.sha(ref))
            with self.assertRaises(ValueError):r.load_reference_context('keep_full','student8b',ref,r.sha(ref))
            with self.assertRaises(ValueError):r.load_reference_context('keep_full','teacher27b',ref,r.sha(ref),study=self.study)

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


def rolling_payload(rounds=5):
    messages = [{'role':'system','content':'SYSTEM_ANCHOR'},
                {'role':'developer','content':'DEVELOPER_ANCHOR'},
                {'role':'user','content':'FROZEN_GOAL 中文'}]
    for index in range(rounds):
        calls = [{'id':str(index)+suffix,'type':'function',
                  'function':{'name':'bash','arguments':json.dumps({'command':'look '+suffix})}}
                 for suffix in ('a','b')]
        messages += [{'role':'assistant','content':'batch '+str(index),'tool_calls':calls}]
        messages += [{'role':'tool','tool_call_id':call['id'],'content':'complete reply '+call['id']}
                     for call in reversed(calls)]
        if index == 0:
            messages += [{'role':'user','content':'LATER_USER_GOAL_ANCHOR'}]
    return {'messages':messages,'tools':[{'type':'function','function':{'name':'bash',
        'parameters':{'type':'object','properties':{'zeta':{'type':'string'},'alpha':{'type':'string'}}}}}],
        'temperature':99,'model':'UNTRUSTED','chat_template_kwargs':{'enable_thinking':True}}


@contextmanager
def owned_fake_relay(controls, qualifier=None, action_channel=None):
    """Real relay UDS and socketpairs only: no world, Docker or network endpoint."""
    core = r.recovery().actor()
    with tempfile.TemporaryDirectory(prefix='alf-fake-') as tmp:
        root = Path(tmp).resolve()
        directory = root/'m';directory.mkdir()
        (root/'task.txt').write_text('FROZEN_GOAL 中文',encoding='utf8')
        reset = public_state(0,'Your task is to: complete the actual goal.')
        (root/'initial_reset.json').write_text(json.dumps(reset),encoding='utf8')
        caps = {'posts':20,'seconds':60,'world_actions':100,'model_payload_bytes_combined':1_000_000}
        manifest = {'case_id':'fake_case','world_seed':17,'stage':'ordinary_reset','caps':caps,
                    'game':{'sha256_game':'fake-game-sha'},'pool_binding':{'sha256':'fake-pool-sha'}}
        study = {'context_margin_tokens':512}
        if controls is not None:
            manifest['runtime_controls'] = study['runtime_controls'] = controls
        if action_channel is not None:
            manifest['action_channel'] = study['action_channel'] = action_channel
        metadata = {'game_id':manifest['case_id'],'seed':17,'step_cap':100,
                    'bridge_sha256':core.BRIDGE_SHA,'asset_sha256':'fake-game-sha',
                    'pool_manifest_sha256':'fake-pool-sha','caps':caps}
        metadata['episode_sha256'] = hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest()
        metadata = dict(event='episode',**metadata) # PublicTrajectory wrapper, outside hash.
        rows = [metadata,{'event':'reset','state':reset}]
        def write_rows(value):
            (root/'execute_world.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in value),encoding='utf8')
        write_rows(rows)
        qualify = qualifier or mock.Mock(return_value={'template_input_tokens':12,'reserved_output_tokens':8192,'context':32768})
        profile = {'model_id':'OWNED_FAKE','context':32768,'output':8192}
        sampling = (r.expected_sampling(study,core,'student8b',profile,17) if action_channel is not None else
                    core.model_payload({},'student8b',profile,17,False))
        manifest['sampling'] = sampling
        if action_channel == 'required':
            manifest['relay_constructor_sampling'] = core.model_payload({},'student8b',profile,17,False)
        relay_type = r.study_relay(core,manifest,study,qualify)
        with mock.patch.object(core,'cleanup_directory'), mock.patch.object(core.socket,'create_connection',
                side_effect=AssertionError('real network forbidden')) as connect:
            relay = relay_type(root,directory,'student8b',profile,17,('OWNED_FAKE_NEVER_RESOLVE',0),caps,
                      sampling,student_enable_thinking=False)
            try:
                yield SimpleNamespace(root=root,core=core,relay=relay,rows=rows,write_rows=write_rows,
                                      manifest=manifest,study=study,qualify=qualify,connect=connect)
            finally:
                relay.close()


def fake_uds_request(relay,payload):
    body = json.dumps(payload,separators=(',',':')).encode()
    packet = (b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body)
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(3);client.connect(str(relay.directory/'s'));client.sendall(packet)
        reply = b''
        while True:
            part = client.recv(65536)
            if not part:break
            reply += part
    return reply


@contextmanager
def fake_upstream(f):
    """Capture an actual serialized packet using a CPU-only owned socketpair."""
    sender,peer = socket.socketpair()
    captured,errors = [],[]
    def receive():
        try:
            peer.settimeout(3);wire=b''
            while b'\r\n\r\n' not in wire:wire+=peer.recv(65536)
            head,body=wire.split(b'\r\n\r\n',1)
            length=int(next(line.split(b':',1)[1] for line in head.split(b'\r\n') if line.lower().startswith(b'content-length:')))
            while len(body)<length:body+=peer.recv(65536)
            captured.append((head,body))
            peer.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}')
        except Exception as exc:errors.append(exc)
        finally:peer.close()
    thread=threading.Thread(target=receive);thread.start()
    try:
        with mock.patch.object(f.core.socket,'create_connection',return_value=sender) as connect:
            yield captured,connect
    finally:
        sender.close();thread.join(timeout=4)
        assert not thread.is_alive()
        assert not errors,errors


class RuntimeControlsTests(unittest.TestCase):
    def test_protocol_controls_are_explicit_strict_and_manifest_bound(self):
        self.assertEqual(r.runtime_controls({}),{'native_terminal_stop':False,'recent_tool_rounds':None})
        valid = {'native_terminal_stop':True,'recent_tool_rounds':3}
        for bad in (None,{},[],dict(valid,unknown=True),dict(valid,native_terminal_stop=1),
                    dict(valid,recent_tool_rounds=True),dict(valid,recent_tool_rounds=3.0),
                    dict(valid,recent_tool_rounds=2),{'recent_tool_rounds':3}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):r.runtime_controls({'runtime_controls':bad})
        study={'runtime_controls':valid}
        self.assertEqual(r.verify_runtime_controls(study,study),valid)
        for manifest in ({},{'runtime_controls':dict(valid,native_terminal_stop=False)}):
            with self.subTest(manifest=manifest),self.assertRaises(ValueError):r.verify_runtime_controls(manifest,study)
        with self.assertRaises(ValueError):r.verify_runtime_controls(study,{})

    def test_rolling_projection_is_actual_wire_and_billed_bytes_with_ordered_anchors(self):
        controls={'native_terminal_stop':True,'recent_tool_rounds':3}
        incoming=rolling_payload();before=copy.deepcopy(incoming)
        with owned_fake_relay(controls) as f:
            with fake_upstream(f) as (captured,connect):
                self.assertTrue(fake_uds_request(f.relay,incoming).startswith(b'HTTP/1.1 200'))
            stored=json.loads((f.root/'requests/00001.json').read_text())
            wire=captured[0][1];payload=json.loads(wire)
            self.assertEqual(wire,(f.root/'requests/00001.body').read_bytes())
            self.assertEqual(wire,json.dumps(stored['forwarded'],separators=(',',':')).encode())
            self.assertEqual(f.relay.budget.request_bytes,len(wire))
            self.assertEqual((f.relay.budget.posts,f.relay.forwarded),(1,1))
            self.assertEqual(stored['incoming'],before)
            anchors=lambda x:[m for m in x['messages'] if m['role'] in {'system','developer','user'}]
            self.assertEqual(anchors(payload),anchors(incoming))
            self.assertEqual([m['content'] for m in payload['messages'] if m['role']=='tool'],
                ['complete reply '+str(i)+s for i in (2,3,4) for s in ('b','a')])
            self.assertEqual(payload['tools'],incoming['tools'])
            self.assertEqual(list(payload['tools'][0]['function']['parameters']['properties']),['zeta','alpha'])
            self.assertEqual(payload['temperature'],0.2)
            self.assertEqual(payload['chat_template_kwargs'],{'enable_thinking':False})
            projection=json.loads((f.root/'projections/00001.json').read_text())
            self.assertEqual((projection['original_round_count'],projection['kept_round_count']),(5,3))
            self.assertEqual(projection['serialized_body_sha256'],hashlib.sha256(wire).hexdigest())
            self.assertEqual(projection['serialized_body_bytes'],len(wire))
            self.assertEqual(projection['received_record_sha256'],r.sha(f.root/'observed_requests/00001.json'))
            self.assertEqual(f.qualify.call_args.args[0],payload)
            self.assertEqual(f.relay.errors,[]);connect.assert_called_once()
            # The same projection applies on later live turns, not only the handoff.
            with fake_upstream(f) as (later,_):fake_uds_request(f.relay,rolling_payload(6))
            self.assertEqual([m['content'] for m in json.loads(later[0][1])['messages'] if m['role']=='tool'],
                ['complete reply '+str(i)+s for i in (3,4,5) for s in ('b','a')])
            self.assertEqual(f.relay.budget.request_bytes,len(wire)+len(later[0][1]))
            self.assertEqual(f.relay.forwarded,2)
            self.assertEqual(json.loads((f.root/'projections/00002.json').read_text())['kept_round_count'],3)
        self.assertEqual(incoming,before)

    def test_absent_controls_keep_exact_identity_wire_and_legacy_order(self):
        with owned_fake_relay(None) as f:
            incoming=rolling_payload()
            with fake_upstream(f) as (captured,_):fake_uds_request(f.relay,incoming)
            expected=f.core.model_payload(incoming,'student8b',{'model_id':'OWNED_FAKE','output':8192},17,False)
            self.assertEqual(captured[0][1],json.dumps(expected,separators=(',',':')).encode())
            self.assertFalse((f.root/'projections').exists())
            self.assertFalse((f.root/'controller_stop.json').exists())
            self.assertFalse((f.root/'requests/00001.body').exists())
            self.assertEqual(f.relay.errors,[])

    def test_native_terminal_stop_and_repeats_have_zero_posts_before_projection_or_qualification(self):
        for won in (False,True):
            with self.subTest(won=won),owned_fake_relay({'native_terminal_stop':True,'recent_tool_rounds':3}) as f:
                terminal=dict(public_state(1,'REAL_NATIVE_TERMINAL'),done=True,won=won)
                f.write_rows(f.rows+[{'event':'step','action':'look','state':terminal}])
                # Invalid tool structure cannot preempt the native terminal controller.
                for _ in range(2):
                    self.assertTrue(fake_uds_request(f.relay,{'messages':[{'role':'tool'}]}).startswith(b'HTTP/1.1 400'))
                self.assertEqual((f.relay.budget.posts,f.relay.budget.request_bytes,f.relay.forwarded),(0,0,0))
                f.connect.assert_not_called();f.qualify.assert_not_called()
                self.assertEqual(f.relay.errors,[]);self.assertFalse(f.relay.budget.failed)
                self.assertEqual(len(f.relay.controller_stops),2)
                witness=json.loads((f.root/'controller_stop.json').read_text())
                self.assertEqual(witness['reason'],'native_won' if won else 'native_done_unwon')
                self.assertEqual(witness['state'],terminal)
                self.assertEqual(witness['sha256'],r.sha(f.root/'execute_world.jsonl'))
                self.assertFalse((f.root/'requests').exists())

    def test_nonterminal_native_state_overrides_model_success_text_then_terminal_blocks_next_post(self):
        with owned_fake_relay({'native_terminal_stop':True,'recent_tool_rounds':None}) as f:
            incoming=rolling_payload(0);incoming['messages'].append({'role':'assistant','content':'done=true won=true I succeeded'})
            with fake_upstream(f):self.assertTrue(fake_uds_request(f.relay,incoming).startswith(b'HTTP/1.1 200'))
            f.write_rows(f.rows+[{'event':'step','action':'look','state':dict(public_state(1,'native done'),done=True)}])
            self.assertTrue(fake_uds_request(f.relay,incoming).startswith(b'HTTP/1.1 400'))
            self.assertEqual((f.relay.forwarded,f.relay.budget.posts),(1,1))
            self.assertEqual(f.relay.terminal_witness['forwarded_posts_at_stop'],1)

    def test_terminal_created_during_token_qualification_is_rechecked_before_actual_send(self):
        with owned_fake_relay({'native_terminal_stop':True,'recent_tool_rounds':3}) as f:
            def qualify(payload):
                f.write_rows(f.rows+[{'event':'step','action':'look','state':dict(public_state(1,'won'),done=True,won=True)}])
                return {'template_input_tokens':12,'reserved_output_tokens':8192,'context':32768}
            f.qualify.side_effect=qualify
            sender,peer=socket.socketpair()
            try:
                with mock.patch.object(f.core.socket,'create_connection',return_value=sender):
                    self.assertTrue(fake_uds_request(f.relay,rolling_payload()).startswith(b'HTTP/1.1 400'))
                self.assertEqual(peer.recv(1),b'')
            finally:sender.close();peer.close()
            self.assertEqual(f.relay.forwarded,0)
            self.assertEqual(f.relay.budget.posts,1) # Reserved, explicitly never forwarded.
            self.assertEqual(f.relay.errors,[])

    def test_malformed_projection_and_native_state_fail_before_any_send(self):
        for mode in ('projection','truncated','missing','bad_json','duplicate_key','wrong_case','wrong_asset','error_event',
                     'noncontiguous','won_without_done','reset_mismatch','step_after_done','symlink'):
            with self.subTest(mode=mode),owned_fake_relay({'native_terminal_stop':True,'recent_tool_rounds':3}) as f:
                path=f.root/'execute_world.jsonl';incoming=rolling_payload()
                rows=copy.deepcopy(f.rows)
                if mode=='projection':incoming['messages'].append({'role':'tool','tool_call_id':'dangling'})
                elif mode=='truncated':path.write_bytes(path.read_bytes().rstrip(b'\n'))
                elif mode=='missing':path.unlink()
                elif mode=='bad_json':path.write_text('not-json\n')
                elif mode=='duplicate_key':path.write_bytes(path.read_bytes().replace(b'"won": false',b'"won": false, "won": true',1))
                elif mode in ('wrong_case','wrong_asset'):
                    rows[0]['game_id' if mode=='wrong_case' else 'asset_sha256']='wrong'
                    metadata=dict(rows[0]);metadata.pop('episode_sha256');metadata.pop('event')
                    rows[0]['episode_sha256']=hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest()
                    f.write_rows(rows)
                elif mode=='error_event':f.write_rows(rows+[{'event':'error','error':'environment_failure','action_count':1}])
                elif mode=='noncontiguous':f.write_rows(rows+[{'event':'step','action':'look','state':public_state(2,'bad count')}])
                elif mode=='won_without_done':f.write_rows(rows+[{'event':'step','action':'look','state':dict(public_state(1,'bad flags'),won=True)}])
                elif mode=='reset_mismatch':rows[1]['state']['observation']='FORGED_RESET';f.write_rows(rows)
                elif mode=='step_after_done':f.write_rows(rows+[
                    {'event':'step','action':'look','state':dict(public_state(1,'done'),done=True)},
                    {'event':'step','action':'look','state':public_state(2,'invalid future')}])
                elif mode=='symlink':target=f.root/'elsewhere';path.rename(target);path.symlink_to(target)
                self.assertTrue(fake_uds_request(f.relay,incoming).startswith(b'HTTP/1.1 403'))
                self.assertEqual((f.relay.budget.posts,f.relay.forwarded),(0,0))
                f.connect.assert_not_called();f.qualify.assert_not_called()
                self.assertTrue(f.relay.errors);self.assertFalse((f.root/'controller_stop.json').exists())

    def test_recorded_terminal_latch_cannot_be_overtaken_by_prepared_sender(self):
        with owned_fake_relay({'native_terminal_stop':True,'recent_tool_rounds':None}) as f:
            checked,resume,terminal_read=threading.Event(),threading.Event(),threading.Event()
            actual=r.native_world_witness;sent,errors=[],[]
            def witness(root,manifest):
                result=actual(root,manifest)
                if threading.current_thread().name=='fake-prepared-sender':
                    checked.set()
                    if not resume.wait(3):raise RuntimeError('test sender was not released')
                else:terminal_read.set()
                return result
            class FakeUpstream:
                def sendall(self,packet):sent.append((packet,f.relay.terminal_witness))
                def shutdown(self,*args):pass
                def close(self):pass
            upstream=FakeUpstream()
            def sender():
                try:f.relay.forward(upstream,b'OWNED_FAKE_PACKET',rolling_payload(0),1)
                except Exception as exc:errors.append(exc)
            def stopper():
                try:f.relay.check_native_terminal()
                except f.core.ControllerStop:pass
                except Exception as exc:errors.append(exc)
            with mock.patch.object(r,'native_world_witness',side_effect=witness):
                first=threading.Thread(target=sender,name='fake-prepared-sender');first.start()
                self.assertTrue(checked.wait(3))
                f.write_rows(f.rows+[{'event':'step','action':'look','state':dict(public_state(1,'done'),done=True)}])
                second=threading.Thread(target=stopper);second.start()
                try:
                    self.assertTrue(terminal_read.wait(3))
                    # Stopper has read terminal, but cannot record a stop while
                    # sender holds the final check+send lock.
                    self.assertIsNone(f.relay.terminal_witness)
                finally:
                    resume.set();first.join(3);second.join(3)
            self.assertFalse(first.is_alive());self.assertFalse(second.is_alive())
            self.assertEqual(errors,[]);self.assertEqual(sent,[(b'OWNED_FAKE_PACKET',None)])
            self.assertEqual(f.relay.terminal_witness['forwarded_posts_at_stop'],1)
            with self.assertRaises(f.core.ControllerStop):f.relay.forward(upstream,b'FORBIDDEN_LATER_PACKET')
            self.assertEqual(len(sent),1)


@contextmanager
def no_experience_fixture():
    """Engineering fixtures only: world/profile/image/tokenizer are CPU mocks."""
    from contextlib import ExitStack
    actual = r.recovery().actor()
    validator = r.recovery().bridge().validate_response
    with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
        qual = Path(tmp).resolve(); case = 'nexttrain_clean_01'
        pool_path = qual/'POOL.json'; pool_path.write_text(json.dumps({'games':[{'id':case,'expert_qualified':True}]}))
        protocol_path = qual/'PROTOCOL.json'
        study = dict(version=1,schema='ALFWORLD_NO_EXTERNAL_EXPERIENCE_SOURCE_V1',experience_mode='none',
            pool_path=str(pool_path),pool_sha256=r.sha(pool_path),case_ids=[case],world_seed=17,model_seeds=[17],
            recent_steps=3,ordinary_continuations=1,context_margin_tokens=512,
            collection_caps=dict(posts=96,seconds=900,world_actions=100,model_payload_bytes_combined=32000000),
            total_caps=dict(posts=128,seconds=1800,world_actions=100,model_payload_bytes_combined=64000000),
            runtime_controls=dict(native_terminal_stop=True,recent_tool_rounds=None))
        def save_protocol():
            protocol_path.write_text(json.dumps(study));return r.sha(protocol_path)
        save_protocol()
        def write(path,value):
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x') as f:json.dump(value,f)
        binary=qual/'CPU_BINARY';binary.write_bytes(b'CPU_NOT_EXECUTABLE')
        carrier=mock.Mock(side_effect=AssertionError('none must not open a carrier'))
        profile={'model_id':'CPU_FAKE'}
        core=SimpleNamespace(write_new=write,load_profile=lambda _:profile,episode_caps=actual.episode_caps,
            condition_prompt=actual.condition_prompt,experience_validator=carrier,
            config=lambda p,seed:{'CPU_MODEL':p['model_id'],'seed':seed},model_payload=lambda *a:{'CPU_SAMPLING':True},
            PROFILE_PINS={b:('CPU_PROFILE','CPU_SHA') for b in ('student8b','teacher27b')},
            dependencies=SimpleNamespace(verify_projection=mock.Mock()),RUNTIME_ROOT='CPU_RUNTIME',RUNTIME_SHA='CPU_SHA',
            BINARY=binary,BINARY_SHA=r.sha(binary),IMAGE='CPU_IMAGE',stop_world=mock.Mock())
        reset=public_state(0,'Your task is to: clean an object. CPU_PUBLIC_GOAL')
        game={'game_path':'CPU_GAME','sha256_game':'CPU_GAME_SHA'}
        def select(path,digest,ident):
            if str(path)!=str(pool_path) or r.sha(pool_path)!=digest or ident!=case:raise ValueError('CPU pool binding mismatch')
            return game,{'path':str(pool_path),'sha256':digest}
        pool=SimpleNamespace(select_game=mock.Mock(side_effect=select),
            start_world=mock.Mock(return_value=((object(),qual/'CPU_WORLD'),reset,game)))
        rec=SimpleNamespace(actor=lambda:core,bridge=lambda:SimpleNamespace(validate_response=validator))
        for patcher in [mock.patch.object(r,'QUAL',qual),mock.patch.object(r,'recovery',return_value=rec),
                mock.patch.object(r,'task_pool',return_value=pool),mock.patch.object(r,'components',return_value={'CPU_ENGINEERING':'fixed'}),
                mock.patch.object(r,'study_token_qualifier',return_value=({'CPU_TOKENIZER':'fixed'},mock.Mock())),
                mock.patch.object(r.subprocess,'check_output',return_value='CPU_IMAGE_ID\n'),
                mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no real containers or worlds')),
                mock.patch('socket.create_connection',side_effect=AssertionError('no backend'))]:stack.enter_context(patcher)
        yield SimpleNamespace(qual=qual,case=case,study=study,protocol=protocol_path,save_protocol=save_protocol,
            pool_path=pool_path,pool=pool,core=core,carrier=carrier,reset=reset,
            root=lambda stage='collect_none',backend='student8b',attempt=1:qual/'context_study_v1/cases'/case/stage/backend/('attempt_v'+str(attempt)))


class NoExternalExperienceTests(unittest.TestCase):
    def test_none_reads_qualified_pool_without_touching_carrier_and_legacy_stays_strict(self):
        with no_experience_fixture() as f:
            game,binding,assignment,text=r.read_case(f.study,f.case)
            self.assertEqual((assignment,text),({},''));f.carrier.assert_not_called()
            f.pool.select_game.assert_called_once_with(str(f.pool_path),f.study['pool_sha256'],f.case)
            legacy=dict(f.study);legacy.pop('experience_mode')
            with self.assertRaises(KeyError):r.read_case(legacy,f.case)

    def test_unknown_mode_external_refs_and_assigned_row_fail_before_carrier(self):
        with no_experience_fixture() as f:
            for mode in [None,False,'legacy','external',{},[]]:
                with self.subTest(mode=mode),self.assertRaises(ValueError):r.read_case(dict(f.study,experience_mode=mode),f.case)
            for key in ['experience_assignment','experience_manifest','reference_context','additional_recovery_source']:
                with self.subTest(key=key),self.assertRaises(ValueError):r.read_case(dict(f.study,**{key:{}}),f.case)
            for assignment in [None,{},dict(carrier='ordinary_public_history',manifest_path='NEVER_READ')]:
                f.pool_path.write_text(json.dumps({'games':[{'id':f.case,'experience_assignment':assignment}]}));f.study['pool_sha256']=r.sha(f.pool_path)
                with self.subTest(assignment=assignment),self.assertRaises(ValueError):r.read_case(f.study,f.case)
            f.carrier.assert_not_called()

    def test_none_refuses_keep_collect_and_reference_context_without_reading_it(self):
        with no_experience_fixture() as f:
            for stage in ['collect','keep_full','keep_recent']:
                with self.subTest(stage=stage),self.assertRaises(ValueError):r.prepare(f.root(stage),f.protocol,f.save_protocol())
            f.pool.start_world.assert_not_called();f.carrier.assert_not_called()
            with self.assertRaises(ValueError):r.load_reference_context('ordinary_reset','student8b',f.qual/'NEVER_READ','a'*64,study=f.study)

    def test_none_episode_records_mode_even_when_mock_world_cannot_start(self):
        with no_experience_fixture() as f:
            root=f.root();m=r.prepare(root,f.protocol,f.save_protocol());digest=r.sha(root/'manifest.json')
            f.pool.start_world.side_effect=subprocess.TimeoutExpired('CPU_FAKE_WORLD',1)
            with mock.patch.object(r,'study_relay',return_value=object):result=r.run_episode(root,digest)
            self.assertEqual(result['status'],'COLLECTION_TIMEOUT')
            self.assertEqual(result['experience_mode'],'none')
            self.assertEqual(json.loads((root/'reservation.json').read_text())['experience_mode'],'none')
            self.assertEqual(result['real_model_calls'],0);f.carrier.assert_not_called()

    def test_prepare_verify_both_backends_and_rehashed_manifest_cannot_import_experience(self):
        with no_experience_fixture() as f:
            for backend in ['student8b','teacher27b']:
                root=f.root(backend=backend);m=r.prepare(root,f.protocol,f.save_protocol());r.verify(root,r.sha(root/'manifest.json'))
                self.assertEqual(m['experience_mode'],'none');self.assertEqual(m['experience_assignment'],{})
                self.assertEqual(m['experience_text_sha256'],hashlib.sha256(b'').hexdigest())
                self.assertEqual((root/'task.txt').read_bytes(),f.core.condition_prompt(f.reset,'none').encode())
                for field,value in [('experience_mode',None),('experience_assignment',{'carrier':'ordinary_public_history'}),
                        ('experience_text_sha256','a'*64),('reference_context',{'path':'NEVER_READ','sha256':'a'*64})]:
                    bad=copy.deepcopy(m)
                    if value is None:bad.pop(field)
                    else:bad[field]=value
                    (root/'manifest.json').write_text(json.dumps(bad))
                    with self.subTest(backend=backend,field=field),self.assertRaises(ValueError):r.verify(root,r.sha(root/'manifest.json'))
                (root/'manifest.json').write_text(json.dumps(m))
                (root/'task.txt').write_text('INJECTED_EXPERT_REFERENCE');bad=copy.deepcopy(m);bad['inputs_sha256']['task.txt']=r.sha(root/'task.txt')
                (root/'manifest.json').write_text(json.dumps(bad))
                with self.assertRaises(ValueError):r.verify(root,r.sha(root/'manifest.json'))
            f.carrier.assert_not_called()

    def make_prefix(self,f):
        root=f.root();m=r.prepare(root,f.protocol,f.save_protocol());digest=r.sha(root/'manifest.json')
        final=public_state(1,'CPU_ACTUAL_UNFINISHED_STATE')
        (root/'execute_world.jsonl').write_text(json.dumps({'event':'reset','state':f.reset})+'\n'+json.dumps({'event':'step','action':'look','state':final})+'\n')
        receipt=dict(label='MULTITASK_CONTEXT_DEVELOPMENT',status='RETURNED',manifest_sha256=digest,experience_mode='none',
            real_model_calls=1,forwarded_model_posts=1,model_posts=1,won=False,unknown_usage_model_posts=0,
            final_world_state=final,world_actions=1,elapsed_seconds=2.5,model_request_payload_bytes=123,model_response_wire_bytes=456,
            response_receipts=[{'complete':True,'usage':{'prompt_tokens':10,'completion_tokens':2,'total_tokens':12}}])
        reservation=dict(mode='REAL_DEVELOPMENT',manifest_sha256=digest,experience_mode='none')
        for name,value in [('receipt.json',receipt),('reservation.json',reservation)]: (root/name).write_text(json.dumps(value))
        return root,m,receipt,reservation

    def test_new_collect_none_prefix_has_real_calls_no_carrier_and_remaining_world_actions(self):
        with no_experience_fixture() as f:
            root,_,receipt,_=self.make_prefix(f);prefix=r.load_source_prefix(f.study,f.case,root)
            self.assertEqual(prefix['manifest']['stage'],'collect_none');self.assertEqual(len(prefix['steps']),1)
            self.assertEqual(r.stage_caps('drop_full',f.study,prefix),dict(posts=127,seconds=1797,world_actions=99,model_payload_bytes_combined=63999421))
            for stage in ['drop_full','drop_recent','goal_recent']:self.assertEqual(r.stage_caps(stage,f.study,prefix)['world_actions'],99)
            with self.assertRaises(ValueError):r.load_prefix(root,f.case)
            with self.assertRaises(ValueError):r.load_source_prefix(dict(f.study,pool_sha256='b'*64),f.case,root)
            f.carrier.assert_not_called()

    def test_new_prefix_rejects_missing_usage_false_origin_and_successful_terminal_states(self):
        with no_experience_fixture() as f:
            root,m,receipt,reservation=self.make_prefix(f)
            for change in [dict(real_model_calls=0),dict(unknown_usage_model_posts=1),dict(response_receipts=[]),
                    dict(response_receipts=[{'complete':True,'usage':None}]),dict(response_receipts=[None]),dict(model_posts=2),dict(won=True),
                    dict(experience_mode='external'),dict(final_world_state=dict(receipt['final_world_state'],done=True))]:
                (root/'receipt.json').write_text(json.dumps(dict(receipt,**change)))
                with self.subTest(change=change),self.assertRaises(ValueError):r.load_source_prefix(f.study,f.case,root)
            (root/'receipt.json').write_text(json.dumps(receipt));bad=copy.deepcopy(m);bad['backend']='teacher27b'
            (root/'manifest.json').write_text(json.dumps(bad));d=r.sha(root/'manifest.json')
            (root/'receipt.json').write_text(json.dumps(dict(receipt,manifest_sha256=d)))
            (root/'reservation.json').write_text(json.dumps(dict(reservation,manifest_sha256=d)))
            with self.assertRaises(ValueError):r.load_source_prefix(f.study,f.case,root)

    def test_new_source_manifest_rebinding_or_exhausted_world_does_not_launder_a_prefix(self):
        with no_experience_fixture() as f:
            root,m,receipt,reservation=self.make_prefix(f)
            for change in [dict(source_root=str(root)),dict(experience_assignment={'carrier':'ordinary_public_history'}),
                    dict(caps=dict(m['caps'],posts=95))]:
                bad=dict(m,**change);(root/'manifest.json').write_text(json.dumps(bad));digest=r.sha(root/'manifest.json')
                (root/'receipt.json').write_text(json.dumps(dict(receipt,manifest_sha256=digest)))
                (root/'reservation.json').write_text(json.dumps(dict(reservation,manifest_sha256=digest)))
                with self.subTest(change=change),self.assertRaises(ValueError):r.load_source_prefix(f.study,f.case,root)
            (root/'manifest.json').write_text(json.dumps(m));digest=r.sha(root/'manifest.json')
            final=public_state(100,'CPU_WORLD_BUDGET_EXHAUSTED')
            events=[{'event':'reset','state':f.reset}]+[{'event':'step','action':'look','state':public_state(i,'CPU_STEP')} for i in range(1,100)]+[{'event':'step','action':'look','state':final}]
            (root/'execute_world.jsonl').write_text(''.join(json.dumps(z)+'\n' for z in events))
            (root/'receipt.json').write_text(json.dumps(dict(receipt,manifest_sha256=digest,world_actions=100,final_world_state=final)))
            (root/'reservation.json').write_text(json.dumps(dict(reservation,manifest_sha256=digest)))
            with self.assertRaises(ValueError):r.load_source_prefix(f.study,f.case,root)


class ActionChannelTests(unittest.TestCase):
    """Engineering controls only; fake UDS traffic is not model evidence."""
    def test_expected_sampling_default_auto_and_required_keep_legacy_bytes(self):
        core=SimpleNamespace(model_payload=mock.Mock(side_effect=lambda *a:dict(model='CPU',seed=a[3],temperature=.2)))
        for backend in ['student8b','teacher27b']:
            legacy=core.model_payload({},backend,{},17,False if backend=='student8b' else None)
            for study in [{},{'action_channel':'auto'}]:
                self.assertEqual(json.dumps(r.expected_sampling(study,core,backend,{},17)),json.dumps(legacy))
            self.assertEqual(r.expected_sampling({'action_channel':'required'},core,backend,{},17),dict(legacy,tool_choice='required'))
        core.model_payload.assert_called_with({},'teacher27b',{},17,None)

    def test_unknown_channel_rejected_by_protocol_before_world(self):
        with no_experience_fixture() as f:
            for value in [None,False,0,'','none','REQUIRED',{},[]]:
                f.study['action_channel']=value
                with self.subTest(value=value),self.assertRaises(ValueError):r.protocol(f.protocol,f.save_protocol())
            f.pool.start_world.assert_not_called()

    def test_prepare_verify_bind_channel_and_sampling_even_with_rehashed_manifest(self):
        with no_experience_fixture() as f:
            for attempt,channel in enumerate([None,'auto','required'],1):
                if channel is None:f.study.pop('action_channel',None)
                else:f.study['action_channel']=channel
                root=f.root(attempt=attempt);m=r.prepare(root,f.protocol,f.save_protocol())
                r.verify(root,r.sha(root/'manifest.json'))
                self.assertEqual('action_channel' in m,channel is not None)
                self.assertEqual(m['sampling'],r.expected_sampling(f.study,f.core,'student8b',{},17))
                self.assertEqual('relay_constructor_sampling' in m,channel=='required')
                variants=[dict(m,action_channel='required' if channel!='required' else 'auto')]
                if channel is not None:
                    removed=copy.deepcopy(m);removed.pop('action_channel');variants.append(removed)
                wrong=copy.deepcopy(m);wrong['sampling']['tool_choice']='auto' if channel=='required' else 'required';variants.append(wrong)
                wrong=copy.deepcopy(m);wrong['relay_constructor_sampling']={'UNBOUND':True};variants.append(wrong)
                for bad in variants:
                    (root/'manifest.json').write_text(json.dumps(bad))
                    with self.subTest(channel=channel,bad=bad),self.assertRaises(ValueError):r.verify(root,r.sha(root/'manifest.json'))
                (root/'manifest.json').write_text(json.dumps(m))
                f.study['action_channel']='auto' if channel=='required' else 'required'
                rebound=copy.deepcopy(m);rebound['protocol_sha256']=f.save_protocol()
                (root/'manifest.json').write_text(json.dumps(rebound))
                with self.assertRaises(ValueError):r.verify(root,r.sha(root/'manifest.json'))

    def test_required_actual_wire_overrides_auto_before_byte_accounting(self):
        for controls in [None,dict(native_terminal_stop=True,recent_tool_rounds=None),
                         dict(native_terminal_stop=True,recent_tool_rounds=3)]:
            with self.subTest(controls=controls),owned_fake_relay(controls,action_channel='required') as f:
                incoming=rolling_payload();incoming['tool_choice']='auto';before=copy.deepcopy(incoming)
                with fake_upstream(f) as (captured,_):
                    self.assertTrue(fake_uds_request(f.relay,incoming).startswith(b'HTTP/1.1 200'))
                stored=json.loads((f.root/'requests/00001.json').read_text());wire=captured[0][1]
                self.assertEqual(json.loads((f.root/'observed_requests/00001.json').read_text()),before)
                self.assertEqual(stored['incoming'],before);self.assertEqual(stored['forwarded']['tool_choice'],'required')
                self.assertEqual(wire,(f.root/'requests/00001.body').read_bytes())
                self.assertEqual(wire,json.dumps(stored['forwarded'],separators=(',',':')).encode())
                self.assertEqual(f.relay.budget.request_bytes,len(wire));self.assertEqual(f.relay.forwarded,1)
                self.assertEqual(stored['forwarded']['tools'],before['tools']);self.assertEqual(incoming,before)
                self.assertEqual(f.qualify.call_args.args[0],stored['forwarded'])
                self.assertNotIn('tool_choice',f.manifest['relay_constructor_sampling'])

    def test_required_bytes_and_native_terminal_gate_prevent_actual_forward(self):
        controls=dict(native_terminal_stop=True,recent_tool_rounds=None)
        with owned_fake_relay(controls,action_channel='required') as f:
            incoming=rolling_payload();incoming['tool_choice']='auto'
            baseline=f.core.model_payload(incoming,'student8b',{'model_id':'OWNED_FAKE','output':8192},17,False)
            f.relay.budget.max_bytes=len(json.dumps(baseline,separators=(',',':')).encode())
            self.assertTrue(fake_uds_request(f.relay,incoming).startswith(b'HTTP/1.1 403'))
            self.assertEqual(f.qualify.call_args.args[0]['tool_choice'],'required')
            self.assertEqual((f.relay.forwarded,f.relay.budget.posts),(0,0));f.connect.assert_not_called()
        with owned_fake_relay(controls,action_channel='required') as f:
            f.write_rows(f.rows+[{'event':'step','action':'look','state':dict(public_state(1,'NATIVE_WON'),won=True,done=True)}])
            for _ in range(2):fake_uds_request(f.relay,rolling_payload())
            self.assertEqual((f.relay.forwarded,f.relay.budget.posts),(0,0));f.connect.assert_not_called();f.qualify.assert_not_called()

    def test_explicit_auto_keeps_legacy_forwarded_wire(self):
        with owned_fake_relay(None,action_channel='auto') as f:
            incoming=rolling_payload();incoming['tool_choice']='auto'
            with fake_upstream(f) as (captured,_):fake_uds_request(f.relay,incoming)
            expected=f.core.model_payload(incoming,'student8b',{'model_id':'OWNED_FAKE','output':8192},17,False)
            self.assertEqual(captured[0][1],json.dumps(expected,separators=(',',':')).encode())
            self.assertFalse((f.root/'requests/00001.body').exists())

    def test_relay_rejects_manifest_or_constructor_sampling_mismatch_before_start(self):
        started=mock.Mock(return_value=None);base=type('CPUModelRelay',(),{'__init__':started})
        core=SimpleNamespace(ModelRelay=base,model_payload=lambda *a:{'CPU_SAMPLING':True})
        study={'action_channel':'required'};sampling={'CPU_SAMPLING':True,'tool_choice':'required'}
        for manifest,supplied in [({'action_channel':'auto','sampling':sampling},sampling),
                ({'action_channel':'required','sampling':{'CPU_SAMPLING':True}},sampling),
                ({'action_channel':'required','sampling':sampling},{'CPU_SAMPLING':True}),
                ({'action_channel':'required','sampling':sampling,'relay_constructor_sampling':{'WRONG':True}},sampling)]:
            with self.subTest(manifest=manifest,supplied=supplied),self.assertRaises(ValueError):
                relay=r.study_relay(core,manifest,study,mock.Mock())
                relay(None,None,'student8b',{},17,None,{},supplied)
        started.assert_not_called()


if __name__ == '__main__':
    unittest.main()
