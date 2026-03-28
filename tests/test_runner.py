from __future__ import annotations

import builtins
import contextlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.models import AgentDefinition, Skill, SkillResources
from moltfarm import runner
from moltfarm.runner import OpenAIAgentsExecutor, StubAgentExecutor, run_workflow


class StubAgentExecutorTests(unittest.TestCase):
    def test_run_is_generic_and_reports_context_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            context_file = project_root / "runs" / "example.json"
            context_file.parent.mkdir(parents=True)
            context_file.write_text('{"status": "completed"}', encoding="utf-8")

            executor = StubAgentExecutor()
            result = executor.run(
                project_root=project_root,
                agent=AgentDefinition(
                    name="generic-worker",
                    description="",
                    model="gpt-5",
                    runtime="stub",
                    context_policy="least_context",
                ),
                skills=[
                    Skill(
                        name="custom-skill",
                        description="A generic custom skill.",
                        path=project_root / "skills" / "custom-skill",
                        instructions="Follow the instructions.",
                        referenced_paths=[Path("references/example.md")],
                        resources=SkillResources(references=[Path("references/example.md")]),
                    )
                ],
                task_input={
                    "task": "inspect the sample artifact",
                    "artifact_path": "runs/example.json",
                },
            )

            self.assertIn("custom-skill", result["summary"])
            self.assertIn("inspect the sample artifact", result["summary"])
            self.assertEqual(["runs/example.json"], result["context_files"])
            self.assertEqual([], result["context_directories"])
            self.assertEqual(
                {"custom-skill": ["references/example.md"]},
                result["skill_references"],
            )
            self.assertEqual(
                [{"name": "custom-skill", "description": "A generic custom skill."}],
                result["skill_catalog"],
            )
            self.assertFalse(result["compaction"]["input_compacted"])
            self.assertFalse(result["compaction"]["output_compacted"])

    def test_stub_executor_detects_plain_filename_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            root_file = project_root / "README.md"
            root_file.write_text("hello\n", encoding="utf-8")

            executor = StubAgentExecutor()
            result = executor.run(
                project_root=project_root,
                agent=AgentDefinition(
                    name="generic-worker",
                    description="",
                    model="gpt-5",
                    runtime="stub",
                    context_policy="least_context",
                ),
                skills=[],
                task_input={"source": "README.md"},
            )

            self.assertEqual(["README.md"], result["context_files"])


