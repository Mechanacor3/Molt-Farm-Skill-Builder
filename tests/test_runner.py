from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

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


class RunWorkflowFailureTests(unittest.TestCase):
    def test_run_workflow_persists_failed_run_record(self) -> None:
        original_build_executor = runner._build_executor
        try:
            class FailingExecutor:
                def run(self, **kwargs):
                    raise RuntimeError("boom")

            runner._build_executor = lambda runtime: FailingExecutor()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                (project_root / "agents" / "triage-worker").mkdir(parents=True)
                (project_root / "workflows" / "manual-triage").mkdir(parents=True)
                (project_root / "skills" / "repo-triage").mkdir(parents=True)
                (project_root / "agents" / "triage-worker" / "agent.yaml").write_text(
                    "name: triage-worker\nmodel: gpt-5\nskills:\n  - repo-triage\nruntime: openai_agents\n",
                    encoding="utf-8",
                )
                (project_root / "workflows" / "manual-triage" / "molt.yaml").write_text(
                    "name: manual-triage\nentry_agent: triage-worker\ninputs:\n  task: test failure\n",
                    encoding="utf-8",
                )
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