class OpenAIAgentsExecutorTests(unittest.TestCase):
    def test_run_uses_activation_tool_and_stubs_sdk_calls(self) -> None:
        calls: dict[str, object] = {}

        class FakeResult:
            def __init__(self, final_output):
                self.final_output = final_output

        class FakeRunner:
            @staticmethod
            def run_sync(agent, input):
                calls.setdefault("runner_calls", []).append((agent, input))
                if agent.kwargs["name"] == "workflow-compactor":
                    return FakeResult("Compacted content.")
                calls["runner_agent"] = agent
                calls["runner_input"] = input
                return FakeResult("Structured skill activation worked.")

        class FakeSDK:
            Runner = FakeRunner

            class Agent:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

            @staticmethod
            def set_tracing_disabled(value):
                calls["tracing_disabled"] = value

            @staticmethod
            def function_tool(fn):
                fn._is_tool = True
                return fn

        original_import = runner._import_openai_agents_sdk
        original_dotenv = runner._load_dotenv
        try:
            runner._import_openai_agents_sdk = lambda project_root: FakeSDK
            runner._load_dotenv = lambda project_root: None

            executor = OpenAIAgentsExecutor()
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                context_file = project_root / "runs" / "example.json"
                context_file.parent.mkdir(parents=True)
                context_file.write_text("{}", encoding="utf-8")
                skill_dir = project_root / "skills" / "run-summarizer"
                (skill_dir / "references").mkdir(parents=True)
                (skill_dir / "scripts").mkdir(parents=True)
                (skill_dir / "references" / "template.md").write_text(
                    "Template body.",
                    encoding="utf-8",
                )
                (skill_dir / "scripts" / "helper.py").write_text(
                    "print('helper')\n",
                    encoding="utf-8",
                )

                skill = Skill(
                    name="run-summarizer",
                    description="Summarize completed runs.",
                    path=skill_dir,
                    instructions="Use the summary template.",
                    referenced_paths=[Path("references/template.md")],
                    resources=SkillResources(
                        references=[Path("references/template.md")],
                        scripts=[Path("scripts/helper.py")],
                    ),
                )
                result = executor.run(
                    project_root=project_root,
                    agent=AgentDefinition(
                        name="triage-worker",
                        description="",
                        model="gpt-5",
                        runtime="openai_agents",
                        context_policy="least_context",
                    ),
                    skills=[skill],
                    task_input={
                        "task": "summarize the run",
                        "run_record_path": "runs/example.json",
                    },
                )

                fake_agent = calls["runner_agent"]
                instructions = fake_agent.kwargs["instructions"]
                self.assertIn("<available_skills>", instructions)
                self.assertIn("<name>run-summarizer</name>", instructions)
                self.assertNotIn("Use the summary template.", instructions)

                activation_tool = fake_agent.kwargs["tools"][0]
                activation_payload = activation_tool("run-summarizer")
                self.assertIn("<skill_content name=\"run-summarizer\">", activation_payload)
                self.assertIn("Skill directory:", activation_payload)
                self.assertIn('<file category="references">references/template.md</file>', activation_payload)
                self.assertIn('<file category="scripts">scripts/helper.py</file>', activation_payload)

                resource_tool = fake_agent.kwargs["tools"][1]
                resource_payload = resource_tool("run-summarizer", "references/template.md")
                self.assertIn('<skill_resource skill="run-summarizer" path="references/template.md">', resource_payload)
        finally:
            runner._import_openai_agents_sdk = original_import
            runner._load_dotenv = original_dotenv

        self.assertTrue(calls["tracing_disabled"])
        self.assertEqual("Structured skill activation worked.", result["summary"])
        self.assertEqual(["runs/example.json"], result["context_files"])
        self.assertEqual([], result["context_directories"])
        self.assertEqual(
            [{"name": "run-summarizer", "description": "Summarize completed runs."}],
            result["skill_catalog"],
        )
        self.assertIn("- run_record_path: runs/example.json", calls["runner_input"])
        self.assertIn('<context_file path="runs/example.json">', calls["runner_input"])
        self.assertFalse(result["compaction"]["input_compacted"])
        self.assertFalse(result["compaction"]["output_compacted"])

    def test_run_compacts_oversized_input_before_main_call(self) -> None:
        calls: dict[str, object] = {}

        class FakeResult:
            def __init__(self, final_output):
                self.final_output = final_output

        class FakeRunner:
            @staticmethod
            def run_sync(agent, input):
                calls.setdefault("runner_calls", []).append((agent, input))
                if agent.kwargs["name"] == "workflow-compactor":
                    return FakeResult("Compacted content.")
                return FakeResult("Main agent response.")

        class FakeSDK:
            Runner = FakeRunner

            class Agent:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

            @staticmethod
            def set_tracing_disabled(value):
                calls["tracing_disabled"] = value

            @staticmethod
            def function_tool(fn):
                return fn

        original_import = runner._import_openai_agents_sdk
        original_dotenv = runner._load_dotenv
        original_threshold = runner.COMPACTION_TOKEN_THRESHOLD
        try:
            runner._import_openai_agents_sdk = lambda project_root: FakeSDK
            runner._load_dotenv = lambda project_root: None
            runner.COMPACTION_TOKEN_THRESHOLD = 10

            executor = OpenAIAgentsExecutor()
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                context_file = project_root / "runs" / "large.txt"
                context_file.parent.mkdir(parents=True)
                context_file.write_text("x" * 1000, encoding="utf-8")

                result = executor.run(
                    project_root=project_root,
                    agent=AgentDefinition(
                        name="triage-worker",
                        description="",
                        model="gpt-5",
                        runtime="openai_agents",
                        context_policy="least_context",
                    ),
                    skills=[
                        Skill(
                            name="repo-triage",
                            description="Triage a repository.",
                            path=project_root / "skills" / "repo-triage",
                            instructions="Keep it short.",
                            resources=SkillResources(),
                        )
                    ],
                    task_input={"task": "triage", "context_path": "runs/large.txt"},
                )
        finally:
            runner._import_openai_agents_sdk = original_import
            runner._load_dotenv = original_dotenv
            runner.COMPACTION_TOKEN_THRESHOLD = original_threshold

        self.assertTrue(result["compaction"]["input_compacted"])
        self.assertEqual("Main agent response.", result["summary"])
        self.assertEqual(2, len(calls["runner_calls"]))
        compactor_input = calls["runner_calls"][0][1]
        main_input = calls["runner_calls"][1][1]
        self.assertIn("Compact this workflow input:", compactor_input)
        self.assertIn("<compacted_workflow_input>", main_input)
        self.assertIn("Compacted content.", main_input)

    def test_run_supports_openai_agents_without_attached_skills(self) -> None:
        calls: dict[str, object] = {}

        class FakeResult:
            def __init__(self, final_output):
                self.final_output = final_output
                self.raw_responses = []
                self.new_items = []

        class FakeRunner:
            @staticmethod
            def run_sync(agent, input):
                calls["runner_agent"] = agent
                calls["runner_input"] = input
                return FakeResult("Baseline output.")

        class FakeSDK:
            Runner = FakeRunner

            class Agent:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

            @staticmethod
            def set_tracing_disabled(value):
                calls["tracing_disabled"] = value

            @staticmethod
            def function_tool(fn):
                return fn

        original_import = runner._import_openai_agents_sdk
        original_dotenv = runner._load_dotenv
        try:
            runner._import_openai_agents_sdk = lambda project_root: FakeSDK
            runner._load_dotenv = lambda project_root: None

            executor = OpenAIAgentsExecutor()
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                result = executor.run(
                    project_root=project_root,
                    agent=AgentDefinition(
                        name="baseline-worker",
                        description="",
                        model="gpt-5",
                        runtime="openai_agents",
                        context_policy="least_context",
                    ),
                    skills=[],
                    task_input={"task": "do the task without skills"},
                )
        finally:
            runner._import_openai_agents_sdk = original_import
            runner._load_dotenv = original_dotenv

        self.assertEqual("Baseline output.", result["summary"])
        fake_agent = calls["runner_agent"]
        self.assertEqual([], fake_agent.kwargs["tools"])
        self.assertIn("No specialized skills are attached for this run.", fake_agent.kwargs["instructions"])

    def test_trace_summary_includes_activated_skill_name(self) -> None:
        class FakeRawItem:
            def __init__(self, item_type, **kwargs):
                self.type = item_type
                for key, value in kwargs.items():
                    setattr(self, key, value)

        class FakeItem:
            def __init__(self, item_type, raw_item):
                self.type = item_type
                self.raw_item = raw_item

        class FakeResult:
            def __init__(self):
                self.raw_responses = []
                self.new_items = [
                    FakeItem(
                        "tool_call_item",
                        FakeRawItem(
                            "function_call",
                            name="activate_skill",
                            arguments='{"name":"develop-web-game"}',
                        ),
                    )
                ]

        trace = runner._extract_trace_summary(FakeResult())
        self.assertEqual(
            [{"type": "tool_call_item", "summary": "function_call:activate_skill:develop-web-game"}],
            trace["items"],
        )


class RunnerHelperTests(unittest.TestCase):
    def test_run_loads_dotenv_compacts_output_and_records_directory_context(self) -> None:
        calls: dict[str, object] = {"dotenv": []}

        class FakeResult:
            def __init__(self, final_output, *, raw_responses=None, new_items=None):
                self.final_output = final_output
                self.raw_responses = raw_responses or []
                self.new_items = new_items or []

        class FakeRunner:
            @staticmethod
            def run_sync(agent, input):
                calls.setdefault("runner_calls", []).append((agent, input))
                if agent.kwargs["name"] == "workflow-compactor":
                    return FakeResult("Compressed output.")
                response_usage = SimpleNamespace(
                    requests=2,
                    input_tokens=30,
                    output_tokens=15,
                    total_tokens=45,
                    request_usage_entries=[
                        SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
                        SimpleNamespace(input_tokens=20, output_tokens=10, total_tokens=30),
                    ],
                )
                message_item = SimpleNamespace(
                    type="message",
                    content=[SimpleNamespace(text="hello"), SimpleNamespace(refusal="no")],
                )
                output_item = SimpleNamespace(type="function_call_output", call_id="call-1")
                return FakeResult(
                    "x" * 1000,
                    raw_responses=[
                        SimpleNamespace(
                            response_id="resp-1",
                            request_id="req-1",
                            usage=response_usage,
                        )
                    ],
                    new_items=[
                        SimpleNamespace(type="message_output_item", raw_item=message_item),
                        SimpleNamespace(type="tool_output_item", raw_item=output_item),
                    ],
                )

        class FakeSDK:
            Runner = FakeRunner

            class Agent:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

            @staticmethod
            def set_tracing_disabled(value):
                calls["tracing_disabled"] = value

            @staticmethod
            def function_tool(fn):
                return fn

        def fake_load_dotenv(path, override):
            calls["dotenv"].append((path, override))

        original_import = runner._import_openai_agents_sdk
        original_dotenv = runner._load_dotenv
        original_compact_input = runner._maybe_compact_input
        original_threshold = runner.COMPACTION_TOKEN_THRESHOLD
        try:
            runner._import_openai_agents_sdk = lambda project_root: FakeSDK
            runner._load_dotenv = lambda project_root: fake_load_dotenv
            runner._maybe_compact_input = lambda **kwargs: (
                kwargs["input_text"],
                {
                    "threshold_tokens": 50,
                    "input_tokens_estimate": 0,
                    "input_compacted": False,
                    "output_tokens_estimate": 0,
                    "output_compacted": False,
                },
            )
            runner.COMPACTION_TOKEN_THRESHOLD = 50

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                artifacts_dir = project_root / "artifacts"
                artifacts_dir.mkdir()
                (artifacts_dir / "report.txt").write_text("report\n", encoding="utf-8")

                result = OpenAIAgentsExecutor().run(
                    project_root=project_root,
                    agent=AgentDefinition(
                        name="triage-worker",
                        description="",
                        model="gpt-5",
                        runtime="openai_agents",
                        context_policy="least_context",
                    ),
                    skills=[],
                    task_input={"task": "inspect the directory", "artifact_dir": "artifacts"},
                )

                self.assertEqual([(project_root / ".env", False)], calls["dotenv"])
                self.assertEqual(["artifacts"], result["context_directories"])
                self.assertTrue(result["compaction"]["output_compacted"])
                self.assertEqual("Compressed output.", result["summary"])
                self.assertEqual(
                    {
                        "requests": 2,
                        "input_tokens": 30,
                        "output_tokens": 15,
                        "total_tokens": 45,
                        "request_usage_entries": [
                            {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                            {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
                        ],
                    },
                    result["metrics"]["usage"],
                )
                self.assertEqual(["resp-1"], result["trace"]["response_ids"])
                self.assertEqual(["req-1"], result["trace"]["request_ids"])
                self.assertEqual(
                    [
                        {"type": "message_output_item", "summary": "hello no"},
                        {"type": "tool_output_item", "summary": "function_call_output:call-1"},
                    ],
                    result["trace"]["items"],
                )
                self.assertEqual(2, len(calls["runner_calls"]))
                self.assertIn('<context_directory path="artifacts">', calls["runner_calls"][0][1])
        finally:
            runner._import_openai_agents_sdk = original_import
            runner._load_dotenv = original_dotenv
            runner._maybe_compact_input = original_compact_input
            runner.COMPACTION_TOKEN_THRESHOLD = original_threshold

    def test_build_executor_resolve_skills_and_target_skill_helpers(self) -> None:
        self.assertIsInstance(runner._build_executor("openai_agents"), OpenAIAgentsExecutor)
        self.assertIsInstance(runner._build_executor("stub"), StubAgentExecutor)

        skill = Skill(
            name="repo-triage",
            description="Triage a repository.",
            path=Path("/tmp/repo-triage"),
            instructions="Keep it short.",
        )
        agent = AgentDefinition(
            name="triage-worker",
            description="",
            model="gpt-5",
            runtime="stub",
            context_policy="least_context",
            skills=["repo-triage"],
        )
        self.assertEqual([skill], runner._resolve_skills(agent, {"repo-triage": skill}))

        missing_agent = AgentDefinition(
            name="triage-worker",
            description="",
            model="gpt-5",
            runtime="stub",
            context_policy="least_context",
            skills=["missing-skill"],
        )
        with self.assertRaises(ValueError):
            runner._resolve_skills(missing_agent, {})

        task_input = {"target_skill": "missing-skill"}
        runner._augment_task_input_with_local_skill_paths(
            task_input=task_input,
            project_root=Path("/tmp/project"),
            skills_by_name={},
        )
        self.assertEqual({"target_skill": "missing-skill"}, task_input)

    def test_default_path_helpers_respect_existing_values(self) -> None:
        task_input: dict[str, object] = {}
        runner._set_default_if_blank(task_input, "missing", None)
        self.assertNotIn("missing", task_input)

        task_input["kept"] = "already-set"
        runner._set_default_if_blank(task_input, "kept", "new-value")
        self.assertEqual("already-set", task_input["kept"])

        task_input["structured"] = ["do", "not", "touch"]
        runner._set_default_if_blank(task_input, "structured", "ignored")
        self.assertEqual(["do", "not", "touch"], task_input["structured"])

        task_input["blank"] = ""
        runner._set_default_if_blank(task_input, "blank", "filled")
        self.assertEqual("filled", task_input["blank"])

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            first = project_root / "runs" / "one.json"
            second = project_root / "runs" / "two.json"
            first.parent.mkdir(parents=True)
            first.write_text("{}", encoding="utf-8")
            second.write_text("{}", encoding="utf-8")

            self.assertIsNone(runner._relative_if_file(project_root, project_root / "missing.json"))
            self.assertEqual("runs/one.json", runner._relative_if_file(project_root, first))

            existing_value = {"comparison_path": "runs/already.json"}
            runner._set_default_path_series(
                task_input=existing_value,
                base_key="comparison_path",
                project_root=project_root,
                paths=[first, second],
            )
            self.assertEqual({"comparison_path": "runs/already.json"}, existing_value)

            existing_series = {"comparison_path_2": "runs/two.json"}
            runner._set_default_path_series(
                task_input=existing_series,
                base_key="comparison_path",
                project_root=project_root,
                paths=[first, second],
            )
            self.assertEqual({"comparison_path_2": "runs/two.json"}, existing_series)

            empty_series: dict[str, str] = {}
            runner._set_default_path_series(
                task_input=empty_series,
                base_key="comparison_path",
                project_root=project_root,
                paths=[project_root / "missing.json"],
            )
            self.assertEqual({}, empty_series)

            generated_series: dict[str, str] = {}
            runner._set_default_path_series(
                task_input=generated_series,
                base_key="comparison_path",
                project_root=project_root,
                paths=[first, second],
            )
            self.assertEqual(
                {
                    "comparison_path": "runs/one.json",
                    "comparison_path_2": "runs/two.json",
                },
                generated_series,
            )

    def test_build_sdk_input_truncates_files_and_directory_listing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            context_file = project_root / "runs" / "huge.txt"
            context_dir = project_root / "artifacts"
            context_file.parent.mkdir(parents=True)
            context_dir.mkdir()
            context_file.write_text("x" * 13_000, encoding="utf-8")
            for index in range(45):
                (context_dir / f"file-{index:02d}.txt").write_text("ok\n", encoding="utf-8")

            prompt = runner._build_sdk_input(
                project_root=project_root,
                task_input={"task": "inspect"},
                context_files=["runs/huge.txt"],
                context_directories=["artifacts"],
            )

        self.assertIn('<context_file path="runs/huge.txt">', prompt)
        self.assertIn('<context_directory path="artifacts">', prompt)
        self.assertIn("[truncated]", prompt)
        self.assertIn("file-00.txt", prompt)

    def test_build_skill_tools_and_function_call_helpers(self) -> None:
        class FakeSDK:
            @staticmethod
            def function_tool(fn):
                return fn

        with self.assertRaises(ValueError):
            runner._build_activate_skill_tool(FakeSDK, [])

        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "skills" / "run-summarizer"
            (skill_dir / "references").mkdir(parents=True)
            (skill_dir / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
            skill = Skill(
                name="1 weird-skill",
                description="Summarize runs.",
                path=skill_dir,
                instructions="Use local artifacts.",
                resources=SkillResources(references=[Path("references/guide.md")]),
            )

            read_skill_resource = runner._build_read_skill_resource_tool(FakeSDK, [skill])
            with self.assertRaises(ValueError):
                read_skill_resource("1 weird-skill", "references/missing.md")

        self.assertEqual(
            "function_call:read_skill_resource:sample-skill:guide.md",
            runner._summarize_function_call(
                name="read_skill_resource",
                arguments={"name": "sample-skill", "path": "guide.md"},
            ),
        )
        self.assertEqual(
            "function_call:other:{'foo': 'bar'}",
            runner._summarize_function_call(name="other", arguments='{"foo":"bar"}'),
        )
        self.assertEqual({"name": "sample-skill"}, runner._parse_function_call_arguments({"name": "sample-skill"}))
        self.assertEqual({}, runner._parse_function_call_arguments(""))
        self.assertEqual({}, runner._parse_function_call_arguments("not-json"))
        self.assertEqual({}, runner._parse_function_call_arguments("[]"))
        self.assertEqual("SKILL_1_WEIRD_SKILL", runner._sanitize_enum_member_name("1 weird-skill"))
        self.assertEqual("SKILL", runner._sanitize_enum_member_name("!!!"))
        self.assertEqual("123", runner._coerce_final_output(123))

    def test_prepare_compaction_source_and_trace_item_helpers(self) -> None:
        original_max_tokens = runner.COMPACTION_SOURCE_MAX_TOKENS
        try:
            runner.COMPACTION_SOURCE_MAX_TOKENS = 10
            sampled = runner._prepare_compaction_source("abcdefghij" * 20)
        finally:
            runner.COMPACTION_SOURCE_MAX_TOKENS = original_max_tokens

        self.assertIn('<window label="head">', sampled)
        self.assertIn('<window label="middle">', sampled)
        self.assertIn('<window label="tail">', sampled)

        self.assertEqual("", runner._summarize_trace_item(None))
        self.assertEqual(
            "dict message",
            runner._summarize_trace_item(
                {"type": "message", "content": [{"text": "dict"}, {"refusal": "message"}]}
            ),
        )
        self.assertEqual(
            "function_call_output:call-2",
            runner._summarize_trace_item({"type": "function_call_output", "call_id": "call-2"}),
        )
        self.assertEqual("{'type': 'other', 'value': 1}", runner._summarize_trace_item({"type": "other", "value": 1}))
        self.assertEqual("plain text", runner._summarize_trace_item("plain text"))

    def test_context_path_estimate_tokens_dotenv_and_import_helpers(self) -> None:
        self.assertFalse(runner._looks_like_context_path("line-one\nline-two"))
        self.assertFalse(runner._looks_like_context_path("x" * 1025))

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self.assertIsNone(runner._resolve_project_relative_path(project_root, "../outside.txt"))

            with mock.patch("pathlib.Path.resolve", side_effect=OSError("boom")):
                self.assertIsNone(runner._resolve_project_relative_path(project_root, "runs/example.json"))

            original_import = builtins.__import__

            def missing_tiktoken(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "tiktoken":
                    raise ImportError("missing")
                return original_import(name, globals, locals, fromlist, level)

            with mock.patch.dict(sys.modules, {}, clear=False):
                sys.modules.pop("tiktoken", None)
                with mock.patch("builtins.__import__", side_effect=missing_tiktoken):
                    self.assertEqual(3, runner._estimate_tokens("abcdefghij"))

            with mock.patch.dict(
                sys.modules,
                {"tiktoken": types.SimpleNamespace(get_encoding=mock.Mock(side_effect=RuntimeError("boom")))},
                clear=False,
            ):
                self.assertEqual(3, runner._estimate_tokens("abcdefghij"))

            fake_loader = object()
            with mock.patch.dict(sys.modules, {"dotenv": types.SimpleNamespace(load_dotenv=fake_loader)}, clear=False):
                self.assertIs(fake_loader, runner._load_dotenv(project_root))

            def missing_dotenv(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "dotenv":
                    raise ImportError("missing")
                return original_import(name, globals, locals, fromlist, level)

            with mock.patch.dict(sys.modules, {}, clear=False):
                sys.modules.pop("dotenv", None)
                with mock.patch("builtins.__import__", side_effect=missing_dotenv):
                    self.assertIsNone(runner._load_dotenv(project_root))

            original_path = list(sys.path)
            try:
                sys.path[:] = ["", str(project_root), "/tmp/other"]
                with runner._sanitized_import_path(project_root):
                    self.assertEqual(["/tmp/other"], sys.path)
                self.assertEqual(["", str(project_root), "/tmp/other"], sys.path)
            finally:
                sys.path[:] = original_path

            with (
                mock.patch.object(runner, "_sanitized_import_path", return_value=contextlib.nullcontext()),
                mock.patch.object(runner.importlib, "import_module", return_value=SimpleNamespace()),
            ):
                with self.assertRaises(ImportError):
                    runner._import_openai_agents_sdk(project_root)


class RunWorkflowFailureTests(unittest.TestCase):
    def test_run_workflow_uses_explicit_manual_lesson_context_files(self) -> None:
        original_build_executor = runner._build_executor
        try:
            runner._build_executor = lambda runtime: runner.StubAgentExecutor()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                (project_root / "skills" / "lesson-extractor").mkdir(parents=True)
                source_file = project_root / "runs" / "source.json"
                comparison_file = project_root / "runs" / "comparison.json"
                source_file.parent.mkdir(parents=True)
                source_file.write_text("{}", encoding="utf-8")
                comparison_file.write_text("{}", encoding="utf-8")
                (project_root / "skills" / "lesson-extractor" / "SKILL.md").write_text(
                    "---\nname: lesson-extractor\ndescription: Extract lessons.\n---\n\nDo it.\n",
                    encoding="utf-8",
                )

                result = run_workflow(
                    project_root=project_root,
                    workflow_name="manual-lesson-extraction",
                    overrides={
                        "source_path": "runs/source.json",
                        "comparison_path": "runs/comparison.json",
                    },
                )

                self.assertEqual("completed", result.status)
                self.assertEqual(
                    ["runs/comparison.json", "runs/source.json"],
                    result.output["context_files"],
                )
        finally:
            runner._build_executor = original_build_executor

    def test_run_workflow_resolves_latest_skill_eval_artifacts_for_refinement(self) -> None:
        original_build_executor = runner._build_executor
        try:
            runner._build_executor = lambda runtime: runner.StubAgentExecutor()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                (project_root / "skills" / "skill-refiner").mkdir(parents=True)
                sample_skill_dir = project_root / "skills" / "sample-skill"
                sample_skill_dir.mkdir(parents=True)
                (project_root / "skills" / "skill-refiner" / "SKILL.md").write_text(
                    "---\nname: skill-refiner\ndescription: Refine skills.\n---\n\nDo it.\n",
                    encoding="utf-8",
                )
                (sample_skill_dir / "SKILL.md").write_text(
                    "---\nname: sample-skill\ndescription: Sample skill.\n---\n\nDo it.\n",
                    encoding="utf-8",
                )
                (sample_skill_dir / "evals").mkdir(parents=True)
                (sample_skill_dir / "evals" / "evals.json").write_text(
                    '{"skill_name":"sample-skill","evals":[]}',
                    encoding="utf-8",
                )
                latest_iteration = sample_skill_dir / "evals" / "workspace" / "iteration-2"
                old_iteration = sample_skill_dir / "evals" / "workspace" / "iteration-1"
                for iteration_dir in [old_iteration, latest_iteration]:
                    (iteration_dir / "eval-case-one" / "with_skill").mkdir(parents=True)
                (latest_iteration / "benchmark.json").write_text("{}", encoding="utf-8")
                (latest_iteration / "feedback.json").write_text("{}", encoding="utf-8")
                (latest_iteration / "eval-case-one" / "comparison.json").write_text("{}", encoding="utf-8")
                (latest_iteration / "eval-case-one" / "with_skill" / "grading.json").write_text(
                    "{}",
                    encoding="utf-8",
                )
                (latest_iteration / "eval-case-one" / "with_skill" / "trace.json").write_text(
                    "{}",
                    encoding="utf-8",
                )
                (old_iteration / "benchmark.json").write_text("{}", encoding="utf-8")

                result = run_workflow(
                    project_root=project_root,
                    workflow_name="manual-skill-refinement",
                    overrides={"target_skill": "sample-skill"},
                )

                self.assertEqual("completed", result.status)
                self.assertEqual(
                    "skills/sample-skill/evals/workspace/iteration-2/benchmark.json",
                    result.inputs["benchmark_path"],
                )
                self.assertEqual(
                    "skills/sample-skill/evals/workspace/iteration-2/feedback.json",
                    result.inputs["feedback_path"],
                )
                self.assertEqual(
                    "skills/sample-skill/evals/workspace/iteration-2/eval-case-one/comparison.json",
                    result.inputs["comparison_path"],
                )
                self.assertEqual(
                    "skills/sample-skill/evals/workspace/iteration-2/eval-case-one/with_skill/trace.json",
                    result.inputs["trace_path"],
                )
                self.assertIn(
                    "skills/sample-skill/evals/workspace/iteration-2/eval-case-one/with_skill/grading.json",
                    result.output["context_files"],
                )
        finally:
            runner._build_executor = original_build_executor

    def test_run_workflow_persists_failed_run_record(self) -> None:
        original_build_executor = runner._build_executor
        try:
            class FailingExecutor:
                def run(self, **kwargs):
                    raise RuntimeError("boom")

            runner._build_executor = lambda runtime: FailingExecutor()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                (project_root / "skills" / "repo-triage").mkdir(parents=True)
                (project_root / "skills" / "repo-triage" / "SKILL.md").write_text(
                    "---\nname: repo-triage\ndescription: Triage repositories.\n---\n\nDo triage.\n",
                    encoding="utf-8",
                )

                result = run_workflow(
                    project_root=project_root,
                    workflow_name="manual-triage",
                )

                self.assertEqual("failed", result.status)
                self.assertIn("Run failed: RuntimeError: boom", result.output["summary"])
                run_record = (project_root / result.run_path).read_text(encoding="utf-8")
                log_record = (project_root / result.log_path).read_text(encoding="utf-8")
                self.assertIn('"status": "failed"', run_record)
                self.assertIn("Run failed: RuntimeError: boom", log_record)
        finally:
            runner._build_executor = original_build_executor


if __name__ == "__main__":
    unittest.main()
